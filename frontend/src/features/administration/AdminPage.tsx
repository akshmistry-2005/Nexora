import React, { useCallback, useEffect, useState } from 'react';
import { AlertTriangle, CheckCircle2, Lock, RotateCcw, ShieldCheck } from 'lucide-react';
import { Alert } from '../../components/common/Alert';
import { Column, DataTable } from '../../components/common/DataTable';
import { KPICard } from '../../components/common/KPICard';
import { Modal } from '../../components/common/Modal';
import { useAuth } from '../../hooks/useAuth';
import { adminService } from '../../services/admin';
import { pipelinesService } from '../../services/pipelines';
import { AuditLogItem, AuditLogSummary, SystemStatusData, UserAdminItem } from '../../types/admin';
import { PipelineHealthSummary, PipelineRun } from '../../types/pipelines';

export const AdminPage: React.FC = () => {
  const { isOwner, user } = useAuth();
  const canManageQuality = isOwner || user?.permissions.includes('dataquality.manage');

  const [activeTab, setActiveTab] = useState<'pipelines' | 'audit' | 'users' | 'environment'>('pipelines');
  const [pipelineSummary, setPipelineSummary] = useState<PipelineHealthSummary | null>(null);
  const [pipelineRuns, setPipelineRuns] = useState<PipelineRun[]>([]);
  const [auditLogs, setAuditLogs] = useState<AuditLogItem[]>([]);
  const [auditSummary, setAuditSummary] = useState<AuditLogSummary | null>(null);
  const [usersList, setUsersList] = useState<UserAdminItem[]>([]);
  const [systemStatus, setSystemStatus] = useState<SystemStatusData | null>(null);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // Reset modal state
  const [resetModalOpen, setResetModalOpen] = useState(false);
  const [resetting, setResetting] = useState(false);

  // Retry action state
  const [retryingId, setRetryingId] = useState<number | null>(null);

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const [pipeSum, pipeRuns, sysStat] = await Promise.all([
        pipelinesService.getPipelineSummary(),
        pipelinesService.listPipelineRuns({ limit: 50 }),
        adminService.getSystemStatus(),
      ]);
      setPipelineSummary(pipeSum);
      setPipelineRuns(pipeRuns);
      setSystemStatus(sysStat);

      if (isOwner) {
        const [logs, logSum, users] = await Promise.all([
          adminService.getAuditLogs({ limit: 50 }),
          adminService.getAuditSummary(),
          adminService.getUsersList(),
        ]);
        setAuditLogs(logs);
        setAuditSummary(logSum);
        setUsersList(users);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch administration data');
    } finally {
      setLoading(false);
    }
  }, [isOwner]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleResetData = async () => {
    try {
      setResetting(true);
      setError(null);
      const res = await adminService.resetDemoData();
      setResetModalOpen(false);
      setSuccessMsg(`${res.message} (Timestamp: ${new Date(res.reset_timestamp).toLocaleTimeString()})`);
      await loadData();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Database reset failed');
    } finally {
      setResetting(false);
    }
  };

  const handleRetryPipeline = async (runId: number) => {
    try {
      setRetryingId(runId);
      setError(null);
      const res = await pipelinesService.retryPipelineRun(runId, 'Operator initiated safe retry from admin UI');
      setSuccessMsg(res.message);
      await loadData();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Pipeline retry failed');
    } finally {
      setRetryingId(null);
    }
  };

  const pipelineColumns: Column<PipelineRun>[] = [
    {
      key: 'pipeline_name',
      header: 'Pipeline Process',
      sortable: true,
      render: (r) => (
        <div>
          <strong style={{ color: '#ffffff', fontSize: '0.85rem' }}>{r.pipeline_name}</strong>
          <div style={{ fontSize: '0.75rem', color: '#94a3b8' }}>ID: #{r.id}</div>
        </div>
      ),
    },
    {
      key: 'status',
      header: 'Execution Status',
      sortable: true,
      render: (r) => {
        const isSuccess = r.status === 'success';
        const isFailed = r.status === 'failed';
        const isRetried = r.status === 'retried';
        const color = isSuccess ? '#34d399' : isFailed ? '#f87171' : isRetried ? '#fbbf24' : '#60a5fa';
        return (
          <span
            style={{
              padding: '2px 8px',
              borderRadius: '4px',
              fontSize: '0.75rem',
              fontWeight: 600,
              textTransform: 'uppercase',
              background: `${color}20`,
              color: color,
            }}
          >
            {r.status}
          </span>
        );
      },
    },
    {
      key: 'duration_ms',
      header: 'Duration',
      sortable: true,
      render: (r) => (
        <span style={{ fontSize: '0.8rem', color: '#cbd5e1' }}>
          {r.duration_ms !== null ? `${r.duration_ms} ms` : 'In progress'}
        </span>
      ),
    },
    {
      key: 'metrics',
      header: 'Execution Telemetry',
      render: (r) => {
        const err = r.metrics?.error_message || r.metrics?.error;
        return (
          <div style={{ fontSize: '0.75rem', color: '#cbd5e1', maxWidth: '300px' }}>
            {err ? (
              <span style={{ color: '#f87171' }}>Error: {String(err)}</span>
            ) : (
              <span>Telemetry: {JSON.stringify(r.metrics)}</span>
            )}
          </div>
        );
      },
    },
    {
      key: 'started_at',
      header: 'Started At',
      sortable: true,
      render: (r) => (
        <span style={{ fontSize: '0.75rem', color: '#94a3b8' }}>
          {new Date(r.started_at).toLocaleString()}
        </span>
      ),
    },
    {
      key: 'id',
      header: 'Actions',
      render: (r) =>
        (r.status === 'failed' || r.status === 'retried') && canManageQuality ? (
          <button
            onClick={() => handleRetryPipeline(r.id)}
            disabled={retryingId === r.id}
            data-testid={`retry-btn-${r.id}`}
            style={{
              padding: '3px 8px',
              fontSize: '0.75rem',
              borderRadius: '4px',
              background: '#2563eb',
              color: '#ffffff',
              border: 'none',
              cursor: retryingId === r.id ? 'wait' : 'pointer',
            }}
          >
            {retryingId === r.id ? 'Retrying...' : 'Safe Retry'}
          </button>
        ) : (
          <span style={{ fontSize: '0.75rem', color: '#64748b' }}>&mdash;</span>
        ),
    },
  ];

  const auditColumns: Column<AuditLogItem>[] = [
    {
      key: 'action_type',
      header: 'Action Event',
      sortable: true,
      render: (r) => (
        <strong style={{ fontSize: '0.8rem', color: '#38bdf8' }}>{r.action_type}</strong>
      ),
    },
    {
      key: 'actor_role',
      header: 'Actor Role',
      sortable: true,
      render: (r) => (
        <span
          style={{
            fontSize: '0.75rem',
            padding: '2px 6px',
            borderRadius: '4px',
            background: 'rgba(100, 116, 139, 0.2)',
            color: '#cbd5e1',
          }}
        >
          {r.actor_role} (ID #{r.actor_user_id ?? 'Anon'})
        </span>
      ),
    },
    {
      key: 'details',
      header: 'Event Details',
      render: (r) => (
        <span style={{ fontSize: '0.75rem', color: '#cbd5e1', fontFamily: 'monospace' }}>
          {r.details ? JSON.stringify(r.details) : 'None'}
        </span>
      ),
    },
    {
      key: 'created_at',
      header: 'Timestamp',
      sortable: true,
      render: (r) => (
        <span style={{ fontSize: '0.75rem', color: '#94a3b8' }}>
          {new Date(r.created_at).toLocaleString()}
        </span>
      ),
    },
  ];

  return (
    <div data-testid="admin-page" style={{ padding: '1.5rem', maxWidth: '1400px', margin: '0 auto' }}>
      {/* Title */}
      <div style={{ marginBottom: '1.25rem' }}>
        <h1 style={{ margin: '0 0 0.25rem', fontSize: '1.625rem', fontWeight: 700, color: '#ffffff' }}>
          Platform Administration & Pipeline Telemetry
        </h1>
        <p style={{ margin: 0, color: '#94a3b8', fontSize: '0.875rem' }}>
          Data pipeline execution tracking, immutable audit trails, and platform governance controls.
        </p>
      </div>

      {/* Mandatory Synthetic Data Notice (M14-T13) */}
      <div
        data-testid="synthetic-data-notice"
        style={{
          padding: '10px 14px',
          marginBottom: '1.25rem',
          background: 'rgba(56, 189, 248, 0.1)',
          border: '1px solid rgba(56, 189, 248, 0.25)',
          color: '#38bdf8',
          borderRadius: '6px',
          fontSize: '0.85rem',
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
        }}
      >
        <ShieldCheck size={18} />
        <span>
          <strong>Demonstration Environment Notice:</strong> All data, pipeline telemetry, and audit logs are
          synthetically generated for demonstration and evaluation purposes.
        </span>
      </div>

      {/* Owner Restriction Notice */}
      {!isOwner && (
        <Alert variant="warning" style={{ marginBottom: '1.25rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Lock size={16} />
            <span>
              <strong>Owner Privileges Required:</strong> Demonstration dataset reset and administrative user oversight
              are restricted to the Platform Owner.
            </span>
          </div>
        </Alert>
      )}

      {/* Notifications */}
      {error && (
        <Alert variant="error" style={{ marginBottom: '1.25rem' }}>
          {error}
        </Alert>
      )}

      {successMsg && (
        <Alert variant="success" style={{ marginBottom: '1.25rem' }} onClose={() => setSuccessMsg(null)}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <CheckCircle2 size={16} />
            <span>{successMsg}</span>
          </div>
        </Alert>
      )}

      {/* Top KPI Scorecards */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
          gap: '1rem',
          marginBottom: '1.5rem',
        }}
      >
        <KPICard
          title="Total Pipeline Runs"
          value={pipelineSummary?.total_runs_count ?? 0}
          format="number"
          subtitle={`${pipelineSummary?.active_pipelines_count ?? 0} active pipelines`}
        />
        <KPICard
          title="Failed Pipeline Runs"
          value={pipelineSummary?.failed_runs_count ?? 0}
          format="number"
          subtitle="Queryable failure telemetry"
        />
        <KPICard
          title="Audit Trail Entries"
          value={auditSummary?.total_logs ?? systemStatus?.table_counts?.audit_logs ?? 0}
          format="number"
          subtitle="Append-only immutable log"
        />
        <KPICard
          title="Database Status"
          value={systemStatus?.database_connected ? 'ONLINE' : 'OFFLINE'}
          subtitle="PostgreSQL 16 Engine"
        />
      </div>

      {/* Tabs */}
      <div
        style={{
          display: 'flex',
          gap: '8px',
          borderBottom: '1px solid #334155',
          marginBottom: '1.25rem',
        }}
      >
        <button
          onClick={() => setActiveTab('pipelines')}
          data-testid="tab-pipelines"
          style={{
            padding: '8px 16px',
            background: 'transparent',
            border: 'none',
            borderBottom: activeTab === 'pipelines' ? '2px solid #38bdf8' : '2px solid transparent',
            color: activeTab === 'pipelines' ? '#ffffff' : '#94a3b8',
            fontWeight: 600,
            fontSize: '0.875rem',
            cursor: 'pointer',
          }}
        >
          Pipelines & Telemetry
        </button>
        {isOwner && (
          <>
            <button
              onClick={() => setActiveTab('audit')}
              data-testid="tab-audit"
              style={{
                padding: '8px 16px',
                background: 'transparent',
                border: 'none',
                borderBottom: activeTab === 'audit' ? '2px solid #38bdf8' : '2px solid transparent',
                color: activeTab === 'audit' ? '#ffffff' : '#94a3b8',
                fontWeight: 600,
                fontSize: '0.875rem',
                cursor: 'pointer',
              }}
            >
              Security Audit Trail
            </button>
            <button
              onClick={() => setActiveTab('users')}
              data-testid="tab-users"
              style={{
                padding: '8px 16px',
                background: 'transparent',
                border: 'none',
                borderBottom: activeTab === 'users' ? '2px solid #38bdf8' : '2px solid transparent',
                color: activeTab === 'users' ? '#ffffff' : '#94a3b8',
                fontWeight: 600,
                fontSize: '0.875rem',
                cursor: 'pointer',
              }}
            >
              User Directory & RBAC
            </button>
          </>
        )}
        <button
          onClick={() => setActiveTab('environment')}
          data-testid="tab-environment"
          style={{
            padding: '8px 16px',
            background: 'transparent',
            border: 'none',
            borderBottom: activeTab === 'environment' ? '2px solid #38bdf8' : '2px solid transparent',
            color: activeTab === 'environment' ? '#ffffff' : '#94a3b8',
            fontWeight: 600,
            fontSize: '0.875rem',
            cursor: 'pointer',
          }}
        >
          Environment & Reset
        </button>
      </div>

      {/* Tab 1: Pipelines */}
      {activeTab === 'pipelines' && (
        <div>
          {loading ? (
            <div style={{ padding: '2rem', textAlign: 'center', color: '#94a3b8' }}>
              Loading pipeline execution telemetry...
            </div>
          ) : (
            <DataTable
              data={pipelineRuns as unknown as Record<string, unknown>[]}
              columns={pipelineColumns as unknown as Column<Record<string, unknown>>[]}
              keyExtractor={(r) => String((r as unknown as PipelineRun).id)}
              enableSearch
              searchPlaceholder="Search pipeline executions..."
            />
          )}
        </div>
      )}

      {/* Tab 2: Security Audit Trail */}
      {activeTab === 'audit' && isOwner && (
        <div>
          <div
            style={{
              padding: '10px',
              background: '#0f172a',
              borderRadius: '6px',
              marginBottom: '1rem',
              fontSize: '0.8rem',
              color: '#94a3b8',
            }}
          >
            <strong>PostgreSQL Engine Enforcement:</strong> The <code>audit_logs</code> table is protected by a database
            trigger. Direct <code>UPDATE</code> and <code>DELETE</code> operations are rejected at the database layer.
          </div>
          <DataTable
            data={auditLogs as unknown as Record<string, unknown>[]}
            columns={auditColumns as unknown as Column<Record<string, unknown>>[]}
            keyExtractor={(r) => String((r as unknown as AuditLogItem).id)}
            enableSearch
            searchPlaceholder="Search audit events by action or actor..."
          />
        </div>
      )}

      {/* Tab 3: Users */}
      {activeTab === 'users' && isOwner && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
          {usersList.map((u) => (
            <div
              key={u.id}
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                padding: '12px',
                background: '#1e293b',
                borderRadius: '6px',
                border: '1px solid #334155',
              }}
            >
              <div>
                <strong style={{ color: '#ffffff' }}>{u.full_name}</strong>
                <div style={{ fontSize: '0.8rem', color: '#94a3b8' }}>{u.email}</div>
              </div>
              <div style={{ display: 'flex', gap: '6px', alignItems: 'center' }}>
                {u.roles.map((r) => (
                  <span
                    key={r}
                    style={{
                      padding: '2px 8px',
                      background: '#2563eb20',
                      color: '#60a5fa',
                      borderRadius: '4px',
                      fontSize: '0.75rem',
                    }}
                  >
                    {r}
                  </span>
                ))}
                {u.is_owner && (
                  <span
                    style={{
                      padding: '2px 8px',
                      background: '#10b98120',
                      color: '#34d399',
                      borderRadius: '4px',
                      fontSize: '0.75rem',
                      fontWeight: 600,
                    }}
                  >
                    OWNER
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Tab 4: Environment & Reset */}
      {activeTab === 'environment' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          <div
            style={{
              background: '#1e293b',
              borderRadius: '8px',
              border: '1px solid #334155',
              padding: '1.25rem',
            }}
          >
            <h3 style={{ margin: '0 0 0.5rem', fontSize: '1.1rem', color: '#ffffff' }}>
              Synthetic Dataset Record Volumes
            </h3>
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))',
                gap: '0.75rem',
              }}
            >
              {systemStatus?.table_counts &&
                Object.entries(systemStatus.table_counts).map(([tbl, cnt]) => (
                  <div key={tbl} style={{ background: '#0f172a', padding: '10px', borderRadius: '4px' }}>
                    <div style={{ fontSize: '0.75rem', color: '#94a3b8', textTransform: 'capitalize' }}>{tbl}</div>
                    <div style={{ fontSize: '1.2rem', fontWeight: 700, color: '#ffffff' }}>
                      {cnt.toLocaleString()}
                    </div>
                  </div>
                ))}
            </div>
          </div>

          <div
            style={{
              background: '#1e293b',
              borderRadius: '8px',
              border: '1px solid #334155',
              padding: '1.25rem',
            }}
          >
            <h3 style={{ margin: '0 0 0.5rem', fontSize: '1.1rem', color: '#ffffff' }}>
              Demonstration Environment Reset
            </h3>
            <p style={{ margin: '0 0 1rem', fontSize: '0.85rem', color: '#94a3b8', maxWidth: '600px' }}>
              Reset all dynamic transactions and pipeline test runs back to clean baseline state. Restricted strictly
              to Platform Owner.
            </p>

            <button
              type="button"
              data-testid="admin-reset-data-btn"
              disabled={!isOwner}
              onClick={() => setResetModalOpen(true)}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '0.45rem',
                background: isOwner ? '#ef4444' : '#334155',
                color: isOwner ? '#ffffff' : '#64748b',
                border: 'none',
                borderRadius: '6px',
                padding: '8px 16px',
                fontWeight: 600,
                fontSize: '0.875rem',
                cursor: isOwner ? 'pointer' : 'not-allowed',
              }}
            >
              <RotateCcw size={15} />
              Reset Demonstration Database
            </button>
          </div>
        </div>
      )}

      {/* Confirmation Modal */}
      <Modal
        isOpen={resetModalOpen}
        onClose={() => setResetModalOpen(false)}
        title="Confirm Demonstration Data Reset"
        maxWidth="480px"
        footer={
          <>
            <button
              type="button"
              onClick={() => setResetModalOpen(false)}
              style={{
                background: 'transparent',
                border: '1px solid #475569',
                color: '#cbd5e1',
                borderRadius: '4px',
                padding: '6px 14px',
                cursor: 'pointer',
              }}
            >
              Cancel
            </button>
            <button
              type="button"
              data-testid="confirm-reset-btn"
              disabled={resetting}
              onClick={handleResetData}
              style={{
                background: '#ef4444',
                color: '#ffffff',
                border: 'none',
                borderRadius: '4px',
                padding: '6px 16px',
                fontWeight: 600,
                cursor: resetting ? 'wait' : 'pointer',
              }}
            >
              {resetting ? 'Resetting...' : 'Confirm Reset'}
            </button>
          </>
        }
      >
        <div style={{ display: 'flex', alignItems: 'flex-start', gap: '0.75rem' }}>
          <div style={{ color: '#ef4444', flexShrink: 0, marginTop: '2px' }}>
            <AlertTriangle size={24} />
          </div>
          <div style={{ fontSize: '0.875rem', color: '#cbd5e1', lineHeight: 1.5 }}>
            <p style={{ margin: '0 0 0.5rem', fontWeight: 600, color: '#ffffff' }}>
              Are you sure you want to reset the synthetic demonstration dataset?
            </p>
            <p style={{ margin: 0 }}>
              This operation executes owner reset, cleans dynamic staging records, and appends an immutable
              ADMIN_SYSTEM_RESET audit event.
            </p>
          </div>
        </div>
      </Modal>
    </div>
  );
};
