from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class DataSourceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    organization_id: int
    name: str
    source_type: str
    file_name: str
    file_size_bytes: int
    file_checksum: str
    uploaded_by_id: int
    created_at: datetime


class ImportJobRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    data_source_id: int
    target_entity: str
    status: str
    total_rows: int
    loaded_rows: int
    rejected_rows: int
    mapping_config: dict[str, Any]
    error_details: dict[str, Any] | None
    started_at: datetime | None
    completed_at: datetime | None


class StagingRecordRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    import_job_id: int
    row_number: int
    raw_data: dict[str, Any]
    cleaned_data: dict[str, Any] | None
    validation_status: str
    issues: list[Any] | None


class PreviewResponse(BaseModel):
    file_name: str
    file_size_bytes: int
    file_checksum: str
    target_entity: str
    detected_headers: list[str]
    suggested_mapping: dict[str, str]
    missing_required_headers: list[str]
    total_detected_rows: int
    preview_rows: list[dict[str, Any]]
    inferred_types: dict[str, str]
    is_duplicate: bool


class ImportResultResponse(BaseModel):
    import_job_id: int
    data_source_id: int
    target_entity: str
    status: str
    total_rows: int
    loaded_rows: int
    rejected_rows: int
    error_details: dict[str, Any] | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
