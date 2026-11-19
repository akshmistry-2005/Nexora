import React, { useCallback, useEffect, useState } from 'react';
import { Column, DataTable } from '../../components/common/DataTable';
import { KPICard } from '../../components/common/KPICard';
import { useAuth } from '../../hooks/useAuth';
import { anomaliesService } from '../../services/anomalies';
import {
  AnomalyAlert,
  AnomalyDomain,
  AnomalySeverity,
  AnomalyStatus,
  AnomalySummaryStats,
  IsolationForestBenchmark,
} from '../../types/anomalies';

export const AnomaliesPage: React.FC = () => {
  const { user } = useAuth();
  const isOwner = user?.role === 'owner';

  const [activeTab, setActiveTab] = useState<'feed' | 'benchmark'>('feed');
  const [alerts, setAlerts] = useState<AnomalyAlert[]>([]);
  const [stats, setStats] = useState<AnomalySummaryStats | null>(null);
  const [benchmark, setBenchmark] = useState<IsolationForestBenchmark | null>(null);
  const [loading, setLoading] = useState(true);
  const [scanLoading, setScanLoading] = useState(false);
  const [benchmarkLoading, setBenchmarkLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // Filters
  const [selectedDomain, setSelectedDomain] = useState<string>('all');
  const [selectedSeverity, setSelectedSeverity] = useState<string>('all');
  const [selectedStatus, setSelectedStatus] = useState<string>('all');

  // Triage Modal state
  const [triageAlert, setTriageAlert] = useState<AnomalyAlert | null>(null);
  const [triageStatus, setTriageStatus] = useState<AnomalyStatus>('acknowledged');
  const [triageNotes, setTriageNotes] = useState('');
  const [triageSubmitting, setTriageSubmitting] = useState(false);

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const [statsData, alertsData] = await Promise.all([
        anomaliesService.getSummaryStats(),
        anomaliesService.getAnomalies({
          domain: selectedDomain === 'all' ? undefined : (selectedDomain as AnomalyDomain),
          severity: selectedSeverity === 'all' ? undefined : (selectedSeverity as AnomalySeverity),
          status: selectedStatus === 'all' ? undefined : (selectedStatus as AnomalyStatus),
          limit: 100,
        }),
      ]);
      setStats(statsData);
      setAlerts(alertsData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch anomaly data');
    } finally {
      setLoading(false);
    }
  }, [selectedDomain, selectedSeverity, selectedStatus]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const loadBenchmark = async () => {
    try {
      setBenchmarkLoading(true);
      setError(null);
      const data = await anomaliesService.getIsolationForestBenchmark(0.03);
      setBenchmark(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load Isolation Forest benchmark');
    } finally {
      setBenchmarkLoading(false);
    }
  };

  const handleTabChange = (tab: 'feed' | 'benchmark') => {
    setActiveTab(tab);
    if (tab === 'benchmark' && !benchmark) {
      loadBenchmark();
    }
  };

  const handleRunDetection = async () => {
    try {
      setScanLoading(true);
      setError(null);
      const res = await anomaliesService.runAutomatedDetection(3.0);
      setSuccessMsg(
        `Automated scan completed in ${res.run_duration_ms}ms. ${res.new_anomalies_detected} new anomalies detected across ${res.domains_scanned.join(', ')}.`,
      );
      await loadData();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Automated detection scan failed');
    } finally {
      setScanLoading(false);
    }
  };

  const handleAcknowledgeSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!triageAlert) return;
    try {
      setTriageSubmitting(true);
      await anomaliesService.acknowledgeAnomaly(triageAlert.id, {
        status: triageStatus,
        notes: triageNotes || undefined,
      });
      setSuccessMsg(`Alert #${triageAlert.id} status updated to ${triageStatus}.`);
      setTriageAlert(null);
      setTriageNotes('');
      await loadData();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update alert status');
    } finally {
      setTriageSubmitting(false);
    }
  };

  const columns: Column<AnomalyAlert>[] = [
    {
      key: 'domain',
      header: 'Domain / Metric',
      sortable: true,
      render: (r) => (
        <div>
          <span
            style={{
              padding: '2px 6px',
              borderRadius: '4px',
              fontSize: '0.7rem',
              fontWeight: 700,
              textTransform: 'uppercase',
              background: 'rgba(59, 130, 246, 0.15)',
              color: '#60a5fa',
              marginRight: '6px',
            }}
          >
            {r.domain}
          </span>
          <strong style={{ color: '#ffffff', fontSize: '0.85rem' }}>{r.metric_name}</strong>
          <div style={{ fontSize: '0.75rem', color: '#94a3b8', marginTop: '2px' }}>
            Entity: {r.entity_identifier}
          </div>
        </div>
      ),
    },
    {
      key: 'severity',
      header: 'Severity',
      sortable: true,
      render: (r) => {
        const bg =
          r.severity === 'critical'
            ? 'rgba(239, 68, 68, 0.2)'
            : r.severity === 'high'
              ? 'rgba(245, 158, 11, 0.2)'
              : r.severity === 'medium'
                ? 'rgba(59, 130, 246, 0.2)'
                : 'rgba(100, 116, 139, 0.2)';
        const color =
          r.severity === 'critical'
            ? '#f87171'
            : r.severity === 'high'
              ? '#fbbf24'
              : r.severity === 'medium'
                ? '#60a5fa'
                : '#94a3b8';
        return (
          <span
            style={{
              padding: '2px 8px',
              borderRadius: '4px',
              fontSize: '0.75rem',
              fontWeight: 600,
              textTransform: 'capitalize',
              background: bg,
              color: color,
            }}
          >
            {r.severity}
          </span>
        );
      },
    },
    {
      key: 'z_score',
      header: 'Deviation (Z-Score)',
      sortable: true,
      render: (r) => (
        <div>
          <span
            style={{
              fontFamily: 'monospace',
              fontWeight: 600,
              color: Math.abs(Number(r.z_score || 0)) >= 3.0 ? '#f87171' : '#fbbf24',
            }}
          >
            {Number(r.z_score || 0) > 0 ? `+${r.z_score}` : r.z_score}σ
          </span>
          <div style={{ fontSize: '0.75rem', color: '#94a3b8' }}>
            Obs: {Number(r.observed_value).toLocaleString()} | Base:{' '}
            {Number(r.baseline_value).toLocaleString()}
          </div>
        </div>
      ),
    },
    {
      key: 'explanation',
      header: 'Statistical Context',
      render: (r) => (
        <div style={{ fontSize: '0.8rem', color: '#cbd5e1', maxWidth: '380px', lineHeight: 1.4 }}>
          {r.explanation}
        </div>
      ),
    },
    {
      key: 'status',
      header: 'Status',
      sortable: true,
      render: (r) => {
        const isAck = r.status === 'acknowledged';
        const isRes = r.status === 'resolved';
        const color = isRes ? '#34d399' : isAck ? '#60a5fa' : '#f87171';
        return (
          <span
            style={{
              fontSize: '0.75rem',
              fontWeight: 600,
              textTransform: 'capitalize',
              color: color,
            }}
          >
            {r.status}
          </span>
        );
      },
    },
    {
      key: 'id',
      header: 'Actions',
      render: (r) =>
        isOwner ? (
          <button
            onClick={() => {
              setTriageAlert(r);
              setTriageStatus('acknowledged');
              setTriageNotes('');
            }}
            style={{
              padding: '4px 10px',
              fontSize: '0.75rem',
              fontWeight: 600,
              borderRadius: '4px',
              background: '#334155',
              color: '#ffffff',
              border: '1px solid #475569',
              cursor: 'pointer',
            }}
            data-testid={`triage-btn-${r.id}`}
          >
            Triage
          </button>
        ) : (
          <span style={{ fontSize: '0.75rem', color: '#64748b' }}>View only</span>
        ),
    },
  ];

  return (
    <div data-testid="anomalies-page" style={{ padding: '1.5rem', maxWidth: '1400px', margin: '0 auto' }}>
      {/* Header */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'flex-start',
          marginBottom: '1.5rem',
          flexWrap: 'wrap',
          gap: '1rem',
        }}
      >
        <div>
          <h1 style={{ margin: '0 0 0.25rem', fontSize: '1.625rem', fontWeight: 700, color: '#ffffff' }}>
            Anomaly Detection & Risk Intelligence
          </h1>
          <p style={{ margin: 0, color: '#94a3b8', fontSize: '0.875rem' }}>
            Multi-sigma statistical outlier detection, mathematical explainability, and triage workflows.
          </p>
        </div>

        {isOwner && (
          <button
            onClick={handleRunDetection}
            disabled={scanLoading}
            data-testid="run-scan-btn"
            style={{
              padding: '8px 16px',
              borderRadius: '6px',
              background: scanLoading ? '#475569' : '#2563eb',
              color: '#ffffff',
              border: 'none',
              fontWeight: 600,
              fontSize: '0.875rem',
              cursor: scanLoading ? 'not-allowed' : 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
            }}
          >
            {scanLoading ? 'Scanning...' : 'Run Automated Scan'}
          </button>
        )}
      </div>

      {/* Notifications */}
      {error && (
        <div
          data-testid="anomalies-error-alert"
          style={{
            padding: '10px 14px',
            marginBottom: '1.25rem',
            background: 'rgba(239, 68, 68, 0.15)',
            border: '1px solid rgba(239, 68, 68, 0.3)',
            color: '#f87171',
            borderRadius: '6px',
            fontSize: '0.875rem',
          }}
        >
          {error}
        </div>
      )}

      {successMsg && (
        <div
          data-testid="anomalies-success-alert"
          style={{
            padding: '10px 14px',
            marginBottom: '1.25rem',
            background: 'rgba(16, 185, 129, 0.15)',
            border: '1px solid rgba(16, 185, 129, 0.3)',
            color: '#34d399',
            borderRadius: '6px',
            fontSize: '0.875rem',
            display: 'flex',
            justifyContent: 'space-between',
          }}
        >
          <span>{successMsg}</span>
          <button
            onClick={() => setSuccessMsg(null)}
            style={{ background: 'transparent', border: 'none', color: '#34d399', cursor: 'pointer' }}
          >
            &times;
          </button>
        </div>
      )}

      {/* KPI Cards */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
          gap: '1rem',
          marginBottom: '1.5rem',
        }}
      >
        <KPICard
          title="Total Alerts Logged"
          value={stats?.total_alerts ?? 0}
          format="number"
          subtitle="All historical detections"
        />
        <KPICard
          title="Open Anomalies"
          value={stats?.open_alerts ?? 0}
          format="number"
          subtitle="Awaiting triage or review"
        />
        <KPICard
          title="Critical Severities"
          value={stats?.critical_count ?? 0}
          format="number"
          subtitle="|Z| >= 3.5 or deviation >= 75%"
        />
        <KPICard
          title="Acknowledged"
          value={stats?.acknowledged_count ?? 0}
          format="number"
          subtitle="Audited and confirmed"
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
          onClick={() => handleTabChange('feed')}
          data-testid="tab-alerts-feed"
          style={{
            padding: '8px 16px',
            background: 'transparent',
            border: 'none',
            borderBottom: activeTab === 'feed' ? '2px solid #38bdf8' : '2px solid transparent',
            color: activeTab === 'feed' ? '#ffffff' : '#94a3b8',
            fontWeight: 600,
            fontSize: '0.875rem',
            cursor: 'pointer',
          }}
        >
          Active Outliers & Alerts Feed
        </button>
        <button
          onClick={() => handleTabChange('benchmark')}
          data-testid="tab-isolation-forest"
          style={{
            padding: '8px 16px',
            background: 'transparent',
            border: 'none',
            borderBottom: activeTab === 'benchmark' ? '2px solid #38bdf8' : '2px solid transparent',
            color: activeTab === 'benchmark' ? '#ffffff' : '#94a3b8',
            fontWeight: 600,
            fontSize: '0.875rem',
            cursor: 'pointer',
          }}
        >
          Isolation Forest Benchmark (BL-16)
        </button>
      </div>

      {/* Tab 1: Live Alerts Feed */}
      {activeTab === 'feed' && (
        <div>
          {/* Filter Bar */}
          <div
            style={{
              display: 'flex',
              gap: '12px',
              marginBottom: '1rem',
              flexWrap: 'wrap',
              background: '#1e293b',
              padding: '12px',
              borderRadius: '8px',
              alignItems: 'center',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <label htmlFor="domain-filter" style={{ fontSize: '0.8rem', color: '#94a3b8' }}>Domain:</label>
              <select
                id="domain-filter"
                value={selectedDomain}
                onChange={(e) => setSelectedDomain(e.target.value)}
                style={{
                  background: '#0f172a',
                  color: '#ffffff',
                  border: '1px solid #334155',
                  padding: '4px 8px',
                  borderRadius: '4px',
                  fontSize: '0.8rem',
                }}
              >
                <option value="all">All Domains</option>
                <option value="sales">Sales</option>
                <option value="transaction">Transaction</option>
                <option value="inventory">Inventory</option>
                <option value="marketing">Marketing</option>
                <option value="operations">Operations</option>
              </select>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <label htmlFor="severity-filter" style={{ fontSize: '0.8rem', color: '#94a3b8' }}>Severity:</label>
              <select
                id="severity-filter"
                value={selectedSeverity}
                onChange={(e) => setSelectedSeverity(e.target.value)}
                style={{
                  background: '#0f172a',
                  color: '#ffffff',
                  border: '1px solid #334155',
                  padding: '4px 8px',
                  borderRadius: '4px',
                  fontSize: '0.8rem',
                }}
              >
                <option value="all">All Severities</option>
                <option value="critical">Critical</option>
                <option value="high">High</option>
                <option value="medium">Medium</option>
                <option value="low">Low</option>
              </select>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <label htmlFor="status-filter" style={{ fontSize: '0.8rem', color: '#94a3b8' }}>Status:</label>
              <select
                id="status-filter"
                value={selectedStatus}
                onChange={(e) => setSelectedStatus(e.target.value)}
                style={{
                  background: '#0f172a',
                  color: '#ffffff',
                  border: '1px solid #334155',
                  padding: '4px 8px',
                  borderRadius: '4px',
                  fontSize: '0.8rem',
                }}
              >
                <option value="all">All Statuses</option>
                <option value="open">Open</option>
                <option value="acknowledged">Acknowledged</option>
                <option value="resolved">Resolved</option>
                <option value="dismissed">Dismissed</option>
              </select>
            </div>

            <button
              onClick={() => {
                setSelectedDomain('all');
                setSelectedSeverity('all');
                setSelectedStatus('all');
              }}
              style={{
                marginLeft: 'auto',
                background: 'transparent',
                border: 'none',
                color: '#38bdf8',
                fontSize: '0.8rem',
                cursor: 'pointer',
              }}
            >
              Reset Filters
            </button>
          </div>

          {/* Table */}
          {loading ? (
            <div style={{ padding: '2rem', textAlign: 'center', color: '#94a3b8' }}>
              Loading anomaly intelligence...
            </div>
          ) : (
            <DataTable
              data={alerts as unknown as Record<string, unknown>[]}
              columns={columns as unknown as Column<Record<string, unknown>>[]}
              keyExtractor={(r) => String((r as unknown as AnomalyAlert).id)}
              enableSearch
              searchPlaceholder="Search anomalies by metric, SKU, or explanation..."
            />
          )}
        </div>
      )}

      {/* Tab 2: Isolation Forest Benchmark (BL-16) */}
      {activeTab === 'benchmark' && (
        <div>
          {benchmarkLoading ? (
            <div style={{ padding: '2rem', textAlign: 'center', color: '#94a3b8' }}>
              Evaluating multivariate Isolation Forest against univariate statistical baseline...
            </div>
          ) : benchmark ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
              <div
                style={{
                  background: '#1e293b',
                  borderRadius: '8px',
                  padding: '1.25rem',
                  border: '1px solid #334155',
                }}
              >
                <h3 style={{ margin: '0 0 0.5rem', color: '#ffffff', fontSize: '1.1rem' }}>
                  Multivariate ML vs Univariate Statistical Baseline (BL-16)
                </h3>
                <p style={{ margin: '0 0 1rem', color: '#94a3b8', fontSize: '0.85rem' }}>
                  {benchmark.agreement_rate_pct !== undefined
                    ? `Statistical concordance rate: ${benchmark.agreement_rate_pct}%`
                    : 'Comparison between Isolation Forest (scikit-learn) and rolling 3-sigma Z-scores.'}
                </p>

                <div
                  style={{
                    display: 'grid',
                    gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
                    gap: '1rem',
                  }}
                >
                  <div style={{ background: '#0f172a', padding: '1rem', borderRadius: '6px' }}>
                    <div style={{ fontSize: '0.75rem', color: '#94a3b8' }}>Evaluated Samples</div>
                    <div style={{ fontSize: '1.4rem', fontWeight: 700, color: '#ffffff' }}>
                      {benchmark.total_samples_evaluated ?? 0}
                    </div>
                  </div>
                  <div style={{ background: '#0f172a', padding: '1rem', borderRadius: '6px' }}>
                    <div style={{ fontSize: '0.75rem', color: '#94a3b8' }}>Univariate Z-Score Outliers</div>
                    <div style={{ fontSize: '1.4rem', fontWeight: 700, color: '#fbbf24' }}>
                      {benchmark.univariate_anomalies_detected ?? 0}
                    </div>
                  </div>
                  <div style={{ background: '#0f172a', padding: '1rem', borderRadius: '6px' }}>
                    <div style={{ fontSize: '0.75rem', color: '#94a3b8' }}>Isolation Forest Outliers</div>
                    <div style={{ fontSize: '1.4rem', fontWeight: 700, color: '#38bdf8' }}>
                      {benchmark.multivariate_anomalies_detected ?? 0}
                    </div>
                  </div>
                  <div style={{ background: '#0f172a', padding: '1rem', borderRadius: '6px' }}>
                    <div style={{ fontSize: '0.75rem', color: '#94a3b8' }}>Concordant (Overlap)</div>
                    <div style={{ fontSize: '1.4rem', fontWeight: 700, color: '#34d399' }}>
                      {benchmark.overlap_count ?? 0}
                    </div>
                  </div>
                </div>
              </div>

              <div
                style={{
                  background: '#1e293b',
                  borderRadius: '8px',
                  padding: '1.25rem',
                  border: '1px solid #334155',
                }}
              >
                <h4 style={{ margin: '0 0 0.5rem', color: '#ffffff', fontSize: '0.95rem' }}>
                  Key Architectural Insights
                </h4>
                <ul style={{ margin: 0, paddingLeft: '1.2rem', color: '#cbd5e1', fontSize: '0.85rem', lineHeight: 1.6 }}>
                  <li>
                    <strong>Univariate Z-Score Baseline:</strong> Operates independently on single metric distributions (e.g. daily revenue surge). Fast, highly interpretable, and forms our real-time production alerting core.
                  </li>
                  <li>
                    <strong>Multivariate Isolation Forest:</strong> Evaluates joint feature interactions (e.g. daily revenue, order count, and average order value simultaneously). Catches composite anomalies where individual metrics remain within normal standard deviation bounds.
                  </li>
                  <li>
                    <strong>Zero False Accusations:</strong> Both statistical and unsupervised models adhere to objective mathematical framing, omitting speculative or defamatory fraud accusations.
                  </li>
                </ul>
              </div>
            </div>
          ) : (
            <div style={{ padding: '2rem', textAlign: 'center', color: '#94a3b8' }}>
              <button
                onClick={loadBenchmark}
                style={{
                  padding: '8px 16px',
                  background: '#2563eb',
                  color: '#ffffff',
                  border: 'none',
                  borderRadius: '6px',
                  cursor: 'pointer',
                }}
              >
                Load Benchmark Results
              </button>
            </div>
          )}
        </div>
      )}

      {/* Triage / Acknowledgement Modal */}
      {triageAlert && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            background: 'rgba(0, 0, 0, 0.75)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000,
          }}
        >
          <div
            style={{
              background: '#1e293b',
              padding: '1.5rem',
              borderRadius: '8px',
              width: '100%',
              maxWidth: '500px',
              border: '1px solid #334155',
            }}
          >
            <h3 style={{ margin: '0 0 0.5rem', color: '#ffffff' }}>
              Triage Anomaly #{triageAlert.id}
            </h3>
            <p style={{ margin: '0 0 1rem', color: '#94a3b8', fontSize: '0.85rem' }}>
              {triageAlert.domain.toUpperCase()} &bull; {triageAlert.metric_name} ({triageAlert.entity_identifier})
            </p>

            <form onSubmit={handleAcknowledgeSubmit}>
              <div style={{ marginBottom: '1rem' }}>
                <label style={{ display: 'block', fontSize: '0.8rem', color: '#cbd5e1', marginBottom: '4px' }}>
                  Target Workflow Status:
                </label>
                <select
                  value={triageStatus}
                  onChange={(e) => setTriageStatus(e.target.value as AnomalyStatus)}
                  style={{
                    width: '100%',
                    background: '#0f172a',
                    color: '#ffffff',
                    border: '1px solid #334155',
                    padding: '8px',
                    borderRadius: '4px',
                  }}
                >
                  <option value="acknowledged">Acknowledged (Confirmed Outlier)</option>
                  <option value="resolved">Resolved (Corrective Action Taken)</option>
                  <option value="dismissed">Dismissed (Expected Business Event)</option>
                </select>
              </div>

              <div style={{ marginBottom: '1.25rem' }}>
                <label style={{ display: 'block', fontSize: '0.8rem', color: '#cbd5e1', marginBottom: '4px' }}>
                  Audit Investigation Notes:
                </label>
                <textarea
                  value={triageNotes}
                  onChange={(e) => setTriageNotes(e.target.value)}
                  placeholder="Record root cause or mitigation steps for the audit log..."
                  rows={3}
                  style={{
                    width: '100%',
                    background: '#0f172a',
                    color: '#ffffff',
                    border: '1px solid #334155',
                    padding: '8px',
                    borderRadius: '4px',
                    fontSize: '0.85rem',
                  }}
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px' }}>
                <button
                  type="button"
                  onClick={() => setTriageAlert(null)}
                  style={{
                    padding: '8px 14px',
                    background: '#334155',
                    color: '#ffffff',
                    border: 'none',
                    borderRadius: '4px',
                    cursor: 'pointer',
                  }}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={triageSubmitting}
                  style={{
                    padding: '8px 16px',
                    background: '#2563eb',
                    color: '#ffffff',
                    border: 'none',
                    borderRadius: '4px',
                    cursor: triageSubmitting ? 'not-allowed' : 'pointer',
                    fontWeight: 600,
                  }}
                >
                  {triageSubmitting ? 'Submitting...' : 'Save Triage Status'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
