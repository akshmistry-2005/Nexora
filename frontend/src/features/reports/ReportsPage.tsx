import React from 'react';
import { Column, DataTable } from '../../components/common/DataTable';
import { KPICard } from '../../components/common/KPICard';
import { useAuth } from '../../hooks/useAuth';

interface ReportCatalogueItem {
  id: string;
  name: string;
  category: string;
  cadence: string;
  exportable: boolean;
  lastGenerated: string;
}

const CATALOGUE_REPORTS: ReportCatalogueItem[] = [
  {
    id: '1',
    name: 'Executive Financial Summary',
    category: 'Executive',
    cadence: 'Monthly',
    exportable: true,
    lastGenerated: '2026-11-01',
  },
  {
    id: '2',
    name: 'Regional Sales Territory Breakdown',
    category: 'Sales',
    cadence: 'Weekly',
    exportable: true,
    lastGenerated: '2026-11-18',
  },
  {
    id: '3',
    name: 'Customer Cohort & LTV Performance',
    category: 'Marketing',
    cadence: 'Monthly',
    exportable: true,
    lastGenerated: '2026-11-01',
  },
  {
    id: '4',
    name: 'Inventory Reorder & Lead Time Analysis',
    category: 'Operations',
    cadence: 'Weekly',
    exportable: true,
    lastGenerated: '2026-11-15',
  },
];

export const ReportsPage: React.FC = () => {
  const { hasPermission } = useAuth();
  const canExport = hasPermission('report.export');

  const columns: Column<ReportCatalogueItem>[] = [
    { key: 'name', header: 'Report Name', sortable: true },
    { key: 'category', header: 'Department', sortable: true },
    { key: 'cadence', header: 'Cadence', sortable: true },
    { key: 'lastGenerated', header: 'Last Generated', sortable: true },
    {
      key: 'exportable',
      header: 'Export Access',
      render: () => (
        <span
          style={{
            fontSize: '0.75rem',
            padding: '2px 8px',
            borderRadius: 'var(--radius-sm)',
            background: canExport ? 'var(--color-primary-muted)' : 'rgba(255, 255, 255, 0.05)',
            color: canExport ? 'var(--color-primary)' : 'var(--color-text-subtle)',
          }}
        >
          {canExport ? 'Export Permitted' : 'Export Restricted'}
        </span>
      ),
    },
  ];

  return (
    <div data-testid="reports-page">
      <div style={{ marginBottom: '1.25rem' }}>
        <h1
          style={{ margin: '0 0 0.25rem', fontSize: '1.625rem', fontWeight: 700, color: '#ffffff' }}
        >
          Standard Reports & Data Exports
        </h1>
        <p style={{ margin: 0, color: 'var(--color-text-muted)', fontSize: '0.875rem' }}>
          Curated enterprise reporting catalogue, saved views, and sanitized CSV exports.
        </p>
      </div>

      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
          gap: '1rem',
          marginBottom: '1.5rem',
        }}
      >
        <KPICard title="Standard Reports" value={4} format="number" subtitle="Curated catalogue" />
        <KPICard
          title="Max Export Limit"
          value={50000}
          format="number"
          subtitle="Rows per download"
        />
        <KPICard title="Formula Injection Guard" value="ACTIVE" subtitle="RFC 4180 sanitizer" />
        <KPICard
          title="Export Authorization"
          value={canExport ? 'GRANTED' : 'RESTRICTED'}
          subtitle={canExport ? 'Full CSV exports enabled' : 'General Viewer restricted'}
        />
      </div>

      <DataTable
        data={CATALOGUE_REPORTS as unknown as Record<string, unknown>[]}
        columns={columns as unknown as Column<Record<string, unknown>>[]}
        keyExtractor={(r) => (r as unknown as ReportCatalogueItem).id}
        enableSearch
        searchPlaceholder="Search report catalogue..."
      />
    </div>
  );
};
