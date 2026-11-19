import React, { ReactNode } from 'react';
import { AlertCircle, CheckCircle, Info, TriangleAlert, X } from 'lucide-react';

export type AlertVariant = 'info' | 'success' | 'warning' | 'error';

export interface AlertProps {
  variant?: AlertVariant;
  title?: string;
  children: ReactNode;
  onClose?: () => void;
  style?: React.CSSProperties;
}

export const Alert: React.FC<AlertProps> = ({
  variant = 'info',
  title,
  children,
  onClose,
  style = {},
}) => {
  const getVariantConfig = () => {
    switch (variant) {
      case 'success':
        return {
          bg: 'var(--color-success-muted)',
          border: 'rgba(16, 185, 129, 0.4)',
          text: '#a7f3d0',
          icon: <CheckCircle size={18} color="var(--color-success)" />,
        };
      case 'warning':
        return {
          bg: 'var(--color-warning-muted)',
          border: 'rgba(245, 158, 11, 0.4)',
          text: '#fde68a',
          icon: <TriangleAlert size={18} color="var(--color-warning)" />,
        };
      case 'error':
        return {
          bg: 'var(--color-danger-muted)',
          border: 'rgba(239, 68, 68, 0.4)',
          text: '#fca5a5',
          icon: <AlertCircle size={18} color="var(--color-danger)" />,
        };
      case 'info':
      default:
        return {
          bg: 'var(--color-primary-muted)',
          border: 'rgba(59, 130, 246, 0.4)',
          text: '#bfdbfe',
          icon: <Info size={18} color="var(--color-primary)" />,
        };
    }
  };

  const config = getVariantConfig();

  return (
    <div
      data-testid={`alert-${variant}`}
      role={variant === 'error' ? 'alert' : 'status'}
      style={{
        display: 'flex',
        alignItems: 'flex-start',
        gap: '0.75rem',
        padding: '0.875rem 1rem',
        borderRadius: 'var(--radius-md)',
        background: config.bg,
        border: `1px solid ${config.border}`,
        color: config.text,
        fontSize: '0.875rem',
        ...style,
      }}
    >
      <div style={{ flexShrink: 0, marginTop: '2px' }}>{config.icon}</div>
      <div style={{ flex: 1 }}>
        {title && (
          <div
            style={{
              fontWeight: 600,
              marginBottom: '0.25rem',
              color: 'var(--color-text-primary)',
            }}
          >
            {title}
          </div>
        )}
        <div>{children}</div>
      </div>
      {onClose && (
        <button
          type="button"
          onClick={onClose}
          aria-label="Close alert"
          style={{
            background: 'transparent',
            border: 'none',
            color: 'inherit',
            cursor: 'pointer',
            padding: '2px',
            borderRadius: 'var(--radius-sm)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            opacity: 0.7,
            transition: 'opacity var(--transition-fast)',
          }}
        >
          <X size={16} />
        </button>
      )}
    </div>
  );
};
