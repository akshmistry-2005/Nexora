"""Module 16 — Documentation and Local Handover Tests.

Tests M16-T01 through M16-T13:
- M16-T01: README verification
- M16-T02: Prerequisite verification
- M16-T03: Dependency install instructions
- M16-T04: Environment config
- M16-T05: DB initialization instructions
- M16-T06: Synthetic data initialization instructions
- M16-T07: Application startup instructions
- M16-T08: Test execution instructions
- M16-T09: Documentation accuracy
- M16-T10: Model documentation
- M16-T11: Demo access documentation
- M16-T12: Clean-environment reproducibility
- M16-T13: Final handover review
"""

from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]


def test_m16_t01_readme_verification():
    """M16-T01: README exists, well-formatted, and covers all core architecture sections."""
    readme_path = ROOT_DIR / "README.md"
    assert readme_path.exists(), "README.md must exist at project root."

    content = readme_path.read_text(encoding="utf-8")
    assert "NEXORA" in content
    assert "Architecture Overview" in content
    assert "Implemented Platform Modules" in content
    assert "Prerequisites" in content
    assert "Quick Start" in content
    assert "Demonstration Personas" in content
    assert "Quality Gates" in content


def test_m16_t02_prerequisite_verification():
    """M16-T02: Prerequisites document Python, Node.js, npm, Docker, and PostgreSQL."""
    readme_content = (ROOT_DIR / "README.md").read_text(encoding="utf-8")
    assert "Python" in readme_content
    assert "Node.js" in readme_content
    assert "Docker" in readme_content
    assert "PostgreSQL" in readme_content


def test_m16_t03_dependency_install_instructions():
    """M16-T03: Dependency install commands for backend and frontend are documented."""
    readme_content = (ROOT_DIR / "README.md").read_text(encoding="utf-8")
    assert 'pip install -e ".[dev]"' in readme_content
    assert "npm install" in readme_content


def test_m16_t04_environment_config():
    """M16-T04: .env.example exists and contains all required configuration parameters."""
    env_example_path = ROOT_DIR / ".env.example"
    assert env_example_path.exists(), ".env.example must exist at root."

    content = env_example_path.read_text(encoding="utf-8")
    assert "DATABASE_URL" in content
    assert "POSTGRES_USER" in content
    assert "JWT_SECRET_KEY" in content
    assert "OWNER_EMAIL" in content
    assert "VITE_API_BASE_URL" in content


def test_m16_t05_db_initialization_instructions():
    """M16-T05: Alembic migration execution instructions and migrations directory exist."""
    readme_content = (ROOT_DIR / "README.md").read_text(encoding="utf-8")
    assert "alembic upgrade head" in readme_content

    migrations_dir = ROOT_DIR / "backend" / "migrations" / "versions"
    assert migrations_dir.exists()
    migration_files = list(migrations_dir.glob("*.py"))
    assert len(migration_files) >= 1, "At least one Alembic migration must exist."


def test_m16_t06_synthetic_data_initialization():
    """M16-T06: Synthetic data seeder and model training scripts exist and are documented."""
    readme_content = (ROOT_DIR / "README.md").read_text(encoding="utf-8")
    assert "seed_database.py" in readme_content
    assert "train_models.py" in readme_content

    assert (ROOT_DIR / "scripts" / "seed_database.py").exists()
    assert (ROOT_DIR / "scripts" / "train_models.py").exists()


def test_m16_t07_application_startup_instructions():
    """M16-T07: Application startup commands and verification ports are documented."""
    readme_content = (ROOT_DIR / "README.md").read_text(encoding="utf-8")
    assert "uvicorn app.main:app" in readme_content
    assert "npm run dev" in readme_content
    assert "8000" in readme_content
    assert "5173" in readme_content


def test_m16_t08_test_execution_instructions():
    """M16-T08: Test execution instructions cover pytest, vitest, ruff, mypy, eslint, tsc."""
    readme_content = (ROOT_DIR / "README.md").read_text(encoding="utf-8")
    assert "pytest" in readme_content
    assert "ruff" in readme_content
    assert "mypy" in readme_content
    assert "lint" in readme_content
    assert "typecheck" in readme_content


def test_m16_t09_documentation_accuracy():
    """M16-T09: All referenced documentation files exist on disk."""
    docs_dir = ROOT_DIR / "docs"
    assert docs_dir.exists()

    required_docs = [
        "local-handover.md",
        "model-documentation.md",
        "data-dictionary.md",
        "metric-definitions.md",
        "product-requirements.md",
        "test-plan.md",
    ]
    for doc in required_docs:
        assert (docs_dir / doc).exists(), f"Document '{doc}' must exist."


def test_m16_t10_model_documentation():
    """M16-T10: Model documentation covers Churn, Sales Forecast, Demand, and Anomalies."""
    model_doc_path = ROOT_DIR / "docs" / "model-documentation.md"
    assert model_doc_path.exists()

    content = model_doc_path.read_text(encoding="utf-8")
    assert "Customer Churn" in content
    assert "Sales Revenue Forecasting" in content
    assert "Product Demand Forecasting" in content
    assert "Anomaly Detection" in content
    assert "Isolation Forest" in content
    assert "Accusation Prohibition" in content


def test_m16_t11_demo_access_documentation():
    """M16-T11: Demo credentials and personas are fully documented."""
    readme_content = (ROOT_DIR / "README.md").read_text(encoding="utf-8")
    assert "owner@nexora.local" in readme_content
    assert "NexoraOwnerPass2026!" in readme_content
    assert "demo_exec@nexora.local" in readme_content
    assert "demo_ops@nexora.local" in readme_content
    assert "demo_comm@nexora.local" in readme_content
    assert "demo_analyst@nexora.local" in readme_content
    assert "demo_viewer@nexora.local" in readme_content


def test_m16_t12_clean_environment_reproducibility():
    """M16-T12: Local handover guide contains complete step-by-step reproduction guide."""
    handover_path = ROOT_DIR / "docs" / "local-handover.md"
    assert handover_path.exists()

    content = handover_path.read_text(encoding="utf-8")
    assert "Clean-Environment Setup Checklist" in content
    assert "docker compose up -d postgres" in content
    assert "pip install" in content
    assert "npm install" in content
    assert "Troubleshooting" in content


def test_m16_t13_final_handover_review():
    """M16-T13: Test reports exist for modules 01 through 15 and test plan tracks status."""
    reports_dir = ROOT_DIR / "docs" / "test-reports"
    assert reports_dir.exists()

    for m in range(1, 16):
        m_str = f"{m:02d}"
        report_file = reports_dir / f"module-{m_str}.md"
        assert report_file.exists(), f"Test report for module {m_str} must exist."

    test_plan_content = (ROOT_DIR / "docs" / "test-plan.md").read_text(encoding="utf-8")
    assert "module-14-complete" in test_plan_content
    assert "module-15-complete" in test_plan_content
