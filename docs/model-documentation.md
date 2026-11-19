# NEXORA — Machine Learning & Predictive Analytics Model Documentation

**Document Status:** Complete (Module 12, 13, 16 Baseline)  
**Framework:** Scikit-Learn 1.9.1, NumPy 2.5.5, SciPy 1.18.1  
**Artifact Storage:** `artifacts/models/*.joblib` and `artifacts/model_metadata/*.json`  

---

## 1. Overview & Machine Learning Architecture

Nexora incorporates evaluated machine learning pipelines and unsupervised risk intelligence models designed to deliver actionable business intelligence across three primary predictive domains and one anomaly detection domain:

```
                            ┌───────────────────────────────────────┐
                            │      PostgreSQL 16 Analytical DB      │
                            └───────────────────┬───────────────────┘
                                                │
                                    Feature Engineering Pipeline
                                                │
         ┌──────────────────────────────┬───────┴──────────────────────┬──────────────────────────────┐
         ▼                              ▼                              ▼                              ▼
┌──────────────────┐           ┌──────────────────┐           ┌──────────────────┐           ┌──────────────────┐
│  Customer Churn  │           │  Sales Forecast  │           │  Product Demand  │           │ Anomaly / Risk   │
│  Classification  │           │   Time-Series    │           │    Regression    │           │ Isolation Forest │
├──────────────────┤           ├──────────────────┤           ├──────────────────┤           ├──────────────────┤
│ Candidate: RF    │           │ Candidate: RF    │           │ Candidate: RF    │           │ Model: IsoForest │
│ Baseline: LogReg │           │ Baseline: 7d MA  │           │ Baseline: Linear │           │ Baseline: IQR    │
│ Metric: ROC-AUC  │           │ Metric: MAE/RMSE │           │ Metric: MAE/RMSE │           │ Score: Outlier   │
└──────────────────┘           └──────────────────┘           └──────────────────┘           └──────────────────┘
```

All models are trained deterministically (`random_state=42`) via `scripts/train_models.py` and evaluated against an explicit statistical baseline. Model metadata, performance evaluations, feature importance rankings, and governance notices are serialized to JSON in `artifacts/model_metadata/` and served via REST API at `/api/v1/predictions/models`.

---

## 2. Customer Churn Prediction Model

### 2.1 Problem Formulation & Definition
- **Objective:** Predict the probability of a customer lapsing into churn to enable proactive CRM retention interventions.
- **Target Variable:** `is_churned` (Binary: `1` if days since last order $> 90$ days, `0` otherwise).
- **Dataset Size:** 2,500 enterprise customers with aggregated transaction metrics.

### 2.2 Feature Matrix
| Feature Name | Type | Description |
| :--- | :--- | :--- |
| `order_count` | Integer | Total lifetime completed orders placed by customer |
| `total_spend` | Float | Cumulative gross expenditure in USD |
| `avg_order_value` | Float | Mean monetary value per order |
| `days_as_customer` | Integer | Account age in days since first recorded order |
| `customer_type_enc` | Categorical | Label encoded customer segment (Enterprise, Mid-Market, SMB) |
| `channel_enc` | Categorical | Label encoded primary channel (Direct B2B, Partner, Online) |

### 2.3 Algorithms & Baseline Comparison
- **Candidate Model:** `RandomForestClassifier` (100 estimators, max depth 6, class weight balanced).
- **Baseline Model:** `LogisticRegression` (L2 penalty, liblinear solver).
- **Split:** 80% Train, 20% Holdout Test (stratified).

### 2.4 Evaluated Performance Metrics
| Metric | Baseline (Logistic Regression) | Candidate (Random Forest) |
| :--- | :---: | :---: |
| **ROC-AUC** | 0.7596 | **0.7558** |
| **Accuracy** | 0.7000 | **0.6980** |
| **Precision** | 0.5000 | **0.4950** |
| **Recall** | 0.4267 | **0.3333** |
| **F1-Score** | 0.4604 | **0.3984** |

### 2.5 Feature Importance Ranking
1. `days_as_customer` (38.8%) — Account tenure is the primary indicator of retention stability.
2. `avg_order_value` (25.3%) — High average basket size correlates with recurring enterprise contracts.
3. `order_count` (18.1%) — Purchase frequency indicates active account engagement.
4. `total_spend` (16.2%) — Lifetime monetary commitment.
5. `customer_type_enc` (1.6%) / `channel_enc` (0.0%).

### 2.6 Governance & Ethics Notice
> **Governance Notice:** Probabilistic customer churn model. High-risk flag signals intervention priority; actual retention outcomes depend on customer success follow-up. Model output must not be used to automatically terminate client contracts or penalize accounts.

---

## 3. Daily Sales Revenue Forecasting Model

### 3.1 Problem Formulation & Definition
- **Objective:** Predict daily aggregated gross sales revenue over dynamic forecast horizons (7 to 30 days).
- **Target Variable:** `daily_revenue` (Continuous USD).
- **Dataset Size:** 365 daily revenue aggregates derived from 15,000 historical transactions.

### 3.2 Feature Matrix
| Feature Name | Type | Description |
| :--- | :--- | :--- |
| `day_of_week` | Integer | Day of week index ($0 = \text{Monday}, 6 = \text{Sunday}$) |
| `month` | Integer | Calendar month ($1 - 12$) |
| `is_weekend` | Binary | 1 for Saturday/Sunday, 0 for Monday-Friday |
| `lag_1` | Float | Previous day's revenue in USD |
| `lag_7` | Float | Same day last week revenue in USD |
| `rolling_mean_7` | Float | 7-day backward rolling simple moving average |
| `rolling_mean_14` | Float | 14-day backward rolling simple moving average |

### 3.3 Algorithms & Baseline Comparison
- **Candidate Model:** `RandomForestRegressor` (100 estimators, max depth 5).
- **Baseline Model:** Historical 7-day Moving Average (Rolling Mean).
- **Split:** Chronological 80% Train, 20% Out-of-Time Test.

### 3.4 Evaluated Performance Metrics
| Metric | Baseline (7d Moving Average) | Candidate (Random Forest) |
| :--- | :---: | :---: |
| **MAE (Mean Absolute Error)** | \$148,378.87 | **\$82,439.92** (44.4% error reduction) |
| **RMSE (Root Mean Squared Error)** | \$168,003.73 | **\$109,377.71** (34.9% error reduction) |
| **MAPE (Mean Absolute Percentage Error)** | 62.10% | **35.85%** |

### 3.5 Feature Importance Ranking
1. `rolling_mean_14` (66.8%) — Medium-term baseline revenue trend.
2. `rolling_mean_7` (13.8%) — Short-term momentum.
3. `lag_7` (6.9%) — Weekly seasonality and recurring purchase patterns.
4. `lag_1` (4.4%) — Immediate autocorrelation.
5. Calendar features (`is_weekend`, `day_of_week`, `month`) accounting for remainder.

### 3.6 Governance & Ethics Notice
> **Governance Notice:** Time-series forecasts assume continuity of seasonal demand. Unpredicted macroeconomic shifts or supply chain shocks may increase forecast variance.

---

## 4. Product Demand Forecasting Model

### 4.1 Problem Formulation & Definition
- **Objective:** Forecast weekly product unit sales volume across active catalog SKUs to optimize inventory replenishment thresholds.
- **Target Variable:** `total_units_sold` (Continuous units per SKU).
- **Dataset Size:** Product catalog transaction aggregates across 5 distinct categories.

### 4.2 Feature Matrix
| Feature Name | Type | Description |
| :--- | :--- | :--- |
| `unit_price` | Float | Current SKU list price in USD |
| `order_frequency` | Integer | Total order items containing SKU |
| `total_revenue` | Float | Historical revenue generated by SKU |
| `category_id` | Integer | Product category identifier |

### 4.3 Algorithms & Baseline Comparison
- **Candidate Model:** `RandomForestRegressor` (100 estimators, max depth 5).
- **Baseline Model:** Standard `LinearRegression`.
- **Split:** 80% Train, 20% Test.

### 4.4 Evaluated Performance Metrics
| Metric | Baseline (Linear Regression) | Candidate (Random Forest) |
| :--- | :---: | :---: |
| **MAE (Mean Absolute Error)** | 22.77 units | **13.71 units** (39.8% error reduction) |
| **RMSE (Root Mean Squared Error)** | 29.31 units | **17.16 units** (41.5% error reduction) |

### 4.5 Feature Importance Ranking
1. `order_frequency` (83.9%) — Historical velocity is the dominant driver of demand volume.
2. `total_revenue` (8.6%) — SKU revenue contribution.
3. `unit_price` (4.4%) — Price sensitivity elasticity.
4. `category_id` (3.1%) — Category demand baseline.

### 4.6 Governance & Ethics Notice
> **Governance Notice:** Product demand forecasts support replenishment thresholds; lead-time variance and supplier reliability must be factored into purchase orders.

---

## 5. Anomaly Detection & Risk Intelligence (Unsupervised)

### 5.1 Architecture & Objectives
Nexora implements dual-engine risk intelligence that combines heuristic rule-based detection with unsupervised multivariate machine learning:
1. **Rule-Based Engine (IQR Baseline):** Evaluates univariate statistical outliers using the Interquartile Range ($Q_3 + 1.5 \times \text{IQR}$).
2. **Unsupervised Machine Learning Benchmark (BL-16):** Employs Scikit-Learn `IsolationForest` ($5\%$ contamination rate) across multivariate feature space (Order Gross Amount, Item Count, Unit Price, Velocity).

### 5.2 Mathematical Explanation & Metrics
Every detected anomaly alert provides an objective, mathematical explanation of why it was flagged:
- Flagged fields (e.g., `gross_amount` = \$15,400.00).
- Population baseline statistics: Mean ($\mu$), Median ($Q_2$), Standard Deviation ($\sigma$), and 99th percentile ($P_{99}$).
- Distance metric: Z-Score ($z = \frac{x - \mu}{\sigma}$) and IQR multiplier.

### 5.3 Mandatory Accusation Prohibition Rule (Compliance Standard)
In strict accordance with corporate risk governance standards:
- **Rule:** Explanations generated by the anomaly detection engine or displayed in UI triage modals **MUST NEVER** accuse a customer or user of "fraud", "theft", "crime", or dishonest conduct.
- **Enforcement:** Automated tests (`test_m13_t08`) verify that generated explanations contain zero defamatory or accusatory terminology and focus exclusively on statistical deviations relative to peer baselines.

---

## 6. Retraining & Model Serialization Pipeline

All models can be retrained and persisted in a single command:
```powershell
python scripts/train_models.py
```
This updates:
- Model binaries: `artifacts/models/*.joblib`
- Governance metadata: `artifacts/model_metadata/*.json`
- In-memory inference engine in FastAPI backend without service downtime.
