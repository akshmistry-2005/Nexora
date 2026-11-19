import React from 'react';
import { Check, Shield } from 'lucide-react';
import { DEMO_ROLES, DemoRoleType } from '../../types/auth';
import { useAuth } from '../../hooks/useAuth';
import { Modal } from '../common/Modal';

export interface DemoRoleSelectorProps {
  isOpen: boolean;
  onClose: () => void;
}

export const DemoRoleSelector: React.FC<DemoRoleSelectorProps> = ({ isOpen, onClose }) => {
  const { role, loginAsDemoRole, loading } = useAuth();

  const handleSelect = async (selectedRole: DemoRoleType) => {
    try {
      await loginAsDemoRole(selectedRole);
      onClose();
    } catch {
      // Error handled by AuthContext
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Select Demonstration Persona"
      maxWidth="600px"
      footer={
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            width: '100%',
          }}
        >
          <span style={{ fontSize: '0.75rem', color: 'var(--color-text-subtle)' }}>
            All demo personas operate with read-only database protections.
          </span>
          <button
            type="button"
            onClick={onClose}
            style={{
              background: 'var(--color-bg-surface-elevated)',
              border: '1px solid var(--color-border-default)',
              color: 'var(--color-text-secondary)',
              borderRadius: 'var(--radius-md)',
              padding: '0.45rem 1rem',
              fontSize: '0.8125rem',
              cursor: 'pointer',
            }}
          >
            Done
          </button>
        </div>
      }
    >
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
        {DEMO_ROLES.map((demo) => {
          const isSelected = role === demo.id;
          return (
            <div
              key={demo.id}
              data-testid={`demo-role-card-${demo.id}`}
              onClick={() => !loading && handleSelect(demo.id)}
              style={{
                display: 'flex',
                alignItems: 'flex-start',
                justifyContent: 'space-between',
                padding: '1rem',
                borderRadius: 'var(--radius-md)',
                border: `1px solid ${isSelected ? 'var(--color-primary)' : 'var(--color-border-subtle)'}`,
                background: isSelected
                  ? 'var(--color-primary-muted)'
                  : 'var(--color-bg-surface-elevated)',
                cursor: loading ? 'wait' : 'pointer',
                transition: 'all var(--transition-fast)',
              }}
            >
              <div style={{ flex: 1, paddingRight: '1rem' }}>
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.5rem',
                    marginBottom: '0.35rem',
                  }}
                >
                  <span
                    style={{
                      display: 'inline-block',
                      width: '8px',
                      height: '8px',
                      borderRadius: 'var(--radius-full)',
                      background: demo.badgeColor,
                    }}
                  />
                  <h4
                    style={{
                      margin: 0,
                      fontSize: '0.9375rem',
                      fontWeight: 600,
                      color: 'var(--color-text-primary)',
                    }}
                  >
                    {demo.title}
                  </h4>
                  {isSelected && (
                    <span
                      style={{
                        fontSize: '0.6875rem',
                        fontWeight: 600,
                        textTransform: 'uppercase',
                        background: 'var(--color-primary)',
                        color: '#ffffff',
                        padding: '1px 6px',
                        borderRadius: 'var(--radius-sm)',
                      }}
                    >
                      Active
                    </span>
                  )}
                </div>
                <p
                  style={{
                    margin: '0 0 0.5rem',
                    fontSize: '0.8125rem',
                    color: 'var(--color-text-muted)',
                  }}
                >
                  {demo.description}
                </p>
                <div
                  style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', flexWrap: 'wrap' }}
                >
                  <span
                    style={{
                      fontSize: '0.6875rem',
                      color: 'var(--color-text-subtle)',
                      fontWeight: 500,
                    }}
                  >
                    Core Views:
                  </span>
                  {demo.primaryViews.map((v) => (
                    <span
                      key={v}
                      style={{
                        fontSize: '0.6875rem',
                        background: 'rgba(255, 255, 255, 0.05)',
                        border: '1px solid var(--color-border-subtle)',
                        borderRadius: 'var(--radius-sm)',
                        padding: '1px 5px',
                        color: 'var(--color-text-secondary)',
                      }}
                    >
                      {v}
                    </span>
                  ))}
                </div>
              </div>

              <div style={{ flexShrink: 0, marginTop: '2px' }}>
                {isSelected ? (
                  <div
                    style={{
                      width: '24px',
                      height: '24px',
                      borderRadius: 'var(--radius-full)',
                      background: 'var(--color-primary)',
                      color: '#ffffff',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                    }}
                  >
                    <Check size={14} />
                  </div>
                ) : (
                  <Shield size={18} color="var(--color-text-subtle)" />
                )}
              </div>
            </div>
          );
        })}
      </div>
    </Modal>
  );
};
