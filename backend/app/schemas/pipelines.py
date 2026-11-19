"""Pydantic schemas for data pipeline monitoring and execution tracking."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class PipelineRunRead(BaseModel):
    """Structured representation of an executed data pipeline run."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    import_job_id: int | None = None
    pipeline_name: str = Field(..., description="Name of the pipeline process")
    status: str = Field(..., description="Status: running, success, failed, retried")
    duration_ms: int | None = Field(None, description="Execution duration in milliseconds")
    metrics: dict[str, Any] = Field(default_factory=dict, description="Execution metrics")
    started_at: datetime
    ended_at: datetime | None = None


class PipelineSummaryItem(BaseModel):
    """Aggregate health and last-refresh telemetry for an individual pipeline."""

    pipeline_name: str
    total_runs: int
    successful_runs: int
    failed_runs: int
    last_successful_run_at: datetime | None = None
    last_run_status: str | None = None


class PipelineHealthSummary(BaseModel):
    """Comprehensive observability scorecard across all ingestion and ETL pipelines."""

    active_pipelines_count: int
    total_runs_count: int
    failed_runs_count: int
    last_successful_refresh: datetime | None = None
    pipelines: list[PipelineSummaryItem]
    synthetic_notice: str = (
        "Demonstration Environment: All telemetry metrics reflect local synthetic execution."
    )


class PipelineRetryResponse(BaseModel):
    """Response payload following a safe pipeline retry operation."""

    previous_run_id: int
    new_run_id: int
    pipeline_name: str
    status: str
    message: str
    retried_at: datetime
