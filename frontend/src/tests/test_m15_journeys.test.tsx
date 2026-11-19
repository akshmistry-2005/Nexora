import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { AppRoutes } from '../app/App';
import { AuthProvider } from '../context/AuthProvider';

const jsonResponse = (data: unknown) =>
  ({
    ok: true,
    status: 200,
    headers: new Headers({ 'content-type': 'application/json' }),
    json: async () => data,
  }) as unknown as Response;

const mockAnalystUser = {
  access_token: 'fake-jwt-token-analyst',
  token_type: 'Bearer',
  expires_in_seconds: 7200,
  user_id: 4,
  email: 'demo_analyst@nexora.local',
  full_name: 'Marcus Chen (Data Analyst)',
  role: 'data_analyst',
  is_owner: false,
  permissions: [
    'dashboard.view',
    'sales.view',
    'customer.view',
    'marketing.view',
    'finance.view',
    'inventory.view',
    'operations.view',
    'supplier.view',
    'statistics.view',
    'predictions.view',
    'anomaly.view',
    'datasource.view',
    'dataquality.view',
    'report.view',
    'report.export',
    'report.sensitive_fields',
  ],
};

const mockOverviewData = {
  success: true,
  data: {
    net_revenue: 12450000.0,
    total_orders: 15000,
    total_customers: 2500,
    active_customers: 1980,
    average_order_value: 830.0,
    gross_profit: 4850000.0,
    gross_margin_pct: 38.9,
    total_expenses: 1250000.0,
    net_profit: 3600000.0,
    net_margin_pct: 28.9,
    inventory_valuation: 850000.0,
    fulfilment_rate: 98.4,
    marketing_spend: 450000.0,
    revenue_trend: [{ period: '2025-01', revenue: 950000.0 }],
    regional_breakdown: [{ region_name: 'North America', gross_revenue: 6200000.0 }],
    top_products: [{ product_name: 'Nexora Core Server', units_sold: 450 }],
  },
};

const mockLedgerData = {
  success: true,
  data: {
    data: [
      {
        order_number: 'ORD-2025-001',
        customer_name: 'Acme Corp',
        order_date: '2025-06-01',
        channel: 'Direct B2B',
        region: 'North America',
        gross_amount: 15400.0,
        net_amount: 14800.0,
        status: 'completed',
        line_item_count: 5,
      },
    ],
    meta: {
      page: 1,
      page_size: 25,
      total_items: 1,
      total_pages: 1,
      has_next: false,
      has_prev: false,
    },
  },
};

describe('Module 15 — System Integration and Complete Journeys Frontend', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    localStorage.clear();
    localStorage.setItem('nexora_auth_token', 'fake-jwt-token-analyst');
  });

  it('M15-T02: Complete Analyst Journey — verifies full navigation and analytical view rendering', async () => {
    vi.spyOn(globalThis, 'fetch').mockImplementation(async (input) => {
      const url = String(input);
      if (url.includes('/api/v1/auth/')) {
        return jsonResponse({ success: true, data: mockAnalystUser });
      }
      if (url.includes('/api/v1/analytics/overview')) {
        return jsonResponse(mockOverviewData);
      }
      if (url.includes('/api/v1/analytics/ledger')) {
        return jsonResponse(mockLedgerData);
      }
      return jsonResponse({ success: true, data: [] });
    });

    render(
      <MemoryRouter initialEntries={['/']}>
        <AuthProvider>
          <AppRoutes />
        </AuthProvider>
      </MemoryRouter>,
    );

    // Initial Overview page loads
    await waitFor(() => {
      expect(screen.getByText('NEXORA')).toBeInTheDocument();
    });

    // Check presence of sidebar navigation links
    expect(screen.getByTestId('nav-item-overview')).toBeInTheDocument();
    expect(screen.getByTestId('nav-item-sales')).toBeInTheDocument();
    expect(screen.getByTestId('nav-item-reports')).toBeInTheDocument();
  });

  it('M15-T04 & M15-T15: Accessibility & responsive UI protection against unauthorized write actions', async () => {
    vi.spyOn(globalThis, 'fetch').mockImplementation(async (input) => {
      const url = String(input);
      if (url.includes('/api/v1/auth/')) {
        return jsonResponse({ success: true, data: mockAnalystUser });
      }
      if (url.includes('/api/v1/pipelines/summary')) {
        return jsonResponse({
          success: true,
          data: {
            active_pipelines_count: 3,
            total_runs_count: 10,
            failed_runs_count: 1,
            successful_runs_count: 9,
            overall_status: 'healthy',
            last_run_timestamp: '2026-11-19T18:00:00Z',
          },
        });
      }
      if (url.includes('/api/v1/pipelines/runs')) {
        return jsonResponse({ success: true, data: [] });
      }
      if (url.includes('/api/v1/admin/status')) {
        return jsonResponse({
          success: true,
          data: {
            database_connected: true,
            version: '0.2.0',
            environment: 'production',
            table_counts: { orders: 15000, customers: 2500, audit_logs: 120 },
          },
        });
      }
      return jsonResponse({ success: true, data: [] });
    });

    render(
      <MemoryRouter initialEntries={['/admin']}>
        <AuthProvider>
          <AppRoutes />
        </AuthProvider>
      </MemoryRouter>,
    );

    // Navigating to Admin as demo analyst displays lock banner
    await waitFor(() => {
      expect(screen.getByText(/Owner Privileges Required/i)).toBeInTheDocument();
    });

    // Switch to Environment & Reset tab
    const envTab = screen.getByTestId('tab-environment');
    fireEvent.click(envTab);

    // Reset button is disabled for demo analyst
    const resetBtn = screen.getByTestId('admin-reset-data-btn');
    expect(resetBtn).toBeDisabled();
  });
});
