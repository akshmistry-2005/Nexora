import React, { useState } from 'react';
import { Column, DataTable } from '../../components/common/DataTable';
import { FilterBar } from '../../components/common/FilterBar';
import { KPICard } from '../../components/common/KPICard';
import { DateRange } from '../../types/common';

interface CustomerItem {
  id: number;
  code: string;
  name: string;
  type: string;
  region: string;
  totalSpend: number;
  ordersCount: number;
  status: string;
}

const SAMPLE_CUSTOMERS: CustomerItem[] = [
  {
    id: 1,
    code: 'CUST-00001',
    name: 'Apex Logistics LLC',
    type: 'Enterprise',
    region: 'North America',
    totalSpend: 184500,
    ordersCount: 24,
    status: 'Active',
  },
  {
    id: 2,
    code: 'CUST-00002',
    name: 'Beacon Cloud Systems',
    type: 'B2B',
    region: 'Europe',
    totalSpend: 92300,
    ordersCount: 15,
    status: 'Active',
  },
  {
    id: 3,
    code: 'CUST-00003',
    name: 'Cascade Retail Partners',
    type: 'Enterprise',
    region: 'North America',
    totalSpend: 312000,
    ordersCount: 42,
    status: 'Active',
  },
  {
    id: 4,
    code: 'CUST-00004',
    name: 'Delta Dynamics Corp',
    type: 'Enterprise',
    region: 'Asia-Pacific',
    totalSpend: 421000,
    ordersCount: 56,
    status: 'Active',
  },
  {
    id: 5,
    code: 'CUST-00005',
    name: 'Echo Industrial Tech',
    type: 'B2B',
    region: 'Europe',
    totalSpend: 67400,
    ordersCount: 11,
    status: 'Active',
  },
];

export const CustomersPage: React.FC = () => {
  const [dateRange, setDateRange] = useState<DateRange>({
    startDate: '2026-01-01',
    endDate: '2026-11-18',
    preset: 'ytd',
  });

  const columns: Column<CustomerItem>[] = [
    { key: 'code', header: 'Customer Code', sortable: true },
    { key: 'name', header: 'Company Name', sortable: true },
    { key: 'type', header: 'Segment', sortable: true },
    { key: 'region', header: 'Territory', sortable: true },
    {
      key: 'totalSpend',
      header: 'Lifetime Spend',
      sortable: true,
      align: 'right',
      render: (r) => `$${r.totalSpend.toLocaleString()}`,
    },
    { key: 'ordersCount', header: 'Total Orders', sortable: true, align: 'right' },
    {
      key: 'status',
      header: 'Account Status',
      sortable: true,
      render: (r) => (
        <span
          style={{
            padding: '2px 8px',
            borderRadius: 'var(--radius-sm)',
            fontSize: '0.75rem',
            fontWeight: 600,
            background: 'var(--color-success-muted)',
            color: 'var(--color-success)',
          }}
        >
          {r.status}
        </span>
      ),
    },
  ];

  return (
    <div data-testid="customers-page">
      <div style={{ marginBottom: '1.25rem' }}>
        <h1
          style={{ margin: '0 0 0.25rem', fontSize: '1.625rem', fontWeight: 700, color: '#ffffff' }}
        >
          Customer Intelligence & Accounts
        </h1>
        <p style={{ margin: 0, color: 'var(--color-text-muted)', fontSize: '0.875rem' }}>
          Customer lifetime value, acquisition channels, regional distribution, and retention
          metrics.
        </p>
      </div>

      <FilterBar dateRange={dateRange} onDateRangeChange={setDateRange} />

      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
          gap: '1rem',
          marginBottom: '1.5rem',
        }}
      >
        <KPICard
          title="Total Customer Base"
          value={2500}
          format="number"
          trend={{ value: 6.4, direction: 'up', period: 'vs last year' }}
        />
        <KPICard
          title="Average LTV"
          value={1420}
          format="currency"
          trend={{ value: 3.2, direction: 'up', period: 'vs target' }}
        />
        <KPICard
          title="Retention Rate"
          value={89.2}
          format="percent"
          trend={{ value: 1.1, direction: 'up', period: '90-day active' }}
        />
        <KPICard
          title="Predicted Churn Risk"
          value={4.8}
          format="percent"
          trend={{ value: 0.8, direction: 'down', isPositive: true, period: 'ML low risk' }}
        />
      </div>

      <DataTable
        data={SAMPLE_CUSTOMERS as unknown as Record<string, unknown>[]}
        columns={columns as unknown as Column<Record<string, unknown>>[]}
        keyExtractor={(r) => (r as unknown as CustomerItem).id}
        enableSearch
        searchPlaceholder="Filter customers by code, name, or region..."
      />
    </div>
  );
};
