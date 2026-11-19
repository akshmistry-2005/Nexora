# NEXORA — Master Test Plan & Module Gate Registry

**Document Status:** Active Living Document (Initialized in Module 1)  
**Compliance:** Enforces the *Nexora Mandatory Module-Wise Testing, Validation & Development Gate System*.

---

## 1. Testing Strategy & Gate Rules

### 1.1 Mandatory Module Development Cycle
Every module strictly follows:
```text
Understand → Implement → Test → Identify Failures → Fix → Retest
→ Regression Test → Document → Commit Checkpoint → Approve Module → Next Module
```

### 1.2 Non-Negotiable Rules
1. **Strict 16-Module Sequence:** Never skip, reorder, or merge modules.
2. **Stop-on-Failure:** Even one failing mandatory test halts progression until root-caused, fixed, retested, and verified.
3. **No Test Manipulation:** Never delete, weaken, disable, hard-code around, or fabricate test results.
4. **Real Verification:** Database, RBAC, analytics, ML, and export workflows are tested against real PostgreSQL tables and real backend APIs—never mocked to claim DB behavior works.
5. **Cumulative Regression:** Before closing Module $N$, relevant automated regression suites for Modules $1 \dots N-1$ are rerun and recorded in `docs/test-reports/module-NN.md`.
6. **Git Checkpoints:** Every module that passes its gate receives a dedicated Git commit recorded in its completion report.

---

## 2. Test Execution Architecture

| Layer | Toolchain | Scope |
| :--- | :--- | :--- |
| **Backend Unit & Analytics** | `pytest` | Metric formulas, data cleaning rules, 5 quality dimensions, statistical oracles, ML leakage/metric checks, anomaly baselines. |
| **Backend Integration & Security** | `pytest` + `httpx` (`AsyncClient` / `TestClient`) + Dedicated `nexora_test_db` | Real SQLAlchemy + Alembic migrations, pagination/sorting/filtering, 401/403 RBAC enforcement, privilege escalation attempts, CSV upload/rollback, sanitized CSV export, audit logs. |
| **Frontend Component & Unit** | `Vitest` + React Testing Library + `tsc --noEmit` + `ESLint` | Reusable KPI cards, data tables, filter bars, form validation, loading/empty/error states, role-aware nav & controls. |
| **End-to-End & Browser QA** | Live browser / Playwright inspection | Full demo & owner workflows, chart-to-table drill-downs, laptop/tablet responsive widths, keyboard accessibility, zero console/network errors. |
| **Code Quality Gates** | `ruff check`, `ruff format --check`, `mypy`, `npm run lint`, `npm run typecheck` | Run on every module from Module 2 onward. |
| **Manual / Audit Checks** | Structured checklists in `docs/test-reports/module-XX.md` | Specification completeness (M1), visual/explanation clarity, clean-environment README handover (M16). |

---

## 3. Cumulative Regression Policy
- Backend tests are tagged with module markers (`m02`, `m03`, `m04`, …, `m15`).
- Running `pytest` executes all prior module tests together so schema changes, RBAC updates, or analytics edits immediately reveal regressions.
- Running `npm test` + `npm run typecheck` + `npm run lint` in `frontend/` verifies frontend regression health.
- Every `docs/test-reports/module-XX.md` logs exact commands executed, actual counts, defects found/fixed, and regression results.

---

## 4. Complete 205-Test-Case Registry (Modules 1–16)

### Module 1 — Project Planning and Requirements (`M1-T01` – `M1-T06`)
| Test ID | Description | Mode | Status |
| :--- | :--- | :--- | :---: |
| `M1-T01` | Project scope completeness (all 15 sections documented) | Audit + Automated Check | PASS |
| `M1-T02` | User role verification (all 6 roles defined with purpose & access level) | Audit + Automated Check | PASS |
| `M1-T03` | Role and permission matrix (explicit decisions; demo roles read-only; owner admin) | Audit + Automated Check | PASS |
| `M1-T04` | User journey validation (9 core demo + owner workflows with boundaries) | Audit + Automated Check | PASS |
| `M1-T05` | Metric definition validation (formulas, units, sources, assumptions) | Audit + Automated Check | PASS |
| `M1-T06` | Acceptance criteria validation (measurable completion conditions per task) | Audit + Automated Check | PASS |

### Module 2 — Development Environment and Repository (`M2-T01` – `M2-T10`)
- `M2-T01` Repository structure (PASS) · `M2-T02` Frontend dependency install (PASS) · `M2-T03` Backend dependency install (PASS) · `M2-T04` PostgreSQL startup (PASS) · `M2-T05` Backend startup (PASS) · `M2-T06` Backend health check (PASS) · `M2-T07` Frontend startup (PASS) · `M2-T08` Frontend-backend connectivity (PASS) · `M2-T09` Environment configuration (PASS) · `M2-T10` Code quality tools (PASS).

### Module 3 — Database Design and Synthetic Data (`M3-T01` – `M3-T11`)
- `M3-T01` Database creation (PASS) · `M3-T02` Migration execution (PASS) · `M3-T03` ER verification (PASS) · `M3-T04` PK/FK/unique constraints (PASS) · `M3-T05` `organization_id` validation (PASS) · `M3-T06` Synthetic data generation (PASS) · `M3-T07` Data coverage validation (PASS) · `M3-T08` Referential integrity check (PASS) · `M3-T09` Data plausibility check (PASS) · `M3-T10` Deterministic seed test (PASS) · `M3-T11` Database reset test (PASS).

### Module 4 — Backend Foundation and API Standards (`M4-T01` – `M4-T11`)
- `M4-T01` Backend startup (PASS) · `M4-T02` DB connectivity (PASS) · `M4-T03` DB session handling (PASS) · `M4-T04` API response format (PASS) · `M4-T05` Request validation (PASS) · `M4-T06` Pagination (PASS) · `M4-T07` Sorting (PASS) · `M4-T08` Filtering (PASS) · `M4-T09` Invalid filter handling (PASS) · `M4-T10` OpenAPI documentation (PASS) · `M4-T11` Safe error handling (PASS).

### Module 5 — Authentication, Roles and Permissions (`M5-T01` – `M5-T12`)
- `M5-T01` Owner login success · `M5-T02` Owner login failure · `M5-T03` Demo role selection · `M5-T04` Owner role protection · `M5-T05` Demo read-only protection · `M5-T06` Unauthenticated 401 · `M5-T07` Insufficient permission 403 · `M5-T08` Privilege escalation attempt · `M5-T09` Session expiration · `M5-T10` Logout revocation · `M5-T11` Password hashing security · `M5-T12` Backend authorization enforcement.

### Module 6 — Frontend Foundation and Design System (`M6-T01` – `M6-T12`)
- `M6-T01` Application shell · `M6-T02` Navigation · `M6-T03` Role-aware navigation · `M6-T04` KPI card component · `M6-T05` Table component · `M6-T06` Loading states · `M6-T07` Empty states · `M6-T08` Error states · `M6-T09` Form validation · `M6-T10` Responsive layout · `M6-T11` Keyboard accessibility · `M6-T12` Browser console check.

### Module 7 — Data Ingestion and Source Management (`M7-T01` – `M7-T13`)
- `M7-T01` Valid CSV upload · `M7-T02` Invalid extension · `M7-T03` Oversized file · `M7-T04` Empty file · `M7-T05` Malformed CSV · `M7-T06` Missing required columns · `M7-T07` Column mapping · `M7-T08` Data preview · `M7-T09` Successful import · `M7-T10` Transaction rollback · `M7-T11` Import history · `M7-T12` Duplicate import behavior · `M7-T13` Demo role restrictions.

### Module 8 — Data Cleaning, Validation and Quality (`M8-T01` – `M8-T12`)
- `M8-T01` Missing value detection · `M8-T02` Duplicate detection · `M8-T03` Invalid date detection · `M8-T04` Numeric validation · `M8-T05` Category consistency · `M8-T06` Referential integrity validation · `M8-T07` 5 quality dimensions math · `M8-T08` Transformation traceability · `M8-T09` Raw data preservation · `M8-T10` Repeatability · `M8-T11` Cleaning approval RBAC · `M8-T12` Curated data validation.

### Module 9 — Core Business Intelligence Modules (`M9-T01` – `M9-T17`)
- `M9-T01` Overview reconciliation · `M9-T02` Sales calcs · `M9-T03` Customer calcs · `M9-T04` Marketing calcs · `M9-T05` Financial calcs · `M9-T06` Inventory calcs · `M9-T07` Operations calcs · `M9-T08` Supplier calcs · `M9-T09` Date filter · `M9-T10` Region/category filters · `M9-T11` Filter combinations · `M9-T12` Chart-to-table drill-down · `M9-T13` Cross-module reconciliation · `M9-T14` Empty result handling · `M9-T15` No hard-coded analytics · `M9-T16` Role-based access · `M9-T17` Query performance baseline.

### Module 10 — Reports, Exports and Saved Views (`M10-T01` – `M10-T12`)
- `M10-T01` Report catalogue · `M10-T02` Report data accuracy · `M10-T03` Saved view creation · `M10-T04` Saved view restoration · `M10-T05` CSV export · `M10-T06` Export reconciliation · `M10-T07` Export metadata & synthetic notice · `M10-T08` Export permissions · `M10-T09` Restricted field protection · `M10-T10` Formula injection protection · `M10-T11` Large export handling · `M10-T12` PDF export (if implemented) or clean deferral.

### Module 11 — Statistical Analysis (`M11-T01` – `M11-T13`)
- `M11-T01` Mean · `M11-T02` Median & mode · `M11-T03` Variance & SD · `M11-T04` Quartiles & percentiles · `M11-T05` Missing value handling · `M11-T06` Distribution analysis · `M11-T07` Correlation analysis · `M11-T08` Correlation ≠ causation warning · `M11-T09` Hypothesis testing · `M11-T10` Invalid statistical assumptions · `M11-T11` Confidence intervals · `M11-T12` Reproducibility · `M11-T13` Backend/frontend consistency.

### Module 12 — Predictive Analytics (`M12-T01` – `M12-T17`)
- `M12-T01` Model problem definition · `M12-T02` Dataset suitability · `M12-T03` Data leakage prevention · `M12-T04` Baseline model training · `M12-T05` Candidate comparison · `M12-T06` Regression/forecasting metrics (MAE/RMSE) · `M12-T07` Classification metrics (Precision/Recall/F1/ROC-AUC) · `M12-T08` Overfitting check · `M12-T09` Repeatable training · `M12-T10` Model metadata · `M12-T11` Model loading · `M12-T12` Prediction API · `M12-T13` Invalid inference input · `M12-T14` Batch vs API consistency · `M12-T15` Prediction UI · `M12-T16` Prediction limitations · `M12-T17` Missing model artifact handling.

### Module 13 — Anomaly Detection and Risk Intelligence (`M13-T01` – `M13-T13`)
- `M13-T01` Sales anomaly · `M13-T02` Transaction anomaly · `M13-T03` Inventory anomaly · `M13-T04` Marketing anomaly · `M13-T05` Normal data verification · `M13-T06` Baseline comparison · `M13-T07` Severity calculation · `M13-T08` Explanation validation · `M13-T09` False-positive control · `M13-T10` Duplicate alert prevention · `M13-T11` Acknowledgement workflow · `M13-T12` Unauthorized acknowledgement · `M13-T13` Optional Isolation Forest comparison.

### Module 14 — Pipeline Monitoring, Auditability and Administration (`M14-T01` – `M14-T13`)
- `M14-T01` Pipeline run creation · `M14-T02` Pipeline metadata · `M14-T03` Failed pipeline visibility · `M14-T04` Last successful refresh preservation · `M14-T05` Safe retry · `M14-T06` Audit login events · `M14-T07` Audit import/export events · `M14-T08` Audit admin events · `M14-T09` Audit log append-only protection · `M14-T10` Demo role restrictions · `M14-T11` Owner administration · `M14-T12` Owner-only reset · `M14-T13` Synthetic-data notice.

### Module 15 — Integration, Security and Quality Assurance (`M15-T01` – `M15-T20`)
- `M15-T01` Fresh environment setup · `M15-T02` Complete demo journey · `M15-T03` Complete owner journey · `M15-T04` Unauthorized write protection · `M15-T05` Role escalation testing · `M15-T06` Unauthorized export testing · `M15-T07` Invalid/expired/revoked tokens · `M15-T08` File upload security · `M15-T09` API input security · `M15-T10` CORS validation · `M15-T11` Frontend component regression · `M15-T12` Backend unit/integration suite · `M15-T13` DB integrity regression · `M15-T14` Browser console verification · `M15-T15` Responsive & accessibility review · `M15-T16` Performance verification · `M15-T17` Backup & restore · `M15-T18` Reset & reseed · `M15-T19` Complete automated suite · `M15-T20` Defect severity review.

### Module 16 — Documentation and Local Handover (`M16-T01` – `M16-T13`)
- `M16-T01` README verification · `M16-T02` Prerequisite verification · `M16-T03` Dependency install instructions · `M16-T04` Environment config · `M16-T05` DB initialization · `M16-T06` Synthetic data initialization · `M16-T07` Application startup · `M16-T08` Test execution instructions · `M16-T09` Documentation accuracy · `M16-T10` Model documentation · `M16-T11` Demo access documentation · `M16-T12` Clean-environment reproducibility · `M16-T13` Final handover review.

---

## 5. Module Gate Status Log

| Module | Gate Status | Report Path | Git Checkpoint |
| :---: | :---: | :--- | :--- |
| 01 | PASS | `docs/test-reports/module-01.md` | `module-01-complete` tag (`215b662`) |
| 02 | PASS | `docs/test-reports/module-02.md` | `module-02-complete` tag (`bdc7c4f`) |
| 03 | PASS | `docs/test-reports/module-03.md` | `module-03-complete` tag (`2e77842`) |
| 04 | PASS | `docs/test-reports/module-04.md` | `module-04-complete` tag (`5e9882c`) |
| 05 | PASS | `docs/test-reports/module-05.md` | `module-05-complete` tag (`67e6e50`) |
| 06 | PASS | `docs/test-reports/module-06.md` | `module-06-complete` tag (`46d207c`) |
| 07 | PASS | `docs/test-reports/module-07.md` | `module-07-complete` tag (`e6ae8ad`) |
| 08 | PASS | `docs/test-reports/module-08.md` | `module-08-complete` tag (`e0e58e5`) |
| 09 | PASS | `docs/test-reports/module-09.md` | `module-09-complete` tag (`5acc87d`) |
| 10–16 | Not Started | `docs/test-reports/module-10.md` – `module-16.md` | — |
