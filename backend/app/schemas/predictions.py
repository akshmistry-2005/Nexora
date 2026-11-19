"""Pydantic schemas for predictive analytics, model governance, and ML inference."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ModelMetadataItem(BaseModel):
    """Metadata, provenance, and performance comparison of a trained ML model."""

    model_config = ConfigDict(from_attributes=True)

    model_id: str = Field(..., description="Unique machine learning model identifier")
    model_name: str = Field(..., description="Human-readable model name")
    problem_type: str = Field(..., description="ML formulation (classification or regression)")
    target_variable: str = Field(..., description="Predictive target column")
    features: list[str] = Field(..., description="Ordered list of input feature names")
    baseline_algorithm: str = Field(..., description="Naive baseline model algorithm")
    candidate_algorithm: str = Field(..., description="Advanced candidate model algorithm")
    hyperparameters: dict[str, Any] = Field(
        default_factory=dict, description="Candidate hyperparameter settings"
    )
    sample_size_train: int = Field(..., description="Number of training observations")
    sample_size_test: int = Field(..., description="Number of holdout test observations")
    split_strategy: str = Field(..., description="Data split method (e.g. chronological temporal)")
    baseline_metrics: dict[str, float] = Field(
        ..., description="Evaluation metrics of the baseline model"
    )
    candidate_metrics: dict[str, float] = Field(
        ..., description="Evaluation metrics of the candidate model"
    )
    overfitting_gap: float | None = Field(
        None, description="Difference between train and test performance"
    )
    feature_importances: dict[str, float] = Field(
        default_factory=dict, description="Feature importance scores"
    )
    trained_at: str = Field(..., description="ISO 8601 timestamp of model training run")
    artifact_path: str = Field(..., description="Path to persisted model artifact (.joblib)")
    is_loaded: bool = Field(True, description="Whether artifact is loaded in memory")
    governance_notice: str = Field(
        default=(
            "Model predictions are statistical approximations based on historical data. "
            "Decisions should incorporate domain expertise."
        ),
        description="Mandatory model governance disclaimer",
    )


class ChurnInferenceInput(BaseModel):
    """Input features for single customer churn classification."""

    tenure_days: int = Field(..., ge=0, le=7300, description="Customer relationship age in days")
    order_count: int = Field(..., ge=0, le=10000, description="Lifetime count of completed orders")
    total_spend: float = Field(..., ge=0.0, description="Lifetime gross spend in base currency")
    avg_order_value: float = Field(..., ge=0.0, description="Average monetary value per order")
    days_since_last_order: int | None = Field(
        default=None, ge=0, le=7300, description="Optional days elapsed since last order"
    )
    returns_count: int = Field(
        default=0, ge=0, le=1000, description="Count of returned orders or items"
    )
    customer_type: str = Field(default="B2B", description="Customer tier: B2B, B2C, or Enterprise")
    acquisition_channel: str = Field(default="Direct", description="Initial acquisition channel")


class ChurnInferenceOutput(BaseModel):
    """Inference output for customer churn prediction."""

    churn_probability: float = Field(
        ..., ge=0.0, le=1.0, description="Predicted probability of churn"
    )
    is_churn_predicted: bool = Field(..., description="Binary classification at threshold 0.5")
    risk_tier: str = Field(..., description="Categorized risk: Low, Medium, or High")
    contributing_factors: list[dict[str, Any]] = Field(
        default_factory=list, description="Top positive and negative risk factors"
    )
    model_id: str = Field(default="customer_churn", description="Model used for inference")
    governance_notice: str = Field(
        default="Customer churn prediction is a probabilistic risk indicator, not a certainty.",
        description="Limitations disclaimer",
    )


class BatchChurnInferenceInput(BaseModel):
    """Batch input records for customer churn inference."""

    records: list[ChurnInferenceInput] = Field(
        ..., min_length=1, max_length=500, description="List of customer feature vectors"
    )


class BatchChurnInferenceOutput(BaseModel):
    """Batch inference output records."""

    total_records: int = Field(..., description="Count of scored customer records")
    results: list[ChurnInferenceOutput] = Field(..., description="Scored predictions")


class HighRiskCustomerItem(BaseModel):
    """High risk churn customer for operational CRM intervention."""

    customer_id: int
    company_name: str | None
    contact_name: str
    email: str
    customer_type: str
    lifetime_spend: float
    order_count: int
    days_since_last_order: int
    churn_probability: float
    risk_tier: str


class SalesForecastPoint(BaseModel):
    """Single daily time-series forecast projection."""

    date: str = Field(..., description="Projected calendar date (YYYY-MM-DD)")
    forecasted_revenue: float = Field(..., description="Point revenue prediction")
    lower_bound_95: float = Field(..., description="Lower bound of 95% confidence interval")
    upper_bound_95: float = Field(..., description="Upper bound of 95% confidence interval")


class SalesForecastResponse(BaseModel):
    """Multi-step time series demand and sales forecast."""

    horizon_days: int = Field(..., description="Forecast horizon in days (e.g. 30, 60, 90)")
    model_id: str = Field(default="sales_forecast", description="Forecast model identifier")
    total_forecasted_revenue: float = Field(
        ..., description="Sum of projected revenue across horizon"
    )
    evaluation_metrics: dict[str, float] = Field(
        ..., description="Candidate holdout test metrics (MAE, RMSE, R2, MAPE)"
    )
    baseline_metrics: dict[str, float] = Field(
        ..., description="Baseline naive holdout test metrics (MAE, RMSE)"
    )
    forecast_series: list[SalesForecastPoint] = Field(
        ..., description="Daily projected sequence with confidence intervals"
    )
    historical_series: list[dict[str, Any]] = Field(
        ..., description="Recent historical daily revenue for baseline context"
    )
    governance_notice: str = Field(
        default=(
            "Projections assume normal macroeconomic conditions and stable distribution channels."
        ),
        description="Assumptions disclaimer",
    )


class ProductDemandItem(BaseModel):
    """Projected SKU inventory demand and reorder alert."""

    product_id: int
    sku: str
    name: str
    category_name: str
    unit_price: float
    current_stock: int
    target_stock: int
    forecasted_monthly_demand: int
    reorder_recommended: bool


class ProductDemandResponse(BaseModel):
    """Demand forecasting response for catalog products."""

    total_products: int
    reorder_count: int
    products: list[ProductDemandItem]
    evaluation_metrics: dict[str, float]
    governance_notice: str
