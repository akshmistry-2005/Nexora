"""
NEXORA — Module 7 Test Suite: Data Ingestion and Source Management
Validates test cases M7-T01 through M7-T13 against live FastAPI application and PostgreSQL database.
"""

import io
import uuid
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.main import app
from app.models.customer import Customer
from app.models.data_ops import ImportJob


@pytest.fixture(scope="module", autouse=True)
def cleanup_imported_test_data() -> Generator[None, None, None]:
    """Ensure any test-created customers are cleaned up after module tests run."""
    yield
    engine = create_engine(settings.database_url, future=True)
    with Session(engine) as session:
        session.query(Customer).filter(Customer.id > 2500).delete()
        session.commit()
    engine.dispose()


@pytest.fixture(scope="module")
def client() -> TestClient:
    """Module-level TestClient for FastAPI endpoints."""
    return TestClient(app)


@pytest.fixture(scope="module")
def db_session() -> Session:
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
def demo_headers(client: TestClient) -> dict[str, str]:
    """Provide authenticated headers for Demo Data Analyst."""
    resp = client.post("/api/v1/auth/demo-login", json={"role": "data_analyst"})
    assert resp.status_code == 200
    token = resp.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.m07
def test_m07_t01_valid_csv_upload_preview(
    client: TestClient, owner_headers: dict[str, str]
) -> None:
    """M7-T01: Valid CSV upload — accepts valid CSV and parses headers and rows."""
    csv_content = (
        b"customer_code,contact_name,email,region_id,customer_type,acquisition_channel\n"
        b"CUST-NEW-01,Test Contact 1,tc1@example.com,1,B2B,Direct\n"
        b"CUST-NEW-02,Test Contact 2,tc2@example.com,2,Enterprise,Referral\n"
    )

    response = client.post(
        "/api/v1/data-sources/upload-preview",
        headers=owner_headers,
        data={"target_entity": "customers"},
        files={"file": ("valid_customers.csv", io.BytesIO(csv_content), "text/csv")},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    data = payload["data"]
    assert data["file_name"] == "valid_customers.csv"
    assert data["total_detected_rows"] == 2
    assert "customer_code" in data["detected_headers"]
    assert data["missing_required_headers"] == []
    assert len(data["preview_rows"]) == 2


@pytest.mark.m07
def test_m07_t02_invalid_extension(client: TestClient, owner_headers: dict[str, str]) -> None:
    """M7-T02: Invalid extension — rejects non-CSV files with 400 Bad Request."""
    bad_content = b'{"bad": "json"}'
    response = client.post(
        "/api/v1/data-sources/upload-preview",
        headers=owner_headers,
        data={"target_entity": "customers"},
        files={"file": ("payload.json", io.BytesIO(bad_content), "application/json")},
    )
    assert response.status_code == 400
    payload = response.json()
    assert payload["success"] is False
    assert payload["error"]["code"] == "INVALID_FILE_TYPE"


@pytest.mark.m07
def test_m07_t03_oversized_file(client: TestClient, owner_headers: dict[str, str]) -> None:
    """M7-T03: Oversized file — rejects files exceeding MAX_UPLOAD_SIZE_MB with 413."""
    # 10.5 MB dummy content
    oversized_content = b"a" * (11 * 1024 * 1024)
    response = client.post(
        "/api/v1/data-sources/upload-preview",
        headers=owner_headers,
        data={"target_entity": "customers"},
        files={"file": ("large_file.csv", io.BytesIO(oversized_content), "text/csv")},
    )
    assert response.status_code == 413
    payload = response.json()
    assert payload["success"] is False
    assert payload["error"]["code"] == "FILE_TOO_LARGE"


@pytest.mark.m07
def test_m07_t04_empty_file(client: TestClient, owner_headers: dict[str, str]) -> None:
    """M7-T04: Empty file — rejects 0-byte or whitespace file with 400."""
    empty_content = b""
    response = client.post(
        "/api/v1/data-sources/upload-preview",
        headers=owner_headers,
        data={"target_entity": "customers"},
        files={"file": ("empty.csv", io.BytesIO(empty_content), "text/csv")},
    )
    assert response.status_code == 400
    payload = response.json()
    assert payload["success"] is False
    assert payload["error"]["code"] == "EMPTY_FILE"


@pytest.mark.m07
def test_m07_t05_malformed_csv(client: TestClient, owner_headers: dict[str, str]) -> None:
    """M7-T05: Malformed CSV — rejects uneven column counts per line."""
    malformed_content = (
        b"col1,col2,col3\n"
        b"val1,val2,val3\n"
        b"broken_val1,broken_val2\n"  # missing 3rd column
    )

    response = client.post(
        "/api/v1/data-sources/upload-preview",
        headers=owner_headers,
        data={"target_entity": "customers"},
        files={"file": ("malformed.csv", io.BytesIO(malformed_content), "text/csv")},
    )
    assert response.status_code == 400
    payload = response.json()
    assert payload["success"] is False
    assert payload["error"]["code"] == "MALFORMED_CSV"


@pytest.mark.m07
def test_m07_t06_missing_required_columns(
    client: TestClient, owner_headers: dict[str, str]
) -> None:
    """M7-T06: Missing required columns — import execution fails if required fields are missing."""
    csv_missing_email = (
        b"customer_code,contact_name,region_id,customer_type,acquisition_channel\n"
        b"CUST-NO-MAIL,Contact No Mail,1,B2B,Direct\n"
    )

    response = client.post(
        "/api/v1/data-sources/import",
        headers=owner_headers,
        data={"target_entity": "customers"},
        files={"file": ("missing_email.csv", io.BytesIO(csv_missing_email), "text/csv")},
    )
    assert response.status_code == 400
    payload = response.json()
    assert payload["success"] is False
    assert payload["error"]["code"] == "MISSING_REQUIRED_COLUMNS"


@pytest.mark.m07
def test_m07_t07_column_mapping(client: TestClient, owner_headers: dict[str, str]) -> None:
    """M7-T07: Column mapping — supports custom mapping between CSV headers and schema."""
    code = f"MAP-{uuid.uuid4().hex[:6].upper()}"
    custom_header_csv = (
        "ClientCode,FullName,EmailAddress,TerritoryId,ClientSegment,Source\n"
        f"{code},Mapped User,{code.lower()}@test.local,1,Enterprise,Organic Search\n"
    ).encode()

    custom_mapping_json = (
        '{"customer_code": "ClientCode", "contact_name": "FullName", '
        '"email": "EmailAddress", "region_id": "TerritoryId", '
        '"customer_type": "ClientSegment", "acquisition_channel": "Source"}'
    )

    response = client.post(
        "/api/v1/data-sources/import",
        headers=owner_headers,
        data={
            "target_entity": "customers",
            "custom_mapping": custom_mapping_json,
            "allow_duplicate": True,
        },
        files={"file": ("mapped_customers.csv", io.BytesIO(custom_header_csv), "text/csv")},
    )
    assert response.status_code == 201
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["loaded_rows"] == 1


@pytest.mark.m07
def test_m07_t08_data_preview(
    client: TestClient, owner_headers: dict[str, str], db_session: Session
) -> None:
    """M7-T08: Data preview — returns inferred types and preview rows without modifying DB."""
    test_code = f"PREV-{uuid.uuid4().hex[:6].upper()}"
    csv_content = (
        "customer_code,contact_name,email,region_id,customer_type,acquisition_channel\n"
        f"{test_code},Preview User,{test_code.lower()}@preview.local,1,B2B,Direct\n"
    ).encode()

    response = client.post(
        "/api/v1/data-sources/upload-preview",
        headers=owner_headers,
        data={"target_entity": "customers"},
        files={"file": ("preview_only.csv", io.BytesIO(csv_content), "text/csv")},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["inferred_types"]["region_id"] == "integer"
    assert len(data["preview_rows"]) == 1

    # Verify database was NOT written
    existing = db_session.scalar(select(Customer).where(Customer.customer_code == test_code))
    assert existing is None


@pytest.mark.m07
def test_m07_t09_successful_import(
    client: TestClient, owner_headers: dict[str, str], db_session: Session
) -> None:
    """M7-T09: Successful import — creates DataSource, ImportJob, and destination rows."""
    code1 = f"IMP1-{uuid.uuid4().hex[:6].upper()}"
    code2 = f"IMP2-{uuid.uuid4().hex[:6].upper()}"
    valid_csv = (
        "customer_code,contact_name,email,region_id,customer_type,acquisition_channel\n"
        f"{code1},Imported User One,{code1.lower()}@nexora.test,1,B2B,Direct\n"
        f"{code2},Imported User Two,{code2.lower()}@nexora.test,2,Enterprise,Partner\n"
    ).encode()

    response = client.post(
        "/api/v1/data-sources/import",
        headers=owner_headers,
        data={"target_entity": "customers", "allow_duplicate": True},
        files={"file": ("batch_import.csv", io.BytesIO(valid_csv), "text/csv")},
    )
    assert response.status_code == 201
    payload = response.json()
    assert payload["success"] is True
    data = payload["data"]
    assert data["status"] == "completed"
    assert data["loaded_rows"] == 2
    assert data["rejected_rows"] == 0

    # Verify rows in PostgreSQL
    c1 = db_session.scalar(select(Customer).where(Customer.customer_code == code1))
    c2 = db_session.scalar(select(Customer).where(Customer.customer_code == code2))
    assert c1 is not None
    assert c2 is not None


@pytest.mark.m07
def test_m07_t10_transaction_rollback(
    client: TestClient, owner_headers: dict[str, str], db_session: Session
) -> None:
    """M7-T10: Transaction rollback — constraint error rolls back all rows atomically."""
    valid_code = f"ROLL-VALID-{uuid.uuid4().hex[:6].upper()}"
    bad_region_code = f"ROLL-BAD-{uuid.uuid4().hex[:6].upper()}"

    # Row 1 is valid, Row 2 has non-integer region_id which triggers failure
    failing_csv = (
        "customer_code,contact_name,email,region_id,customer_type,acquisition_channel\n"
        f"{valid_code},Good Contact,{valid_code.lower()}@nexora.test,1,B2B,Direct\n"
        f"{bad_region_code},Bad,{bad_region_code.lower()}@nexora.test,NOT_A_NUM,B2B,Direct\n"
    ).encode()

    response = client.post(
        "/api/v1/data-sources/import",
        headers=owner_headers,
        data={"target_entity": "customers", "allow_duplicate": True},
        files={"file": ("failing_batch.csv", io.BytesIO(failing_csv), "text/csv")},
    )
    assert response.status_code == 400
    assert response.json()["success"] is False

    # Verify Row 1 was rolled back and is NOT in PostgreSQL
    c_valid = db_session.scalar(select(Customer).where(Customer.customer_code == valid_code))
    assert c_valid is None, "Valid row was not rolled back after batch failure!"

    # Verify import job records rolled_back status
    failed_job = db_session.scalar(
        select(ImportJob).where(ImportJob.status == "rolled_back").order_by(ImportJob.id.desc())
    )
    assert failed_job is not None


@pytest.mark.m07
def test_m07_t11_import_history(client: TestClient, owner_headers: dict[str, str]) -> None:
    """M7-T11: Import history — inspect execution audit history with pagination."""
    response = client.get("/api/v1/data-sources/history?page=1&page_size=10", headers=owner_headers)
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert "data" in payload
    assert "meta" in payload
    assert payload["meta"]["total_items"] >= 1
    assert any(job["status"] in ("completed", "rolled_back") for job in payload["data"])


@pytest.mark.m07
def test_m07_t12_duplicate_import_behavior(
    client: TestClient, owner_headers: dict[str, str]
) -> None:
    """M7-T12: Duplicate import behavior — re-uploading file rejects with 409 Conflict."""
    unique_suffix = uuid.uuid4().hex[:8]
    dup_csv = (
        "customer_code,contact_name,email,region_id,customer_type,acquisition_channel\n"
        f"DUP-{unique_suffix},Dup User,dup_{unique_suffix}@nexora.test,1,B2B,Direct\n"
    ).encode()

    # First upload succeeds
    resp1 = client.post(
        "/api/v1/data-sources/import",
        headers=owner_headers,
        data={"target_entity": "customers", "allow_duplicate": False},
        files={"file": (f"dup_{unique_suffix}.csv", io.BytesIO(dup_csv), "text/csv")},
    )
    assert resp1.status_code == 201

    # Second upload of exact same content rejected as duplicate
    resp2 = client.post(
        "/api/v1/data-sources/import",
        headers=owner_headers,
        data={"target_entity": "customers", "allow_duplicate": False},
        files={"file": (f"dup_{unique_suffix}.csv", io.BytesIO(dup_csv), "text/csv")},
    )
    assert resp2.status_code == 409
    payload = resp2.json()
    assert payload["error"]["code"] == "DUPLICATE_IMPORT"

    # With allow_duplicate=True, forced re-import is permitted
    resp3 = client.post(
        "/api/v1/data-sources/import",
        headers=owner_headers,
        data={"target_entity": "customers", "allow_duplicate": True},
        files={"file": (f"dup_{unique_suffix}.csv", io.BytesIO(dup_csv), "text/csv")},
    )
    # Note: destination insert might fail if customer_code unique constraint exists,
    # or succeed if staged. The key is allow_duplicate bypassed the 409 check!
    assert resp3.status_code != 409


@pytest.mark.m07
def test_m07_t13_demo_role_restrictions(client: TestClient, demo_headers: dict[str, str]) -> None:
    """M7-T13: Demo role restrictions — demo users cannot upload imports (403 Forbidden)."""
    csv_content = b"customer_code,contact_name,email,region_id,customer_type,acquisition_channel\n"

    # 1. Demo user calls upload-preview -> 403 Forbidden
    preview_resp = client.post(
        "/api/v1/data-sources/upload-preview",
        headers=demo_headers,
        data={"target_entity": "customers"},
        files={"file": ("demo_try.csv", io.BytesIO(csv_content), "text/csv")},
    )
    assert preview_resp.status_code == 403
    assert preview_resp.json()["error"]["code"] == "FORBIDDEN"

    # 2. Demo user calls import -> 403 Forbidden
    import_resp = client.post(
        "/api/v1/data-sources/import",
        headers=demo_headers,
        data={"target_entity": "customers"},
        files={"file": ("demo_try.csv", io.BytesIO(csv_content), "text/csv")},
    )
    assert import_resp.status_code == 403
    assert import_resp.json()["error"]["code"] == "FORBIDDEN"
