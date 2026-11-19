import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from passlib.hash import argon2
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.config import settings
from app.core.exceptions import AuthenticationError, PermissionDeniedError
from app.models.auth import Role, User
from app.schemas.auth import TokenResponse

# The 5 allow-listed public demonstration roles and their seeded system emails
ALLOWED_DEMO_ROLES: set[str] = {
    "executive",
    "department_manager",
    "data_analyst",
    "data_scientist",
    "general_viewer",
}

DEMO_ROLE_EMAILS: dict[str, str] = {
    "executive": "demo_executive@nexora.local",
    "department_manager": "demo_dept_manager@nexora.local",
    "data_analyst": "demo_analyst@nexora.local",
    "data_scientist": "demo_scientist@nexora.local",
    "general_viewer": "demo_viewer@nexora.local",
}

# In-memory revocation registry for revoked token JTIs (JWT IDs)
_revoked_tokens: set[str] = set()


class AuthService:
    """Authentication and session lifecycle management service."""

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify candidate plaintext password against stored Argon2 hash."""
        try:
            return argon2.verify(plain_password, hashed_password)
        except Exception:
            return False

    def create_access_token(
        self,
        user: User,
        role_name: str,
        permissions: list[str],
        expires_delta: timedelta | None = None,
    ) -> tuple[str, str, int]:
        """Create a signed JWT access token with JTI and expiration."""
        expire_minutes = settings.access_token_expire_minutes
        expires = expires_delta or timedelta(minutes=expire_minutes)
        now = datetime.now(UTC)
        exp_time = now + expires
        token_jti = str(uuid.uuid4())

        payload: dict[str, Any] = {
            "sub": str(user.id),
            "email": user.email,
            "full_name": user.full_name,
            "role": role_name,
            "permissions": permissions,
            "is_owner": user.is_owner,
            "jti": token_jti,
            "iat": int(now.timestamp()),
            "exp": int(exp_time.timestamp()),
        }

        token = jwt.encode(
            payload,
            settings.jwt_secret_key,
            algorithm=settings.jwt_algorithm,
        )
        return token, token_jti, int(expires.total_seconds())

    def decode_access_token(self, token: str) -> dict[str, Any]:
        """Decode and validate JWT access token signature, expiration, and revocation status."""
        try:
            payload = jwt.decode(
                token,
                settings.jwt_secret_key,
                algorithms=[settings.jwt_algorithm],
            )
        except jwt.ExpiredSignatureError as e:
            raise AuthenticationError("Session token has expired. Please log in again.") from e
        except jwt.PyJWTError as e:
            raise AuthenticationError("Invalid authentication token.") from e

        jti = payload.get("jti")
        if jti and jti in _revoked_tokens:
            raise AuthenticationError("Session token has been revoked. Please log in again.")

        return payload

    def revoke_token(self, token: str) -> None:
        """Revoke a token by adding its JTI to the revocation set."""
        try:
            payload = jwt.decode(
                token,
                settings.jwt_secret_key,
                algorithms=[settings.jwt_algorithm],
                options={"verify_exp": False},
            )
            jti = payload.get("jti")
            if jti:
                _revoked_tokens.add(jti)
        except Exception:
            pass

    def get_user_permissions(self, session: Session, user: User) -> list[str]:
        """Fetch all distinct permission codes assigned to the user via their roles."""
        # Query roles with permissions eagerly loaded
        stmt = (
            select(Role)
            .join(User.roles)
            .where(User.id == user.id)
            .options(selectinload(Role.permissions))
        )
        roles = session.scalars(stmt).all()
        perms: set[str] = set()
        for r in roles:
            for p in r.permissions:
                perms.add(p.code)
        return sorted(perms)

    def authenticate_owner(
        self,
        session: Session,
        email: str,
        password: str,
    ) -> TokenResponse:
        """Authenticate the private platform Owner."""
        stmt = (
            select(User)
            .where(User.email == email.strip().lower())
            .options(selectinload(User.roles))
        )
        user = session.scalar(stmt)

        # Constant-time-like rejection for missing user or non-owner
        if not user or not user.is_owner or not user.is_active:
            raise AuthenticationError("Invalid owner credentials.")

        if not self.verify_password(password, user.password_hash):
            raise AuthenticationError("Invalid owner credentials.")

        permissions = self.get_user_permissions(session, user)
        token, _, expires_sec = self.create_access_token(
            user=user,
            role_name="owner",
            permissions=permissions,
        )

        return TokenResponse(
            access_token=token,
            expires_in_seconds=expires_sec,
            user_id=user.id,
            email=user.email,
            full_name=user.full_name,
            role="owner",
            permissions=permissions,
        )

    def authenticate_demo_role(
        self,
        session: Session,
        role_slug: str,
    ) -> TokenResponse:
        """Authenticate a public demo visitor for an allow-listed read-only role."""
        normalized_role = role_slug.strip().lower()

        # Strict Owner protection (M5-T04)
        if normalized_role in ("owner", "admin", "administrator"):
            raise PermissionDeniedError(
                "The Owner/Admin account is protected and cannot be accessed via the public demo."
            )

        if normalized_role not in ALLOWED_DEMO_ROLES:
            raise PermissionDeniedError(
                f"Role '{role_slug}' is not a valid demonstration role. "
                f"Allowed roles: {sorted(ALLOWED_DEMO_ROLES)}"
            )

        demo_email = DEMO_ROLE_EMAILS.get(normalized_role, f"demo_{normalized_role}@nexora.local")
        stmt = select(User).where(User.email == demo_email).options(selectinload(User.roles))
        demo_user = session.scalar(stmt)

        if not demo_user:
            raise AuthenticationError(
                f"Demo account for role '{normalized_role}' not found. Please verify seeding."
            )

        permissions = self.get_user_permissions(session, demo_user)
        token, _, expires_sec = self.create_access_token(
            user=demo_user,
            role_name=normalized_role,
            permissions=permissions,
        )

        return TokenResponse(
            access_token=token,
            expires_in_seconds=expires_sec,
            user_id=demo_user.id,
            email=demo_user.email,
            full_name=demo_user.full_name,
            role=normalized_role,
            permissions=permissions,
        )


auth_service = AuthService()
