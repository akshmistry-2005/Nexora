from collections.abc import Callable
from dataclasses import dataclass

from fastapi import Depends, Header, Request
from sqlalchemy.orm import Session

from app.core.exceptions import AuthenticationError, PermissionDeniedError
from app.db.session import get_db
from app.models.auth import User
from app.services.auth import auth_service


@dataclass
class AuthenticatedUser:
    """Convenient container holding identity and claims for the authenticated request."""

    user: User
    id: int
    email: str
    full_name: str
    role: str
    is_owner: bool
    permissions: list[str]
    token: str

    def has_permission(self, permission_code: str) -> bool:
        return self.is_owner or (permission_code in self.permissions)


def get_token_from_request(
    request: Request,
    authorization: str | None = Header(default=None),
) -> str:
    """Extract bearer token from Authorization header or cookie."""
    if authorization and authorization.startswith("Bearer "):
        return authorization.split(" ", 1)[1].strip()

    cookie_token = request.cookies.get("nexora_session")
    if cookie_token:
        return cookie_token

    raise AuthenticationError("Authentication token is required to access this resource.")


def get_current_user(
    token: str = Depends(get_token_from_request),
    session: Session = Depends(get_db),
) -> AuthenticatedUser:
    """FastAPI dependency to extract, decode, and validate the current authenticated user."""
    payload = auth_service.decode_access_token(token)
    user_id = int(payload.get("sub", 0))

    user = session.get(User, user_id)
    if not user or not user.is_active:
        raise AuthenticationError("Authenticated user account is inactive or not found.")

    role = payload.get("role", "general_viewer")
    permissions = payload.get("permissions", [])
    is_owner = bool(payload.get("is_owner", False))

    return AuthenticatedUser(
        user=user,
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=role,
        is_owner=is_owner,
        permissions=permissions,
        token=token,
    )


def require_permission(permission_code: str) -> Callable[[AuthenticatedUser], AuthenticatedUser]:
    """Dependency factory checking that the authenticated user possesses the required permission."""

    def permission_checker(
        current_user: AuthenticatedUser = Depends(get_current_user),
    ) -> AuthenticatedUser:
        if not current_user.has_permission(permission_code):
            raise PermissionDeniedError(
                f"Action forbidden: missing required permission '{permission_code}'."
            )
        return current_user

    return permission_checker


def require_owner(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> AuthenticatedUser:
    """Dependency ensuring only the private platform Owner can execute this action."""
    if not current_user.is_owner or current_user.role != "owner":
        raise PermissionDeniedError(
            "Access restricted: this administrative operation requires the Owner account."
        )
    return current_user
