import React, { useId, useMemo, useState } from 'react';
import {
  ArrowDown,
  ArrowUp,
  ArrowUpDown,
  ChevronLeft,
  ChevronRight,
  Download,
  Search,
} from 'lucide-react';
import { EmptyState } from './EmptyState';
import { SkeletonLoader } from './SkeletonLoader';
import { SortDirection } from '../../types/common';

export interface Column<T> {
  key: string;
  header: string;
  render?: (row: T, index: number) => React.ReactNode;
  sortable?: boolean;
  align?: 'left' | 'center' | 'right';
  width?: string;
}

export interface DataTableProps<T> {
  data: T[];
  columns: Column<T>[];
  keyExtractor: (row: T) => string | number;
  loading?: boolean;
  emptyMessage?: string;
  searchPlaceholder?: string;
  enableSearch?: boolean;
  enableSelection?: boolean;
  onSelectionChange?: (selectedRows: T[]) => void;
  onExport?: () => void;
  initialPageSize?: number;
  pageSizeOptions?: number[];
  style?: React.CSSProperties;
}

export function DataTable<T extends Record<string, unknown>>({
  data = [],
  columns,
  keyExtractor,
  loading = false,
  emptyMessage = 'No matching records found in this view',
  searchPlaceholder = 'Search records...',
  enableSearch = true,
  enableSelection = false,
  onSelectionChange,
  onExport,
  initialPageSize = 10,
  pageSizeOptions = [5, 10, 25, 50],
  style = {},
}: DataTableProps<T>) {
  const searchInputId = useId();
  const [searchQuery, setSearchQuery] = useState('');
  const [sortKey, setSortKey] = useState<string | null>(null);
  const [sortDir, setSortDir] = useState<SortDirection>('asc');
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(initialPageSize);
  const [selectedKeys, setSelectedKeys] = useState<Set<string | number>>(new Set());

  // 1. Filter
  const filteredData = useMemo(() => {
    const safeData = data ?? [];
    if (!searchQuery.trim()) return safeData;
    const q = searchQuery.toLowerCase();
    return safeData.filter((row) =>
      Object.values(row).some((val) => {
        if (val === null || val === undefined) return false;
        return String(val).toLowerCase().includes(q);
      }),
    );
  }, [data, searchQuery]);

  // 2. Sort
  const sortedData = useMemo(() => {
    if (!sortKey) return filteredData;
    return [...filteredData].sort((a, b) => {
      const valA = a[sortKey];
      const valB = b[sortKey];

      if (valA === valB) return 0;
      if (valA === null || valA === undefined) return 1;
      if (valB === null || valB === undefined) return -1;

      if (typeof valA === 'number' && typeof valB === 'number') {
        return sortDir === 'asc' ? valA - valB : valB - valA;
      }
      const strA = String(valA).toLowerCase();
      const strB = String(valB).toLowerCase();
      return sortDir === 'asc' ? strA.localeCompare(strB) : strB.localeCompare(strA);
    });
  }, [filteredData, sortKey, sortDir]);

  // 3. Paginate
  const totalItems = sortedData.length;
  const totalPages = Math.max(1, Math.ceil(totalItems / pageSize));
  const activePage = Math.min(currentPage, totalPages);
  const startIndex = (activePage - 1) * pageSize;
  const paginatedData = sortedData.slice(startIndex, startIndex + pageSize);

  const handleSort = (key: string) => {
    if (sortKey === key) {
      if (sortDir === 'asc') {
        setSortDir('desc');
      } else {
        setSortKey(null);
        setSortDir('asc');
      }
    } else {
      setSortKey(key);
      setSortDir('asc');
    }
  };

  const handleSelectAll = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.checked) {
      const allKeys = new Set(paginatedData.map(keyExtractor));
      setSelectedKeys(allKeys);
      onSelectionChange?.(paginatedData);
    } else {
      setSelectedKeys(new Set());
      onSelectionChange?.([]);
    }
  };

  const handleSelectRow = (row: T) => {
    const key = keyExtractor(row);
    const newSelected = new Set(selectedKeys);
    if (newSelected.has(key)) {
      newSelected.delete(key);
    } else {
      newSelected.add(key);
    }
    setSelectedKeys(newSelected);
    const selectedRows = data.filter((item) => newSelected.has(keyExtractor(item)));
    onSelectionChange?.(selectedRows);
  };

  return (
    <div
      data-testid="data-table-container"
      style={{
        background: 'var(--color-bg-surface)',
        borderRadius: 'var(--radius-lg)',
        border: '1px solid var(--color-border-subtle)',
        overflow: 'hidden',
        boxShadow: 'var(--shadow-sm)',
        display: 'flex',
        flexDirection: 'column',
        ...style,
      }}
    >
      {/* Table Toolbar */}
      {(enableSearch || onExport) && (
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '1rem',
            borderBottom: '1px solid var(--color-border-subtle)',
            gap: '1rem',
            flexWrap: 'wrap',
          }}
        >
          {enableSearch && (
            <div
              style={{
                position: 'relative',
                display: 'flex',
                alignItems: 'center',
                maxWidth: '320px',
                width: '100%',
              }}
            >
              <label
                htmlFor={searchInputId}
                style={{
                  position: 'absolute',
                  width: 1,
                  height: 1,
                  padding: 0,
                  margin: -1,
                  overflow: 'hidden',
                  clip: 'rect(0, 0, 0, 0)',
                  whiteSpace: 'nowrap',
                  border: 0,
                }}
              >
                {searchPlaceholder}
              </label>
              <Search
                size={16}
                aria-hidden="true"
                style={{
                  position: 'absolute',
                  left: '10px',
                  color: 'var(--color-text-muted)',
                  pointerEvents: 'none',
                }}
              />
              <input
                id={searchInputId}
                type="text"
                data-testid="data-table-search"
                value={searchQuery}
                onChange={(e) => {
                  setSearchQuery(e.target.value);
                  setCurrentPage(1);
                }}
                placeholder={searchPlaceholder}
                style={{
                  width: '100%',
                  background: 'var(--color-bg-surface-elevated)',
                  border: '1px solid var(--color-border-default)',
                  borderRadius: 'var(--radius-md)',
                  padding: '0.45rem 0.75rem 0.45rem 2rem',
                  color: 'var(--color-text-primary)',
                  fontSize: '0.875rem',
                }}
              />
            </div>
          )}

          {onExport && (
            <button
              type="button"
              data-testid="data-table-export-btn"
              onClick={onExport}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '0.4rem',
                background: 'var(--color-bg-surface-elevated)',
                border: '1px solid var(--color-border-default)',
                borderRadius: 'var(--radius-md)',
                color: 'var(--color-text-secondary)',
                padding: '0.45rem 0.85rem',
                fontSize: '0.8125rem',
                fontWeight: 500,
                cursor: 'pointer',
                transition: 'background var(--transition-fast)',
              }}
            >
              <Download size={14} />
              Export
            </button>
          )}
        </div>
      )}

      {/* Main Table Content */}
      <div style={{ overflowX: 'auto', width: '100%' }}>
        <table
          data-testid="data-table"
          role="table"
          style={{
            width: '100%',
            borderCollapse: 'collapse',
            textAlign: 'left',
            fontSize: '0.875rem',
          }}
        >
          <thead>
            <tr
              style={{
                borderBottom: '1px solid var(--color-border-subtle)',
                background: 'rgba(255, 255, 255, 0.02)',
              }}
            >
              {enableSelection && (
                <th style={{ width: '40px', padding: '0.75rem 1rem' }}>
                  <input
                    type="checkbox"
                    aria-label="Select all rows on current page"
                    checked={
                      paginatedData.length > 0 &&
                      paginatedData.every((r) => selectedKeys.has(keyExtractor(r)))
                    }
                    onChange={handleSelectAll}
                  />
                </th>
              )}
              {columns.map((col) => (
                <th
                  key={col.key}
                  style={{
                    padding: '0.75rem 1rem',
                    color: 'var(--color-text-muted)',
                    fontWeight: 600,
                    fontSize: '0.75rem',
                    textTransform: 'uppercase',
                    letterSpacing: '0.04em',
                    textAlign: col.align || 'left',
                    width: col.width,
                    userSelect: 'none',
                  }}
                >
                  {col.sortable ? (
                    <button
                      type="button"
                      data-testid={`sort-${col.key}`}
                      onClick={() => handleSort(col.key)}
                      style={{
                        background: 'transparent',
                        border: 'none',
                        color: 'inherit',
                        font: 'inherit',
                        textTransform: 'inherit',
                        letterSpacing: 'inherit',
                        cursor: 'pointer',
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: '0.35rem',
                        padding: 0,
                      }}
                    >
                      {col.header}
                      {sortKey === col.key ? (
                        sortDir === 'asc' ? (
                          <ArrowUp size={14} color="var(--color-primary)" />
                        ) : (
                          <ArrowDown size={14} color="var(--color-primary)" />
                        )
                      ) : (
                        <ArrowUpDown size={13} style={{ opacity: 0.4 }} />
                      )}
                    </button>
                  ) : (
                    col.header
                  )}
                </th>
              ))}
            </tr>
          </thead>

          <tbody>
            {loading ? (
              Array.from({ length: pageSize }).map((_, i) => (
                <tr key={i} style={{ borderBottom: '1px solid var(--color-border-subtle)' }}>
                  <td
                    colSpan={columns.length + (enableSelection ? 1 : 0)}
                    style={{ padding: '0.75rem 1rem' }}
                  >
                    <SkeletonLoader variant="text" width="90%" height="20px" />
                  </td>
                </tr>
              ))
            ) : paginatedData.length === 0 ? (
              <tr>
                <td
                  colSpan={columns.length + (enableSelection ? 1 : 0)}
                  style={{ padding: '2rem 1rem' }}
                >
                  <EmptyState description={emptyMessage} />
                </td>
              </tr>
            ) : (
              paginatedData.map((row, idx) => {
                const rowKey = keyExtractor(row);
                const isSelected = selectedKeys.has(rowKey);
                return (
                  <tr
                    key={rowKey}
                    data-testid="table-row"
                    style={{
                      borderBottom: '1px solid var(--color-border-subtle)',
                      background: isSelected ? 'var(--color-primary-muted)' : 'transparent',
                      transition: 'background var(--transition-fast)',
                    }}
                  >
                    {enableSelection && (
                      <td style={{ padding: '0.75rem 1rem' }}>
                        <input
                          type="checkbox"
                          checked={isSelected}
                          aria-label={`Select row ${rowKey}`}
                          onChange={() => handleSelectRow(row)}
                        />
                      </td>
                    )}
                    {columns.map((col) => (
                      <td
                        key={col.key}
                        style={{
                          padding: '0.75rem 1rem',
                          textAlign: col.align || 'left',
                          color: 'var(--color-text-secondary)',
                        }}
                      >
                        {col.render
                          ? col.render(row, startIndex + idx)
                          : String(row[col.key] ?? '')}
                      </td>
                    ))}
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination Bar */}
      {!loading && totalItems > 0 && (
        <div
          data-testid="data-table-pagination"
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '0.75rem 1rem',
            borderTop: '1px solid var(--color-border-subtle)',
            fontSize: '0.8125rem',
            color: 'var(--color-text-muted)',
            flexWrap: 'wrap',
            gap: '0.75rem',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <span>
              Showing <strong>{startIndex + 1}</strong> to{' '}
              <strong>{Math.min(startIndex + pageSize, totalItems)}</strong> of{' '}
              <strong>{totalItems}</strong> entries
            </span>
            <select
              data-testid="page-size-select"
              value={pageSize}
              onChange={(e) => {
                setPageSize(Number(e.target.value));
                setCurrentPage(1);
              }}
              style={{
                background: 'var(--color-bg-surface-elevated)',
                border: '1px solid var(--color-border-default)',
                borderRadius: 'var(--radius-sm)',
                color: 'var(--color-text-secondary)',
                padding: '2px 6px',
                fontSize: '0.75rem',
              }}
            >
              {pageSizeOptions.map((opt) => (
                <option key={opt} value={opt}>
                  {opt} / page
                </option>
              ))}
            </select>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
            <button
              type="button"
              data-testid="pagination-prev"
              disabled={activePage <= 1}
              onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
              style={{
                background: 'transparent',
                border: '1px solid var(--color-border-default)',
                borderRadius: 'var(--radius-sm)',
                color: activePage <= 1 ? 'var(--color-text-subtle)' : 'var(--color-text-secondary)',
                padding: '4px 8px',
                cursor: activePage <= 1 ? 'not-allowed' : 'pointer',
                display: 'flex',
                alignItems: 'center',
              }}
            >
              <ChevronLeft size={14} />
            </button>
            <span style={{ padding: '0 0.5rem' }}>
              Page <strong>{activePage}</strong> of <strong>{totalPages}</strong>
            </span>
            <button
              type="button"
              data-testid="pagination-next"
              disabled={activePage >= totalPages}
              onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
              style={{
                background: 'transparent',
                border: '1px solid var(--color-border-default)',
                borderRadius: 'var(--radius-sm)',
                color:
                  activePage >= totalPages
                    ? 'var(--color-text-subtle)'
                    : 'var(--color-text-secondary)',
                padding: '4px 8px',
                cursor: activePage >= totalPages ? 'not-allowed' : 'pointer',
                display: 'flex',
                alignItems: 'center',
              }}
            >
              <ChevronRight size={14} />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
