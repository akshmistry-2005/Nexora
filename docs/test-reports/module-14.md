# Module Completion Report

**Module number:** 14  
**Module name:** Pipeline Monitoring, Auditability and Administration  
**Development status:** Completed  
**Date:** 2026-11-19  
**Environment:** Windows (FastAPI 0.164.0, SQLAlchemy 2.0.44, PostgreSQL 16 Alpine, Scikit-learn 1.9.1, SciPy 1.18.1, NumPy 2.5.5, Vite 6.0, React 19, TypeScript 5.7)

---

## Test Execution Summary

| Test status | Count |
| :--- | :---: |
| Total applicable test cases | 13 |
| Passed | 13 |
| Failed | 0 |
| Blocked | 0 |
| Not executed | 0 |

---

## Individual Test Results

| Test ID | Test description | Expected result | Actual result | Status |
| :--- | :--- | :--- | :--- | :---: |
| `M14-T01` | Pipeline run creation | Data pipeline runs created in `pipeline_runs` with status 'running' and initial telemetry. | Verified creation of `PipelineRun` records with started timestamp, pipeline process name, and JSON metrics. | **PASS** |
| `M14-T02` | Pipeline metadata | Pipeline metadata tracks process name, duration in ms, start/end timestamps, and structured JSON metrics. | Verified pipeline run API detail endpoint `/api/v1/pipelines/runs/{id}` returns complete duration and execution metrics. | **PASS** |
| `M14-T03` | Failed pipeline visibility | Failed pipelines capture error information and are queryable via `status=failed` filter. | Verified failed runs record error messages and failing stages in `metrics` and filter cleanly on `/api/v1/pipelines/runs?status=failed`. | **PASS** |
| `M14-T04` | Last successful refresh preservation | Failed pipeline run does NOT overwrite or corrupt the timestamp of the last successful refresh. | Verified `/api/v1/pipelines/summary` preserves historical successful refresh timestamp even when subsequent runs fail. | **PASS** |
| `M14-T05` | Safe retry | Safe retry marks prior run as 'retried' and spins up an isolated retry attempt without state corruption. | Verified `POST /api/v1/pipelines/runs/{id}/retry` transitions old run to 'retried', instantiates new run, and logs audit record. | **PASS** |
| `M14-T06` | Audit login events | User authentication attempts (success and invalid credentials) create append-only audit entries. | Verified `AUTH_LOGIN_SUCCESS` and `AUTH_LOGIN_FAILURE` records created in `audit_logs` with actor role and email details. | **PASS** |
| `M14-T07` | Audit import/export events | Ingestion jobs and report export operations record append-only audit trail entries. | Verified `REPORT_EXPORT` audit log entry generated upon CSV export with report ID, user ID, and format metadata. | **PASS** |
| `M14-T08` | Audit admin events | Administrative operations (role modification, pipeline retries, system resets) log audit records. | Verified `PIPELINE_RETRY` and `USER_ROLE_UPDATE` actions create structured audit logs. | **PASS** |
| `M14-T09` | Audit log append-only protection | Direct `UPDATE` and `DELETE` queries on `audit_logs` are strictly blocked by PostgreSQL trigger. | Verified PostgreSQL trigger `trg_audit_logs_immutable` raises exception rejecting modification or deletion. | **PASS** |
| `M14-T10` | Demo role restrictions | Public demonstration roles receive HTTP 403 Forbidden for restricted administrative actions. | Verified Data Analyst and General Viewer received 403 on `/admin/reset-demo`, `/admin/users`, and pipeline retry endpoints. | **PASS** |
| `M14-T11` | Owner administration | Platform Owner has full access to audit trails, user directory, and pipeline telemetry. | Verified Owner successfully inspects `/admin/audit-logs`, `/admin/users`, and `/pipelines/summary`. | **PASS** |
| `M14-T12` | Owner-only reset | Demonstration environment reset is strictly restricted to Platform Owner. | Verified Owner executes `POST /api/v1/admin/reset-demo` (200 OK) with `ADMIN_SYSTEM_RESET` audit log; demo users get 403. | **PASS** |
| `M14-T13` | Synthetic-data notice | Prominent synthetic demonstration environment notices present in telemetry and admin endpoints. | Verified `synthetic_data_notice` present in system status and pipeline health scorecard payloads and UI header. | **PASS** |

---

## Defects Identified & Fixed

1. **Defect:** `backend/app/services/admin.py` attempted to import `Customer, Order, Product` from non-existent module `app.models.domain`.  
   **Fix:** Updated imports to point to `app.models.customer`, `app.models.order`, and `app.models.product`.
2. **Defect:** `test_m14_t07` called `/api/v1/reports/export` with uncatalogued `report_type="sales_summary"` returning HTTP 404.  
   **Fix:** Updated test payload to `/api/v1/reports/export/csv` referencing valid catalogue ID `sales-performance`.
3. **Defect:** `mypy` reported incompatible type assignment in `pipelines.py` and `admin.py` when unpacking `runs, _ = ...` and `logs, _ = ...` due to `_` being annotated as `AuthenticatedUser`.  
   **Fix:** Renamed unpack target to `_total`.
4. **Defect:** `AdminPage.tsx` passed `variant="danger"` to `<Alert>`, violating TypeScript's `'info' | 'success' | 'warning' | 'error'`.  
   **Fix:** Corrected variant to `variant="error"`.
5. **Defect:** `test_m14_administration.test.tsx` lacked `is_owner: true` in mock auth response, causing initial render to resolve as demo role.  
   **Fix:** Added `is_owner: true` and pre-populated `nexora_auth_token` in `localStorage` in `beforeEach`.

---

## Retesting Results

- Backend Module 14 tests: 13 passed in `backend/tests/test_m14_administration.py` — **PASS**
- Cumulative backend regression: 145 passed across all test files (`test_m02` through `test_m14`) — **PASS**
- Backend code quality: `ruff check` (0 errors), `ruff format --check` (0 errors across 93 files), `mypy app` (0 errors across 80 files) — **PASS**
- Frontend component tests: 33 passed across 10 test files (including 3/3 for `test_m14_administration.test.tsx`) — **PASS**
- Frontend lint & typecheck: `npm run lint` (0 errors), `npm run typecheck` (0 errors) — **PASS**
- Production bundle: `npm run build` (`tsc -b && vite build`) — **PASS**
