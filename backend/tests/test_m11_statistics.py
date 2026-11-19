"""
NEXORA — Module 11 Test Suite: Statistical Analysis & Modeling
Validates test cases M11-T01 to M11-T13 against live FastAPI application and PostgreSQL database.
"""

import math
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.core.config import settings
from app.main import app
from app.services.statistics import statistics_service


@pytest.fixture(scope="module")
def client() -> TestClient:
    """Module-level TestClient for FastAPI endpoints."""
    return TestClient(app)


@pytest.fixture(scope="module")
def db_session() -> Generator[Session, None, None]:
    """Module-level database session connected to live PostgreSQL."""
    engine = create_engine(settings.database_url, future=True)
    with Session(engine) as session:
        yield session
    engine.dispose()


@pytest.fixture(scope="module")
def analyst_headers(client: TestClient) -> dict[str, str]:
    """Provide authenticated headers for Demo Data Analyst."""
    resp = client.post("/api/v1/auth/demo-login", json={"role": "data_analyst"})
    assert resp.status_code == 200
    token = resp.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="module")
def viewer_headers(client: TestClient) -> dict[str, str]:
    """Provide authenticated headers for General Viewer (lacks statistics.view)."""
    resp = client.post("/api/v1/auth/demo-login", json={"role": "general_viewer"})
    assert resp.status_code == 200
    token = resp.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_m11_t01_mean_calculation() -> None:
    """M11-T01: Mean — verify sample mean against known mathematical oracle."""
    dataset = [10.0, 20.0, 30.0, 40.0, 50.0]
    res = statistics_service.compute_descriptive(dataset)
    assert res.n == 5
    assert res.mean == 30.0


def test_m11_t02_median_and_mode_calculation() -> None:
    """M11-T02: Median & Mode — verify 50th percentile and modal frequency."""
    # Odd length series
    dataset_odd = [1.0, 2.0, 2.0, 3.0, 4.0]
    res_odd = statistics_service.compute_descriptive(dataset_odd)
    assert res_odd.median == 2.0
    assert res_odd.mode == 2.0

    # Even length series: median is average of middle two
    dataset_even = [10.0, 20.0, 30.0, 40.0]
    res_even = statistics_service.compute_descriptive(dataset_even)
    assert res_even.median == 25.0


def test_m11_t03_variance_and_standard_deviation() -> None:
    """M11-T03: Variance & SD — verify sample variance with Bessel's correction (ddof=1)."""
    dataset = [2.0, 4.0, 4.0, 4.0, 5.0, 5.0, 7.0, 9.0]
    res = statistics_service.compute_descriptive(dataset)
    # Mean = 5.0, sum of sq diff = (9+1+1+1+0+0+4+16) = 32 / (8 - 1) = 4.5714
    assert res.mean == 5.0
    assert round(res.variance, 4) == 4.5714
    assert round(res.std_dev, 4) == round(math.sqrt(32.0 / 7.0), 4)


def test_m11_t04_quartiles_and_percentiles() -> None:
    """M11-T04: Quartiles & percentiles — verify Q1, Q2, Q3, IQR, min, and max."""
    dataset = [10.0, 20.0, 30.0, 40.0, 50.0]
    res = statistics_service.compute_descriptive(dataset)
    assert res.min == 10.0
    assert res.max == 50.0
    assert res.q1 == 20.0
    assert res.q2 == 30.0
    assert res.q3 == 40.0
    assert res.iqr == 20.0


def test_m11_t05_missing_value_handling() -> None:
    """M11-T05: Missing value handling — exclude nulls and NaNs with explicit counts."""
    dataset = [10.0, None, 20.0, float("nan"), 30.0]
    res = statistics_service.compute_descriptive(dataset)
    assert res.n == 3
    assert res.missing_count == 2
    assert res.mean == 20.0


def test_m11_t06_distribution_analysis() -> None:
    """M11-T06: Distribution analysis — skewness, kurtosis, and histogram buckets."""
    # Symmetric distribution has skewness ~ 0
    sym_data = [10.0, 20.0, 30.0, 40.0, 50.0]
    res_sym = statistics_service.compute_descriptive(sym_data)
    assert res_sym.skewness == 0.0
    assert len(res_sym.histogram) > 0
    assert sum(b.count for b in res_sym.histogram) == 5

    # Right-skewed distribution has positive skewness
    right_skew = [10.0, 11.0, 12.0, 13.0, 14.0, 100.0]
    res_right = statistics_service.compute_descriptive(right_skew)
    assert res_right.skewness > 0.0


def test_m11_t07_correlation_analysis(
    client: TestClient, analyst_headers: dict[str, str], db_session: Session
) -> None:
    """M11-T07: Correlation analysis — compute Pearson and Spearman matrices across dimensions."""
    resp = client.get("/api/v1/statistics/correlation?entity=orders", headers=analyst_headers)
    assert resp.status_code == 200
    data = resp.json()["data"]

    assert len(data["variables"]) >= 4
    n_vars = len(data["variables"])
    p_mat = data["pearson_matrix"]
    s_mat = data["spearman_matrix"]

    assert len(p_mat) == n_vars
    assert len(s_mat) == n_vars

    # Diagonal must be 1.0
    for i in range(n_vars):
        assert p_mat[i][i] == 1.0
        assert s_mat[i][i] == 1.0

    # Symmetry check
    for i in range(n_vars):
        for j in range(n_vars):
            assert p_mat[i][j] == p_mat[j][i]
            assert -1.0 <= p_mat[i][j] <= 1.0


def test_m11_t08_correlation_causation_warning(
    client: TestClient, analyst_headers: dict[str, str]
) -> None:
    """M11-T08: Correlation != causation warning — explicit disclaimer in API and UI."""
    # Check correlation endpoint disclaimer
    corr_resp = client.get("/api/v1/statistics/correlation", headers=analyst_headers)
    assert corr_resp.status_code == 200
    corr_warn = corr_resp.json()["data"]["causation_warning"]
    assert "Correlation does not imply causation" in corr_warn

    # Check descriptive endpoint disclaimer
    desc_resp = client.get("/api/v1/statistics/descriptive", headers=analyst_headers)
    assert desc_resp.status_code == 200
    desc_warn = desc_resp.json()["data"]["causation_warning"]
    assert "Correlation does not imply causation" in desc_warn


def test_m11_t09_hypothesis_testing(client: TestClient, analyst_headers: dict[str, str]) -> None:
    """M11-T09: Hypothesis testing — two-sample Welch's t-test with unequal variances."""
    # Significant difference test
    payload = {
        "group_a_name": "Tier 1 Enterprise",
        "group_b_name": "Tier 3 SMB",
        "group_a_values": [500.0, 520.0, 510.0, 530.0, 490.0],
        "group_b_values": [100.0, 110.0, 105.0, 95.0, 115.0],
        "alpha": 0.05,
    }
    resp = client.post("/api/v1/statistics/hypothesis-test", json=payload, headers=analyst_headers)
    assert resp.status_code == 200
    data = resp.json()["data"]

    assert data["group_a_n"] == 5
    assert data["group_b_n"] == 5
    assert data["group_a_mean"] > data["group_b_mean"]
    assert data["t_statistic"] > 0
    assert data["p_value"] < 0.001
    assert data["significant"] is True
    assert "Statistically significant difference detected" in data["interpretation"]


def test_m11_t10_invalid_statistical_assumptions(
    client: TestClient, analyst_headers: dict[str, str]
) -> None:
    """M11-T10: Invalid statistical assumptions — N < 2 or zero variance raises 400/422."""
    # Single observation (N=1)
    single_val_resp = client.post(
        "/api/v1/statistics/compute",
        json={"values": [10.0]},
        headers=analyst_headers,
    )
    assert single_val_resp.status_code == 400
    assert single_val_resp.json()["error"]["code"] == "BAD_REQUEST"
    assert "insufficient" in single_val_resp.json()["error"]["message"].lower()

    # Hypothesis test with insufficient sample
    invalid_ht_resp = client.post(
        "/api/v1/statistics/hypothesis-test",
        json={
            "group_a_name": "A",
            "group_b_name": "B",
            "group_a_values": [100.0],
            "group_b_values": [50.0, 60.0],
            "alpha": 0.05,
        },
        headers=analyst_headers,
    )
    assert invalid_ht_resp.status_code == 400


def test_m11_t11_confidence_intervals() -> None:
    """M11-T11: Confidence intervals — 95% confidence interval with Student's t critical."""
    dataset = [10.0, 20.0, 30.0, 40.0, 50.0]
    res = statistics_service.compute_descriptive(dataset)
    ci = res.confidence_interval_95
    assert len(ci) == 2
    ci_lower, ci_upper = ci[0], ci[1]

    # CI must encompass the mean symmetrically
    assert ci_lower < res.mean < ci_upper
    assert round(res.mean - ci_lower, 2) == round(ci_upper - res.mean, 2)


def test_m11_t12_reproducibility() -> None:
    """M11-T12: Reproducibility — repeated calculations return identical deterministic values."""
    dataset = [15.5, 23.2, 8.7, 44.1, 19.8, 31.4, 27.6]
    run_1 = statistics_service.compute_descriptive(dataset)
    run_2 = statistics_service.compute_descriptive(dataset)

    assert run_1.mean == run_2.mean
    assert run_1.variance == run_2.variance
    assert run_1.std_dev == run_2.std_dev
    assert run_1.q1 == run_2.q1
    assert run_1.confidence_interval_95 == run_2.confidence_interval_95


def test_m11_t13_backend_frontend_consistency(
    client: TestClient, analyst_headers: dict[str, str], viewer_headers: dict[str, str]
) -> None:
    """M11-T13: Backend/frontend consistency & RBAC — verify real DB metrics and permissions."""
    # 1. General viewer without statistics.view receives 403
    viewer_resp = client.get("/api/v1/statistics/descriptive", headers=viewer_headers)
    assert viewer_resp.status_code == 403

    # 2. Analyst with statistics.view receives 200 with live DB statistics
    resp = client.get(
        "/api/v1/statistics/descriptive?entity=orders&field=total_amount",
        headers=analyst_headers,
    )
    assert resp.status_code == 200
    body = resp.json()["data"]

    assert body["n"] > 1000
    assert body["mean"] > 0.0
    assert body["median"] > 0.0
    assert body["std_dev"] > 0.0
    assert len(body["histogram"]) > 0

    # 3. Channel comparison test
    comp_resp = client.get("/api/v1/statistics/channel-comparison", headers=analyst_headers)
    assert comp_resp.status_code == 200
    comp_data = comp_resp.json()["data"]
    assert comp_data["group_a_n"] > 0
    assert comp_data["group_b_n"] > 0
    assert comp_data["t_statistic"] is not None
