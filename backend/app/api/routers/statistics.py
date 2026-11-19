from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.permissions.dependencies import AuthenticatedUser, require_permission
from app.schemas.common import StandardResponse
from app.schemas.statistics import (
    ComputeStatsRequest,
    CorrelationMatrixResponse,
    DescriptiveStatsResponse,
    HypothesisTestRequest,
    HypothesisTestResponse,
)
from app.services.statistics import statistics_service

router = APIRouter(prefix="/statistics", tags=["Statistical Analysis & Modeling"])


@router.get(
    "/descriptive",
    response_model=StandardResponse[DescriptiveStatsResponse],
    summary="Get univariate descriptive statistics on database entities",
)
def get_descriptive_statistics(
    entity: str = Query(default="orders", description="Entity name"),
    field: str = Query(default="total_amount", description="Numeric field name"),
    limit: int = Query(default=5000, ge=10, le=50000),
    session: Session = Depends(get_db),
    _: AuthenticatedUser = Depends(require_permission("statistics.view")),
) -> StandardResponse[DescriptiveStatsResponse]:
    data = statistics_service.get_entity_stats(session, entity, field, limit)
    return StandardResponse(data=data)


@router.post(
    "/compute",
    response_model=StandardResponse[DescriptiveStatsResponse],
    summary="Calculate descriptive statistical metrics on user-submitted vector",
)
def compute_statistics_vector(
    payload: ComputeStatsRequest,
    _: AuthenticatedUser = Depends(require_permission("statistics.view")),
) -> StandardResponse[DescriptiveStatsResponse]:
    data = statistics_service.compute_descriptive(payload.values, payload.metric_name)
    return StandardResponse(data=data)


@router.get(
    "/correlation",
    response_model=StandardResponse[CorrelationMatrixResponse],
    summary="Compute Pearson and Spearman correlation matrices across dimensions",
)
def get_correlation_matrix(
    entity: str = Query(default="orders", description="Entity name ('orders', 'products')"),
    session: Session = Depends(get_db),
    _: AuthenticatedUser = Depends(require_permission("statistics.view")),
) -> StandardResponse[CorrelationMatrixResponse]:
    data = statistics_service.compute_correlation_matrix(session, entity)
    return StandardResponse(data=data)


@router.post(
    "/hypothesis-test",
    response_model=StandardResponse[HypothesisTestResponse],
    summary="Execute two-sample Welch's t-test comparing sample distributions",
)
def execute_hypothesis_test(
    payload: HypothesisTestRequest,
    _: AuthenticatedUser = Depends(require_permission("statistics.view")),
) -> StandardResponse[HypothesisTestResponse]:
    data = statistics_service.compute_hypothesis_test(payload)
    return StandardResponse(data=data)


@router.get(
    "/channel-comparison",
    response_model=StandardResponse[HypothesisTestResponse],
    summary="Execute live Welch's t-test comparing sales channels from database",
)
def get_channel_comparison(
    session: Session = Depends(get_db),
    _: AuthenticatedUser = Depends(require_permission("statistics.view")),
) -> StandardResponse[HypothesisTestResponse]:
    data = statistics_service.get_channel_comparison_test(session)
    return StandardResponse(data=data)
