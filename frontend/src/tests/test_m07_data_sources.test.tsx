import { render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { MemoryRouter } from 'react-router-dom';
import { AuthProvider } from '../context/AuthProvider';
import { DataSourcesPage } from '../features/data-sources/DataSourcesPage';

const mockDemoUser = {
  access_token: 'fake-jwt-token',
  token_type: 'Bearer',
  expires_in_seconds: 7200,
  user_id: 3,
  email: 'demo_analyst@nexora.local',
  full_name: 'Marcus Chen (Data Analyst)',
  role: 'data_analyst',
  permissions: ['datasource.view', 'dashboard.view'],
};

const mockHistoryResponse = {
  success: true,
  data: [
    {
      id: 101,
      data_source_id: 1,
      target_entity: 'customers',
      status: 'completed',
      total_rows: 50,
      loaded_rows: 50,
      rejected_rows: 0,
      mapping_config: { customer_code: 'code' },
      error_details: null,
      started_at: '2026-11-19T10:00:00Z',
      completed_at: '2026-11-19T10:00:05Z',
    },
  ],
  meta: {
    page: 1,
    page_size: 50,
    total_items: 1,
    total_pages: 1,
    has_next: false,
    has_prev: false,
  },
};

describe('Module 7 — Data Ingestion & Source Management Frontend', () => {
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
      if (url.includes('/api/v1/data-sources/history')) {
        return {
          ok: true,
          headers: new Headers({ 'content-type': 'application/json' }),
          json: async () => mockHistoryResponse,
        } as Response;
      }
      return {
        ok: true,
        headers: new Headers({ 'content-type': 'application/json' }),
        json: async () => ({ success: true, data: [] }),
      } as Response;
    });
  });

  it('renders page header and KPI metrics', async () => {
    render(
      <MemoryRouter>
        <AuthProvider>
          <DataSourcesPage />
        </AuthProvider>
      </MemoryRouter>,
    );

    expect(
      screen.getByRole('heading', { name: /Data Ingestion & Source Management/i }),
    ).toBeInTheDocument();
    expect(screen.getByText(/Completed Ingestions/i)).toBeInTheDocument();
    expect(screen.getByText(/Total Ingested Records/i)).toBeInTheDocument();
    expect(screen.getByText(/Rollback Protection/i)).toBeInTheDocument();
  });

  it('displays read-only warning for demo users and fetches ingestion history', async () => {
    render(
      <MemoryRouter>
        <AuthProvider>
          <DataSourcesPage />
        </AuthProvider>
      </MemoryRouter>,
    );

    // Should display read-only warning banner for demo roles
    await waitFor(() => {
      expect(screen.getByText(/Read-Only Mode/i)).toBeInTheDocument();
    });

    // Should display history record in the table
    await waitFor(() => {
      expect(screen.getByText('#101')).toBeInTheDocument();
      expect(screen.getByText(/customers/i)).toBeInTheDocument();
    });
  });
});
