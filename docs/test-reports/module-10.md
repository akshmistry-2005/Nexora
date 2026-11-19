# Module Completion Report

**Module number:** 10  
**Module name:** Reports, Exports and Saved Views  
**Development status:** Completed  
**Date:** 2026-11-19  
**Environment:** Windows (FastAPI 0.164.0, SQLAlchemy 2.0.44, PostgreSQL 16 Alpine, Vite 6.0, React 19, TypeScript 5.7)

---

## Test Execution Summary

| Test status | Count |
| :--- | :---: |
| Total applicable test cases | 12 |
| Passed | 12 |
| Failed | 0 |
| Blocked | 0 |
| Not executed | 0 |

---

## Individual Test Results

| Test ID | Test description | Expected result | Actual result | Status |
| :--- | :--- | :--- | :--- | :---: |
| `M10-T01` | Report catalogue | 8 structured reports matching all 8 business domains available via API & UI. | Verified `GET /api/v1/reports/catalogue` returns 8 reports across Overview, Sales, Customer, Marketing, Finance, Inventory, Operations, and Supplier. | **PASS** |
| `M10-T02` | Report data accuracy | Report totals and row items match live DB queries and aggregated formulas. | Verified `GET /api/v1/reports/sales-performance/data` matches DB order volumes and revenue. | **PASS** |
| `M10-T03` | Saved view creation | User view filter configurations are persisted into the `saved_views` table with audit trail. | Verified `POST /api/v1/reports/saved-views` creates record in `saved_views` and logs `AuditLog`. | **PASS** |
| `M10-T04` | Saved view restoration & access | Saved views are retrieved; private views cannot be accessed or deleted by unauthorized roles. | Verified private view returns 403 to general viewer, accessible to creator, and deletable by creator. | **PASS** |
| `M10-T05` | CSV export generation | Streams valid CSV format with RFC 4180 compliance and attachment headers. | Verified `GET /api/v1/reports/sales-performance/export/csv` returns `text/csv` with disposition header. | **PASS** |
| `M10-T06` | Export reconciliation | Row sums in generated CSV match reported API and DB revenue totals. | Verified sum of `net_revenue` in parsed CSV rows equals API reported revenue exactly. | **PASS** |
| `M10-T07` | Export metadata & synthetic notice | CSV contains header metadata lines, timestamp, actor, and synthetic demonstration notice. | Verified `# Notice: Synthetic Data Demonstration — Generated for Local Analytics Evaluation` and export metadata rows in CSV header. | **PASS** |
| `M10-T08` | Export permissions | `report.export` permission strictly enforced; 401 unauth, 403 viewer, 200 analyst/owner. | Verified unauthenticated client returns 401, general viewer returns 403, and analyst returns 200. | **PASS** |
| `M10-T09` | Restricted field protection | Internal cost/margin fields omitted for roles lacking `report.sensitive_fields`. | Verified `department_manager` export strips `cost_of_goods_sold` and `gross_margin`, while `data_analyst` includes them. | **PASS** |
| `M10-T10` | Formula injection protection | Neutralizes cells starting with `=`, `+`, `-`, `@`, `\t`, `\r` (CWE-1236 / RFC 4180). | Verified formula cells prefixed with single quote `'`; numeric values preserved as numbers. | **PASS** |
| `M10-T11` | Large export handling | Export limit safely capped at `settings.max_export_rows` and streamed in chunks. | Verified request with `limit=60000` is safely capped and streamed without memory crash. | **PASS** |
| `M10-T12` | PDF export clean deferral | Server-side PDF export returns clean 501 Not Implemented; UI shows no broken button. | Verified `/export/pdf` returns 501 with informative deferral notice; UI presents disabled v1.1 badge. | **PASS** |

---

## Defects Identified & Fixed

1. **Defect:** `TimestampMixin` does not have an `updated_at` column, triggering mypy error on `SavedView.updated_at`.  
   **Fix:** Updated `SavedViewRead` conversion to set `updated_at=None`.
2. **Defect:** Email mismatch in `test_m10_t07_export_metadata_and_synthetic_notice` (`demo.analyst` vs `demo_analyst`).  
   **Fix:** Aligned assertion with seeded email address `demo_analyst@nexora.local`.
3. **Defect:** Query validation `limit: int = Query(default=10000, le=50000)` returned 422 on `limit=60000` instead of graceful capping.  
   **Fix:** Replaced strict Pydantic `le=50000` validation with internal `limit = min(limit, settings.max_export_rows)` logic.
4. **Defect:** `AuthProvider.tsx` threw `TypeError: Cannot read properties of undefined (reading 'includes')` when `user.permissions` was undefined during test mocking.  
   **Fix:** Hardened `hasPermission` with optional chaining: `Boolean(user.permissions?.includes(permissionCode))`.
5. **Defect:** `ReportsPage.tsx` passed `limit` as 3rd parameter to `reportsService.getReportData` and `downloadCsv` instead of inside the filter object.  
   **Fix:** Corrected call signatures to `{ limit: 500 }` and `{ limit: 10000 }`.
6. **Defect:** `DataTableProps` used `loading` prop rather than `isLoading`.  
   **Fix:** Updated `ReportsPage.tsx` table props to `loading={loading}`.

---

## Retesting Results

- Backend Module 10 tests: 12 passed in `backend/tests/test_m10_reports.py` — **PASS**
- Cumulative backend regression: 89 passed across all test files (`test_m02` through `test_m10`) — **PASS**
- Backend code quality: `ruff check` (0 errors), `ruff format --check` (0 errors), `mypy app` (0 errors across 64 files) — **PASS**
- Frontend component tests: 21 passed across 6 test files (`App.test.tsx`, `test_m06`, `test_m07`, `test_m08`, `test_m09`, `test_m10`) — **PASS**
- Frontend lint & typecheck: `npm run lint` (0 errors), `npm run typecheck` (0 errors) — **PASS**
- Production bundle: `npm run build` (`tsc -b && vite build`) — **PASS**
