import { Component, ErrorInfo, ReactNode } from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    console.error('Unhandled React Error in Component Tree:', error, errorInfo);
  }

  handleReset = (): void => {
    this.setState({ hasError: false, error: null });
  };

  render(): ReactNode {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <div
          data-testid="error-boundary-fallback"
          role="alert"
          style={{
            padding: '2rem',
            margin: '1.5rem',
            borderRadius: 'var(--radius-lg)',
            background: 'var(--color-bg-surface)',
            border: '1px solid var(--color-border-default)',
            textAlign: 'center',
            color: 'var(--color-text-secondary)',
          }}
        >
          <div
            style={{
              display: 'inline-flex',
              padding: '1rem',
              borderRadius: 'var(--radius-full)',
              background: 'var(--color-danger-muted)',
              color: 'var(--color-danger)',
              marginBottom: '1rem',
            }}
          >
            <AlertTriangle size={32} />
          </div>
          <h2 style={{ color: 'var(--color-text-primary)', margin: '0 0 0.5rem' }}>
            Something went wrong rendering this view
          </h2>
          <p
            style={{
              color: 'var(--color-text-muted)',
              fontSize: '0.875rem',
              maxWidth: '500px',
              margin: '0 auto 1.5rem',
            }}
          >
            {this.state.error?.message ||
              'An unexpected rendering issue occurred. You can retry safely without losing your session.'}
          </p>
          <button
            type="button"
            onClick={this.handleReset}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '0.5rem',
              background: 'var(--color-primary)',
              color: '#ffffff',
              border: 'none',
              borderRadius: 'var(--radius-md)',
              padding: '0.5rem 1.25rem',
              fontWeight: 500,
              fontSize: '0.875rem',
              cursor: 'pointer',
            }}
          >
            <RefreshCw size={16} />
            Try again
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}
