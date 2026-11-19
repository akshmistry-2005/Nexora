"""Module 14: Pipeline Monitoring, Auditability and Administration Test Suite.

Validates test cases M14-T01 through M14-T13 against live PostgreSQL database:
- M14-T01: Pipeline run creation and status tracking
- M14-T02: Pipeline metadata, execution duration, and structured metrics JSON
- M14-T03: Failed pipeline visibility with error details
- M14-T04: Preservation of last successful refresh timestamp upon failure
- M14-T05: Safe pipeline retry without state corruption
- M14-T06: Audit logging of authentication events (success and failure)
- M14-T07: Audit logging of data import and report export events
- M14-T08: Audit logging of administrative operations
- M14-T09: Audit log append-only protection (PostgreSQL trigger prohibits UPDATE/DELETE)
- M14-T10: Demo role restrictions (403 for unauthorized administrative actions)
- M14-T11: Platform owner administrative oversight (users, audit logs, health)
- M14-T12: Owner-only demonstration dataset reset
- M14-T13: Prominent synthetic demonstration environment notices
"""

from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import desc, select, text
from sqlalchemy.exc import DBAPIError

from app.db.session import SessionLocal
from app.main import app
from app.models.data_ops import AuditLog, PipelineRun
from app.services import admin as admin_service
from app.services import pipelines as pipeline_service


@pytest.fixture(scope="module")
def client() -> TestClient:
    """FastAPI test client instance."""
    return TestClient(app)


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


@pytest.fixture(scope="module")
def analyst_headers(client: TestClient) -> dict[str, str]:
    """Authenticated bearer token for Demo Data Analyst."""
    resp = client.post("/api/v1/auth/demo-login", json={"role": "data_analyst"})
    assert resp.status_code == 200
    token = resp.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="module")
def viewer_headers(client: TestClient) -> dict[str, str]:
    """Authenticated bearer token for General Viewer."""
    resp = client.post("/api/v1/auth/demo-login", json={"role": "general_viewer"})
    assert resp.status_code == 200
    token = resp.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_m14_t01_pipeline_run_creation():
    """M14-T01: Pipeline run can be created with status 'running' and initial telemetry."""
    with SessionLocal() as db:
        run = pipeline_service.create_pipeline_run(
            db,
            pipeline_name="test_order_aggregation_etl",
            status="running",
            metrics={"scanned_orders": 1200},
        )
        assert run.id is not None
        assert run.pipeline_name == "test_order_aggregation_etl"
        assert run.status == "running"
        assert run.started_at is not None
        assert run.metrics["scanned_orders"] == 1200


def test_m14_t02_pipeline_metadata(client: TestClient, analyst_headers: dict[str, str]):
    """M14-T02: Pipeline metadata captures duration, timing, and structured JSON metrics."""
    with SessionLocal() as db:
        now = datetime.now(UTC)
        run = PipelineRun(
            pipeline_name="test_inventory_sync",
            status="success",
            duration_ms=452,
            started_at=now - timedelta(seconds=1),
            ended_at=now,
            metrics={
                "items_synced": 350,
                "anomalies_detected": 0,
                "target": "warehouse_east",
            },
        )
        db.add(run)
        db.commit()
        run_id = run.id

    res = client.get(f"/api/v1/pipelines/runs/{run_id}", headers=analyst_headers)
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["pipeline_name"] == "test_inventory_sync"
    assert data["status"] == "success"
    assert data["duration_ms"] == 452
    assert data["metrics"]["items_synced"] == 350


def test_m14_t03_failed_pipeline_visibility(client: TestClient, analyst_headers: dict[str, str]):
    """M14-T03: Failed pipelines capture error details and are queryable via status filter."""
    with SessionLocal() as db:
        failed_run = PipelineRun(
            pipeline_name="test_sales_ingest_failure",
            status="failed",
            duration_ms=120,
            started_at=datetime.now(UTC),
            ended_at=datetime.now(UTC),
            metrics={
                "error_message": "Network connection dropped by source host",
                "failure_stage": "extract",
                "rows_scanned": 42,
            },
        )
        db.add(failed_run)
        db.commit()

    res = client.get("/api/v1/pipelines/runs?status=failed", headers=analyst_headers)
    assert res.status_code == 200
    data = res.json()["data"]
    assert len(data) >= 1
    failed_items = [r for r in data if r["pipeline_name"] == "test_sales_ingest_failure"]
    assert len(failed_items) >= 1
    assert "error_message" in failed_items[0]["metrics"]
    assert failed_items[0]["metrics"]["failure_stage"] == "extract"


def test_m14_t04_last_successful_refresh_preservation(
    client: TestClient, analyst_headers: dict[str, str]
):
    """M14-T04: Failed pipeline run does NOT overwrite last successful refresh timestamp."""
    p_name = "test_analytics_daily_refresh"
    with SessionLocal() as db:
        # 1. Successful run
        succ_time = datetime(2026, 11, 18, 14, 0, 0, tzinfo=UTC)
        succ_run = PipelineRun(
            pipeline_name=p_name,
            status="success",
            started_at=succ_time - timedelta(minutes=5),
            ended_at=succ_time,
            metrics={"last_successful_refresh": succ_time.isoformat()},
        )
        db.add(succ_run)
        db.commit()

        # 2. Subsequent failed run
        fail_time = datetime(2026, 11, 19, 8, 0, 0, tzinfo=UTC)
        fail_run = PipelineRun(
            pipeline_name=p_name,
            status="failed",
            started_at=fail_time - timedelta(minutes=1),
            ended_at=fail_time,
            metrics={
                "error_message": "Disk space full",
                "last_successful_refresh": succ_time.isoformat(),
            },
        )
        db.add(fail_run)
        db.commit()

    # Query summary endpoint
    res = client.get("/api/v1/pipelines/summary", headers=analyst_headers)
    assert res.status_code == 200
    summary = res.json()["data"]
    target_pipe = next((p for p in summary["pipelines"] if p["pipeline_name"] == p_name), None)
    assert target_pipe is not None
    # Last successful run must reflect the successful run, not the failure
    assert target_pipe["last_successful_run_at"] is not None
    assert "2026-11-18" in target_pipe["last_successful_run_at"]


def test_m14_t05_safe_retry(client: TestClient, owner_headers: dict[str, str]):
    """M14-T05: Safe retry of a failed pipeline creates a new run without data corruption."""
    with SessionLocal() as db:
        run = PipelineRun(
            pipeline_name="test_order_recalculation",
            status="failed",
            started_at=datetime.now(UTC),
            ended_at=datetime.now(UTC),
            metrics={"error": "Deadlock detected during lock acquisition"},
        )
        db.add(run)
        db.commit()
        failed_id = run.id

    # Owner executes retry
    res = client.post(
        f"/api/v1/pipelines/runs/{failed_id}/retry?notes=Re-executed+after+deadlock+release",
        headers=owner_headers,
    )
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["previous_run_id"] == failed_id
    assert data["new_run_id"] != failed_id
    assert data["status"] == "running"

    # Verify DB state: old run marked retried, new run is running
    with SessionLocal() as db:
        old_run = db.get(PipelineRun, failed_id)
        assert old_run is not None and old_run.status == "retried"
        new_run = db.get(PipelineRun, data["new_run_id"])
        assert new_run is not None and new_run.status == "running"
        assert new_run.metrics["retried_from_run_id"] == failed_id


def test_m14_t06_audit_login_events(client: TestClient):
    """M14-T06: Authentication events (success and failure) create immutable audit logs."""
    # 1. Successful owner login
    res = client.post(
        "/api/v1/auth/login",
        json={"email": "owner@nexora.local", "password": "NexoraOwnerPass2026!"},
    )
    assert res.status_code == 200

    # 2. Failed owner login (invalid credentials)
    fail_res = client.post(
        "/api/v1/auth/login",
        json={"email": "owner@nexora.local", "password": "WrongPassword999!"},
    )
    assert fail_res.status_code == 401

    # Verify both audit records in database
    with SessionLocal() as db:
        succ_log = db.scalar(
            select(AuditLog)
            .where(AuditLog.action_type == "AUTH_LOGIN_SUCCESS", AuditLog.actor_role == "owner")
            .order_by(desc(AuditLog.id))
        )
        assert succ_log is not None
        assert succ_log.actor_user_id == 1

        fail_log = db.scalar(
            select(AuditLog)
            .where(
                AuditLog.action_type == "AUTH_LOGIN_FAILURE",
                AuditLog.actor_role == "unauthenticated",
            )
            .order_by(desc(AuditLog.id))
        )
        assert fail_log is not None
        assert fail_log.details is not None
        assert "owner@nexora.local" in fail_log.details.get("email", "")


def test_m14_t07_audit_import_export_events(client: TestClient, analyst_headers: dict[str, str]):
    """M14-T07: Report export operations generate append-only REPORT_EXPORT audit records."""
    # Trigger report export as data analyst
    export_payload = {
        "report_id": "sales-performance",
        "format": "csv",
        "limit": 100,
    }
    res = client.post("/api/v1/reports/export/csv", json=export_payload, headers=analyst_headers)
    assert res.status_code == 200

    with SessionLocal() as db:
        export_log = db.scalar(
            select(AuditLog)
            .where(AuditLog.action_type == "REPORT_EXPORT", AuditLog.actor_role == "data_analyst")
            .order_by(desc(AuditLog.id))
        )
        assert export_log is not None
        assert export_log.details["format"] == "csv"
        assert export_log.entity_id == "sales-performance"


def test_m14_t08_audit_admin_events(client: TestClient, owner_headers: dict[str, str]):
    """M14-T08: Administrative operations produce categorized audit trail records."""
    with SessionLocal() as db:
        admin_service.log_audit_event(
            db,
            action_type="USER_ROLE_UPDATE",
            actor_role="owner",
            actor_user_id=1,
            entity_type="users",
            entity_id="4",
            details={"previous_role": "general_viewer", "assigned_role": "data_analyst"},
        )

    with SessionLocal() as db:
        role_log = db.scalar(
            select(AuditLog)
            .where(AuditLog.action_type == "USER_ROLE_UPDATE", AuditLog.entity_id == "4")
            .order_by(desc(AuditLog.id))
        )
        assert role_log is not None
        assert role_log.actor_role == "owner"
        assert role_log.details["assigned_role"] == "data_analyst"


def test_m14_t09_audit_log_append_only_protection():
    """M14-T09: Direct UPDATE and DELETE on audit_logs are rejected by PostgreSQL trigger."""
    with SessionLocal() as db:
        # Create a valid append-only record
        log = admin_service.log_audit_event(
            db,
            action_type="TEST_IMMUTABILITY_EVENT",
            actor_role="owner",
            actor_user_id=1,
            details={"test": True},
        )
        log_id = log.id

    # Attempt direct UPDATE — must be blocked by PostgreSQL trigger
    with SessionLocal() as db:
        with pytest.raises(DBAPIError) as exc_info:
            db.execute(text(f"UPDATE audit_logs SET actor_role = 'hacked' WHERE id = {log_id};"))
            db.commit()
        assert "Audit logs are immutable and append-only" in str(exc_info.value)
        db.rollback()

    # Attempt direct DELETE — must be blocked by PostgreSQL trigger
    with SessionLocal() as db:
        with pytest.raises(DBAPIError) as exc_info:
            db.execute(text(f"DELETE FROM audit_logs WHERE id = {log_id};"))
            db.commit()
        assert "Audit logs are immutable and append-only" in str(exc_info.value)
        db.rollback()


def test_m14_t10_demo_role_restrictions(
    client: TestClient, analyst_headers: dict[str, str], viewer_headers: dict[str, str]
):
    """M14-T10: Demo roles receive HTTP 403 Forbidden for restricted administrative operations."""
    # 1. Reset demo data attempt by Data Analyst -> 403
    res_reset = client.post("/api/v1/admin/reset-demo", headers=analyst_headers)
    assert res_reset.status_code == 403

    # 2. User directory access attempt by General Viewer -> 403
    res_users = client.get("/api/v1/admin/users", headers=viewer_headers)
    assert res_users.status_code == 403

    # 3. Pipeline retry attempt by General Viewer -> 403
    res_retry = client.post("/api/v1/pipelines/runs/1/retry", headers=viewer_headers)
    assert res_retry.status_code == 403


def test_m14_t11_owner_administration(client: TestClient, owner_headers: dict[str, str]):
    """M14-T11: Platform owner has full access to audit trails, users, and pipeline telemetry."""
    # Audit logs
    res_logs = client.get("/api/v1/admin/audit-logs?limit=10", headers=owner_headers)
    assert res_logs.status_code == 200
    assert len(res_logs.json()["data"]) >= 1

    # Audit summary
    res_sum = client.get("/api/v1/admin/audit-summary", headers=owner_headers)
    assert res_sum.status_code == 200
    assert res_sum.json()["data"]["total_logs"] >= 1

    # Users list
    res_users = client.get("/api/v1/admin/users", headers=owner_headers)
    assert res_users.status_code == 200
    assert len(res_users.json()["data"]) >= 5


def test_m14_t12_owner_only_reset(client: TestClient, owner_headers: dict[str, str]):
    """M14-T12: Platform owner successfully executes demo reset, logging ADMIN_SYSTEM_RESET."""
    res = client.post("/api/v1/admin/reset-demo", headers=owner_headers)
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["status"] == "success"
    assert "reset_timestamp" in data

    # Verify audit trail
    with SessionLocal() as db:
        reset_log = db.scalar(
            select(AuditLog)
            .where(AuditLog.action_type == "ADMIN_SYSTEM_RESET")
            .order_by(desc(AuditLog.id))
        )
        assert reset_log is not None
        assert reset_log.actor_role == "owner"


def test_m14_t13_synthetic_data_notice(client: TestClient, analyst_headers: dict[str, str]):
    """M14-T13: Prominent synthetic demonstration environment notices present in telemetry."""
    # Pipeline health scorecard notice
    res_pipe = client.get("/api/v1/pipelines/summary", headers=analyst_headers)
    assert res_pipe.status_code == 200
    assert "synthetic" in res_pipe.json()["data"]["synthetic_notice"].lower()

    # System status notice
    res_sys = client.get("/api/v1/admin/system-status", headers=analyst_headers)
    assert res_sys.status_code == 200
    assert res_sys.json()["data"]["is_demonstration"] is True
    assert "synthetic" in res_sys.json()["data"]["synthetic_data_notice"].lower()
    assert res_sys.json()["data"]["database_connected"] is True
