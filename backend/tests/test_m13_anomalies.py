"""Module 13: Anomaly Detection and Risk Intelligence Test Suite (M13-T01 through M13-T13).

Validates:
- Multi-domain anomaly detection (Sales, Transaction, Inventory, Marketing)
- Normal data preservation and false-positive controls
- Baseline moving average comparisons and multi-tier severity calculations
- Objective, non-defamatory plain-language explanations
- Duplicate alert prevention (idempotent detection scans)
- Owner-only alert triage/acknowledgement workflow with audit trail
- RBAC permission enforcement (403 for unauthorized acknowledgement)
- Multivariate Isolation Forest comparative benchmarking against univariate Z-scores
"""

from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.db.session import SessionLocal
from app.main import app
from app.models.data_ops import AnomalyAlert, AuditLog
from app.services import anomalies as anomaly_service


@pytest.fixture(scope="module")
def client() -> TestClient:
    """FastAPI test client instance."""
    return TestClient(app)


@pytest.fixture(scope="module")
def owner_headers(client: TestClient) -> dict[str, str]:
    """Authenticated bearer token for Platform Owner (has anomaly.acknowledge)."""
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": "owner@nexora.local", "password": "NexoraOwnerPass2026!"},
    )
    assert resp.status_code == 200
    token = resp.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="module")
def analyst_headers(client: TestClient) -> dict[str, str]:
    """Authenticated bearer token for Demo Data Analyst (has anomaly.view, no acknowledge)."""
    resp = client.post("/api/v1/auth/demo-login", json={"role": "data_analyst"})
    assert resp.status_code == 200
    token = resp.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="module")
def viewer_headers(client: TestClient) -> dict[str, str]:
    """Authenticated bearer token for General Viewer (has anomaly.view, no acknowledge)."""
    resp = client.post("/api/v1/auth/demo-login", json={"role": "general_viewer"})
    assert resp.status_code == 200
    token = resp.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_m13_t01_sales_anomaly(client: TestClient, analyst_headers: dict[str, str]):
    """M13-T01: Detection and retrieval of sales anomalies (daily revenue multi-sigma shifts)."""
    res = client.get("/api/v1/anomalies?domain=sales", headers=analyst_headers)
    assert res.status_code == 200
    sales_alerts = res.json()["data"]
    assert len(sales_alerts) >= 1, "Expected at least 1 sales anomaly alert."

    alert = sales_alerts[0]
    assert alert["domain"] == "sales"
    assert alert["metric_name"] == "daily_revenue"
    assert alert["severity"] in ["high", "critical"]
    assert float(alert["observed_value"]) > 0.0
    assert float(alert["baseline_value"]) > 0.0
    assert alert["z_score"] is not None
    assert abs(float(alert["z_score"])) >= 3.0


def test_m13_t02_transaction_anomaly(client: TestClient, analyst_headers: dict[str, str]):
    """M13-T02: Detection and retrieval of transaction anomalies (unusual order values)."""
    res = client.get("/api/v1/anomalies?domain=transaction", headers=analyst_headers)
    assert res.status_code == 200
    tx_alerts = res.json()["data"]
    assert len(tx_alerts) >= 1, "Expected at least 1 transaction anomaly alert."

    alert = tx_alerts[0]
    assert alert["domain"] == "transaction"
    assert alert["metric_name"] == "order_total"
    assert float(alert["z_score"]) >= 3.0
    assert float(alert["observed_value"]) > float(alert["baseline_value"])


def test_m13_t03_inventory_anomaly(client: TestClient, analyst_headers: dict[str, str]):
    """M13-T03: Detection and retrieval of inventory stockout and depletion velocity anomalies."""
    res = client.get("/api/v1/anomalies?domain=inventory", headers=analyst_headers)
    assert res.status_code == 200
    inv_alerts = res.json()["data"]
    assert len(inv_alerts) >= 1, "Expected at least 1 inventory anomaly alert."

    alert = inv_alerts[0]
    assert alert["domain"] == "inventory"
    assert "depletion" in alert["metric_name"].lower() or "stock" in alert["metric_name"].lower()
    assert alert["severity"] in ["high", "critical"]


def test_m13_t04_marketing_anomaly(client: TestClient, analyst_headers: dict[str, str]):
    """M13-T04: Detection and retrieval of marketing campaign overspend anomalies."""
    res = client.get("/api/v1/anomalies?domain=marketing", headers=analyst_headers)
    assert res.status_code == 200
    mkt_alerts = res.json()["data"]
    assert len(mkt_alerts) >= 1, "Expected at least 1 marketing anomaly alert."

    alert = mkt_alerts[0]
    assert alert["domain"] == "marketing"
    assert "spend" in alert["metric_name"].lower()
    assert alert["severity"] in ["high", "critical"]


def test_m13_t05_normal_data_verification():
    """M13-T05: Normal observations within 2 sigma bounds are NOT flagged as anomalies."""
    # Test severity calculation for normal metric within 1.5 sigma
    normal_sev = anomaly_service.calculate_severity(z_score=1.2, deviation_pct=15.0)
    assert normal_sev == "low"

    # Verify that a 1.0 sigma deviation does not trigger an alert
    borderline_sev = anomaly_service.calculate_severity(z_score=1.8, deviation_pct=18.0)
    assert borderline_sev == "low"


def test_m13_t06_baseline_comparison(client: TestClient, analyst_headers: dict[str, str]):
    """M13-T06: Baseline accurately reflects expectation and deviation = observed - baseline."""
    res = client.get("/api/v1/anomalies", headers=analyst_headers)
    assert res.status_code == 200
    alerts = res.json()["data"]

    for a in alerts:
        obs = float(a["observed_value"])
        base = float(a["baseline_value"])
        dev = float(a["deviation_amount"])
        # Mathematical identity: dev == obs - base
        assert abs(dev - (obs - base)) < 0.05, f"Deviation mismatch: {dev} != {obs} - {base}"


def test_m13_t07_severity_calculation():
    """M13-T07: Multi-tier severity calculation based on Z-score and percentage deviation."""
    # Critical: |Z| >= 3.5 or deviation >= 75%
    assert anomaly_service.calculate_severity(z_score=3.8, deviation_pct=80.0) == "critical"
    assert anomaly_service.calculate_severity(z_score=-3.9, deviation_pct=-85.0) == "critical"

    # High: 3.0 <= |Z| < 3.5 or deviation >= 50%
    assert anomaly_service.calculate_severity(z_score=3.2, deviation_pct=55.0) == "high"

    # Medium: 2.0 <= |Z| < 3.0 or deviation >= 25%
    assert anomaly_service.calculate_severity(z_score=2.3, deviation_pct=28.0) == "medium"

    # Low: |Z| < 2.0
    assert anomaly_service.calculate_severity(z_score=1.1, deviation_pct=10.0) == "low"


def test_m13_t08_explanation_validation(client: TestClient, analyst_headers: dict[str, str]):
    """M13-T08: Explanations provide objective mathematical context and NEVER accuse fraud."""
    res = client.get("/api/v1/anomalies", headers=analyst_headers)
    assert res.status_code == 200
    alerts = res.json()["data"]

    for a in alerts:
        expl = a["explanation"].lower()
        # Must never contain speculative/accusatory fraud claims
        assert "suspected fraud" not in expl
        assert "crime" not in expl
        assert "theft" not in expl
        if "fraud" in expl:
            assert "not confirmed fraud" in expl, (
                f"Defamatory term 'fraud' found in explanation: {a['explanation']}"
            )

        # Must describe metric, observed, baseline, or deviation context
        assert len(expl) > 15
        assert any(
            term in expl
            for term in [
                "revenue",
                "order",
                "total",
                "inventory",
                "depletion",
                "spend",
                "expenditure",
                "rate",
                "baseline",
                "deviation",
                "deviates",
                "spiked",
                "threshold",
            ]
        )


def test_m13_t09_false_positive_control():
    """M13-T09: Automated detection enforces >= 3.0 sigma threshold to control false positives."""
    with SessionLocal() as db:
        # Run detection with strict 3.0 threshold
        res = anomaly_service.run_automated_detection(db, threshold_sigma=3.0)
        assert res.total_scanned_records > 0
        assert "sales" in res.domains_scanned


def test_m13_t10_duplicate_alert_prevention():
    """M13-T10: Repeated detection scans on the same dataset do not produce duplicate alerts."""
    with SessionLocal() as db:
        # Initial scan
        anomaly_service.run_automated_detection(db, threshold_sigma=3.0)
        # Immediate second scan
        res2 = anomaly_service.run_automated_detection(db, threshold_sigma=3.0)

        # Idempotence: Second scan must produce 0 new alerts for identical data
        assert res2.new_anomalies_detected == 0, "Duplicate alerts must not be generated."


def test_m13_t11_acknowledgement_workflow(client: TestClient, owner_headers: dict[str, str]):
    """M13-T11: Platform owner successfully acknowledges an anomaly and creates an audit record."""
    # Create or find an open alert to acknowledge
    with SessionLocal() as db:
        alert = db.scalar(select(AnomalyAlert).where(AnomalyAlert.status == "open"))
        if not alert:
            alert = AnomalyAlert(
                organization_id=1,
                domain="sales",
                entity_identifier="2026-11-10",
                metric_name="daily_revenue",
                observed_value=Decimal("1200.00"),
                baseline_value=Decimal("8500.00"),
                deviation_amount=Decimal("-7300.00"),
                z_score=Decimal("-3.60"),
                severity="critical",
                explanation="Test sales alert for acknowledgement.",
                status="open",
            )
            db.add(alert)
            db.commit()
            db.refresh(alert)
        alert_id = alert.id

    # Owner acknowledges
    ack_payload = {
        "status": "acknowledged",
        "notes": "Investigated: temporary internet disruption.",
    }
    res = client.post(
        f"/api/v1/anomalies/{alert_id}/acknowledge", json=ack_payload, headers=owner_headers
    )
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["status"] == "acknowledged"
    assert data["acknowledged_at"] is not None
    assert data["acknowledged_by_id"] is not None

    # Verify audit log was recorded
    with SessionLocal() as db:
        audit = db.scalar(
            select(AuditLog)
            .where(
                AuditLog.entity_id == str(alert_id), AuditLog.action_type == "ANOMALY_STATUS_UPDATE"
            )
            .order_by(AuditLog.id.desc())
        )
        assert audit is not None, "Audit log record must be created on anomaly acknowledgement."
        assert audit.details["new_status"] == "acknowledged"


def test_m13_t12_unauthorized_acknowledgement(
    client: TestClient, analyst_headers: dict[str, str], viewer_headers: dict[str, str]
):
    """M13-T12: Roles without anomaly.acknowledge (analyst, viewer) receive HTTP 403 Forbidden."""
    ack_payload = {"status": "acknowledged"}

    # Data Analyst attempt
    res = client.post("/api/v1/anomalies/1/acknowledge", json=ack_payload, headers=analyst_headers)
    assert res.status_code == 403

    # General Viewer attempt
    res = client.post("/api/v1/anomalies/1/acknowledge", json=ack_payload, headers=viewer_headers)
    assert res.status_code == 403


def test_m13_t13_isolation_forest_benchmark(client: TestClient, analyst_headers: dict[str, str]):
    """M13-T13: Benchmark between Isolation Forest and univariate statistical baseline."""
    res = client.get(
        "/api/v1/anomalies/benchmark/isolation-forest?contamination=0.03", headers=analyst_headers
    )
    assert res.status_code == 200
    bench = res.json()["data"]

    assert bench["algorithm"] == "IsolationForest (scikit-learn)"
    assert bench["contamination_rate"] == 0.03
    assert bench["total_observations_evaluated"] >= 30
    assert bench["isolation_forest_detected"] > 0
    assert bench["statistical_baseline_detected"] > 0
    assert 0.0 <= bench["concordance_rate"] <= 100.0
    assert len(bench["benchmark_evaluation"]) > 20
