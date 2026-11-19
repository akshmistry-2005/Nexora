import React from 'react';
import { Column, DataTable } from '../../components/common/DataTable';
import { KPICard } from '../../components/common/KPICard';

interface AnomalyRow {
  id: string;
  metric: string;
  deviation: string;
  severity: string;
  detectedAt: string;
  status: string;
}

const SAMPLE_ANOMALIES: AnomalyRow[] = [
  {
    id: '1',
    metric: 'Daily Sales Surge',
    deviation: '+3.4σ above 30-day baseline',
    severity: 'High',
    detectedAt: '2026-11-17',
    status: 'Unacknowledged',
  },
  {
    id: '2',
    metric: 'Marketing Spend Spike',
    deviation: '+2.8σ in Paid Search flight',
    severity: 'Medium',
    detectedAt: '2026-11-15',
    status: 'Investigating',
  },
  {
    id: '3',
    metric: 'Stockout Velocity Alert',
    deviation: 'Inventory depletion 4x normal rate',
    severity: 'Critical',
    detectedAt: '2026-11-14',
    status: 'Acknowledged',
  },
];

export const AnomaliesPage: React.FC = () => {
  const columns: Column<AnomalyRow>[] = [
    { key: 'metric', header: 'Anomaly Metric', sortable: true },
    { key: 'deviation', header: 'Statistical Deviation', sortable: true },
    {
      key: 'severity',
      header: 'Severity',
      sortable: true,
      render: (r) => (
        <span
          style={{
            padding: '2px 8px',
            borderRadius: 'var(--radius-sm)',
            fontSize: '0.75rem',
            fontWeight: 600,
            background:
              r.severity === 'Critical'
                ? 'var(--color-danger-muted)'
                : r.severity === 'High'
                  ? 'var(--color-warning-muted)'
                  : 'var(--color-primary-muted)',
            color:
              r.severity === 'Critical'
                ? 'var(--color-danger)'
                : r.severity === 'High'
                  ? 'var(--color-warning)'
                  : 'var(--color-primary)',
          }}
        >
          {r.severity}
        </span>
      ),
    },
    { key: 'detectedAt', header: 'Detected At', sortable: true },
    { key: 'status', header: 'Workflow Status', sortable: true },
  ];

  return (
    <div data-testid="anomalies-page">
      <div style={{ marginBottom: '1.25rem' }}>
        <h1
          style={{ margin: '0 0 0.25rem', fontSize: '1.625rem', fontWeight: 700, color: '#ffffff' }}
        >
          Anomaly Detection & Risk Intelligence
        </h1>
        <p style={{ margin: 0, color: 'var(--color-text-muted)', fontSize: '0.875rem' }}>
          Automated multi-sigma statistical outliers, risk alerts, and operational investigations.
        </p>
      </div>

      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
          gap: '1rem',
          marginBottom: '1.5rem',
        }}
      >
        <KPICard
          title="Active Anomaly Alerts"
          value={3}
          format="number"
          trend={{ value: 1, direction: 'down', isPositive: true, period: '1 unacknowledged' }}
        />
        <KPICard
          title="Critical Severities"
          value={1}
          format="number"
          subtitle="Stockout risk alert"
        />
        <KPICard
          title="Z-Score Baseline Window"
          value={30}
          format="raw"
          subtitle="30-day moving window"
        />
        <KPICard
          title="False Positive Rate"
          value={2.1}
          format="percent"
          subtitle="Controlled via 2.5σ filter"
        />
      </div>

      <DataTable
        data={SAMPLE_ANOMALIES as unknown as Record<string, unknown>[]}
        columns={columns as unknown as Column<Record<string, unknown>>[]}
        keyExtractor={(r) => (r as unknown as AnomalyRow).id}
        enableSearch
        searchPlaceholder="Search anomaly alerts..."
      />
    </div>
  );
};
