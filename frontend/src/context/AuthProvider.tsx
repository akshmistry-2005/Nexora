import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { authApi } from '../services/auth';
import { getStoredToken } from '../services/api';
import { AuthMeResponse, DemoRoleType, UserRole } from '../types/auth';
import { AuthContext } from './AuthContext';

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<AuthMeResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchProfile = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const token = getStoredToken();
      if (!token) {
        // Auto-initialize demo session as Executive for pleasant first impression
        const demoAuth = await authApi.loginDemo('executive');
        setUser({
          user_id: demoAuth.user_id,
          email: demoAuth.email,
          full_name: demoAuth.full_name,
          is_owner: false,
          role: demoAuth.role,
          permissions: demoAuth.permissions,
        });
      } else {
        const profile = await authApi.getMe();
        setUser(profile);
      }
    } catch {
      // If stored token expired or invalid, fallback to demo executive
      try {
        const demoAuth = await authApi.loginDemo('executive');
        setUser({
          user_id: demoAuth.user_id,
          email: demoAuth.email,
          full_name: demoAuth.full_name,
          is_owner: false,
          role: demoAuth.role,
          permissions: demoAuth.permissions,
        });
      } catch (fallbackErr: unknown) {
        setError(
          fallbackErr instanceof Error
            ? fallbackErr.message
            : 'Authentication initialization failed',
        );
      }
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchProfile();
  }, [fetchProfile]);

  const loginAsDemoRole = useCallback(async (demoRole: DemoRoleType) => {
    setLoading(true);
    setError(null);
    try {
      const resp = await authApi.loginDemo(demoRole);
      setUser({
        user_id: resp.user_id,
        email: resp.email,
        full_name: resp.full_name,
        is_owner: false,
        role: resp.role,
        permissions: resp.permissions,
      });
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Demo login failed');
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const loginAsOwner = useCallback(async (password: string, email = 'owner@nexora.local') => {
    setLoading(true);
    setError(null);
    try {
      const resp = await authApi.loginOwner(password, email);
      setUser({
        user_id: resp.user_id,
        email: resp.email,
        full_name: resp.full_name,
        is_owner: true,
        role: 'owner',
        permissions: resp.permissions,
      });
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Owner login failed');
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const logout = useCallback(async () => {
    setLoading(true);
    try {
      await authApi.logout();
      // After logout, revert to default demo role (Executive)
      const demoAuth = await authApi.loginDemo('executive');
      setUser({
        user_id: demoAuth.user_id,
        email: demoAuth.email,
        full_name: demoAuth.full_name,
        is_owner: false,
        role: demoAuth.role,
        permissions: demoAuth.permissions,
      });
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Logout failed');
    } finally {
      setLoading(false);
    }
  }, []);

  const clearError = useCallback(() => setError(null), []);

  const hasPermission = useCallback(
    (permissionCode: string): boolean => {
      if (!user) return false;
      if (user.is_owner || user.role === 'owner') return true;
      return user.permissions.includes(permissionCode);
    },
    [user],
  );

  const value = useMemo(
    () => ({
      user,
      role: (user?.role || 'general_viewer') as UserRole,
      isOwner: Boolean(user?.is_owner),
      permissions: user?.permissions || [],
      loading,
      error,
      hasPermission,
      loginAsDemoRole,
      loginAsOwner,
      logout,
      clearError,
    }),
    [user, loading, error, hasPermission, loginAsDemoRole, loginAsOwner, logout, clearError],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
