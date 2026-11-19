import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { AuthProvider } from '../context/AuthProvider';
import { AnomaliesPage } from '../features/anomalies/AnomaliesPage';

const jsonResponse = (data: unknown) =>
  ({
    ok: true,
    status: 200,
    headers: new Headers({ 'content-type': 'application/json' }),
    json: async () => data,
  }) as unknown as Response;

const mockOwnerUser = {
  access_token: 'fake-jwt-token-owner',
  token_type: 'Bearer',
  expires_in_seconds: 7200,
  user_id: 1,
  email: 'demo_owner@nexora.local',
  full_name: 'Elena Vance (Platform Owner)',
  role: 'owner',
  permissions: ['anomaly.view', 'anomaly.acknowledge', 'dashboard.view'],
};

const mockStats = {
  success: true,
  data: {
    total_alerts: 4,
    open_alerts: 3,
    critical_count: 2,
    high_count: 1,
    medium_count: 1,
    low_count: 0,
    acknowledged_count: 1,
    by_domain: { sales: 1, transaction: 1, inventory: 1, marketing: 1 },
  },
};

const mockAlerts = {
  success: true,
  data: [
    {
      id: 1,
      organization_id: 1,
      domain: 'sales',
      entity_identifier: '2025-04-18',
      metric_name: 'daily_revenue',
      observed_value: 1420.0,
      baseline_value: 8950.0,
      deviation_amount: -7530.0,
      z_score: -3.85,
      severity: 'critical',
      explanation: 'Observed daily sales revenue dropped by 84% compared to baseline average ($8,950.00).',
      status: 'open',
      detected_at: '2025-06-12T12:00:00Z',
      acknowledged_at: null,
      acknowledged_by_id: null,
      created_at: '2025-06-12T12:00:00Z',
    },
    {
      id: 2,
      organization_id: 1,
      domain: 'transaction',
      entity_identifier: 'ORD-2025-008412',
      metric_name: 'order_total',
      observed_value: 14890.0,
      baseline_value: 1420.0,
      deviation_amount: 13470.0,
      z_score: 4.2,
      severity: 'high',
      explanation: 'Order total is 10.5x above standard customer order size. Flagged for review; not confirmed fraud.',
      status: 'open',
      detected_at: '2025-06-12T12:00:00Z',
      acknowledged_at: null,
      acknowledged_by_id: null,
      created_at: '2025-06-12T12:00:00Z',
    },
  ],
};

const mockBenchmark = {
  success: true,
  data: {
    algorithm: 'IsolationForest (scikit-learn)',
    contamination_rate: 0.03,
    total_observations_evaluated: 750,
    statistical_baseline_detected: 8,
    isolation_forest_detected: 22,
    overlap_count: 7,
    concordance_rate: 87.5,
    benchmark_evaluation: 'Isolation Forest detected 15 additional composite anomalies beyond univariate Z-scores.',
    total_samples_evaluated: 750,
    univariate_anomalies_detected: 8,
    multivariate_anomalies_detected: 22,
    agreement_rate_pct: 87.5,
  },
};

describe('Module 13 — Anomaly Detection & Risk Intelligence Frontend', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    localStorage.clear();
  });

  it('renders anomaly dashboard header, KPI cards, and alerts table with mathematical explanations', async () => {
    vi.spyOn(globalThis, 'fetch').mockImplementation(async (input) => {
      const url = String(input);
      if (url.includes('/api/v1/auth/')) {
        return jsonResponse({ success: true, data: mockOwnerUser });
      }
      if (url.includes('/api/v1/anomalies/stats')) {
        return jsonResponse(mockStats);
      }
      if (url.includes('/api/v1/anomalies')) {
        return jsonResponse(mockAlerts);
      }
      return jsonResponse({ success: true, data: null });
    });

    render(
      <MemoryRouter>
        <AuthProvider>
          <AnomaliesPage />
        </AuthProvider>
      </MemoryRouter>,
    );

    // Title verification
    expect(screen.getByText('Anomaly Detection & Risk Intelligence')).toBeInTheDocument();

    // KPI cards loaded
    await waitFor(() => {
      expect(screen.getByText('Total Alerts Logged')).toBeInTheDocument();
      expect(screen.getByText('Open Anomalies')).toBeInTheDocument();
      expect(screen.getByText('Critical Severities')).toBeInTheDocument();
    });

    // Verify alerts table rendered with objective explanation
    await waitFor(() => {
      expect(screen.getByText('daily_revenue')).toBeInTheDocument();
      expect(screen.getByText(/Observed daily sales revenue dropped by 84%/i)).toBeInTheDocument();
    });

    // Owner action button exists
    expect(screen.getByTestId('run-scan-btn')).toBeInTheDocument();
    expect(screen.getByTestId('triage-btn-1')).toBeInTheDocument();
  });

  it('switches to Isolation Forest Benchmark tab (BL-16) and renders multivariate comparisons', async () => {
    vi.spyOn(globalThis, 'fetch').mockImplementation(async (input) => {
      const url = String(input);
      if (url.includes('/api/v1/auth/')) {
        return jsonResponse({ success: true, data: mockOwnerUser });
      }
      if (url.includes('/api/v1/anomalies/stats')) {
        return jsonResponse(mockStats);
      }
      if (url.includes('/api/v1/anomalies/benchmark/isolation-forest')) {
        return jsonResponse(mockBenchmark);
      }
      if (url.includes('/api/v1/anomalies')) {
        return jsonResponse(mockAlerts);
      }
      return jsonResponse({ success: true, data: null });
    });

    render(
      <MemoryRouter>
        <AuthProvider>
          <AnomaliesPage />
        </AuthProvider>
      </MemoryRouter>,
    );

    // Switch to benchmark tab
    const benchTab = screen.getByTestId('tab-isolation-forest');
    fireEvent.click(benchTab);

    // Verify benchmark metrics
    await waitFor(() => {
      expect(screen.getByText(/Multivariate ML vs Univariate Statistical Baseline/i)).toBeInTheDocument();
      expect(screen.getByText('Evaluated Samples')).toBeInTheDocument();
      expect(screen.getByText('Isolation Forest Outliers')).toBeInTheDocument();
      expect(screen.getByText('Concordant (Overlap)')).toBeInTheDocument();
    });
  });

  it('opens triage modal and submits acknowledgement workflow for an anomaly alert', async () => {
    let ackPayloadSent: unknown = null;

    vi.spyOn(globalThis, 'fetch').mockImplementation(async (input, init) => {
      const url = String(input);
      if (url.includes('/api/v1/auth/')) {
        return jsonResponse({ success: true, data: mockOwnerUser });
      }
      if (url.includes('/api/v1/anomalies/stats')) {
        return jsonResponse(mockStats);
      }
      if (url.includes('/acknowledge')) {
        ackPayloadSent = JSON.parse((init?.body as string) || '{}');
        return jsonResponse({
          success: true,
          data: { ...mockAlerts.data[0], status: 'acknowledged' },
        });
      }
      if (url.includes('/api/v1/anomalies')) {
        return jsonResponse(mockAlerts);
      }
      return jsonResponse({ success: true, data: null });
    });

    render(
      <MemoryRouter>
        <AuthProvider>
          <AnomaliesPage />
        </AuthProvider>
      </MemoryRouter>,
    );

    // Wait for table to load
    await waitFor(() => {
      expect(screen.getByTestId('triage-btn-1')).toBeInTheDocument();
    });

    // Open triage modal
    fireEvent.click(screen.getByTestId('triage-btn-1'));
    expect(screen.getByText('Triage Anomaly #1')).toBeInTheDocument();

    // Type notes and submit
    const notesInput = screen.getByPlaceholderText(/Record root cause or mitigation steps/i);
    fireEvent.change(notesInput, { target: { value: 'Verified network outage during Easter promotion.' } });

    const submitBtn = screen.getByText('Save Triage Status');
    fireEvent.click(submitBtn);

    // Verify payload sent
    await waitFor(() => {
      expect(ackPayloadSent).toEqual({
        status: 'acknowledged',
        notes: 'Verified network outage during Easter promotion.',
      });
    });
  });
});
