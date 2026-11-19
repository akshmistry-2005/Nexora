import { render, screen, waitFor, within } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { MemoryRouter } from 'react-router-dom';
import { AuthProvider } from '../context/AuthProvider';
import { OverviewPage } from '../features/overview/OverviewPage';

const mockDemoUser = {
  access_token: 'fake-jwt-token',
  token_type: 'Bearer',
  expires_in_seconds: 7200,
  user_id: 3,
  email: 'demo_analyst@nexora.local',
  full_name: 'Marcus Chen (Data Analyst)',
  role: 'data_analyst',
  permissions: ['dashboard.view', 'sales.view'],
};

const mockOverviewData = {
  success: true,
  data: {
    net_revenue: 15420300.5,
    total_orders: 14850,
    total_customers: 2500,
    active_customers: 1820,
    average_order_value: 1038.4,
    gross_profit: 6245000.0,
    gross_margin_pct: 40.5,
    total_expenses: 3120000.0,
    net_profit: 3125000.0,
    net_margin_pct: 20.3,
    inventory_valuation: 4890000.0,
    fulfilment_rate: 97.4,
    marketing_spend: 850000.0,
    revenue_trend: [
      { month: '2025-01', revenue: 1200000.0, orders: 1100 },
      { month: '2025-02', revenue: 1350000.0, orders: 1250 },
    ],
    regional_breakdown: [
      { region: 'North America', revenue: 8500000.0, orders: 8200 },
    ],
    top_products: [
      { name: 'Enterprise Cloud Server', revenue: 450000.0, units: 120 },
    ],
  },
};

const mockLedgerData = {
  success: true,
  data: [
    {
      id: 1,
      order_number: 'ORD-2025-001',
      customer_name: 'Acme Global Corp',
      sales_channel: 'Direct B2B',
      order_date: '2025-06-15T10:00:00Z',
      status: 'completed',
      region: 'North America',
      total_amount: 14850.0,
    },
    {
      id: 2,
      order_number: 'ORD-2025-002',
      customer_name: 'Beacon Systems',
      sales_channel: 'Online Portal',
      order_date: '2025-06-16T11:00:00Z',
      status: 'shipped',
      region: 'Europe & UK',
      total_amount: 8420.0,
    },
  ],
  meta: {
    page: 1,
    page_size: 10,
    total_items: 2,
    total_pages: 1,
    has_next: false,
    has_prev: false,
  },
};

describe('Module 9 — Core Business Intelligence Frontend', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    localStorage.clear();

    vi.spyOn(globalThis, 'fetch').mockImplementation(async (input) => {
      const url = String(input);
      if (url.includes('/api/v1/auth/demo-login')) {
        return {
          ok: true,
          headers: new Headers({ 'content-type': 'application/json' }),
          json: async () => ({ success: true, data: mockDemoUser }),
        } as Response;
      }
      if (url.includes('/api/v1/analytics/overview')) {
        return {
          ok: true,
          headers: new Headers({ 'content-type': 'application/json' }),
          json: async () => mockOverviewData,
        } as Response;
      }
      if (url.includes('/api/v1/analytics/ledger')) {
        return {
          ok: true,
          headers: new Headers({ 'content-type': 'application/json' }),
          json: async () => mockLedgerData,
        } as Response;
      }

      return {
        ok: true,
        headers: new Headers({ 'content-type': 'application/json' }),
        json: async () => ({ success: true, data: {} }),
      } as Response;
    });
  });

  it('renders executive KPI cards and live drill-down order ledger', async () => {
    render(
      <MemoryRouter>
        <AuthProvider>
          <OverviewPage />
        </AuthProvider>
      </MemoryRouter>,
    );

    expect(screen.getByText(/Executive Performance Overview/i)).toBeInTheDocument();

    await waitFor(() => {
      const kpiGrid = screen.getByTestId('overview-kpi-grid');
      expect(within(kpiGrid).getByText('Net Revenue')).toBeInTheDocument();
      expect(within(kpiGrid).getByText('Total Orders')).toBeInTheDocument();
      expect(within(kpiGrid).getByText('Average Order Value')).toBeInTheDocument();
      expect(within(kpiGrid).getByText('Gross Margin')).toBeInTheDocument();
      expect(within(kpiGrid).getByText('Inventory Valuation')).toBeInTheDocument();
      expect(within(kpiGrid).getByText('Fulfilment Rate')).toBeInTheDocument();
    });

    // Check drill-down ledger rendered in DataTable
    expect(screen.getByText('ORD-2025-001')).toBeInTheDocument();
    expect(screen.getByText('Acme Global Corp')).toBeInTheDocument();
    expect(screen.getByText('ORD-2025-002')).toBeInTheDocument();
    expect(screen.getByText('Beacon Systems')).toBeInTheDocument();
  });
});
