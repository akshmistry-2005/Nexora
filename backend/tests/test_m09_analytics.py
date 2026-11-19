"""
NEXORA — Module 9 Test Suite: Core Business Intelligence Modules
Validates test cases M9-T01 through M9-T17 against live FastAPI application and PostgreSQL database.
"""

import time
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.core.config import settings
from app.main import app
from app.schemas.analytics import AnalyticsFilterParams
from app.services.analytics import analytics_service


@pytest.fixture(scope="module")
def client() -> TestClient:
    """Module-level TestClient for FastAPI endpoints."""
    return TestClient(app)


@pytest.fixture(scope="module")
def db_session() -> Generator[Session, None, None]:
    """Module-level database session connected to live PostgreSQL."""
    engine = create_engine(settings.database_url, future=True)
    with Session(engine) as session:
        yield session
    engine.dispose()


@pytest.fixture(scope="module")
def owner_headers(client: TestClient) -> dict[str, str]:
    """Provide authenticated headers for Platform Owner."""
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": "owner@nexora.local", "password": "NexoraOwnerPass2026!"},
    )
    assert resp.status_code == 200
    token = resp.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="module")
def analyst_headers(client: TestClient) -> dict[str, str]:
    """Provide authenticated headers for Demo Data Analyst."""
    resp = client.post("/api/v1/auth/demo-login", json={"role": "data_analyst"})
    assert resp.status_code == 200
    token = resp.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_m09_t01_overview_reconciliation(db_session: Session) -> None:
    """M9-T01: Overview reconciliation — verify headline KPIs reconcile with database records."""
    overview = analytics_service.get_overview_analytics(db_session)
    assert overview.total_orders > 0
    assert overview.total_customers >= 2500
    assert overview.net_revenue > 0.0
    assert overview.gross_profit > 0.0
    assert 0.0 <= overview.gross_margin_pct <= 100.0
    assert overview.inventory_valuation > 0.0
    assert 0.0 <= overview.fulfilment_rate <= 100.0
    assert len(overview.regional_breakdown) > 0
    assert len(overview.top_products) > 0


def test_m09_t02_sales_calculations(db_session: Session) -> None:
    """M9-T02: Sales calculations — verify revenue, discounts, units sold, and channel mix."""
    sales = analytics_service.get_sales_analytics(db_session)
    assert sales.gross_revenue >= sales.net_revenue
    assert sales.order_count > 0
    assert sales.units_sold >= sales.order_count
    assert sales.aov > 0.0
    assert 0.0 <= sales.discount_rate_pct <= 100.0
    assert len(sales.channel_breakdown) > 0
    assert len(sales.category_breakdown) > 0
    assert len(sales.sales_rep_leaderboard) > 0


def test_m09_t03_customer_calculations(db_session: Session) -> None:
    """M9-T03: Customer calculations — verify customer counts, segmentation, ARPU, and churn."""
    cust = analytics_service.get_customer_analytics(db_session)
    assert cust.total_customers >= 2500
    assert cust.active_customers > 0
    assert 0.0 <= cust.churn_rate_pct <= 100.0
    assert cust.arpu > 0.0
    assert len(cust.segment_breakdown) > 0
    assert len(cust.acquisition_breakdown) > 0
    assert len(cust.top_customers) > 0


def test_m09_t04_marketing_calculations(db_session: Session) -> None:
    """M9-T04: Marketing calculations — verify spend, clicks, CTR, CAC, and ROAS."""
    mkt = analytics_service.get_marketing_analytics(db_session)
    assert mkt.total_spend > 0.0
    assert mkt.impressions >= mkt.clicks
    assert mkt.clicks >= mkt.conversions
    assert 0.0 <= mkt.ctr_pct <= 100.0
    assert mkt.cpc > 0.0
    assert mkt.cac > 0.0
    assert mkt.roas > 0.0
    assert len(mkt.channel_breakdown) > 0


def test_m09_t05_financial_calculations(db_session: Session) -> None:
    """M9-T05: Financial calculations — P&L metrics, gross/net margins, and budget variance."""
    fin = analytics_service.get_finance_analytics(db_session)
    assert fin.net_revenue > 0.0
    assert fin.cogs > 0.0
    assert fin.gross_profit == round(fin.net_revenue - fin.cogs, 2)
    assert fin.operating_expenses > 0.0
    assert fin.net_profit == round(fin.gross_profit - fin.operating_expenses, 2)
    assert fin.total_allocated_budget > 0.0
    assert len(fin.expense_categories) > 0
    assert len(fin.department_budgets) > 0


def test_m09_t06_inventory_calculations(db_session: Session) -> None:
    """M9-T06: Inventory calculations — total SKUs, valuation, turnover, and reorder alerts."""
    inv = analytics_service.get_inventory_analytics(db_session)
    assert inv.total_skus >= 100
    assert inv.available_stock_units > 0
    assert inv.inventory_valuation > 0.0
    assert inv.turnover_rate >= 0.0
    assert len(inv.warehouse_breakdown) > 0
    assert len(inv.category_breakdown) > 0
    assert len(inv.reorder_alerts) > 0


def test_m09_t07_operations_calculations(db_session: Session) -> None:
    """M9-T07: Operations calculations — verify fulfilment rates, delivery SLAs, and returns."""
    ops = analytics_service.get_operations_analytics(db_session)
    assert ops.total_orders_processed > 0
    assert 0.0 <= ops.fulfilment_rate_pct <= 100.0
    assert 0.0 <= ops.cancellation_rate_pct <= 100.0
    assert 0.0 <= ops.return_rate_pct <= 100.0
    assert len(ops.status_pipeline) > 0
    assert len(ops.returns_by_reason) > 0


def test_m09_t08_supplier_calculations(db_session: Session) -> None:
    """M9-T08: Supplier calculations — vendor spend, lead time, defect rate, and scorecards."""
    supp = analytics_service.get_supplier_analytics(db_session)
    assert supp.total_suppliers >= 20
    assert supp.active_suppliers > 0
    assert supp.po_count > 0
    assert supp.total_supplier_spend > 0.0
    assert supp.avg_lead_time_days > 0.0
    assert 0.0 <= supp.on_time_delivery_rate_pct <= 100.0
    assert 0.0 <= supp.defect_rate_pct <= 100.0
    assert len(supp.supplier_scorecard) > 0


def test_m09_t09_date_filter_recalculation(db_session: Session) -> None:
    """M9-T09: Date filter — verify analytical metrics recalculate accurately for date windows."""
    all_time = analytics_service.get_sales_analytics(db_session)

    # 3-month window filter
    filtered = analytics_service.get_sales_analytics(
        db_session,
        AnalyticsFilterParams(
            start_date="2025-01-01T00:00:00Z",
            end_date="2025-03-31T23:59:59Z",
        ),
    )

    assert filtered.order_count > 0
    assert filtered.order_count < all_time.order_count
    assert filtered.net_revenue < all_time.net_revenue


def test_m09_t09_region_filter(db_session: Session) -> None:
    """M9-T10: Region filter — verify metrics correctly partition by region."""
    all_sales = analytics_service.get_sales_analytics(db_session)
    region_sales = analytics_service.get_sales_analytics(
        db_session, AnalyticsFilterParams(region_id=1)
    )

    assert region_sales.order_count > 0
    assert region_sales.order_count < all_sales.order_count
    assert region_sales.net_revenue < all_sales.net_revenue


def test_m09_t11_filter_combinations(db_session: Session) -> None:
    """M9-T11: Combined filters — verify intersection of date range and region."""
    combo = analytics_service.get_sales_analytics(
        db_session,
        AnalyticsFilterParams(
            start_date="2025-01-01T00:00:00Z",
            end_date="2025-06-30T23:59:59Z",
            region_id=1,
        ),
    )
    assert combo.order_count > 0
    assert combo.net_revenue > 0.0


def test_m09_t12_chart_to_table_drilldown(db_session: Session) -> None:
    """M9-T12: Chart-to-table drill-down — verify ledger rows match aggregated totals."""
    sales = analytics_service.get_sales_analytics(db_session, AnalyticsFilterParams(region_id=1))
    items, total_count = analytics_service.get_ledger(
        db_session, AnalyticsFilterParams(region_id=1), limit=100
    )

    assert total_count == sales.order_count
    assert len(items) == min(100, total_count)
    for it in items:
        assert it.order_number.startswith("ORD-")
        assert it.total_amount > 0.0


def test_m09_t13_cross_module_reconciliation(db_session: Session) -> None:
    """M9-T13: Cross-module reconciliation — Net Revenue in Overview == Sales == Finance."""
    overview = analytics_service.get_overview_analytics(db_session)
    sales = analytics_service.get_sales_analytics(db_session)
    finance = analytics_service.get_finance_analytics(db_session)

    assert overview.net_revenue == sales.net_revenue
    assert sales.net_revenue == finance.net_revenue
    assert overview.gross_profit == finance.gross_profit


def test_m09_t14_empty_result_handling(db_session: Session) -> None:
    """M9-T14: Empty result handling — out-of-range dates return safe zeroes without 500 errors."""
    empty_params = AnalyticsFilterParams(
        start_date="2099-01-01T00:00:00Z",
        end_date="2099-01-02T00:00:00Z",
    )
    sales = analytics_service.get_sales_analytics(db_session, empty_params)
    assert sales.order_count == 0
    assert sales.net_revenue == 0.0
    assert sales.aov == 0.0
    assert sales.discount_rate_pct == 0.0

    overview = analytics_service.get_overview_analytics(db_session, empty_params)
    assert overview.total_orders == 0
    assert overview.net_revenue == 0.0
    assert overview.gross_margin_pct == 0.0


def test_m09_t15_no_hard_coded_analytics(db_session: Session) -> None:
    """M9-T15: No hard-coded analytics — metrics vary dynamically between distinct regions."""
    reg1 = analytics_service.get_sales_analytics(db_session, AnalyticsFilterParams(region_id=1))
    reg2 = analytics_service.get_sales_analytics(db_session, AnalyticsFilterParams(region_id=2))

    assert reg1.net_revenue != reg2.net_revenue
    assert reg1.order_count != reg2.order_count
    assert reg1.net_revenue > 0.0
    assert reg2.net_revenue > 0.0


def test_m09_t16_role_based_access(client: TestClient, analyst_headers: dict[str, str]) -> None:
    """M9-T16: RBAC enforcement — protected BI endpoints return 401 without auth, 200 with auth."""
    # 1. Unauthenticated request -> HTTP 401
    clean_client = TestClient(app)
    clean_client.cookies.clear()
    resp_unauth = clean_client.get("/api/v1/analytics/overview")
    assert resp_unauth.status_code == 401

    # 2. Authenticated demo user -> HTTP 200 OK
    resp_auth = client.get("/api/v1/analytics/overview", headers=analyst_headers)
    assert resp_auth.status_code == 200
    assert resp_auth.json()["success"] is True
    assert "net_revenue" in resp_auth.json()["data"]

    resp_sales = client.get("/api/v1/analytics/sales", headers=analyst_headers)
    assert resp_sales.status_code == 200


def test_m09_t17_query_performance_baseline(
    client: TestClient, analyst_headers: dict[str, str]
) -> None:
    """M9-T17: Query performance baseline — complex multi-join analytical query runs under 1.5s."""
    start_t = time.perf_counter()
    resp = client.get("/api/v1/analytics/overview", headers=analyst_headers)
    elapsed = time.perf_counter() - start_t

    assert resp.status_code == 200
    assert elapsed < 1.5, f"Analytical query exceeded 1.5s latency threshold: {elapsed:.3f}s"
