"""Module 12: Predictive Analytics & ML Engine Test Suite (M12-T01 through M12-T17).

Validates:
- Model problem definitions, dataset suitability, and leakage-free temporal splits
- Baseline vs. candidate model training and holdout evaluation (MAE, RMSE, ROC-AUC, F1)
- Overfitting checks, repeatable training with fixed random seeds
- Model metadata persistence in artifacts/model_metadata/ and artifact loading
- Real-time and batch inference APIs, input validation, and batch consistency
- Missing artifact safety and mandatory governance disclaimers
"""

import json

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.db.session import SessionLocal
from app.main import app
from app.services import predictions as pred_service
from app.services.ml_training import (
    METADATA_DIR,
    MODELS_DIR,
    train_customer_churn_model,
    train_product_demand_model,
    train_sales_forecast_model,
)


@pytest.fixture(scope="module")
def client() -> TestClient:
    """FastAPI test client instance."""
    return TestClient(app)


@pytest.fixture(scope="module")
def analyst_headers(client: TestClient) -> dict[str, str]:
    """Authenticated bearer token for Demo Data Analyst."""
    resp = client.post("/api/v1/auth/demo-login", json={"role": "data_analyst"})
    assert resp.status_code == 200
    token = resp.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="module")
def viewer_headers(client: TestClient) -> dict[str, str]:
    """Authenticated bearer token for General Viewer (unauthorized for predictions)."""
    resp = client.post("/api/v1/auth/demo-login", json={"role": "general_viewer"})
    assert resp.status_code == 200
    token = resp.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="module")
def owner_headers(client: TestClient) -> dict[str, str]:
    """Authenticated bearer token for Platform Owner."""
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": "owner@nexora.local", "password": "NexoraOwnerPass2026!"},
    )
    assert resp.status_code == 200
    token = resp.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="module", autouse=True)
def ensure_models_trained():
    """Ensure baseline and candidate models are trained and saved prior to test suite."""
    with SessionLocal() as db:
        train_customer_churn_model(db, random_state=42)
        train_sales_forecast_model(db, random_state=42)
        train_product_demand_model(db, random_state=42)


def test_m12_t01_model_problem_definition():
    """M12-T01: Explicit machine learning problem formulation and target definitions."""
    models = pred_service.list_models()
    assert len(models) >= 3, "Expected at least 3 predictive models (churn, sales, demand)."

    churn_meta = next(m for m in models if m.model_id == "customer_churn")
    assert churn_meta.problem_type == "binary_classification"
    assert "is_churned" in churn_meta.target_variable
    assert len(churn_meta.features) >= 5

    sales_meta = next(m for m in models if m.model_id == "sales_forecast")
    assert sales_meta.problem_type == "regression_time_series"
    assert sales_meta.target_variable == "daily_revenue"
    assert "lag_1" in sales_meta.features

    demand_meta = next(m for m in models if m.model_id == "product_demand")
    assert demand_meta.problem_type == "regression_demand"
    assert demand_meta.target_variable == "total_units_sold"


def test_m12_t02_dataset_suitability():
    """M12-T02: Dataset suitability, sample size bounds, and absence of empty target columns."""
    with SessionLocal() as db:
        cust_count = db.execute(text("SELECT COUNT(*) FROM customers")).scalar()
        orders_count = db.execute(text("SELECT COUNT(*) FROM orders")).scalar()
        days_count = db.execute(
            text("SELECT COUNT(DISTINCT DATE(order_date)) FROM orders")
        ).scalar()
        prod_count = db.execute(text("SELECT COUNT(*) FROM products")).scalar()

    assert cust_count >= 100, f"Customer dataset must have >= 100 rows, found {cust_count}"
    assert orders_count >= 1000, f"Order dataset must have >= 1000 rows, found {orders_count}"
    assert days_count >= 60, (
        f"Daily time series must have >= 60 observation days, found {days_count}"
    )
    assert prod_count >= 20, f"Product dataset must have >= 20 products, found {prod_count}"


def test_m12_t03_data_leakage_prevention():
    """M12-T03: Data leakage prevention via chronological splits and target isolation."""
    sales_meta = pred_service.get_model_metadata("sales_forecast")
    # Chronological temporal split must be recorded
    assert "Chronological" in sales_meta.split_strategy
    assert "leakage" in sales_meta.split_strategy.lower()

    # Churn model input features must NOT include the raw recency column if used for thresholding
    churn_meta = pred_service.get_model_metadata("customer_churn")
    assert "days_since_last_order" not in churn_meta.features


def test_m12_t04_baseline_model_training():
    """M12-T04: Baseline model training and performance logging for all models."""
    churn_meta = pred_service.get_model_metadata("customer_churn")
    assert churn_meta.baseline_algorithm == "LogisticRegression"
    assert "roc_auc" in churn_meta.baseline_metrics
    assert churn_meta.baseline_metrics["roc_auc"] > 0.50

    sales_meta = pred_service.get_model_metadata("sales_forecast")
    assert "DummyRegressor" in sales_meta.baseline_algorithm
    assert "mae" in sales_meta.baseline_metrics
    assert sales_meta.baseline_metrics["mae"] > 0.0


def test_m12_t05_candidate_comparison():
    """M12-T05: Candidate vs baseline model comparison demonstrating evaluated benchmark."""
    sales_meta = pred_service.get_model_metadata("sales_forecast")
    # Candidate Random Forest must outperform naive mean baseline MAE
    cand_mae = sales_meta.candidate_metrics["mae"]
    base_mae = sales_meta.baseline_metrics["mae"]
    assert cand_mae < base_mae, (
        f"Candidate MAE ({cand_mae}) should be lower than baseline MAE ({base_mae})"
    )

    demand_meta = pred_service.get_model_metadata("product_demand")
    cand_demand_mae = demand_meta.candidate_metrics["mae"]
    base_demand_mae = demand_meta.baseline_metrics["mae"]
    assert cand_demand_mae < base_demand_mae, (
        f"Demand candidate MAE ({cand_demand_mae}) should be < baseline MAE ({base_demand_mae})"
    )


def test_m12_t06_regression_forecasting_metrics():
    """M12-T06: Regression forecasting metrics (MAE, RMSE, MAPE) with mathematical consistency."""
    sales_meta = pred_service.get_model_metadata("sales_forecast")
    metrics = sales_meta.candidate_metrics
    assert "mae" in metrics
    assert "rmse" in metrics
    assert "mape" in metrics

    # Mathematically, RMSE >= MAE for any non-trivial error distribution
    assert metrics["rmse"] >= metrics["mae"], (
        f"RMSE ({metrics['rmse']}) must be >= MAE ({metrics['mae']})"
    )


def test_m12_t07_classification_metrics():
    """M12-T07: Classification metrics (Precision, Recall, F1, ROC-AUC) on holdout set."""
    churn_meta = pred_service.get_model_metadata("customer_churn")
    metrics = churn_meta.candidate_metrics
    assert "accuracy" in metrics
    assert "precision" in metrics
    assert "recall" in metrics
    assert "f1" in metrics
    assert "roc_auc" in metrics

    for key, val in metrics.items():
        assert 0.0 <= val <= 1.0, f"Metric {key} = {val} outside valid range [0, 1]"
    assert metrics["roc_auc"] >= 0.65, (
        f"ROC-AUC {metrics['roc_auc']} below acceptable threshold 0.65"
    )


def test_m12_t08_overfitting_check():
    """M12-T08: Generalization gap evaluation between train and holdout test set."""
    churn_meta = pred_service.get_model_metadata("customer_churn")
    assert churn_meta.overfitting_gap is not None
    # Generalization gap between train and test ROC-AUC should be reasonable (< 0.35)
    assert abs(churn_meta.overfitting_gap) < 0.35, (
        f"Overfitting gap {churn_meta.overfitting_gap} exceeds acceptable boundary."
    )


def test_m12_t09_repeatable_training():
    """M12-T09: Repeatable training with fixed random seed produces identical metrics."""
    with SessionLocal() as db:
        meta1 = train_customer_churn_model(db, random_state=42)
        meta2 = train_customer_churn_model(db, random_state=42)

    assert meta1["candidate_metrics"] == meta2["candidate_metrics"], (
        "Training metrics must be deterministic."
    )
    assert meta1["baseline_metrics"] == meta2["baseline_metrics"], (
        "Baseline metrics must be deterministic."
    )


def test_m12_t10_model_metadata_persistence():
    """M12-T10: Model metadata saved as valid structured JSON in artifacts/model_metadata/."""
    for model_id in ["customer_churn", "sales_forecast", "product_demand"]:
        meta_file = METADATA_DIR / f"{model_id}.json"
        assert meta_file.exists(), f"Metadata file {meta_file} not found."
        with open(meta_file, encoding="utf-8") as f:
            data = json.load(f)
        assert data["model_id"] == model_id
        assert "features" in data
        assert "sample_size_train" in data
        assert "sample_size_test" in data
        assert "trained_at" in data


def test_m12_t11_model_loading():
    """M12-T11: Model artifact persistence and clean in-memory loading."""
    for model_id in ["customer_churn", "sales_forecast", "product_demand"]:
        model_file = MODELS_DIR / f"{model_id}.joblib"
        assert model_file.exists(), f"Artifact {model_file} not found."

        pipeline = pred_service._get_or_load_pipeline(model_id)
        assert "model" in pipeline
        assert "scaler" in pipeline


def test_m12_t12_prediction_api_endpoints(client: TestClient, analyst_headers: dict[str, str]):
    """M12-T12: Live prediction API endpoints with RBAC enforcement (predictions.view)."""
    # 1. Churn Inference API
    churn_payload = {
        "tenure_days": 365,
        "order_count": 8,
        "total_spend": 24000.0,
        "avg_order_value": 3000.0,
        "days_since_last_order": 45,
        "returns_count": 0,
        "customer_type": "B2B",
        "acquisition_channel": "Direct",
    }
    res = client.post(
        "/api/v1/predictions/churn/predict", json=churn_payload, headers=analyst_headers
    )
    assert res.status_code == 200
    data = res.json()["data"]
    assert "churn_probability" in data
    assert 0.0 <= data["churn_probability"] <= 1.0
    assert data["risk_tier"] in ["Low", "Medium", "High"]
    assert len(data["contributing_factors"]) >= 1

    # 2. Sales Forecast API
    res = client.get("/api/v1/predictions/sales/forecast?horizon_days=30", headers=analyst_headers)
    assert res.status_code == 200
    fdata = res.json()["data"]
    assert fdata["horizon_days"] == 30
    assert len(fdata["forecast_series"]) == 30
    assert fdata["total_forecasted_revenue"] > 0.0
    for pt in fdata["forecast_series"]:
        assert pt["lower_bound_95"] <= pt["forecasted_revenue"] <= pt["upper_bound_95"]

    # 3. Product Demand API
    res = client.get("/api/v1/predictions/demand/forecast?limit=10", headers=analyst_headers)
    assert res.status_code == 200
    pdata = res.json()["data"]
    assert pdata["total_products"] > 0
    assert len(pdata["products"]) <= 10


def test_m12_t13_invalid_inference_input(client: TestClient, analyst_headers: dict[str, str]):
    """M12-T13: Input validation returns HTTP 422 for invalid bounds and negative values."""
    # Negative tenure
    invalid_payload = {
        "tenure_days": -5,
        "order_count": 8,
        "total_spend": 24000.0,
        "avg_order_value": 3000.0,
    }
    res = client.post(
        "/api/v1/predictions/churn/predict", json=invalid_payload, headers=analyst_headers
    )
    assert res.status_code == 422

    # Invalid horizon (> 365)
    res = client.get("/api/v1/predictions/sales/forecast?horizon_days=500", headers=analyst_headers)
    assert res.status_code == 422


def test_m12_t14_batch_vs_api_consistency(client: TestClient, analyst_headers: dict[str, str]):
    """M12-T14: Batch inference outputs strictly match single-record inference outputs."""
    records = [
        {
            "tenure_days": 120,
            "order_count": 2,
            "total_spend": 1200.0,
            "avg_order_value": 600.0,
            "returns_count": 1,
            "customer_type": "B2C",
            "acquisition_channel": "Online",
        },
        {
            "tenure_days": 700,
            "order_count": 25,
            "total_spend": 85000.0,
            "avg_order_value": 3400.0,
            "returns_count": 0,
            "customer_type": "Enterprise",
            "acquisition_channel": "Direct",
        },
    ]

    # Batch call
    batch_res = client.post(
        "/api/v1/predictions/churn/batch", json={"records": records}, headers=analyst_headers
    )
    assert batch_res.status_code == 200
    batch_results = batch_res.json()["data"]["results"]

    # Single calls
    single_results = []
    for rec in records:
        s_res = client.post("/api/v1/predictions/churn/predict", json=rec, headers=analyst_headers)
        assert s_res.status_code == 200
        single_results.append(s_res.json()["data"])

    assert len(batch_results) == len(single_results)
    for b_item, s_item in zip(batch_results, single_results, strict=False):
        assert abs(b_item["churn_probability"] - s_item["churn_probability"]) < 1e-4
        assert b_item["risk_tier"] == s_item["risk_tier"]
        assert b_item["is_churn_predicted"] == s_item["is_churn_predicted"]


def test_m12_t15_prediction_ui_backend_endpoints(
    client: TestClient, analyst_headers: dict[str, str], viewer_headers: dict[str, str]
):
    """M12-T15: Endpoints serving UI views (high-risk list, model listing, RBAC access denial)."""
    # High-risk customer feed
    res = client.get("/api/v1/predictions/churn/high-risk?limit=15", headers=analyst_headers)
    assert res.status_code == 200
    hr_data = res.json()["data"]
    assert len(hr_data) <= 15
    for c in hr_data:
        assert "churn_probability" in c
        assert "risk_tier" in c

    # Models overview for governance UI
    res = client.get("/api/v1/predictions/models", headers=analyst_headers)
    assert res.status_code == 200
    models_data = res.json()["data"]
    assert len(models_data) >= 3

    # General viewer lacks predictions.view -> HTTP 403 Forbidden
    denied = client.get("/api/v1/predictions/models", headers=viewer_headers)
    assert denied.status_code == 403


def test_m12_t16_prediction_limitations_notice(client: TestClient, analyst_headers: dict[str, str]):
    """M12-T16: Mandatory governance notice on assumptions present on all outputs."""
    res = client.get("/api/v1/predictions/sales/forecast?horizon_days=30", headers=analyst_headers)
    assert res.status_code == 200
    assert "governance_notice" in res.json()["data"]
    assert len(res.json()["data"]["governance_notice"]) > 10

    res = client.post(
        "/api/v1/predictions/churn/predict",
        json={
            "tenure_days": 100,
            "order_count": 1,
            "total_spend": 500.0,
            "avg_order_value": 500.0,
        },
        headers=analyst_headers,
    )
    assert res.status_code == 200
    assert "governance_notice" in res.json()["data"]


def test_m12_t17_missing_model_artifact_handling(
    client: TestClient, analyst_headers: dict[str, str]
):
    """M12-T17: Missing model artifact returns HTTP 404/503 gracefully without 500 crash."""
    res = client.get("/api/v1/predictions/models/non_existent_model", headers=analyst_headers)
    assert res.status_code == 404
    error_msg = res.json().get("error", {}).get("message", "") or res.json().get("detail", "")
    assert "not found" in error_msg.lower()
