from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class OrderItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: int
    quantity: int
    unit_cost: Decimal
    unit_price: Decimal
    discount_amount: Decimal
    total_line_amount: Decimal


class OrderRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    organization_id: int
    order_number: str
    customer_id: int
    sales_rep_id: int | None
    region_id: int
    warehouse_id: int | None
    campaign_id: int | None
    order_date: datetime
    status: str
    sales_channel: str
    subtotal_amount: Decimal
    discount_amount: Decimal
    tax_amount: Decimal
    shipping_amount: Decimal
    total_amount: Decimal
    shipped_at: datetime | None
    delivered_at: datetime | None


class OrderDetailRead(OrderRead):
    items: list[OrderItemRead] = []


class OrderFilterParams(BaseModel):
    """Query filters for orders endpoint."""

    status: (
        Literal["pending", "processing", "shipped", "completed", "cancelled", "returned"] | None
    ) = Field(default=None, description="Filter by order lifecycle status")
    region_id: int | None = Field(default=None, description="Filter by region ID")
    sales_channel: Literal["Direct", "Online", "Partner", "Field Sales"] | None = Field(
        default=None, description="Filter by sales channel"
    )
    customer_id: int | None = Field(default=None, description="Filter by customer ID")
    start_date: datetime | None = Field(default=None, description="Earliest order datetime")
    end_date: datetime | None = Field(default=None, description="Latest order datetime")
    sort_by: Literal["id", "order_date", "total_amount", "status"] = "order_date"
    sort_dir: Literal["asc", "desc"] = "desc"
