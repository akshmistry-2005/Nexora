# NEXORA — Enterprise Data Intelligence & Business Analytics Platform

Nexora is a local-first, portfolio-grade Enterprise Data Intelligence & Business Analytics Platform built for a fictional enterprise (*Nexora Technologies*). It demonstrates end-to-end software architecture, database engineering, CSV data ingestion, explainable data cleaning & 5-dimension quality scoring, real database-backed business intelligence, inferential statistics, evaluated machine learning models, anomaly detection, and backend-enforced role-based access control (RBAC).

> **Note:** All baseline datasets in Nexora are synthetic and fictional. Deployment is intentionally deferred until local v1.0 is complete.

---

## Architecture Overview

| Layer | Technology | Directory |
| :--- | :--- | :--- |
| **Frontend** | React + TypeScript + Vite + Tailwind CSS | `frontend/` |
| **Backend API** | Python + FastAPI + SQLAlchemy + Pydantic | `backend/` |
| **Database** | PostgreSQL 16 (via Docker Compose) | `docker-compose.yml` |
| **Analytics & ML** | Pandas, NumPy, SciPy, statsmodels, scikit-learn | `backend/app/analytics/` |
| **Data & Scripts** | Synthetic data generators, seed/reset/train scripts | `data/`, `scripts/` |
| **Documentation** | Requirements, metrics, architecture, ER, test reports | `docs/` |

---

## Prerequisites

- **Python** 3.11+ (tested on Python 3.13.1)
- **Node.js** 20+ & **npm** 10+ (tested on Node v22.19.0 / npm 10.9.3)
- **Git** 2.40+
- **Docker Desktop** with **Docker Compose v2** (recommended for local PostgreSQL 16)

---

## Quick Start (Local Development)

### 1. Configure Environment Variables
```powershell
Copy-Item .env.example .env
```
Review `.env` and keep real local secrets out of version control (`.env` is git-ignored).

### 2. Start PostgreSQL (Docker Compose)
```powershell
docker compose up -d postgres
docker compose ps
```

### 3. Setup & Start Backend (FastAPI)
```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```
Verify backend health: `http://127.0.0.1:8000/api/v1/health`  
Interactive API docs: `http://127.0.0.1:8000/docs`

### 4. Setup & Start Frontend (React + TypeScript)
Open a second terminal:
```powershell
cd frontend
npm install
npm run dev
```
Open `http://localhost:5173` to verify live frontend-to-backend connectivity.

---

## Code Quality & Testing Commands

### Backend Checks
```powershell
cd backend
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m ruff format --check .
.\.venv\Scripts\python.exe -m mypy app
.\.venv\Scripts\python.exe -m pytest
```

### Frontend Checks
```powershell
cd frontend
npm run lint
npm run typecheck
npm run test
```

---

## Project Documentation
- [Product Requirements & Backlog](docs/product-requirements.md)
- [Metric Definitions & Data Vocabulary](docs/metric-definitions.md)
- [Master Test Plan](docs/test-plan.md)
- [Module Test Reports](docs/test-reports/)
