"""Pydantic schemas for administration, security audit trails, and system status."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class AuditLogRead(BaseModel):
    """Structured representation of an append-only security or operational audit event."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    organization_id: int | None = None
    actor_user_id: int | None = None
    actor_role: str = Field(..., description="Role of the actor at event time")
    action_type: str = Field(..., description="Normalized action identifier")
    entity_type: str | None = None
    entity_id: str | None = None
    ip_address: str | None = None
    details: dict[str, Any] | None = None
    created_at: datetime


class AuditLogSummary(BaseModel):
    """Aggregate breakdown of recorded audit operations across the platform."""

    total_logs: int
    by_action_type: dict[str, int]
    by_role: dict[str, int]


class UserAdminRead(BaseModel):
    """Administrative user view with assigned roles and active state."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    full_name: str
    is_active: bool
    is_owner: bool
    roles: list[str]
    created_at: datetime


class SystemStatusResponse(BaseModel):
    """System health, environment classification, and synthetic dataset metadata."""

    platform_name: str = "Nexora Enterprise Analytics"
    version: str = "0.2.0"
    environment: str = "demonstration_local"
    is_demonstration: bool = True
    database_connected: bool
    synthetic_data_notice: str = (
        "Demonstration Environment: All data, metrics, and logs are synthetically generated."
    )
    table_counts: dict[str, int]
    timestamp: datetime


class ResetDemoResponse(BaseModel):
    """Confirmation payload following an owner-authorized demonstration data reset."""

    status: str = "success"
    message: str
    synthetic_notice: str = (
        "Demonstration dataset safely reseeded. Production state remains isolated."
    )
    reset_timestamp: datetime
