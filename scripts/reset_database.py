#!/usr/bin/env python3
"""
NEXORA — Database Reset Script
Safely truncates all application tables while preserving migrations and schema structure.
"""

import os
import sys
from pathlib import Path

# Ensure backend root is on sys.path
backend_dir = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(backend_dir))

from sqlalchemy import create_engine, text
from app.core.config import settings

TABLES_TO_TRUNCATE = [
    "organizations",
    "departments",
    "regions",
    "employees",
    "suppliers",
    "categories",
    "products",
    "warehouses",
    "inventory",
    "stock_movements",
    "customers",
    "orders",
    "order_items",
    "payments",
    "order_returns",
    "campaigns",
    "campaign_events",
    "purchase_orders",
    "expenses",
    "budgets",
    "users",
    "roles",
    "permissions",
    "role_permissions",
    "user_roles",
    "data_sources",
    "import_jobs",
    "staging_records",
    "pipeline_runs",
    "saved_views",
    "audit_logs",
    "anomaly_alerts",
]


def reset_database(database_url: str | None = None) -> None:
    target_url = database_url or os.getenv("DATABASE_URL", settings.database_url)
    print(f"Connecting to database: {target_url}")
    engine = create_engine(target_url, future=True)

    truncate_sql = f"TRUNCATE TABLE {', '.join(TABLES_TO_TRUNCATE)} RESTART IDENTITY CASCADE;"

    with engine.begin() as conn:
        print("Truncating tables with RESTART IDENTITY CASCADE...")
        conn.execute(text(truncate_sql))
        print("All tables successfully truncated.")

    engine.dispose()
    print("Database reset complete.")


if __name__ == "__main__":
    url_arg = sys.argv[1] if len(sys.argv) > 1 else None
    reset_database(url_arg)
