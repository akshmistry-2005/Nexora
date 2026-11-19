import React from 'react';
import { KPICard } from '../../components/common/KPICard';

export const InventoryPage: React.FC = () => {
  return (
    <div data-testid="inventory-page">
      <div style={{ marginBottom: '1.25rem' }}>
        <h1
          style={{ margin: '0 0 0.25rem', fontSize: '1.625rem', fontWeight: 700, color: '#ffffff' }}
        >
          Inventory Health & Warehouse Logistics
        </h1>
        <p style={{ margin: 0, color: 'var(--color-text-muted)', fontSize: '0.875rem' }}>
          Stock levels across 4 regional warehouses, safety thresholds, and stockout risk models.
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
          title="Total Inventory Value"
          value={1890000}
          format="currency"
          trend={{ value: 4.2, direction: 'up', period: '480 inventory SKUs' }}
        />
        <KPICard
          title="Stockout Risk Alerts"
          value={3}
          format="number"
          trend={{ value: 2, direction: 'down', isPositive: true, period: 'below reorder point' }}
        />
        <KPICard
          title="Inventory Turnover Ratio"
          value={6.8}
          format="raw"
          subtitle="6.8x annual turns"
          trend={{ value: 0.4, direction: 'up', isPositive: true }}
        />
        <KPICard
          title="Fill Rate"
          value={98.6}
          format="percent"
          trend={{ value: 0.3, direction: 'up', period: 'on-time fulfillment' }}
        />
      </div>
    </div>
  );
};
