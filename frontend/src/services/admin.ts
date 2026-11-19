import {
  AuditLogItem,
  AuditLogSummary,
  ResetDemoResponse,
  SystemStatusData,
  UserAdminItem,
} from '../types/admin';
import { apiClient } from './api';

export interface AuditLogFilterParams {
  action_type?: string;
  actor_role?: string;
  entity_type?: string;
  limit?: number;
  offset?: number;
}

export const adminService = {
  async getAuditLogs(params: AuditLogFilterParams = {}): Promise<AuditLogItem[]> {
    const query = new URLSearchParams();
    if (params.action_type) query.append('action_type', params.action_type);
    if (params.actor_role) query.append('actor_role', params.actor_role);
    if (params.entity_type) query.append('entity_type', params.entity_type);
    if (params.limit !== undefined) query.append('limit', String(params.limit));
    if (params.offset !== undefined) query.append('offset', String(params.offset));

    const qs = query.toString();
    return apiClient<AuditLogItem[]>(`/api/v1/admin/audit-logs${qs ? `?${qs}` : ''}`);
  },

  async getAuditSummary(): Promise<AuditLogSummary> {
    return apiClient<AuditLogSummary>('/api/v1/admin/audit-summary');
  },

  async getUsersList(): Promise<UserAdminItem[]> {
    return apiClient<UserAdminItem[]>('/api/v1/admin/users');
  },

  async getSystemStatus(): Promise<SystemStatusData> {
    return apiClient<SystemStatusData>('/api/v1/admin/system-status');
  },

  async resetDemoData(): Promise<ResetDemoResponse> {
    return apiClient<ResetDemoResponse>('/api/v1/admin/reset-demo', {
      method: 'POST',
    });
  },
};
