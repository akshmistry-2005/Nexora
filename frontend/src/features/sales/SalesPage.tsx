import React from 'react';
import { KPICard } from '../../components/common/KPICard';

export const SalesPage: React.FC = () => {
  return (
    <div data-testid="sales-page">
      <div style={{ marginBottom: '1.25rem' }}>
        <h1
          style={{ margin: '0 0 0.25rem', fontSize: '1.625rem', fontWeight: 700, color: '#ffffff' }}
        >
          Sales Intelligence & Revenue Analytics
        </h1>
        <p style={{ margin: 0, color: 'var(--color-text-muted)', fontSize: '0.875rem' }}>
          Territory breakdowns, product sales velocity, representative quotas, and margin analysis.
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
          title="Gross Sales"
          value={3920000}
          format="currency"
          trend={{ value: 12.1, direction: 'up', period: 'vs last month' }}
        />
        <KPICard
          title="Average Order Value"
          value={232}
          format="currency"
          trend={{ value: 4.5, direction: 'up', period: 'vs Q3' }}
        />
        <KPICard
          title="Discount Rate"
          value={4.2}
          format="percent"
          trend={{ value: 0.3, direction: 'down', isPositive: true, period: 'vs target 5%' }}
        />
        <KPICard
          title="Total Units Sold"
          value={28836}
          format="number"
          trend={{ value: 7.9, direction: 'up', period: '120 products' }}
        />
      </div>
    </div>
  );
};
