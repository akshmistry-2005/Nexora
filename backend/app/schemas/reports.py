from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ReportCatalogueItem(BaseModel):
    """Metadata item in the enterprise report catalogue."""

    report_id: str
    name: str
    domain: str
    description: str
    cadence: str
    exportable: bool = True
    columns: list[str]
    sensitive_columns: list[str] = Field(default_factory=list)


class ReportDataResponse(BaseModel):
    """Full structured report dataset response."""

    report_id: str
    name: str
    domain: str
    generated_at: datetime
    total_rows: int
    columns: list[str]
    summary: dict[str, Any]
    rows: list[dict[str, Any]]
    synthetic_notice: str = (
        "Synthetic Data Demonstration — Generated for Local Analytics Evaluation"
    )


class SavedViewCreate(BaseModel):
    """Payload to create a user-saved view."""

    section: str = Field(..., max_length=50, description="Dashboard/report section key")
    name: str = Field(..., min_length=1, max_length=100, description="Descriptive view name")
    filter_config: dict[str, Any] = Field(..., description="Serialized filter state")
    is_shared: bool = Field(default=False, description="Whether view is visible to all users")


class SavedViewUpdate(BaseModel):
    """Payload to update an existing saved view."""

    name: str | None = Field(default=None, min_length=1, max_length=100)
    filter_config: dict[str, Any] | None = None
    is_shared: bool | None = None


class SavedViewRead(BaseModel):
    """Representation of a persisted user-saved view."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    creator_name: str | None = None
    section: str
    name: str
    filter_config: dict[str, Any]
    is_shared: bool
    created_at: datetime
    updated_at: datetime | None = None


class ExportRequest(BaseModel):
    """Parameters for on-demand CSV report export."""

    report_id: str
    format: str = Field(default="csv", description="Export format: 'csv' or 'pdf'")
    filters: dict[str, Any] | None = None
    limit: int = Field(default=10000, ge=1, le=50000)
