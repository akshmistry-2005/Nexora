import React, { useState } from 'react';
import { KeyRound, Lock } from 'lucide-react';
import { useAuth } from '../../hooks/useAuth';
import { Alert } from '../common/Alert';
import { FormField } from '../common/FormField';
import { Modal } from '../common/Modal';

export interface OwnerLoginModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const OwnerLoginModal: React.FC<OwnerLoginModalProps> = ({ isOpen, onClose }) => {
  const { loginAsOwner, loading } = useAuth();
  const [email, setEmail] = useState('owner@nexora.local');
  const [password, setPassword] = useState('');
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<{ email?: string; password?: string }>({});

  const validate = (): boolean => {
    const errors: { email?: string; password?: string } = {};
    if (!email.trim()) {
      errors.email = 'Email address is required.';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      errors.email = 'Please provide a valid email format.';
    }

    if (!password) {
      errors.password = 'Password is required.';
    } else if (password.length < 6) {
      errors.password = 'Password must be at least 6 characters.';
    }

    setFieldErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);

    if (!validate()) return;

    try {
      await loginAsOwner(password, email);
      setPassword('');
      onClose();
    } catch (err: unknown) {
      setErrorMsg(err instanceof Error ? err.message : 'Invalid owner credentials.');
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Platform Owner Authentication" maxWidth="460px">
      <form onSubmit={handleSubmit} data-testid="owner-login-form" noValidate>
        <div style={{ marginBottom: '1.25rem' }}>
          <p
            style={{
              margin: '0 0 1rem',
              fontSize: '0.8125rem',
              color: 'var(--color-text-muted)',
              lineHeight: 1.5,
            }}
          >
            Access administrative controls, data source mutation, user management, and demonstration
            data reset.
          </p>

          {errorMsg && (
            <Alert
              variant="error"
              style={{ marginBottom: '1rem' }}
              onClose={() => setErrorMsg(null)}
            >
              {errorMsg}
            </Alert>
          )}

          <FormField
            label="Owner Email"
            type="email"
            required
            value={email}
            onChange={(e) => {
              setEmail(e.target.value);
              if (fieldErrors.email) setFieldErrors({ ...fieldErrors, email: undefined });
            }}
            error={fieldErrors.email}
            placeholder="owner@nexora.local"
            autoComplete="username"
          />

          <FormField
            label="Owner Password"
            type="password"
            required
            value={password}
            onChange={(e) => {
              setPassword(e.target.value);
              if (fieldErrors.password) setFieldErrors({ ...fieldErrors, password: undefined });
            }}
            error={fieldErrors.password}
            placeholder="••••••••••••"
            autoComplete="current-password"
          />
        </div>

        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'flex-end',
            gap: '0.75rem',
            marginTop: '1.5rem',
          }}
        >
          <button
            type="button"
            onClick={onClose}
            style={{
              background: 'transparent',
              border: '1px solid var(--color-border-default)',
              color: 'var(--color-text-secondary)',
              borderRadius: 'var(--radius-md)',
              padding: '0.5rem 1rem',
              fontSize: '0.875rem',
              cursor: 'pointer',
            }}
          >
            Cancel
          </button>
          <button
            type="submit"
            data-testid="owner-login-submit"
            disabled={loading}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '0.4rem',
              background: 'var(--color-primary)',
              color: '#ffffff',
              border: 'none',
              borderRadius: 'var(--radius-md)',
              padding: '0.5rem 1.25rem',
              fontSize: '0.875rem',
              fontWeight: 600,
              cursor: loading ? 'wait' : 'pointer',
              opacity: loading ? 0.7 : 1,
            }}
          >
            {loading ? <Lock size={15} /> : <KeyRound size={15} />}
            {loading ? 'Authenticating...' : 'Sign In as Owner'}
          </button>
        </div>
      </form>
    </Modal>
  );
};
