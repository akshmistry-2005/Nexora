import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { AuthProvider } from '../context/AuthProvider';
import { PredictionsPage } from '../features/predictions/PredictionsPage';

const jsonResponse = (data: unknown) => ({
  ok: true,
  status: 200,
  headers: new Headers({ 'content-type': 'application/json' }),
  json: async () => data,
}) as unknown as Response;

const mockAnalystUser = {
  access_token: 'fake-jwt-token',
  token_type: 'Bearer',
  expires_in_seconds: 7200,
  user_id: 3,
  email: 'demo_analyst@nexora.local',
  full_name: 'Marcus Chen (Data Analyst)',
  role: 'data_analyst',
  permissions: ['dashboard.view', 'predictions.view'],
};

const mockModels = {
  success: true,
  data: [
    {
      model_id: 'customer_churn',
      model_name: 'Customer Churn Prediction',
      problem_type: 'binary_classification',
      target_variable: 'is_churned',
      features: ['tenure_days', 'order_count', 'total_spend'],
      baseline_algorithm: 'LogisticRegression',
      candidate_algorithm: 'RandomForestClassifier',
      hyperparameters: { n_estimators: 100 },
      sample_size_train: 2000,
      sample_size_test: 500,
      split_strategy: 'Stratified 80/20 split',
      baseline_metrics: { roc_auc: 0.72, precision: 0.65 },
      candidate_metrics: { roc_auc: 0.756, precision: 0.86 },
      overfitting_gap: 0.04,
      feature_importances: { tenure_days: 0.65 },
      trained_at: '2026-11-19T10:00:00Z',
      artifact_path: 'artifacts/models/customer_churn.joblib',
      is_loaded: true,
      governance_notice: 'Probabilistic customer churn model.',
    },
    {
      model_id: 'sales_forecast',
      model_name: 'Sales Revenue Forecasting',
      problem_type: 'regression_time_series',
      target_variable: 'daily_revenue',
      features: ['lag_1', 'lag_7'],
      baseline_algorithm: 'DummyRegressor (Mean)',
      candidate_algorithm: 'RandomForestRegressor',
      hyperparameters: { n_estimators: 100 },
      sample_size_train: 770,
      sample_size_test: 190,
      split_strategy: 'Chronological 80/20 split',
      baseline_metrics: { mae: 148000, rmse: 168000 },
      candidate_metrics: { mae: 82440, rmse: 109000, mape: 35.8 },
      overfitting_gap: 12000,
      feature_importances: { lag_1: 0.4 },
      trained_at: '2026-11-19T10:00:00Z',
      artifact_path: 'artifacts/models/sales_forecast.joblib',
      is_loaded: true,
      governance_notice: 'Time-series forecasts assume continuity.',
    },
  ],
};

const mockHighRiskCustomers = {
  success: true,
  data: [
    {
      customer_id: 101,
      company_name: 'Apex Industrial Supply',
      contact_name: 'Sarah Connor',
      email: 'sconnor@apex.local',
      customer_type: 'Enterprise',
      lifetime_spend: 54000,
      order_count: 14,
      days_since_last_order: 112,
      churn_probability: 0.842,
      risk_tier: 'High',
    },
  ],
};

const mockSimResult = {
  success: true,
  data: {
    churn_probability: 0.785,
    is_churn_predicted: true,
    risk_tier: 'High',
    contributing_factors: [
      { factor: 'Order Inactivity', impact: 'High Risk', description: '45 days without a purchase.' },
    ],
    model_id: 'customer_churn',
    governance_notice: 'Probabilistic customer churn model.',
  },
};

const mockSalesForecast = {
  success: true,
  data: {
    horizon_days: 30,
    model_id: 'sales_forecast',
    total_forecasted_revenue: 2850000,
    evaluation_metrics: { mae: 82440, rmse: 109000 },
    baseline_metrics: { mae: 148000 },
    forecast_series: [
      { date: '2026-11-15', forecasted_revenue: 95000, lower_bound_95: 75000, upper_bound_95: 115000 },
      { date: '2026-11-16', forecasted_revenue: 92000, lower_bound_95: 71000, upper_bound_95: 113000 },
    ],
    historical_series: [
      { date: '2026-11-13', revenue: 89000 },
      { date: '2026-11-14', revenue: 91000 },
    ],
    governance_notice: 'Time series assumptions apply.',
  },
};

const mockDemandForecast = {
  success: true,
  data: {
    total_products: 1,
    reorder_count: 1,
    products: [
      {
        product_id: 1,
        sku: 'NX-SEC-100',
        name: 'Nexora Security Key Pro',
        category_name: 'Security',
        unit_price: 120.0,
        current_stock: 45,
        target_stock: 250,
        forecasted_monthly_demand: 180,
        reorder_recommended: true,
      },
    ],
    evaluation_metrics: { mae: 13.7 },
    governance_notice: 'Demand planning estimates.',
  },
};

describe('Module 12 — Predictive Analytics Frontend', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    localStorage.clear();
  });

  it('renders predictions header, model governance notice, and top KPI cards', async () => {
    vi.spyOn(globalThis, 'fetch').mockImplementation(async (input) => {
      const url = String(input);
      if (url.includes('/api/v1/auth/')) {
        return jsonResponse({ success: true, data: mockAnalystUser });
      }
      if (url.includes('/api/v1/predictions/models')) {
        return jsonResponse(mockModels);
      }
      return jsonResponse({ success: true, data: null });
    });

    render(
      <MemoryRouter>
        <AuthProvider>
          <PredictionsPage />
        </AuthProvider>
      </MemoryRouter>,
    );

    // Title and mandatory governance alert banner (M12-T16)
    expect(screen.getByText('Predictive Models & Demand Forecasting')).toBeInTheDocument();
    expect(screen.getByText(/Predictions are generated from validated scikit-learn pipeline/i)).toBeInTheDocument();

    // Check KPI cards
    await waitFor(() => {
      expect(screen.getByText('Churn Model ROC-AUC')).toBeInTheDocument();
      expect(screen.getByText('Forecast MAE')).toBeInTheDocument();
      expect(screen.getByText('Churn Precision')).toBeInTheDocument();
      expect(screen.getByText('Active ML Pipelines')).toBeInTheDocument();
    });

    // Governance table
    expect(screen.getByText('Candidate vs. Baseline Performance Comparison (M12-T05)')).toBeInTheDocument();
    expect(screen.getByText('Customer Churn Prediction')).toBeInTheDocument();
    expect(screen.getByText('Sales Revenue Forecasting')).toBeInTheDocument();
  });

  it('switches to customer churn tab, renders high-risk queue, and runs interactive simulator', async () => {
    vi.spyOn(globalThis, 'fetch').mockImplementation(async (input) => {
      const url = String(input);
      if (url.includes('/api/v1/auth/')) {
        return jsonResponse({ success: true, data: mockAnalystUser });
      }
      if (url.includes('/api/v1/predictions/models')) {
        return jsonResponse(mockModels);
      }
      if (url.includes('/api/v1/predictions/churn/high-risk')) {
        return jsonResponse(mockHighRiskCustomers);
      }
      if (url.includes('/api/v1/predictions/churn/predict')) {
        return jsonResponse(mockSimResult);
      }
      return jsonResponse({ success: true, data: null });
    });

    render(
      <MemoryRouter>
        <AuthProvider>
          <PredictionsPage />
        </AuthProvider>
      </MemoryRouter>,
    );

    const churnTab = screen.getByText('Customer Churn Classifier');
    fireEvent.click(churnTab);

    await waitFor(() => {
      expect(screen.getByText('Interactive Customer Churn Simulator')).toBeInTheDocument();
      expect(screen.getByText('High-Risk Churn Account Intervention Queue')).toBeInTheDocument();
      expect(screen.getByText('Apex Industrial Supply')).toBeInTheDocument();
    });

    // Run simulator
    const scoreBtn = screen.getByText('Score Churn Risk');
    fireEvent.click(scoreBtn);

    await waitFor(() => {
      expect(screen.getByText(/Churn Probability: 78.5%/i)).toBeInTheDocument();
      expect(screen.getByText('Risk Tier: High')).toBeInTheDocument();
    });
  });

  it('switches to sales forecasting and SKU demand tabs', async () => {
    vi.spyOn(globalThis, 'fetch').mockImplementation(async (input) => {
      const url = String(input);
      if (url.includes('/api/v1/auth/')) {
        return jsonResponse({ success: true, data: mockAnalystUser });
      }
      if (url.includes('/api/v1/predictions/models')) {
        return jsonResponse(mockModels);
      }
      if (url.includes('/api/v1/predictions/sales/forecast')) {
        return jsonResponse(mockSalesForecast);
      }
      if (url.includes('/api/v1/predictions/demand/forecast')) {
        return jsonResponse(mockDemandForecast);
      }
      return jsonResponse({ success: true, data: null });
    });

    render(
      <MemoryRouter>
        <AuthProvider>
          <PredictionsPage />
        </AuthProvider>
      </MemoryRouter>,
    );

    // Sales tab
    const salesTab = screen.getByText('Sales Time-Series Forecasting');
    fireEvent.click(salesTab);

    await waitFor(() => {
      expect(screen.getByText(/Sales Revenue Projections/i)).toBeInTheDocument();
      expect(screen.getByText('$95,000')).toBeInTheDocument();
    });

    // Demand tab
    const demandTab = screen.getByText('SKU Demand & Replenishment');
    fireEvent.click(demandTab);

    await waitFor(() => {
      expect(screen.getByText('SKU Monthly Demand & Replenishment Thresholds')).toBeInTheDocument();
      expect(screen.getByText('Nexora Security Key Pro')).toBeInTheDocument();
      expect(screen.getByText('Reorder Needed')).toBeInTheDocument();
    });
  });
});
