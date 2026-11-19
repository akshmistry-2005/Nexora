import math
from collections.abc import Sequence
from typing import Any

import numpy as np
import scipy.stats as stats
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import BadRequestError
from app.models.customer import Customer
from app.models.order import Order
from app.models.product import Product
from app.schemas.statistics import (
    CorrelationMatrixResponse,
    DescriptiveStatsResponse,
    HistogramBin,
    HypothesisTestRequest,
    HypothesisTestResponse,
)


class StatisticsService:
    """Parametric and non-parametric analytical service."""

    CAUSATION_WARNING = (
        "Correlation does not imply causation. High correlation coefficients indicate "
        "co-movement, not causal mechanisms."
    )

    def compute_descriptive(
        self, values: Sequence[float | None], metric_name: str = "series"
    ) -> DescriptiveStatsResponse:
        """
        Compute univariate statistical metrics on a numerical series.
        Filters missing/NaN values and enforces strict mathematical validity (N >= 2).
        """
        # 1. Clean missing & null values (M11-T05)
        clean_vals = [float(v) for v in values if v is not None and not math.isnan(float(v))]
        missing_count = len(values) - len(clean_vals)
        n = len(clean_vals)

        # 2. Validate statistical assumptions (M11-T10)
        if n < 2:
            raise BadRequestError(
                f"Sample size N={n} is insufficient. Descriptive variance and confidence "
                f"intervals require at least 2 valid observations.",
                details=[{"field": "values", "issue": "Minimum sample size is 2"}],
            )

        arr = np.array(clean_vals, dtype=np.float64)

        # 3. Parametric & Central Tendency metrics (M11-T01, M11-T02, M11-T03)
        mean_val = float(np.mean(arr))
        median_val = float(np.median(arr))

        # Mode calculation
        try:
            mode_res = stats.mode(arr, keepdims=False)
            mode_val = float(mode_res.mode)
        except Exception:
            mode_val = float(clean_vals[0])

        var_val = float(np.var(arr, ddof=1))
        std_val = float(np.std(arr, ddof=1))
        min_val = float(np.min(arr))
        max_val = float(np.max(arr))

        # 4. Quartiles & Percentiles (M11-T04)
        q1_val, q2_val, q3_val = np.percentile(arr, [25, 50, 75])
        iqr_val = float(q3_val - q1_val)

        # 5. Distribution Analysis: Skewness & Kurtosis (M11-T06)
        if std_val > 0.0:
            skew_val = float(stats.skew(arr))
            kurt_val = float(stats.kurtosis(arr))
        else:
            skew_val = 0.0
            kurt_val = 0.0

        # 6. Confidence Interval 95% (M11-T11)
        if std_val > 0.0:
            t_crit = float(stats.t.ppf(0.975, df=n - 1))
            margin = t_crit * (std_val / math.sqrt(n))
            ci_95 = [round(mean_val - margin, 4), round(mean_val + margin, 4)]
        else:
            ci_95 = [round(mean_val, 4), round(mean_val, 4)]

        # 7. Histogram bins (M11-T06)
        num_bins = min(10, max(2, n // 2))
        counts, bin_edges = np.histogram(arr, bins=num_bins)
        histogram_bins = [
            HistogramBin(
                bin_start=round(float(bin_edges[i]), 2),
                bin_end=round(float(bin_edges[i + 1]), 2),
                count=int(counts[i]),
            )
            for i in range(len(counts))
        ]

        return DescriptiveStatsResponse(
            metric_name=metric_name,
            n=n,
            missing_count=missing_count,
            mean=round(mean_val, 4),
            median=round(median_val, 4),
            mode=round(mode_val, 4),
            variance=round(var_val, 4),
            std_dev=round(std_val, 4),
            min=round(min_val, 4),
            max=round(max_val, 4),
            q1=round(float(q1_val), 4),
            q2=round(float(q2_val), 4),
            q3=round(float(q3_val), 4),
            iqr=round(iqr_val, 4),
            confidence_interval_95=ci_95,
            skewness=round(skew_val, 4),
            kurtosis=round(kurt_val, 4),
            histogram=histogram_bins,
        )

    def compute_hypothesis_test(self, req: HypothesisTestRequest) -> HypothesisTestResponse:
        """
        Execute two-sample Welch's t-test comparing sample distributions.
        Does not assume equal variances.
        """
        clean_a = [
            float(v) for v in req.group_a_values if v is not None and not math.isnan(float(v))
        ]
        clean_b = [
            float(v) for v in req.group_b_values if v is not None and not math.isnan(float(v))
        ]

        # Validate statistical assumptions (M11-T10)
        if len(clean_a) < 2 or len(clean_b) < 2:
            raise BadRequestError(
                f"Both sample groups must have at least 2 valid observations for Welch's t-test. "
                f"Got N_A={len(clean_a)}, N_B={len(clean_b)}.",
                details=[{"field": "sample_size", "issue": "Group size < 2"}],
            )

        arr_a = np.array(clean_a, dtype=np.float64)
        arr_b = np.array(clean_b, dtype=np.float64)

        mean_a = float(np.mean(arr_a))
        mean_b = float(np.mean(arr_b))
        std_a = float(np.std(arr_a, ddof=1))
        std_b = float(np.std(arr_b, ddof=1))

        if std_a == 0.0 and std_b == 0.0:
            if mean_a == mean_b:
                return HypothesisTestResponse(
                    group_a_name=req.group_a_name,
                    group_b_name=req.group_b_name,
                    group_a_n=len(clean_a),
                    group_b_n=len(clean_b),
                    group_a_mean=round(mean_a, 4),
                    group_b_mean=round(mean_b, 4),
                    group_a_std=0.0,
                    group_b_std=0.0,
                    t_statistic=0.0,
                    p_value=1.0,
                    degrees_of_freedom=float(len(clean_a) + len(clean_b) - 2),
                    alpha=req.alpha,
                    significant=False,
                    effect_size_cohens_d=0.0,
                    interpretation="Both groups exhibit identical constants with zero variance.",
                )
            raise BadRequestError(
                "Both sample groups exhibit zero variance with differing values; "
                "cannot compute t-statistic.",
                details=[{"field": "variance", "issue": "Zero variance in both groups"}],
            )

        # Welch's t-test (M11-T09)
        ttest_res = stats.ttest_ind(arr_a, arr_b, equal_var=False)
        t_stat = float(ttest_res.statistic)
        p_val = float(ttest_res.pvalue)
        df_val = float(ttest_res.df)

        # Cohen's d effect size
        pooled_std = math.sqrt((std_a**2 + std_b**2) / 2.0)
        cohens_d = (mean_a - mean_b) / pooled_std if pooled_std > 0 else 0.0

        is_significant = bool(p_val < req.alpha)
        if is_significant:
            interp = (
                f"Statistically significant difference detected (t = {t_stat:.3f}, "
                f"p = {p_val:.4f} < {req.alpha}). Group '{req.group_a_name}' (M = {mean_a:.2f}) "
                f"differs significantly from Group '{req.group_b_name}' (M = {mean_b:.2f}) "
                f"with Cohen's d = {cohens_d:.3f}."
            )
        else:
            interp = (
                f"No statistically significant difference detected (t = {t_stat:.3f}, "
                f"p = {p_val:.4f} >= {req.alpha}). The observed difference in sample means "
                "could reasonably occur under the null hypothesis."
            )

        return HypothesisTestResponse(
            group_a_name=req.group_a_name,
            group_b_name=req.group_b_name,
            group_a_n=len(clean_a),
            group_b_n=len(clean_b),
            group_a_mean=round(mean_a, 4),
            group_b_mean=round(mean_b, 4),
            group_a_std=round(std_a, 4),
            group_b_std=round(std_b, 4),
            t_statistic=round(t_stat, 4),
            p_value=round(p_val, 6),
            degrees_of_freedom=round(df_val, 2),
            alpha=req.alpha,
            significant=is_significant,
            effect_size_cohens_d=round(cohens_d, 4),
            interpretation=interp,
        )

    def compute_correlation_matrix(
        self, db: Session, entity: str = "orders", limit: int = 1000
    ) -> CorrelationMatrixResponse:
        """
        Calculate Pearson and Spearman correlation matrices across numeric dimensions.
        Includes sample size and mandatory causation warning (M11-T07, M11-T08).
        """
        q: Any
        if entity == "products":
            q = (
                select(
                    Product.unit_price,
                    Product.unit_cost,
                    Product.reorder_point,
                    Product.target_stock,
                )
                .order_by(Product.id)
                .limit(limit)
            )
            variables = ["Unit Price", "Unit Cost", "Reorder Point", "Target Stock"]
        else:
            # Default to orders entity
            q = (
                select(
                    Order.subtotal_amount,
                    Order.discount_amount,
                    Order.shipping_amount,
                    Order.tax_amount,
                    Order.total_amount,
                )
                .where(Order.status != "cancelled")
                .order_by(Order.order_date.desc())
                .limit(limit)
            )
            variables = [
                "Subtotal",
                "Discount Amount",
                "Shipping Amount",
                "Tax Amount",
                "Net Revenue",
            ]

        rows = db.execute(q).fetchall()
        if len(rows) < 3:
            raise BadRequestError("Insufficient database observations for correlation matrix.")

        data_matrix = np.array([[float(col) for col in row] for row in rows], dtype=np.float64)
        num_vars = len(variables)

        pearson_mat = np.zeros((num_vars, num_vars))
        spearman_mat = np.zeros((num_vars, num_vars))
        p_val_mat = np.zeros((num_vars, num_vars))

        for i in range(num_vars):
            for j in range(num_vars):
                if i == j:
                    pearson_mat[i, j] = 1.0
                    spearman_mat[i, j] = 1.0
                    p_val_mat[i, j] = 0.0
                else:
                    col_i = data_matrix[:, i]
                    col_j = data_matrix[:, j]
                    if np.std(col_i) == 0.0 or np.std(col_j) == 0.0:
                        pearson_mat[i, j] = 0.0
                        spearman_mat[i, j] = 0.0
                        p_val_mat[i, j] = 1.0
                    else:
                        p_r, p_p = stats.pearsonr(col_i, col_j)
                        s_r, _ = stats.spearmanr(col_i, col_j)
                        pearson_mat[i, j] = (
                            round(float(p_r), 4) if not math.isnan(float(p_r)) else 0.0
                        )
                        spearman_mat[i, j] = (
                            round(float(s_r), 4) if not math.isnan(float(s_r)) else 0.0
                        )
                        p_val_mat[i, j] = (
                            round(float(p_p), 6) if not math.isnan(float(p_p)) else 1.0
                        )

        return CorrelationMatrixResponse(
            variables=variables,
            pearson_matrix=pearson_mat.tolist(),
            spearman_matrix=spearman_mat.tolist(),
            p_values=p_val_mat.tolist(),
            sample_size=len(rows),
        )

    def get_entity_stats(
        self, db: Session, entity: str = "orders", field: str = "total_amount", limit: int = 5000
    ) -> DescriptiveStatsResponse:
        """Fetch real records from PostgreSQL and compute complete descriptive metrics."""
        q: Any
        if entity == "products":
            col = Product.unit_price if field == "unit_price" else Product.unit_cost
            q = select(col).limit(limit)
        elif entity == "customers":
            q = select(Customer.organization_id).limit(limit)
        else:
            if field == "discount_amount":
                col = Order.discount_amount
            elif field == "subtotal_amount":
                col = Order.subtotal_amount
            else:
                col = Order.total_amount
            q = select(col).where(Order.status != "cancelled").limit(limit)

        records: list[Any] = list(db.execute(q).scalars().all())
        values = [float(v) for v in records if v is not None]
        return self.compute_descriptive(values, metric_name=f"{entity}.{field}")

    def get_channel_comparison_test(self, db: Session) -> HypothesisTestResponse:
        """Compare Order values between 'Direct' and 'Online' channels with Welch's t-test."""
        direct_q = (
            select(Order.total_amount)
            .where(Order.sales_channel == "Direct", Order.status != "cancelled")
            .limit(1000)
        )
        online_q = (
            select(Order.total_amount)
            .where(Order.sales_channel == "Online", Order.status != "cancelled")
            .limit(1000)
        )

        direct_vals: Sequence[float | None] = [
            float(v) for v in db.execute(direct_q).scalars().all() if v is not None
        ]
        online_vals: Sequence[float | None] = [
            float(v) for v in db.execute(online_q).scalars().all() if v is not None
        ]

        req = HypothesisTestRequest(
            group_a_name="Direct Sales Channel",
            group_b_name="Online Sales Channel",
            group_a_values=direct_vals,
            group_b_values=online_vals,
            alpha=0.05,
        )
        return self.compute_hypothesis_test(req)


statistics_service = StatisticsService()
