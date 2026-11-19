# Module Completion Report

**Module number:** 12  
**Module name:** Predictive Analytics & ML Engine  
**Development status:** Completed  
**Date:** 2026-11-19  
**Environment:** Windows (FastAPI 0.164.0, SQLAlchemy 2.0.44, PostgreSQL 16 Alpine, Scikit-learn 1.9.1, SciPy 1.18.1, NumPy 2.5.5, Vite 6.0, React 19, TypeScript 5.7)

---

## Test Execution Summary

| Test status | Count |
| :--- | :---: |
| Total applicable test cases | 17 |
| Passed | 17 |
| Failed | 0 |
| Blocked | 0 |
| Not executed | 0 |

---

## Individual Test Results

| Test ID | Test description | Expected result | Actual result | Status |
| :--- | :--- | :--- | :--- | :---: |
| `M12-T01` | Model problem definition | Explicit ML problem formulations for Churn (classification), Sales Forecast (time-series regression), and Product Demand (SKU regression). | Verified models metadata lists explicit formulation, target variables, and feature spaces. | **PASS** |
| `M12-T02` | Dataset suitability | Datasets meet sample size bounds: customers >= 100, orders >= 1000, daily time-series >= 60, products >= 20. | Verified live DB row counts (2,500 customers, 15,000 orders, 971 distinct daily observations, 120 products). | **PASS** |
| `M12-T03` | Data leakage prevention | Chronological forward-facing temporal split without future lookahead; feature matrices exclude thresholded targets; scalers fit on train only. | Verified sales forecasting uses strictly chronological 80/20 train/test split, scaler fitted exclusively on training set, and churn target threshold isolated. | **PASS** |
| `M12-T04` | Baseline model training | Naive baseline models trained and evaluated: LogisticRegression for churn, DummyRegressor (mean) for sales and demand. | Verified baseline models logged with ROC-AUC (0.72) and MAE ($148,378.87 / 22.77) in metadata. | **PASS** |
| `M12-T05` | Candidate comparison | Candidate Random Forest models outperform or benchmark baseline models on primary holdout test metrics. | Verified candidate sales MAE ($82,439.92) is significantly lower than baseline MAE ($148,378.87); demand candidate MAE (13.71) beats baseline (22.77). | **PASS** |
| `M12-T06` | Regression metrics (MAE/RMSE) | Holdout evaluation computes MAE, RMSE, and MAPE; mathematical property $RMSE \ge MAE$ holds. | Verified holdout regression metrics: $RMSE = 109,377.71 \ge MAE = 82,439.92$ on sales test split. | **PASS** |
| `M12-T07` | Classification metrics (Precision/Recall/F1/ROC-AUC) | Precision, Recall, F1, and ROC-AUC computed strictly on holdout test set with values in $[0.0, 1.0]$. | Verified churn classification metrics: ROC-AUC = 0.7558, Precision = 0.495, Recall = 0.333, F1 = 0.398. | **PASS** |
| `M12-T08` | Overfitting check | Generalization gap between training metrics and holdout test metrics evaluated and bounded. | Verified ROC-AUC generalization gap is 0.04 (< 0.35 threshold), indicating stable variance. | **PASS** |
| `M12-T09` | Repeatable training | Fixed random seed (`random_state=42`) across splitters and estimators yields bitwise identical metrics. | Verified consecutive training executions produce identical JSON candidate and baseline metrics. | **PASS** |
| `M12-T10` | Model metadata persistence | Complete metadata saved to `artifacts/model_metadata/<model_id>.json` with features, metrics, and timestamps. | Verified all 3 metadata JSON artifacts present with complete schema validation. | **PASS** |
| `M12-T11` | Model loading | Model pipeline artifacts (.joblib) persisted and loaded cleanly into memory with fitted scalers and models. | Verified `_get_or_load_pipeline` successfully loads all three pipeline objects from disk. | **PASS** |
| `M12-T12` | Prediction API endpoints | Real-time prediction endpoints for single churn inference, sales forecasting, and demand planning. | Verified `POST /churn/predict`, `GET /sales/forecast`, and `GET /demand/forecast` return structured predictions. | **PASS** |
| `M12-T13` | Invalid inference input | Input validation returns HTTP 422 for negative tenures, invalid horizons, or malformed payloads. | Verified negative tenure returns 422; horizon > 365 returns 422 Unprocessable Content. | **PASS** |
| `M12-T14` | Batch vs API consistency | Batch inference API produces identical predictions to individual single-record inferences. | Verified batch churn scoring strictly matches single inference probabilities within 1e-4 tolerance. | **PASS** |
| `M12-T15` | Prediction UI integration | Endpoints supporting interactive UI views (high-risk queue, model listing, RBAC access denial). | Verified `GET /churn/high-risk` returns prioritized CRM queue; general viewer is denied access with HTTP 403. | **PASS** |
| `M12-T16` | Prediction limitations notice | Prominent governance notice on assumptions and limitations present on all API outputs and UI header. | Verified `"Model Governance"` alert in UI and `governance_notice` string present on every endpoint payload. | **PASS** |
| `M12-T17` | Missing model artifact handling | Missing model artifacts return HTTP 404/503 gracefully without unhandled 500 crashes. | Verified requesting non-existent model returns HTTP 404 with structured JSON error response. | **PASS** |

---

## Defects Identified & Fixed

1. **Defect:** PostgreSQL `EXTRACT(DAY FROM ('2026-11-14' - c.signup_date))` threw `function extract(unknown, integer) does not exist` because subtracting two dates in PostgreSQL yields an integer directly.  
   **Fix:** Simplified expression to `('2026-11-14'::date - c.signup_date) as tenure_days`.
2. **Defect:** Including `days_since_last_order` directly in features when churn target was thresholded on `days_since_last_order > 90` caused target leakage (1.0 ROC-AUC).  
   **Fix:** Removed raw recency column from training features to adhere strictly to `M12-T03` Data Leakage Prevention.
3. **Defect:** `psycopg.errors.AmbiguousParameter` raised in `forecast_product_demand` on untyped `WHERE (:cat_id IS NULL OR p.category_id = :cat_id)` with `None` parameter.  
   **Fix:** Switched to dynamic query construction appending `WHERE p.category_id = :cat_id` only when `category_id` is specified.
4. **Defect:** FastAPI `Annotated[int, Query(default=25, ge=1)]` threw `AssertionError: Query default value cannot be set in Annotated`.  
   **Fix:** Set default using assignment `= 25` outside the `Query()` annotation.
5. **Defect:** `PredictionsPage.tsx` imported `useAuth` from `../../context/AuthProvider` instead of `../../hooks/useAuth`, causing `useAuth is not a function` in tests.  
   **Fix:** Corrected import path to `../../hooks/useAuth`.

---

## Retesting Results

- Backend Module 12 tests: 17 passed in `backend/tests/test_m12_predictions.py` — **PASS**
- Cumulative backend regression: 119 passed across all test files (`test_m02` through `test_m12`) in 22.89s — **PASS**
- Backend code quality: `ruff check` (0 errors), `ruff format --check` (0 errors across 82 files), `mypy app` (0 errors across 71 files) — **PASS**
- Frontend component tests: 27 passed across 8 test files (`App.test.tsx`, `test_m06`, `test_m07`, `test_m08`, `test_m09`, `test_m10`, `test_m11`, `test_m12`) — **PASS**
- Frontend lint & typecheck: `npm run lint` (0 errors), `npm run typecheck` (0 errors) — **PASS**
- Production bundle: `npm run build` (`tsc -b && vite build`) — **PASS**
