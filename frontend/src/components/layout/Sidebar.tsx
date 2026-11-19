import React from 'react';
import {
  Activity,
  AlertTriangle,
  BarChart3,
  BrainCircuit,
  Building2,
  ChevronLeft,
  ChevronRight,
  Database,
  FileSpreadsheet,
  Layers,
  LineChart,
  Lock,
  Package,
  Settings,
  ShieldCheck,
  TrendingUp,
  Truck,
  Users,
} from 'lucide-react';
import { NavLink } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import { NavGroup } from '../../types/navigation';

export interface SidebarProps {
  collapsed: boolean;
  onToggleCollapse: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ collapsed, onToggleCollapse }) => {
  const { hasPermission, isOwner } = useAuth();

  const navigationGroups: NavGroup[] = [
    {
      label: 'Business Intelligence',
      items: [
        {
          id: 'overview',
          label: 'Executive Overview',
          path: '/',
          icon: <Layers size={18} />,
          requiredPermission: 'dashboard.view',
        },
        {
          id: 'sales',
          label: 'Sales Intelligence',
          path: '/sales',
          icon: <TrendingUp size={18} />,
          requiredPermission: 'sales.view',
        },
        {
          id: 'customers',
          label: 'Customer Intelligence',
          path: '/customers',
          icon: <Users size={18} />,
          requiredPermission: 'customer.view',
        },
        {
          id: 'marketing',
          label: 'Marketing ROI',
          path: '/marketing',
          icon: <BarChart3 size={18} />,
          requiredPermission: 'marketing.view',
        },
        {
          id: 'finance',
          label: 'Financial Performance',
          path: '/finance',
          icon: <Building2 size={18} />,
          requiredPermission: 'finance.view',
        },
        {
          id: 'inventory',
          label: 'Inventory & Warehouse',
          path: '/inventory',
          icon: <Package size={18} />,
          requiredPermission: 'inventory.view',
        },
        {
          id: 'operations',
          label: 'Operations & Fulfillment',
          path: '/operations',
          icon: <Activity size={18} />,
          requiredPermission: 'operations.view',
        },
        {
          id: 'suppliers',
          label: 'Supplier Performance',
          path: '/suppliers',
          icon: <Truck size={18} />,
          requiredPermission: 'supplier.view',
        },
      ],
    },
    {
      label: 'Advanced Analytics & AI',
      items: [
        {
          id: 'statistics',
          label: 'Statistical Analysis',
          path: '/statistics',
          icon: <LineChart size={18} />,
          requiredPermission: 'statistics.view',
        },
        {
          id: 'predictions',
          label: 'Predictive Models',
          path: '/predictions',
          icon: <BrainCircuit size={18} />,
          requiredPermission: 'predictions.view',
        },
        {
          id: 'anomalies',
          label: 'Anomaly Detection',
          path: '/anomalies',
          icon: <AlertTriangle size={18} />,
          requiredPermission: 'anomaly.view',
        },
      ],
    },
    {
      label: 'Reporting & Data Ops',
      items: [
        {
          id: 'reports',
          label: 'Reports & Exports',
          path: '/reports',
          icon: <FileSpreadsheet size={18} />,
          requiredPermission: 'report.view',
        },
        {
          id: 'data-sources',
          label: 'Data Ingestion',
          path: '/data-sources',
          icon: <Database size={18} />,
          requiredPermission: 'datasource.view',
        },
        {
          id: 'data-quality',
          label: 'Data Quality Engine',
          path: '/data-quality',
          icon: <ShieldCheck size={18} />,
          requiredPermission: 'dataquality.view',
        },
      ],
    },
    {
      label: 'Administration',
      items: [
        {
          id: 'admin',
          label: 'Platform Administration',
          path: '/admin',
          icon: <Settings size={18} />,
          requiredPermission: 'audit.view',
          ownerOnly: true,
        },
      ],
    },
  ];

  return (
    <aside
      data-testid="app-sidebar"
      style={{
        width: collapsed ? '68px' : '260px',
        minWidth: collapsed ? '68px' : '260px',
        background: 'var(--color-bg-surface)',
        borderRight: '1px solid var(--color-border-subtle)',
        display: 'flex',
        flexDirection: 'column',
        transition: 'width var(--transition-normal), min-width var(--transition-normal)',
        position: 'relative',
        zIndex: 30,
        height: '100vh',
        overflow: 'hidden',
      }}
    >
      {/* Brand Header */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: collapsed ? 'center' : 'space-between',
          padding: '1.25rem 1rem',
          borderBottom: '1px solid var(--color-border-subtle)',
          height: '64px',
          boxSizing: 'border-box',
        }}
      >
        {!collapsed && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
            <div
              style={{
                width: '32px',
                height: '32px',
                borderRadius: 'var(--radius-md)',
                background: 'linear-gradient(135deg, #3b82f6 0%, #06b6d4 100%)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: '#ffffff',
                fontWeight: 800,
                fontSize: '1rem',
              }}
            >
              N
            </div>
            <div>
              <div
                style={{
                  fontWeight: 700,
                  fontSize: '1rem',
                  color: '#ffffff',
                  letterSpacing: '0.02em',
                }}
              >
                NEXORA
              </div>
              <div style={{ fontSize: '0.6875rem', color: 'var(--color-text-subtle)' }}>
                Data Intelligence
              </div>
            </div>
          </div>
        )}

        {collapsed && (
          <div
            style={{
              width: '32px',
              height: '32px',
              borderRadius: 'var(--radius-md)',
              background: 'linear-gradient(135deg, #3b82f6 0%, #06b6d4 100%)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#ffffff',
              fontWeight: 800,
              fontSize: '1rem',
            }}
          >
            N
          </div>
        )}

        <button
          type="button"
          data-testid="sidebar-toggle-btn"
          aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          onClick={onToggleCollapse}
          style={{
            background: 'transparent',
            border: 'none',
            color: 'var(--color-text-muted)',
            cursor: 'pointer',
            padding: '4px',
            borderRadius: 'var(--radius-sm)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          {collapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
        </button>
      </div>

      {/* Nav Groups */}
      <nav
        style={{
          flex: 1,
          overflowY: 'auto',
          padding: '1rem 0.5rem',
          display: 'flex',
          flexDirection: 'column',
          gap: '1.25rem',
        }}
      >
        {navigationGroups.map((group, groupIdx) => {
          return (
            <div key={groupIdx}>
              {!collapsed && (
                <div
                  style={{
                    fontSize: '0.6875rem',
                    fontWeight: 700,
                    textTransform: 'uppercase',
                    letterSpacing: '0.06em',
                    color: 'var(--color-text-subtle)',
                    padding: '0 0.75rem 0.4rem',
                  }}
                >
                  {group.label}
                </div>
              )}

              <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
                {group.items.map((item) => {
                  const hasAccess = item.ownerOnly
                    ? isOwner
                    : !item.requiredPermission || hasPermission(item.requiredPermission);

                  return (
                    <NavLink
                      key={item.id}
                      to={item.path}
                      end={item.path === '/'}
                      data-testid={`nav-item-${item.id}`}
                      style={({ isActive }) => ({
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: collapsed ? 'center' : 'space-between',
                        padding: collapsed ? '0.6rem 0' : '0.55rem 0.75rem',
                        borderRadius: 'var(--radius-md)',
                        textDecoration: 'none',
                        color: isActive
                          ? '#ffffff'
                          : hasAccess
                            ? 'var(--color-text-secondary)'
                            : 'var(--color-text-subtle)',
                        background: isActive ? 'var(--color-primary-muted)' : 'transparent',
                        fontWeight: isActive ? 600 : 400,
                        fontSize: '0.84rem',
                        borderLeft: isActive
                          ? '3px solid var(--color-primary)'
                          : '3px solid transparent',
                        transition:
                          'background var(--transition-fast), color var(--transition-fast)',
                      })}
                    >
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
                        <span style={{ display: 'flex', alignItems: 'center' }}>{item.icon}</span>
                        {!collapsed && <span>{item.label}</span>}
                      </div>

                      {!collapsed && !hasAccess && (
                        <span title="Restricted by current role" style={{ opacity: 0.6 }}>
                          <Lock size={13} color="var(--color-text-subtle)" />
                        </span>
                      )}
                    </NavLink>
                  );
                })}
              </div>
            </div>
          );
        })}
      </nav>

      {/* Synthetic Data Disclaimer Footer */}
      {!collapsed && (
        <div
          style={{
            padding: '0.75rem',
            margin: '0.5rem',
            borderRadius: 'var(--radius-md)',
            background: 'rgba(255, 255, 255, 0.02)',
            border: '1px solid var(--color-border-subtle)',
            fontSize: '0.6875rem',
            color: 'var(--color-text-subtle)',
            lineHeight: 1.4,
          }}
        >
          <div style={{ fontWeight: 600, color: 'var(--color-text-muted)', marginBottom: '2px' }}>
            DEMO ENVIRONMENT
          </div>
          All analytics powered by synthetic enterprise seed data.
        </div>
      )}
    </aside>
  );
};
