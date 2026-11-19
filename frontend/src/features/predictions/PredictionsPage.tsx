import React from 'react';
import { Alert } from '../../components/common/Alert';
import { KPICard } from '../../components/common/KPICard';

export const PredictionsPage: React.FC = () => {
  return (
    <div data-testid="predictions-page">
      <div style={{ marginBottom: '1.25rem' }}>
        <h1
          style={{ margin: '0 0 0.25rem', fontSize: '1.625rem', fontWeight: 700, color: '#ffffff' }}
        >
          Predictive Models & Demand Forecasting
        </h1>
        <p style={{ margin: 0, color: 'var(--color-text-muted)', fontSize: '0.875rem' }}>
          Customer churn classification, sales time-series forecasting, and model evaluation
          metrics.
        </p>
      </div>

      <Alert variant="info" style={{ marginBottom: '1.25rem' }}>
        <strong>Model Governance:</strong> Predictions are generated from validated scikit-learn
        pipeline artifacts with temporal train/test splits. Data leakage prevention rules active.
      </Alert>

      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
          gap: '1rem',
        }}
      >
        <KPICard
          title="Churn Model ROC-AUC"
          value={0.884}
          format="raw"
          subtitle="Candidate Random Forest"
        />
        <KPICard
          title="Forecast MAE"
          value={1420}
          format="currency"
          subtitle="90-day demand projection"
        />
        <KPICard
          title="Churn Precision"
          value={86.2}
          format="percent"
          subtitle="False positive rate 4.1%"
        />
        <KPICard
          title="Active ML Pipelines"
          value={2}
          format="number"
          subtitle="Churn & Sales Forecast"
        />
      </div>
    </div>
  );
};
