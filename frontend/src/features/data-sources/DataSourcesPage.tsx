import React from 'react';
import { Alert } from '../../components/common/Alert';
import { KPICard } from '../../components/common/KPICard';
import { useAuth } from '../../hooks/useAuth';

export const DataSourcesPage: React.FC = () => {
  const { isOwner } = useAuth();

  return (
    <div data-testid="data-sources-page">
      <div style={{ marginBottom: '1.25rem' }}>
        <h1
          style={{ margin: '0 0 0.25rem', fontSize: '1.625rem', fontWeight: 700, color: '#ffffff' }}
        >
          Data Ingestion & Source Management
        </h1>
        <p style={{ margin: 0, color: 'var(--color-text-muted)', fontSize: '0.875rem' }}>
          Batch CSV uploads, schema mapping, transaction rollback safety, and upload history.
        </p>
      </div>

      {!isOwner && (
        <Alert variant="info" style={{ marginBottom: '1.25rem' }}>
          <strong>Read-Only Mode:</strong> File upload and dataset ingestion are restricted to the
          Platform Owner. Demonstration roles can inspect ingestion history and mapping templates.
        </Alert>
      )}

      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
          gap: '1rem',
        }}
      >
        <KPICard
          title="Total Ingested Datasets"
          value={7}
          format="number"
          subtitle="Transactional and Master"
        />
        <KPICard title="Max Upload Limit" value={10} format="raw" subtitle="10 MB max file size" />
        <KPICard
          title="Rollback Protection"
          value="ENABLED"
          subtitle="Atomic database transactions"
        />
        <KPICard title="Ingestion Status" value="HEALTHY" subtitle="PostgreSQL 16 pipeline" />
      </div>
    </div>
  );
};
