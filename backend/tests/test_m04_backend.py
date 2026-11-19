"""
NEXORA — Module 4 Test Suite: Backend Foundation and API Standards
Validates test cases M4-T01 through M4-T11 against live FastAPI application and PostgreSQL database.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="module")
def client() -> TestClient:
    """Module-level TestClient for FastAPI endpoints."""
    return TestClient(app)


@pytest.fixture(scope="module")
def auth_headers(client: TestClient) -> dict[str, str]:
    """Provide authenticated headers using the demo analyst account."""
    resp = client.post("/api/v1/auth/demo-login", json={"role": "data_analyst"})
    assert resp.status_code == 200
    token = resp.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.m04
def test_m04_t01_backend_startup(client: TestClient) -> None:
    """M4-T01: Backend application startup — verify FastAPI app initializes without errors."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


@pytest.mark.m04
def test_m04_t02_database_connectivity(client: TestClient, auth_headers: dict[str, str]) -> None:
    """M4-T02: Database connectivity — verify endpoint reads actual seeded database records."""
    response = client.get("/api/v1/organizations/current", headers=auth_headers)
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["code"] == "NEXORA"
    assert payload["data"]["name"] == "Nexora Technologies Inc."


@pytest.mark.m04
def test_m04_t03_database_session_handling(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    """M4-T03: DB session handling — verify repeated requests & errors don't leak sessions."""
    # Execute 15 sequential requests including controlled 404s
    for _ in range(10):
        res = client.get("/api/v1/categories", headers=auth_headers)
        assert res.status_code == 200
        assert res.json()["success"] is True

    for _ in range(5):
        res_err = client.get("/api/v1/products/9999999", headers=auth_headers)
        assert res_err.status_code == 404
        assert res_err.json()["success"] is False

    # Verify session pool is still clean and healthy
    final_res = client.get("/api/v1/health")
    assert final_res.status_code == 200
    assert final_res.json()["database"] == "connected"


@pytest.mark.m04
def test_m04_t04_api_response_format(client: TestClient, auth_headers: dict[str, str]) -> None:
    """M4-T04: API response format — verify consistent response envelope structure."""
    # Standard single item response envelope
    res_single = client.get("/api/v1/organizations/current", headers=auth_headers)
    payload_single = res_single.json()
    assert "success" in payload_single
    assert "data" in payload_single
    assert "error" in payload_single

    # Paginated response envelope
    res_page = client.get("/api/v1/products?page=1&page_size=5", headers=auth_headers)
    payload_page = res_page.json()
    assert payload_page["success"] is True
    assert isinstance(payload_page["data"], list)
    assert len(payload_page["data"]) == 5
    assert "meta" in payload_page
    meta = payload_page["meta"]
    assert meta["page"] == 1
    assert meta["page_size"] == 5
    assert meta["total_items"] == 120
    assert meta["total_pages"] == 24
    assert meta["has_next"] is True
    assert meta["has_prev"] is False


@pytest.mark.m04
def test_m04_t05_request_validation(client: TestClient, auth_headers: dict[str, str]) -> None:
    """M4-T05: Request validation — invalid types or negative pagination parameters return 422."""
    res_bad_page = client.get("/api/v1/customers?page=0", headers=auth_headers)  # ge=1
    assert res_bad_page.status_code == 422
    payload = res_bad_page.json()
    assert payload["success"] is False
    assert payload["error"]["code"] == "VALIDATION_ERROR"
    assert len(payload["error"]["details"]) > 0

    res_bad_size = client.get("/api/v1/customers?page_size=999", headers=auth_headers)  # le=100
    assert res_bad_size.status_code == 422


@pytest.mark.m04
def test_m04_t06_pagination(client: TestClient, auth_headers: dict[str, str]) -> None:
    """M4-T06: Pagination — verify multiple pages return distinct records without overlaps."""
    page_1 = client.get(
        "/api/v1/products?page=1&page_size=10&sort_by=id&sort_dir=asc",
        headers=auth_headers,
    ).json()
    page_2 = client.get(
        "/api/v1/products?page=2&page_size=10&sort_by=id&sort_dir=asc",
        headers=auth_headers,
    ).json()

    p1_ids = [item["id"] for item in page_1["data"]]
    p2_ids = [item["id"] for item in page_2["data"]]

    assert len(p1_ids) == 10
    assert len(p2_ids) == 10
    # No ID overlap between page 1 and page 2
    assert set(p1_ids).isdisjoint(set(p2_ids))
    assert max(p1_ids) < min(p2_ids)


@pytest.mark.m04
def test_m04_t07_sorting(client: TestClient, auth_headers: dict[str, str]) -> None:
    """M4-T07: Sorting — verify ascending and descending order on supported columns."""
    res_asc = client.get(
        "/api/v1/products?page=1&page_size=10&sort_by=unit_price&sort_dir=asc",
        headers=auth_headers,
    ).json()
    prices_asc = [float(item["unit_price"]) for item in res_asc["data"]]
    assert prices_asc == sorted(prices_asc)

    res_desc = client.get(
        "/api/v1/products?page=1&page_size=10&sort_by=unit_price&sort_dir=desc",
        headers=auth_headers,
    ).json()
    prices_desc = [float(item["unit_price"]) for item in res_desc["data"]]
    assert prices_desc == sorted(prices_desc, reverse=True)


@pytest.mark.m04
def test_m04_t08_filtering(client: TestClient, auth_headers: dict[str, str]) -> None:
    """M4-T08: Filtering — verify combined filters satisfy all conditions."""
    res = client.get(
        "/api/v1/customers?region_id=1&customer_type=Enterprise&page=1&page_size=50",
        headers=auth_headers,
    ).json()
    assert res["success"] is True
    assert len(res["data"]) > 0
    for cust in res["data"]:
        assert cust["region_id"] == 1
        assert cust["customer_type"] == "Enterprise"

    # Search filter
    res_search = client.get("/api/v1/products?search=LAPTOPS", headers=auth_headers).json()
    assert res_search["success"] is True
    assert len(res_search["data"]) > 0
    for prod in res_search["data"]:
        assert "LAPTOPS" in prod["sku"] or "Laptops" in prod["name"]


@pytest.mark.m04
def test_m04_t09_invalid_filter_handling(client: TestClient, auth_headers: dict[str, str]) -> None:
    """M4-T09: Invalid filter handling — unsupported filter parameters return 422."""
    res_bad_status = client.get("/api/v1/orders?status=invalid_status_xyz", headers=auth_headers)
    assert res_bad_status.status_code == 422
    payload = res_bad_status.json()
    assert payload["success"] is False
    assert payload["error"]["code"] == "VALIDATION_ERROR"

    res_bad_channel = client.get(
        "/api/v1/orders?sales_channel=UnknownChannel", headers=auth_headers
    )
    assert res_bad_channel.status_code == 422


@pytest.mark.m04
def test_m04_t10_api_documentation(client: TestClient) -> None:
    """M4-T10: API documentation — verify OpenAPI JSON schema is generated and accurate."""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    assert schema["info"]["title"] == "Nexora Enterprise Data Intelligence Platform"
    assert "/api/v1/health" in schema["paths"]
    assert "/api/v1/auth/login" in schema["paths"]
    assert "/api/v1/auth/demo-login" in schema["paths"]
    assert "/api/v1/organizations/current" in schema["paths"]
    assert "/api/v1/products" in schema["paths"]
    assert "/api/v1/customers" in schema["paths"]
    assert "/api/v1/orders" in schema["paths"]


@pytest.mark.m04
def test_m04_t11_error_handling(client: TestClient, auth_headers: dict[str, str]) -> None:
    """M4-T11: Error handling — controlled exceptions return safe error without stack traces."""
    response = client.get("/api/v1/orders/99999999", headers=auth_headers)
    assert response.status_code == 404
    payload = response.json()
    assert payload["success"] is False
    assert payload["error"]["code"] == "NOT_FOUND"
    assert "not found" in payload["error"]["message"].lower()
    # Confirm no stack trace or DB connection string is leaked
    assert "traceback" not in str(payload).lower()
    assert "postgresql://" not in str(payload).lower()
