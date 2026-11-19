import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { AuthProvider } from '../context/AuthProvider';
import { StatisticsPage } from '../features/statistics/StatisticsPage';

const jsonResponse = (data: unknown) => ({
  ok: true,
  status: 200,
  headers: new Headers({ 'content-type': 'application/json' }),
  json: async () => data,
}) as unknown as Response;

const mockAnalystUser = {
  access_token: 'fake-jwt-token',
  token_type: 'Bearer',
  expires_in_seconds: 7200,
  user_id: 3,
  email: 'demo_analyst@nexora.local',
  full_name: 'Marcus Chen (Data Analyst)',
  role: 'data_analyst',
  permissions: ['dashboard.view', 'report.view', 'statistics.view'],
};

const mockDescriptiveStats = {
  success: true,
  data: {
    entity: 'orders',
    field: 'total_amount',
    n: 1000,
    missing_count: 0,
    mean: 2540.5,
    median: 2100.0,
    mode: 1500.0,
    variance: 1250000.0,
    std_dev: 1118.03,
    min: 150.0,
    max: 9800.0,
    q1: 1400.0,
    q2: 2100.0,
    q3: 3400.0,
    iqr: 2000.0,
    skewness: 1.25,
    kurtosis: 1.8,
    confidence_interval_95: [2471.15, 2609.85],
    histogram: [
      { bin_start: 150.0, bin_end: 1115.0, count: 250 },
      { bin_start: 1115.0, bin_end: 2080.0, count: 320 },
      { bin_start: 2080.0, bin_end: 3045.0, count: 180 },
      { bin_start: 3045.0, bin_end: 4010.0, count: 110 },
      { bin_start: 4010.0, bin_end: 4975.0, count: 60 },
      { bin_start: 4975.0, bin_end: 5940.0, count: 35 },
      { bin_start: 5940.0, bin_end: 6905.0, count: 20 },
      { bin_start: 6905.0, bin_end: 7870.0, count: 12 },
      { bin_start: 7870.0, bin_end: 8835.0, count: 8 },
      { bin_start: 8835.0, bin_end: 9800.0, count: 5 },
    ],
    disclaimer:
      'Correlation does not imply causation. High correlation coefficients indicate co-movement, not causal mechanisms. Inferential hypotheses enforce sample bounds (N >= 2).',
  },
};

const mockCorrelationData = {
  success: true,
  data: {
    variables: ['total_amount', 'subtotal_amount', 'tax_amount'],
    sample_size: 1000,
    pearson_matrix: [
      [1.0, 0.98, 0.65],
      [0.98, 1.0, 0.63],
      [0.65, 0.63, 1.0],
    ],
    spearman_matrix: [
      [1.0, 0.97, 0.62],
      [0.97, 1.0, 0.6],
      [0.62, 0.6, 1.0],
    ],
    p_values: [
      [0.0, 0.00001, 0.0001],
      [0.00001, 0.0, 0.0001],
      [0.0001, 0.0001, 0.0],
    ],
    disclaimer:
      'Correlation does not imply causation. High correlation coefficients indicate co-movement, not causal mechanisms. Inferential hypotheses enforce sample bounds (N >= 2).',
  },
};

const mockHypothesisData = {
  success: true,
  data: {
    test_name: "Welch's Two-Sample t-Test (Unequal Variances)",
    group_a_name: 'Direct Channel Orders',
    group_b_name: 'Online Channel Orders',
    group_a_n: 3719,
    group_b_n: 3752,
    group_a_mean: 2480.25,
    group_b_mean: 2610.8,
    group_a_std: 1150.4,
    group_b_std: 1210.6,
    t_statistic: -4.772,
    p_value: 0.00000185,
    degrees_of_freedom: 7458.2,
    significant: true,
    alpha: 0.05,
    effect_size_cohens_d: -0.1105,
    interpretation:
      'Reject the null hypothesis (p = 1.8500e-06 < 0.05). There is a statistically significant difference between Direct Channel Orders and Online Channel Orders.',
    disclaimer:
      'Correlation does not imply causation. High correlation coefficients indicate co-movement, not causal mechanisms. Inferential hypotheses enforce sample bounds (N >= 2).',
  },
};

describe('Module 11 — Statistical Analysis Frontend', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    localStorage.clear();
  });

  it('renders statistics page header, mandatory causation disclaimer, and top KPI cards', async () => {
    vi.spyOn(globalThis, 'fetch').mockImplementation(async (input) => {
      const url = String(input);
      if (url.includes('/api/v1/auth/')) {
        return jsonResponse({ success: true, data: mockAnalystUser });
      }
      if (url.includes('/api/v1/statistics/descriptive')) {
        return jsonResponse(mockDescriptiveStats);
      }
      return jsonResponse({ success: true, data: null });
    });

    render(
      <MemoryRouter>
        <AuthProvider>
          <StatisticsPage />
        </AuthProvider>
      </MemoryRouter>,
    );

    // Title and mandatory causation disclaimer
    expect(
      screen.getByText('Statistical Analysis & Distribution Modeling'),
    ).toBeInTheDocument();
    expect(screen.getByText('Statistical Assumption Notice')).toBeInTheDocument();
    expect(
      screen.getByText(/Correlation does not imply causation/i),
    ).toBeInTheDocument();

    // Check KPI cards
    await waitFor(() => {
      expect(screen.getByText('Sample Mean (x̄)')).toBeInTheDocument();
      expect(screen.getByText('Median (Q2 / 50th %ile)')).toBeInTheDocument();
      expect(screen.getByText('Distribution Skewness')).toBeInTheDocument();
      expect(screen.getByText('95% Confidence Interval')).toBeInTheDocument();
      expect(screen.getByText('[2471.15, 2609.85]')).toBeInTheDocument();
    });

    // Scorecard & Histogram
    expect(
      screen.getByText('Parametric, Non-Parametric & Dispersion Scorecard'),
    ).toBeInTheDocument();
    expect(
      screen.getByText('Sample Frequency Histogram (10-Bin Stratification)'),
    ).toBeInTheDocument();
  });

  it('switches to correlation matrix tab and toggles between Pearson and Spearman matrices', async () => {
    vi.spyOn(globalThis, 'fetch').mockImplementation(async (input) => {
      const url = String(input);
      if (url.includes('/api/v1/auth/')) {
        return jsonResponse({ success: true, data: mockAnalystUser });
      }
      if (url.includes('/api/v1/statistics/descriptive')) {
        return jsonResponse(mockDescriptiveStats);
      }
      if (url.includes('/api/v1/statistics/correlation')) {
        return jsonResponse(mockCorrelationData);
      }
      return jsonResponse({ success: true, data: null });
    });

    render(
      <MemoryRouter>
        <AuthProvider>
          <StatisticsPage />
        </AuthProvider>
      </MemoryRouter>,
    );

    const correlationTab = screen.getByText('Bivariate Correlation Matrices');
    fireEvent.click(correlationTab);

    await waitFor(() => {
      expect(
        screen.getByText(/Sample Size: N = 1000 order records/i),
      ).toBeInTheDocument();
      // Should show Pearson matrix button
      expect(screen.getByText('Pearson (r) Linear')).toBeInTheDocument();
      expect(screen.getByText('Spearman (ρ) Monotonic Rank')).toBeInTheDocument();
    });

    // Toggle to Spearman
    fireEvent.click(screen.getByText('Spearman (ρ) Monotonic Rank'));
    // Pearson and Spearman headers and variables
    expect(screen.getAllByText('tax_amount').length).toBeGreaterThanOrEqual(2);
  });

  it('switches to hypothesis testing tab and displays Welch t-test results and interpretation', async () => {
    vi.spyOn(globalThis, 'fetch').mockImplementation(async (input) => {
      const url = String(input);
      if (url.includes('/api/v1/auth/')) {
        return jsonResponse({ success: true, data: mockAnalystUser });
      }
      if (url.includes('/api/v1/statistics/descriptive')) {
        return jsonResponse(mockDescriptiveStats);
      }
      if (url.includes('/api/v1/statistics/channel-comparison')) {
        return jsonResponse(mockHypothesisData);
      }
      return jsonResponse({ success: true, data: null });
    });

    render(
      <MemoryRouter>
        <AuthProvider>
          <StatisticsPage />
        </AuthProvider>
      </MemoryRouter>,
    );

    const hypothesisTab = screen.getByText("Hypothesis Testing (Welch's t-Test)");
    fireEvent.click(hypothesisTab);

    await waitFor(() => {
      expect(
        screen.getByText("Welch's Two-Sample t-Test (Unequal Variances)"),
      ).toBeInTheDocument();
      expect(
        screen.getByText('Statistically Significant (p < 0.05)'),
      ).toBeInTheDocument();
      expect(screen.getByText('t-Statistic')).toBeInTheDocument();
      expect(screen.getByText('-4.772')).toBeInTheDocument();
      expect(screen.getByText("Cohen's d (Effect Size)")).toBeInTheDocument();
      expect(screen.getByText('-0.111')).toBeInTheDocument();
      expect(
        screen.getByText(/Reject the null hypothesis/i),
      ).toBeInTheDocument();
    });
  });
});
