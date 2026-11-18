from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any, Optional

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.auth import User


class DataSource(Base, TimestampMixin):
    """Data source registry record."""

    __tablename__ = "data_sources"
    __table_args__ = (CheckConstraint("file_size_bytes >= 0", name="ck_datasource_size"),)

    organization_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    source_type: Mapped[str] = mapped_column(String(30), default="CSV", nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    file_checksum: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    uploaded_by_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )

    import_jobs: Mapped[list["ImportJob"]] = relationship(
        back_populates="data_source", cascade="all, delete-orphan"
    )


class ImportJob(Base):
    """Import job execution state and metadata."""

    __tablename__ = "import_jobs"
    __table_args__ = (
        CheckConstraint(
            "status IN ('queued', 'validating', 'staging', 'cleaning', "
            "'completed', 'failed', 'rolled_back')",
            name="ck_import_status",
        ),
        CheckConstraint("total_rows >= 0", name="ck_import_total_rows"),
        CheckConstraint("loaded_rows >= 0", name="ck_import_loaded_rows"),
        CheckConstraint("rejected_rows >= 0", name="ck_import_rejected_rows"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    data_source_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("data_sources.id", ondelete="CASCADE"), nullable=False, index=True
    )
    target_entity: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(25), default="queued", nullable=False, index=True)
    total_rows: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    loaded_rows: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    rejected_rows: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    mapping_config: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    error_details: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    data_source: Mapped["DataSource"] = relationship(back_populates="import_jobs")
    staging_records: Mapped[list["StagingRecord"]] = relationship(
        back_populates="import_job", cascade="all, delete-orphan"
    )
    pipeline_runs: Mapped[list["PipelineRun"]] = relationship(back_populates="import_job")


class StagingRecord(Base):
    """Raw uploaded rows staged before and during cleaning."""

    __tablename__ = "staging_records"
    __table_args__ = (
        CheckConstraint("row_number > 0", name="ck_staging_row_number"),
        CheckConstraint(
            "validation_status IN ('valid', 'invalid', 'cleaned', 'curated')",
            name="ck_staging_status",
        ),
    )

    import_job_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("import_jobs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    row_number: Mapped[int] = mapped_column(Integer, nullable=False)
    raw_data: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    cleaned_data: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    validation_status: Mapped[str] = mapped_column(String(20), default="valid", nullable=False)
    issues: Mapped[list[Any] | None] = mapped_column(JSONB, nullable=True)

    import_job: Mapped["ImportJob"] = relationship(back_populates="staging_records")


class PipelineRun(Base):
    """Observability tracking for data preparation and pipeline executions."""

    __tablename__ = "pipeline_runs"
    __table_args__ = (
        CheckConstraint(
            "status IN ('running', 'success', 'failed', 'retried')",
            name="ck_pipeline_status",
        ),
    )

    import_job_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("import_jobs.id", ondelete="SET NULL"), nullable=True, index=True
    )
    pipeline_name: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="running", nullable=False)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    metrics: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    import_job: Mapped[Optional["ImportJob"]] = relationship(back_populates="pipeline_runs")


class SavedView(Base, TimestampMixin):
    """User-saved filter configurations for reports and dashboards."""

    __tablename__ = "saved_views"

    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    section: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    filter_config: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    is_shared: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    user: Mapped["User"] = relationship()


class AuditLog(Base):
    """Append-only operational and security audit trail."""

    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    organization_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True, index=True
    )
    actor_user_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    actor_role: Mapped[str] = mapped_column(String(50), nullable=False)
    action_type: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    entity_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    entity_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    details: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )


class AnomalyAlert(Base):
    """Detected business anomalies with baselines and explanations."""

    __tablename__ = "anomaly_alerts"
    __table_args__ = (
        CheckConstraint(
            "domain IN ('sales', 'transaction', 'inventory', 'marketing', 'operations')",
            name="ck_anomaly_domain",
        ),
        CheckConstraint(
            "severity IN ('low', 'medium', 'high', 'critical')",
            name="ck_anomaly_severity",
        ),
        CheckConstraint(
            "status IN ('open', 'acknowledged', 'resolved', 'dismissed')",
            name="ck_anomaly_status",
        ),
    )

    organization_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    domain: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    entity_identifier: Mapped[str] = mapped_column(String(100), nullable=False)
    metric_name: Mapped[str] = mapped_column(String(80), nullable=False)
    observed_value: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    baseline_value: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    deviation_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    z_score: Mapped[Decimal | None] = mapped_column(Numeric(6, 2), nullable=True)
    severity: Mapped[str] = mapped_column(String(20), default="medium", nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="open", nullable=False, index=True)
    detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
    acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    acknowledged_by_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
