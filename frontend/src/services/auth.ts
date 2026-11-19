import { AuthMeResponse, DemoRoleType, TokenResponse } from '../types/auth';
import { apiClient, clearStoredToken, setStoredToken } from './api';

export const authApi = {
  async loginDemo(role: DemoRoleType): Promise<TokenResponse> {
    const data = await apiClient<TokenResponse>('/api/v1/auth/demo-login', {
      method: 'POST',
      body: JSON.stringify({ role }),
    });
    setStoredToken(data.access_token);
    return data;
  },

  async loginOwner(password: string, email = 'owner@nexora.local'): Promise<TokenResponse> {
    const data = await apiClient<TokenResponse>('/api/v1/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
    setStoredToken(data.access_token);
    return data;
  },

  async logout(): Promise<void> {
    try {
      await apiClient<{ message: string }>('/api/v1/auth/logout', {
        method: 'POST',
      });
    } catch {
      // ignore server errors during logout
    } finally {
      clearStoredToken();
    }
  },

  async getMe(): Promise<AuthMeResponse> {
    return apiClient<AuthMeResponse>('/api/v1/auth/me');
  },
};
