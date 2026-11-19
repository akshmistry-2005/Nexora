export type PipelineStatus = 'running' | 'success' | 'failed' | 'retried';

export interface PipelineRun {
  id: number;
  import_job_id: number | null;
  pipeline_name: string;
  status: PipelineStatus;
  duration_ms: number | null;
  metrics: Record<string, unknown>;
  started_at: string;
  ended_at: string | null;
}

export interface PipelineSummaryItem {
  pipeline_name: string;
  total_runs: number;
  successful_runs: number;
  failed_runs: number;
  last_successful_run_at: string | null;
  last_run_status: PipelineStatus | null;
}

export interface PipelineHealthSummary {
  active_pipelines_count: number;
  total_runs_count: number;
  failed_runs_count: number;
  last_successful_refresh: string | null;
  pipelines: PipelineSummaryItem[];
  synthetic_notice: string;
}

export interface PipelineRetryResponse {
  previous_run_id: number;
  new_run_id: number;
  pipeline_name: string;
  status: PipelineStatus;
  message: string;
  retried_at: string;
}
