import React from 'react';
import { KPICard } from '../../components/common/KPICard';

export const OperationsPage: React.FC = () => {
  return (
    <div data-testid="operations-page">
      <div style={{ marginBottom: '1.25rem' }}>
        <h1
          style={{ margin: '0 0 0.25rem', fontSize: '1.625rem', fontWeight: 700, color: '#ffffff' }}
        >
          Operations & Order Fulfillment
        </h1>
        <p style={{ margin: 0, color: 'var(--color-text-muted)', fontSize: '0.875rem' }}>
          Order lifecycle duration, shipping carrier performance, delivery SLA, and returns volume.
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
          title="Average Fulfillment Time"
          value={1.8}
          format="raw"
          subtitle="1.8 days from order to ship"
          trend={{ value: 0.3, direction: 'down', isPositive: true }}
        />
        <KPICard
          title="On-Time Delivery SLA"
          value={97.4}
          format="percent"
          trend={{ value: 1.2, direction: 'up', period: 'vs benchmark 95%' }}
        />
        <KPICard
          title="Return Rate"
          value={3.7}
          format="percent"
          trend={{ value: 0.2, direction: 'down', isPositive: true, period: '566 total returns' }}
        />
        <KPICard
          title="Fulfillment Accuracy"
          value={99.3}
          format="percent"
          trend={{ value: 0.1, direction: 'up', period: 'clean orders' }}
        />
      </div>
    </div>
  );
};
