import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.mark.m02
def test_health_endpoint_returns_healthy_with_live_postgres() -> None:
    """M2-T06: Backend health-check endpoint returns healthy status with live PostgreSQL."""
    client = TestClient(app)
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "healthy"
    assert payload["database"] == "connected"
    assert payload["version"] == "0.2.0"
    assert "timestamp" in payload
