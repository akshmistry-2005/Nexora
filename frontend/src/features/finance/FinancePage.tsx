import React from 'react';
import { KPICard } from '../../components/common/KPICard';

export const FinancePage: React.FC = () => {
  return (
    <div data-testid="finance-page">
      <div style={{ marginBottom: '1.25rem' }}>
        <h1
          style={{ margin: '0 0 0.25rem', fontSize: '1.625rem', fontWeight: 700, color: '#ffffff' }}
        >
          Financial Performance & Profitability
        </h1>
        <p style={{ margin: 0, color: 'var(--color-text-muted)', fontSize: '0.875rem' }}>
          Operating expenses, budget variance, EBITDA, and cash collection cycles.
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
          title="Operating Expenses (OpEx)"
          value={1250000}
          format="currency"
          trend={{ value: 2.3, direction: 'down', isPositive: true, period: 'vs budget' }}
        />
        <KPICard
          title="Net Operating Margin"
          value={28.4}
          format="percent"
          trend={{ value: 1.8, direction: 'up', period: 'vs target 25%' }}
        />
        <KPICard
          title="Budget Utilization"
          value={91.2}
          format="percent"
          trend={{ value: 0.5, direction: 'neutral', period: '144 cost centers' }}
        />
        <KPICard
          title="DSO (Days Sales Outstanding)"
          value={34}
          format="raw"
          subtitle="34 days average collection"
          trend={{ value: 3, direction: 'down', isPositive: true }}
        />
      </div>
    </div>
  );
};
