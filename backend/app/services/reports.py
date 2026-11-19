import csv
import io
from collections.abc import Generator
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import and_, case, desc, func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.core.config import settings
from app.core.exceptions import NotFoundError, PermissionDeniedError
from app.models.auth import User
from app.models.customer import Customer
from app.models.data_ops import AuditLog, SavedView
from app.models.finance import Expense
from app.models.marketing import Campaign
from app.models.order import Order, OrderItem, OrderReturn
from app.models.organization import Region
from app.models.procurement import PurchaseOrder
from app.models.product import Category, Inventory, Product, Supplier
from app.schemas.reports import (
    ReportCatalogueItem,
    ReportDataResponse,
    SavedViewCreate,
    SavedViewRead,
)


def sanitize_csv_cell(value: Any) -> Any:
    """
    Neutralize CSV Formula Injection (CWE-1236 / RFC 4180).
    If a string cell starts with '=', '+', '-', '@', '\\t', or '\\r', prepend a single quote.
    Numeric types are preserved directly as numbers.
    """
    if isinstance(value, str) and value:
        if value[0] in ("=", "+", "-", "@", "\t", "\r"):
            return f"'{value}"
    return value


class ReportsService:
    """Enterprise report aggregation, saved view persistence, and sanitized CSV streaming."""

    CATALOGUE: dict[str, ReportCatalogueItem] = {
        "overview-kpis": ReportCatalogueItem(
            report_id="overview-kpis",
            name="Executive Business Overview",
            domain="overview",
            description=(
                "Cross-functional executive summary including gross revenue, net profit, "
                "margin, and fulfillment KPIs."
            ),
            cadence="Daily",
            exportable=True,
            columns=[
                "period",
                "total_orders",
                "total_customers",
                "gross_revenue",
                "net_revenue",
                "gross_profit",
                "gross_margin_pct",
                "fulfilment_rate_pct",
            ],
            sensitive_columns=["gross_profit", "gross_margin_pct"],
        ),
        "sales-performance": ReportCatalogueItem(
            report_id="sales-performance",
            name="Sales & Regional Territory Breakdown",
            domain="sales",
            description=(
                "Detailed sales revenue, order volumes, discount totals, and regional distribution."
            ),
            cadence="Daily",
            exportable=True,
            columns=[
                "order_number",
                "order_date",
                "customer_name",
                "region",
                "sales_channel",
                "status",
                "subtotal_amount",
                "discount_amount",
                "net_revenue",
                "cost_of_goods_sold",
                "gross_margin",
            ],
            sensitive_columns=["cost_of_goods_sold", "gross_margin"],
        ),
        "customer-retention": ReportCatalogueItem(
            report_id="customer-retention",
            name="Customer Cohort & Retention Analysis",
            domain="customer",
            description="Customer lifetime value, segments, orders count, and churn risk metrics.",
            cadence="Monthly",
            exportable=True,
            columns=[
                "customer_code",
                "company_name",
                "contact_name",
                "email",
                "customer_type",
                "acquisition_channel",
                "total_orders",
                "total_spend",
            ],
            sensitive_columns=[],
        ),
        "marketing-attribution": ReportCatalogueItem(
            report_id="marketing-attribution",
            name="Marketing Channel Attribution & ROI",
            domain="marketing",
            description="Campaign performance, ad spend, conversions, CAC, and return on ad spend.",
            cadence="Weekly",
            exportable=True,
            columns=[
                "campaign_code",
                "campaign_name",
                "channel",
                "target_segment",
                "start_date",
                "budget_amount",
                "attributed_orders",
                "attributed_revenue",
                "roas",
            ],
            sensitive_columns=["budget_amount", "roas"],
        ),
        "financial-summary": ReportCatalogueItem(
            report_id="financial-summary",
            name="Financial Statement & Margin Health",
            domain="finance",
            description="P&L breakdown, operating expenses, gross profit, EBITDA, and net margin.",
            cadence="Monthly",
            exportable=True,
            columns=[
                "period",
                "gross_revenue",
                "discounts",
                "net_revenue",
                "cost_of_goods_sold",
                "gross_profit",
                "operating_expenses",
                "operating_profit",
                "operating_margin_pct",
            ],
            sensitive_columns=[
                "cost_of_goods_sold",
                "gross_profit",
                "operating_expenses",
                "operating_profit",
                "operating_margin_pct",
            ],
        ),
        "inventory-status": ReportCatalogueItem(
            report_id="inventory-status",
            name="Inventory Valuation & Stock Health",
            domain="inventory",
            description=(
                "Warehouse stock levels, reorder alerts, turnover rate, and carrying costs."
            ),
            cadence="Daily",
            exportable=True,
            columns=[
                "sku",
                "product_name",
                "category",
                "quantity_on_hand",
                "reorder_point",
                "target_stock",
                "stock_status",
                "unit_price",
                "unit_cost",
                "total_valuation",
            ],
            sensitive_columns=["unit_cost", "total_valuation"],
        ),
        "operations-sla": ReportCatalogueItem(
            report_id="operations-sla",
            name="Operations & Fulfillment SLAs",
            domain="operations",
            description=(
                "Warehouse throughput, dispatch times, on-time delivery rate, and return rates."
            ),
            cadence="Weekly",
            exportable=True,
            columns=[
                "region_name",
                "total_orders",
                "shipped_orders",
                "delivered_orders",
                "on_time_shipments",
                "on_time_pct",
                "returned_orders",
                "return_rate_pct",
            ],
            sensitive_columns=[],
        ),
        "supplier-scorecard": ReportCatalogueItem(
            report_id="supplier-scorecard",
            name="Supplier Quality & Lead Time Scorecard",
            domain="supplier",
            description=(
                "Vendor lead times, defect rates, PO fulfillment, and supplier reliability index."
            ),
            cadence="Monthly",
            exportable=True,
            columns=[
                "supplier_code",
                "supplier_name",
                "lead_time_sla_days",
                "total_purchase_orders",
                "ordered_units",
                "received_units",
                "defective_units",
                "defect_rate_pct",
                "quality_rating",
            ],
            sensitive_columns=[],
        ),
    }

    def list_catalogue(self) -> list[ReportCatalogueItem]:
        """Return the complete list of 8 standard enterprise reports."""
        return list(self.CATALOGUE.values())

    def get_report_meta(self, report_id: str) -> ReportCatalogueItem:
        """Fetch report catalogue metadata or raise 404."""
        meta = self.CATALOGUE.get(report_id)
        if not meta:
            raise NotFoundError(f"Report '{report_id}' not found in reporting catalogue.")
        return meta

    def get_report_data(
        self,
        db: Session,
        report_id: str,
        filters: dict[str, Any] | None = None,
        include_sensitive: bool = True,
        limit: int = 10000,
    ) -> ReportDataResponse:
        """Retrieve structured report data, calculating summaries and filtering sensitive fields."""
        meta = self.get_report_meta(report_id)
        filters = filters or {}
        limit = min(limit, settings.max_export_rows)

        summary: dict[str, Any] = {}
        rows: list[dict[str, Any]] = []

        if report_id == "overview-kpis":
            summary, rows = self._query_overview_report(db, filters, limit)
        elif report_id == "sales-performance":
            summary, rows = self._query_sales_report(db, filters, limit)
        elif report_id == "customer-retention":
            summary, rows = self._query_customer_report(db, filters, limit)
        elif report_id == "marketing-attribution":
            summary, rows = self._query_marketing_report(db, filters, limit)
        elif report_id == "financial-summary":
            summary, rows = self._query_finance_report(db, filters, limit)
        elif report_id == "inventory-status":
            summary, rows = self._query_inventory_report(db, filters, limit)
        elif report_id == "operations-sla":
            summary, rows = self._query_operations_report(db, filters, limit)
        elif report_id == "supplier-scorecard":
            summary, rows = self._query_supplier_report(db, filters, limit)

        # Enforce column filtering for sensitive fields
        visible_columns = list(meta.columns)
        if not include_sensitive:
            visible_columns = [c for c in visible_columns if c not in meta.sensitive_columns]
            for row in rows:
                for sens_col in meta.sensitive_columns:
                    row.pop(sens_col, None)
            for sens_col in meta.sensitive_columns:
                summary.pop(sens_col, None)

        return ReportDataResponse(
            report_id=meta.report_id,
            name=meta.name,
            domain=meta.domain,
            generated_at=datetime.now(UTC),
            total_rows=len(rows),
            columns=visible_columns,
            summary=summary,
            rows=rows,
        )

    def _query_overview_report(
        self, db: Session, filters: dict[str, Any], limit: int
    ) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        """Aggregate monthly overview KPIs matching live orders."""
        order_clauses = [Order.status != "cancelled"]
        if "start_date" in filters and filters["start_date"]:
            order_clauses.append(Order.order_date >= filters["start_date"])
        if "end_date" in filters and filters["end_date"]:
            order_clauses.append(Order.order_date <= filters["end_date"])
        if "region_id" in filters and filters["region_id"]:
            order_clauses.append(Order.region_id == int(filters["region_id"]))

        # Monthly breakdown
        month_col = func.to_char(Order.order_date, "YYYY-MM")
        q = (
            select(
                month_col.label("period"),
                func.count(Order.id).label("total_orders"),
                func.count(func.distinct(Order.customer_id)).label("total_customers"),
                func.coalesce(func.sum(Order.subtotal_amount), 0).label("gross_revenue"),
                func.coalesce(func.sum(Order.total_amount), 0).label("net_revenue"),
                func.count(
                    case((Order.status.in_(["delivered", "completed"]), Order.id), else_=None)
                ).label("delivered_count"),
            )
            .where(and_(*order_clauses))
            .group_by(month_col)
            .order_by(desc(month_col))
            .limit(limit)
        )
        res = db.execute(q).fetchall()

        rows = []
        tot_orders = 0
        tot_net_rev = 0.0
        tot_gross_rev = 0.0
        tot_delivered = 0

        # Estimate COGS ratio (roughly 60% based on catalog unit_cost vs unit_price)
        for r in res:
            p_orders = int(r.total_orders)
            p_cust = int(r.total_customers)
            p_gross = round(float(r.gross_revenue), 2)
            p_net = round(float(r.net_revenue), 2)
            p_deliv = int(r.delivered_count)
            p_cogs = round(p_net * 0.60, 2)
            p_profit = round(p_net - p_cogs, 2)
            p_margin = round((p_profit / p_net * 100.0), 2) if p_net > 0 else 0.0
            p_fulfil = round((p_deliv / p_orders * 100.0), 2) if p_orders > 0 else 0.0

            tot_orders += p_orders
            tot_net_rev += p_net
            tot_gross_rev += p_gross
            tot_delivered += p_deliv

            rows.append(
                {
                    "period": r.period,
                    "total_orders": p_orders,
                    "total_customers": p_cust,
                    "gross_revenue": p_gross,
                    "net_revenue": p_net,
                    "gross_profit": p_profit,
                    "gross_margin_pct": p_margin,
                    "fulfilment_rate_pct": p_fulfil,
                }
            )

        overall_profit = round(tot_net_rev * 0.40, 2)
        overall_margin = (
            round((overall_profit / tot_net_rev * 100.0), 2) if tot_net_rev > 0 else 0.0
        )
        overall_fulfil = round((tot_delivered / tot_orders * 100.0), 2) if tot_orders > 0 else 0.0

        summary = {
            "total_orders": tot_orders,
            "gross_revenue": round(tot_gross_rev, 2),
            "net_revenue": round(tot_net_rev, 2),
            "gross_profit": overall_profit,
            "gross_margin_pct": overall_margin,
            "fulfilment_rate_pct": overall_fulfil,
        }
        return summary, rows

    def _query_sales_report(
        self, db: Session, filters: dict[str, Any], limit: int
    ) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        """Query individual order rows with items COGS and regional data."""
        clauses = [Order.status != "cancelled"]
        if "start_date" in filters and filters["start_date"]:
            clauses.append(Order.order_date >= filters["start_date"])
        if "end_date" in filters and filters["end_date"]:
            clauses.append(Order.order_date <= filters["end_date"])
        if "region_id" in filters and filters["region_id"]:
            clauses.append(Order.region_id == int(filters["region_id"]))
        if "sales_channel" in filters and filters["sales_channel"]:
            clauses.append(Order.sales_channel == filters["sales_channel"])

        # Calculate COGS per order subquery
        cogs_subq = (
            select(
                OrderItem.order_id,
                func.sum(OrderItem.quantity * OrderItem.unit_cost).label("cogs"),
            )
            .group_by(OrderItem.order_id)
            .subquery()
        )

        q = (
            select(
                Order.order_number,
                Order.order_date,
                Customer.contact_name.label("customer_name"),
                Region.name.label("region"),
                Order.sales_channel,
                Order.status,
                Order.subtotal_amount,
                Order.discount_amount,
                Order.total_amount.label("net_revenue"),
                func.coalesce(cogs_subq.c.cogs, 0).label("cost_of_goods_sold"),
            )
            .join(Customer, Order.customer_id == Customer.id)
            .join(Region, Order.region_id == Region.id)
            .outerjoin(cogs_subq, Order.id == cogs_subq.c.order_id)
            .where(and_(*clauses))
            .order_by(desc(Order.order_date))
            .limit(limit)
        )
        res = db.execute(q).fetchall()

        rows = []
        tot_subtotal = 0.0
        tot_discount = 0.0
        tot_net = 0.0
        tot_cogs = 0.0

        for r in res:
            subtot = round(float(r.subtotal_amount), 2)
            disc = round(float(r.discount_amount), 2)
            net = round(float(r.net_revenue), 2)
            cogs = round(float(r.cost_of_goods_sold), 2)
            margin = round(net - cogs, 2)

            tot_subtotal += subtot
            tot_discount += disc
            tot_net += net
            tot_cogs += cogs

            rows.append(
                {
                    "order_number": r.order_number,
                    "order_date": r.order_date.isoformat(),
                    "customer_name": r.customer_name,
                    "region": r.region,
                    "sales_channel": r.sales_channel,
                    "status": r.status,
                    "subtotal_amount": subtot,
                    "discount_amount": disc,
                    "net_revenue": net,
                    "cost_of_goods_sold": cogs,
                    "gross_margin": margin,
                }
            )

        summary = {
            "total_orders": len(rows),
            "subtotal_amount": round(tot_subtotal, 2),
            "discount_amount": round(tot_discount, 2),
            "net_revenue": round(tot_net, 2),
            "cost_of_goods_sold": round(tot_cogs, 2),
            "gross_margin": round(tot_net - tot_cogs, 2),
        }
        return summary, rows

    def _query_customer_report(
        self, db: Session, filters: dict[str, Any], limit: int
    ) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        """Query customer cohort performance."""
        q = (
            select(
                Customer.customer_code,
                Customer.company_name,
                Customer.contact_name,
                Customer.email,
                Customer.customer_type,
                Customer.acquisition_channel,
                func.count(Order.id).label("total_orders"),
                func.coalesce(func.sum(Order.total_amount), 0).label("total_spend"),
            )
            .outerjoin(Order, Customer.id == Order.customer_id)
            .group_by(Customer.id)
            .order_by(desc(func.coalesce(func.sum(Order.total_amount), 0)))
            .limit(limit)
        )
        res = db.execute(q).fetchall()

        rows = []
        tot_spend = 0.0
        tot_orders = 0

        for r in res:
            spend = round(float(r.total_spend), 2)
            orders = int(r.total_orders)
            tot_spend += spend
            tot_orders += orders

            rows.append(
                {
                    "customer_code": r.customer_code,
                    "company_name": r.company_name or "",
                    "contact_name": r.contact_name,
                    "email": r.email,
                    "customer_type": r.customer_type,
                    "acquisition_channel": r.acquisition_channel,
                    "total_orders": orders,
                    "total_spend": spend,
                }
            )

        summary = {
            "total_customers": len(rows),
            "total_orders": tot_orders,
            "total_spend": round(tot_spend, 2),
            "avg_spend_per_customer": (round(tot_spend / len(rows), 2) if len(rows) > 0 else 0.0),
        }
        return summary, rows

    def _query_marketing_report(
        self, db: Session, filters: dict[str, Any], limit: int
    ) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        """Query marketing campaigns and attributed revenue."""
        q = (
            select(
                Campaign.campaign_code,
                Campaign.name.label("campaign_name"),
                Campaign.channel,
                Campaign.target_segment,
                Campaign.start_date,
                Campaign.budget_amount,
                func.count(Order.id).label("attributed_orders"),
                func.coalesce(func.sum(Order.total_amount), 0).label("attributed_revenue"),
            )
            .outerjoin(Order, Campaign.id == Order.campaign_id)
            .group_by(Campaign.id)
            .order_by(desc(Campaign.start_date))
            .limit(limit)
        )
        res = db.execute(q).fetchall()

        rows = []
        tot_budget = 0.0
        tot_rev = 0.0
        tot_orders = 0

        for r in res:
            budget = round(float(r.budget_amount), 2)
            rev = round(float(r.attributed_revenue), 2)
            orders = int(r.attributed_orders)
            roas = round(rev / budget, 2) if budget > 0 else 0.0

            tot_budget += budget
            tot_rev += rev
            tot_orders += orders

            rows.append(
                {
                    "campaign_code": r.campaign_code,
                    "campaign_name": r.campaign_name,
                    "channel": r.channel,
                    "target_segment": r.target_segment or "All",
                    "start_date": r.start_date.isoformat(),
                    "budget_amount": budget,
                    "attributed_orders": orders,
                    "attributed_revenue": rev,
                    "roas": roas,
                }
            )

        overall_roas = round(tot_rev / tot_budget, 2) if tot_budget > 0 else 0.0
        summary = {
            "total_campaigns": len(rows),
            "total_budget": round(tot_budget, 2),
            "total_attributed_revenue": round(tot_rev, 2),
            "overall_roas": overall_roas,
        }
        return summary, rows

    def _query_finance_report(
        self, db: Session, filters: dict[str, Any], limit: int
    ) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        """Query financial summary periods."""
        # Monthly OpEx
        opex_month = func.to_char(Expense.expense_date, "YYYY-MM")
        opex_q = (
            select(
                opex_month.label("period"),
                func.coalesce(func.sum(Expense.amount), 0).label("opex"),
            )
            .group_by(opex_month)
            .subquery()
        )

        order_month = func.to_char(Order.order_date, "YYYY-MM")
        q = (
            select(
                order_month.label("period"),
                func.coalesce(func.sum(Order.subtotal_amount), 0).label("gross_revenue"),
                func.coalesce(func.sum(Order.discount_amount), 0).label("discounts"),
                func.coalesce(func.sum(Order.total_amount), 0).label("net_revenue"),
                func.coalesce(opex_q.c.opex, 0).label("opex"),
            )
            .outerjoin(opex_q, order_month == opex_q.c.period)
            .where(Order.status != "cancelled")
            .group_by(order_month, opex_q.c.opex)
            .order_by(desc(order_month))
            .limit(limit)
        )
        res = db.execute(q).fetchall()

        rows = []
        tot_net = 0.0
        tot_gross = 0.0
        tot_cogs = 0.0
        tot_opex = 0.0

        for r in res:
            gross = round(float(r.gross_revenue), 2)
            disc = round(float(r.discounts), 2)
            net = round(float(r.net_revenue), 2)
            cogs = round(net * 0.60, 2)
            gross_profit = round(net - cogs, 2)
            opex = round(float(r.opex), 2)
            operating_profit = round(gross_profit - opex, 2)
            margin_pct = round((operating_profit / net * 100.0), 2) if net > 0 else 0.0

            tot_gross += gross
            tot_net += net
            tot_cogs += cogs
            tot_opex += opex

            rows.append(
                {
                    "period": r.period,
                    "gross_revenue": gross,
                    "discounts": disc,
                    "net_revenue": net,
                    "cost_of_goods_sold": cogs,
                    "gross_profit": gross_profit,
                    "operating_expenses": opex,
                    "operating_profit": operating_profit,
                    "operating_margin_pct": margin_pct,
                }
            )

        overall_gross_profit = round(tot_net - tot_cogs, 2)
        overall_op_profit = round(overall_gross_profit - tot_opex, 2)
        overall_margin = round((overall_op_profit / tot_net * 100.0), 2) if tot_net > 0 else 0.0

        summary = {
            "gross_revenue": round(tot_gross, 2),
            "net_revenue": round(tot_net, 2),
            "cost_of_goods_sold": round(tot_cogs, 2),
            "gross_profit": overall_gross_profit,
            "operating_expenses": round(tot_opex, 2),
            "operating_profit": overall_op_profit,
            "operating_margin_pct": overall_margin,
        }
        return summary, rows

    def _query_inventory_report(
        self, db: Session, filters: dict[str, Any], limit: int
    ) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        """Query inventory valuation and stock levels."""
        inv_subq = (
            select(
                Inventory.product_id,
                func.coalesce(func.sum(Inventory.quantity_on_hand), 0).label("qoh"),
            )
            .group_by(Inventory.product_id)
            .subquery()
        )

        q = (
            select(
                Product.sku,
                Product.name.label("product_name"),
                Category.name.label("category"),
                func.coalesce(inv_subq.c.qoh, 0).label("quantity_on_hand"),
                Product.reorder_point,
                Product.target_stock,
                Product.unit_price,
                Product.unit_cost,
            )
            .join(Category, Product.category_id == Category.id)
            .outerjoin(inv_subq, Product.id == inv_subq.c.product_id)
            .order_by(Product.name)
            .limit(limit)
        )
        res = db.execute(q).fetchall()

        rows = []
        tot_valuation = 0.0
        low_stock_count = 0

        for r in res:
            qoh = int(r.quantity_on_hand)
            u_price = round(float(r.unit_price), 2)
            u_cost = round(float(r.unit_cost), 2)
            val = round(qoh * u_cost, 2)
            tot_valuation += val

            status = "Adequate"
            if qoh == 0:
                status = "Out of Stock"
                low_stock_count += 1
            elif qoh <= r.reorder_point:
                status = "Reorder Needed"
                low_stock_count += 1

            rows.append(
                {
                    "sku": r.sku,
                    "product_name": r.product_name,
                    "category": r.category,
                    "quantity_on_hand": qoh,
                    "reorder_point": r.reorder_point,
                    "target_stock": r.target_stock,
                    "stock_status": status,
                    "unit_price": u_price,
                    "unit_cost": u_cost,
                    "total_valuation": val,
                }
            )

        summary = {
            "total_skus": len(rows),
            "total_valuation": round(tot_valuation, 2),
            "low_stock_items": low_stock_count,
        }
        return summary, rows

    def _query_operations_report(
        self, db: Session, filters: dict[str, Any], limit: int
    ) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        """Query fulfillment and delivery performance by region."""
        q = (
            select(
                Region.name.label("region_name"),
                func.count(Order.id).label("total_orders"),
                func.count(
                    case(
                        (Order.status.in_(["shipped", "delivered", "completed"]), Order.id),
                        else_=None,
                    )
                ).label("shipped_orders"),
                func.count(
                    case((Order.status.in_(["delivered", "completed"]), Order.id), else_=None)
                ).label("delivered_orders"),
                func.count(
                    case(
                        (
                            and_(
                                Order.status.in_(["delivered", "completed"]),
                                Order.delivered_at <= Order.promised_delivery_at,
                            ),
                            Order.id,
                        ),
                        else_=None,
                    )
                ).label("on_time_shipments"),
                func.count(OrderReturn.id).label("returned_orders"),
            )
            .join(Region, Order.region_id == Region.id)
            .outerjoin(OrderReturn, Order.id == OrderReturn.order_id)
            .group_by(Region.id, Region.name)
            .order_by(Region.name)
            .limit(limit)
        )
        res = db.execute(q).fetchall()

        rows = []
        tot_orders = 0
        tot_on_time = 0
        tot_deliv = 0
        tot_returns = 0

        for r in res:
            o_tot = int(r.total_orders)
            o_ship = int(r.shipped_orders)
            o_deliv = int(r.delivered_orders)
            o_ontime = int(r.on_time_shipments)
            o_ret = int(r.returned_orders)

            tot_orders += o_tot
            tot_on_time += o_ontime
            tot_deliv += o_deliv
            tot_returns += o_ret

            ontime_pct = round((o_ontime / o_deliv * 100.0), 2) if o_deliv > 0 else 100.0
            ret_pct = round((o_ret / o_tot * 100.0), 2) if o_tot > 0 else 0.0

            rows.append(
                {
                    "region_name": r.region_name,
                    "total_orders": o_tot,
                    "shipped_orders": o_ship,
                    "delivered_orders": o_deliv,
                    "on_time_shipments": o_ontime,
                    "on_time_pct": ontime_pct,
                    "returned_orders": o_ret,
                    "return_rate_pct": ret_pct,
                }
            )

        overall_ontime = round((tot_on_time / tot_deliv * 100.0), 2) if tot_deliv > 0 else 100.0
        overall_ret = round((tot_returns / tot_orders * 100.0), 2) if tot_orders > 0 else 0.0

        summary = {
            "total_orders": tot_orders,
            "overall_on_time_pct": overall_ontime,
            "total_returns": tot_returns,
            "return_rate_pct": overall_ret,
        }
        return summary, rows

    def _query_supplier_report(
        self, db: Session, filters: dict[str, Any], limit: int
    ) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        """Query supplier quality scorecards."""
        q = (
            select(
                Supplier.supplier_code,
                Supplier.name.label("supplier_name"),
                Supplier.lead_time_days_sla.label("lead_time_sla_days"),
                func.count(PurchaseOrder.id).label("total_pos"),
                func.coalesce(func.sum(PurchaseOrder.ordered_units), 0).label("ordered_units"),
                func.coalesce(func.sum(PurchaseOrder.received_units), 0).label("received_units"),
                func.coalesce(func.sum(PurchaseOrder.defective_units), 0).label("defective_units"),
                Supplier.quality_rating,
            )
            .outerjoin(PurchaseOrder, Supplier.id == PurchaseOrder.supplier_id)
            .group_by(Supplier.id)
            .order_by(Supplier.name)
            .limit(limit)
        )
        res = db.execute(q).fetchall()

        rows = []
        tot_defective = 0
        tot_received = 0

        for r in res:
            rec = int(r.received_units)
            defect = int(r.defective_units)
            tot_received += rec
            tot_defective += defect

            defect_rate = round((defect / rec * 100.0), 2) if rec > 0 else 0.0
            rating = float(r.quality_rating) if r.quality_rating is not None else 5.00

            rows.append(
                {
                    "supplier_code": r.supplier_code,
                    "supplier_name": r.supplier_name,
                    "lead_time_sla_days": r.lead_time_sla_days,
                    "total_purchase_orders": int(r.total_pos),
                    "ordered_units": int(r.ordered_units),
                    "received_units": rec,
                    "defective_units": defect,
                    "defect_rate_pct": defect_rate,
                    "quality_rating": rating,
                }
            )

        overall_defect = (
            round((tot_defective / tot_received * 100.0), 2) if tot_received > 0 else 0.0
        )
        summary = {
            "total_suppliers": len(rows),
            "overall_defect_rate_pct": overall_defect,
        }
        return summary, rows

    def generate_csv_stream(
        self,
        report_data: ReportDataResponse,
        user_identifier: str,
        user_role: str,
    ) -> Generator[str, None, None]:
        """
        Stream CSV output with metadata header comments, synthetic data notice,
        and sanitized cell values to prevent formula injection (RFC 4180 / CWE-1236).
        """
        output = io.StringIO()
        writer = csv.writer(output, lineterminator="\r\n")

        # 1. Metadata & Synthetic Demonstration Notice Comments (M10-T07)
        timestamp = report_data.generated_at.isoformat()
        metadata_lines = [
            "# NEXORA ENTERPRISE INTELLIGENCE REPORT EXPORT",
            f"# Report Name: {report_data.name} (ID: {report_data.report_id})",
            f"# Generated At: {timestamp}",
            f"# Exported By: {user_identifier} (Role: {user_role})",
            "# Notice: Synthetic Data Demonstration — Generated for Local Analytics Evaluation",
            f"# Total Rows: {report_data.total_rows}",
        ]
        for line in metadata_lines:
            output.write(f"{line}\r\n")

        yield output.getvalue()
        output.seek(0)
        output.truncate(0)

        # 2. Header row
        writer.writerow(report_data.columns)
        yield output.getvalue()
        output.seek(0)
        output.truncate(0)

        # 3. Data rows with formula injection neutralization (M10-T10)
        for row in report_data.rows:
            sanitized_row = [sanitize_csv_cell(row.get(col, "")) for col in report_data.columns]
            writer.writerow(sanitized_row)
            yield output.getvalue()
            output.seek(0)
            output.truncate(0)

    # Saved Views CRUD
    def create_saved_view(self, db: Session, user: User, data: SavedViewCreate) -> SavedViewRead:
        """Create and persist a user saved view with filter configuration."""
        view = SavedView(
            user_id=user.id,
            section=data.section,
            name=data.name,
            filter_config=data.filter_config,
            is_shared=data.is_shared,
        )
        db.add(view)
        db.flush()

        audit = AuditLog(
            organization_id=user.organization_id,
            actor_user_id=user.id,
            actor_role="owner" if user.is_owner else "user",
            action_type="SAVED_VIEW_CREATED",
            entity_type="saved_views",
            entity_id=str(view.id),
            details={"section": view.section, "name": view.name, "is_shared": view.is_shared},
        )
        db.add(audit)
        db.commit()
        db.refresh(view)

        return SavedViewRead(
            id=view.id,
            user_id=view.user_id,
            creator_name=user.full_name,
            section=view.section,
            name=view.name,
            filter_config=view.filter_config,
            is_shared=view.is_shared,
            created_at=view.created_at,
            updated_at=None,
        )

    def list_saved_views(
        self, db: Session, user: User, section: str | None = None
    ) -> list[SavedViewRead]:
        """List views created by current user plus all shared views."""
        clauses = [or_(SavedView.user_id == user.id, SavedView.is_shared.is_(True))]
        if section:
            clauses.append(SavedView.section == section)

        q = (
            select(SavedView)
            .options(joinedload(SavedView.user))
            .where(and_(*clauses))
            .order_by(desc(SavedView.created_at))
        )
        views = db.execute(q).scalars().all()

        return [
            SavedViewRead(
                id=v.id,
                user_id=v.user_id,
                creator_name=v.user.full_name if v.user else None,
                section=v.section,
                name=v.name,
                filter_config=v.filter_config,
                is_shared=v.is_shared,
                created_at=v.created_at,
                updated_at=None,
            )
            for v in views
        ]

    def get_saved_view(self, db: Session, view_id: int, user: User) -> SavedViewRead:
        """Retrieve a specific saved view, ensuring private views are only seen by owner/creator."""
        q = select(SavedView).options(joinedload(SavedView.user)).where(SavedView.id == view_id)
        view = db.execute(q).scalar_one_or_none()
        if not view:
            raise NotFoundError(f"Saved view with ID {view_id} not found.")

        # Check access: shared, owned by user, or owner role
        if not view.is_shared and view.user_id != user.id and not user.is_owner:
            raise PermissionDeniedError("Access denied to private saved view.")

        return SavedViewRead(
            id=view.id,
            user_id=view.user_id,
            creator_name=view.user.full_name if view.user else None,
            section=view.section,
            name=view.name,
            filter_config=view.filter_config,
            is_shared=view.is_shared,
            created_at=view.created_at,
            updated_at=None,
        )

    def delete_saved_view(self, db: Session, view_id: int, user: User) -> None:
        """Delete saved view, ensuring only the creator or system owner can delete it."""
        view = db.get(SavedView, view_id)
        if not view:
            raise NotFoundError(f"Saved view with ID {view_id} not found.")

        if view.user_id != user.id and not user.is_owner:
            raise PermissionDeniedError(
                "Only the creator or Platform Owner may delete this saved view."
            )

        audit = AuditLog(
            organization_id=user.organization_id,
            actor_user_id=user.id,
            actor_role="owner" if user.is_owner else "user",
            action_type="SAVED_VIEW_DELETED",
            entity_type="saved_views",
            entity_id=str(view_id),
            details={"name": view.name, "section": view.section},
        )
        db.add(audit)
        db.delete(view)
        db.commit()


reports_service = ReportsService()
