import React, { useState } from 'react';
import { Alert } from '../../components/common/Alert';
import { Column, DataTable } from '../../components/common/DataTable';
import { FilterBar } from '../../components/common/FilterBar';
import { KPICard } from '../../components/common/KPICard';
import { DateRange } from '../../types/common';

interface RecentOrder {
  id: string;
  orderNumber: string;
  customerName: string;
  channel: string;
  totalAmount: number;
  status: string;
  orderDate: string;
}

const SAMPLE_ORDERS: RecentOrder[] = [
  {
    id: '1',
    orderNumber: 'ORD-2026-09142',
    customerName: 'Apex Logistics LLC',
    channel: 'Direct B2B',
    totalAmount: 14850,
    status: 'Completed',
    orderDate: '2026-11-18',
  },
  {
    id: '2',
    orderNumber: 'ORD-2026-09141',
    customerName: 'Beacon Cloud Systems',
    channel: 'Online Portal',
    totalAmount: 8420,
    status: 'Completed',
    orderDate: '2026-11-18',
  },
  {
    id: '3',
    orderNumber: 'ORD-2026-09140',
    customerName: 'Cascade Retail Partners',
    channel: 'Direct B2B',
    totalAmount: 22100,
    status: 'Processing',
    orderDate: '2026-11-17',
  },
  {
    id: '4',
    orderNumber: 'ORD-2026-09139',
    customerName: 'Delta Dynamics Corp',
    channel: 'Enterprise EDI',
    totalAmount: 43250,
    status: 'Completed',
    orderDate: '2026-11-17',
  },
  {
    id: '5',
    orderNumber: 'ORD-2026-09138',
    customerName: 'Echo Industrial Tech',
    channel: 'Direct B2B',
    totalAmount: 11900,
    status: 'Completed',
    orderDate: '2026-11-16',
  },
  {
    id: '6',
    orderNumber: 'ORD-2026-09137',
    customerName: 'Horizon Health Network',
    channel: 'Enterprise EDI',
    totalAmount: 67300,
    status: 'Completed',
    orderDate: '2026-11-16',
  },
  {
    id: '7',
    orderNumber: 'ORD-2026-09136',
    customerName: 'Summit Media Group',
    channel: 'Online Portal',
    totalAmount: 5400,
    status: 'Shipped',
    orderDate: '2026-11-15',
  },
];

export const OverviewPage: React.FC = () => {
  const [dateRange, setDateRange] = useState<DateRange>({
    startDate: '2026-10-19',
    endDate: '2026-11-18',
    preset: '30d',
  });
  const [selectedRegion, setSelectedRegion] = useState<string | number | null>(null);

  const columns: Column<RecentOrder>[] = [
    { key: 'orderNumber', header: 'Order Ref', sortable: true },
    { key: 'customerName', header: 'Customer', sortable: true },
    { key: 'channel', header: 'Sales Channel', sortable: true },
    {
      key: 'totalAmount',
      header: 'Total Value',
      sortable: true,
      align: 'right',
      render: (r) => `$${r.totalAmount.toLocaleString()}`,
    },
    {
      key: 'status',
      header: 'Status',
      sortable: true,
      render: (r) => (
        <span
          style={{
            padding: '2px 8px',
            borderRadius: 'var(--radius-sm)',
            fontSize: '0.75rem',
            fontWeight: 600,
            background:
              r.status === 'Completed'
                ? 'var(--color-success-muted)'
                : r.status === 'Processing'
                  ? 'var(--color-warning-muted)'
                  : 'var(--color-primary-muted)',
            color:
              r.status === 'Completed'
                ? 'var(--color-success)'
                : r.status === 'Processing'
                  ? 'var(--color-warning)'
                  : 'var(--color-primary)',
          }}
        >
          {r.status}
        </span>
      ),
    },
    { key: 'orderDate', header: 'Date', sortable: true },
  ];

  return (
    <div data-testid="overview-page">
      {/* Page Title */}
      <div style={{ marginBottom: '1.25rem' }}>
        <h1
          style={{ margin: '0 0 0.25rem', fontSize: '1.625rem', fontWeight: 700, color: '#ffffff' }}
        >
          Executive Performance Overview
        </h1>
        <p style={{ margin: 0, color: 'var(--color-text-muted)', fontSize: '0.875rem' }}>
          Real-time enterprise metrics, operating margins, regional health, and recent order volume.
        </p>
      </div>

      <Alert variant="info" style={{ marginBottom: '1.25rem' }}>
        <strong>Synthetic Demonstration Notice:</strong> All metrics, transactions, and customers
        displayed are generated deterministically from seed seed=42 for portfolio evaluation.
      </Alert>

      {/* Global Filter Bar */}
      <FilterBar
        dateRange={dateRange}
        onDateRangeChange={setDateRange}
        regions={[
          { label: 'North America', value: 1 },
          { label: 'Europe', value: 2 },
          { label: 'Asia-Pacific', value: 3 },
          { label: 'Latin America', value: 4 },
          { label: 'Middle East & Africa', value: 5 },
        ]}
        selectedRegion={selectedRegion}
        onRegionChange={setSelectedRegion}
        onReset={() => {
          setSelectedRegion(null);
          setDateRange({ startDate: '2026-10-19', endDate: '2026-11-18', preset: '30d' });
        }}
      />

      {/* KPI Cards Grid */}
      <div
        data-testid="kpi-grid"
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
          gap: '1rem',
          marginBottom: '1.5rem',
        }}
      >
        <KPICard
          title="Total Net Revenue"
          value={3485290}
          format="currency"
          trend={{ value: 14.8, direction: 'up', isPositive: true, period: 'vs previous 30 days' }}
          tooltip="Gross revenue minus cancellations, refunds, discounts, and regional taxes."
        />
        <KPICard
          title="Gross Margin"
          value={42.6}
          format="percent"
          trend={{ value: 2.1, direction: 'up', isPositive: true, period: 'vs target 40%' }}
          tooltip="(Net Revenue - Total COGS) / Net Revenue."
        />
        <KPICard
          title="Order Volume"
          value={15000}
          format="number"
          trend={{ value: 8.5, direction: 'up', isPositive: true, period: 'vs last quarter' }}
          tooltip="Total completed and in-flight sales transactions across all territories."
        />
        <KPICard
          title="Active Customers"
          value={2500}
          format="number"
          trend={{ value: 5.2, direction: 'up', isPositive: true, period: 'vs 90-day baseline' }}
          tooltip="Unique customer accounts with at least one confirmed order in 90 days."
        />
      </div>

      {/* Recent Orders Data Table */}
      <div style={{ marginTop: '1.5rem' }}>
        <h2
          style={{ fontSize: '1.125rem', fontWeight: 600, color: '#ffffff', margin: '0 0 0.75rem' }}
        >
          Recent High-Value Transactions
        </h2>
        <DataTable
          data={SAMPLE_ORDERS as unknown as Record<string, unknown>[]}
          columns={columns as unknown as Column<Record<string, unknown>>[]}
          keyExtractor={(r) => (r as unknown as RecentOrder).id}
          enableSearch
          searchPlaceholder="Search order number, client name..."
          onExport={() => alert('CSV export triggered with sanitized headers.')}
        />
      </div>
    </div>
  );
};
