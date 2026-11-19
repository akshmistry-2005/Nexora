import React from 'react';
import { Alert } from '../../components/common/Alert';
import { KPICard } from '../../components/common/KPICard';

export const StatisticsPage: React.FC = () => {
  return (
    <div data-testid="statistics-page">
      <div style={{ marginBottom: '1.25rem' }}>
        <h1
          style={{ margin: '0 0 0.25rem', fontSize: '1.625rem', fontWeight: 700, color: '#ffffff' }}
        >
          Statistical Analysis & Distribution Modeling
        </h1>
        <p style={{ margin: 0, color: 'var(--color-text-muted)', fontSize: '0.875rem' }}>
          Parametric and non-parametric tests, variance distributions, quartile spreads, and
          correlation matrices.
        </p>
      </div>

      <Alert variant="warning" style={{ marginBottom: '1.25rem' }}>
        <strong>Statistical Assumption Notice:</strong> High correlation does not imply causation.
        Hypothesis test oracles enforce normality and sample size bounds.
      </Alert>

      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
          gap: '1rem',
        }}
      >
        <KPICard
          title="Mean Order Value"
          value={232.4}
          format="currency"
          subtitle="Std Dev: $48.2"
        />
        <KPICard title="Median Order Value" value={218.0} format="currency" subtitle="IQR: $64.0" />
        <KPICard
          title="Revenue Skewness"
          value={0.42}
          format="raw"
          subtitle="Moderate right skew"
        />
        <KPICard
          title="Statistically Tested Metrics"
          value={14}
          format="number"
          subtitle="p < 0.05 confidence"
        />
      </div>
    </div>
  );
};
