"""Predictive Analytics API Router.

Provides endpoints for customer churn classification, sales time-series forecasting,
SKU demand projections, and model governance metadata.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.permissions.dependencies import AuthenticatedUser, require_permission
from app.schemas.common import StandardResponse
from app.schemas.predictions import (
    BatchChurnInferenceInput,
    BatchChurnInferenceOutput,
    ChurnInferenceInput,
    ChurnInferenceOutput,
    HighRiskCustomerItem,
    ModelMetadataItem,
    ProductDemandResponse,
    SalesForecastResponse,
)
from app.services import predictions as pred_service

router = APIRouter(prefix="/predictions", tags=["predictive-analytics"])


@router.get(
    "/models",
    response_model=StandardResponse[list[ModelMetadataItem]],
    summary="List all registered ML models and evaluation benchmarks",
)
def list_models_endpoint(
    db: Annotated[Session, Depends(get_db)],
    _: AuthenticatedUser = Depends(require_permission("predictions.view")),
) -> StandardResponse[list[ModelMetadataItem]]:
    """Retrieve metadata, baseline vs candidate metrics, and governance notices for all models."""
    models = pred_service.list_models(db=db)
    return StandardResponse(data=models)


@router.get(
    "/models/{model_id}",
    response_model=StandardResponse[ModelMetadataItem],
    summary="Get detailed metadata for a specific ML model",
)
def get_model_metadata_endpoint(
    model_id: str,
    db: Annotated[Session, Depends(get_db)],
    _: AuthenticatedUser = Depends(require_permission("predictions.view")),
) -> StandardResponse[ModelMetadataItem]:
    """Retrieve hyperparameters, feature importances, and validation metrics for a model."""
    try:
        metadata = pred_service.get_model_metadata(model_id, db=db)
        return StandardResponse(data=metadata)
    except FileNotFoundError as err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model metadata not found: {err}",
        ) from err


@router.post(
    "/models/{model_id}/reload",
    response_model=StandardResponse[ModelMetadataItem],
    summary="Retrain and reload model artifact (Owner only)",
)
def reload_model_endpoint(
    model_id: str,
    db: Annotated[Session, Depends(get_db)],
    _: AuthenticatedUser = Depends(require_permission("predictions.manage")),
) -> StandardResponse[ModelMetadataItem]:
    """Execute end-to-end retraining, artifact persistence, and cache invalidation."""
    try:
        updated = pred_service.reload_model(model_id, db=db)
        return StandardResponse(data=updated)
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(err),
        ) from err


@router.post(
    "/churn/predict",
    response_model=StandardResponse[ChurnInferenceOutput],
    summary="Predict churn probability for a customer feature vector",
)
def predict_churn_endpoint(
    payload: ChurnInferenceInput,
    db: Annotated[Session, Depends(get_db)],
    _: AuthenticatedUser = Depends(require_permission("predictions.view")),
) -> StandardResponse[ChurnInferenceOutput]:
    """Perform customer churn classification with risk tiering and contributing factors."""
    try:
        result = pred_service.predict_churn(payload, db=db)
        return StandardResponse(data=result)
    except FileNotFoundError as err:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Churn model artifact not ready: {err}",
        ) from err


@router.post(
    "/churn/batch",
    response_model=StandardResponse[BatchChurnInferenceOutput],
    summary="Batch score churn risk across multiple customer feature vectors",
)
def batch_predict_churn_endpoint(
    payload: BatchChurnInferenceInput,
    db: Annotated[Session, Depends(get_db)],
    _: AuthenticatedUser = Depends(require_permission("predictions.view")),
) -> StandardResponse[BatchChurnInferenceOutput]:
    """Score a batch of customer feature records with identical logic to single inference."""
    try:
        result = pred_service.batch_predict_churn(payload.records, db=db)
        return StandardResponse(data=result)
    except FileNotFoundError as err:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Churn model artifact not ready: {err}",
        ) from err


@router.get(
    "/churn/high-risk",
    response_model=StandardResponse[list[HighRiskCustomerItem]],
    summary="List top customers at high churn risk from database",
)
def get_high_risk_customers_endpoint(
    db: Annotated[Session, Depends(get_db)],
    limit: Annotated[int, Query(ge=1, le=200)] = 25,
    _: AuthenticatedUser = Depends(require_permission("predictions.view")),
) -> StandardResponse[list[HighRiskCustomerItem]]:
    """Retrieve live database customers evaluated by the churn prediction model."""
    try:
        customers = pred_service.get_high_risk_customers(db, limit=limit)
        return StandardResponse(data=customers)
    except FileNotFoundError as err:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Churn model artifact not ready: {err}",
        ) from err


@router.get(
    "/sales/forecast",
    response_model=StandardResponse[SalesForecastResponse],
    summary="Generate sales revenue time-series forecast",
)
def forecast_sales_endpoint(
    db: Annotated[Session, Depends(get_db)],
    horizon_days: Annotated[int, Query(ge=1, le=365)] = 30,
    _: AuthenticatedUser = Depends(require_permission("predictions.view")),
) -> StandardResponse[SalesForecastResponse]:
    """Forecast future sales revenue with 95% confidence intervals and evaluation metrics."""
    try:
        forecast = pred_service.forecast_sales(horizon_days=horizon_days, db=db)
        return StandardResponse(data=forecast)
    except FileNotFoundError as err:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Forecast model artifact not ready: {err}",
        ) from err


@router.get(
    "/demand/forecast",
    response_model=StandardResponse[ProductDemandResponse],
    summary="Forecast SKU product demand and stock replenishment",
)
def forecast_demand_endpoint(
    db: Annotated[Session, Depends(get_db)],
    category_id: Annotated[int | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 15,
    _: AuthenticatedUser = Depends(require_permission("predictions.view")),
) -> StandardResponse[ProductDemandResponse]:
    """Estimate monthly SKU demand and flag replenishment needs."""
    try:
        demand = pred_service.forecast_product_demand(db, category_id=category_id, limit=limit)
        return StandardResponse(data=demand)
    except FileNotFoundError as err:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Product demand model artifact not ready: {err}",
        ) from err
