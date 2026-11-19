import React, { useCallback, useEffect, useState } from 'react';
import { AlertCircle, CheckCircle, Database, FileSpreadsheet, RefreshCw, Upload } from 'lucide-react';
import { Alert } from '../../components/common/Alert';
import { Column, DataTable } from '../../components/common/DataTable';
import { FormField } from '../../components/common/FormField';
import { KPICard } from '../../components/common/KPICard';
import { Modal } from '../../components/common/Modal';
import { SkeletonLoader } from '../../components/common/SkeletonLoader';
import { useAuth } from '../../hooks/useAuth';
import { dataSourcesService } from '../../services/dataSources';
import { ImportJob, PreviewResponse } from '../../types/dataSources';

const TARGET_ENTITIES = [
  { value: 'customers', label: 'Customers (Master Data)' },
  { value: 'products', label: 'Products (Master Catalog)' },
  { value: 'orders', label: 'Orders (Transactional Data)' },
];

export const DataSourcesPage: React.FC = () => {
  const { isOwner } = useAuth();

  // History state
  const [history, setHistory] = useState<ImportJob[]>([]);
  const [loadingHistory, setLoadingHistory] = useState<boolean>(true);
  const [historyError, setHistoryError] = useState<string | null>(null);

  // Upload & preview state
  const [targetEntity, setTargetEntity] = useState<string>('customers');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState<boolean>(false);
  const [uploadError, setUploadError] = useState<string | null>(null);

  // Preview modal state
  const [previewData, setPreviewData] = useState<PreviewResponse | null>(null);
  const [columnMapping, setColumnMapping] = useState<Record<string, string>>({});
  const [allowDuplicate, setAllowDuplicate] = useState<boolean>(false);
  const [importing, setImporting] = useState<boolean>(false);
  const [importSuccessMsg, setImportSuccessMsg] = useState<string | null>(null);

  const fetchHistory = useCallback(async () => {
    setLoadingHistory(true);
    setHistoryError(null);
    try {
      const jobs = await dataSourcesService.getImportHistory(1, 50);
      setHistory(Array.isArray(jobs) ? jobs : []);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to load ingestion history';
      setHistoryError(msg);
    } finally {
      setLoadingHistory(false);
    }
  }, []);

  useEffect(() => {
    fetchHistory();
  }, [fetchHistory]);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0]);
      setUploadError(null);
      setImportSuccessMsg(null);
    }
  };

  const handlePreviewUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFile) {
      setUploadError('Please select a CSV file to inspect.');
      return;
    }

    setUploading(true);
    setUploadError(null);
    try {
      const preview = await dataSourcesService.uploadPreview(selectedFile, targetEntity);
      setPreviewData(preview);
      setColumnMapping(preview.suggested_mapping);
      setAllowDuplicate(preview.is_duplicate);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to inspect file.';
      setUploadError(msg);
    } finally {
      setUploading(false);
    }
  };

  const handleExecuteImport = async () => {
    if (!selectedFile || !previewData) return;

    setImporting(true);
    setUploadError(null);
    try {
      const result = await dataSourcesService.importData(
        selectedFile,
        targetEntity,
        columnMapping,
        allowDuplicate,
      );
      setImportSuccessMsg(
        `Successfully imported ${result.loaded_rows} records into '${result.target_entity}' (Job #${result.job_id}).`,
      );
      setPreviewData(null);
      setSelectedFile(null);
      fetchHistory();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Import failed.';
      setUploadError(msg);
    } finally {
      setImporting(false);
    }
  };

  // Metrics calculation
  const totalCompleted = history.filter((h) => h.status === 'completed').length;
  const totalLoadedRows = history.reduce((acc, h) => acc + (h.loaded_rows || 0), 0);

  const historyColumns: Column<Record<string, unknown>>[] = [
    {
      key: 'id',
      header: 'Job ID',
      width: '90px',
      render: (row) => <strong>#{String(row.id)}</strong>,
    },
    {
      key: 'target_entity',
      header: 'Target Entity',
      render: (row) => (
        <span
          style={{
            textTransform: 'uppercase',
            fontSize: '0.75rem',
            letterSpacing: '0.05em',
            padding: '2px 8px',
            borderRadius: '4px',
            background: 'var(--color-bg-secondary)',
            border: '1px solid var(--color-border)',
            color: 'var(--color-accent-teal)',
          }}
        >
          {String(row.target_entity)}
        </span>
      ),
    },
    {
      key: 'status',
      header: 'Status',
      render: (row) => {
        const s = String(row.status);
        const color =
          s === 'completed'
            ? 'var(--color-status-success)'
            : s === 'rolled_back' || s === 'failed'
              ? 'var(--color-status-danger)'
              : 'var(--color-status-warning)';
        return (
          <span
            style={{
              color,
              fontWeight: 600,
              fontSize: '0.8125rem',
              display: 'inline-flex',
              alignItems: 'center',
              gap: '4px',
            }}
          >
            {s === 'completed' && <CheckCircle size={14} />}
            {s === 'rolled_back' && <AlertCircle size={14} />}
            {s}
          </span>
        );
      },
    },
    {
      key: 'loaded_rows',
      header: 'Loaded / Total',
      render: (row) => `${row.loaded_rows} / ${row.total_rows}`,
    },
    {
      key: 'started_at',
      header: 'Executed At',
      render: (row) =>
        row.started_at ? new Date(String(row.started_at)).toLocaleString() : '—',
    },
  ];

  return (
    <div data-testid="data-sources-page">
      <div style={{ marginBottom: '1.25rem' }}>
        <h1
          style={{ margin: '0 0 0.25rem', fontSize: '1.625rem', fontWeight: 700, color: '#ffffff' }}
        >
          Data Ingestion & Source Management
        </h1>
        <p style={{ margin: 0, color: 'var(--color-text-muted)', fontSize: '0.875rem' }}>
          Batch CSV uploads, schema auto-mapping, transaction rollback safety, and upload history.
        </p>
      </div>

      {!isOwner && (
        <Alert variant="info" style={{ marginBottom: '1.25rem' }}>
          <strong>Read-Only Mode:</strong> File upload and dataset ingestion are restricted to the
          Platform Owner. Demonstration roles can inspect ingestion history and mapping templates.
        </Alert>
      )}

      {importSuccessMsg && (
        <Alert variant="success" style={{ marginBottom: '1.25rem' }}>
          {importSuccessMsg}
        </Alert>
      )}

      {uploadError && (
        <Alert variant="error" style={{ marginBottom: '1.25rem' }}>
          {uploadError}
        </Alert>
      )}

      {/* KPI Cards */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
          gap: '1rem',
          marginBottom: '1.5rem',
        }}
      >
        <KPICard
          title="Completed Ingestions"
          value={totalCompleted}
          format="number"
          subtitle={`${history.length} total jobs logged`}
        />
        <KPICard
          title="Total Ingested Records"
          value={totalLoadedRows}
          format="number"
          subtitle="Direct PostgreSQL inserts"
        />
        <KPICard
          title="Rollback Protection"
          value="ENABLED"
          subtitle="Zero partial row writes"
        />
        <KPICard
          title="Max Upload Limit"
          value="10 MB"
          subtitle="CSV format with SHA-256 hash"
        />
      </div>

      {/* Upload Dropzone Section (Owner Only) */}
      {isOwner && (
        <div
          style={{
            background: 'var(--color-bg-card)',
            border: '1px solid var(--color-border)',
            borderRadius: 'var(--radius-lg)',
            padding: '1.5rem',
            marginBottom: '1.5rem',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
            <Database size={20} color="var(--color-accent-teal)" />
            <h2 style={{ margin: 0, fontSize: '1.125rem', fontWeight: 600, color: '#ffffff' }}>
              Upload New Dataset
            </h2>
          </div>

          <form onSubmit={handlePreviewUpload}>
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
                gap: '1rem',
                marginBottom: '1.25rem',
              }}
            >
              <FormField label="Target Business Entity" id="target-entity-select">
                <select
                  id="target-entity-select"
                  value={targetEntity}
                  onChange={(e) => setTargetEntity(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '0.625rem',
                    background: 'var(--color-bg-secondary)',
                    border: '1px solid var(--color-border)',
                    borderRadius: 'var(--radius-md)',
                    color: '#ffffff',
                    fontSize: '0.875rem',
                  }}
                >
                  {TARGET_ENTITIES.map((ent) => (
                    <option key={ent.value} value={ent.value}>
                      {ent.label}
                    </option>
                  ))}
                </select>
              </FormField>

              <FormField label="Select CSV File (.csv, max 10MB)" id="file-input">
                <input
                  id="file-input"
                  type="file"
                  accept=".csv"
                  onChange={handleFileChange}
                  style={{
                    width: '100%',
                    padding: '0.5rem',
                    background: 'var(--color-bg-secondary)',
                    border: '1px solid var(--color-border)',
                    borderRadius: 'var(--radius-md)',
                    color: 'var(--color-text-muted)',
                    fontSize: '0.875rem',
                  }}
                />
              </FormField>
            </div>

            <button
              type="submit"
              disabled={uploading || !selectedFile}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '0.5rem',
                padding: '0.625rem 1.25rem',
                background:
                  uploading || !selectedFile ? 'var(--color-border)' : 'var(--color-accent-teal)',
                color: uploading || !selectedFile ? 'var(--color-text-muted)' : '#0f172a',
                border: 'none',
                borderRadius: 'var(--radius-md)',
                fontWeight: 600,
                fontSize: '0.875rem',
                cursor: uploading || !selectedFile ? 'not-allowed' : 'pointer',
              }}
            >
              <Upload size={16} />
              {uploading ? 'Analyzing CSV...' : 'Inspect & Preview File'}
            </button>
          </form>
        </div>
      )}

      {/* Ingestion History Section */}
      <div
        style={{
          background: 'var(--color-bg-card)',
          border: '1px solid var(--color-border)',
          borderRadius: 'var(--radius-lg)',
          padding: '1.5rem',
        }}
      >
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            marginBottom: '1rem',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <FileSpreadsheet size={20} color="var(--color-accent-teal)" />
            <h2 style={{ margin: 0, fontSize: '1.125rem', fontWeight: 600, color: '#ffffff' }}>
              Ingestion Execution History
            </h2>
          </div>
          <button
            onClick={fetchHistory}
            disabled={loadingHistory}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '0.375rem',
              padding: '0.375rem 0.75rem',
              background: 'transparent',
              border: '1px solid var(--color-border)',
              borderRadius: 'var(--radius-md)',
              color: 'var(--color-text-muted)',
              fontSize: '0.8125rem',
              cursor: loadingHistory ? 'wait' : 'pointer',
            }}
          >
            <RefreshCw size={14} className={loadingHistory ? 'animate-spin' : ''} />
            Refresh
          </button>
        </div>

        {historyError && (
          <Alert variant="error" style={{ marginBottom: '1rem' }}>
            {historyError}
          </Alert>
        )}

        {loadingHistory ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            <SkeletonLoader height="40px" />
            <SkeletonLoader height="40px" />
            <SkeletonLoader height="40px" />
          </div>
        ) : (
          <DataTable
            data={history as unknown as Record<string, unknown>[]}
            columns={historyColumns}
            keyExtractor={(row) => String(row.id)}
            emptyMessage="No dataset imports have been executed yet."
            enableSearch={true}
            searchPlaceholder="Search jobs by entity or status..."
          />
        )}
      </div>

      {/* Column Mapping & Preview Modal */}
      {previewData && (
        <Modal
          isOpen={Boolean(previewData)}
          onClose={() => setPreviewData(null)}
          title={`Dataset Ingestion Preview — ${previewData.file_name}`}
          maxWidth="760px"
          footer={
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem' }}>
              <button
                type="button"
                onClick={() => setPreviewData(null)}
                style={{
                  padding: '0.5rem 1rem',
                  background: 'transparent',
                  border: '1px solid var(--color-border)',
                  color: 'var(--color-text-muted)',
                  borderRadius: 'var(--radius-md)',
                  cursor: 'pointer',
                }}
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleExecuteImport}
                disabled={importing || previewData.missing_required_headers.length > 0}
                style={{
                  padding: '0.5rem 1.25rem',
                  background:
                    importing || previewData.missing_required_headers.length > 0
                      ? 'var(--color-border)'
                      : 'var(--color-accent-teal)',
                  color: '#0f172a',
                  border: 'none',
                  borderRadius: 'var(--radius-md)',
                  fontWeight: 600,
                  cursor:
                    importing || previewData.missing_required_headers.length > 0
                      ? 'not-allowed'
                      : 'pointer',
                }}
              >
                {importing ? 'Importing Dataset...' : 'Confirm & Execute Ingestion'}
              </button>
            </div>
          }
        >
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
            {/* Duplicate notice */}
            {previewData.is_duplicate && (
              <Alert variant="warning">
                <strong>Duplicate Checksum Detected:</strong> This identical file has already been
                imported. Check the box below if you wish to force re-import.
              </Alert>
            )}

            {/* Missing required headers notice */}
            {previewData.missing_required_headers.length > 0 && (
              <Alert variant="error">
                <strong>Missing Required Columns:</strong> The CSV lacks required fields for{' '}
                {previewData.target_entity}:{' '}
                <code>{previewData.missing_required_headers.join(', ')}</code>
              </Alert>
            )}

            {/* File info summary */}
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(3, 1fr)',
                gap: '0.75rem',
                background: 'var(--color-bg-secondary)',
                padding: '0.875rem',
                borderRadius: 'var(--radius-md)',
                fontSize: '0.8125rem',
              }}
            >
              <div>
                <span style={{ color: 'var(--color-text-muted)' }}>Detected Rows:</span>{' '}
                <strong>{previewData.total_detected_rows}</strong>
              </div>
              <div>
                <span style={{ color: 'var(--color-text-muted)' }}>Target Entity:</span>{' '}
                <strong style={{ textTransform: 'capitalize' }}>{previewData.target_entity}</strong>
              </div>
              <div>
                <span style={{ color: 'var(--color-text-muted)' }}>File Size:</span>{' '}
                <strong>{(previewData.file_size_bytes / 1024).toFixed(1)} KB</strong>
              </div>
            </div>

            {/* Column Mapping Section */}
            <div>
              <h3
                style={{
                  margin: '0 0 0.5rem',
                  fontSize: '0.9375rem',
                  fontWeight: 600,
                  color: '#ffffff',
                }}
              >
                Schema Column Mapping
              </h3>
              <p
                style={{
                  margin: '0 0 0.75rem',
                  color: 'var(--color-text-muted)',
                  fontSize: '0.8125rem',
                }}
              >
                Match your CSV column headers with the database entity schema.
              </p>
              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: '1fr 1fr',
                  gap: '0.5rem',
                  maxHeight: '180px',
                  overflowY: 'auto',
                }}
              >
                {Object.keys(previewData.suggested_mapping).map((schemaField) => (
                  <div
                    key={schemaField}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      background: 'var(--color-bg-secondary)',
                      padding: '0.5rem 0.75rem',
                      borderRadius: 'var(--radius-sm)',
                    }}
                  >
                    <span style={{ fontSize: '0.8125rem', fontWeight: 500, color: '#ffffff' }}>
                      {schemaField}
                    </span>
                    <select
                      value={columnMapping[schemaField] || ''}
                      onChange={(e) =>
                        setColumnMapping({ ...columnMapping, [schemaField]: e.target.value })
                      }
                      style={{
                        padding: '0.25rem 0.5rem',
                        background: 'var(--color-bg-card)',
                        border: '1px solid var(--color-border)',
                        color: '#ffffff',
                        borderRadius: '4px',
                        fontSize: '0.75rem',
                      }}
                    >
                      <option value="">-- select column --</option>
                      {previewData.detected_headers.map((hdr) => (
                        <option key={hdr} value={hdr}>
                          {hdr} ({previewData.inferred_types[hdr] || 'text'})
                        </option>
                      ))}
                    </select>
                  </div>
                ))}
              </div>
            </div>

            {/* Preview Rows Table */}
            <div>
              <h3
                style={{
                  margin: '0 0 0.5rem',
                  fontSize: '0.9375rem',
                  fontWeight: 600,
                  color: '#ffffff',
                }}
              >
                Sample Data Rows (First 5 Rows)
              </h3>
              <div
                style={{
                  overflowX: 'auto',
                  border: '1px solid var(--color-border)',
                  borderRadius: 'var(--radius-sm)',
                }}
              >
                <table
                  style={{
                    width: '100%',
                    borderCollapse: 'collapse',
                    fontSize: '0.75rem',
                    textAlign: 'left',
                  }}
                >
                  <thead style={{ background: 'var(--color-bg-secondary)' }}>
                    <tr>
                      {previewData.detected_headers.map((h) => (
                        <th
                          key={h}
                          style={{
                            padding: '6px 10px',
                            borderBottom: '1px solid var(--color-border)',
                            color: 'var(--color-text-muted)',
                          }}
                        >
                          {h}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {previewData.preview_rows.map((row, idx) => (
                      <tr
                        key={idx}
                        style={{ borderBottom: '1px solid var(--color-border-subtle)' }}
                      >
                        {previewData.detected_headers.map((h) => (
                          <td
                            key={h}
                            style={{
                              padding: '6px 10px',
                              color: '#ffffff',
                              whiteSpace: 'nowrap',
                            }}
                          >
                            {String(row[h] ?? '')}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Allow duplicate checkbox */}
            {previewData.is_duplicate && (
              <label
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem',
                  fontSize: '0.8125rem',
                  color: 'var(--color-text-muted)',
                  cursor: 'pointer',
                }}
              >
                <input
                  type="checkbox"
                  checked={allowDuplicate}
                  onChange={(e) => setAllowDuplicate(e.target.checked)}
                />
                Force re-import despite duplicate checksum
              </label>
            )}
          </div>
        </Modal>
      )}
    </div>
  );
};
