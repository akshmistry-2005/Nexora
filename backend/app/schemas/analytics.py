from typing import Any

from pydantic import BaseModel


class AnalyticsFilterParams(BaseModel):
    """Common filtering parameters across analytical intelligence queries."""

    start_date: str | None = None
    end_date: str | None = None
    region_id: int | None = None
    category_id: int | None = None
    sales_channel: str | None = None
    customer_type: str | None = None


class OverviewAnalyticsResponse(BaseModel):
    """High-level consolidated executive KPI summary."""

    net_revenue: float
    total_orders: int
    total_customers: int
    active_customers: int
    average_order_value: float
    gross_profit: float
    gross_margin_pct: float
    total_expenses: float
    net_profit: float
    net_margin_pct: float
    inventory_valuation: float
    fulfilment_rate: float
    marketing_spend: float
    revenue_trend: list[dict[str, Any]]
    regional_breakdown: list[dict[str, Any]]
    top_products: list[dict[str, Any]]


class SalesAnalyticsResponse(BaseModel):
    """Detailed sales volume, product performance, and channel intelligence."""

    gross_revenue: float
    total_discounts: float
    total_refunds: float
    net_revenue: float
    order_count: int
    units_sold: int
    aov: float
    discount_rate_pct: float
    channel_breakdown: list[dict[str, Any]]
    regional_breakdown: list[dict[str, Any]]
    category_breakdown: list[dict[str, Any]]
    monthly_trend: list[dict[str, Any]]
    sales_rep_leaderboard: list[dict[str, Any]]


class CustomerAnalyticsResponse(BaseModel):
    """Customer acquisition, cohort activity, and lifetime value intelligence."""

    total_customers: int
    active_customers: int
    new_customers: int
    churn_count: int
    churn_rate_pct: float
    arpu: float
    segment_breakdown: list[dict[str, Any]]
    acquisition_breakdown: list[dict[str, Any]]
    regional_breakdown: list[dict[str, Any]]
    top_customers: list[dict[str, Any]]


class MarketingAnalyticsResponse(BaseModel):
    """Marketing campaign spend, conversion rates, and ROI metrics."""

    total_spend: float
    impressions: int
    clicks: int
    conversions: int
    ctr_pct: float
    cpc: float
    cac: float
    roas: float
    attributed_revenue: float
    channel_breakdown: list[dict[str, Any]]
    top_campaigns: list[dict[str, Any]]


class FinanceAnalyticsResponse(BaseModel):
    """P&L summary, margin health, and budget vs actual variance."""

    net_revenue: float
    cogs: float
    gross_profit: float
    gross_margin_pct: float
    operating_expenses: float
    net_profit: float
    net_margin_pct: float
    total_allocated_budget: float
    total_actual_spend: float
    budget_variance_amount: float
    budget_variance_pct: float
    expense_categories: list[dict[str, Any]]
    department_budgets: list[dict[str, Any]]


class InventoryAnalyticsResponse(BaseModel):
    """Warehouse stock valuation, availability, turnover, and reorder warnings."""

    total_skus: int
    available_stock_units: int
    inventory_valuation: float
    low_stock_count: int
    out_of_stock_count: int
    turnover_rate: float
    warehouse_breakdown: list[dict[str, Any]]
    category_breakdown: list[dict[str, Any]]
    reorder_alerts: list[dict[str, Any]]


class OperationsAnalyticsResponse(BaseModel):
    """Fulfilment throughput, delivery SLA compliance, and return tracking."""

    total_orders_processed: int
    fulfilment_rate_pct: float
    avg_fulfilment_hours: float
    avg_delivery_days: float
    on_time_delivery_rate_pct: float
    return_rate_pct: float
    cancellation_rate_pct: float
    status_pipeline: list[dict[str, Any]]
    returns_by_reason: list[dict[str, Any]]


class SupplierAnalyticsResponse(BaseModel):
    """Procurement expenditures, delivery lead times, and supplier quality."""

    total_suppliers: int
    active_suppliers: int
    po_count: int
    total_supplier_spend: float
    avg_lead_time_days: float
    on_time_delivery_rate_pct: float
    defect_rate_pct: float
    supplier_scorecard: list[dict[str, Any]]


class AnalyticsLedgerItem(BaseModel):
    """Drill-down ledger item representing underlying transaction record."""

    id: int
    order_number: str
    customer_name: str
    sales_channel: str
    order_date: str
    status: str
    region: str
    total_amount: float
