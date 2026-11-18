import { useEffect, useState } from 'react';

export interface HealthState {
  status: string;
  service: string;
  version: string;
  environment: string;
  database: string;
  timestamp: string;
}

export function App() {
  const [health, setHealth] = useState<HealthState | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';

  useEffect(() => {
    fetch(`${apiBaseUrl}/api/v1/health`)
      .then(async (res) => {
        if (!res.ok) {
          throw new Error(`Backend returned HTTP ${res.status}`);
        }
        return res.json();
      })
      .then((data: HealthState) => {
        setHealth(data);
        setLoading(false);
      })
      .catch((err: Error) => {
        setError(err.message);
        setLoading(false);
      });
  }, [apiBaseUrl]);

  return (
    <main
      style={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '2rem',
      }}
    >
      <div
        style={{
          maxWidth: '640px',
          width: '100%',
          background: '#1e293b',
          borderRadius: '12px',
          padding: '2rem',
          border: '1px solid #334155',
          boxShadow: '0 10px 25px -5px rgba(0, 0, 0, 0.3)',
        }}
      >
        <header style={{ marginBottom: '1.5rem' }}>
          <span
            style={{
              fontSize: '0.75rem',
              letterSpacing: '0.08em',
              textTransform: 'uppercase',
              color: '#38bdf8',
              fontWeight: 700,
            }}
          >
            Module 2 • Environment & Foundation
          </span>
          <h1 style={{ fontSize: '1.75rem', margin: '0.25rem 0 0.5rem', color: '#ffffff' }}>
            Nexora Intelligence Platform
          </h1>
          <p style={{ margin: 0, color: '#94a3b8', fontSize: '0.875rem' }}>
            React + TypeScript frontend connected to FastAPI backend & PostgreSQL.
          </p>
        </header>

        <section style={{ borderTop: '1px solid #334155', paddingTop: '1.5rem' }}>
          <h2 style={{ fontSize: '1rem', color: '#cbd5e1', margin: '0 0 1rem' }}>
            System Connectivity Status
          </h2>

          {loading && (
            <p data-testid="status-loading" style={{ color: '#cbd5e1' }}>
              Checking backend connectivity...
            </p>
          )}

          {error && (
            <div
              data-testid="status-error"
              style={{
                padding: '0.75rem 1rem',
                borderRadius: '8px',
                background: '#451a1a',
                color: '#fca5a5',
                border: '1px solid #7f1d1d',
                fontSize: '0.875rem',
              }}
            >
              <strong>Backend connection error:</strong> {error}
            </div>
          )}

          {health && (
            <div data-testid="status-healthy">
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem',
                  marginBottom: '1rem',
                }}
              >
                <span
                  style={{
                    display: 'inline-block',
                    width: '10px',
                    height: '10px',
                    borderRadius: '50%',
                    background: health.status === 'healthy' ? '#22c55e' : '#f59e0b',
                  }}
                />
                <strong style={{ color: '#ffffff' }}>
                  Backend Status: {health.status.toUpperCase()}
                </strong>
              </div>

              <dl
                style={{
                  display: 'grid',
                  gridTemplateColumns: '140px 1fr',
                  gap: '0.5rem 1rem',
                  fontSize: '0.875rem',
                  margin: 0,
                }}
              >
                <dt style={{ color: '#94a3b8' }}>Service:</dt>
                <dd style={{ color: '#f8fafc', margin: 0 }}>{health.service}</dd>
                <dt style={{ color: '#94a3b8' }}>Version:</dt>
                <dd style={{ color: '#f8fafc', margin: 0 }}>{health.version}</dd>
                <dt style={{ color: '#94a3b8' }}>Database:</dt>
                <dd
                  data-testid="db-status"
                  style={{
                    color: health.database === 'connected' ? '#4ade80' : '#f87171',
                    margin: 0,
                    fontWeight: 600,
                  }}
                >
                  {health.database}
                </dd>
                <dt style={{ color: '#94a3b8' }}>Environment:</dt>
                <dd style={{ color: '#f8fafc', margin: 0 }}>{health.environment}</dd>
                <dt style={{ color: '#94a3b8' }}>Timestamp:</dt>
                <dd style={{ color: '#94a3b8', margin: 0, fontSize: '0.75rem' }}>
                  {health.timestamp}
                </dd>
              </dl>
            </div>
          )}
        </section>
      </div>
    </main>
  );
}
