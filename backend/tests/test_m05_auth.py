"""
NEXORA — Module 5 Test Suite: Authentication, Roles and Permissions
Validates test cases M5-T01 through M5-T12 against live FastAPI application and PostgreSQL database.
"""

import uuid
from datetime import UTC, datetime, timedelta

import jwt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.main import app
from app.models.auth import User
from app.models.customer import Customer
from app.services.auth import ALLOWED_DEMO_ROLES


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


@pytest.mark.m05
def test_m05_t01_owner_login_success(client: TestClient) -> None:
    """M5-T01: Owner login success — authenticate owner with valid credentials."""
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": "owner@nexora.local", "password": "NexoraOwnerPass2026!"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    payload = data["data"]
    assert payload["role"] == "owner"
    assert payload["email"] == "owner@nexora.local"
    assert "access_token" in payload
    assert payload["token_type"] == "Bearer"
    assert len(payload["permissions"]) >= 29
    assert "user.manage" in payload["permissions"]
    assert "system.reset_demo" in payload["permissions"]
    assert "report.sensitive_fields" in payload["permissions"]

    # Verify cookie was set
    assert "nexora_session" in resp.cookies


@pytest.mark.m05
def test_m05_t02_owner_login_failure(client: TestClient) -> None:
    """M5-T02: Owner login failure — invalid password and unknown email return 401 UNAUTHORIZED."""
    # Invalid password
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": "owner@nexora.local", "password": "WrongPassword123!"},
    )
    assert resp.status_code == 401
    data = resp.json()
    assert data["success"] is False
    assert data["error"]["code"] == "UNAUTHORIZED"

    # Nonexistent user
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": "unknown_admin@nexora.local", "password": "SomePassword123!"},
    )
    assert resp.status_code == 401
    assert resp.json()["success"] is False
    assert resp.json()["error"]["code"] == "UNAUTHORIZED"


@pytest.mark.m05
def test_m05_t03_demo_role_selection(client: TestClient) -> None:
    """M5-T03: Demo role selection — all 5 allow-listed demo roles can authenticate."""
    for role in sorted(ALLOWED_DEMO_ROLES):
        resp = client.post("/api/v1/auth/demo-login", json={"role": role})
        assert resp.status_code == 200, f"Role {role} demo login failed: {resp.text}"
        data = resp.json()
        assert data["success"] is True
        payload = data["data"]
        assert payload["role"] == role
        assert "access_token" in payload
        assert "customer.view" in payload["permissions"]

        # Verify role-specific permission nuances
        if role == "general_viewer":
            assert "report.export" not in payload["permissions"]
        if role == "data_scientist":
            assert "predictions.view" in payload["permissions"]


@pytest.mark.m05
def test_m05_t04_owner_role_protection(client: TestClient) -> None:
    """M5-T04: Owner role protection — demo selector strictly rejects Owner/Admin with 403."""
    # Attempt owner role via demo-login
    resp = client.post("/api/v1/auth/demo-login", json={"role": "owner"})
    assert resp.status_code == 403
    assert resp.json()["success"] is False
    assert resp.json()["error"]["code"] == "FORBIDDEN"

    # Attempt admin alias
    resp_admin = client.post("/api/v1/auth/demo-login", json={"role": "admin"})
    assert resp_admin.status_code == 403
    assert resp_admin.json()["error"]["code"] == "FORBIDDEN"

    # Attempt arbitrary unauthorized role
    resp_invalid = client.post("/api/v1/auth/demo-login", json={"role": "superadmin"})
    assert resp_invalid.status_code == 403
    assert resp_invalid.json()["error"]["code"] == "FORBIDDEN"


@pytest.mark.m05
def test_m05_t05_demo_read_only_protection(client: TestClient, db_session: Session) -> None:
    """M5-T05: Demo read-only protection — demo roles cannot perform POST, PUT, DELETE."""
    test_customer_code = f"TEST-RO-{uuid.uuid4().hex[:6].upper()}"
    new_customer_payload = {
        "customer_code": test_customer_code,
        "company_name": "Unauthorized Test Corp",
        "contact_name": "Unauthorized DemoWrite",
        "email": f"{test_customer_code.lower()}@example.com",
        "region_id": 1,
        "customer_type": "B2B",
        "acquisition_channel": "Direct",
    }

    # Test all demo roles
    for role in ALLOWED_DEMO_ROLES:
        # Get demo token
        login_resp = client.post("/api/v1/auth/demo-login", json={"role": role})
        assert login_resp.status_code == 200
        token = login_resp.json()["data"]["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 1. Attempt POST (Create)
        create_resp = client.post("/api/v1/customers", json=new_customer_payload, headers=headers)
        assert create_resp.status_code == 403, f"Role {role} was able to POST customer!"
        assert create_resp.json()["error"]["code"] == "FORBIDDEN"

        # 2. Attempt PUT (Update)
        update_resp = client.put(
            "/api/v1/customers/1",
            json={"contact_name": "HackedName"},
            headers=headers,
        )
        assert update_resp.status_code == 403, f"Role {role} was able to PUT customer!"
        assert update_resp.json()["error"]["code"] == "FORBIDDEN"

        # 3. Attempt DELETE
        delete_resp = client.delete("/api/v1/customers/1", headers=headers)
        assert delete_resp.status_code == 403, f"Role {role} was able to DELETE customer!"
        assert delete_resp.json()["error"]["code"] == "FORBIDDEN"

    # Verify database was NOT modified
    existing = db_session.scalar(
        select(Customer).where(Customer.customer_code == test_customer_code)
    )
    assert existing is None, "Customer record was unexpectedly created by demo role!"


@pytest.mark.m05
def test_m05_t06_unauthenticated_request() -> None:
    """M5-T06: Unauthenticated request — protected endpoints return 401 UNAUTHORIZED."""
    clean_client = TestClient(app)
    clean_client.cookies.clear()
    endpoints = [
        ("GET", "/api/v1/customers"),
        ("GET", "/api/v1/orders"),
        ("GET", "/api/v1/products"),
        ("GET", "/api/v1/organizations/current"),
        ("GET", "/api/v1/auth/me"),
    ]
    for method, path in endpoints:
        resp = clean_client.request(method, path)
        assert resp.status_code == 401, f"{method} {path} did not return 401 when unauthenticated"
        data = resp.json()
        assert data["success"] is False
        assert data["error"]["code"] == "UNAUTHORIZED"


@pytest.mark.m05
def test_m05_t07_insufficient_permission(client: TestClient) -> None:
    """M5-T07: Insufficient permission — user without specific permission returns 403 FORBIDDEN."""
    # Log in as general_viewer
    login_resp = client.post("/api/v1/auth/demo-login", json={"role": "general_viewer"})
    assert login_resp.status_code == 200
    token = login_resp.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Can access customer.view
    view_resp = client.get("/api/v1/customers?page=1&page_size=5", headers=headers)
    assert view_resp.status_code == 200

    # Cannot access customer.create (permission denied 403 FORBIDDEN)
    create_resp = client.post(
        "/api/v1/customers",
        json={
            "customer_code": "CUST-DENIED",
            "contact_name": "Denied Test",
            "email": "denied@example.com",
            "region_id": 1,
            "customer_type": "B2B",
            "acquisition_channel": "Direct",
        },
        headers=headers,
    )
    assert create_resp.status_code == 403
    assert create_resp.json()["error"]["code"] == "FORBIDDEN"


@pytest.mark.m05
def test_m05_t08_privilege_escalation_attempt(client: TestClient) -> None:
    """M5-T08: Privilege escalation attempt — tampered JWT or fake secret returns 401."""
    # 1. Token signed with wrong secret key claiming to be owner
    fake_payload = {
        "sub": "1",
        "email": "owner@nexora.local",
        "full_name": "Fake Owner",
        "role": "owner",
        "permissions": ["user.manage", "customer.create", "customer.delete"],
        "is_owner": True,
        "jti": str(uuid.uuid4()),
        "exp": int((datetime.now(UTC) + timedelta(hours=1)).timestamp()),
    }
    fake_secret = "completely-wrong-secret-key-that-is-at-least-32-bytes-long"
    forged_token = jwt.encode(fake_payload, fake_secret, algorithm="HS256")
    resp = client.get("/api/v1/customers", headers={"Authorization": f"Bearer {forged_token}"})
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "UNAUTHORIZED"

    # 2. Tampered valid token (corrupt the signature part)
    login_resp = client.post("/api/v1/auth/demo-login", json={"role": "data_analyst"})
    valid_token = login_resp.json()["data"]["access_token"]
    corrupted_token = valid_token[:-6] + "xxxxxx"

    resp2 = client.get("/api/v1/customers", headers={"Authorization": f"Bearer {corrupted_token}"})
    assert resp2.status_code == 401
    assert resp2.json()["error"]["code"] == "UNAUTHORIZED"


@pytest.mark.m05
def test_m05_t09_session_expiration(client: TestClient) -> None:
    """M5-T09: Session expiration — expired JWT token returns 401 with expiration error."""
    expired_payload = {
        "sub": "1",
        "email": "owner@nexora.local",
        "full_name": "Owner",
        "role": "owner",
        "permissions": ["customer.view"],
        "is_owner": True,
        "jti": str(uuid.uuid4()),
        "iat": int((datetime.now(UTC) - timedelta(hours=2)).timestamp()),
        "exp": int((datetime.now(UTC) - timedelta(hours=1)).timestamp()),  # expired 1 hour ago
    }
    expired_token = jwt.encode(
        expired_payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm
    )

    resp = client.get("/api/v1/customers", headers={"Authorization": f"Bearer {expired_token}"})
    assert resp.status_code == 401
    data = resp.json()
    assert data["error"]["code"] == "UNAUTHORIZED"
    assert "expired" in data["error"]["message"].lower()


@pytest.mark.m05
def test_m05_t10_logout_revocation(client: TestClient) -> None:
    """M5-T10: Logout revocation — logging out revokes JTI; subsequent calls return 401."""
    # Log in
    login_resp = client.post("/api/v1/auth/demo-login", json={"role": "executive"})
    assert login_resp.status_code == 200
    token = login_resp.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Verify session is valid
    me_resp = client.get("/api/v1/auth/me", headers=headers)
    assert me_resp.status_code == 200
    assert me_resp.json()["data"]["role"] == "executive"

    # Log out
    logout_resp = client.post("/api/v1/auth/logout", headers=headers)
    assert logout_resp.status_code == 200
    assert logout_resp.json()["success"] is True

    # Attempt to reuse the revoked token
    post_logout_resp = client.get("/api/v1/auth/me", headers=headers)
    assert post_logout_resp.status_code == 401
    data = post_logout_resp.json()
    assert data["error"]["code"] == "UNAUTHORIZED"
    assert "revoked" in data["error"]["message"].lower()


@pytest.mark.m05
def test_m05_t11_password_hashing_security(db_session: Session) -> None:
    """M5-T11: Password hashing security — verify stored passwords use Argon2."""
    users = db_session.scalars(select(User)).all()
    assert len(users) >= 6

    for user in users:
        assert user.password_hash is not None
        # Must start with $argon2id$ or $argon2i$
        assert user.password_hash.startswith("$argon2"), (
            f"User {user.email} password hash does not use Argon2: {user.password_hash[:15]}"
        )
        # Verify plaintext passwords are never stored
        assert user.password_hash != "NexoraOwnerPass2026!"
        assert user.password_hash != "NexoraDemoPass2026!"
        assert len(user.password_hash) > 50


@pytest.mark.m05
def test_m05_t12_backend_authorization_enforcement(client: TestClient) -> None:
    """M5-T12: Backend authorization enforcement — direct API calls strictly enforce RBAC."""
    # 1. Owner can create customer via API
    owner_login = client.post(
        "/api/v1/auth/login",
        json={"email": "owner@nexora.local", "password": "NexoraOwnerPass2026!"},
    )
    assert owner_login.status_code == 200
    owner_token = owner_login.json()["data"]["access_token"]
    owner_headers = {"Authorization": f"Bearer {owner_token}"}

    test_code = f"AUTH-{uuid.uuid4().hex[:6].upper()}"
    create_resp = client.post(
        "/api/v1/customers",
        json={
            "customer_code": test_code,
            "company_name": "DirectAuth Corp",
            "contact_name": "DirectAuth EnforceTest",
            "email": f"{test_code.lower()}@test.local",
            "region_id": 1,
            "customer_type": "B2B",
            "acquisition_channel": "Direct",
        },
        headers=owner_headers,
    )
    assert create_resp.status_code == 201
    created_cust = create_resp.json()["data"]
    cust_id = created_cust["id"]

    # 2. Demo role tries to update that customer -> 403 Forbidden
    analyst_login = client.post("/api/v1/auth/demo-login", json={"role": "data_analyst"})
    analyst_token = analyst_login.json()["data"]["access_token"]
    analyst_headers = {"Authorization": f"Bearer {analyst_token}"}

    update_resp = client.put(
        f"/api/v1/customers/{cust_id}",
        json={"contact_name": "TamperedByAnalyst"},
        headers=analyst_headers,
    )
    assert update_resp.status_code == 403
    assert update_resp.json()["error"]["code"] == "FORBIDDEN"

    # 3. Owner updates customer -> 200 OK
    owner_update = client.put(
        f"/api/v1/customers/{cust_id}",
        json={"contact_name": "UpdatedByOwner"},
        headers=owner_headers,
    )
    assert owner_update.status_code == 200
    assert owner_update.json()["data"]["contact_name"] == "UpdatedByOwner"

    # 4. Demo role tries to delete -> 403 Forbidden
    del_demo = client.delete(f"/api/v1/customers/{cust_id}", headers=analyst_headers)
    assert del_demo.status_code == 403
    assert del_demo.json()["error"]["code"] == "FORBIDDEN"

    # 5. Owner deletes customer -> 200 OK
    del_owner = client.delete(f"/api/v1/customers/{cust_id}", headers=owner_headers)
    assert del_owner.status_code == 200
