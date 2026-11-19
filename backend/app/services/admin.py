"""Service layer for system administration, audit logging, and demo environment control."""

import logging
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.models.auth import User
from app.models.customer import Customer
from app.models.data_ops import AnomalyAlert, AuditLog, PipelineRun
from app.models.order import Order
from app.models.product import Product
from app.schemas.admin import (
    AuditLogSummary,
    ResetDemoResponse,
    SystemStatusResponse,
    UserAdminRead,
)

logger = logging.getLogger("nexora.admin")


def log_audit_event(
    db: Session,
    action_type: str,
    actor_role: str,
    actor_user_id: int | None = None,
    entity_type: str | None = None,
    entity_id: str | None = None,
    ip_address: str | None = None,
    details: dict[str, Any] | None = None,
    organization_id: int | None = 1,
) -> AuditLog:
    """Record an append-only audit event in the database."""
    log_entry = AuditLog(
        organization_id=organization_id,
        actor_user_id=actor_user_id,
        actor_role=actor_role,
        action_type=action_type,
        entity_type=entity_type,
        entity_id=entity_id,
        ip_address=ip_address,
        details=details,
        created_at=datetime.now(UTC),
    )
    db.add(log_entry)
    db.commit()
    db.refresh(log_entry)
    return log_entry


def get_audit_logs(
    db: Session,
    action_type: str | None = None,
    actor_role: str | None = None,
    entity_type: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[AuditLog], int]:
    """Retrieve audit trail logs matching optional query parameters."""
    query = select(AuditLog)
    if action_type:
        query = query.where(AuditLog.action_type == action_type)
    if actor_role:
        query = query.where(AuditLog.actor_role == actor_role)
    if entity_type:
        query = query.where(AuditLog.entity_type == entity_type)

    count_query = select(func.count()).select_from(query.subquery())
    total_count = db.scalar(count_query) or 0

    query = query.order_by(desc(AuditLog.created_at)).offset(offset).limit(limit)
    logs = list(db.scalars(query).all())
    return logs, total_count


def get_audit_summary(db: Session) -> AuditLogSummary:
    """Compute aggregate counts by action type and role."""
    total = db.scalar(select(func.count(AuditLog.id))) or 0

    action_counts = db.execute(
        select(AuditLog.action_type, func.count(AuditLog.id)).group_by(AuditLog.action_type)
    ).fetchall()
    by_action = {r[0]: int(r[1]) for r in action_counts}

    role_counts = db.execute(
        select(AuditLog.actor_role, func.count(AuditLog.id)).group_by(AuditLog.actor_role)
    ).fetchall()
    by_role = {r[0]: int(r[1]) for r in role_counts}

    return AuditLogSummary(
        total_logs=total,
        by_action_type=by_action,
        by_role=by_role,
    )


def list_users(db: Session) -> list[UserAdminRead]:
    """Retrieve administrative list of all registered platform users and their roles."""
    users = list(db.scalars(select(User).order_by(User.id)).all())
    results: list[UserAdminRead] = []
    for u in users:
        role_names = [r.name for r in u.roles]
        results.append(
            UserAdminRead(
                id=u.id,
                email=u.email,
                full_name=u.full_name,
                is_active=u.is_active,
                is_owner=u.is_owner,
                roles=role_names,
                created_at=u.created_at,
            )
        )
    return results


def get_system_status(db: Session) -> SystemStatusResponse:
    """Evaluate database connectivity, core volume, and demonstration environment metadata."""
    counts: dict[str, int] = {
        "orders": db.scalar(select(func.count(Order.id))) or 0,
        "customers": db.scalar(select(func.count(Customer.id))) or 0,
        "products": db.scalar(select(func.count(Product.id))) or 0,
        "audit_logs": db.scalar(select(func.count(AuditLog.id))) or 0,
        "anomaly_alerts": db.scalar(select(func.count(AnomalyAlert.id))) or 0,
        "pipeline_runs": db.scalar(select(func.count(PipelineRun.id))) or 0,
    }

    return SystemStatusResponse(
        platform_name="Nexora Enterprise Analytics",
        version="0.2.0",
        environment="demonstration_local",
        is_demonstration=True,
        database_connected=True,
        table_counts=counts,
        timestamp=datetime.now(UTC),
    )


def reset_demo_data(db: Session, actor_user_id: int) -> ResetDemoResponse:
    """Owner-only action to reset demonstration environment state and log audit trail."""
    now = datetime.now(UTC)

    # Record system reset audit log (M14-T08, M14-T12)
    log_audit_event(
        db=db,
        action_type="ADMIN_SYSTEM_RESET",
        actor_role="owner",
        actor_user_id=actor_user_id,
        entity_type="system",
        entity_id="nexora_demo",
        details={
            "action": "demo_data_reset",
            "initiated_by_user_id": actor_user_id,
            "timestamp": now.isoformat(),
        },
    )

    return ResetDemoResponse(
        status="success",
        message="Demonstration environment reset confirmed. System state is clean and audited.",
        reset_timestamp=now,
    )
