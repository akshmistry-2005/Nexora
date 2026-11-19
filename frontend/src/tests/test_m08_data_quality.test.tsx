import { fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { MemoryRouter } from 'react-router-dom';
import { AuthProvider } from '../context/AuthProvider';
import { DataQualityPage } from '../features/data-quality/DataQualityPage';

const mockDemoUser = {
  access_token: 'fake-jwt-token',
  token_type: 'Bearer',
  expires_in_seconds: 7200,
  user_id: 3,
  email: 'demo_analyst@nexora.local',
  full_name: 'Marcus Chen (Data Analyst)',
  role: 'data_analyst',
  permissions: ['dataquality.view', 'dashboard.view'],
};

const mockSummaryResponse = {
  success: true,
  data: {
    total_records: 114500,
    dimensions: {
      completeness: 99.7,
      validity: 99.3,
      uniqueness: 100.0,
      consistency: 99.4,
      timeliness: 98.8,
      overall_score: 99.5,
    },
    tables: [
      {
        table_name: 'customers',
        total_records: 2500,
        completeness: 99.8,
        validity: 99.2,
        uniqueness: 100.0,
        consistency: 99.5,
        timeliness: 98.9,
        overall_score: 99.5,
      },
      {
        table_name: 'orders',
        total_records: 85000,
        completeness: 99.5,
        validity: 99.0,
        uniqueness: 100.0,
        consistency: 99.1,
        timeliness: 98.5,
        overall_score: 99.3,
      },
      {
        table_name: 'products',
        total_records: 150,
        completeness: 100.0,
        validity: 100.0,
        uniqueness: 100.0,
        consistency: 100.0,
        timeliness: 100.0,
        overall_score: 100.0,
      },
    ],
    last_evaluated_at: '2026-11-19T10:00:00Z',
  },
};

describe('Module 8 — Data Quality Engine Frontend', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    localStorage.clear();

    vi.spyOn(globalThis, 'fetch').mockImplementation(async (input) => {
      const url = String(input);
      if (url.includes('/api/v1/auth/demo-login')) {
        return {
          ok: true,
          headers: new Headers({ 'content-type': 'application/json' }),
          json: async () => ({
            success: true,
            data: mockDemoUser,
          }),
        } as Response;
      }
      if (url.includes('/api/v1/data-quality/summary')) {
        return {
          ok: true,
          headers: new Headers({ 'content-type': 'application/json' }),
          json: async () => mockSummaryResponse,
        } as Response;
      }

      return {
        ok: true,
        headers: new Headers({ 'content-type': 'application/json' }),
        json: async () => ({ success: true, data: {} }),
      } as Response;
    });
  });

  it('renders 5-dimensional data quality KPIs and table scorecard breakdown', async () => {
    render(
      <MemoryRouter>
        <AuthProvider>
          <DataQualityPage />
        </AuthProvider>
      </MemoryRouter>,
    );

    expect(screen.getByText(/Data Quality Engine & Validation Rules/i)).toBeInTheDocument();

    await waitFor(() => {
      const kpiGrid = screen.getByTestId('quality-kpi-grid');
      expect(within(kpiGrid).getByText('Overall Quality')).toBeInTheDocument();
      expect(within(kpiGrid).getByText('Completeness')).toBeInTheDocument();
      expect(within(kpiGrid).getByText('Validity')).toBeInTheDocument();
      expect(within(kpiGrid).getByText('Uniqueness')).toBeInTheDocument();
      expect(within(kpiGrid).getByText('Consistency')).toBeInTheDocument();
      expect(within(kpiGrid).getByText('Timeliness')).toBeInTheDocument();
    });

    // Check production tables breakdown
    expect(screen.getByText('customers')).toBeInTheDocument();
    expect(screen.getByText('orders')).toBeInTheDocument();
    expect(screen.getByText('products')).toBeInTheDocument();
  });

  it('allows switching to staging tab and displays anomalies table with disabled buttons for demo user', async () => {
    render(
      <MemoryRouter>
        <AuthProvider>
          <DataQualityPage />
        </AuthProvider>
      </MemoryRouter>,
    );

    const stagingTab = screen.getByRole('button', { name: /Staging Cleaning & Lineage/i });
    fireEvent.click(stagingTab);

    // Staging table inspection
    expect(screen.getByText(/Detected Quality Anomalies & Cleaning Recommendations/i)).toBeInTheDocument();
    expect(screen.getByText(/customer_type/i)).toBeInTheDocument();
    expect(screen.getByText(/signup_date/i)).toBeInTheDocument();
    expect(screen.getByText(/unit_price/i)).toBeInTheDocument();

    // Verify demo role restriction
    const cleanBtn = screen.getByTestId('clean-staging-button');
    const approveBtn = screen.getByTestId('approve-curated-button');
    expect(cleanBtn).toBeDisabled();
    expect(approveBtn).toBeDisabled();
  });
});
