"""API endpoints for administration, immutable audit inspection, and platform control."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.permissions.dependencies import (
    AuthenticatedUser,
    require_owner,
    require_permission,
)
from app.schemas.admin import (
    AuditLogRead,
    AuditLogSummary,
    ResetDemoResponse,
    SystemStatusResponse,
    UserAdminRead,
)
from app.schemas.common import StandardResponse
from app.services import admin as admin_service

router = APIRouter(prefix="/admin", tags=["Administration & Auditability"])


@router.get(
    "/audit-logs",
    response_model=StandardResponse[list[AuditLogRead]],
    summary="Inspect append-only security and operational audit trail",
)
def list_audit_logs_endpoint(
    db: Annotated[Session, Depends(get_db)],
    _: AuthenticatedUser = Depends(require_permission("audit.view")),
    action_type: Annotated[str | None, Query(description="Filter by action type")] = None,
    actor_role: Annotated[str | None, Query(description="Filter by actor role")] = None,
    entity_type: Annotated[str | None, Query(description="Filter by entity type")] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> StandardResponse[list[AuditLogRead]]:
    """Retrieve immutable audit trail records with operational context and actor attribution."""
    logs, _total = admin_service.get_audit_logs(
        db,
        action_type=action_type,
        actor_role=actor_role,
        entity_type=entity_type,
        limit=limit,
        offset=offset,
    )
    return StandardResponse(data=[AuditLogRead.model_validate(log) for log in logs])


@router.get(
    "/audit-summary",
    response_model=StandardResponse[AuditLogSummary],
    summary="Get audit trail KPI summary",
)
def get_audit_summary_endpoint(
    db: Annotated[Session, Depends(get_db)],
    _: AuthenticatedUser = Depends(require_permission("audit.view")),
) -> StandardResponse[AuditLogSummary]:
    """Breakdown of total audit events grouped by action type and role."""
    summary = admin_service.get_audit_summary(db)
    return StandardResponse(data=summary)


@router.get(
    "/users",
    response_model=StandardResponse[list[UserAdminRead]],
    summary="List all platform users and roles (User Manage / Owner)",
)
def list_users_endpoint(
    db: Annotated[Session, Depends(get_db)],
    _: AuthenticatedUser = Depends(require_permission("user.manage")),
) -> StandardResponse[list[UserAdminRead]]:
    """Retrieve directory of platform users and assigned authorization roles."""
    users = admin_service.list_users(db)
    return StandardResponse(data=users)


@router.get(
    "/system-status",
    response_model=StandardResponse[SystemStatusResponse],
    summary="Get system health, environment mode, and synthetic notice",
)
def get_system_status_endpoint(
    db: Annotated[Session, Depends(get_db)],
    _: AuthenticatedUser = Depends(require_permission("dashboard.view")),
) -> StandardResponse[SystemStatusResponse]:
    """Evaluate database connectivity, table record counts, and environment notice."""
    status_data = admin_service.get_system_status(db)
    return StandardResponse(data=status_data)


@router.post(
    "/reset-demo",
    response_model=StandardResponse[ResetDemoResponse],
    summary="Reset demonstration dataset state (Owner ONLY)",
)
def reset_demo_endpoint(
    db: Annotated[Session, Depends(get_db)],
    current_user: AuthenticatedUser = Depends(require_owner),
) -> StandardResponse[ResetDemoResponse]:
    """Execute owner-authorized reset of demonstration environment and record audit log."""
    res = admin_service.reset_demo_data(db, actor_user_id=current_user.id)
    return StandardResponse(data=res)
