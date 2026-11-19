# NEXORA — Enterprise Data Intelligence & Business Analytics Platform

[![Python](https://img.shields.io/badge/Python-3.13.1-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.164.0-009688.svg)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16_Alpine-336791.svg)](https://www.postgresql.org/)
[![React](https://img.shields.io/badge/React-19.0.0-61DAFB.svg)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.7.2-3178C6.svg)](https://www.typescriptlang.org/)
[![Vite](https://img.shields.io/badge/Vite-6.0.7-646CFF.svg)](https://vitejs.dev/)
[![Scikit-Learn](https://img.shields.io/badge/scikit--learn-1.9.1-F7931E.svg)](https://scikit-learn.org/)
[![Code Quality](https://img.shields.io/badge/Code_Quality-0_ruff_%7C_0_mypy_%7C_0_eslint-brightgreen.svg)]()
[![Automated Tests](https://img.shields.io/badge/Tests-160_Pytest_%7C_35_Vitest_PASS-success.svg)]()

Nexora is a local-first, portfolio-grade Enterprise Data Intelligence & Business Analytics Platform built for a fictional enterprise (*Nexora Technologies*). It demonstrates end-to-end software architecture, relational database engineering, CSV ingestion & 5-dimension quality scoring, real database-backed business intelligence, inferential statistics, evaluated machine learning models, unsupervised anomaly detection, and backend-enforced role-based access control (RBAC).

> **Demonstration Environment Notice:** All baseline datasets in Nexora are synthetically generated for enterprise demonstration and evaluation purposes.

---

## Architecture Overview

```
                                      [ Browser Client (Port 5173) ]
                                                     │
                                           Vite Dev Server / SPA
                                                     │
                                       RESTful JSON over HTTP / CORS
                                                     │
                                                     ▼
                                      [ FastAPI Backend (Port 8000) ]
                                 ┌───────────────────┴───────────────────┐
                                 │                                       │
                      API Routers & Controllers               Predictive & Stat Services
                      - /api/v1/auth                          - Customer Churn (RandomForest)
                      - /api/v1/analytics                     - Sales Forecast (RandomForest)
                      - /api/v1/statistics                    - Demand Forecast (RandomForest)
                      - /api/v1/predictions                   - Anomaly Detection (IsoForest)
                      - /api/v1/data-sources                  - Statistical Hypothesis Engine
                      - /api/v1/data-quality                  - Data Ingestion & Scoring
                      - /api/v1/reports                       - Pipeline & Telemetry Logs
                      - /api/v1/pipelines
                      - /api/v1/admin
                                 │                                       │
                                 └───────────────────┬───────────────────┘
                                                     │
                                        SQLAlchemy 2.0 ORM (psycopg3)
                                                     │
                                                     ▼
                                    [ PostgreSQL 16 Alpine (Port 5432) ]
                                    - Operational Schema (28 Tables)
                                    - Append-Only Trigger (`trg_audit_logs_immutable`)
                                    - 2,500 Customers, 15,000 Orders Baseline
```

### Technology Stack Mapping

| Layer | Technology | Primary Directory |
| :--- | :--- | :--- |
| **Frontend SPA** | React 19, TypeScript 5.7, Vite 6, Tailwind CSS | `frontend/` |
| **Backend API** | Python 3.13, FastAPI, SQLAlchemy 2.0, Pydantic v2 | `backend/` |
| **Database Engine** | PostgreSQL 16 Alpine via Docker Compose | `docker-compose.yml` |
| **Data Migration** | Alembic (with database-level immutable triggers) | `backend/migrations/` |
| **Machine Learning** | Scikit-Learn 1.9, NumPy 2.5, SciPy 1.18, statsmodels | `backend/app/analytics/`, `artifacts/` |
| **Data Pipelines** | Synthetic enterprise generators, batch seeders, trainer | `scripts/`, `data/` |
| **Documentation** | Requirements, metric definitions, test reports, model docs | `docs/` |

---

## Implemented Platform Modules

| Module ID | Module Title | Primary Capabilities & Scope |
| :---: | :--- | :--- |
| **M01** | Repository & Environment | Multi-runtime tooling, git checkpointing, clean directory layout |
| **M02** | Health & Containerization | Docker Compose PostgreSQL 16, multi-stage containers, health endpoint |
| **M03** | Database Engineering | 28 tables, Alembic migrations, foreign keys, btree indexes |
| **M04** | Backend Foundation | FastAPI application structure, CORS, global error handling, logging |
| **M05** | Authentication & RBAC | JWT access tokens, password hashing, role permissions, owner setup |
| **M06** | Frontend Foundation | Design system tokens, AppShell, sidebar, topbar, KPI cards, DataTable |
| **M07** | Data Ingestion | CSV upload preview, sanitization, schema mapping, batch staging |
| **M08** | Data Quality Engine | 5-dimension scoring (Completeness, Uniqueness, Validity, Timeliness, Consistency) |
| **M09** | Core BI Dashboards | Executive overview, sales intelligence, order ledger, drill-down analytics |
| **M10** | Reports & Exports | Saved analytical views, catalog, CSV/Excel exports with permission checks |
| **M11** | Statistical Analysis | Descriptive stats, Pearson/Spearman correlation, Welch t-test, ANOVA, Chi-Square |
| **M12** | Predictive Analytics | Customer Churn (RF), Sales Forecast (RF), SKU Demand (RF), model governance |
| **M13** | Anomaly Detection | Isolation Forest benchmark (BL-16), IQR rules, accusation prohibition compliance |
| **M14** | Pipeline & Audit Admin | Append-only audit trigger (`trg_audit_logs_immutable`), pipeline health, demo reset |
| **M15** | Integration & Security | End-to-end integration, SQLi/XSS defense, token expiry, accessibility review |
| **M16** | Documentation & Handover | Complete technical documentation, local reproduction guide, operations manual |

---

## Prerequisites

- **Python:** 3.11+ (verified on Python 3.13.1)
- **Node.js:** 20.0+ (verified on Node.js v22.19.0)
- **npm:** 10.0+ (verified on npm 10.9.3)
- **Docker Desktop & Docker Compose v2:** (verified with PostgreSQL 16 Alpine)
- **Git:** 2.40+

---

## Quick Start (Clean Environment Setup)

### 1. Environment Configuration
```powershell
Copy-Item .env.example .env
```
Keep real secrets out of source control (`.env` is git-ignored).

### 2. Start PostgreSQL Engine
```powershell
docker compose up -d postgres
docker compose ps
```

### 3. Initialize Backend & Database
```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
alembic upgrade head
cd ..
```

### 4. Seed Synthetic Dataset & Train ML Models
```powershell
python scripts/seed_database.py
python scripts/train_models.py
```

### 5. Start Backend API Server
```powershell
cd backend
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```
- Health Verification: `http://127.0.0.1:8000/api/v1/health`
- Interactive OpenAPI Docs: `http://127.0.0.1:8000/docs`

### 6. Install & Start Frontend Client
In a second terminal:
```powershell
cd frontend
npm install
npm run dev
```
- Local Application URL: `http://localhost:5173`

---

## Demonstration Personas & Credentials

The platform includes 5 pre-configured demonstration personas (with one-click login in the top bar) and one privileged Platform Owner account:

| Persona / Role | Email | Password | Access Scope |
| :--- | :--- | :--- | :--- |
| **Platform Owner** | `owner@nexora.local` | `NexoraOwnerPass2026!` | Full administrative access, audit logs, user directory, system reset |
| **Executive Sponsor** | `demo_exec@nexora.local` | *(One-Click Demo Login)* | Executive overview, sales KPIs, revenue summaries, board reports |
| **Operations Lead** | `demo_ops@nexora.local` | *(One-Click Demo Login)* | Inventory health, supplier scorecard, operations telemetry, quality triage |
| **Commercial Manager** | `demo_comm@nexora.local` | *(One-Click Demo Login)* | Customer intelligence, marketing campaigns, churn simulators, sales drilldown |
| **Data Analyst** | `demo_analyst@nexora.local` | *(One-Click Demo Login)* | Full BI analytics, inferential statistics, ML models, report export |
| **General Viewer** | `demo_viewer@nexora.local` | *(One-Click Demo Login)* | Read-only high-level dashboards; export and mutations disabled |

---

## Quality Gates & Verification Commands

The project strictly complies with the **Nexora Mandatory Module-Wise Testing Gate System**. Zero lint errors, zero typecheck errors, and 100% test pass rate are enforced across both stacks:

### Backend Checks (160 Tests)
```powershell
# Run complete pytest suite with real PostgreSQL database
backend\.venv\Scripts\python.exe -m pytest backend\tests

# Run Ruff linter (0 errors enforced)
backend\.venv\Scripts\ruff.exe check backend\app backend\tests

# Run Ruff code format check (0 discrepancies enforced)
backend\.venv\Scripts\ruff.exe format --check backend\app backend\tests

# Run Mypy static type checker (0 errors enforced across 80 source files)
powershell -Command "cd backend; .\.venv\Scripts\python.exe -m mypy app"
```

### Frontend Checks (35 Tests)
```powershell
# Run Vitest test suites across all frontend modules
npm --prefix frontend test -- --run

# Run ESLint (0 errors, 0 warnings enforced)
npm --prefix frontend run lint

# Run TypeScript type check (0 errors enforced)
npm --prefix frontend run typecheck

# Verify production bundle compilation
npm --prefix frontend run build
```

---

## Project Documentation Index

- [Local Handover & Operations Guide](docs/local-handover.md)
- [Machine Learning Model Documentation](docs/model-documentation.md)
- [Canonical Data Dictionary](docs/data-dictionary.md)
- [Metric Definitions & Business Formulas](docs/metric-definitions.md)
- [Product Requirements & Backlog](docs/product-requirements.md)
- [Master Test Plan & Gate Log](docs/test-plan.md)
- [Module Completion Reports (Modules 01–16)](docs/test-reports/)
