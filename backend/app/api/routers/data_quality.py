from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.permissions.dependencies import (
    AuthenticatedUser,
    require_permission,
)
from app.schemas.common import StandardResponse
from app.schemas.data_quality import (
    ApproveCuratedResponse,
    CleanStagingRequest,
    CleanStagingResponse,
    QualityEvaluationReport,
    SystemQualitySummary,
)
from app.services.data_quality import quality_service

router = APIRouter(prefix="/data-quality", tags=["Data Quality & Validation"])


@router.get(
    "/summary",
    response_model=StandardResponse[SystemQualitySummary],
    summary="Get system-wide data quality score and table breakdown",
    description="Compute 5-dimensional quality metrics across core production database entities.",
)
def get_system_quality_summary(
    session: Session = Depends(get_db),
    _: AuthenticatedUser = Depends(require_permission("dataquality.view")),
) -> StandardResponse[SystemQualitySummary]:
    summary = quality_service.get_system_quality_summary(session)
    return StandardResponse(data=summary)


@router.get(
    "/evaluations/{import_job_id}",
    response_model=StandardResponse[QualityEvaluationReport],
    summary="Evaluate data quality of staged records for an import job",
    description=(
        "Inspect staged raw rows, score 5 dimensions, and catalogue row-level validation anomalies."
    ),
)
def evaluate_staging_job(
    import_job_id: int,
    session: Session = Depends(get_db),
    _: AuthenticatedUser = Depends(require_permission("dataquality.view")),
) -> StandardResponse[QualityEvaluationReport]:
    report = quality_service.evaluate_staging_job(import_job_id=import_job_id, db=session)
    return StandardResponse(data=report)


@router.post(
    "/clean/{import_job_id}",
    response_model=StandardResponse[CleanStagingResponse],
    summary="Execute automated cleaning pipeline on staged records (Owner/Engineer)",
    description=(
        "Normalize categories, trim whitespace, standardize dates, clean numbers, "
        "and track lineage."
    ),
)
def clean_staging_job(
    import_job_id: int,
    request: CleanStagingRequest | None = None,
    session: Session = Depends(get_db),
    _: AuthenticatedUser = Depends(require_permission("dataquality.manage")),
) -> StandardResponse[CleanStagingResponse]:
    auto_impute = request.auto_impute_missing if request else True
    std_cats = request.standardize_categories if request else True
    std_dates = request.standardize_dates if request else True

    cleaned_response = quality_service.clean_staging_job(
        import_job_id=import_job_id,
        auto_impute_missing=auto_impute,
        standardize_categories=std_cats,
        standardize_dates=std_dates,
        db=session,
    )
    return StandardResponse(data=cleaned_response)


@router.post(
    "/approve/{import_job_id}",
    response_model=StandardResponse[ApproveCuratedResponse],
    status_code=status.HTTP_200_OK,
    summary="Approve and promote curated staging records into destination tables (Owner-only)",
    description="Atomically promote validated clean records into live PostgreSQL entities.",
)
def approve_curated_records(
    import_job_id: int,
    session: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(require_permission("dataquality.manage")),
) -> StandardResponse[ApproveCuratedResponse]:
    res = quality_service.approve_and_promote(
        import_job_id=import_job_id,
        user_id=current_user.id,
        user_role=current_user.role,
        db=session,
    )
    return StandardResponse(data=res)
