from collections.abc import Sequence

from pydantic import BaseModel, Field


class HistogramBin(BaseModel):
    """Histogram bucket intervals and sample counts."""

    bin_start: float
    bin_end: float
    count: int


class DescriptiveStatsResponse(BaseModel):
    """Univariate parametric and non-parametric summary metrics."""

    metric_name: str
    n: int
    missing_count: int
    mean: float
    median: float
    mode: float
    variance: float
    std_dev: float
    min: float
    max: float
    q1: float
    q2: float
    q3: float
    iqr: float
    confidence_interval_95: list[float] = Field(
        ..., min_length=2, max_length=2, description="[lower_bound, upper_bound]"
    )
    skewness: float
    kurtosis: float
    histogram: list[HistogramBin]
    causation_warning: str = (
        "Correlation does not imply causation. Statistical metrics summarize sample "
        "distributions and do not prove underlying causal drivers."
    )


class ComputeStatsRequest(BaseModel):
    """Payload to calculate statistical summaries on a user-submitted vector."""

    values: list[float | None]
    metric_name: str = "custom_series"


class CorrelationMatrixResponse(BaseModel):
    """Bivariate Pearson and Spearman correlation matrices across dimensions."""

    variables: list[str]
    pearson_matrix: list[list[float]]
    spearman_matrix: list[list[float]]
    p_values: list[list[float]]
    sample_size: int
    causation_warning: str = (
        "Correlation does not imply causation. High correlation coefficients indicate "
        "co-movement, not causal mechanisms."
    )


class HypothesisTestRequest(BaseModel):
    """Two-sample Welch's t-test input payload."""

    group_a_name: str = Field(default="Group A", max_length=50)
    group_b_name: str = Field(default="Group B", max_length=50)
    group_a_values: Sequence[float | None]
    group_b_values: Sequence[float | None]
    alpha: float = Field(default=0.05, ge=0.001, le=0.20)


class HypothesisTestResponse(BaseModel):
    """Two-sample Welch's t-test inferential results."""

    test_name: str = "Welch's Two-Sample t-Test (Unequal Variances)"
    group_a_name: str
    group_b_name: str
    group_a_n: int
    group_b_n: int
    group_a_mean: float
    group_b_mean: float
    group_a_std: float
    group_b_std: float
    t_statistic: float
    p_value: float
    degrees_of_freedom: float
    alpha: float
    significant: bool
    effect_size_cohens_d: float
    interpretation: str
    causation_warning: str = (
        "Statistical significance (p < 0.05) rejects the null hypothesis of equal "
        "population means, but does not establish causal attribution."
    )
