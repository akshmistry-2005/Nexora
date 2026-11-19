import React, { useEffect, useState } from 'react';
import { Alert } from '../../components/common/Alert';
import { Column, DataTable } from '../../components/common/DataTable';
import { KPICard } from '../../components/common/KPICard';
import { Modal } from '../../components/common/Modal';
import { useAuth } from '../../hooks/useAuth';
import { reportsService } from '../../services/reports';
import { ReportCatalogueItem, ReportData, SavedView } from '../../types/reports';

export const ReportsPage: React.FC = () => {
  const { hasPermission } = useAuth();
  const canExport = hasPermission('report.export');

  const [activeTab, setActiveTab] = useState<'catalogue' | 'viewer' | 'saved_views'>('catalogue');
  const [catalogue, setCatalogue] = useState<ReportCatalogueItem[]>([]);
  const [selectedReportId, setSelectedReportId] = useState<string>('sales-performance');
  const [reportData, setReportData] = useState<ReportData | null>(null);
  const [savedViews, setSavedViews] = useState<SavedView[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [exporting, setExporting] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Save view modal state
  const [showSaveModal, setShowSaveModal] = useState<boolean>(false);
  const [viewName, setViewName] = useState<string>('');
  const [isShared, setIsShared] = useState<boolean>(false);
  const [saveSuccessMsg, setSaveSuccessMsg] = useState<string | null>(null);

  // Load catalogue and saved views on mount
  useEffect(() => {
    loadCatalogue();
    loadSavedViews();
  }, []);

  const loadCatalogue = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await reportsService.getCatalogue();
      const items = Array.isArray(res)
        ? res
        : (res && (res as unknown as { data: ReportCatalogueItem[] }).data) || [];
      setCatalogue(items);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load report catalogue.');
    } finally {
      setLoading(false);
    }
  };

  const loadSavedViews = async () => {
    try {
      const res = await reportsService.listSavedViews();
      const views = Array.isArray(res)
        ? res
        : (res && (res as unknown as { data: SavedView[] }).data) || [];
      setSavedViews(views);
    } catch {
      // Ignored for viewers without read access
    }
  };

  const handleOpenReport = async (reportId: string) => {
    setSelectedReportId(reportId);
    setActiveTab('viewer');
    try {
      setLoading(true);
      setError(null);
      const data = await reportsService.getReportData(reportId, { limit: 500 });
      setReportData(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : `Failed to load report '${reportId}'.`);
    } finally {
      setLoading(false);
    }
  };

  const handleExportCsv = async () => {
    if (!canExport || !selectedReportId) return;
    try {
      setExporting(true);
      await reportsService.downloadCsv(selectedReportId, { limit: 10000 });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Export failed.');
    } finally {
      setExporting(false);
    }
  };

  const handleCreateSavedView = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!viewName.trim()) return;

    try {
      await reportsService.createSavedView({
        section: reportData?.domain || 'reporting',
        name: viewName.trim(),
        filter_config: { report_id: selectedReportId, limit: 500 },
        is_shared: isShared,
      });
      setShowSaveModal(false);
      setViewName('');
      setSaveSuccessMsg('Saved view created successfully.');
      loadSavedViews();
      setTimeout(() => setSaveSuccessMsg(null), 4000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create saved view.');
    }
  };

  const handleDeleteSavedView = async (viewId: number) => {
    try {
      await reportsService.deleteSavedView(viewId);
      loadSavedViews();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete saved view.');
    }
  };

  // Catalogue table columns
  const catalogueColumns: Column<Record<string, unknown>>[] = [
    {
      key: 'name',
      header: 'Report Name',
      sortable: true,
      render: (row) => (
        <div>
          <div style={{ fontWeight: 600, color: '#ffffff' }}>{String(row.name)}</div>
          <div style={{ fontSize: '0.75rem', color: 'var(--color-text-subtle)' }}>
            {String(row.description)}
          </div>
        </div>
      ),
    },
    {
      key: 'domain',
      header: 'Domain',
      sortable: true,
      render: (row) => (
        <span
          style={{
            textTransform: 'uppercase',
            fontSize: '0.7rem',
            padding: '2px 8px',
            borderRadius: '4px',
            background: 'rgba(255, 255, 255, 0.08)',
            color: 'var(--color-primary-light, #90cdf4)',
            fontWeight: 600,
          }}
        >
          {String(row.domain)}
        </span>
      ),
    },
    { key: 'cadence', header: 'Cadence', sortable: true },
    {
      key: 'columns',
      header: 'Metrics & Columns',
      render: (row) => <span>{Array.isArray(row.columns) ? `${row.columns.length} columns` : '—'}</span>,
    },
    {
      key: 'exportable',
      header: 'Export Authorization',
      render: () => (
        <span
          style={{
            fontSize: '0.75rem',
            padding: '2px 8px',
            borderRadius: 'var(--radius-sm)',
            background: canExport ? 'rgba(72, 187, 120, 0.15)' : 'rgba(255, 255, 255, 0.05)',
            color: canExport ? '#48bb78' : 'var(--color-text-subtle)',
            fontWeight: 600,
          }}
        >
          {canExport ? 'Export Permitted' : 'Export Restricted'}
        </span>
      ),
    },
    {
      key: 'actions',
      header: 'Action',
      render: (row) => (
        <button
          onClick={() => handleOpenReport(String(row.report_id))}
          style={{
            padding: '4px 12px',
            fontSize: '0.8rem',
            fontWeight: 600,
            borderRadius: '4px',
            border: '1px solid var(--color-border)',
            background: 'var(--color-surface)',
            color: '#ffffff',
            cursor: 'pointer',
          }}
        >
          View Data →
        </button>
      ),
    },
  ];

  // Dynamic columns for active report viewer
  const activeReportColumns: Column<Record<string, unknown>>[] =
    reportData?.columns.map((col) => ({
      key: col,
      header: col
        .replace(/_/g, ' ')
        .replace(/\b\w/g, (l) => l.toUpperCase()),
      sortable: true,
      render: (row) => {
        const val = row[col];
        if (typeof val === 'number') {
          return <span>{val.toLocaleString()}</span>;
        }
        return <span>{val !== null && val !== undefined ? String(val) : '—'}</span>;
      },
    })) || [];

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

      {/* Synthetic Notice Banner */}
      <div style={{ marginBottom: '1rem' }}>
        <Alert variant="info" title="Synthetic Data Demonstration Notice">
          Notice: Synthetic Data Demonstration — All report records, exports, and aggregations are deterministically generated for local analytics evaluation.
        </Alert>
      </div>

      {saveSuccessMsg && (
        <div style={{ marginBottom: '1rem' }}>
          <Alert variant="success">{saveSuccessMsg}</Alert>
        </div>
      )}

      {error && (
        <div style={{ marginBottom: '1rem' }}>
          <Alert variant="error">{error}</Alert>
        </div>
      )}

      {/* Navigation Tabs */}
      <div
        style={{
          display: 'flex',
          gap: '0.5rem',
          borderBottom: '1px solid var(--color-border)',
          marginBottom: '1.5rem',
        }}
      >
        <button
          onClick={() => setActiveTab('catalogue')}
          style={{
            padding: '0.625rem 1.25rem',
            background: 'transparent',
            border: 'none',
            borderBottom: activeTab === 'catalogue' ? '2px solid var(--color-primary)' : '2px solid transparent',
            color: activeTab === 'catalogue' ? '#ffffff' : 'var(--color-text-muted)',
            fontWeight: 600,
            cursor: 'pointer',
          }}
        >
          Report Catalogue ({catalogue.length || 8})
        </button>
        <button
          onClick={() => {
            if (reportData) setActiveTab('viewer');
            else handleOpenReport(selectedReportId);
          }}
          style={{
            padding: '0.625rem 1.25rem',
            background: 'transparent',
            border: 'none',
            borderBottom: activeTab === 'viewer' ? '2px solid var(--color-primary)' : '2px solid transparent',
            color: activeTab === 'viewer' ? '#ffffff' : 'var(--color-text-muted)',
            fontWeight: 600,
            cursor: 'pointer',
          }}
        >
          Active Report Viewer {reportData ? `(${reportData.name})` : ''}
        </button>
        <button
          onClick={() => setActiveTab('saved_views')}
          style={{
            padding: '0.625rem 1.25rem',
            background: 'transparent',
            border: 'none',
            borderBottom: activeTab === 'saved_views' ? '2px solid var(--color-primary)' : '2px solid transparent',
            color: activeTab === 'saved_views' ? '#ffffff' : 'var(--color-text-muted)',
            fontWeight: 600,
            cursor: 'pointer',
          }}
        >
          Saved Views ({savedViews.length})
        </button>
      </div>

      {/* Catalogue Tab */}
      {activeTab === 'catalogue' && (
        <div>
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
              gap: '1rem',
              marginBottom: '1.5rem',
            }}
          >
            <KPICard
              title="Standard Reports"
              value={catalogue.length || 8}
              format="number"
              subtitle="Curated catalogue"
            />
            <KPICard
              title="Max Export Limit"
              value={50000}
              format="number"
              subtitle="Rows per download"
            />
            <KPICard title="Formula Injection Guard" value="ACTIVE" subtitle="RFC 4180 / CWE-1236" />
            <KPICard
              title="Export Authorization"
              value={canExport ? 'GRANTED' : 'RESTRICTED'}
              subtitle={canExport ? 'Full CSV exports enabled' : 'General Viewer restricted'}
            />
          </div>

          <DataTable
            data={catalogue as unknown as Record<string, unknown>[]}
            columns={catalogueColumns}
            keyExtractor={(r) => String((r as unknown as ReportCatalogueItem).report_id)}
            enableSearch
            searchPlaceholder="Search 8 business domain reports..."
            loading={loading}
          />
        </div>
      )}

      {/* Active Report Viewer Tab */}
      {activeTab === 'viewer' && (
        <div>
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              flexWrap: 'wrap',
              gap: '1rem',
              marginBottom: '1rem',
              background: 'var(--color-surface)',
              padding: '1rem',
              borderRadius: 'var(--radius-md)',
              border: '1px solid var(--color-border)',
            }}
          >
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.25rem' }}>
                <h2 style={{ margin: 0, fontSize: '1.25rem', color: '#ffffff' }}>
                  {reportData?.name || 'Loading Report...'}
                </h2>
                {reportData && (
                  <span
                    style={{
                      fontSize: '0.7rem',
                      padding: '2px 8px',
                      borderRadius: '4px',
                      background: 'rgba(255, 255, 255, 0.1)',
                      color: 'var(--color-primary-light, #90cdf4)',
                      fontWeight: 600,
                      textTransform: 'uppercase',
                    }}
                  >
                    {reportData.domain}
                  </span>
                )}
              </div>
              <p style={{ margin: 0, color: 'var(--color-text-muted)', fontSize: '0.8rem' }}>
                Total Records: {reportData?.total_rows || 0} rows | Cadence: Daily | Mode: Live Query
              </p>
            </div>

            <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
              <button
                onClick={() => setShowSaveModal(true)}
                style={{
                  padding: '6px 14px',
                  fontSize: '0.825rem',
                  fontWeight: 600,
                  borderRadius: '6px',
                  border: '1px solid var(--color-border)',
                  background: 'transparent',
                  color: '#ffffff',
                  cursor: 'pointer',
                }}
              >
                ★ Save View
              </button>

              {/* Export CSV Button */}
              <button
                data-testid="export-csv-button"
                onClick={handleExportCsv}
                disabled={!canExport || exporting}
                title={canExport ? 'Export sanitized CSV' : 'General Viewers cannot export data'}
                style={{
                  padding: '6px 14px',
                  fontSize: '0.825rem',
                  fontWeight: 600,
                  borderRadius: '6px',
                  border: 'none',
                  background: canExport ? 'var(--color-primary, #3182ce)' : 'rgba(255, 255, 255, 0.1)',
                  color: canExport ? '#ffffff' : 'rgba(255, 255, 255, 0.4)',
                  cursor: canExport && !exporting ? 'pointer' : 'not-allowed',
                }}
              >
                {exporting ? 'Exporting...' : '↓ Download CSV'}
              </button>

              {/* PDF Export Button (Clean Deferral - No Broken Action) */}
              <button
                disabled
                title="Server-side PDF generation is deferred to v1.1. Please use CSV export."
                style={{
                  padding: '6px 12px',
                  fontSize: '0.8rem',
                  borderRadius: '6px',
                  border: '1px solid rgba(255, 255, 255, 0.1)',
                  background: 'rgba(255, 255, 255, 0.05)',
                  color: 'rgba(255, 255, 255, 0.4)',
                  cursor: 'not-allowed',
                }}
              >
                PDF Export (v1.1)
              </button>
            </div>
          </div>

          {/* Report Summary Cards */}
          {reportData?.summary && Object.keys(reportData.summary).length > 0 && (
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
                gap: '1rem',
                marginBottom: '1.25rem',
              }}
            >
              {Object.entries(reportData.summary).slice(0, 4).map(([k, v]) => (
                <KPICard
                  key={k}
                  title={k.replace(/_/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase())}
                  value={typeof v === 'number' ? v : String(v)}
                  format={typeof v === 'number' && k.includes('revenue') ? 'currency' : 'number'}
                />
              ))}
            </div>
          )}

          {/* Interactive Report Data Table */}
          <DataTable
            data={(reportData?.rows || []) as Record<string, unknown>[]}
            columns={activeReportColumns}
            keyExtractor={(row) =>
              String(
                row.order_number ||
                  row.id ||
                  row.sku ||
                  row.customer_code ||
                  row.period ||
                  row.campaign_code ||
                  row.supplier_code ||
                  row.region_name ||
                  Math.random(),
              )
            }
            enableSearch
            searchPlaceholder={`Search within ${reportData?.name || 'report'}...`}
            loading={loading}
          />
        </div>
      )}

      {/* Saved Views Tab */}
      {activeTab === 'saved_views' && (
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
            <h2 style={{ margin: 0, fontSize: '1.2rem', color: '#ffffff' }}>
              Persisted Saved Filter Configurations
            </h2>
          </div>

          <DataTable
            data={savedViews as unknown as Record<string, unknown>[]}
            columns={[
              {
                key: 'name',
                header: 'View Name',
                sortable: true,
                render: (r) => (
                  <div style={{ fontWeight: 600, color: '#ffffff' }}>{String(r.name)}</div>
                ),
              },
              {
                key: 'section',
                header: 'Section',
                sortable: true,
                render: (r) => (
                  <span
                    style={{
                      textTransform: 'uppercase',
                      fontSize: '0.7rem',
                      padding: '2px 8px',
                      borderRadius: '4px',
                      background: 'rgba(255, 255, 255, 0.08)',
                      color: 'var(--color-primary-light, #90cdf4)',
                    }}
                  >
                    {String(r.section)}
                  </span>
                ),
              },
              {
                key: 'creator_name',
                header: 'Created By',
                render: (r) => <span>{String(r.creator_name || 'System')}</span>,
              },
              {
                key: 'is_shared',
                header: 'Visibility',
                render: (r) => (
                  <span
                    style={{
                      fontSize: '0.75rem',
                      padding: '2px 8px',
                      borderRadius: '4px',
                      background: r.is_shared ? 'rgba(66, 153, 225, 0.15)' : 'rgba(255, 255, 255, 0.05)',
                      color: r.is_shared ? '#63b3ed' : 'var(--color-text-subtle)',
                    }}
                  >
                    {r.is_shared ? 'Shared' : 'Private'}
                  </span>
                ),
              },
              {
                key: 'actions',
                header: 'Action',
                render: (r) => (
                  <div style={{ display: 'flex', gap: '0.5rem' }}>
                    <button
                      onClick={() => {
                        const cfg = r.filter_config as Record<string, unknown>;
                        if (cfg?.report_id) {
                          handleOpenReport(String(cfg.report_id));
                        } else {
                          handleOpenReport('sales-performance');
                        }
                      }}
                      style={{
                        padding: '4px 10px',
                        fontSize: '0.75rem',
                        fontWeight: 600,
                        borderRadius: '4px',
                        border: '1px solid var(--color-border)',
                        background: 'transparent',
                        color: '#ffffff',
                        cursor: 'pointer',
                      }}
                    >
                      Apply View
                    </button>
                    <button
                      onClick={() => handleDeleteSavedView(Number(r.id))}
                      style={{
                        padding: '4px 10px',
                        fontSize: '0.75rem',
                        fontWeight: 600,
                        borderRadius: '4px',
                        border: '1px solid rgba(229, 62, 62, 0.4)',
                        background: 'transparent',
                        color: '#feb2b2',
                        cursor: 'pointer',
                      }}
                    >
                      Delete
                    </button>
                  </div>
                ),
              },
            ]}
            keyExtractor={(r) => String((r as unknown as SavedView).id)}
            enableSearch
            searchPlaceholder="Search saved views..."
          />
        </div>
      )}

      {/* Save View Modal */}
      <Modal
        isOpen={showSaveModal}
        onClose={() => setShowSaveModal(false)}
        title="Save Current Filter Configuration"
      >
        <form onSubmit={handleCreateSavedView}>
          <div style={{ marginBottom: '1rem' }}>
            <label
              htmlFor="view-name"
              style={{ display: 'block', marginBottom: '0.375rem', fontSize: '0.875rem', fontWeight: 500 }}
            >
              View Name
            </label>
            <input
              id="view-name"
              type="text"
              required
              value={viewName}
              onChange={(e) => setViewName(e.target.value)}
              placeholder="e.g. Q4 Executive Sales Breakdown"
              style={{
                width: '100%',
                padding: '0.5rem',
                borderRadius: 'var(--radius-sm)',
                border: '1px solid var(--color-border)',
                background: 'rgba(0, 0, 0, 0.2)',
                color: '#ffffff',
              }}
            />
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1.25rem' }}>
            <input
              id="is-shared-checkbox"
              type="checkbox"
              checked={isShared}
              onChange={(e) => setIsShared(e.target.checked)}
            />
            <label htmlFor="is-shared-checkbox" style={{ fontSize: '0.85rem', color: 'var(--color-text-muted)' }}>
              Share this view with team members across the organization
            </label>
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.5rem' }}>
            <button
              type="button"
              onClick={() => setShowSaveModal(false)}
              style={{
                padding: '0.5rem 1rem',
                borderRadius: 'var(--radius-sm)',
                border: '1px solid var(--color-border)',
                background: 'transparent',
                color: 'var(--color-text-muted)',
                cursor: 'pointer',
              }}
            >
              Cancel
            </button>
            <button
              type="submit"
              style={{
                padding: '0.5rem 1rem',
                borderRadius: 'var(--radius-sm)',
                border: 'none',
                background: 'var(--color-primary, #3182ce)',
                color: '#ffffff',
                fontWeight: 600,
                cursor: 'pointer',
              }}
            >
              Save View
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
