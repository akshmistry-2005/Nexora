import {
  ChurnPredictionInput,
  ChurnPredictionResult,
  HighRiskCustomer,
  ModelMetadata,
  ProductDemandData,
  SalesForecastData,
} from '../types/predictions';
import { apiClient } from './api';

export const predictionsService = {
  async listModels(): Promise<ModelMetadata[]> {
    return apiClient<ModelMetadata[]>('/api/v1/predictions/models');
  },

  async getModelMetadata(modelId: string): Promise<ModelMetadata> {
    return apiClient<ModelMetadata>(`/api/v1/predictions/models/${encodeURIComponent(modelId)}`);
  },

  async predictChurn(input: ChurnPredictionInput): Promise<ChurnPredictionResult> {
    return apiClient<ChurnPredictionResult>('/api/v1/predictions/churn/predict', {
      method: 'POST',
      body: JSON.stringify(input),
    });
  },

  async getHighRiskCustomers(limit = 25): Promise<HighRiskCustomer[]> {
    return apiClient<HighRiskCustomer[]>(`/api/v1/predictions/churn/high-risk?limit=${limit}`);
  },

  async forecastSales(horizonDays = 30): Promise<SalesForecastData> {
    return apiClient<SalesForecastData>(
      `/api/v1/predictions/sales/forecast?horizon_days=${horizonDays}`,
    );
  },

  async forecastDemand(limit = 15, categoryId?: number): Promise<ProductDemandData> {
    const query = new URLSearchParams({ limit: String(limit) });
    if (categoryId !== undefined) {
      query.append('category_id', String(categoryId));
    }
    return apiClient<ProductDemandData>(`/api/v1/predictions/demand/forecast?${query.toString()}`);
  },

  async reloadModel(modelId: string): Promise<ModelMetadata> {
    return apiClient<ModelMetadata>(
      `/api/v1/predictions/models/${encodeURIComponent(modelId)}/reload`,
      {
        method: 'POST',
      },
    );
  },
};
