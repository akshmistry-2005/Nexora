import React from 'react';
import { Calendar } from 'lucide-react';
import { DateRange } from '../../types/common';

export interface DateRangeSelectorProps {
  value: DateRange;
  onChange: (range: DateRange) => void;
  style?: React.CSSProperties;
}

export const DateRangeSelector: React.FC<DateRangeSelectorProps> = ({
  value,
  onChange,
  style = {},
}) => {
  const setPreset = (preset: '7d' | '30d' | '90d' | 'ytd') => {
    const end = new Date();
    const start = new Date();

    if (preset === '7d') {
      start.setDate(end.getDate() - 7);
    } else if (preset === '30d') {
      start.setDate(end.getDate() - 30);
    } else if (preset === '90d') {
      start.setDate(end.getDate() - 90);
    } else if (preset === 'ytd') {
      start.setMonth(0, 1);
    }

    onChange({
      startDate: start.toISOString().split('T')[0],
      endDate: end.toISOString().split('T')[0],
      preset,
    });
  };

  return (
    <div
      data-testid="date-range-selector"
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '0.5rem',
        background: 'var(--color-bg-surface)',
        border: '1px solid var(--color-border-default)',
        borderRadius: 'var(--radius-md)',
        padding: '0.25rem 0.5rem',
        fontSize: '0.8125rem',
        ...style,
      }}
    >
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '0.35rem',
          color: 'var(--color-text-muted)',
        }}
      >
        <Calendar size={14} />
      </div>

      <div style={{ display: 'flex', gap: '2px' }}>
        {(['7d', '30d', '90d', 'ytd'] as const).map((p) => {
          const isActive = value.preset === p;
          return (
            <button
              key={p}
              type="button"
              data-testid={`preset-${p}`}
              onClick={() => setPreset(p)}
              style={{
                background: isActive ? 'var(--color-primary)' : 'transparent',
                color: isActive ? '#ffffff' : 'var(--color-text-secondary)',
                border: 'none',
                borderRadius: 'var(--radius-sm)',
                padding: '2px 8px',
                fontSize: '0.75rem',
                fontWeight: isActive ? 600 : 400,
                cursor: 'pointer',
                transition: 'background var(--transition-fast)',
              }}
            >
              {p.toUpperCase()}
            </button>
          );
        })}
      </div>

      <div style={{ width: '1px', height: '14px', background: 'var(--color-border-default)' }} />

      <div style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
        <input
          type="date"
          data-testid="date-range-start"
          aria-label="Start date"
          value={value.startDate}
          onChange={(e) =>
            onChange({
              ...value,
              startDate: e.target.value,
              preset: 'custom',
            })
          }
          style={{
            background: 'var(--color-bg-surface-elevated)',
            border: '1px solid var(--color-border-subtle)',
            borderRadius: 'var(--radius-sm)',
            color: 'var(--color-text-secondary)',
            fontSize: '0.75rem',
            padding: '2px 4px',
          }}
        />
        <span style={{ color: 'var(--color-text-subtle)' }}>to</span>
        <input
          type="date"
          data-testid="date-range-end"
          aria-label="End date"
          value={value.endDate}
          onChange={(e) =>
            onChange({
              ...value,
              endDate: e.target.value,
              preset: 'custom',
            })
          }
          style={{
            background: 'var(--color-bg-surface-elevated)',
            border: '1px solid var(--color-border-subtle)',
            borderRadius: 'var(--radius-sm)',
            color: 'var(--color-text-secondary)',
            fontSize: '0.75rem',
            padding: '2px 4px',
          }}
        />
      </div>
    </div>
  );
};
