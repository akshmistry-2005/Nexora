from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class CategoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    organization_id: int
    name: str
    code: str
    description: str | None


class ProductRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    organization_id: int
    category_id: int
    sku: str
    name: str
    unit_cost: Decimal
    unit_price: Decimal
    reorder_point: int
    target_stock: int
    is_active: bool
    created_at: datetime


class ProductFilterParams(BaseModel):
    """Query filters for products endpoint."""

    category_id: int | None = Field(default=None, description="Filter by category ID")
    is_active: bool | None = Field(default=None, description="Filter active status")
    search: str | None = Field(default=None, description="Search by product name or SKU")
    sort_by: Literal["id", "name", "sku", "unit_price", "unit_cost", "created_at"] = "id"
    sort_dir: Literal["asc", "desc"] = "asc"


class WarehouseRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    organization_id: int
    region_id: int
    warehouse_code: str
    name: str
    capacity_units: int


class InventoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    organization_id: int
    warehouse_id: int
    product_id: int
    quantity_on_hand: int
    quantity_reserved: int
    reorder_point: int
    last_restocked_at: datetime | None
    updated_at: datetime
