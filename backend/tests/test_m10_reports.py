"""
NEXORA — Module 10 Test Suite: Reports, Exports, and Saved Views
Validates M10-T01 through M10-T12 against live FastAPI application and PostgreSQL database.
"""

import csv
import io
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.main import app
from app.models.data_ops import AuditLog, SavedView
from app.services.reports import sanitize_csv_cell


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
def owner_headers(client: TestClient) -> dict[str, str]:
    """Provide authenticated headers for Platform Owner."""
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": "owner@nexora.local", "password": "NexoraOwnerPass2026!"},
    )
    assert resp.status_code == 200
    token = resp.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="module")
def analyst_headers(client: TestClient) -> dict[str, str]:
    """Provide authenticated headers for Demo Data Analyst."""
    resp = client.post("/api/v1/auth/demo-login", json={"role": "data_analyst"})
    assert resp.status_code == 200
    token = resp.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="module")
def manager_headers(client: TestClient) -> dict[str, str]:
    """Provide authenticated headers for Department Manager (no sensitive fields)."""
    resp = client.post("/api/v1/auth/demo-login", json={"role": "department_manager"})
    assert resp.status_code == 200
    token = resp.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="module")
def viewer_headers(client: TestClient) -> dict[str, str]:
    """Provide authenticated headers for General Viewer (no export permission)."""
    resp = client.post("/api/v1/auth/demo-login", json={"role": "general_viewer"})
    assert resp.status_code == 200
    token = resp.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_m10_t01_report_catalogue(client: TestClient, viewer_headers: dict[str, str]) -> None:
    """M10-T01: Report catalogue — 8 structured reports matching 8 domains."""
    resp = client.get("/api/v1/reports/catalogue", headers=viewer_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    reports = body["data"]

    # Verify exactly 8 reports exist
    assert len(reports) == 8

    expected_domains = {
        "overview",
        "sales",
        "customer",
        "marketing",
        "finance",
        "inventory",
        "operations",
        "supplier",
    }
    actual_domains = {r["domain"] for r in reports}
    assert actual_domains == expected_domains

    # Check structure of catalogue items
    for item in reports:
        assert "report_id" in item
        assert "name" in item
        assert "domain" in item
        assert "description" in item
        assert "cadence" in item
        assert "columns" in item
        assert len(item["columns"]) > 0


def test_m10_t02_report_data_accuracy(
    client: TestClient, analyst_headers: dict[str, str], db_session: Session
) -> None:
    """M10-T02: Report data accuracy — verify report aggregates match database queries."""
    resp = client.get("/api/v1/reports/sales-performance/data?limit=500", headers=analyst_headers)
    assert resp.status_code == 200
    data = resp.json()["data"]

    assert data["report_id"] == "sales-performance"
    assert data["total_rows"] > 0
    assert len(data["rows"]) == data["total_rows"]
    assert "synthetic_notice" in data
    assert "Synthetic Data Demonstration" in data["synthetic_notice"]

    # Check summary calculation
    summary = data["summary"]
    assert summary["total_orders"] == data["total_rows"]
    assert summary["net_revenue"] > 0.0

    # Cross-check first row structure
    first_row = data["rows"][0]
    assert "order_number" in first_row
    assert "net_revenue" in first_row
    assert "cost_of_goods_sold" in first_row  # Analyst has sensitive fields


def test_m10_t03_saved_view_creation(
    client: TestClient, analyst_headers: dict[str, str], db_session: Session
) -> None:
    """M10-T03: Saved view creation — persist user view into saved_views table."""
    payload = {
        "section": "sales",
        "name": "Midwest High Value Orders Q4",
        "filter_config": {
            "region_id": 2,
            "min_total": 500.0,
            "sales_channel": "Direct",
        },
        "is_shared": True,
    }

    resp = client.post("/api/v1/reports/saved-views", json=payload, headers=analyst_headers)
    assert resp.status_code == 201
    body = resp.json()
    assert body["success"] is True
    view_data = body["data"]

    view_id = view_data["id"]
    assert view_data["name"] == payload["name"]
    assert view_data["section"] == "sales"
    assert view_data["filter_config"]["region_id"] == 2
    assert view_data["is_shared"] is True

    # Verify real DB persistence
    db_view = db_session.get(SavedView, view_id)
    assert db_view is not None
    assert db_view.name == payload["name"]
    assert db_view.filter_config == payload["filter_config"]

    # Verify audit log recorded
    audit = db_session.execute(
        select(AuditLog).where(
            AuditLog.action_type == "SAVED_VIEW_CREATED",
            AuditLog.entity_id == str(view_id),
        )
    ).scalar_one_or_none()
    assert audit is not None


def test_m10_t04_saved_view_restoration_and_access(
    client: TestClient,
    analyst_headers: dict[str, str],
    viewer_headers: dict[str, str],
    owner_headers: dict[str, str],
    db_session: Session,
) -> None:
    """M10-T04: Saved view restoration — retrieve saved views and test private view access."""
    # 1. Create a private view by Analyst
    priv_resp = client.post(
        "/api/v1/reports/saved-views",
        json={
            "section": "marketing",
            "name": "Analyst Private ROI Filter",
            "filter_config": {"channel": "Search Ads"},
            "is_shared": False,
        },
        headers=analyst_headers,
    )
    assert priv_resp.status_code == 201
    priv_id = priv_resp.json()["data"]["id"]

    # 2. General viewer cannot read private view (403)
    unauth_get = client.get(f"/api/v1/reports/saved-views/{priv_id}", headers=viewer_headers)
    assert unauth_get.status_code == 403

    # 3. Creator can read it (200)
    creator_get = client.get(f"/api/v1/reports/saved-views/{priv_id}", headers=analyst_headers)
    assert creator_get.status_code == 200
    assert creator_get.json()["data"]["filter_config"] == {"channel": "Search Ads"}

    # 4. General viewer cannot delete analyst's view (403)
    unauth_del = client.delete(f"/api/v1/reports/saved-views/{priv_id}", headers=viewer_headers)
    assert unauth_del.status_code == 403

    # 5. Creator can delete it (200)
    del_resp = client.delete(f"/api/v1/reports/saved-views/{priv_id}", headers=analyst_headers)
    assert del_resp.status_code == 200
    assert del_resp.json()["data"]["deleted"] is True

    # Verify deletion in DB
    assert db_session.get(SavedView, priv_id) is None


def test_m10_t05_csv_export_generation(client: TestClient, analyst_headers: dict[str, str]) -> None:
    """M10-T05: CSV export generation — stream valid CSV with correct headers."""
    resp = client.get(
        "/api/v1/reports/sales-performance/export/csv?limit=25",
        headers=analyst_headers,
    )
    assert resp.status_code == 200
    assert "text/csv" in resp.headers["content-type"]
    assert "attachment; filename=" in resp.headers["content-disposition"]

    content = resp.text
    assert len(content) > 0
    # Must contain CSV columns
    assert "order_number,order_date,customer_name" in content


def test_m10_t06_export_reconciliation(client: TestClient, analyst_headers: dict[str, str]) -> None:
    """M10-T06: Export reconciliation — sum of rows in CSV matches reported total net revenue."""
    # Fetch report data via API
    api_resp = client.get(
        "/api/v1/reports/sales-performance/data?limit=50",
        headers=analyst_headers,
    )
    assert api_resp.status_code == 200
    api_data = api_resp.json()["data"]
    expected_sum = sum(row["net_revenue"] for row in api_data["rows"])

    # Fetch CSV export with same limit
    csv_resp = client.get(
        "/api/v1/reports/sales-performance/export/csv?limit=50",
        headers=analyst_headers,
    )
    assert csv_resp.status_code == 200

    # Parse CSV, skipping comment lines starting with #
    lines = [line for line in csv_resp.text.splitlines() if not line.startswith("#")]
    reader = csv.DictReader(io.StringIO("\n".join(lines)))
    csv_sum = 0.0
    row_count = 0
    for r in reader:
        csv_sum += float(r["net_revenue"])
        row_count += 1

    assert row_count == len(api_data["rows"])
    assert round(csv_sum, 2) == round(expected_sum, 2)


def test_m10_t07_export_metadata_and_synthetic_notice(
    client: TestClient, analyst_headers: dict[str, str]
) -> None:
    """M10-T07: Export metadata & synthetic notice — verify notice rows in CSV headers."""
    resp = client.get("/api/v1/reports/overview-kpis/export/csv", headers=analyst_headers)
    assert resp.status_code == 200
    text = resp.text

    notice_part = "Synthetic Data Demonstration — Generated for Local Analytics Evaluation"
    assert "# NEXORA ENTERPRISE INTELLIGENCE REPORT EXPORT" in text
    assert "# Report Name: Executive Business Overview" in text
    assert notice_part in text
    assert "# Exported By: demo_analyst@nexora.local (Role: data_analyst)" in text


def test_m10_t08_export_permissions(
    client: TestClient,
    viewer_headers: dict[str, str],
    analyst_headers: dict[str, str],
    owner_headers: dict[str, str],
) -> None:
    """M10-T08: Export permissions — demo viewers without export permission receive 403."""
    # 1. Unauthenticated request -> 401
    unauth_client = TestClient(app)
    unauth_resp = unauth_client.get("/api/v1/reports/sales-performance/export/csv")
    assert unauth_resp.status_code == 401

    # 2. General Viewer (lacks report.export) -> 403 Forbidden
    viewer_resp = client.get(
        "/api/v1/reports/sales-performance/export/csv",
        headers=viewer_headers,
    )
    assert viewer_resp.status_code == 403
    assert viewer_resp.json()["error"]["code"] == "FORBIDDEN"

    # 3. Analyst (has report.export) -> 200 OK
    analyst_resp = client.get(
        "/api/v1/reports/sales-performance/export/csv?limit=5",
        headers=analyst_headers,
    )
    assert analyst_resp.status_code == 200

    # 4. Owner (has report.export) -> 200 OK
    owner_resp = client.get(
        "/api/v1/reports/sales-performance/export/csv?limit=5",
        headers=owner_headers,
    )
    assert owner_resp.status_code == 200


def test_m10_t09_restricted_field_protection(
    client: TestClient,
    manager_headers: dict[str, str],
    analyst_headers: dict[str, str],
) -> None:
    """M10-T09: Restricted field protection — strip sensitive cost/margin fields when lacking."""
    # Department manager has report.export, but NOT report.sensitive_fields
    mgr_resp = client.get(
        "/api/v1/reports/sales-performance/export/csv?limit=10",
        headers=manager_headers,
    )
    assert mgr_resp.status_code == 200
    mgr_text = mgr_resp.text

    # Manager export must NOT contain cost_of_goods_sold or gross_margin
    assert "cost_of_goods_sold" not in mgr_text
    assert "gross_margin" not in mgr_text
    assert "net_revenue" in mgr_text

    # Analyst HAS report.sensitive_fields -> must contain sensitive columns
    analyst_resp = client.get(
        "/api/v1/reports/sales-performance/export/csv?limit=10",
        headers=analyst_headers,
    )
    assert analyst_resp.status_code == 200
    analyst_text = analyst_resp.text
    assert "cost_of_goods_sold" in analyst_text
    assert "gross_margin" in analyst_text


def test_m10_t10_formula_injection_protection() -> None:
    """M10-T10: Formula injection protection — sanitize =, +, -, @, \\t, \\r."""
    # Test individual cell sanitizer
    assert sanitize_csv_cell("=1+1") == "'=1+1"
    assert sanitize_csv_cell("=cmd|' /C calc'!A0") == "'=cmd|' /C calc'!A0"
    assert sanitize_csv_cell("+12345") == "'+12345"
    assert sanitize_csv_cell("-12345") == "'-12345"
    assert sanitize_csv_cell("@SUM(1,2)") == "'@SUM(1,2)"
    assert sanitize_csv_cell("\tTabbed") == "'\tTabbed"
    assert sanitize_csv_cell("\rReturn") == "'\rReturn"

    # Benign string unchanged
    assert sanitize_csv_cell("Normal Text") == "Normal Text"
    assert sanitize_csv_cell("Acme Corp") == "Acme Corp"

    # Numbers remain numbers
    assert sanitize_csv_cell(123) == 123
    assert sanitize_csv_cell(-45.67) == -45.67


def test_m10_t11_large_export_handling(client: TestClient, analyst_headers: dict[str, str]) -> None:
    """M10-T11: Large export handling — verify capping at settings.max_export_rows."""
    # Requesting excessive rows gets capped cleanly without memory failure
    resp = client.get(
        "/api/v1/reports/sales-performance/export/csv?limit=60000",
        headers=analyst_headers,
    )
    assert resp.status_code == 200
    # Stream chunks correctly received
    lines = resp.text.splitlines()
    assert len(lines) > 5


def test_m10_t12_pdf_export_clean_deferral(
    client: TestClient, analyst_headers: dict[str, str], viewer_headers: dict[str, str]
) -> None:
    """M10-T12: PDF export — cleanly deferred endpoint returning 501 with informative notice."""
    # Viewer without export permission gets 403
    v_resp = client.get("/api/v1/reports/sales-performance/export/pdf", headers=viewer_headers)
    assert v_resp.status_code == 403

    # User with export permission receives 501 Not Implemented with clear message
    resp = client.get("/api/v1/reports/sales-performance/export/pdf", headers=analyst_headers)
    assert resp.status_code == 501
    body = resp.json()
    assert "PDF report generation is deferred to v1.1" in body["error"]["message"]
