export interface ModelMetadata {
  model_id: string;
  model_name: string;
  problem_type: string;
  target_variable: string;
  features: string[];
  baseline_algorithm: string;
  candidate_algorithm: string;
  hyperparameters: Record<string, unknown>;
  sample_size_train: number;
  sample_size_test: number;
  split_strategy: string;
  baseline_metrics: Record<string, number>;
  candidate_metrics: Record<string, number>;
  overfitting_gap?: number | null;
  feature_importances: Record<string, number>;
  trained_at: string;
  artifact_path: string;
  is_loaded: boolean;
  governance_notice: string;
}

export interface ChurnPredictionInput {
  tenure_days: number;
  order_count: number;
  total_spend: number;
  avg_order_value: number;
  days_since_last_order?: number;
  returns_count?: number;
  customer_type?: string;
  acquisition_channel?: string;
}

export interface ContributingFactor {
  factor: string;
  impact: string;
  description: string;
}

export interface ChurnPredictionResult {
  churn_probability: number;
  is_churn_predicted: boolean;
  risk_tier: 'Low' | 'Medium' | 'High';
  contributing_factors: ContributingFactor[];
  model_id: string;
  governance_notice: string;
}

export interface HighRiskCustomer {
  customer_id: number;
  company_name: string | null;
  contact_name: string;
  email: string;
  customer_type: string;
  lifetime_spend: number;
  order_count: number;
  days_since_last_order: number;
  churn_probability: number;
  risk_tier: string;
}

export interface SalesForecastPoint {
  date: string;
  forecasted_revenue: number;
  lower_bound_95: number;
  upper_bound_95: number;
}

export interface SalesForecastData {
  horizon_days: number;
  model_id: string;
  total_forecasted_revenue: number;
  evaluation_metrics: Record<string, number>;
  baseline_metrics: Record<string, number>;
  forecast_series: SalesForecastPoint[];
  historical_series: Array<{ date: string; revenue: number }>;
  governance_notice: string;
}

export interface ProductDemandItem {
  product_id: number;
  sku: string;
  name: string;
  category_name: string;
  unit_price: number;
  current_stock: number;
  target_stock: number;
  forecasted_monthly_demand: number;
  reorder_recommended: boolean;
}

export interface ProductDemandData {
  total_products: number;
  reorder_count: number;
  products: ProductDemandItem[];
  evaluation_metrics: Record<string, number>;
  governance_notice: string;
}
