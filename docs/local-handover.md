# NEXORA — Local Handover & Operations Guide

**Document Status:** Approved Baseline (Module 16 Handover)  
**Platform Version:** 0.2.0  
**Environment:** Local Development (Windows / Linux / macOS)  
**Date:** 2026-11-19  

---

## 1. System Overview

Nexora is a local-first, portfolio-grade Enterprise Data Intelligence & Business Analytics Platform built for a fictional enterprise (*Nexora Technologies*). The platform incorporates full-stack enterprise architecture:
- **Relational Data Foundation:** PostgreSQL 16 Alpine running on Docker Compose, with schema managed via Alembic migrations.
- **Append-Only Security Audit:** Database-level trigger `trg_audit_logs_immutable` preventing modification or deletion of compliance logs.
- **FastAPI Analytical Backend:** High-performance RESTful API using SQLAlchemy 2.0 (psycopg3 driver) and Pydantic v2 schemas.
- **React 19 Frontend:** TypeScript + Vite SPA utilizing custom design system tokens, responsive layout, and role-based view customization.
- **Machine Learning & Predictive Engine:** Scikit-Learn pipelines for Customer Churn, Sales Forecasting, Product Demand, and Isolation Forest Anomaly Detection.
- **Inferential Statistics:** Welch t-tests, ANOVA F-tests, Chi-square tests of independence, and dual Pearson/Spearman correlation matrices.

---

## 2. System Architecture & Component Mapping

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

---

## 3. Clean-Environment Setup Checklist

### 3.1 Software Prerequisites
Verify the host environment satisfies the minimum version requirements:
- **Python:** 3.11+ (verified on Python 3.13.1)
- **Node.js:** 20.0+ (verified on Node.js v22.19.0)
- **npm:** 10.0+ (verified on npm 10.9.3)
- **Docker Desktop & Docker Compose v2:** (verified with PostgreSQL 16 Alpine)
- **Git:** 2.40+

### 3.2 Clone & Environment Variable Configuration
```powershell
# 1. Clone the repository
git clone https://github.com/example/Nexora_project.git
cd Nexora_project

# 2. Copy the environment template
Copy-Item .env.example .env
```

Review `.env` settings:
```ini
POSTGRES_USER=nexora_user
POSTGRES_PASSWORD=nexora_local_dev_password_change_me
POSTGRES_DB=nexora_db
POSTGRES_TEST_DB=nexora_test_db
POSTGRES_PORT=5432
DATABASE_URL=postgresql+psycopg://nexora_user:nexora_local_dev_password_change_me@localhost:5432/nexora_db
TEST_DATABASE_URL=postgresql+psycopg://nexora_user:nexora_local_dev_password_change_me@localhost:5432/nexora_test_db
BACKEND_HOST=127.0.0.1
BACKEND_PORT=8000
JWT_SECRET_KEY=nexora_local_dev_jwt_secret_key_change_in_production_min_32_chars
OWNER_EMAIL=owner@nexora.local
VITE_API_BASE_URL=http://127.0.0.1:8000
```

### 3.3 Start PostgreSQL Engine
```powershell
# Start PostgreSQL via Docker Compose
docker compose up -d postgres

# Verify container is healthy and listening on port 5432
docker compose ps
```

### 3.4 Backend Environment & Database Initialization
```powershell
# Navigate into backend directory
cd backend

# Create Python virtual environment
python -m venv .venv

# Activate virtual environment
# Windows PowerShell:
.\.venv\Scripts\Activate.ps1
# macOS / Linux:
# source .venv/bin/activate

# Install backend package and development dependencies in editable mode
pip install -e ".[dev]"

# Apply all database migrations up to head (installs tables and append-only triggers)
alembic upgrade head

# Return to root directory
cd ..
```

### 3.5 Synthetic Data Seeding & Model Training
```powershell
# Seed database with baseline synthetic enterprise dataset (2,500 customers, 15,000 orders)
python scripts/seed_database.py

# Train and serialize all machine learning models to artifacts/
python scripts/train_models.py
```

### 3.6 Frontend Installation & Build
```powershell
# Navigate to frontend directory
cd frontend

# Install Node modules
npm install

# Verify production build compilation
npm run build

# Return to root directory
cd ..
```

---

## 4. Starting Platform Services

### 4.1 Running the Backend API
In terminal 1 (with backend `.venv` activated):
```powershell
cd backend
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```
- Health Check: `http://127.0.0.1:8000/api/v1/health`
- Interactive Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc Documentation: `http://127.0.0.1:8000/redoc`

### 4.2 Running the Frontend Client
In terminal 2:
```powershell
cd frontend
npm run dev
```
- Local Application URL: `http://localhost:5173`

---

## 5. Demonstration Roles & Authentication Matrix

Nexora includes five preconfigured demonstration personas and one privileged Platform Owner account:

| Role / Persona | Email | Password | Primary Permissions / Scope |
| :--- | :--- | :--- | :--- |
| **Platform Owner** | `owner@nexora.local` | `NexoraOwnerPass2026!` | Full administrative access, audit logs, user directory, system reset |
| **Executive Sponsor** | `demo_exec@nexora.local` | *Direct Demo Login* | Executive overview, sales KPIs, revenue summaries, board reports |
| **Operations Lead** | `demo_ops@nexora.local` | *Direct Demo Login* | Inventory health, supplier scorecard, operations telemetry, quality triage |
| **Commercial Manager** | `demo_comm@nexora.local` | *Direct Demo Login* | Customer intelligence, marketing campaigns, churn simulators, sales drilldown |
| **Data Analyst** | `demo_analyst@nexora.local` | *Direct Demo Login* | Full BI analytics, inferential statistics, ML models, report export |
| **General Viewer** | `demo_viewer@nexora.local` | *Direct Demo Login* | Read-only high-level dashboards; export and mutations disabled |

---

## 6. Comprehensive Verification & Quality Gates

Run the automated quality gates to verify complete platform integrity:

### 6.1 Backend Verification Suite
```powershell
# 1. Run all 160 backend unit, database, and integration tests
backend\.venv\Scripts\python.exe -m pytest backend\tests

# 2. Run Ruff linter (0 errors enforced)
backend\.venv\Scripts\ruff.exe check backend\app backend\tests

# 3. Run Ruff code formatting check (0 format discrepancies enforced)
backend\.venv\Scripts\ruff.exe format --check backend\app backend\tests

# 4. Run Mypy static type checker across backend (0 type errors enforced)
powershell -Command "cd backend; .\.venv\Scripts\python.exe -m mypy app"
```

### 6.2 Frontend Verification Suite
```powershell
# 1. Run all 35 frontend Vitest component & journey tests
npm --prefix frontend test -- --run

# 2. Run ESLint (0 errors, 0 warnings enforced)
npm --prefix frontend run lint

# 3. Run TypeScript type checker (0 errors enforced)
npm --prefix frontend run typecheck

# 4. Production bundle compilation
npm --prefix frontend run build
```

---

## 7. Troubleshooting & Operational FAQs

### Q1: `psycopg.OperationalError: could not connect to server: Connection refused`
- **Root Cause:** PostgreSQL Docker container is not running or port 5432 is blocked.
- **Resolution:** Run `docker compose up -d postgres` and verify with `docker compose ps`.

### Q2: `InternalServerError: PermissionDenied: Audit log records are append-only`
- **Root Cause:** A raw SQL script attempted an `UPDATE` or `DELETE` on the `audit_logs` table.
- **Resolution:** This is the intended behavior of the database security trigger `trg_audit_logs_immutable`. Audit log entries can only be appended (`INSERT`).

### Q3: `HTTP 401 Unauthorized: Signature has expired`
- **Root Cause:** JWT token lifetime has elapsed (default 120 minutes).
- **Resolution:** Switch personas via the UI top bar persona switcher or log back in via the Platform Owner modal.

### Q4: Resetting the Environment to Baseline
- **Option A (Via UI):** Switch to Platform Owner persona, open Admin page $\rightarrow$ Environment & Reset tab $\rightarrow$ Click "Reset Demonstration Dataset".
- **Option B (Via CLI):**
  ```powershell
  python scripts/seed_database.py
  python scripts/train_models.py
  ```
