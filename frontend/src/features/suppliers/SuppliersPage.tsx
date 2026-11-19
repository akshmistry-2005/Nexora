import React from 'react';
import { KPICard } from '../../components/common/KPICard';

export const SuppliersPage: React.FC = () => {
  return (
    <div data-testid="suppliers-page">
      <div style={{ marginBottom: '1.25rem' }}>
        <h1
          style={{ margin: '0 0 0.25rem', fontSize: '1.625rem', fontWeight: 700, color: '#ffffff' }}
        >
          Supplier Intelligence & Procurement
        </h1>
        <p style={{ margin: 0, color: 'var(--color-text-muted)', fontSize: '0.875rem' }}>
          Purchase orders, vendor lead time variance, defect rates, and supplier concentration risk.
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
          title="Active Suppliers"
          value={25}
          format="number"
          trend={{ value: 2, direction: 'up', period: '25 vetted vendors' }}
        />
        <KPICard
          title="Total PO Volume"
          value={1200}
          format="number"
          trend={{ value: 9.4, direction: 'up', period: 'all purchase orders' }}
        />
        <KPICard
          title="Avg Supplier Lead Time"
          value={8.4}
          format="raw"
          subtitle="8.4 days from PO to receipt"
          trend={{ value: 0.6, direction: 'down', isPositive: true }}
        />
        <KPICard
          title="Supplier Defect Rate"
          value={0.8}
          format="percent"
          trend={{ value: 0.2, direction: 'down', isPositive: true, period: 'quality compliant' }}
        />
      </div>
    </div>
  );
};
