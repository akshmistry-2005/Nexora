export type DemoRoleType =
  'executive' | 'department_manager' | 'data_analyst' | 'data_scientist' | 'general_viewer';

export type UserRole = DemoRoleType | 'owner';

export interface TokenResponse {
  access_token: string;
  token_type: string;
  expires_in_seconds: number;
  user_id: number;
  email: string;
  full_name: string;
  role: UserRole;
  permissions: string[];
}

export interface AuthMeResponse {
  user_id: number;
  email: string;
  full_name: string;
  is_owner: boolean;
  role: UserRole;
  permissions: string[];
}

export interface DemoRoleOption {
  id: DemoRoleType;
  title: string;
  roleName: string;
  badgeColor: string;
  description: string;
  primaryViews: string[];
}

export const DEMO_ROLES: DemoRoleOption[] = [
  {
    id: 'executive',
    title: 'Executive (CEO / C-Suite)',
    roleName: 'Executive',
    badgeColor: '#06b6d4',
    description:
      'High-level business performance, net margins, cross-department trends, and anomalies.',
    primaryViews: ['Overview', 'Sales', 'Finance', 'Anomalies'],
  },
  {
    id: 'department_manager',
    title: 'Department Manager (Sales & Ops)',
    roleName: 'Department Manager',
    badgeColor: '#3b82f6',
    description:
      'Operational metrics, regional sales pipelines, campaign effectiveness, and inventory velocity.',
    primaryViews: ['Sales', 'Marketing', 'Inventory', 'Operations'],
  },
  {
    id: 'data_analyst',
    title: 'Data Analyst (Senior BI Specialist)',
    roleName: 'Data Analyst',
    badgeColor: '#10b981',
    description:
      'Granular dataset exploration, parameterized filtering, custom reports, and sanitized CSV exports.',
    primaryViews: ['Customers', 'Orders', 'Reports', 'Statistics'],
  },
  {
    id: 'data_scientist',
    title: 'Data Scientist (ML & Forecasting)',
    roleName: 'Data Scientist',
    badgeColor: '#8b5cf6',
    description:
      'Statistical distributions, regression oracles, customer churn models, and demand forecasts.',
    primaryViews: ['Statistics', 'Predictions', 'Anomalies'],
  },
  {
    id: 'general_viewer',
    title: 'General Viewer (Auditor / Guest)',
    roleName: 'General Viewer',
    badgeColor: '#94a3b8',
    description: 'Read-only exploratory access to core dashboards; data exports are restricted.',
    primaryViews: ['Overview', 'Sales', 'Reports (Read-only)'],
  },
];
