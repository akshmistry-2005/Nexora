"""Prediction and Inference Service.

Handles model artifact loading, batch and single-record inference,
time-series sales projections with confidence intervals, SKU demand forecasting,
and model governance metadata.
"""

import json
import logging
import math
from datetime import datetime, timedelta
from typing import Any

import joblib
import numpy as np
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.schemas.predictions import (
    BatchChurnInferenceOutput,
    ChurnInferenceInput,
    ChurnInferenceOutput,
    HighRiskCustomerItem,
    ModelMetadataItem,
    ProductDemandItem,
    ProductDemandResponse,
    SalesForecastPoint,
    SalesForecastResponse,
)
from app.services.ml_training import (
    ARTIFACTS_DIR,
    METADATA_DIR,
    MODELS_DIR,
    train_customer_churn_model,
    train_product_demand_model,
    train_sales_forecast_model,
)

logger = logging.getLogger(__name__)

# In-memory artifact cache
_LOADED_MODELS: dict[str, Any] = {}


def _get_or_load_pipeline(model_id: str, db: Session | None = None) -> Any:
    """Retrieve model pipeline from cache or load from disk, training if missing."""
    if model_id in _LOADED_MODELS:
        return _LOADED_MODELS[model_id]

    model_path = MODELS_DIR / f"{model_id}.joblib"
    if not model_path.exists():
        if db is not None:
            logger.info(f"Model artifact {model_id}.joblib not found; training on demand.")
            if model_id == "customer_churn":
                train_customer_churn_model(db)
            elif model_id == "sales_forecast":
                train_sales_forecast_model(db)
            elif model_id == "product_demand":
                train_product_demand_model(db)
        else:
            raise FileNotFoundError(
                f"Model artifact for '{model_id}' is missing and cannot be loaded."
            )

    if not model_path.exists():
        raise FileNotFoundError(
            f"Model artifact for '{model_id}' could not be located at {model_path}."
        )

    pipeline = joblib.load(model_path)
    _LOADED_MODELS[model_id] = pipeline
    return pipeline


def get_model_metadata(model_id: str, db: Session | None = None) -> ModelMetadataItem:
    """Read saved JSON metadata for a model."""
    meta_path = METADATA_DIR / f"{model_id}.json"
    if not meta_path.exists():
        if db is not None:
            # Train and generate metadata
            if model_id == "customer_churn":
                data = train_customer_churn_model(db)
            elif model_id == "sales_forecast":
                data = train_sales_forecast_model(db)
            elif model_id == "product_demand":
                data = train_product_demand_model(db)
            else:
                raise FileNotFoundError(f"Unknown model identifier '{model_id}'.")
            return ModelMetadataItem(**data)
        raise FileNotFoundError(f"Metadata file for model '{model_id}' does not exist.")

    with open(meta_path, encoding="utf-8") as f:
        data = json.load(f)

    # Check if artifact is accessible
    art_path = ARTIFACTS_DIR.parent / data.get("artifact_path", "")
    data["is_loaded"] = art_path.exists()
    return ModelMetadataItem(**data)


def list_models(db: Session | None = None) -> list[ModelMetadataItem]:
    """List all registered ML models and their performance benchmarks."""
    model_ids = ["customer_churn", "sales_forecast", "product_demand"]
    items: list[ModelMetadataItem] = []
    for mid in model_ids:
        try:
            items.append(get_model_metadata(mid, db=db))
        except FileNotFoundError:
            logger.warning(f"Metadata for {mid} not available.")
    return items


def predict_churn(
    input_data: ChurnInferenceInput, db: Session | None = None
) -> ChurnInferenceOutput:
    """Score churn probability and risk tier for a single customer."""
    pipeline = _get_or_load_pipeline("customer_churn", db=db)
    scaler = pipeline["scaler"]
    model = pipeline["model"]
    type_map = pipeline.get("type_map", {"B2B": 0, "B2C": 1, "Enterprise": 2})
    channel_map = pipeline.get(
        "channel_map", {"Direct": 0, "Field Sales": 1, "Partner": 2, "Online": 3}
    )

    c_type = type_map.get(input_data.customer_type, 0)
    c_chan = channel_map.get(input_data.acquisition_channel, 0)

    vec = np.array(
        [
            [
                float(input_data.tenure_days),
                float(input_data.order_count),
                float(input_data.total_spend),
                float(input_data.avg_order_value),
                float(input_data.returns_count),
                float(c_type),
                float(c_chan),
            ]
        ],
        dtype=np.float64,
    )

    vec_scaled = scaler.transform(vec)
    prob = float(model.predict_proba(vec_scaled)[0, 1])
    is_churn = prob >= 0.50

    if prob >= 0.65:
        tier = "High"
    elif prob >= 0.35:
        tier = "Medium"
    else:
        tier = "Low"

    # Identify top contributing risk factors based on deviations from normal customer means
    factors = []
    if input_data.days_since_last_order and input_data.days_since_last_order > 60:
        factors.append(
            {
                "factor": "Order Inactivity",
                "impact": "High Risk",
                "description": f"{input_data.days_since_last_order} days without a purchase.",
            }
        )
    if input_data.order_count < 3:
        factors.append(
            {
                "factor": "Low Transaction Frequency",
                "impact": "Moderate Risk",
                "description": (
                    f"Customer has only placed {input_data.order_count} lifetime orders."
                ),
            }
        )
    if input_data.returns_count > 2:
        factors.append(
            {
                "factor": "Elevated Return Rate",
                "impact": "Risk Driver",
                "description": f"{input_data.returns_count} returns logged.",
            }
        )
    if not factors:
        factors.append(
            {
                "factor": "Healthy Account Engagement",
                "impact": "Retention Driver",
                "description": "Consistent order velocity and low return frequency.",
            }
        )

    return ChurnInferenceOutput(
        churn_probability=round(prob, 4),
        is_churn_predicted=is_churn,
        risk_tier=tier,
        contributing_factors=factors,
        model_id="customer_churn",
    )


def batch_predict_churn(
    records: list[ChurnInferenceInput], db: Session | None = None
) -> BatchChurnInferenceOutput:
    """Score a batch of customer feature records consistently with single inference."""
    pipeline = _get_or_load_pipeline("customer_churn", db=db)
    scaler = pipeline["scaler"]
    model = pipeline["model"]
    type_map = pipeline.get("type_map", {"B2B": 0, "B2C": 1, "Enterprise": 2})
    channel_map = pipeline.get(
        "channel_map", {"Direct": 0, "Field Sales": 1, "Partner": 2, "Online": 3}
    )

    rows = []
    for r in records:
        c_type = type_map.get(r.customer_type, 0)
        c_chan = channel_map.get(r.acquisition_channel, 0)
        rows.append(
            [
                float(r.tenure_days),
                float(r.order_count),
                float(r.total_spend),
                float(r.avg_order_value),
                float(r.returns_count),
                float(c_type),
                float(c_chan),
            ]
        )

    matrix = np.array(rows, dtype=np.float64)
    matrix_scaled = scaler.transform(matrix)
    probs = model.predict_proba(matrix_scaled)[:, 1]

    results: list[ChurnInferenceOutput] = []
    for _r, prob_val in zip(records, probs, strict=False):
        p = float(prob_val)
        is_c = p >= 0.50
        tier = "High" if p >= 0.65 else ("Medium" if p >= 0.35 else "Low")
        results.append(
            ChurnInferenceOutput(
                churn_probability=round(p, 4),
                is_churn_predicted=is_c,
                risk_tier=tier,
                contributing_factors=[],
                model_id="customer_churn",
            )
        )

    return BatchChurnInferenceOutput(total_records=len(results), results=results)


def get_high_risk_customers(db: Session, limit: int = 25) -> list[HighRiskCustomerItem]:
    """Retrieve customers with highest estimated churn risk from live database records."""
    pipeline = _get_or_load_pipeline("customer_churn", db=db)
    scaler = pipeline["scaler"]
    model = pipeline["model"]
    type_map = pipeline.get("type_map", {"B2B": 0, "B2C": 1, "Enterprise": 2})
    channel_map = pipeline.get(
        "channel_map", {"Direct": 0, "Field Sales": 1, "Partner": 2, "Online": 3}
    )

    query = """
    WITH customer_stats AS (
        SELECT
            c.id,
            c.company_name,
            c.contact_name,
            c.email,
            c.customer_type,
            c.acquisition_channel,
            COUNT(o.id) as order_count,
            COALESCE(SUM(o.total_amount), 0) as total_spend,
            COALESCE(AVG(o.total_amount), 0) as avg_order_value,
            COALESCE(
                EXTRACT(DAY FROM ('2026-11-14 23:59:59+00'::timestamptz - MAX(o.order_date))),
                999
            ) as days_since_last_order,
            ('2026-11-14'::date - c.signup_date) as tenure_days
        FROM customers c
        LEFT JOIN orders o ON c.id = o.customer_id
        GROUP BY c.id, c.signup_date, c.customer_type, c.acquisition_channel
    ),
    returns_stats AS (
        SELECT
            o.customer_id,
            COUNT(r.id) as returns_count
        FROM orders o
        JOIN order_returns r ON o.id = r.order_id
        GROUP BY o.customer_id
    )
    SELECT
        cs.id,
        cs.company_name,
        cs.contact_name,
        cs.email,
        cs.customer_type,
        cs.acquisition_channel,
        cs.tenure_days,
        cs.order_count,
        cs.total_spend,
        cs.avg_order_value,
        cs.days_since_last_order,
        COALESCE(rs.returns_count, 0) as returns_count
    FROM customer_stats cs
    LEFT JOIN returns_stats rs ON cs.id = rs.customer_id
    WHERE cs.order_count > 0
    ORDER BY cs.days_since_last_order DESC
    LIMIT 200;
    """
    rows = db.execute(text(query)).fetchall()
    if not rows:
        return []

    x_list = []
    for r in rows:
        c_type = type_map.get(str(r.customer_type), 0)
        c_chan = channel_map.get(str(r.acquisition_channel), 0)
        x_list.append(
            [
                float(r.tenure_days or 0),
                float(r.order_count or 0),
                float(r.total_spend or 0.0),
                float(r.avg_order_value or 0.0),
                float(r.returns_count or 0),
                float(c_type),
                float(c_chan),
            ]
        )

    x_mat = np.array(x_list, dtype=np.float64)
    x_scaled = scaler.transform(x_mat)
    probs = model.predict_proba(x_scaled)[:, 1]

    items: list[HighRiskCustomerItem] = []
    for r, p_val in zip(rows, probs, strict=False):
        prob = float(p_val)
        tier = "High" if prob >= 0.65 else ("Medium" if prob >= 0.35 else "Low")
        items.append(
            HighRiskCustomerItem(
                customer_id=r.id,
                company_name=r.company_name,
                contact_name=r.contact_name,
                email=r.email,
                customer_type=r.customer_type,
                lifetime_spend=round(float(r.total_spend), 2),
                order_count=int(r.order_count),
                days_since_last_order=int(r.days_since_last_order),
                churn_probability=round(prob, 4),
                risk_tier=tier,
            )
        )

    # Sort descending by churn probability
    items.sort(key=lambda x: x.churn_probability, reverse=True)
    return items[:limit]


def forecast_sales(horizon_days: int = 30, db: Session | None = None) -> SalesForecastResponse:
    """Project multi-step sales revenue over horizon (30/60/90 days) with 95% confidence bands."""
    if horizon_days < 1 or horizon_days > 365:
        raise ValueError("Forecast horizon must be between 1 and 365 days.")

    pipeline = _get_or_load_pipeline("sales_forecast", db=db)
    scaler = pipeline["scaler"]
    model = pipeline["model"]
    recent_series = list(pipeline["recent_series"])
    recent_dates = list(pipeline["recent_dates"])

    meta = get_model_metadata("sales_forecast", db=db)
    candidate_metrics = meta.candidate_metrics
    baseline_metrics = meta.baseline_metrics
    rmse = candidate_metrics.get("rmse", 50000.0)

    # Start date of projection is the day after the last date in historical series
    last_date_str = recent_dates[-1]
    last_date = datetime.strptime(last_date_str, "%Y-%m-%d")

    projected_points: list[SalesForecastPoint] = []
    working_series = list(recent_series)

    total_rev = 0.0

    for step in range(1, horizon_days + 1):
        target_date = last_date + timedelta(days=step)
        dow = float(target_date.weekday())
        dom = float(target_date.day)
        mo = float(target_date.month)
        lag_1 = working_series[-1]
        lag_7 = working_series[-7] if len(working_series) >= 7 else working_series[0]
        rm_7 = float(np.mean(working_series[-7:]))
        rm_14 = float(np.mean(working_series[-14:]))

        x_feat = np.array([[dow, dom, mo, lag_1, lag_7, rm_7, rm_14]], dtype=np.float64)
        x_scaled = scaler.transform(x_feat)
        pred_rev = float(model.predict(x_scaled)[0])
        pred_rev = max(0.0, pred_rev)

        # Confidence interval: 95% interval expands with sqrt(horizon_step)
        uncertainty = 1.96 * rmse * math.sqrt(step / 10.0 + 0.9)
        lower_bound = max(0.0, round(pred_rev - uncertainty, 2))
        upper_bound = round(pred_rev + uncertainty, 2)

        working_series.append(pred_rev)
        total_rev += pred_rev

        projected_points.append(
            SalesForecastPoint(
                date=target_date.strftime("%Y-%m-%d"),
                forecasted_revenue=round(pred_rev, 2),
                lower_bound_95=lower_bound,
                upper_bound_95=upper_bound,
            )
        )

    # Contextual recent history
    history = [
        {"date": d, "revenue": round(r, 2)}
        for d, r in zip(recent_dates[-14:], recent_series[-14:], strict=False)
    ]

    return SalesForecastResponse(
        horizon_days=horizon_days,
        model_id="sales_forecast",
        total_forecasted_revenue=round(total_rev, 2),
        evaluation_metrics=candidate_metrics,
        baseline_metrics=baseline_metrics,
        forecast_series=projected_points,
        historical_series=history,
    )


def forecast_product_demand(
    db: Session, category_id: int | None = None, limit: int = 15
) -> ProductDemandResponse:
    """Project SKU monthly demand and identify reorder replenishment requirements."""
    pipeline = _get_or_load_pipeline("product_demand", db=db)
    scaler = pipeline["scaler"]
    model = pipeline["model"]

    meta = get_model_metadata("product_demand", db=db)
    eval_metrics = meta.candidate_metrics

    where_clause = ""
    params: dict[str, Any] = {"lim": limit}
    if category_id is not None:
        where_clause = "WHERE p.category_id = :cat_id"
        params["cat_id"] = category_id

    query = f"""
    WITH order_stats AS (
        SELECT
            oi.product_id,
            COUNT(DISTINCT o.id) as order_frequency,
            COALESCE(SUM(oi.quantity), 0) as total_units_sold
        FROM order_items oi
        JOIN orders o ON oi.order_id = o.id
        GROUP BY oi.product_id
    ),
    inventory_stats AS (
        SELECT
            product_id,
            COALESCE(SUM(quantity_on_hand), 0) as current_stock
        FROM inventory
        GROUP BY product_id
    )
    SELECT
        p.id,
        p.sku,
        p.name,
        c.name as category_name,
        p.category_id,
        p.unit_price,
        p.unit_cost,
        p.reorder_point,
        p.target_stock,
        COALESCE(inv.current_stock, 150) as current_stock,
        COALESCE(os.order_frequency, 10) as order_frequency,
        COALESCE(os.total_units_sold, 100) as total_units_sold
    FROM products p
    JOIN categories c ON p.category_id = c.id
    LEFT JOIN order_stats os ON p.id = os.product_id
    LEFT JOIN inventory_stats inv ON p.id = inv.product_id
    {where_clause}
    ORDER BY p.id
    LIMIT :lim;
    """
    rows = db.execute(text(query), params).fetchall()
    if not rows:
        return ProductDemandResponse(
            total_products=0,
            reorder_count=0,
            products=[],
            evaluation_metrics=eval_metrics,
            governance_notice="No products found matching criteria.",
        )

    items: list[ProductDemandItem] = []
    reorder_count = 0

    for r in rows:
        price = float(r.unit_price)
        cost = float(r.unit_cost)
        margin = price - cost
        reorder_pt = int(r.reorder_point)
        target = int(r.target_stock)
        freq = float(r.order_frequency)
        cat_id = float(r.category_id)
        stock = int(r.current_stock)

        x_feat = np.array(
            [[price, cost, margin, reorder_pt, target, freq, cat_id]], dtype=np.float64
        )
        x_scaled = scaler.transform(x_feat)
        # Model predicts total units; monthly demand is roughly ~1/30 of 3-year total or scaled
        pred_units = float(model.predict(x_scaled)[0])
        monthly_demand = max(5, int(round(pred_units / 12.0)))

        needs_reorder = stock < (reorder_pt + monthly_demand)
        if needs_reorder:
            reorder_count += 1

        items.append(
            ProductDemandItem(
                product_id=r.id,
                sku=r.sku,
                name=r.name,
                category_name=r.category_name,
                unit_price=round(price, 2),
                current_stock=stock,
                target_stock=target,
                forecasted_monthly_demand=monthly_demand,
                reorder_recommended=needs_reorder,
            )
        )

    return ProductDemandResponse(
        total_products=len(items),
        reorder_count=reorder_count,
        products=items,
        evaluation_metrics=eval_metrics,
        governance_notice=(
            "Product demand estimates inform reorder points and lead-time safety stock planning."
        ),
    )


def reload_model(model_id: str, db: Session) -> ModelMetadataItem:
    """Retrain model on the fly, update stored artifacts, and refresh in-memory cache."""
    if model_id == "customer_churn":
        train_customer_churn_model(db)
    elif model_id == "sales_forecast":
        train_sales_forecast_model(db)
    elif model_id == "product_demand":
        train_product_demand_model(db)
    else:
        raise ValueError(f"Unknown model identifier '{model_id}'.")

    # Invalidate cache
    _LOADED_MODELS.pop(model_id, None)
    return get_model_metadata(model_id, db=db)
