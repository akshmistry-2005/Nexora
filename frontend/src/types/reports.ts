export interface ReportCatalogueItem {
  report_id: string;
  name: string;
  domain: string;
  description: string;
  cadence: string;
  exportable: boolean;
  columns: string[];
  sensitive_columns: string[];
}

export interface ReportData {
  report_id: string;
  name: string;
  domain: string;
  generated_at: string;
  total_rows: number;
  columns: string[];
  summary: Record<string, unknown>;
  rows: Record<string, unknown>[];
  synthetic_notice: string;
}

export interface SavedView {
  id: number;
  user_id: number;
  creator_name?: string | null;
  section: string;
  name: string;
  filter_config: Record<string, unknown>;
  is_shared: boolean;
  created_at: string;
}

export interface CreateSavedViewPayload {
  section: string;
  name: string;
  filter_config: Record<string, unknown>;
  is_shared?: boolean;
}
