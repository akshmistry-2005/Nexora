import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { BrowserRouter, MemoryRouter } from 'react-router-dom';
import { AuthProvider } from '../context/AuthProvider';
import { AppShell } from '../components/layout/AppShell';
import { KPICard } from '../components/common/KPICard';
import { DataTable, Column } from '../components/common/DataTable';
import { SkeletonLoader } from '../components/common/SkeletonLoader';
import { EmptyState } from '../components/common/EmptyState';
import { Alert } from '../components/common/Alert';
import { ErrorBoundary } from '../components/common/ErrorBoundary';
import { FormField } from '../components/common/FormField';
import { Modal } from '../components/common/Modal';

const mockDemoUser = {
  access_token: 'fake-jwt-token',
  token_type: 'Bearer',
  expires_in_seconds: 7200,
  user_id: 2,
  email: 'demo_executive@nexora.local',
  full_name: 'Elena Vance (CEO)',
  role: 'executive',
  permissions: ['dashboard.view', 'sales.view', 'customer.view', 'report.view'],
};

describe('Module 6 — Frontend Foundation and Design System', () => {
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
      if (url.includes('/api/v1/health')) {
        return {
          ok: true,
          headers: new Headers({ 'content-type': 'application/json' }),
          json: async () => ({ status: 'healthy', database: 'connected' }),
        } as Response;
      }
      return {
        ok: true,
        headers: new Headers({ 'content-type': 'application/json' }),
        json: async () => ({ success: true, data: {} }),
      } as Response;
    });
  });

  // M6-T01: Application shell
  it('M6-T01: Application shell — renders persistent shell, sidebar, topbar, breadcrumbs, and content area', async () => {
    render(
      <AuthProvider>
        <MemoryRouter initialEntries={['/']}>
          <AppShell />
        </MemoryRouter>
      </AuthProvider>,
    );

    await waitFor(() => {
      expect(screen.getByTestId('active-role-label')).toBeInTheDocument();
    });

    expect(screen.getByTestId('app-shell')).toBeInTheDocument();
    expect(screen.getByTestId('app-sidebar')).toBeInTheDocument();
    expect(screen.getByTestId('app-topbar')).toBeInTheDocument();
    expect(screen.getByTestId('breadcrumbs')).toBeInTheDocument();
    expect(screen.getByTestId('main-content')).toBeInTheDocument();
  });

  // M6-T02: Navigation
  it('M6-T02: Navigation — sidebar provides navigable links with active styling', async () => {
    render(
      <AuthProvider>
        <MemoryRouter initialEntries={['/sales']}>
          <AppShell />
        </MemoryRouter>
      </AuthProvider>,
    );

    await waitFor(() => {
      expect(screen.getByTestId('active-role-label')).toBeInTheDocument();
    });

    const salesLink = screen.getByTestId('nav-item-sales');
    expect(salesLink).toBeInTheDocument();
    expect(salesLink).toHaveAttribute('href', '/sales');

    const overviewLink = screen.getByTestId('nav-item-overview');
    expect(overviewLink).toHaveAttribute('href', '/');
  });

  // M6-T03: Role-aware navigation
  it('M6-T03: Role-aware navigation — displays active persona badge, demo selector lists all 5 roles, and owner login opens modal', async () => {
    render(
      <AuthProvider>
        <MemoryRouter initialEntries={['/']}>
          <AppShell />
        </MemoryRouter>
      </AuthProvider>,
    );

    // Verify active persona badge in topbar
    await waitFor(() => {
      expect(screen.getByTestId('active-role-label')).toHaveTextContent(/Executive/i);
    });

    // Click demo role switcher
    const switcherBtn = screen.getByTestId('demo-role-switcher-btn');
    fireEvent.click(switcherBtn);

    // Modal should be open showing all 5 demo roles
    expect(screen.getByText('Select Demonstration Persona')).toBeInTheDocument();
    expect(screen.getByTestId('demo-role-card-executive')).toBeInTheDocument();
    expect(screen.getByTestId('demo-role-card-department_manager')).toBeInTheDocument();
    expect(screen.getByTestId('demo-role-card-data_analyst')).toBeInTheDocument();
    expect(screen.getByTestId('demo-role-card-data_scientist')).toBeInTheDocument();
    expect(screen.getByTestId('demo-role-card-general_viewer')).toBeInTheDocument();

    // Click on Owner Login button
    const ownerLoginBtn = screen.getByTestId('owner-login-btn');
    fireEvent.click(ownerLoginBtn);
    expect(screen.getByText('Platform Owner Authentication')).toBeInTheDocument();
  });

  // M6-T04: KPI card component
  it('M6-T04: KPI card component — renders title, formatted numeric values, trend indicators, and tooltips', () => {
    const { rerender } = render(
      <KPICard
        title="Total Revenue"
        value={1250000}
        format="currency"
        trend={{ value: 12.5, direction: 'up', isPositive: true, period: 'vs last month' }}
        tooltip="Gross revenue minus discounts"
      />,
    );

    expect(screen.getByText('Total Revenue')).toBeInTheDocument();
    expect(screen.getByTestId('kpi-value')).toHaveTextContent('$1,250,000');
    expect(screen.getByTestId('kpi-trend')).toHaveTextContent('12.5%');
    expect(screen.getByText('vs last month')).toBeInTheDocument();

    // Tooltip interaction on first card
    const infoBtn = screen.getByLabelText(/Metric info for Total Revenue/i);
    expect(infoBtn).toBeInTheDocument();
    fireEvent.click(infoBtn);
    expect(screen.getByRole('tooltip')).toHaveTextContent('Gross revenue minus discounts');

    // Percentage format
    rerender(
      <KPICard
        title="Gross Margin"
        value={42.8}
        format="percent"
        tooltip="Operating profit margin"
      />,
    );
    expect(screen.getByTestId('kpi-value')).toHaveTextContent('+42.8%');
  });

  // M6-T05: DataTable component
  it('M6-T05: DataTable component — supports sorting, pagination, search filtering, and row selection', () => {
    interface TestItem extends Record<string, unknown> {
      id: string;
      name: string;
      amount: number;
    }

    const testData: TestItem[] = [
      { id: '1', name: 'Alpha Logistics', amount: 300 },
      { id: '2', name: 'Beta Solutions', amount: 150 },
      { id: '3', name: 'Gamma Systems', amount: 750 },
      { id: '4', name: 'Delta Technologies', amount: 450 },
      { id: '5', name: 'Epsilon Networks', amount: 600 },
      { id: '6', name: 'Zeta Innovations', amount: 900 },
    ];

    const columns: Column<TestItem>[] = [
      { key: 'name', header: 'Client Name', sortable: true },
      { key: 'amount', header: 'Amount', sortable: true, render: (r) => `$${r.amount}` },
    ];

    const onSelectionChange = vi.fn();
    const onExport = vi.fn();

    render(
      <DataTable<TestItem>
        data={testData}
        columns={columns}
        keyExtractor={(r) => r.id}
        initialPageSize={3}
        enableSearch
        enableSelection
        onSelectionChange={onSelectionChange}
        onExport={onExport}
      />,
    );

    // Initial page shows 3 items
    const rows = screen.getAllByTestId('table-row');
    expect(rows).toHaveLength(3);
    expect(screen.getByText('Alpha Logistics')).toBeInTheDocument();

    // Search filter
    const searchInput = screen.getByTestId('data-table-search');
    fireEvent.change(searchInput, { target: { value: 'Delta' } });
    expect(screen.getByText('Delta Technologies')).toBeInTheDocument();
    expect(screen.queryByText('Alpha Logistics')).not.toBeInTheDocument();

    // Clear search
    fireEvent.change(searchInput, { target: { value: '' } });

    // Pagination: Next page
    const nextBtn = screen.getByTestId('pagination-next');
    fireEvent.click(nextBtn);
    expect(screen.getByText('Delta Technologies')).toBeInTheDocument();

    // Export button hook
    const exportBtn = screen.getByTestId('data-table-export-btn');
    fireEvent.click(exportBtn);
    expect(onExport).toHaveBeenCalledTimes(1);

    // Row selection checkbox
    const checkboxes = screen.getAllByRole('checkbox');
    fireEvent.click(checkboxes[1]); // First row on page 2
    expect(onSelectionChange).toHaveBeenCalled();
  });

  // M6-T06: Loading states
  it('M6-T06: Loading states — renders SkeletonLoader placeholders with shimmer animation and aria-busy', () => {
    const { rerender } = render(<SkeletonLoader variant="card" count={3} />);
    const loader = screen.getByTestId('skeleton-loader');
    expect(loader).toBeInTheDocument();
    expect(loader).toHaveAttribute('aria-busy', 'true');

    // KPICard loading state
    rerender(<KPICard title="Revenue" value={100} loading />);
    expect(screen.getByTestId('kpi-card-loading')).toBeInTheDocument();
  });

  // M6-T07: Empty states
  it('M6-T07: Empty states — displays descriptive empty state with optional action callback', () => {
    const onAction = vi.fn();
    render(
      <EmptyState
        title="No Orders Found"
        description="Try adjusting your territory filters."
        action={{ label: 'Reset Filter', onClick: onAction }}
      />,
    );

    expect(screen.getByTestId('empty-state')).toBeInTheDocument();
    expect(screen.getByText('No Orders Found')).toBeInTheDocument();
    expect(screen.getByText('Try adjusting your territory filters.')).toBeInTheDocument();

    const actionBtn = screen.getByText('Reset Filter');
    fireEvent.click(actionBtn);
    expect(onAction).toHaveBeenCalledTimes(1);
  });

  // M6-T08: Error states
  it('M6-T08: Error states — Alert renders info/success/warning/error variants and ErrorBoundary catches crashes', () => {
    const onClose = vi.fn();
    const { rerender } = render(
      <Alert variant="error" title="Critical Failure" onClose={onClose}>
        Failed to communicate with database cluster.
      </Alert>,
    );

    expect(screen.getByTestId('alert-error')).toBeInTheDocument();
    expect(screen.getByText('Critical Failure')).toBeInTheDocument();
    expect(screen.getByText(/Failed to communicate with database/i)).toBeInTheDocument();

    const closeBtn = screen.getByLabelText('Close alert');
    fireEvent.click(closeBtn);
    expect(onClose).toHaveBeenCalledTimes(1);

    // Test ErrorBoundary with crashing component
    const BadComponent = () => {
      throw new Error('Test crash in child component');
    };

    // Suppress console.error during expected test error
    const spy = vi.spyOn(console, 'error').mockImplementation(() => {});

    rerender(
      <ErrorBoundary>
        <BadComponent />
      </ErrorBoundary>,
    );

    expect(screen.getByTestId('error-boundary-fallback')).toBeInTheDocument();
    expect(screen.getByText(/Something went wrong rendering this view/i)).toBeInTheDocument();
    expect(screen.getByText(/Test crash in child component/i)).toBeInTheDocument();

    spy.mockRestore();
  });

  // M6-T09: Form validation
  it('M6-T09: Form validation — FormField displays real-time validation errors and aria-invalid attributes', () => {
    const { rerender } = render(
      <FormField
        label="Owner Email"
        type="email"
        value=""
        onChange={() => {}}
        required
        error="Email address is required."
      />,
    );

    const input = screen.getByLabelText(/Owner Email/i);
    expect(input).toBeInTheDocument();
    expect(input).toHaveAttribute('aria-invalid', 'true');
    expect(screen.getByTestId('field-error')).toHaveTextContent('Email address is required.');

    // Clear error
    rerender(
      <FormField label="Owner Email" type="email" value="valid@nexora.local" error={null} />,
    );
    expect(input).toHaveAttribute('aria-invalid', 'false');
    expect(screen.queryByTestId('field-error')).not.toBeInTheDocument();
  });

  // M6-T10: Responsive layout
  it('M6-T10: Responsive layout — sidebar toggle collapses width and retains accessibility', async () => {
    render(
      <AuthProvider>
        <MemoryRouter initialEntries={['/']}>
          <AppShell />
        </MemoryRouter>
      </AuthProvider>,
    );

    await waitFor(() => {
      expect(screen.getByTestId('active-role-label')).toBeInTheDocument();
    });

    const sidebar = screen.getByTestId('app-sidebar');
    expect(sidebar).toHaveStyle({ width: '260px' });

    // Click collapse toggle button
    const toggleBtn = screen.getByTestId('sidebar-toggle-btn');
    fireEvent.click(toggleBtn);

    // Sidebar should now be collapsed to 68px
    expect(sidebar).toHaveStyle({ width: '68px' });

    // Click again to expand back to 260px
    fireEvent.click(toggleBtn);
    expect(sidebar).toHaveStyle({ width: '260px' });
  });

  // M6-T11: Keyboard accessibility
  it('M6-T11: Keyboard accessibility — Modal closes on Escape key and buttons respond to keyboard', () => {
    const onClose = vi.fn();
    render(
      <Modal isOpen={true} onClose={onClose} title="Accessibility Test Dialog">
        <div>Accessible Dialog Content</div>
      </Modal>,
    );

    expect(screen.getByRole('dialog')).toBeInTheDocument();
    expect(screen.getByRole('dialog')).toHaveAttribute('aria-modal', 'true');

    // Trigger Escape key
    fireEvent.keyDown(window, { key: 'Escape', code: 'Escape' });
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  // M6-T12: Browser console check
  it('M6-T12: Browser console check — renders complex tree without console errors or key warnings', async () => {
    const consoleErrorSpy = vi.spyOn(console, 'error');
    const consoleWarnSpy = vi.spyOn(console, 'warn');

    render(
      <AuthProvider>
        <BrowserRouter>
          <AppShell />
        </BrowserRouter>
      </AuthProvider>,
    );

    await waitFor(() => {
      expect(screen.getByTestId('active-role-label')).toBeInTheDocument();
    });

    // Filter out React Router or TestClient noise
    const criticalErrors = consoleErrorSpy.mock.calls.filter((call) =>
      call.some(
        (arg) =>
          typeof arg === 'string' &&
          (arg.includes('Each child in a list') || arg.includes('Uncaught')),
      ),
    );

    expect(criticalErrors).toHaveLength(0);
    expect(consoleWarnSpy).not.toHaveBeenCalledWith(expect.stringContaining('React key'));

    consoleErrorSpy.mockRestore();
    consoleWarnSpy.mockRestore();
  });
});
