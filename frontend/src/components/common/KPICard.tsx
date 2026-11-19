import React, { useState } from 'react';
import { HelpCircle, TrendingDown, TrendingUp } from 'lucide-react';
import { SkeletonLoader } from './SkeletonLoader';

export interface KPICardProps {
  title: string;
  value: string | number;
  format?: 'currency' | 'percent' | 'number' | 'raw';
  trend?: {
    value: number; // e.g. 12.4 for +12.4%
    direction?: 'up' | 'down' | 'neutral';
    isPositive?: boolean; // if undefined, up is positive, down is negative
    period?: string; // e.g. "vs previous period"
  };
  subtitle?: string;
  tooltip?: string;
  loading?: boolean;
  empty?: boolean;
  style?: React.CSSProperties;
}

export const KPICard: React.FC<KPICardProps> = ({
  title,
  value,
  format = 'raw',
  trend,
  subtitle,
  tooltip,
  loading = false,
  empty = false,
  style = {},
}) => {
  const [showTooltip, setShowTooltip] = useState(false);

  const formatValue = (val: string | number): string => {
    if (typeof val !== 'number') return String(val);
    switch (format) {
      case 'currency':
        return new Intl.NumberFormat('en-US', {
          style: 'currency',
          currency: 'USD',
          maximumFractionDigits: 0,
        }).format(val);
      case 'percent':
        return `${val > 0 ? '+' : ''}${val.toFixed(1)}%`;
      case 'number':
        return new Intl.NumberFormat('en-US').format(val);
      case 'raw':
      default:
        return String(val);
    }
  };

  if (loading) {
    return (
      <div
        data-testid="kpi-card-loading"
        style={{
          background: 'var(--color-bg-surface)',
          borderRadius: 'var(--radius-lg)',
          border: '1px solid var(--color-border-subtle)',
          padding: '1.25rem',
          minWidth: '220px',
          ...style,
        }}
      >
        <SkeletonLoader variant="text" width="50%" height="16px" />
        <SkeletonLoader variant="text" width="75%" height="32px" style={{ margin: '0.75rem 0' }} />
        <SkeletonLoader variant="text" width="40%" height="14px" />
      </div>
    );
  }

  const isUp = trend?.direction ? trend.direction === 'up' : (trend?.value ?? 0) >= 0;
  const isPositive = trend?.isPositive !== undefined ? trend.isPositive : isUp;
  const trendColor = isPositive ? 'var(--color-success)' : 'var(--color-danger)';
  const trendBg = isPositive ? 'var(--color-success-muted)' : 'var(--color-danger-muted)';

  return (
    <div
      data-testid="kpi-card"
      style={{
        background: 'var(--color-bg-surface)',
        borderRadius: 'var(--radius-lg)',
        border: '1px solid var(--color-border-subtle)',
        padding: '1.25rem',
        minWidth: '220px',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'space-between',
        position: 'relative',
        transition: 'transform var(--transition-fast), border-color var(--transition-fast)',
        boxShadow: 'var(--shadow-sm)',
        ...style,
      }}
    >
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          marginBottom: '0.5rem',
        }}
      >
        <span
          style={{
            fontSize: '0.8125rem',
            fontWeight: 500,
            color: 'var(--color-text-muted)',
            textTransform: 'uppercase',
            letterSpacing: '0.04em',
          }}
        >
          {title}
        </span>
        {tooltip && (
          <div style={{ position: 'relative' }}>
            <button
              type="button"
              aria-label={`Metric info for ${title}`}
              onClick={() => setShowTooltip(!showTooltip)}
              onMouseEnter={() => setShowTooltip(true)}
              onMouseLeave={() => setShowTooltip(false)}
              style={{
                background: 'transparent',
                border: 'none',
                color: 'var(--color-text-subtle)',
                cursor: 'pointer',
                padding: '2px',
                display: 'flex',
                alignItems: 'center',
              }}
            >
              <HelpCircle size={15} />
            </button>
            {showTooltip && (
              <div
                role="tooltip"
                style={{
                  position: 'absolute',
                  top: '100%',
                  right: 0,
                  marginTop: '6px',
                  background: 'var(--color-bg-surface-elevated)',
                  border: '1px solid var(--color-border-default)',
                  borderRadius: 'var(--radius-md)',
                  padding: '0.5rem 0.75rem',
                  fontSize: '0.75rem',
                  color: 'var(--color-text-primary)',
                  boxShadow: 'var(--shadow-md)',
                  zIndex: 20,
                  width: '200px',
                  lineHeight: 1.4,
                }}
              >
                {tooltip}
              </div>
            )}
          </div>
        )}
      </div>

      <div style={{ margin: '0.25rem 0 0.5rem' }}>
        <span
          data-testid="kpi-value"
          style={{
            fontSize: '1.75rem',
            fontWeight: 700,
            color: empty ? 'var(--color-text-subtle)' : 'var(--color-text-primary)',
            letterSpacing: '-0.02em',
          }}
        >
          {empty ? '—' : formatValue(value)}
        </span>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap' }}>
        {trend && !empty && (
          <span
            data-testid="kpi-trend"
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '2px',
              fontSize: '0.75rem',
              fontWeight: 600,
              padding: '2px 6px',
              borderRadius: 'var(--radius-sm)',
              background: trendBg,
              color: trendColor,
            }}
          >
            {isUp ? <TrendingUp size={12} /> : <TrendingDown size={12} />}
            {Math.abs(trend.value)}%
          </span>
        )}
        <span style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>
          {trend?.period || subtitle || ''}
        </span>
      </div>
    </div>
  );
};
