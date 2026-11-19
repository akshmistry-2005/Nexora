import {
  PipelineHealthSummary,
  PipelineRetryResponse,
  PipelineRun,
  PipelineStatus,
} from '../types/pipelines';
import { apiClient } from './api';

export interface PipelineFilterParams {
  status?: PipelineStatus;
  pipeline_name?: string;
  limit?: number;
  offset?: number;
}

export const pipelinesService = {
  async listPipelineRuns(params: PipelineFilterParams = {}): Promise<PipelineRun[]> {
    const query = new URLSearchParams();
    if (params.status) query.append('status', params.status);
    if (params.pipeline_name) query.append('pipeline_name', params.pipeline_name);
    if (params.limit !== undefined) query.append('limit', String(params.limit));
    if (params.offset !== undefined) query.append('offset', String(params.offset));

    const qs = query.toString();
    return apiClient<PipelineRun[]>(`/api/v1/pipelines/runs${qs ? `?${qs}` : ''}`);
  },

  async getPipelineSummary(): Promise<PipelineHealthSummary> {
    return apiClient<PipelineHealthSummary>('/api/v1/pipelines/summary');
  },

  async getPipelineRunById(runId: number): Promise<PipelineRun> {
    return apiClient<PipelineRun>(`/api/v1/pipelines/runs/${runId}`);
  },

  async retryPipelineRun(runId: number, notes?: string): Promise<PipelineRetryResponse> {
    const query = notes ? `?notes=${encodeURIComponent(notes)}` : '';
    return apiClient<PipelineRetryResponse>(`/api/v1/pipelines/runs/${runId}/retry${query}`, {
      method: 'POST',
    });
  },
};
