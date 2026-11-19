import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { AuthProvider } from '../context/AuthProvider';
import { AdminPage } from '../features/administration/AdminPage';

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
  email: 'owner@nexora.local',
  full_name: 'Elena Vance (Platform Owner)',
  role: 'owner',
  is_owner: true,
  permissions: [
    'dashboard.view',
    'audit.view',
    'user.manage',
    'dataquality.view',
    'dataquality.manage',
    'system.reset_demo',
  ],
};

const mockPipelineSummary = {
  success: true,
  data: {
    active_pipelines_count: 3,
    total_runs_count: 45,
    failed_runs_count: 2,
    last_successful_refresh: '2026-11-19T10:00:00Z',
    pipelines: [
      {
        pipeline_name: 'daily_analytics_aggregation',
        total_runs: 25,
        successful_runs: 24,
        failed_runs: 1,
        last_successful_run_at: '2026-11-19T10:00:00Z',
        last_run_status: 'success',
      },
    ],
    synthetic_notice: 'Demonstration Environment: All telemetry metrics reflect local synthetic execution.',
  },
};

const mockPipelineRuns = {
  success: true,
  data: [
    {
      id: 101,
      import_job_id: null,
      pipeline_name: 'daily_analytics_aggregation',
      status: 'failed',
      duration_ms: 320,
      metrics: { error_message: 'Temporary socket timeout during aggregation' },
      started_at: '2026-11-19T10:15:00Z',
      ended_at: '2026-11-19T10:15:01Z',
    },
    {
      id: 102,
      import_job_id: null,
      pipeline_name: 'inventory_replenishment_sync',
      status: 'success',
      duration_ms: 180,
      metrics: { items_synced: 120 },
      started_at: '2026-11-19T09:00:00Z',
      ended_at: '2026-11-19T09:00:01Z',
    },
  ],
};

const mockSystemStatus = {
  success: true,
  data: {
    platform_name: 'Nexora Enterprise Analytics',
    version: '0.2.0',
    environment: 'demonstration_local',
    is_demonstration: true,
    database_connected: true,
    synthetic_data_notice: 'Demonstration Environment: All data, metrics, and logs are synthetically generated.',
    table_counts: {
      orders: 15000,
      customers: 2500,
      products: 120,
      audit_logs: 180,
    },
    timestamp: '2026-11-19T12:00:00Z',
  },
};

const mockAuditLogs = {
  success: true,
  data: [
    {
      id: 1,
      organization_id: 1,
      actor_user_id: 1,
      actor_role: 'owner',
      action_type: 'AUTH_LOGIN_SUCCESS',
      entity_type: 'user',
      entity_id: '1',
      ip_address: '127.0.0.1',
      details: { email: 'owner@nexora.local' },
      created_at: '2026-11-19T08:00:00Z',
    },
  ],
};

const mockAuditSummary = {
  success: true,
  data: {
    total_logs: 180,
    by_action_type: { AUTH_LOGIN_SUCCESS: 120, REPORT_EXPORT: 40, PIPELINE_RETRY: 20 },
    by_role: { owner: 50, data_analyst: 130 },
  },
};

const mockUsersList = {
  success: true,
  data: [
    {
      id: 1,
      email: 'owner@nexora.local',
      full_name: 'Elena Vance',
      is_active: true,
      is_owner: true,
      roles: ['owner'],
      created_at: '2026-11-18T00:00:00Z',
    },
  ],
};

describe('Module 14 — Pipeline Monitoring & Administration Frontend', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    localStorage.clear();
    localStorage.setItem('nexora_auth_token', 'fake-jwt-token-owner');
  });

  it('renders admin header, mandatory synthetic data notice banner (M14-T13), and telemetry cards', async () => {
    vi.spyOn(globalThis, 'fetch').mockImplementation(async (input) => {
      const url = String(input);
      if (url.includes('/api/v1/auth/')) {
        return jsonResponse({ success: true, data: mockOwnerUser });
      }
      if (url.includes('/api/v1/pipelines/summary')) {
        return jsonResponse(mockPipelineSummary);
      }
      if (url.includes('/api/v1/pipelines/runs')) {
        return jsonResponse(mockPipelineRuns);
      }
      if (url.includes('/api/v1/admin/system-status')) {
        return jsonResponse(mockSystemStatus);
      }
      if (url.includes('/api/v1/admin/audit-logs')) {
        return jsonResponse(mockAuditLogs);
      }
      if (url.includes('/api/v1/admin/audit-summary')) {
        return jsonResponse(mockAuditSummary);
      }
      if (url.includes('/api/v1/admin/users')) {
        return jsonResponse(mockUsersList);
      }
      return jsonResponse({ success: true, data: null });
    });

    render(
      <MemoryRouter>
        <AuthProvider>
          <AdminPage />
        </AuthProvider>
      </MemoryRouter>,
    );

    // Header & synthetic data banner
    expect(screen.getByText('Platform Administration & Pipeline Telemetry')).toBeInTheDocument();
    expect(screen.getByTestId('synthetic-data-notice')).toBeInTheDocument();
    expect(screen.getByText(/All data, pipeline telemetry, and audit logs are synthetically generated/i)).toBeInTheDocument();

    // Verify telemetry cards
    await waitFor(() => {
      expect(screen.getByText('Total Pipeline Runs')).toBeInTheDocument();
      expect(screen.getByText('Failed Pipeline Runs')).toBeInTheDocument();
      expect(screen.getByText('Audit Trail Entries')).toBeInTheDocument();
    });

    // Check pipeline runs table
    await waitFor(() => {
      expect(screen.getByText('daily_analytics_aggregation')).toBeInTheDocument();
      expect(screen.getByTestId('retry-btn-101')).toBeInTheDocument();
    });
  });

  it('switches to audit trail tab and displays append-only database enforcement notice', async () => {
    vi.spyOn(globalThis, 'fetch').mockImplementation(async (input) => {
      const url = String(input);
      if (url.includes('/api/v1/auth/')) {
        return jsonResponse({ success: true, data: mockOwnerUser });
      }
      if (url.includes('/api/v1/pipelines/summary')) {
        return jsonResponse(mockPipelineSummary);
      }
      if (url.includes('/api/v1/pipelines/runs')) {
        return jsonResponse(mockPipelineRuns);
      }
      if (url.includes('/api/v1/admin/system-status')) {
        return jsonResponse(mockSystemStatus);
      }
      if (url.includes('/api/v1/admin/audit-logs')) {
        return jsonResponse(mockAuditLogs);
      }
      if (url.includes('/api/v1/admin/audit-summary')) {
        return jsonResponse(mockAuditSummary);
      }
      if (url.includes('/api/v1/admin/users')) {
        return jsonResponse(mockUsersList);
      }
      return jsonResponse({ success: true, data: null });
    });

    render(
      <MemoryRouter>
        <AuthProvider>
          <AdminPage />
        </AuthProvider>
      </MemoryRouter>,
    );

    // Wait for auth & data load
    await waitFor(() => {
      expect(screen.getByTestId('tab-audit')).toBeInTheDocument();
    });

    // Switch to audit tab
    const auditTab = screen.getByTestId('tab-audit');
    fireEvent.click(auditTab);

    await waitFor(() => {
      expect(screen.getByText(/PostgreSQL Engine Enforcement/i)).toBeInTheDocument();
      expect(screen.getByText('AUTH_LOGIN_SUCCESS')).toBeInTheDocument();
    });
  });

  it('allows Platform Owner to open confirmation modal and trigger demo reset', async () => {
    let resetCalled = false;

    vi.spyOn(globalThis, 'fetch').mockImplementation(async (input) => {
      const url = String(input);
      if (url.includes('/api/v1/auth/')) {
        return jsonResponse({ success: true, data: mockOwnerUser });
      }
      if (url.includes('/api/v1/admin/reset-demo')) {
        resetCalled = true;
        return jsonResponse({
          success: true,
          data: {
            status: 'success',
            message: 'Demonstration dataset reset complete',
            reset_timestamp: '2026-11-19T12:00:00Z',
          },
        });
      }
      if (url.includes('/api/v1/pipelines/summary')) {
        return jsonResponse(mockPipelineSummary);
      }
      if (url.includes('/api/v1/pipelines/runs')) {
        return jsonResponse(mockPipelineRuns);
      }
      if (url.includes('/api/v1/admin/system-status')) {
        return jsonResponse(mockSystemStatus);
      }
      return jsonResponse({ success: true, data: null });
    });

    render(
      <MemoryRouter>
        <AuthProvider>
          <AdminPage />
        </AuthProvider>
      </MemoryRouter>,
    );

    // Wait for auth load to establish owner role
    await waitFor(() => {
      expect(screen.getByTestId('tab-environment')).toBeInTheDocument();
      expect(screen.getByTestId('tab-audit')).toBeInTheDocument();
    });

    // Switch to environment tab
    const envTab = screen.getByTestId('tab-environment');
    fireEvent.click(envTab);

    // Click reset button
    const resetBtn = screen.getByTestId('admin-reset-data-btn');
    expect(resetBtn).not.toBeDisabled();
    fireEvent.click(resetBtn);

    // Modal opens
    expect(screen.getByText('Confirm Demonstration Data Reset')).toBeInTheDocument();

    // Confirm reset
    const confirmBtn = screen.getByTestId('confirm-reset-btn');
    fireEvent.click(confirmBtn);

    await waitFor(() => {
      expect(resetCalled).toBe(true);
    });
  });
});
