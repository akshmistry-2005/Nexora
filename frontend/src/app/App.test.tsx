import { render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { App } from './App';

describe('App Root & Foundation Rendering', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    localStorage.clear();
  });

  it('renders application shell with sidebar, topbar, and overview page', async () => {
    vi.spyOn(globalThis, 'fetch').mockImplementation(async (input) => {
      const url = String(input);
      if (url.includes('/api/v1/auth/demo-login')) {
        return {
          ok: true,
          headers: new Headers({ 'content-type': 'application/json' }),
          json: async () => ({
            success: true,
            data: {
              access_token: 'fake-jwt-token',
              token_type: 'Bearer',
              expires_in_seconds: 7200,
              user_id: 2,
              email: 'demo_executive@nexora.local',
              full_name: 'Elena Vance (CEO)',
              role: 'executive',
              permissions: ['dashboard.view', 'sales.view', 'customer.view'],
            },
          }),
        } as Response;
      }
      if (url.includes('/api/v1/health')) {
        return {
          ok: true,
          headers: new Headers({ 'content-type': 'application/json' }),
          json: async () => ({
            status: 'healthy',
            service: 'Nexora Enterprise Data Intelligence Platform',
            version: '0.2.0',
            environment: 'development',
            database: 'connected',
            timestamp: '2026-11-19T10:00:00Z',
          }),
        } as Response;
      }
      return {
        ok: true,
        headers: new Headers({ 'content-type': 'application/json' }),
        json: async () => ({ success: true, data: {} }),
      } as Response;
    });

    render(<App />);

    // Verify Shell elements
    expect(screen.getByTestId('app-shell')).toBeInTheDocument();
    expect(screen.getByTestId('app-sidebar')).toBeInTheDocument();
    expect(screen.getByTestId('app-topbar')).toBeInTheDocument();
    expect(screen.getByTestId('main-content')).toBeInTheDocument();

    // Verify Overview content
    expect(screen.getByTestId('overview-page')).toBeInTheDocument();

    // Verify active demo role badge
    await waitFor(() => {
      expect(screen.getByTestId('active-role-label')).toHaveTextContent(/Executive/i);
    });

    // Verify backend health indicator
    await waitFor(() => {
      expect(screen.getByTestId('backend-health-pill')).toHaveTextContent(/API Active/i);
    });
  });
});
