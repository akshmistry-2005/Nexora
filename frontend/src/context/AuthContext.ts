import { createContext } from 'react';
import { AuthMeResponse, DemoRoleType, UserRole } from '../types/auth';

export interface AuthContextType {
  user: AuthMeResponse | null;
  role: UserRole;
  isOwner: boolean;
  permissions: string[];
  loading: boolean;
  error: string | null;
  hasPermission: (permissionCode: string) => boolean;
  loginAsDemoRole: (role: DemoRoleType) => Promise<void>;
  loginAsOwner: (password: string, email?: string) => Promise<void>;
  logout: () => Promise<void>;
  clearError: () => void;
}

export const AuthContext = createContext<AuthContextType | undefined>(undefined);
