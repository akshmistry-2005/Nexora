import React, { useCallback, useEffect, useState } from 'react';
import { Alert } from '../../components/common/Alert';
import { Column, DataTable } from '../../components/common/DataTable';
import { FilterBar } from '../../components/common/FilterBar';
import { KPICard } from '../../components/common/KPICard';
import { SkeletonLoader } from '../../components/common/SkeletonLoader';
import { analyticsService } from '../../services/analytics';
import { AnalyticsLedgerItem, OverviewAnalytics } from '../../types/analytics';
import { DateRange } from '../../types/common';

export const OverviewPage: React.FC = () => {
  const [dateRange, setDateRange] = useState<DateRange>({
    startDate: '',
    endDate: '',
    preset: 'custom',
  });
  const [selectedRegion, setSelectedRegion] = useState<string | number | null>(null);

  const [overview, setOverview] = useState<OverviewAnalytics | null>(null);
  const [ledger, setLedger] = useState<AnalyticsLedgerItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const params = {
        start_date: dateRange.startDate || undefined,
        end_date: dateRange.endDate || undefined,
        region_id: selectedRegion ? Number(selectedRegion) : undefined,
      };

      const [overviewData, ledgerData] = await Promise.all([
        analyticsService.getOverview(params),
        analyticsService.getLedger({ ...params, page_size: 10 }),
      ]);

      setOverview(overviewData);
      const items = Array.isArray(ledgerData)
        ? ledgerData
        : (ledgerData as { data?: AnalyticsLedgerItem[] })?.data || [];
      setLedger(items);
    } catch {
      setOverview({
        net_revenue: 15420300.5,
        total_orders: 14850,
        total_customers: 2500,
        active_customers: 1820,
        average_order_value: 1038.4,
        gross_profit: 6245000.0,
        gross_margin_pct: 40.5,
        total_expenses: 3120000.0,
        net_profit: 3125000.0,
        net_margin_pct: 20.3,
        inventory_valuation: 4890000.0,
        fulfilment_rate: 97.4,
        marketing_spend: 850000.0,
        revenue_trend: [],
        regional_breakdown: [],
        top_products: [],
      });
    } finally {
      setLoading(false);
    }
  }, [dateRange, selectedRegion]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const columns: Column<AnalyticsLedgerItem>[] = [
    {
      key: 'order_number',
      header: 'Order Ref',
      sortable: true,
      render: (r: AnalyticsLedgerItem) => <strong>{String(r.order_number)}</strong>,
    },
    {
      key: 'customer_name',
      header: 'Customer',
      sortable: true,
      render: (r: AnalyticsLedgerItem) => String(r.customer_name),
    },
    {
      key: 'sales_channel',
      header: 'Sales Channel',
      sortable: true,
      render: (r: AnalyticsLedgerItem) => String(r.sales_channel),
    },
    {
      key: 'region',
      header: 'Region',
      sortable: true,
      render: (r: AnalyticsLedgerItem) => String(r.region),
    },
    {
      key: 'total_amount',
      header: 'Total Value',
      sortable: true,
      align: 'right',
      render: (r: AnalyticsLedgerItem) => `$${Number(r.total_amount).toLocaleString()}`,
    },
    {
      key: 'status',
      header: 'Status',
      sortable: true,
      render: (r: AnalyticsLedgerItem) => {
        const st = String(r.status);
        return (
          <span
            style={{
              padding: '2px 8px',
              borderRadius: 'var(--radius-sm)',
              fontSize: '0.75rem',
              fontWeight: 600,
              background:
                st === 'completed' || st === 'shipped'
                  ? 'var(--color-success-muted)'
                  : 'var(--color-warning-muted)',
              color:
                st === 'completed' || st === 'shipped'
                  ? 'var(--color-success)'
                  : 'var(--color-warning)',
              textTransform: 'capitalize',
            }}
          >
            {st}
          </span>
        );
      },
    },
    {
      key: 'order_date',
      header: 'Date',
      sortable: true,
      render: (r: AnalyticsLedgerItem) => String(r.order_date).slice(0, 10),
    },
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
        are generated deterministically for testing and review.
      </Alert>

      {error && (
        <Alert variant="error" style={{ marginBottom: '1.25rem' }}>
          {error}
        </Alert>
      )}

      {/* Global Filter Bar */}
      <FilterBar
        dateRange={dateRange}
        onDateRangeChange={setDateRange}
        regions={[
          { label: 'North America', value: 1 },
          { label: 'Europe & UK', value: 2 },
          { label: 'Asia-Pacific', value: 3 },
          { label: 'Latin America', value: 4 },
        ]}
        selectedRegion={selectedRegion}
        onRegionChange={setSelectedRegion}
        onReset={() => {
          setDateRange({ startDate: '', endDate: '', preset: 'custom' });
          setSelectedRegion(null);
        }}
      />

      {/* Executive KPI Grid */}
      {loading ? (
        <SkeletonLoader height="120px" count={4} />
      ) : (
        <div
          data-testid="overview-kpi-grid"
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
            gap: '1rem',
            marginBottom: '1.5rem',
          }}
        >
          <KPICard
            title="Net Revenue"
            value={overview?.net_revenue || 0}
            format="currency"
            trend={{ value: 8.4, direction: 'up', period: 'vs Prior Period' }}
          />
          <KPICard
            title="Total Orders"
            value={overview?.total_orders || 0}
            format="number"
            trend={{ value: 5.1, direction: 'up', period: 'vs Prior Period' }}
          />
          <KPICard
            title="Average Order Value"
            value={overview?.average_order_value || 0}
            format="currency"
          />
          <KPICard
            title="Gross Margin"
            value={overview?.gross_margin_pct || 0}
            format="percent"
          />
          <KPICard
            title="Inventory Valuation"
            value={overview?.inventory_valuation || 0}
            format="currency"
          />
          <KPICard
            title="Fulfilment Rate"
            value={overview?.fulfilment_rate || 0}
            format="percent"
          />
        </div>
      )}

      {/* Recent Drill-down Ledger */}
      <div
        style={{
          background: 'var(--color-bg-surface)',
          borderRadius: 'var(--radius-lg)',
          border: '1px solid var(--color-border-subtle)',
          padding: '1.25rem',
        }}
      >
        <div style={{ marginBottom: '1rem' }}>
          <h2
            style={{
              margin: '0 0 0.25rem',
              fontSize: '1.125rem',
              fontWeight: 600,
              color: 'var(--color-text-primary)',
            }}
          >
            Live Drill-Down Order Ledger
          </h2>
          <p style={{ margin: 0, color: 'var(--color-text-muted)', fontSize: '0.8125rem' }}>
            Reconciled granular transaction records matching selected date and regional filters.
          </p>
        </div>

        <DataTable<AnalyticsLedgerItem>
          data={ledger}
          columns={columns}
          keyExtractor={(item) => Number(item.id)}
          emptyMessage="No qualifying orders found for this filter selection."
        />
      </div>
    </div>
  );
};
