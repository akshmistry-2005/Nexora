# NEXORA — Enterprise Data Intelligence & Business Analytics Platform

[![Python](https://img.shields.io/badge/Python-3.13.1-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.164.0-009688.svg)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16_Alpine-336791.svg)](https://www.postgresql.org/)
[![React](https://img.shields.io/badge/React-19.0.0-61DAFB.svg)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.7.2-3178C6.svg)](https://www.typescriptlang.org/)
[![Vite](https://img.shields.io/badge/Vite-6.0.7-646CFF.svg)](https://vitejs.dev/)
[![Scikit-Learn](https://img.shields.io/badge/scikit--learn-1.9.1-F7931E.svg)](https://scikit-learn.org/)
[![Tests](https://img.shields.io/badge/Tests-173_Pytest_%7C_35_Vitest_PASS-success.svg)]()

Nexora is a local-first, enterprise-grade Data Intelligence and Business Analytics Platform designed for modern corporate decision-making. It bridges the gap between transactional relational databases, advanced statistical inference, machine learning, and executive BI dashboards.

Built with a normalized 28-table PostgreSQL database, a high-performance Python FastAPI backend, and a reactive React 19 / TypeScript frontend, Nexora provides complete operational visibility across revenue, sales channels, customer churn, supply chain logistics, and marketing attribution.

---

## 1. What is the Project About?

Nexora acts as the centralized analytical nervous system for an enterprise (*Nexora Technologies Inc.*):

### Architecture Overview

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

### Core Architecture Highlights:
- **Relational Data Foundation:** PostgreSQL 16 engine managing 28 relational tables with foreign key constraints, indexes, and automated schema migrations via Alembic.
- **Append-Only Security Audit:** A database procedural trigger (`trg_audit_logs_immutable`) intercepts any `UPDATE` or `DELETE` on compliance logs at the database engine level, mathematically preventing tampering.
- **Parametric & Non-Parametric Statistics:** Welch’s t-tests (handling unequal variances), ANOVA tests, and dual Pearson/Spearman correlation matrices.
- **Machine Learning Pipelines:** Scikit-Learn pipelines evaluated against explicit statistical baselines for customer churn classification, time-series revenue forecasting, and product demand regression.
- **Unsupervised Anomaly Detection:** Multivariate Isolation Forest model benchmarked against univariate Interquartile Range (IQR) fences, adhering to strict corporate accusation-prohibition compliance.
- **5-Dimension Data Quality Engine:** Automated profiling across Completeness, Uniqueness, Validity, Timeliness, and Consistency.
- **Role-Based Access Control (RBAC):** Backend-enforced JWT authentication separating public demonstration personas from privileged platform owners.

### Implemented Platform Modules

| Module ID | Module Title | Primary Capabilities & Scope |
| :---: | :--- | :--- |
| **M01–M04** | Foundation & Architecture | Multi-stage Docker PostgreSQL 16, Alembic migrations, 28 tables, FastAPI REST API |
| **M05** | Authentication & RBAC | JWT access tokens, password hashing, role permissions, owner setup |
| **M06** | Frontend Foundation | Design system tokens, AppShell, sidebar, topbar, KPI cards, DataTable |
| **M07–M08** | Data Ingestion & Quality | CSV upload preview, schema mapping, 5-dimension quality scoring |
| **M09–M10** | BI Dashboards & Reports | Executive overview, sales drilldown, saved analytical views, CSV/Excel export |
| **M11** | Statistical Analysis | Descriptive stats, Pearson/Spearman correlation, Welch t-test, ANOVA, Chi-Square |
| **M12–M13** | Predictive ML & Anomalies | Customer Churn (RF), Sales Forecast (RF), SKU Demand (RF), Isolation Forest |
| **M14–M16** | Administration & Handover | Append-only audit trigger, pipeline health telemetry, test gates, local handover |

---

## 2. Current Platform Functionality & Data Foundation

Nexora comes pre-populated with a deterministic synthetic enterprise dataset covering 24–30 months of operational history:

### Pre-Loaded Enterprise Dataset
- **2,500 Enterprise Customers:** Categorized across Enterprise, Mid-Market, and SMB tiers.
- **15,000 Historical Transactions:** Representing ~$12.5M in gross revenue with realistic seasonal trends and channel variations (Direct B2B, Partner, Online).
- **38,000+ Order Line Items:** Spanning 100 hardware and software catalog SKUs across 5 categories.
- **10 Warehouses & 15 Suppliers:** Tracking real-time inventory valuations, stockout thresholds, and contractual lead times.
- **3,600 Daily Marketing Campaign Events:** Tracking impressions, clicks, conversions, spend, and ROAS.

### Demonstration Personas & Credentials

The platform includes 5 pre-configured demonstration personas (with one-click login in the top bar) and one privileged Platform Owner account:

| Persona / Role | Demo Email | Access Scope |
| :--- | :--- | :--- |
| **Platform Owner** | `owner@nexora.local` *(Password: `NexoraOwnerPass2026!`)* | Full administrative control, user RBAC, telemetry, demo reset |
| **Executive Sponsor** | `demo_exec@nexora.local` | Executive overview, gross margins, net revenue, board summaries |
| **Commercial Manager** | `demo_comm@nexora.local` | Customer intelligence, sales channels, order ledger, churn simulators |
| **Operations Lead** | `demo_ops@nexora.local` | Inventory health, warehouse valuations, supplier reliability |
| **Data Analyst** | `demo_analyst@nexora.local` | Full BI analytics, inferential statistics, ML models, report export |
| **General Viewer** | `demo_viewer@nexora.local` | Read-only dashboards; exports and data mutations locked |

---

## 3. Quick Start & Installation Guide

Follow these exact steps to clone, initialize, and run Nexora on your machine:

### Prerequisites
- **Git** (2.40+)
- **Docker Desktop** (running Docker Compose v2)
- **Python** (3.11+ / tested on 3.13)
- **Node.js** (20+ / npm 10+)
- **PostgreSQL** 16 (managed automatically via Docker)

---

### Step 1: Clone the Repository & Configure Environment
```bash
git clone https://github.com/akshmistry-2005/Nexora.git
cd Nexora

# Windows PowerShell:
Copy-Item .env.example .env
# macOS / Linux:
# cp .env.example .env
```

---

### Step 2: Start PostgreSQL (Docker)
```bash
docker compose up -d postgres
```
*PostgreSQL 16 Alpine is now running in an isolated container on port `5432`.*

---

### Step 3: Setup Backend & Initialize Database
```bash
cd backend
python -m venv .venv

# Activate virtual environment:
# Windows PowerShell:
.\.venv\Scripts\Activate.ps1
# macOS / Linux:
# source .venv/bin/activate

# Install dependencies in editable mode
pip install -e ".[dev]"

# Apply database migrations
alembic upgrade head

# Seed synthetic enterprise dataset & train ML models
cd ..
python scripts/seed_database.py
python scripts/train_models.py
```

---

### Step 4: Run the Application

**Terminal 1 — Backend API Server:**
```bash
cd backend
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```
- API Health Check: `http://127.0.0.1:8000/api/v1/health`
- Interactive OpenAPI Docs: `http://127.0.0.1:8000/docs`

**Terminal 2 — Frontend Client:**
```bash
cd frontend
npm install
npm run dev
```
- Web Application: **`http://localhost:5173`**

---

## Quality Gates & Verification Commands

To verify that all 208 automated unit, database, and integration tests pass cleanly:

```bash
# Run 173 backend pytest tests against real PostgreSQL
backend/.venv/Scripts/python.exe -m pytest backend/tests

# Run 35 frontend Vitest tests
npm --prefix frontend test -- --run

# Run static quality checks (0 errors enforced)
backend/.venv/Scripts/ruff.exe check backend/app backend/tests
powershell -Command "cd backend; .\.venv\Scripts\python.exe -m mypy app"
npm --prefix frontend run lint
npm --prefix frontend run typecheck
```

---

## Technical Documentation Index

- [Local Handover & Operations Guide](docs/local-handover.md)
- [Machine Learning Model Documentation](docs/model-documentation.md)
- [Canonical Data Dictionary (28 Tables)](docs/data-dictionary.md)
- [Metric Definitions & Business Formulas](docs/metric-definitions.md)
- [Product Requirements & Architecture Spec](docs/product-requirements.md)
- [Master Test Plan & Verification Log](docs/test-plan.md)
