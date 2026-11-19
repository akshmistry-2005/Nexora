import React, { useEffect, useState } from 'react';
import { KeyRound, LogOut, Menu, Sparkles, UserCheck } from 'lucide-react';
import { useAuth } from '../../hooks/useAuth';
import { BreadcrumbItem } from '../../types/navigation';
import { Breadcrumbs } from './Breadcrumbs';

export interface TopBarProps {
  breadcrumbs: BreadcrumbItem[];
  onToggleSidebarMobile: () => void;
  onOpenDemoSelector: () => void;
  onOpenOwnerLogin: () => void;
}

export const TopBar: React.FC<TopBarProps> = ({
  breadcrumbs,
  onToggleSidebarMobile,
  onOpenDemoSelector,
  onOpenOwnerLogin,
}) => {
  const { role, isOwner, logout } = useAuth();
  const [backendHealthy, setBackendHealthy] = useState<boolean | null>(null);

  useEffect(() => {
    const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';
    fetch(`${apiBaseUrl}/api/v1/health`)
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => setBackendHealthy(data?.status === 'healthy'))
      .catch(() => setBackendHealthy(false));
  }, []);

  const getRoleBadgeConfig = () => {
    if (isOwner || role === 'owner') {
      return {
        label: 'Platform Owner',
        bg: 'rgba(245, 158, 11, 0.15)',
        border: 'rgba(245, 158, 11, 0.4)',
        color: '#fbbf24',
      };
    }
    switch (role) {
      case 'executive':
        return {
          label: 'Executive (Demo)',
          bg: 'rgba(6, 182, 212, 0.15)',
          border: 'rgba(6, 182, 212, 0.4)',
          color: '#22d3ee',
        };
      case 'department_manager':
        return {
          label: 'Dept Manager (Demo)',
          bg: 'rgba(59, 130, 246, 0.15)',
          border: 'rgba(59, 130, 246, 0.4)',
          color: '#60a5fa',
        };
      case 'data_analyst':
        return {
          label: 'Data Analyst (Demo)',
          bg: 'rgba(16, 185, 129, 0.15)',
          border: 'rgba(16, 185, 129, 0.4)',
          color: '#34d399',
        };
      case 'data_scientist':
        return {
          label: 'Data Scientist (Demo)',
          bg: 'rgba(139, 92, 246, 0.15)',
          border: 'rgba(139, 92, 246, 0.4)',
          color: '#a78bfa',
        };
      case 'general_viewer':
      default:
        return {
          label: 'General Viewer (Demo)',
          bg: 'rgba(148, 163, 184, 0.15)',
          border: 'rgba(148, 163, 184, 0.4)',
          color: '#cbd5e1',
        };
    }
  };

  const badgeConfig = getRoleBadgeConfig();

  return (
    <header
      data-testid="app-topbar"
      style={{
        height: '64px',
        background: 'var(--color-bg-surface)',
        borderBottom: '1px solid var(--color-border-subtle)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0 1.5rem',
        boxSizing: 'border-box',
        position: 'sticky',
        top: 0,
        zIndex: 20,
      }}
    >
      {/* Left: Mobile hamburger & breadcrumbs */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
        <button
          type="button"
          data-testid="mobile-sidebar-toggle"
          onClick={onToggleSidebarMobile}
          aria-label="Toggle navigation menu"
          style={{
            display: 'none', // shown via media query or tablet layout
            background: 'transparent',
            border: 'none',
            color: 'var(--color-text-secondary)',
            cursor: 'pointer',
            padding: '4px',
          }}
        >
          <Menu size={20} />
        </button>

        <Breadcrumbs items={breadcrumbs} />
      </div>

      {/* Right: Status pill, Role selector, and Owner controls */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
        {/* Backend health indicator */}
        <div
          data-testid="backend-health-pill"
          title={backendHealthy ? 'Backend API & PostgreSQL connected' : 'Connecting to backend...'}
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '0.35rem',
            padding: '2px 8px',
            borderRadius: 'var(--radius-full)',
            background: backendHealthy
              ? 'var(--color-success-muted)'
              : 'var(--color-warning-muted)',
            border: `1px solid ${backendHealthy ? 'rgba(16, 185, 129, 0.3)' : 'rgba(245, 158, 11, 0.3)'}`,
            fontSize: '0.6875rem',
            color: backendHealthy ? 'var(--color-success)' : 'var(--color-warning)',
          }}
        >
          <span
            style={{
              width: '6px',
              height: '6px',
              borderRadius: 'var(--radius-full)',
              background: backendHealthy ? 'var(--color-success)' : 'var(--color-warning)',
            }}
          />
          {backendHealthy ? 'API Active' : 'Connecting'}
        </div>

        {/* Role Badge and Persona Switcher */}
        <button
          type="button"
          data-testid="demo-role-switcher-btn"
          onClick={onOpenDemoSelector}
          title="Change active demonstration role"
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '0.4rem',
            padding: '0.35rem 0.75rem',
            borderRadius: 'var(--radius-full)',
            background: badgeConfig.bg,
            border: `1px solid ${badgeConfig.border}`,
            color: badgeConfig.color,
            fontSize: '0.75rem',
            fontWeight: 600,
            cursor: 'pointer',
            transition: 'opacity var(--transition-fast)',
          }}
        >
          <UserCheck size={13} />
          <span data-testid="active-role-label">{badgeConfig.label}</span>
          <Sparkles size={11} style={{ opacity: 0.7 }} />
        </button>

        {/* Owner sign in or sign out */}
        {isOwner ? (
          <button
            type="button"
            data-testid="logout-btn"
            onClick={logout}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '0.35rem',
              background: 'transparent',
              border: '1px solid var(--color-border-default)',
              color: 'var(--color-text-secondary)',
              borderRadius: 'var(--radius-md)',
              padding: '0.35rem 0.65rem',
              fontSize: '0.75rem',
              cursor: 'pointer',
            }}
          >
            <LogOut size={13} />
            Sign Out
          </button>
        ) : (
          <button
            type="button"
            data-testid="owner-login-btn"
            onClick={onOpenOwnerLogin}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '0.35rem',
              background: 'var(--color-bg-surface-elevated)',
              border: '1px solid var(--color-border-default)',
              color: 'var(--color-text-secondary)',
              borderRadius: 'var(--radius-md)',
              padding: '0.35rem 0.75rem',
              fontSize: '0.75rem',
              fontWeight: 500,
              cursor: 'pointer',
            }}
          >
            <KeyRound size={13} />
            Owner Login
          </button>
        )}
      </div>
    </header>
  );
};
