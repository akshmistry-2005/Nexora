import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { AuthProvider } from '../context/AuthProvider';
import { ReportsPage } from '../features/reports/ReportsPage';

const jsonResponse = (data: unknown) => ({
  ok: true,
  status: 200,
  headers: new Headers({ 'content-type': 'application/json' }),
  json: async () => data,
  blob: async () => new Blob(['# CSV Data\r\ncol1,col2\r\nval1,val2\r\n'], { type: 'text/csv' }),
}) as unknown as Response;

const mockAnalystUser = {
  access_token: 'fake-jwt-token',
  token_type: 'Bearer',
  expires_in_seconds: 7200,
  user_id: 3,
  email: 'demo_analyst@nexora.local',
  full_name: 'Marcus Chen (Data Analyst)',
  role: 'data_analyst',
  permissions: ['dashboard.view', 'report.view', 'report.export', 'report.sensitive_fields'],
};

const mockViewerUser = {
  access_token: 'fake-jwt-token-viewer',
  token_type: 'Bearer',
  expires_in_seconds: 7200,
  user_id: 5,
  email: 'demo_viewer@nexora.local',
  full_name: 'Alex Rivera (Viewer)',
  role: 'general_viewer',
  permissions: ['dashboard.view', 'report.view'],
};

const mockCatalogueData = {
  success: true,
  data: [
    {
      report_id: 'overview-kpis',
      name: 'Executive Business Overview',
      domain: 'overview',
      description: 'Cross-functional executive summary including gross revenue, net profit.',
      cadence: 'Daily',
      exportable: true,
      columns: ['period', 'net_revenue', 'gross_profit'],
      sensitive_columns: ['gross_profit'],
    },
    {
      report_id: 'sales-performance',
      name: 'Sales & Regional Territory Breakdown',
      domain: 'sales',
      description: 'Detailed sales revenue, order volumes, discount totals, and regional distribution.',
      cadence: 'Daily',
      exportable: true,
      columns: ['order_number', 'order_date', 'customer_name', 'net_revenue', 'cost_of_goods_sold'],
      sensitive_columns: ['cost_of_goods_sold'],
    },
  ],
};

const mockReportData = {
  success: true,
  data: {
    report_id: 'sales-performance',
    name: 'Sales & Regional Territory Breakdown',
    domain: 'sales',
    generated_at: '2026-11-19T11:00:00Z',
    total_rows: 2,
    columns: ['order_number', 'customer_name', 'net_revenue'],
    summary: {
      total_orders: 2,
      net_revenue: 14500.0,
    },
    rows: [
      { order_number: 'ORD-1001', customer_name: 'Acme Corp', net_revenue: 9500.0 },
      { order_number: 'ORD-1002', customer_name: 'Globex Ltd', net_revenue: 5000.0 },
    ],
    synthetic_notice: 'Synthetic Data Demonstration — Generated for Local Analytics Evaluation',
  },
};

const mockSavedViews = {
  success: true,
  data: [
    {
      id: 1,
      user_id: 3,
      creator_name: 'Marcus Chen',
      section: 'sales',
      name: 'Midwest High Value Orders Q4',
      filter_config: { region_id: 2, sales_channel: 'Direct' },
      is_shared: true,
      created_at: '2026-11-19T10:00:00Z',
    },
  ],
};

describe('Module 10 — Reports, Exports and Saved Views Frontend', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    localStorage.clear();
  });

  it('renders report catalogue, synthetic notice banner, and headline metrics', async () => {
    vi.spyOn(globalThis, 'fetch').mockImplementation(async (input) => {
      const url = String(input);
      if (url.includes('/api/v1/auth/')) {
        return jsonResponse({ success: true, data: mockAnalystUser });
      }
      if (url.includes('/api/v1/reports/catalogue')) {
        return jsonResponse(mockCatalogueData);
      }
      if (url.includes('/api/v1/reports/saved-views')) {
        return jsonResponse(mockSavedViews);
      }
      return jsonResponse({ success: true, data: [] });
    });

    render(
      <MemoryRouter>
        <AuthProvider>
          <ReportsPage />
        </AuthProvider>
      </MemoryRouter>,
    );

    expect(screen.getByText('Standard Reports & Data Exports')).toBeInTheDocument();
    expect(
      screen.getByText(/Synthetic Data Demonstration Notice/i),
    ).toBeInTheDocument();
    expect(screen.getByText('Formula Injection Guard')).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText('Executive Business Overview')).toBeInTheDocument();
      expect(screen.getByText('Sales & Regional Territory Breakdown')).toBeInTheDocument();
    });
  });

  it('enables export button for authorized analyst and displays active report viewer', async () => {
    vi.spyOn(globalThis, 'fetch').mockImplementation(async (input) => {
      const url = String(input);
      if (url.includes('/api/v1/auth/')) {
        return jsonResponse({ success: true, data: mockAnalystUser });
      }
      if (url.includes('/api/v1/reports/catalogue')) {
        return jsonResponse(mockCatalogueData);
      }
      if (url.includes('/api/v1/reports/saved-views')) {
        return jsonResponse(mockSavedViews);
      }
      if (url.includes('/api/v1/reports/sales-performance/data')) {
        return jsonResponse(mockReportData);
      }
      return jsonResponse({ success: true, data: [] });
    });

    render(
      <MemoryRouter>
        <AuthProvider>
          <ReportsPage />
        </AuthProvider>
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(screen.getByText('Sales & Regional Territory Breakdown')).toBeInTheDocument();
    });

    // Switch to viewer tab
    const viewerTabBtn = screen.getByText(/Active Report Viewer/i);
    fireEvent.click(viewerTabBtn);

    await waitFor(() => {
      expect(screen.getByTestId('export-csv-button')).toBeInTheDocument();
      expect(screen.getByTestId('export-csv-button')).not.toBeDisabled();
      expect(screen.getByText('ORD-1001')).toBeInTheDocument();
      expect(screen.getByText('Acme Corp')).toBeInTheDocument();
      expect(screen.getByText('PDF Export (v1.1)')).toBeInTheDocument();
    });
  });

  it('restricts export button for demo general viewer without export permission', async () => {
    vi.spyOn(globalThis, 'fetch').mockImplementation(async (input) => {
      const url = String(input);
      if (url.includes('/api/v1/auth/')) {
        return jsonResponse({ success: true, data: mockViewerUser });
      }
      if (url.includes('/api/v1/reports/catalogue')) {
        return jsonResponse(mockCatalogueData);
      }
      if (url.includes('/api/v1/reports/saved-views')) {
        return jsonResponse(mockSavedViews);
      }
      if (url.includes('/api/v1/reports/sales-performance/data')) {
        return jsonResponse(mockReportData);
      }
      return jsonResponse({ success: true, data: [] });
    });

    render(
      <MemoryRouter>
        <AuthProvider>
          <ReportsPage />
        </AuthProvider>
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(screen.getByText('Sales & Regional Territory Breakdown')).toBeInTheDocument();
    });

    // Switch to viewer tab
    const viewerTabBtn = screen.getByText(/Active Report Viewer/i);
    fireEvent.click(viewerTabBtn);

    await waitFor(() => {
      const exportBtn = screen.getByTestId('export-csv-button');
      expect(exportBtn).toBeDisabled();
    });
  });
});
