"""Service layer for pipeline monitoring, execution telemetry, and safe retry management."""

import logging
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.models.data_ops import AuditLog, PipelineRun
from app.schemas.pipelines import (
    PipelineHealthSummary,
    PipelineRetryResponse,
    PipelineSummaryItem,
)

logger = logging.getLogger("nexora.pipelines")


def create_pipeline_run(
    db: Session,
    pipeline_name: str,
    status: str = "running",
    metrics: dict[str, Any] | None = None,
    import_job_id: int | None = None,
) -> PipelineRun:
    """Create a new pipeline execution record."""
    valid_statuses = ("running", "success", "failed", "retried")
    if status not in valid_statuses:
        raise ValueError(f"Invalid pipeline status '{status}'. Must be one of {valid_statuses}")

    run = PipelineRun(
        import_job_id=import_job_id,
        pipeline_name=pipeline_name,
        status=status,
        metrics=metrics or {},
        started_at=datetime.now(UTC),
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    return run


def get_pipeline_runs(
    db: Session,
    status: str | None = None,
    pipeline_name: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[PipelineRun], int]:
    """Retrieve pipeline run history matching optional filters."""
    query = select(PipelineRun)
    if status:
        query = query.where(PipelineRun.status == status.lower())
    if pipeline_name:
        query = query.where(PipelineRun.pipeline_name == pipeline_name)

    count_query = select(func.count()).select_from(query.subquery())
    total_count = db.scalar(count_query) or 0

    query = query.order_by(desc(PipelineRun.started_at)).offset(offset).limit(limit)
    runs = list(db.scalars(query).all())
    return runs, total_count


def get_pipeline_run_by_id(db: Session, run_id: int) -> PipelineRun | None:
    """Retrieve a single pipeline run by primary key."""
    return db.get(PipelineRun, run_id)


def retry_pipeline_run(
    db: Session,
    run_id: int,
    actor_user_id: int,
    actor_role: str,
    notes: str | None = None,
) -> PipelineRetryResponse:
    """Execute safe retry of a failed or retried pipeline run."""
    run = db.get(PipelineRun, run_id)
    if not run:
        raise ValueError(f"Pipeline run #{run_id} not found.")

    if run.status not in ("failed", "retried"):
        raise ValueError(
            f"Only failed/retried pipeline runs can be retried. Status is '{run.status}'."
        )

    # 1. Preserve last successful refresh timestamp (M14-T04)
    last_refresh = run.metrics.get("last_successful_refresh")
    if not last_refresh:
        # Look up most recent successful run for this pipeline
        prev_success = db.scalar(
            select(PipelineRun)
            .where(
                PipelineRun.pipeline_name == run.pipeline_name,
                PipelineRun.status == "success",
            )
            .order_by(desc(PipelineRun.ended_at))
            .limit(1)
        )
        if prev_success and prev_success.ended_at:
            last_refresh = prev_success.ended_at.isoformat()

    # 2. Mark previous run as retried
    run.status = "retried"

    # 3. Create clean retry attempt
    now = datetime.now(UTC)
    retry_metrics: dict[str, Any] = {
        "retried_from_run_id": run.id,
        "retry_notes": notes,
        "last_successful_refresh": last_refresh,
        "retry_attempt": run.metrics.get("retry_attempt", 0) + 1,
    }

    new_run = PipelineRun(
        import_job_id=run.import_job_id,
        pipeline_name=run.pipeline_name,
        status="running",
        duration_ms=None,
        metrics=retry_metrics,
        started_at=now,
    )
    db.add(new_run)
    db.flush()

    # 4. Append operational audit log (M14-T08)
    audit = AuditLog(
        organization_id=1,
        actor_user_id=actor_user_id,
        actor_role=actor_role,
        action_type="PIPELINE_RETRY",
        entity_type="pipeline_runs",
        entity_id=str(new_run.id),
        details={
            "previous_run_id": run.id,
            "pipeline_name": run.pipeline_name,
            "last_successful_refresh": last_refresh,
            "notes": notes,
        },
    )
    db.add(audit)
    db.commit()
    db.refresh(new_run)

    return PipelineRetryResponse(
        previous_run_id=run.id,
        new_run_id=new_run.id,
        pipeline_name=new_run.pipeline_name,
        status=new_run.status,
        message=f"Pipeline '{run.pipeline_name}' safely retried with new run #{new_run.id}.",
        retried_at=now,
    )


def get_pipeline_health_summary(db: Session) -> PipelineHealthSummary:
    """Compute aggregate pipeline scorecard and preserve last successful refresh telemetry."""
    total_runs = db.scalar(select(func.count(PipelineRun.id))) or 0
    failed_runs = (
        db.scalar(select(func.count(PipelineRun.id)).where(PipelineRun.status == "failed")) or 0
    )

    # Distinct pipeline names
    pipeline_names = list(db.scalars(select(PipelineRun.pipeline_name).distinct()).all())

    items: list[PipelineSummaryItem] = []
    global_last_refresh: datetime | None = None

    for name in pipeline_names:
        tot = (
            db.scalar(select(func.count(PipelineRun.id)).where(PipelineRun.pipeline_name == name))
            or 0
        )
        succ = (
            db.scalar(
                select(func.count(PipelineRun.id)).where(
                    PipelineRun.pipeline_name == name, PipelineRun.status == "success"
                )
            )
            or 0
        )
        fail = (
            db.scalar(
                select(func.count(PipelineRun.id)).where(
                    PipelineRun.pipeline_name == name, PipelineRun.status == "failed"
                )
            )
            or 0
        )

        last_succ = db.scalar(
            select(PipelineRun.ended_at)
            .where(PipelineRun.pipeline_name == name, PipelineRun.status == "success")
            .order_by(desc(PipelineRun.ended_at))
            .limit(1)
        )

        last_run = db.scalar(
            select(PipelineRun)
            .where(PipelineRun.pipeline_name == name)
            .order_by(desc(PipelineRun.started_at))
            .limit(1)
        )

        if last_succ and (global_last_refresh is None or last_succ > global_last_refresh):
            global_last_refresh = last_succ

        items.append(
            PipelineSummaryItem(
                pipeline_name=name,
                total_runs=tot,
                successful_runs=succ,
                failed_runs=fail,
                last_successful_run_at=last_succ,
                last_run_status=last_run.status if last_run else None,
            )
        )

    return PipelineHealthSummary(
        active_pipelines_count=len(pipeline_names),
        total_runs_count=total_runs,
        failed_runs_count=failed_runs,
        last_successful_refresh=global_last_refresh,
        pipelines=items,
    )
