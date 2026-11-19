"""Pydantic schemas for anomaly detection, risk intelligence, and alert triage."""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class AnomalyAlertRead(BaseModel):
    """Structured representation of a detected business anomaly."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    organization_id: int
    domain: str = Field(
        ..., description="Business domain: sales, transaction, inventory, marketing, operations"
    )
    entity_identifier: str = Field(..., description="Affected entity ID, SKU, or descriptor")
    metric_name: str = Field(..., description="Anomaly metric analyzed")
    observed_value: Decimal = Field(..., description="Observed anomalous metric value")
    baseline_value: Decimal = Field(
        ..., description="Expected baseline moving average or benchmark"
    )
    deviation_amount: Decimal = Field(..., description="Observed minus baseline difference")
    z_score: Decimal | None = Field(None, description="Standard deviations away from baseline mean")
    severity: str = Field(..., description="Severity level: low, medium, high, critical")
    explanation: str = Field(..., description="Plain-language statistical context and explanation")
    status: str = Field(
        default="open",
        description="Alert workflow status: open, acknowledged, resolved, dismissed",
    )
    detected_at: datetime
    acknowledged_at: datetime | None = None
    acknowledged_by_id: int | None = None


class AnomalySummaryStats(BaseModel):
    """Aggregate KPI statistics for the Anomaly & Risk Intelligence workbench."""

    total_alerts: int
    open_alerts: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    acknowledged_count: int
    by_domain: dict[str, int]


class AnomalyAcknowledgeRequest(BaseModel):
    """Request payload to update anomaly status."""

    status: str = Field(
        default="acknowledged",
        description="Target status: acknowledged, resolved, or dismissed",
    )
    notes: str | None = Field(
        default=None,
        description="Optional triage notes from investigating reviewer",
    )


class AnomalyDetectionRunResponse(BaseModel):
    """Summary of executed automated detection scan across platform domains."""

    new_anomalies_detected: int
    total_scanned_records: int
    domains_scanned: list[str]
    detector_algorithm: str = Field(
        default="Multi-Sigma Rolling Baseline (Z-Score + IQR)",
        description="Detection method used",
    )
    run_duration_ms: float


class IsolationForestBenchmarkResponse(BaseModel):
    """Comparative evaluation benchmark between Isolation Forest and statistical baseline."""

    algorithm: str = "IsolationForest (scikit-learn)"
    contamination_rate: float
    total_observations_evaluated: int
    statistical_baseline_detected: int
    isolation_forest_detected: int
    overlap_count: int
    concordance_rate: float = Field(..., description="Percentage agreement between models")
    benchmark_evaluation: str
