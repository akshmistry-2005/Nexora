import React, { useEffect, useState } from 'react';
import { Alert } from '../../components/common/Alert';
import { KPICard } from '../../components/common/KPICard';
import { statisticsService } from '../../services/statistics';
import { CorrelationMatrix, DescriptiveStats, HypothesisTest } from '../../types/statistics';

export const StatisticsPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'descriptive' | 'correlation' | 'hypothesis'>('descriptive');
  const [selectedField, setSelectedField] = useState<{ entity: string; field: string }>({
    entity: 'orders',
    field: 'total_amount',
  });

  const [stats, setStats] = useState<DescriptiveStats | null>(null);
  const [correlation, setCorrelation] = useState<CorrelationMatrix | null>(null);
  const [hypothesis, setHypothesis] = useState<HypothesisTest | null>(null);
  const [matrixType, setMatrixType] = useState<'pearson' | 'spearman'>('pearson');

  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadDescriptiveStats(selectedField.entity, selectedField.field);
  }, [selectedField]);

  useEffect(() => {
    if (activeTab === 'correlation' && !correlation) {
      loadCorrelation();
    } else if (activeTab === 'hypothesis' && !hypothesis) {
      loadHypothesis();
    }
  }, [activeTab, correlation, hypothesis]);

  const loadDescriptiveStats = async (entity: string, field: string) => {
    try {
      setLoading(true);
      setError(null);
      const res = await statisticsService.getDescriptiveStats(entity, field);
      setStats(res);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to compute descriptive statistics.');
    } finally {
      setLoading(false);
    }
  };

  const loadCorrelation = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await statisticsService.getCorrelationMatrix('orders');
      setCorrelation(res);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load correlation matrix.');
    } finally {
      setLoading(false);
    }
  };

  const loadHypothesis = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await statisticsService.getChannelComparison();
      setHypothesis(res);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to run hypothesis test.');
    } finally {
      setLoading(false);
    }
  };

  const maxBinCount = Math.max(...(stats?.histogram.map((b) => b.count) || [1]));

  return (
    <div data-testid="statistics-page">
      <div style={{ marginBottom: '1.25rem' }}>
        <h1
          style={{ margin: '0 0 0.25rem', fontSize: '1.625rem', fontWeight: 700, color: '#ffffff' }}
        >
          Statistical Analysis & Distribution Modeling
        </h1>
        <p style={{ margin: 0, color: 'var(--color-text-muted)', fontSize: '0.875rem' }}>
          Parametric and non-parametric tests, variance distributions, quartile spreads, and
          correlation matrices.
        </p>
      </div>

      {/* Mandatory Causation Disclaimer Alert (M11-T08) */}
      <div style={{ marginBottom: '1.25rem' }}>
        <Alert variant="warning" title="Statistical Assumption Notice">
          Correlation does not imply causation. High correlation coefficients indicate co-movement, not causal mechanisms. Inferential hypotheses enforce sample bounds (N ≥ 2).
        </Alert>
      </div>

      {error && (
        <div style={{ marginBottom: '1.25rem' }}>
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
          onClick={() => setActiveTab('descriptive')}
          style={{
            padding: '0.625rem 1.25rem',
            background: 'transparent',
            border: 'none',
            borderBottom: activeTab === 'descriptive' ? '2px solid var(--color-primary)' : '2px solid transparent',
            color: activeTab === 'descriptive' ? '#ffffff' : 'var(--color-text-muted)',
            fontWeight: 600,
            cursor: 'pointer',
          }}
        >
          Descriptive Statistics & Spread
        </button>
        <button
          onClick={() => setActiveTab('correlation')}
          style={{
            padding: '0.625rem 1.25rem',
            background: 'transparent',
            border: 'none',
            borderBottom: activeTab === 'correlation' ? '2px solid var(--color-primary)' : '2px solid transparent',
            color: activeTab === 'correlation' ? '#ffffff' : 'var(--color-text-muted)',
            fontWeight: 600,
            cursor: 'pointer',
          }}
        >
          Bivariate Correlation Matrices
        </button>
        <button
          onClick={() => setActiveTab('hypothesis')}
          style={{
            padding: '0.625rem 1.25rem',
            background: 'transparent',
            border: 'none',
            borderBottom: activeTab === 'hypothesis' ? '2px solid var(--color-primary)' : '2px solid transparent',
            color: activeTab === 'hypothesis' ? '#ffffff' : 'var(--color-text-muted)',
            fontWeight: 600,
            cursor: 'pointer',
          }}
        >
          Hypothesis Testing (Welch's t-Test)
        </button>
      </div>

      {/* Descriptive Statistics Tab */}
      {activeTab === 'descriptive' && (
        <div>
          {/* Dimension Selector */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '1rem',
              marginBottom: '1.25rem',
              background: 'var(--color-surface)',
              padding: '0.75rem 1rem',
              borderRadius: 'var(--radius-md)',
              border: '1px solid var(--color-border)',
            }}
          >
            <span style={{ fontSize: '0.875rem', fontWeight: 600, color: '#ffffff' }}>
              Select Analyzed Numerical Dimension:
            </span>
            <select
              value={`${selectedField.entity}.${selectedField.field}`}
              onChange={(e) => {
                const [entity, field] = e.target.value.split('.');
                setSelectedField({ entity, field });
              }}
              style={{
                padding: '0.375rem 0.75rem',
                borderRadius: 'var(--radius-sm)',
                border: '1px solid var(--color-border)',
                background: 'rgba(0, 0, 0, 0.3)',
                color: '#ffffff',
                fontSize: '0.85rem',
              }}
            >
              <option value="orders.total_amount">Order Net Revenue (orders.total_amount)</option>
              <option value="orders.subtotal_amount">Order Subtotal Amount (orders.subtotal_amount)</option>
              <option value="orders.discount_amount">Order Discount Amount (orders.discount_amount)</option>
              <option value="products.unit_price">Product Unit Price (products.unit_price)</option>
              <option value="products.unit_cost">Product Unit Cost (products.unit_cost)</option>
            </select>
            {loading && <span style={{ fontSize: '0.8rem', color: 'var(--color-primary-light)' }}>Computing...</span>}
          </div>

          {/* 4 Headline Parametric/Non-Parametric Cards */}
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
              gap: '1rem',
              marginBottom: '1.5rem',
            }}
          >
            <KPICard
              title="Sample Mean (x̄)"
              value={stats?.mean ?? 0}
              format="number"
              subtitle={`Std Dev: ±${stats?.std_dev ?? 0}`}
            />
            <KPICard
              title="Median (Q2 / 50th %ile)"
              value={stats?.median ?? 0}
              format="number"
              subtitle={`IQR Spread: ${stats?.iqr ?? 0}`}
            />
            <KPICard
              title="Distribution Skewness"
              value={stats?.skewness ?? 0}
              format="raw"
              subtitle={
                (stats?.skewness ?? 0) > 0.5
                  ? 'Right-skewed (positive)'
                  : (stats?.skewness ?? 0) < -0.5
                  ? 'Left-skewed (negative)'
                  : 'Approximately symmetric'
              }
            />
            <KPICard
              title="95% Confidence Interval"
              value={
                stats?.confidence_interval_95
                  ? `[${stats.confidence_interval_95[0]}, ${stats.confidence_interval_95[1]}]`
                  : '—'
              }
              subtitle={`Sample size: N = ${stats?.n ?? 0} (df = ${(stats?.n ?? 1) - 1})`}
            />
          </div>

          {/* Detailed Quartiles & Spread Metrics Table */}
          <div
            style={{
              background: 'var(--color-surface)',
              borderRadius: 'var(--radius-md)',
              border: '1px solid var(--color-border)',
              padding: '1.25rem',
              marginBottom: '1.5rem',
            }}
          >
            <h3 style={{ margin: '0 0 1rem', fontSize: '1.05rem', color: '#ffffff' }}>
              Parametric, Non-Parametric & Dispersion Scorecard
            </h3>
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
                gap: '1rem',
              }}
            >
              <div style={{ padding: '0.75rem', background: 'rgba(255, 255, 255, 0.03)', borderRadius: '6px' }}>
                <div style={{ fontSize: '0.75rem', color: 'var(--color-text-subtle)' }}>Observations (N)</div>
                <div style={{ fontSize: '1.1rem', fontWeight: 600, color: '#ffffff' }}>{stats?.n ?? '—'}</div>
                <div style={{ fontSize: '0.7rem', color: 'var(--color-text-muted)' }}>Excluded NaNs: {stats?.missing_count ?? 0}</div>
              </div>
              <div style={{ padding: '0.75rem', background: 'rgba(255, 255, 255, 0.03)', borderRadius: '6px' }}>
                <div style={{ fontSize: '0.75rem', color: 'var(--color-text-subtle)' }}>Sample Variance (s²)</div>
                <div style={{ fontSize: '1.1rem', fontWeight: 600, color: '#ffffff' }}>{stats?.variance ?? '—'}</div>
                <div style={{ fontSize: '0.7rem', color: 'var(--color-text-muted)' }}>Bessel corrected (ddof=1)</div>
              </div>
              <div style={{ padding: '0.75rem', background: 'rgba(255, 255, 255, 0.03)', borderRadius: '6px' }}>
                <div style={{ fontSize: '0.75rem', color: 'var(--color-text-subtle)' }}>Modal Frequency</div>
                <div style={{ fontSize: '1.1rem', fontWeight: 600, color: '#ffffff' }}>{stats?.mode ?? '—'}</div>
                <div style={{ fontSize: '0.7rem', color: 'var(--color-text-muted)' }}>Most recurring value</div>
              </div>
              <div style={{ padding: '0.75rem', background: 'rgba(255, 255, 255, 0.03)', borderRadius: '6px' }}>
                <div style={{ fontSize: '0.75rem', color: 'var(--color-text-subtle)' }}>Range (Min - Max)</div>
                <div style={{ fontSize: '1.1rem', fontWeight: 600, color: '#ffffff' }}>{stats ? `${stats.min} – ${stats.max}` : '—'}</div>
                <div style={{ fontSize: '0.7rem', color: 'var(--color-text-muted)' }}>Spread: {stats ? (stats.max - stats.min).toFixed(2) : '—'}</div>
              </div>
              <div style={{ padding: '0.75rem', background: 'rgba(255, 255, 255, 0.03)', borderRadius: '6px' }}>
                <div style={{ fontSize: '0.75rem', color: 'var(--color-text-subtle)' }}>Quartiles (Q1 – Q3)</div>
                <div style={{ fontSize: '1.1rem', fontWeight: 600, color: '#ffffff' }}>{stats ? `${stats.q1} – ${stats.q3}` : '—'}</div>
                <div style={{ fontSize: '0.7rem', color: 'var(--color-text-muted)' }}>IQR: {stats?.iqr ?? '—'}</div>
              </div>
              <div style={{ padding: '0.75rem', background: 'rgba(255, 255, 255, 0.03)', borderRadius: '6px' }}>
                <div style={{ fontSize: '0.75rem', color: 'var(--color-text-subtle)' }}>Excess Kurtosis</div>
                <div style={{ fontSize: '1.1rem', fontWeight: 600, color: '#ffffff' }}>{stats?.kurtosis ?? '—'}</div>
                <div style={{ fontSize: '0.7rem', color: 'var(--color-text-muted)' }}>Normal baseline = 0.0</div>
              </div>
            </div>
          </div>

          {/* Histogram Distribution Visual (M11-T06) */}
          <div
            style={{
              background: 'var(--color-surface)',
              borderRadius: 'var(--radius-md)',
              border: '1px solid var(--color-border)',
              padding: '1.25rem',
            }}
          >
            <h3 style={{ margin: '0 0 0.5rem', fontSize: '1.05rem', color: '#ffffff' }}>
              Sample Frequency Histogram (10-Bin Stratification)
            </h3>
            <p style={{ margin: '0 0 1.25rem', color: 'var(--color-text-muted)', fontSize: '0.8rem' }}>
              Empirical frequency distribution across interval buckets.
            </p>

            <div
              style={{
                display: 'flex',
                alignItems: 'flex-end',
                gap: '0.5rem',
                height: '180px',
                paddingTop: '1rem',
                borderBottom: '1px solid var(--color-border)',
                marginBottom: '0.5rem',
              }}
            >
              {stats?.histogram.map((bin, i) => {
                const heightPct = Math.round((bin.count / maxBinCount) * 100);
                return (
                  <div
                    key={`bin-${i}`}
                    style={{
                      flex: 1,
                      display: 'flex',
                      flexDirection: 'column',
                      alignItems: 'center',
                      height: '100%',
                      justifyContent: 'flex-end',
                    }}
                  >
                    <span style={{ fontSize: '0.7rem', color: 'var(--color-text-subtle)', marginBottom: '4px' }}>
                      {bin.count}
                    </span>
                    <div
                      style={{
                        width: '100%',
                        height: `${Math.max(4, heightPct)}%`,
                        background: 'var(--color-primary, #3182ce)',
                        borderRadius: '4px 4px 0 0',
                        opacity: 0.85,
                        transition: 'height 0.3s ease',
                      }}
                      title={`Range: [${bin.bin_start}, ${bin.bin_end}] | Count: ${bin.count}`}
                    />
                  </div>
                );
              })}
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.7rem', color: 'var(--color-text-subtle)' }}>
              <span>{stats?.min ?? 0}</span>
              <span>Distribution Bins</span>
              <span>{stats?.max ?? 0}</span>
            </div>
          </div>
        </div>
      )}

      {/* Correlation Matrix Tab (M11-T07) */}
      {activeTab === 'correlation' && (
        <div>
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              marginBottom: '1rem',
            }}
          >
            <div>
              <h2 style={{ margin: 0, fontSize: '1.2rem', color: '#ffffff' }}>
                Bivariate Correlation Matrices
              </h2>
              <p style={{ margin: '0.25rem 0 0', color: 'var(--color-text-muted)', fontSize: '0.8rem' }}>
                Sample Size: N = {correlation?.sample_size || 0} order records
              </p>
            </div>

            <div style={{ display: 'flex', gap: '0.5rem' }}>
              <button
                onClick={() => setMatrixType('pearson')}
                style={{
                  padding: '4px 12px',
                  fontSize: '0.8rem',
                  fontWeight: 600,
                  borderRadius: '4px',
                  border: '1px solid var(--color-border)',
                  background: matrixType === 'pearson' ? 'var(--color-primary)' : 'transparent',
                  color: '#ffffff',
                  cursor: 'pointer',
                }}
              >
                Pearson (r) Linear
              </button>
              <button
                onClick={() => setMatrixType('spearman')}
                style={{
                  padding: '4px 12px',
                  fontSize: '0.8rem',
                  fontWeight: 600,
                  borderRadius: '4px',
                  border: '1px solid var(--color-border)',
                  background: matrixType === 'spearman' ? 'var(--color-primary)' : 'transparent',
                  color: '#ffffff',
                  cursor: 'pointer',
                }}
              >
                Spearman (ρ) Monotonic Rank
              </button>
            </div>
          </div>

          <div
            style={{
              overflowX: 'auto',
              background: 'var(--color-surface)',
              borderRadius: 'var(--radius-md)',
              border: '1px solid var(--color-border)',
              padding: '1rem',
            }}
          >
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'center' }}>
              <thead>
                <tr>
                  <th style={{ padding: '0.75rem', textAlign: 'left', color: 'var(--color-text-muted)', fontSize: '0.85rem' }}>
                    Variables
                  </th>
                  {correlation?.variables.map((v) => (
                    <th key={v} style={{ padding: '0.75rem', color: '#ffffff', fontSize: '0.85rem', fontWeight: 600 }}>
                      {v}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {correlation?.variables.map((v1, rowIdx) => (
                  <tr key={v1} style={{ borderTop: '1px solid var(--color-border-subtle)' }}>
                    <td style={{ padding: '0.75rem', textAlign: 'left', fontWeight: 600, color: '#ffffff', fontSize: '0.85rem' }}>
                      {v1}
                    </td>
                    {correlation.variables.map((_, colIdx) => {
                      const coeff =
                        matrixType === 'pearson'
                          ? correlation.pearson_matrix[rowIdx][colIdx]
                          : correlation.spearman_matrix[rowIdx][colIdx];
                      const pVal = correlation.p_values[rowIdx][colIdx];

                      const isDiag = rowIdx === colIdx;
                      let bg = 'transparent';
                      if (!isDiag && Math.abs(coeff) > 0.7) {
                        bg = coeff > 0 ? 'rgba(72, 187, 120, 0.2)' : 'rgba(239, 68, 68, 0.2)';
                      } else if (!isDiag && Math.abs(coeff) > 0.3) {
                        bg = coeff > 0 ? 'rgba(72, 187, 120, 0.1)' : 'rgba(239, 68, 68, 0.1)';
                      }

                      return (
                        <td
                          key={`cell-${rowIdx}-${colIdx}`}
                          style={{
                            padding: '0.75rem',
                            background: bg,
                            fontSize: '0.85rem',
                            fontWeight: isDiag ? 700 : 500,
                            color: isDiag ? 'var(--color-primary-light)' : '#ffffff',
                          }}
                        >
                          <div>{coeff.toFixed(3)}</div>
                          {!isDiag && (
                            <div style={{ fontSize: '0.65rem', color: 'var(--color-text-subtle)' }}>
                              p={pVal < 0.001 ? '<0.001' : pVal.toFixed(3)}
                            </div>
                          )}
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Hypothesis Testing Tab (M11-T09) */}
      {activeTab === 'hypothesis' && (
        <div>
          <div style={{ marginBottom: '1rem' }}>
            <h2 style={{ margin: '0 0 0.25rem', fontSize: '1.2rem', color: '#ffffff' }}>
              Two-Sample Inferential Hypothesis Testing
            </h2>
            <p style={{ margin: 0, color: 'var(--color-text-muted)', fontSize: '0.8rem' }}>
              Welch's t-test comparing population means without assuming equal variances (Welch-Satterthwaite df).
            </p>
          </div>

          {hypothesis && (
            <div
              style={{
                background: 'var(--color-surface)',
                borderRadius: 'var(--radius-md)',
                border: '1px solid var(--color-border)',
                padding: '1.25rem',
              }}
            >
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  marginBottom: '1.25rem',
                  borderBottom: '1px solid var(--color-border)',
                  paddingBottom: '0.75rem',
                }}
              >
                <div>
                  <h3 style={{ margin: 0, fontSize: '1.1rem', color: '#ffffff' }}>
                    {hypothesis.test_name}
                  </h3>
                  <div style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)' }}>
                    Hypothesis test between '{hypothesis.group_a_name}' vs '{hypothesis.group_b_name}'
                  </div>
                </div>

                <span
                  style={{
                    padding: '4px 12px',
                    borderRadius: '4px',
                    fontSize: '0.75rem',
                    fontWeight: 700,
                    textTransform: 'uppercase',
                    background: hypothesis.significant ? 'rgba(72, 187, 120, 0.2)' : 'rgba(255, 255, 255, 0.08)',
                    color: hypothesis.significant ? '#48bb78' : 'var(--color-text-subtle)',
                  }}
                >
                  {hypothesis.significant ? 'Statistically Significant (p < 0.05)' : 'Not Significant (p ≥ 0.05)'}
                </span>
              </div>

              {/* Group Comparison Details */}
              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
                  gap: '1rem',
                  marginBottom: '1.25rem',
                }}
              >
                <div style={{ padding: '1rem', background: 'rgba(255, 255, 255, 0.03)', borderRadius: '6px' }}>
                  <div style={{ fontWeight: 600, color: '#ffffff', marginBottom: '0.5rem' }}>{hypothesis.group_a_name}</div>
                  <div style={{ fontSize: '0.85rem', color: 'var(--color-text-muted)' }}>Sample Size: N = {hypothesis.group_a_n}</div>
                  <div style={{ fontSize: '1rem', fontWeight: 600, color: '#ffffff', marginTop: '0.25rem' }}>Mean: ${hypothesis.group_a_mean.toLocaleString()}</div>
                  <div style={{ fontSize: '0.8rem', color: 'var(--color-text-subtle)' }}>Std Dev: ±${hypothesis.group_a_std.toLocaleString()}</div>
                </div>

                <div style={{ padding: '1rem', background: 'rgba(255, 255, 255, 0.03)', borderRadius: '6px' }}>
                  <div style={{ fontWeight: 600, color: '#ffffff', marginBottom: '0.5rem' }}>{hypothesis.group_b_name}</div>
                  <div style={{ fontSize: '0.85rem', color: 'var(--color-text-muted)' }}>Sample Size: N = {hypothesis.group_b_n}</div>
                  <div style={{ fontSize: '1rem', fontWeight: 600, color: '#ffffff', marginTop: '0.25rem' }}>Mean: ${hypothesis.group_b_mean.toLocaleString()}</div>
                  <div style={{ fontSize: '0.8rem', color: 'var(--color-text-subtle)' }}>Std Dev: ±${hypothesis.group_b_std.toLocaleString()}</div>
                </div>
              </div>

              {/* Test Statistics Output */}
              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
                  gap: '1rem',
                  marginBottom: '1.25rem',
                  background: 'rgba(0, 0, 0, 0.2)',
                  padding: '1rem',
                  borderRadius: '6px',
                }}
              >
                <div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--color-text-subtle)' }}>t-Statistic</div>
                  <div style={{ fontSize: '1.25rem', fontWeight: 700, color: '#ffffff' }}>{hypothesis.t_statistic.toFixed(3)}</div>
                </div>
                <div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--color-text-subtle)' }}>p-Value</div>
                  <div style={{ fontSize: '1.25rem', fontWeight: 700, color: hypothesis.significant ? '#48bb78' : '#ffffff' }}>
                    {hypothesis.p_value < 0.0001 ? '< 0.0001' : hypothesis.p_value.toFixed(4)}
                  </div>
                </div>
                <div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--color-text-subtle)' }}>Degrees of Freedom (ν)</div>
                  <div style={{ fontSize: '1.25rem', fontWeight: 700, color: '#ffffff' }}>{hypothesis.degrees_of_freedom.toFixed(1)}</div>
                </div>
                <div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--color-text-subtle)' }}>Cohen's d (Effect Size)</div>
                  <div style={{ fontSize: '1.25rem', fontWeight: 700, color: '#ffffff' }}>{hypothesis.effect_size_cohens_d.toFixed(3)}</div>
                </div>
              </div>

              {/* Plain Language Interpretation */}
              <div
                style={{
                  padding: '1rem',
                  background: 'rgba(255, 255, 255, 0.05)',
                  borderRadius: '6px',
                  borderLeft: '4px solid var(--color-primary)',
                }}
              >
                <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--color-primary-light)', marginBottom: '0.25rem' }}>
                  Plain-Language Statistical Interpretation:
                </div>
                <div style={{ fontSize: '0.875rem', color: '#ffffff', lineHeight: 1.5 }}>
                  {hypothesis.interpretation}
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
