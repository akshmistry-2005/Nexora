import {
  ApproveCuratedResponse,
  CleanStagingResponse,
  QualityEvaluationReport,
  SystemQualitySummary,
} from '../types/dataQuality';
import { apiClient } from './api';

export const dataQualityService = {
  async getSystemQualitySummary(): Promise<SystemQualitySummary> {
    return apiClient<SystemQualitySummary>('/api/v1/data-quality/summary');
  },

  async evaluateStagingJob(importJobId: number): Promise<QualityEvaluationReport> {
    return apiClient<QualityEvaluationReport>(`/api/v1/data-quality/evaluations/${importJobId}`);
  },

  async cleanStagingJob(
    importJobId: number,
    options?: {
      auto_impute_missing?: boolean;
      standardize_categories?: boolean;
      standardize_dates?: boolean;
    },
  ): Promise<CleanStagingResponse> {
    return apiClient<CleanStagingResponse>(`/api/v1/data-quality/clean/${importJobId}`, {
      method: 'POST',
      body: JSON.stringify(options || {}),
    });
  },

  async approveCurated(importJobId: number): Promise<ApproveCuratedResponse> {
    return apiClient<ApproveCuratedResponse>(`/api/v1/data-quality/approve/${importJobId}`, {
      method: 'POST',
    });
  },
};
