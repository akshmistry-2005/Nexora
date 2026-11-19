"""
NEXORA — Module 8 Test Suite: Data Cleaning, Validation and Quality Intelligence
Validates test cases M8-T01 through M8-T12 against live FastAPI application and PostgreSQL database.
"""

from collections.abc import Generator
from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.analytics.cleaning.rules import (
    calculate_quality_dimensions,
    detect_duplicates,
    is_missing,
    standardize_category,
    validate_date,
    validate_numeric,
    validate_referential_integrity,
)
from app.core.config import settings
from app.main import app
from app.models.customer import Customer
from app.models.data_ops import DataSource, ImportJob, StagingRecord
from app.services.data_quality import quality_service


@pytest.fixture(scope="module", autouse=True)
def cleanup_m08_test_data() -> Generator[None, None, None]:
    """Ensure any test-created records are cleaned up after module tests run."""
    yield
    engine = create_engine(settings.database_url, future=True)
    with Session(engine) as session:
        # Delete test customers created during M8 testing
        test_customers = (
            session.query(Customer)
            .filter((Customer.id > 2500) | (Customer.customer_code.like("M8-%")))
            .all()
        )
        for cust in test_customers:
            session.delete(cust)
        session.commit()
    engine.dispose()


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
def demo_headers(client: TestClient) -> dict[str, str]:
    """Provide authenticated headers for Demo Data Analyst."""
    resp = client.post(
        "/api/v1/auth/demo-login",
        json={"role": "data_analyst"},
    )
    assert resp.status_code == 200
    token = resp.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_m08_t01_missing_value_detection() -> None:
    """M8-T01: Verify detection of null, empty, and sentinel missing values."""
    assert is_missing(None) is True
    assert is_missing("") is True
    assert is_missing("   ") is True
    assert is_missing("na") is True
    assert is_missing("N/A") is True
    assert is_missing("null") is True
    assert is_missing("?") is True
    assert is_missing("Active") is False
    assert is_missing(42) is False

    test_records = [
        {
            "customer_code": "M8-C01",
            "contact_name": "Valid Name",
            "email": "c01@test.local",
            "region_id": 1,
            "customer_type": "B2B",
            "acquisition_channel": "Direct",
        },
        {
            "customer_code": "",  # Missing
            "contact_name": "Missing Code",
            "email": "null",  # Sentinel missing
            "region_id": 1,
            "customer_type": "B2C",
            "acquisition_channel": "n/a",  # Sentinel missing
        },
    ]

    report = quality_service.evaluate_records("customers", test_records)
    missing_issues = [i for i in report.issues if i.issue_type == "missing_value"]
    assert len(missing_issues) == 3
    assert any(i.field == "customer_code" and i.row_number == 2 for i in missing_issues)
    assert any(i.field == "email" and i.row_number == 2 for i in missing_issues)
    assert any(i.field == "acquisition_channel" and i.row_number == 2 for i in missing_issues)


def test_m08_t02_duplicate_detection() -> None:
    """M8-T02: Verify duplicate detection on business key fields."""
    records = [
        {"customer_code": "M8-DUP-01", "name": "First Record"},
        {"customer_code": "M8-DUP-02", "name": "Second Record"},
        {"customer_code": "M8-DUP-01", "name": "Duplicate of First"},
        {"customer_code": "m8-dup-01", "name": "Case-Insensitive Duplicate"},
    ]

    dup_rows, dup_details = detect_duplicates(records, ["customer_code"])
    assert 1 not in dup_rows
    assert 2 not in dup_rows
    assert 3 in dup_rows
    assert 4 in dup_rows
    assert len(dup_details) == 2


def test_m08_t03_invalid_date_detection() -> None:
    """M8-T03: Verify detection of unparseable, future, and unreasonably old dates."""
    # Valid date
    v1, d1, e1 = validate_date("2025-06-15", "signup_date")
    assert v1 is True and d1 is not None and e1 is None

    # Unparseable format
    v2, d2, e2 = validate_date("not-a-date", "signup_date")
    assert v2 is False and d2 is None and "not a valid recognized date" in str(e2)

    # Future date (not allowed by default)
    future_date = "2099-12-31"
    v3, d3, e3 = validate_date(future_date, "signup_date", allow_future=False)
    assert v3 is False and "in the future" in str(e3)

    # Unreasonably old date (pre-2000)
    v4, d4, e4 = validate_date("1980-01-01", "signup_date")
    assert v4 is False and "unreasonably old" in str(e4)


def test_m08_t04_numeric_validation() -> None:
    """M8-T04: Verify numeric range constraints, type validation, and symbol stripping."""
    # Valid numbers
    v1, n1, _ = validate_numeric(45.5, "unit_price", min_val=0.0)
    assert v1 is True and n1 == 45.5

    # Currency formatting with symbols
    v2, n2, _ = validate_numeric("$1,250.75", "total_amount", min_val=0.0)
    assert v2 is True and n2 == 1250.75

    # Negative number violation
    v3, n3, e3 = validate_numeric(-15.0, "unit_price", min_val=0.0)
    assert v3 is False and "less than minimum allowed" in str(e3)

    # Non-numeric string
    v4, n4, e4 = validate_numeric("twelve", "unit_price", min_val=0.0)
    assert v4 is False and "not a valid number" in str(e4)


def test_m08_t05_category_consistency() -> None:
    """M8-T05: Verify category standardization against canonical domain dictionaries."""
    cmap = {"b2b": "B2B", "b-to-b": "B2B", "business": "B2B", "b2c": "B2C"}

    std1, ch1 = standardize_category("b-to-b", cmap)
    assert std1 == "B2B" and ch1 is True

    std2, ch2 = standardize_category("B2B", cmap)
    assert std2 == "B2B" and ch2 is False

    std3, ch3 = standardize_category("enterprise", cmap)
    assert std3 == "Enterprise" and ch3 is True

    std4, ch4 = standardize_category("Enterprise", cmap)
    assert std4 == "Enterprise" and ch4 is False


def test_m08_t06_referential_integrity_validation(db_session: Session) -> None:
    """M8-T06: Verify foreign key validation against live PostgreSQL database."""
    valid_fks = quality_service.get_valid_foreign_keys(db_session, "customers")
    region_ids = valid_fks["region_id"]
    assert len(region_ids) > 0

    first_region_id = next(iter(region_ids))
    valid_fk, err1 = validate_referential_integrity(first_region_id, region_ids, "region_id")
    assert valid_fk is True and err1 is None

    # Invalid non-existent foreign key ID
    invalid_fk, err2 = validate_referential_integrity(999999, region_ids, "region_id")
    assert invalid_fk is False
    assert "Foreign key violation" in str(err2)


def test_m08_t07_five_quality_dimensions_math() -> None:
    """M8-T07: Verify 5-dimensional data quality formulas against exact mathematical oracle."""
    # Oracle parameters:
    # 10 records total
    # 2 missing cells out of 20 required cells -> Completeness = (1 - 2/20) * 100 = 90.0%
    # 1 invalid field check out of 10 checks -> Validity = (1 - 1/10) * 100 = 90.0%
    # 1 duplicate record out of 10 records -> Uniqueness = (1 - 1/10) * 100 = 90.0%
    # 1 inconsistent cell out of 10 checks -> Consistency = (1 - 1/10) * 100 = 90.0%
    # 8 timely records out of 10 records -> Timeliness = (8 / 10) * 100 = 80.0%
    # Expected weighted score:
    # 0.25*90 + 0.25*90 + 0.20*90 + 0.20*90 + 0.10*80 = 22.5 + 22.5 + 18.0 + 18.0 + 8.0 = 89.0%

    dims = calculate_quality_dimensions(
        total_records=10,
        missing_required_cells=2,
        total_required_cells=20,
        invalid_field_checks=1,
        total_field_checks=10,
        duplicate_records=1,
        inconsistent_cells=1,
        total_consistency_checks=10,
        timely_records=8,
    )

    assert dims.completeness == 90.0
    assert dims.validity == 90.0
    assert dims.uniqueness == 90.0
    assert dims.consistency == 90.0
    assert dims.timeliness == 80.0
    assert dims.overall_score == 89.0


def test_m08_t08_transformation_traceability() -> None:
    """M8-T08: Verify lineage tracking and transformation audit logs for every cleaning mutation."""
    raw_records = [
        {
            "customer_code": "  M8-TRACE-01  ",
            "contact_name": "Alice Smith",
            "email": "alice@test.local",
            "customer_type": "b-to-b",
            "signup_date": "2025/11/04",
        }
    ]

    cleaned_records, transformations = quality_service.clean_records(
        entity_type="customers",
        records=raw_records,
        standardize_categories=True,
        standardize_dates=True,
    )

    assert len(cleaned_records) == 1
    clean_row = cleaned_records[0]
    assert clean_row["customer_code"] == "M8-TRACE-01"
    assert clean_row["customer_type"] == "B2B"
    assert clean_row["signup_date"] == "2025-11-04"

    # Lineage transformations
    rules_applied = {t.rule for t in transformations}
    assert "TRIM_WHITESPACE" in rules_applied
    assert "STANDARDIZE_CATEGORY" in rules_applied
    assert "STANDARDIZE_DATE_ISO" in rules_applied

    # Verify audit fields
    for t in transformations:
        assert t.row_number == 1
        assert t.cleaned_value is not None


def test_m08_t09_raw_data_preservation(
    client: TestClient, db_session: Session, owner_headers: dict[str, str]
) -> None:
    """M8-T09: Verify raw uploaded data is strictly preserved in staging_records."""
    # Create test DataSource and ImportJob with raw staged data
    ds = DataSource(
        organization_id=1,
        name="M8 Preservation Test",
        source_type="CSV",
        file_name="m8_raw_test.csv",
        file_size_bytes=100,
        file_checksum="checksum_m8_preservation",
        uploaded_by_id=1,
    )
    db_session.add(ds)
    db_session.flush()

    job = ImportJob(
        data_source_id=ds.id,
        target_entity="customers",
        status="staging",
        total_rows=1,
    )
    db_session.add(job)
    db_session.flush()

    raw_payload = {
        "customer_code": "  M8-RAW-PRESERVE  ",
        "contact_name": "Bob Raw",
        "email": "bob@raw.local",
        "region_id": "1",
        "customer_type": "business",
        "acquisition_channel": "Direct",
    }

    rec = StagingRecord(
        import_job_id=job.id,
        row_number=1,
        raw_data=raw_payload,
        validation_status="valid",
    )
    db_session.add(rec)
    db_session.commit()

    # Call automated cleaning endpoint
    resp = client.post(f"/api/v1/data-quality/clean/{job.id}", headers=owner_headers)
    assert resp.status_code == 200

    # Query StagingRecord directly from database
    db_session.refresh(rec)
    # Raw data must remain untouched!
    assert rec.raw_data == raw_payload
    assert rec.raw_data["customer_code"] == "  M8-RAW-PRESERVE  "
    assert rec.raw_data["customer_type"] == "business"

    # Cleaned data must contain transformations
    assert rec.cleaned_data is not None
    assert rec.cleaned_data["customer_code"] == "M8-RAW-PRESERVE"
    assert rec.cleaned_data["customer_type"] == "B2B"
    assert rec.validation_status == "cleaned"


def test_m08_t10_repeatability() -> None:
    """M8-T10: Verify identical evaluation scores and cleaning on repeated execution."""
    raw_data = [
        {
            "customer_code": "M8-REP-01",
            "contact_name": "Repeated Test",
            "email": "rep@test.local",
            "region_id": 1,
            "customer_type": "b2c",
            "acquisition_channel": "organic search",
        },
        {
            "customer_code": "M8-REP-02",
            "contact_name": "Repeated Test 2",
            "email": "",
            "region_id": 1,
            "customer_type": "b-to-b",
            "acquisition_channel": "email",
        },
    ]

    report1 = quality_service.evaluate_records("customers", raw_data)
    report2 = quality_service.evaluate_records("customers", raw_data)

    assert report1.dimensions.overall_score == report2.dimensions.overall_score
    assert report1.dimensions.completeness == report2.dimensions.completeness
    assert report1.total_issues == report2.total_issues

    cleaned1, trans1 = quality_service.clean_records("customers", raw_data)
    cleaned2, trans2 = quality_service.clean_records("customers", raw_data)

    assert cleaned1 == cleaned2
    assert len(trans1) == len(trans2)
    assert [t.rule for t in trans1] == [t.rule for t in trans2]


def test_m08_t11_cleaning_approval_rbac(
    client: TestClient,
    db_session: Session,
    owner_headers: dict[str, str],
    demo_headers: dict[str, str],
) -> None:
    """M8-T11: Enforce role-based access control on cleaning and curated approval endpoints."""
    # Staged job
    ds = DataSource(
        organization_id=1,
        name="M8 RBAC Test",
        source_type="CSV",
        file_name="m8_rbac.csv",
        file_size_bytes=80,
        file_checksum="checksum_m8_rbac",
        uploaded_by_id=1,
    )
    db_session.add(ds)
    db_session.flush()

    job = ImportJob(
        data_source_id=ds.id,
        target_entity="customers",
        status="staging",
        total_rows=1,
    )
    db_session.add(job)
    db_session.flush()

    rec = StagingRecord(
        import_job_id=job.id,
        row_number=1,
        raw_data={
            "customer_code": "M8-RBAC-01",
            "contact_name": "RBAC Customer",
            "email": "rbac@test.local",
            "region_id": 1,
            "customer_type": "B2C",
            "acquisition_channel": "Direct",
        },
        validation_status="cleaned",
    )
    db_session.add(rec)
    db_session.commit()

    # 1. Unauthenticated request -> HTTP 401
    unauth_client = TestClient(app)
    unauth_client.cookies.clear()
    resp_unauth = unauth_client.post(f"/api/v1/data-quality/approve/{job.id}")
    assert resp_unauth.status_code == 401

    # 2. Demo role (data_analyst) request -> HTTP 403 Forbidden
    resp_demo_clean = client.post(f"/api/v1/data-quality/clean/{job.id}", headers=demo_headers)
    assert resp_demo_clean.status_code == 403

    resp_demo_approve = client.post(f"/api/v1/data-quality/approve/{job.id}", headers=demo_headers)
    assert resp_demo_approve.status_code == 403

    # 3. Owner request -> HTTP 200 OK
    resp_owner = client.post(f"/api/v1/data-quality/approve/{job.id}", headers=owner_headers)
    assert resp_owner.status_code == 200
    assert resp_owner.json()["data"]["status"] == "completed"


def test_m08_t12_curated_data_validation(
    client: TestClient, db_session: Session, owner_headers: dict[str, str]
) -> None:
    """M8-T12: Verify that promoted curated rows exist in live destination tables."""
    ds = DataSource(
        organization_id=1,
        name="M8 Curated Test",
        source_type="CSV",
        file_name="m8_curated.csv",
        file_size_bytes=120,
        file_checksum="checksum_m8_curated",
        uploaded_by_id=1,
    )
    db_session.add(ds)
    db_session.flush()

    job = ImportJob(
        data_source_id=ds.id,
        target_entity="customers",
        status="staging",
        total_rows=1,
    )
    db_session.add(job)
    db_session.flush()

    unique_code = f"M8-CUR-{datetime.now(UTC).strftime('%H%M%S')}"
    rec = StagingRecord(
        import_job_id=job.id,
        row_number=1,
        raw_data={
            "customer_code": unique_code,
            "contact_name": "Curated Customer",
            "email": f"{unique_code.lower()}@curated.local",
            "region_id": 1,
            "customer_type": "B2B",
            "acquisition_channel": "Direct",
        },
        validation_status="cleaned",
    )
    db_session.add(rec)
    db_session.commit()

    resp = client.post(f"/api/v1/data-quality/approve/{job.id}", headers=owner_headers)
    assert resp.status_code == 200
    assert resp.json()["data"]["curated_rows_promoted"] == 1

    # Verify record was promoted into live PostgreSQL Customer entity
    promoted_customer = db_session.scalar(
        select(Customer).where(Customer.customer_code == unique_code)
    )
    assert promoted_customer is not None
    assert promoted_customer.contact_name == "Curated Customer"
    assert promoted_customer.customer_type == "B2B"
    assert promoted_customer.is_active is True
