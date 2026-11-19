import {
  AnomalyAcknowledgeRequest,
  AnomalyAlert,
  AnomalyDetectionRunResponse,
  AnomalyDomain,
  AnomalySeverity,
  AnomalyStatus,
  AnomalySummaryStats,
  IsolationForestBenchmark,
} from '../types/anomalies';
import { apiClient } from './api';

export interface AnomalyFilterParams {
  domain?: AnomalyDomain;
  severity?: AnomalySeverity;
  status?: AnomalyStatus;
  limit?: number;
  offset?: number;
}

export const anomaliesService = {
  async getAnomalies(params: AnomalyFilterParams = {}): Promise<AnomalyAlert[]> {
    const query = new URLSearchParams();
    if (params.domain) query.append('domain', params.domain);
    if (params.severity) query.append('severity', params.severity);
    if (params.status) query.append('status', params.status);
    if (params.limit !== undefined) query.append('limit', String(params.limit));
    if (params.offset !== undefined) query.append('offset', String(params.offset));

    const qs = query.toString();
    return apiClient<AnomalyAlert[]>(`/api/v1/anomalies${qs ? `?${qs}` : ''}`);
  },

  async getSummaryStats(): Promise<AnomalySummaryStats> {
    return apiClient<AnomalySummaryStats>('/api/v1/anomalies/stats');
  },

  async getAnomalyById(alertId: number): Promise<AnomalyAlert> {
    return apiClient<AnomalyAlert>(`/api/v1/anomalies/${alertId}`);
  },

  async acknowledgeAnomaly(
    alertId: number,
    payload: AnomalyAcknowledgeRequest,
  ): Promise<AnomalyAlert> {
    return apiClient<AnomalyAlert>(`/api/v1/anomalies/${alertId}/acknowledge`, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  async runAutomatedDetection(thresholdSigma = 3.0): Promise<AnomalyDetectionRunResponse> {
    return apiClient<AnomalyDetectionRunResponse>(
      `/api/v1/anomalies/run-detection?threshold_sigma=${thresholdSigma}`,
      {
        method: 'POST',
      },
    );
  },

  async getIsolationForestBenchmark(contamination = 0.03): Promise<IsolationForestBenchmark> {
    return apiClient<IsolationForestBenchmark>(
      `/api/v1/anomalies/benchmark/isolation-forest?contamination=${contamination}`,
    );
  },
};
