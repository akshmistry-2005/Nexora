import React, { useState } from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import { BreadcrumbItem } from '../../types/navigation';
import { DemoRoleSelector } from '../auth/DemoRoleSelector';
import { OwnerLoginModal } from '../auth/OwnerLoginModal';
import { ErrorBoundary } from '../common/ErrorBoundary';
import { Sidebar } from './Sidebar';
import { TopBar } from './TopBar';

const ROUTE_LABELS: Record<string, string> = {
  '/': 'Executive Overview',
  '/sales': 'Sales Intelligence',
  '/customers': 'Customer Intelligence',
  '/marketing': 'Marketing ROI',
  '/finance': 'Financial Performance',
  '/inventory': 'Inventory & Warehouse',
  '/operations': 'Operations & Fulfillment',
  '/suppliers': 'Supplier Performance',
  '/statistics': 'Statistical Analysis',
  '/predictions': 'Predictive Models & Forecasts',
  '/anomalies': 'Anomaly Detection',
  '/reports': 'Reports & Exports',
  '/data-sources': 'Data Ingestion',
  '/data-quality': 'Data Quality Engine',
  '/admin': 'Platform Administration',
};

export const AppShell: React.FC = () => {
  const location = useLocation();
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [demoSelectorOpen, setDemoSelectorOpen] = useState(false);
  const [ownerLoginOpen, setOwnerLoginOpen] = useState(false);

  const currentLabel = ROUTE_LABELS[location.pathname] || 'Analytics Workspace';
  const breadcrumbs: BreadcrumbItem[] = [{ label: 'Nexora', path: '/' }, { label: currentLabel }];

  return (
    <div
      data-testid="app-shell"
      style={{
        display: 'flex',
        minHeight: '100vh',
        width: '100%',
        backgroundColor: 'var(--color-bg-base)',
        color: 'var(--color-text-primary)',
        overflow: 'hidden',
      }}
    >
      {/* Sidebar */}
      <Sidebar
        collapsed={sidebarCollapsed}
        onToggleCollapse={() => setSidebarCollapsed(!sidebarCollapsed)}
      />

      {/* Main Content Area */}
      <div
        style={{
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          height: '100vh',
          overflow: 'hidden',
          minWidth: 0,
        }}
      >
        <TopBar
          breadcrumbs={breadcrumbs}
          onToggleSidebarMobile={() => setSidebarCollapsed(!sidebarCollapsed)}
          onOpenDemoSelector={() => setDemoSelectorOpen(true)}
          onOpenOwnerLogin={() => setOwnerLoginOpen(true)}
        />

        <main
          data-testid="main-content"
          style={{
            flex: 1,
            overflowY: 'auto',
            padding: '1.5rem',
            boxSizing: 'border-box',
          }}
        >
          <ErrorBoundary>
            <Outlet />
          </ErrorBoundary>
        </main>
      </div>

      {/* Modals */}
      <DemoRoleSelector isOpen={demoSelectorOpen} onClose={() => setDemoSelectorOpen(false)} />
      <OwnerLoginModal isOpen={ownerLoginOpen} onClose={() => setOwnerLoginOpen(false)} />
    </div>
  );
};
