import {
  ComputeStatsPayload,
  CorrelationMatrix,
  DescriptiveStats,
  HypothesisTest,
  HypothesisTestPayload,
} from '../types/statistics';
import { apiClient } from './api';

export const statisticsService = {
  async getDescriptiveStats(entity = 'orders', field = 'total_amount'): Promise<DescriptiveStats> {
    return apiClient<DescriptiveStats>(
      `/api/v1/statistics/descriptive?entity=${encodeURIComponent(entity)}&field=${encodeURIComponent(field)}`,
    );
  },

  async computeStatsVector(payload: ComputeStatsPayload): Promise<DescriptiveStats> {
    return apiClient<DescriptiveStats>('/api/v1/statistics/compute', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  async getCorrelationMatrix(entity = 'orders'): Promise<CorrelationMatrix> {
    return apiClient<CorrelationMatrix>(
      `/api/v1/statistics/correlation?entity=${encodeURIComponent(entity)}`,
    );
  },

  async runHypothesisTest(payload: HypothesisTestPayload): Promise<HypothesisTest> {
    return apiClient<HypothesisTest>('/api/v1/statistics/hypothesis-test', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  async getChannelComparison(): Promise<HypothesisTest> {
    return apiClient<HypothesisTest>('/api/v1/statistics/channel-comparison');
  },
};
