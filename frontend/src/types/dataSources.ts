export interface DataSource {
  id: number;
  organization_id: number;
  name: string;
  source_type: string;
  file_name: string;
  file_size_bytes: number;
  file_checksum: string;
  uploaded_by_id: number;
  created_at: string;
}

export interface ImportJob {
  id: number;
  data_source_id: number;
  target_entity: string;
  status: 'pending' | 'processing' | 'completed' | 'failed' | 'rolled_back';
  total_rows: number;
  loaded_rows: number;
  rejected_rows: number;
  mapping_config: Record<string, string>;
  error_details: Record<string, unknown> | null;
  started_at: string | null;
  completed_at: string | null;
}

export interface PreviewResponse {
  file_name: string;
  file_size_bytes: number;
  file_checksum: string;
  target_entity: string;
  detected_headers: string[];
  suggested_mapping: Record<string, string>;
  missing_required_headers: string[];
  total_detected_rows: number;
  preview_rows: Record<string, unknown>[];
  inferred_types: Record<string, string>;
  is_duplicate: boolean;
}

export interface ImportResultResponse {
  job_id: number;
  data_source_id: number;
  status: string;
  target_entity: string;
  total_rows: number;
  loaded_rows: number;
  rejected_rows: number;
  checksum: string;
}
