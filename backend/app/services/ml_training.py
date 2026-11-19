"""Machine Learning Model Training Pipeline.

Provides deterministic, reproducible training routines for:
1. Customer Churn Prediction (Classification)
2. Daily Sales Revenue Forecasting (Time-Series Regression)
3. Product Demand Forecasting (SKU Level Regression)

Enforces strict data leakage prevention (temporal splits, fit-on-train only)
and stores model artifacts and JSON metadata.
"""

import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import joblib
import numpy as np
from sklearn.dummy import DummyRegressor
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    mean_absolute_error,
    precision_score,
    recall_score,
    roc_auc_score,
    root_mean_squared_error,
)
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

ARTIFACTS_DIR = Path(__file__).resolve().parents[3] / "artifacts"
MODELS_DIR = ARTIFACTS_DIR / "models"
METADATA_DIR = ARTIFACTS_DIR / "model_metadata"

MODELS_DIR.mkdir(parents=True, exist_ok=True)
METADATA_DIR.mkdir(parents=True, exist_ok=True)


def train_customer_churn_model(db: Session, random_state: int = 42) -> dict[str, Any]:
    """Train Customer Churn Prediction model with leakage-free split and governance metadata."""
    query = """
    WITH customer_stats AS (
        SELECT
            c.id,
            c.signup_date,
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
        cs.tenure_days,
        cs.order_count,
        cs.total_spend,
        cs.avg_order_value,
        cs.days_since_last_order,
        COALESCE(rs.returns_count, 0) as returns_count,
        cs.customer_type,
        cs.acquisition_channel,
        CASE WHEN cs.days_since_last_order > 90 THEN 1 ELSE 0 END as is_churned
    FROM customer_stats cs
    LEFT JOIN returns_stats rs ON cs.id = rs.customer_id
    ORDER BY cs.id;
    """
    rows = db.execute(text(query)).fetchall()
    if len(rows) < 100:
        raise ValueError(f"Insufficient customer dataset for model training (N={len(rows)} < 100).")

    type_map = {"B2B": 0, "B2C": 1, "Enterprise": 2}
    channel_map = {"Direct": 0, "Field Sales": 1, "Partner": 2, "Online": 3}

    features_list = [
        "tenure_days",
        "order_count",
        "total_spend",
        "avg_order_value",
        "returns_count",
        "customer_type_enc",
        "channel_enc",
    ]

    x_data = []
    y_data = []

    for r in rows:
        tenure = float(r.tenure_days or 0)
        orders = float(r.order_count or 0)
        spend = float(r.total_spend or 0.0)
        aov = float(r.avg_order_value or 0.0)
        ret_count = float(r.returns_count or 0)
        c_type = type_map.get(str(r.customer_type), 0)
        c_chan = channel_map.get(str(r.acquisition_channel), 0)
        churn = int(r.is_churned)

        x_data.append([tenure, orders, spend, aov, ret_count, c_type, c_chan])
        y_data.append(churn)

    x_arr = np.array(x_data, dtype=np.float64)
    y_arr = np.array(y_data, dtype=np.int64)

    # Train / test split (80/20) with random_state for strict reproducibility
    x_train, x_test, y_train, y_test = train_test_split(
        x_arr, y_arr, test_size=0.20, random_state=random_state, stratify=y_arr
    )

    # Preprocessing: StandardScaler fitted ONLY on train set to prevent data leakage
    scaler = StandardScaler()
    x_train_scaled = scaler.fit_transform(x_train)
    x_test_scaled = scaler.transform(x_test)

    # 1. Baseline Model: Logistic Regression
    baseline = LogisticRegression(random_state=random_state, max_iter=500)
    baseline.fit(x_train_scaled, y_train)
    base_preds = baseline.predict(x_test_scaled)
    base_probs = baseline.predict_proba(x_test_scaled)[:, 1]

    baseline_metrics = {
        "accuracy": round(float(accuracy_score(y_test, base_preds)), 4),
        "precision": round(float(precision_score(y_test, base_preds, zero_division=0)), 4),
        "recall": round(float(recall_score(y_test, base_preds, zero_division=0)), 4),
        "f1": round(float(f1_score(y_test, base_preds, zero_division=0)), 4),
        "roc_auc": round(float(roc_auc_score(y_test, base_probs)), 4),
    }

    # 2. Candidate Model: Random Forest Classifier
    candidate = RandomForestClassifier(
        n_estimators=100, max_depth=6, min_samples_leaf=3, random_state=random_state
    )
    candidate.fit(x_train_scaled, y_train)

    cand_train_probs = candidate.predict_proba(x_train_scaled)[:, 1]
    cand_train_preds = candidate.predict(x_train_scaled)
    cand_preds = candidate.predict(x_test_scaled)
    cand_probs = candidate.predict_proba(x_test_scaled)[:, 1]

    train_auc = float(roc_auc_score(y_train, cand_train_probs))
    test_auc = float(roc_auc_score(y_test, cand_probs))
    overfitting_gap = round(train_auc - test_auc, 4)

    candidate_metrics = {
        "accuracy": round(float(accuracy_score(y_test, cand_preds)), 4),
        "precision": round(float(precision_score(y_test, cand_preds, zero_division=0)), 4),
        "recall": round(float(recall_score(y_test, cand_preds, zero_division=0)), 4),
        "f1": round(float(f1_score(y_test, cand_preds, zero_division=0)), 4),
        "roc_auc": round(test_auc, 4),
    }

    # Feature importances
    importances = {
        name: round(float(imp), 4)
        for name, imp in zip(features_list, candidate.feature_importances_, strict=False)
    }

    # Save artifacts
    pipeline = {
        "scaler": scaler,
        "model": candidate,
        "features": features_list,
        "type_map": type_map,
        "channel_map": channel_map,
    }
    model_path = MODELS_DIR / "customer_churn.joblib"
    joblib.dump(pipeline, model_path)

    metadata = {
        "model_id": "customer_churn",
        "model_name": "Customer Churn Prediction",
        "problem_type": "binary_classification",
        "target_variable": "is_churned (recency > 90d)",
        "features": features_list,
        "baseline_algorithm": "LogisticRegression",
        "candidate_algorithm": "RandomForestClassifier",
        "hyperparameters": {
            "n_estimators": 100,
            "max_depth": 6,
            "min_samples_leaf": 3,
            "random_state": random_state,
        },
        "sample_size_train": len(x_train),
        "sample_size_test": len(x_test),
        "split_strategy": "Stratified 80/20 split with fitted-on-train scaling (no leakage)",
        "baseline_metrics": baseline_metrics,
        "candidate_metrics": candidate_metrics,
        "train_metrics": {
            "accuracy": round(float(accuracy_score(y_train, cand_train_preds)), 4),
            "roc_auc": round(train_auc, 4),
        },
        "overfitting_gap": overfitting_gap,
        "feature_importances": importances,
        "trained_at": datetime.now(UTC).isoformat(),
        "artifact_path": str(model_path.relative_to(ARTIFACTS_DIR.parent)),
        "is_loaded": True,
        "governance_notice": (
            "Probabilistic customer churn model. High-risk flag signals intervention priority; "
            "actual retention outcomes depend on CRM execution."
        ),
    }

    meta_path = METADATA_DIR / "customer_churn.json"
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    return metadata


def train_sales_forecast_model(db: Session, random_state: int = 42) -> dict[str, Any]:
    """Train Sales Forecasting time-series model with temporal split (no future lookahead)."""
    query = """
    SELECT
        DATE(order_date) as order_day,
        COALESCE(SUM(total_amount), 0.0) as daily_revenue,
        COUNT(id) as daily_orders
    FROM orders
    GROUP BY DATE(order_date)
    ORDER BY order_day;
    """
    rows = db.execute(text(query)).fetchall()
    if len(rows) < 60:
        raise ValueError(f"Insufficient daily series observations (N={len(rows)} < 60).")

    # Time series lag & calendar feature generation
    series = [float(r.daily_revenue) for r in rows]
    dates = [str(r.order_day) for r in rows]

    features_list = [
        "day_of_week",
        "day_of_month",
        "month",
        "lag_1",
        "lag_7",
        "rolling_mean_7",
        "rolling_mean_14",
    ]

    x_data = []
    y_data = []

    for i in range(14, len(series)):
        dt = datetime.strptime(dates[i], "%Y-%m-%d")
        dow = float(dt.weekday())
        dom = float(dt.day)
        mo = float(dt.month)
        lag_1 = series[i - 1]
        lag_7 = series[i - 7]
        rm_7 = float(np.mean(series[i - 7 : i]))
        rm_14 = float(np.mean(series[i - 14 : i]))

        x_data.append([dow, dom, mo, lag_1, lag_7, rm_7, rm_14])
        y_data.append(series[i])

    x_arr = np.array(x_data, dtype=np.float64)
    y_arr = np.array(y_data, dtype=np.float64)

    # Strict Chronological Temporal Split: train on first 80%, test on most recent 20%
    # Absolutely NO random shuffling to guarantee zero data leakage from future to past
    split_idx = int(len(x_arr) * 0.80)
    x_train, x_test = x_arr[:split_idx], x_arr[split_idx:]
    y_train, y_test = y_arr[:split_idx], y_arr[split_idx:]

    scaler = StandardScaler()
    x_train_scaled = scaler.fit_transform(x_train)
    x_test_scaled = scaler.transform(x_test)

    # 1. Baseline Model: Naive Mean Dummy Regressor
    baseline = DummyRegressor(strategy="mean")
    baseline.fit(x_train_scaled, y_train)
    base_preds = baseline.predict(x_test_scaled)

    base_mae = float(mean_absolute_error(y_test, base_preds))
    base_rmse = float(root_mean_squared_error(y_test, base_preds))

    baseline_metrics = {
        "mae": round(base_mae, 2),
        "rmse": round(base_rmse, 2),
    }

    # 2. Candidate Model: Random Forest Regressor
    candidate = RandomForestRegressor(
        n_estimators=100, max_depth=6, min_samples_leaf=2, random_state=random_state
    )
    candidate.fit(x_train_scaled, y_train)

    cand_train_preds = candidate.predict(x_train_scaled)
    cand_preds = candidate.predict(x_test_scaled)

    train_mae = float(mean_absolute_error(y_train, cand_train_preds))
    test_mae = float(mean_absolute_error(y_test, cand_preds))
    test_rmse = float(root_mean_squared_error(y_test, cand_preds))
    # Mean Absolute Percentage Error
    mape = float(np.mean(np.abs((y_test - cand_preds) / np.maximum(y_test, 1.0)))) * 100.0

    candidate_metrics = {
        "mae": round(test_mae, 2),
        "rmse": round(test_rmse, 2),
        "mape": round(mape, 2),
    }

    importances = {
        name: round(float(imp), 4)
        for name, imp in zip(features_list, candidate.feature_importances_, strict=False)
    }

    pipeline = {
        "scaler": scaler,
        "model": candidate,
        "features": features_list,
        "recent_series": series[-30:],
        "recent_dates": dates[-30:],
    }
    model_path = MODELS_DIR / "sales_forecast.joblib"
    joblib.dump(pipeline, model_path)

    metadata = {
        "model_id": "sales_forecast",
        "model_name": "Sales Revenue Forecasting",
        "problem_type": "regression_time_series",
        "target_variable": "daily_revenue",
        "features": features_list,
        "baseline_algorithm": "DummyRegressor (Historical Mean)",
        "candidate_algorithm": "RandomForestRegressor",
        "hyperparameters": {
            "n_estimators": 100,
            "max_depth": 6,
            "min_samples_leaf": 2,
            "random_state": random_state,
        },
        "sample_size_train": len(x_train),
        "sample_size_test": len(x_test),
        "split_strategy": "Chronological temporal 80/20 split (forward-facing, zero leakage)",
        "baseline_metrics": baseline_metrics,
        "candidate_metrics": candidate_metrics,
        "train_metrics": {
            "mae": round(train_mae, 2),
            "rmse": round(float(root_mean_squared_error(y_train, cand_train_preds)), 2),
        },
        "overfitting_gap": round(abs(train_mae - test_mae), 2),
        "feature_importances": importances,
        "trained_at": datetime.now(UTC).isoformat(),
        "artifact_path": str(model_path.relative_to(ARTIFACTS_DIR.parent)),
        "is_loaded": True,
        "governance_notice": (
            "Time-series forecasts assume continuity of seasonal demand. "
            "Unpredicted macroeconomic shifts may increase forecast variance."
        ),
    }

    meta_path = METADATA_DIR / "sales_forecast.json"
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    return metadata


def train_product_demand_model(db: Session, random_state: int = 42) -> dict[str, Any]:
    """Train Product SKU Demand model (BL-14)."""
    query = """
    SELECT
        p.id,
        p.sku,
        p.name,
        p.category_id,
        p.unit_price,
        p.unit_cost,
        p.reorder_point,
        p.target_stock,
        COALESCE(SUM(oi.quantity), 0) as total_units_sold,
        COUNT(DISTINCT o.id) as order_frequency
    FROM products p
    JOIN order_items oi ON p.id = oi.product_id
    JOIN orders o ON oi.order_id = o.id
    GROUP BY
        p.id, p.sku, p.name, p.category_id, p.unit_price, p.unit_cost,
        p.reorder_point, p.target_stock
    ORDER BY p.id;
    """
    rows = db.execute(text(query)).fetchall()
    if len(rows) < 20:
        raise ValueError(f"Insufficient product dataset (N={len(rows)} < 20).")

    features_list = [
        "unit_price",
        "unit_cost",
        "margin",
        "reorder_point",
        "target_stock",
        "order_frequency",
        "category_id",
    ]

    x_data = []
    y_data = []

    for r in rows:
        price = float(r.unit_price)
        cost = float(r.unit_cost)
        margin = price - cost
        reorder = float(r.reorder_point)
        target = float(r.target_stock)
        freq = float(r.order_frequency)
        cat_id = float(r.category_id)
        units = float(r.total_units_sold)

        x_data.append([price, cost, margin, reorder, target, freq, cat_id])
        y_data.append(units)

    x_arr = np.array(x_data, dtype=np.float64)
    y_arr = np.array(y_data, dtype=np.float64)

    x_train, x_test, y_train, y_test = train_test_split(
        x_arr, y_arr, test_size=0.20, random_state=random_state
    )

    scaler = StandardScaler()
    x_train_scaled = scaler.fit_transform(x_train)
    x_test_scaled = scaler.transform(x_test)

    # Baseline Model: Mean Dummy Regressor
    baseline = DummyRegressor(strategy="mean")
    baseline.fit(x_train_scaled, y_train)
    base_preds = baseline.predict(x_test_scaled)
    base_mae = float(mean_absolute_error(y_test, base_preds))
    base_rmse = float(root_mean_squared_error(y_test, base_preds))

    # Candidate Model: Random Forest Regressor
    candidate = RandomForestRegressor(
        n_estimators=80, max_depth=5, min_samples_leaf=2, random_state=random_state
    )
    candidate.fit(x_train_scaled, y_train)
    cand_preds = candidate.predict(x_test_scaled)
    cand_train_preds = candidate.predict(x_train_scaled)

    train_mae = float(mean_absolute_error(y_train, cand_train_preds))
    test_mae = float(mean_absolute_error(y_test, cand_preds))
    test_rmse = float(root_mean_squared_error(y_test, cand_preds))

    importances = {
        name: round(float(imp), 4)
        for name, imp in zip(features_list, candidate.feature_importances_, strict=False)
    }

    pipeline = {
        "scaler": scaler,
        "model": candidate,
        "features": features_list,
    }
    model_path = MODELS_DIR / "product_demand.joblib"
    joblib.dump(pipeline, model_path)

    metadata = {
        "model_id": "product_demand",
        "model_name": "Product SKU Demand Forecasting",
        "problem_type": "regression_demand",
        "target_variable": "total_units_sold",
        "features": features_list,
        "baseline_algorithm": "DummyRegressor (Mean)",
        "candidate_algorithm": "RandomForestRegressor",
        "hyperparameters": {
            "n_estimators": 80,
            "max_depth": 5,
            "min_samples_leaf": 2,
            "random_state": random_state,
        },
        "sample_size_train": len(x_train),
        "sample_size_test": len(x_test),
        "split_strategy": "Random 80/20 train/test split with fitted-on-train scaling",
        "baseline_metrics": {
            "mae": round(base_mae, 2),
            "rmse": round(base_rmse, 2),
        },
        "candidate_metrics": {
            "mae": round(test_mae, 2),
            "rmse": round(test_rmse, 2),
        },
        "train_metrics": {
            "mae": round(train_mae, 2),
            "rmse": round(float(root_mean_squared_error(y_train, cand_train_preds)), 2),
        },
        "overfitting_gap": round(abs(train_mae - test_mae), 2),
        "feature_importances": importances,
        "trained_at": datetime.now(UTC).isoformat(),
        "artifact_path": str(model_path.relative_to(ARTIFACTS_DIR.parent)),
        "is_loaded": True,
        "governance_notice": (
            "Product demand forecasts support replenishment thresholds; "
            "lead-time variance must be factored into purchase orders."
        ),
    }

    meta_path = METADATA_DIR / "product_demand.json"
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    return metadata


def train_all_models(db: Session, random_state: int = 42) -> dict[str, Any]:
    """Execute end-to-end training and artifact generation across all predictive models."""
    churn_meta = train_customer_churn_model(db, random_state=random_state)
    sales_meta = train_sales_forecast_model(db, random_state=random_state)
    demand_meta = train_product_demand_model(db, random_state=random_state)

    return {
        "customer_churn": churn_meta,
        "sales_forecast": sales_meta,
        "product_demand": demand_meta,
    }
