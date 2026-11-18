from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.order import OrderItem, OrderReturn
    from app.models.organization import Region
    from app.models.procurement import PurchaseOrder


class Supplier(Base, TimestampMixin):
    """Component and finished goods vendor."""

    __tablename__ = "suppliers"
    __table_args__ = (
        UniqueConstraint("organization_id", "supplier_code", name="uq_supplier_org_code"),
        CheckConstraint("lead_time_days_sla >= 1", name="ck_supplier_lead_time"),
    )

    organization_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    region_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("regions.id", ondelete="SET NULL"), nullable=True, index=True
    )
    supplier_code: Mapped[str] = mapped_column(String(30), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    contact_email: Mapped[str | None] = mapped_column(String(120), nullable=True)
    lead_time_days_sla: Mapped[int] = mapped_column(Integer, default=14, nullable=False)
    quality_rating: Mapped[Decimal | None] = mapped_column(Numeric(3, 2), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    purchase_orders: Mapped[list["PurchaseOrder"]] = relationship(back_populates="supplier")


class Category(Base, TimestampMixin):
    """Product catalog category."""

    __tablename__ = "categories"
    __table_args__ = (
        UniqueConstraint("organization_id", "code", name="uq_category_org_code"),
        UniqueConstraint("organization_id", "name", name="uq_category_org_name"),
    )

    organization_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    code: Mapped[str] = mapped_column(String(30), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    products: Mapped[list["Product"]] = relationship(back_populates="category")


class Product(Base, TimestampMixin):
    """Commercial product SKU."""

    __tablename__ = "products"
    __table_args__ = (
        UniqueConstraint("organization_id", "sku", name="uq_product_org_sku"),
        CheckConstraint("unit_cost >= 0.00", name="ck_product_unit_cost"),
        CheckConstraint("unit_price >= 0.00", name="ck_product_unit_price"),
    )

    organization_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    category_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("categories.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    sku: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    unit_cost: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    reorder_point: Mapped[int] = mapped_column(Integer, default=50, nullable=False)
    target_stock: Mapped[int] = mapped_column(Integer, default=250, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    category: Mapped["Category"] = relationship(back_populates="products")
    inventory_records: Mapped[list["Inventory"]] = relationship(back_populates="product")
    order_items: Mapped[list["OrderItem"]] = relationship(back_populates="product")
    order_returns: Mapped[list["OrderReturn"]] = relationship(back_populates="product")


class Warehouse(Base, TimestampMixin):
    """Physical distribution facility."""

    __tablename__ = "warehouses"
    __table_args__ = (
        UniqueConstraint("organization_id", "warehouse_code", name="uq_warehouse_org_code"),
        CheckConstraint("capacity_units >= 0", name="ck_warehouse_capacity"),
    )

    organization_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    region_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("regions.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    warehouse_code: Mapped[str] = mapped_column(String(30), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    capacity_units: Mapped[int] = mapped_column(Integer, default=50000, nullable=False)

    region: Mapped["Region"] = relationship()
    inventory_records: Mapped[list["Inventory"]] = relationship(back_populates="warehouse")
    purchase_orders: Mapped[list["PurchaseOrder"]] = relationship(back_populates="warehouse")


class Inventory(Base):
    """Warehouse inventory level for a SKU."""

    __tablename__ = "inventory"
    __table_args__ = (
        UniqueConstraint("warehouse_id", "product_id", name="uq_inventory_warehouse_product"),
        CheckConstraint("quantity_on_hand >= 0", name="ck_inventory_on_hand"),
        CheckConstraint("quantity_reserved >= 0", name="ck_inventory_reserved"),
    )

    organization_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    warehouse_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("warehouses.id", ondelete="CASCADE"), nullable=False, index=True
    )
    product_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True
    )
    quantity_on_hand: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    quantity_reserved: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    reorder_point: Mapped[int] = mapped_column(Integer, default=50, nullable=False)
    last_restocked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    warehouse: Mapped["Warehouse"] = relationship(back_populates="inventory_records")
    product: Mapped["Product"] = relationship(back_populates="inventory_records")


class StockMovement(Base, TimestampMixin):
    """Audit ledger of inventory adjustments, receipts, and shipments."""

    __tablename__ = "stock_movements"

    organization_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    warehouse_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("warehouses.id", ondelete="CASCADE"), nullable=False, index=True
    )
    product_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # movement_type: receipt, shipment, adjustment, return
    movement_type: Mapped[str] = mapped_column(String(30), nullable=False)
    # quantity_delta: positive or negative
    quantity_delta: Mapped[int] = mapped_column(Integer, nullable=False)
    # reference_id: PO or Order number
    reference_id: Mapped[str | None] = mapped_column(String(80), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
