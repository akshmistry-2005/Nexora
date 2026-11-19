import React from 'react';
import { RotateCcw } from 'lucide-react';
import { DateRangeSelector } from './DateRangeSelector';
import { DateRange } from '../../types/common';

export interface FilterOption {
  label: string;
  value: string | number;
}

export interface FilterBarProps {
  dateRange: DateRange;
  onDateRangeChange: (range: DateRange) => void;
  regions?: FilterOption[];
  selectedRegion?: string | number | null;
  onRegionChange?: (region: string | number | null) => void;
  categories?: FilterOption[];
  selectedCategory?: string | number | null;
  onCategoryChange?: (category: string | number | null) => void;
  onReset?: () => void;
  style?: React.CSSProperties;
}

export const FilterBar: React.FC<FilterBarProps> = ({
  dateRange,
  onDateRangeChange,
  regions = [],
  selectedRegion,
  onRegionChange,
  categories = [],
  selectedCategory,
  onCategoryChange,
  onReset,
  style = {},
}) => {
  return (
    <div
      data-testid="filter-bar"
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '0.75rem',
        padding: '0.75rem 1rem',
        background: 'var(--color-bg-surface)',
        borderRadius: 'var(--radius-lg)',
        border: '1px solid var(--color-border-subtle)',
        marginBottom: '1.25rem',
        ...style,
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flexWrap: 'wrap' }}>
        <DateRangeSelector value={dateRange} onChange={onDateRangeChange} />

        {regions.length > 0 && onRegionChange && (
          <select
            data-testid="region-filter-select"
            aria-label="Filter by region"
            value={selectedRegion ?? ''}
            onChange={(e) => onRegionChange(e.target.value === '' ? null : e.target.value)}
            style={{
              background: 'var(--color-bg-surface-elevated)',
              border: '1px solid var(--color-border-default)',
              borderRadius: 'var(--radius-md)',
              color: 'var(--color-text-secondary)',
              padding: '0.35rem 0.65rem',
              fontSize: '0.8125rem',
            }}
          >
            <option value="">All Regions</option>
            {regions.map((r) => (
              <option key={r.value} value={r.value}>
                {r.label}
              </option>
            ))}
          </select>
        )}

        {categories.length > 0 && onCategoryChange && (
          <select
            data-testid="category-filter-select"
            aria-label="Filter by category"
            value={selectedCategory ?? ''}
            onChange={(e) => onCategoryChange(e.target.value === '' ? null : e.target.value)}
            style={{
              background: 'var(--color-bg-surface-elevated)',
              border: '1px solid var(--color-border-default)',
              borderRadius: 'var(--radius-md)',
              color: 'var(--color-text-secondary)',
              padding: '0.35rem 0.65rem',
              fontSize: '0.8125rem',
            }}
          >
            <option value="">All Categories</option>
            {categories.map((c) => (
              <option key={c.value} value={c.value}>
                {c.label}
              </option>
            ))}
          </select>
        )}
      </div>

      {onReset && (
        <button
          type="button"
          data-testid="filter-reset-btn"
          onClick={onReset}
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '0.35rem',
            background: 'transparent',
            border: 'none',
            color: 'var(--color-text-muted)',
            fontSize: '0.8125rem',
            cursor: 'pointer',
            padding: '0.25rem 0.5rem',
            borderRadius: 'var(--radius-sm)',
            transition: 'color var(--transition-fast)',
          }}
        >
          <RotateCcw size={13} />
          Reset Filters
        </button>
      )}
    </div>
  );
};
