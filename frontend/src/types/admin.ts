export interface AuditLogItem {
  id: number;
  organization_id: number | null;
  actor_user_id: number | null;
  actor_role: string;
  action_type: string;
  entity_type: string | null;
  entity_id: string | null;
  ip_address: string | null;
  details: Record<string, unknown> | null;
  created_at: string;
}

export interface AuditLogSummary {
  total_logs: number;
  by_action_type: Record<string, number>;
  by_role: Record<string, number>;
}

export interface UserAdminItem {
  id: number;
  email: string;
  full_name: string;
  is_active: boolean;
  is_owner: boolean;
  roles: string[];
  created_at: string;
}

export interface SystemStatusData {
  platform_name: string;
  version: string;
  environment: string;
  is_demonstration: boolean;
  database_connected: boolean;
  synthetic_data_notice: string;
  table_counts: Record<string, number>;
  timestamp: string;
}

export interface ResetDemoResponse {
  status: string;
  message: string;
  synthetic_notice: string;
  reset_timestamp: string;
}
