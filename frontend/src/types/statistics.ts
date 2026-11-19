export interface HistogramBin {
  bin_start: number;
  bin_end: number;
  count: number;
}

export interface DescriptiveStats {
  metric_name: string;
  n: number;
  missing_count: number;
  mean: number;
  median: number;
  mode: number;
  variance: number;
  std_dev: number;
  min: number;
  max: number;
  q1: number;
  q2: number;
  q3: number;
  iqr: number;
  confidence_interval_95: [number, number];
  skewness: number;
  kurtosis: number;
  histogram: HistogramBin[];
  causation_warning: string;
}

export interface CorrelationMatrix {
  variables: string[];
  pearson_matrix: number[][];
  spearman_matrix: number[][];
  p_values: number[][];
  sample_size: number;
  causation_warning: string;
}

export interface HypothesisTest {
  test_name: string;
  group_a_name: string;
  group_b_name: string;
  group_a_n: number;
  group_b_n: number;
  group_a_mean: number;
  group_b_mean: number;
  group_a_std: number;
  group_b_std: number;
  t_statistic: number;
  p_value: number;
  degrees_of_freedom: number;
  alpha: number;
  significant: boolean;
  effect_size_cohens_d: number;
  interpretation: string;
  causation_warning: string;
}

export interface ComputeStatsPayload {
  values: (number | null)[];
  metric_name?: string;
}

export interface HypothesisTestPayload {
  group_a_name: string;
  group_b_name: string;
  group_a_values: (number | null)[];
  group_b_values: (number | null)[];
  alpha?: number;
}
