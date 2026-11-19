from typing import Any

from pydantic import BaseModel, Field


class QualityDimensionsScore(BaseModel):
    """5 Quality Dimensions scores and overall weighted quality score."""

    completeness: float = Field(..., ge=0.0, le=100.0, description="Completeness dimension score")
    uniqueness: float = Field(..., ge=0.0, le=100.0, description="Uniqueness dimension score")
    validity: float = Field(..., ge=0.0, le=100.0, description="Validity dimension score")
    consistency: float = Field(..., ge=0.0, le=100.0, description="Consistency dimension score")
    timeliness: float = Field(..., ge=0.0, le=100.0, description="Timeliness dimension score")
    overall_score: float = Field(..., ge=0.0, le=100.0, description="Weighted composite score")


class QualityIssue(BaseModel):
    """Specific data quality anomaly or rule violation."""

    row_number: int
    field: str
    issue_type: str
    severity: str
    message: str
    raw_value: Any = None


class TransformationAudit(BaseModel):
    """Audit log entry capturing individual data cleaning mutation."""

    row_number: int
    field: str
    rule: str
    raw_value: Any
    cleaned_value: Any


class QualityEvaluationReport(BaseModel):
    """Comprehensive data quality scorecard and issue catalog."""

    target_entity: str
    total_records: int
    dimensions: QualityDimensionsScore
    total_issues: int
    issues_by_type: dict[str, int]
    issues: list[QualityIssue]


class CleanStagingRequest(BaseModel):
    """Request payload to execute automated cleaning pipeline on staged records."""

    import_job_id: int
    auto_impute_missing: bool = True
    standardize_categories: bool = True
    standardize_dates: bool = True


class CleanStagingResponse(BaseModel):
    """Response returned upon completing automated cleaning execution."""

    import_job_id: int
    total_records: int
    cleaned_records: int
    invalid_records: int
    total_transformations: int
    dimensions: QualityDimensionsScore
    transformations_sample: list[TransformationAudit]


class ApproveCuratedRequest(BaseModel):
    """Request payload to approve and promote curated staging records into destination tables."""

    import_job_id: int


class ApproveCuratedResponse(BaseModel):
    """Result of staging record promotion to production database."""

    import_job_id: int
    target_entity: str
    curated_rows_promoted: int
    status: str
    message: str


class TableQualityMetric(BaseModel):
    """Individual table quality scorecard."""

    table_name: str
    total_records: int
    completeness: float
    validity: float
    uniqueness: float
    consistency: float
    timeliness: float
    overall_score: float


class SystemQualitySummary(BaseModel):
    """System-wide data quality overview covering core business database entities."""

    total_records: int
    dimensions: QualityDimensionsScore
    tables: list[TableQualityMetric]
    last_evaluated_at: str
