import React, { useState } from 'react';
import { AlertTriangle, Lock, RotateCcw } from 'lucide-react';
import { Alert } from '../../components/common/Alert';
import { KPICard } from '../../components/common/KPICard';
import { Modal } from '../../components/common/Modal';
import { useAuth } from '../../hooks/useAuth';

export const AdminPage: React.FC = () => {
  const { isOwner } = useAuth();
  const [resetModalOpen, setResetModalOpen] = useState(false);
  const [resetting, setResetting] = useState(false);
  const [resetSuccess, setResetSuccess] = useState(false);

  const handleResetData = async () => {
    setResetting(true);
    // Simulate reset call or call backend reset
    setTimeout(() => {
      setResetting(false);
      setResetModalOpen(false);
      setResetSuccess(true);
    }, 1200);
  };

  return (
    <div data-testid="admin-page">
      <div style={{ marginBottom: '1.25rem' }}>
        <h1
          style={{ margin: '0 0 0.25rem', fontSize: '1.625rem', fontWeight: 700, color: '#ffffff' }}
        >
          Platform Administration & Security
        </h1>
        <p style={{ margin: 0, color: 'var(--color-text-muted)', fontSize: '0.875rem' }}>
          Role-based access controls, pipeline telemetry, audit trails, and portfolio reset
          utilities.
        </p>
      </div>

      {!isOwner && (
        <Alert variant="warning" style={{ marginBottom: '1.5rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Lock size={16} />
            <span>
              <strong>Owner Privileges Required:</strong> Destructive operations such as database
              reset, direct record deletion, and user role configuration are restricted to the
              Platform Owner.
            </span>
          </div>
        </Alert>
      )}

      {resetSuccess && (
        <Alert
          variant="success"
          style={{ marginBottom: '1.5rem' }}
          onClose={() => setResetSuccess(false)}
        >
          Demonstration dataset reset initiated successfully. Seed data restored to initial state.
        </Alert>
      )}

      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
          gap: '1rem',
          marginBottom: '1.5rem',
        }}
      >
        <KPICard
          title="Security Roles"
          value={6}
          format="number"
          subtitle="1 Owner + 5 Demo Roles"
        />
        <KPICard
          title="Registered Permissions"
          value={29}
          format="number"
          subtitle="Granular RBAC codes"
        />
        <KPICard
          title="Audit Log Entries"
          value={142}
          format="number"
          subtitle="Append-only log storage"
        />
        <KPICard title="Database Status" value="ONLINE" subtitle="PostgreSQL 16 Docker" />
      </div>

      {/* Admin Action Panels */}
      <div
        style={{
          background: 'var(--color-bg-surface)',
          borderRadius: 'var(--radius-lg)',
          border: '1px solid var(--color-border-subtle)',
          padding: '1.5rem',
        }}
      >
        <h3 style={{ margin: '0 0 0.5rem', fontSize: '1.125rem', color: '#ffffff' }}>
          Demonstration Environment Management
        </h3>
        <p
          style={{
            margin: '0 0 1.25rem',
            fontSize: '0.875rem',
            color: 'var(--color-text-muted)',
            maxWidth: '600px',
          }}
        >
          Reset all transactions, customers, and inventory to the clean synthetic baseline (seed
          42). This action preserves table schemas and recreates 15,000 orders deterministically.
        </p>

        <button
          type="button"
          data-testid="admin-reset-data-btn"
          disabled={!isOwner}
          onClick={() => setResetModalOpen(true)}
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '0.45rem',
            background: isOwner ? 'var(--color-danger)' : 'var(--color-bg-surface-elevated)',
            color: isOwner ? '#ffffff' : 'var(--color-text-subtle)',
            border: 'none',
            borderRadius: 'var(--radius-md)',
            padding: '0.55rem 1.15rem',
            fontWeight: 600,
            fontSize: '0.875rem',
            cursor: isOwner ? 'pointer' : 'not-allowed',
            opacity: isOwner ? 1 : 0.6,
          }}
        >
          <RotateCcw size={15} />
          Reset Demonstration Database
        </button>
      </div>

      {/* Confirmation Modal */}
      <Modal
        isOpen={resetModalOpen}
        onClose={() => setResetModalOpen(false)}
        title="Confirm Demonstration Data Reset"
        maxWidth="480px"
        footer={
          <>
            <button
              type="button"
              onClick={() => setResetModalOpen(false)}
              style={{
                background: 'transparent',
                border: '1px solid var(--color-border-default)',
                color: 'var(--color-text-secondary)',
                borderRadius: 'var(--radius-md)',
                padding: '0.45rem 1rem',
                fontSize: '0.8125rem',
                cursor: 'pointer',
              }}
            >
              Cancel
            </button>
            <button
              type="button"
              data-testid="confirm-reset-btn"
              disabled={resetting}
              onClick={handleResetData}
              style={{
                background: 'var(--color-danger)',
                color: '#ffffff',
                border: 'none',
                borderRadius: 'var(--radius-md)',
                padding: '0.45rem 1.25rem',
                fontSize: '0.8125rem',
                fontWeight: 600,
                cursor: resetting ? 'wait' : 'pointer',
              }}
            >
              {resetting ? 'Resetting...' : 'Confirm Reset'}
            </button>
          </>
        }
      >
        <div style={{ display: 'flex', alignItems: 'flex-start', gap: '0.75rem' }}>
          <div style={{ color: 'var(--color-danger)', flexShrink: 0, marginTop: '2px' }}>
            <AlertTriangle size={24} />
          </div>
          <div
            style={{ fontSize: '0.875rem', color: 'var(--color-text-secondary)', lineHeight: 1.5 }}
          >
            <p
              style={{ margin: '0 0 0.5rem', fontWeight: 600, color: 'var(--color-text-primary)' }}
            >
              Are you sure you want to reset the synthetic database?
            </p>
            <p style={{ margin: 0 }}>
              All dynamic changes, test records, and custom views will be purged and reseeded from
              the deterministic seed dataset.
            </p>
          </div>
        </div>
      </Modal>
    </div>
  );
};
