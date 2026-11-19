import React from 'react';
import { KPICard } from '../../components/common/KPICard';

export const DataQualityPage: React.FC = () => {
  return (
    <div data-testid="data-quality-page">
      <div style={{ marginBottom: '1.25rem' }}>
        <h1
          style={{ margin: '0 0 0.25rem', fontSize: '1.625rem', fontWeight: 700, color: '#ffffff' }}
        >
          Data Quality Engine & Validation Rules
        </h1>
        <p style={{ margin: 0, color: 'var(--color-text-muted)', fontSize: '0.875rem' }}>
          Five-dimensional data quality scoring: completeness, validity, uniqueness, consistency,
          and timeliness.
        </p>
      </div>

      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
          gap: '1rem',
        }}
      >
        <KPICard
          title="Overall Quality Score"
          value={98.8}
          format="percent"
          trend={{ value: 0.4, direction: 'up', period: 'Clean pipeline' }}
        />
        <KPICard title="Completeness" value={99.4} format="percent" subtitle="Zero null PK/FKs" />
        <KPICard title="Uniqueness" value={100} format="percent" subtitle="Zero duplicate orders" />
        <KPICard
          title="Validity"
          value={98.2}
          format="percent"
          subtitle="Positive amounts & prices"
        />
      </div>
    </div>
  );
};
