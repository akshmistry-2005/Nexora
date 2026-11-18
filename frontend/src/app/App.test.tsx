import { render, screen, waitFor } from '@testing-library/react';
import { describe, expect, it, vi, beforeEach } from 'vitest';
import { App } from './App';

describe('M2-T08: Frontend-Backend Connectivity Component', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('renders loading indicator initially', () => {
    vi.spyOn(globalThis, 'fetch').mockImplementation(() => new Promise(() => {}));
    render(<App />);
    expect(screen.getByTestId('status-loading')).toBeInTheDocument();
  });

  it('displays backend healthy status when fetch succeeds', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        status: 'healthy',
        service: 'Nexora Enterprise Data Intelligence Platform',
        version: '0.2.0',
        environment: 'development',
        database: 'connected',
        timestamp: '2026-11-18T18:00:00Z',
      }),
    } as Response);

    render(<App />);

    await waitFor(() => {
      expect(screen.getByTestId('status-healthy')).toBeInTheDocument();
    });

    expect(screen.getByText(/Backend Status: HEALTHY/i)).toBeInTheDocument();
    expect(screen.getByTestId('db-status')).toHaveTextContent('connected');
  });

  it('displays error state when backend fetch fails', async () => {
    vi.spyOn(globalThis, 'fetch').mockRejectedValueOnce(new Error('Failed to fetch'));

    render(<App />);

    await waitFor(() => {
      expect(screen.getByTestId('status-error')).toBeInTheDocument();
    });

    expect(screen.getByText(/Failed to fetch/i)).toBeInTheDocument();
  });
});
