import React from 'react';

export interface SkeletonLoaderProps {
  variant?: 'card' | 'text' | 'table-row' | 'chart' | 'circle';
  count?: number;
  height?: string | number;
  width?: string | number;
  className?: string;
  style?: React.CSSProperties;
}

export const SkeletonLoader: React.FC<SkeletonLoaderProps> = ({
  variant = 'text',
  count = 1,
  height,
  width,
  style = {},
}) => {
  const getVariantStyles = (): React.CSSProperties => {
    switch (variant) {
      case 'card':
        return {
          height: height || '140px',
          width: width || '100%',
          borderRadius: 'var(--radius-lg)',
        };
      case 'chart':
        return {
          height: height || '280px',
          width: width || '100%',
          borderRadius: 'var(--radius-lg)',
        };
      case 'circle':
        return {
          height: height || '40px',
          width: width || '40px',
          borderRadius: 'var(--radius-full)',
        };
      case 'table-row':
        return {
          height: height || '48px',
          width: width || '100%',
          borderRadius: 'var(--radius-sm)',
          marginBottom: '8px',
        };
      case 'text':
      default:
        return {
          height: height || '18px',
          width: width || '80%',
          borderRadius: 'var(--radius-sm)',
          marginBottom: '8px',
        };
    }
  };

  const items = Array.from({ length: count });

  return (
    <div data-testid="skeleton-loader" aria-busy="true" aria-label="Loading content...">
      {items.map((_, index) => (
        <div
          key={index}
          className="skeleton-shimmer"
          style={{
            ...getVariantStyles(),
            ...style,
          }}
        />
      ))}
    </div>
  );
};
