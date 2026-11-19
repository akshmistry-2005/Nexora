from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.permissions.dependencies import AuthenticatedUser, get_current_user
from app.schemas.auth import AuthMeResponse, DemoLoginRequest, OwnerLoginRequest, TokenResponse
from app.schemas.common import StandardResponse
from app.services import admin as admin_service
from app.services.auth import auth_service

router = APIRouter(prefix="/auth", tags=["Authentication & Access"])


@router.post(
    "/login",
    response_model=StandardResponse[TokenResponse],
    summary="Private Owner Authentication",
    description=(
        "Authenticate the platform owner using password credentials. "
        "Sets session cookie and returns Bearer token."
    ),
)
def login_owner(
    request: OwnerLoginRequest,
    response: Response,
    session: Session = Depends(get_db),
) -> StandardResponse[TokenResponse]:
    try:
        token_resp = auth_service.authenticate_owner(
            session=session,
            email=request.email,
            password=request.password,
        )
        admin_service.log_audit_event(
            db=session,
            action_type="AUTH_LOGIN_SUCCESS",
            actor_role="owner",
            actor_user_id=token_resp.user_id,
            entity_type="user",
            entity_id=str(token_resp.user_id),
            details={"email": request.email},
        )
    except Exception as e:
        admin_service.log_audit_event(
            db=session,
            action_type="AUTH_LOGIN_FAILURE",
            actor_role="unauthenticated",
            entity_type="user",
            details={"email": request.email, "reason": str(e)},
        )
        raise

    # Set HTTP-only session cookie for web browser clients
    response.set_cookie(
        key="nexora_session",
        value=token_resp.access_token,
        max_age=token_resp.expires_in_seconds,
        httponly=True,
        samesite="lax",
    )
    return StandardResponse(data=token_resp)


@router.post(
    "/demo-login",
    response_model=StandardResponse[TokenResponse],
    summary="Controlled Public Demo Role Selection",
    description=(
        "Access the platform using one of the five allow-listed read-only demonstration roles. "
        "Strictly rejects any attempt to select Owner/Admin."
    ),
)
def login_demo(
    request: DemoLoginRequest,
    response: Response,
    session: Session = Depends(get_db),
) -> StandardResponse[TokenResponse]:
    token_resp = auth_service.authenticate_demo_role(
        session=session,
        role_slug=request.role,
    )
    admin_service.log_audit_event(
        db=session,
        action_type="AUTH_LOGIN_SUCCESS",
        actor_role=request.role,
        actor_user_id=token_resp.user_id,
        entity_type="user",
        entity_id=str(token_resp.user_id),
        details={"email": token_resp.email, "role": request.role},
    )
    response.set_cookie(
        key="nexora_session",
        value=token_resp.access_token,
        max_age=token_resp.expires_in_seconds,
        httponly=True,
        samesite="lax",
    )
    return StandardResponse(data=token_resp)


@router.post(
    "/logout",
    response_model=StandardResponse[dict[str, str]],
    summary="Revoke active session token and clear cookies",
)
def logout(
    response: Response,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> StandardResponse[dict[str, str]]:
    auth_service.revoke_token(current_user.token)
    response.delete_cookie("nexora_session")
    return StandardResponse(data={"message": "Successfully logged out and session revoked."})


@router.get(
    "/me",
    response_model=StandardResponse[AuthMeResponse],
    summary="Inspect current authenticated session profile and permissions",
)
def get_me(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> StandardResponse[AuthMeResponse]:
    return StandardResponse(
        data=AuthMeResponse(
            user_id=current_user.id,
            email=current_user.email,
            full_name=current_user.full_name,
            is_owner=current_user.is_owner,
            role=current_user.role,
            permissions=current_user.permissions,
        )
    )
