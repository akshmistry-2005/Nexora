"""API endpoints for data pipeline observability, execution tracking, and safe retry."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.permissions.dependencies import AuthenticatedUser, require_permission
from app.schemas.common import StandardResponse
from app.schemas.pipelines import (
    PipelineHealthSummary,
    PipelineRetryResponse,
    PipelineRunRead,
)
from app.services import pipelines as pipeline_service

router = APIRouter(prefix="/pipelines", tags=["Data Pipelines & Observability"])


@router.get(
    "/runs",
    response_model=StandardResponse[list[PipelineRunRead]],
    summary="List pipeline execution history",
)
def list_pipeline_runs_endpoint(
    db: Annotated[Session, Depends(get_db)],
    _: AuthenticatedUser = Depends(require_permission("dataquality.view")),
    status_filter: Annotated[
        str | None,
        Query(
            alias="status",
            description="Status filter: running, success, failed, retried",
        ),
    ] = None,
    pipeline_name: Annotated[str | None, Query(description="Pipeline name filter")] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> StandardResponse[list[PipelineRunRead]]:
    """Retrieve executed pipeline runs with execution metrics and status."""
    runs, _total = pipeline_service.get_pipeline_runs(
        db,
        status=status_filter,
        pipeline_name=pipeline_name,
        limit=limit,
        offset=offset,
    )
    return StandardResponse(data=[PipelineRunRead.model_validate(r) for r in runs])


@router.get(
    "/summary",
    response_model=StandardResponse[PipelineHealthSummary],
    summary="Get pipeline observability scorecard",
)
def get_pipeline_summary_endpoint(
    db: Annotated[Session, Depends(get_db)],
    _: AuthenticatedUser = Depends(require_permission("dataquality.view")),
) -> StandardResponse[PipelineHealthSummary]:
    """Aggregate health scorecard, failure telemetry, and last-successful refresh timestamps."""
    summary = pipeline_service.get_pipeline_health_summary(db)
    return StandardResponse(data=summary)


@router.get(
    "/runs/{run_id}",
    response_model=StandardResponse[PipelineRunRead],
    summary="Get single pipeline execution details",
)
def get_pipeline_run_detail_endpoint(
    run_id: int,
    db: Annotated[Session, Depends(get_db)],
    _: AuthenticatedUser = Depends(require_permission("dataquality.view")),
) -> StandardResponse[PipelineRunRead]:
    """Retrieve complete metadata and execution metrics for a single pipeline run."""
    run = pipeline_service.get_pipeline_run_by_id(db, run_id)
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pipeline run #{run_id} not found.",
        )
    return StandardResponse(data=PipelineRunRead.model_validate(run))


@router.post(
    "/runs/{run_id}/retry",
    response_model=StandardResponse[PipelineRetryResponse],
    summary="Execute safe pipeline retry (Quality Manage / Owner)",
)
def retry_pipeline_endpoint(
    run_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: AuthenticatedUser = Depends(require_permission("dataquality.manage")),
    notes: Annotated[str | None, Query(description="Optional notes on retry rationale")] = None,
) -> StandardResponse[PipelineRetryResponse]:
    """Execute safe retry without corrupting destination state, preserving refresh telemetry."""
    try:
        response = pipeline_service.retry_pipeline_run(
            db,
            run_id=run_id,
            actor_user_id=current_user.id,
            actor_role=current_user.role,
            notes=notes,
        )
        return StandardResponse(data=response)
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(err),
        ) from err
