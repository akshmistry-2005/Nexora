"""Anomaly Detection and Risk Intelligence API Router.

Provides endpoints for alert querying, summary KPIs, multi-sigma detection runs,
workflow triage/acknowledgement, and comparative Isolation Forest benchmarking.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.permissions.dependencies import AuthenticatedUser, require_permission
from app.schemas.anomalies import (
    AnomalyAcknowledgeRequest,
    AnomalyAlertRead,
    AnomalyDetectionRunResponse,
    AnomalySummaryStats,
    IsolationForestBenchmarkResponse,
)
from app.schemas.common import StandardResponse
from app.services import anomalies as anomaly_service

router = APIRouter(prefix="/anomalies", tags=["anomaly-risk-intelligence"])


@router.get(
    "/summary",
    response_model=StandardResponse[AnomalySummaryStats],
    summary="Get anomaly KPI summary metrics and severity breakdown",
)
def get_anomaly_summary_endpoint(
    db: Annotated[Session, Depends(get_db)],
    _: AuthenticatedUser = Depends(require_permission("anomaly.view")),
) -> StandardResponse[AnomalySummaryStats]:
    """Retrieve counts of open, critical, high, medium, and acknowledged alerts."""
    summary = anomaly_service.get_summary_stats(db)
    return StandardResponse(data=summary)


@router.get(
    "",
    response_model=StandardResponse[list[AnomalyAlertRead]],
    summary="List detected anomaly alerts with domain, severity, and status filters",
)
def list_anomalies_endpoint(
    db: Annotated[Session, Depends(get_db)],
    _: AuthenticatedUser = Depends(require_permission("anomaly.view")),
    domain: Annotated[str | None, Query(description="Domain filter")] = None,
    severity: Annotated[str | None, Query(description="Severity filter")] = None,
    status_filter: Annotated[str | None, Query(alias="status", description="Status filter")] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> StandardResponse[list[AnomalyAlertRead]]:
    """Retrieve anomaly alerts feed matching optional multi-criteria filters."""
    alerts, _total = anomaly_service.get_anomalies(
        db,
        domain=domain,
        severity=severity,
        status=status_filter,
        limit=limit,
        offset=offset,
    )
    return StandardResponse(data=[AnomalyAlertRead.model_validate(a) for a in alerts])


@router.get(
    "/benchmark/isolation-forest",
    response_model=StandardResponse[IsolationForestBenchmarkResponse],
    summary="Run comparative benchmark between Isolation Forest and statistical baseline",
)
def isolation_forest_benchmark_endpoint(
    db: Annotated[Session, Depends(get_db)],
    _: AuthenticatedUser = Depends(require_permission("anomaly.view")),
    contamination: Annotated[float, Query(ge=0.001, le=0.2)] = 0.03,
) -> StandardResponse[IsolationForestBenchmarkResponse]:
    """Evaluate multivariate Isolation Forest against univariate Z-score baseline (BL-16)."""
    try:
        benchmark = anomaly_service.run_isolation_forest_benchmark(db, contamination=contamination)
        return StandardResponse(data=benchmark)
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(err),
        ) from err


@router.get(
    "/{alert_id}",
    response_model=StandardResponse[AnomalyAlertRead],
    summary="Get single anomaly alert detail",
)
def get_anomaly_detail_endpoint(
    alert_id: int,
    db: Annotated[Session, Depends(get_db)],
    _: AuthenticatedUser = Depends(require_permission("anomaly.view")),
) -> StandardResponse[AnomalyAlertRead]:
    """Retrieve full anomaly context, baseline comparison, and explanation."""
    alert = anomaly_service.get_anomaly_by_id(db, alert_id)
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Anomaly alert #{alert_id} not found.",
        )
    return StandardResponse(data=AnomalyAlertRead.model_validate(alert))


@router.post(
    "/{alert_id}/acknowledge",
    response_model=StandardResponse[AnomalyAlertRead],
    summary="Acknowledge or update anomaly status (Owner only)",
)
def acknowledge_anomaly_endpoint(
    alert_id: int,
    payload: AnomalyAcknowledgeRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: AuthenticatedUser = Depends(require_permission("anomaly.acknowledge")),
) -> StandardResponse[AnomalyAlertRead]:
    """Update anomaly workflow status to acknowledged, resolved, or dismissed."""
    try:
        updated = anomaly_service.acknowledge_anomaly(
            db,
            alert_id=alert_id,
            user_id=current_user.id,
            new_status=payload.status,
            notes=payload.notes,
        )
        return StandardResponse(data=AnomalyAlertRead.model_validate(updated))
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(err),
        ) from err


@router.post(
    "/run-detection",
    response_model=StandardResponse[AnomalyDetectionRunResponse],
    summary="Trigger automated multi-domain anomaly scan (Owner only)",
)
def run_detection_scan_endpoint(
    db: Annotated[Session, Depends(get_db)],
    _: AuthenticatedUser = Depends(require_permission("anomaly.acknowledge")),
    threshold_sigma: Annotated[float, Query(ge=1.5, le=5.0)] = 3.0,
) -> StandardResponse[AnomalyDetectionRunResponse]:
    """Execute automated statistical baseline scans across sales, transactions, and inventory."""
    run_result = anomaly_service.run_automated_detection(db, threshold_sigma=threshold_sigma)
    return StandardResponse(data=run_result)
