from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.customer import Customer
    from app.models.marketing import Campaign
    from app.models.organization import Employee, Region
    from app.models.product import Product, Warehouse


class Order(Base, TimestampMixin):
    """Sales order header record."""

    __tablename__ = "orders"
    __table_args__ = (
        UniqueConstraint("organization_id", "order_number", name="uq_order_org_number"),
        CheckConstraint(
            "status IN ('pending', 'processing', 'shipped', 'completed', 'cancelled', 'returned')",
            name="ck_order_status",
        ),
        CheckConstraint("subtotal_amount >= 0.00", name="ck_order_subtotal"),
        CheckConstraint("discount_amount >= 0.00", name="ck_order_discount"),
        CheckConstraint("tax_amount >= 0.00", name="ck_order_tax"),
        CheckConstraint("shipping_amount >= 0.00", name="ck_order_shipping"),
        CheckConstraint("total_amount >= 0.00", name="ck_order_total"),
    )

    organization_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    order_number: Mapped[str] = mapped_column(String(40), nullable=False)
    customer_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("customers.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    sales_rep_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("employees.id", ondelete="SET NULL"), nullable=True, index=True
    )
    region_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("regions.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    warehouse_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("warehouses.id", ondelete="SET NULL"), nullable=True, index=True
    )
    campaign_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("campaigns.id", ondelete="SET NULL"), nullable=True, index=True
    )
    order_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(String(25), default="pending", nullable=False, index=True)
    sales_channel: Mapped[str] = mapped_column(String(30), default="Direct", nullable=False)
    subtotal_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0.00, nullable=False)
    discount_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0.00, nullable=False)
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0.00, nullable=False)
    shipping_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0.00, nullable=False)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0.00, nullable=False)
    promised_delivery_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    shipped_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancellation_reason: Mapped[str | None] = mapped_column(String(200), nullable=True)

    customer: Mapped["Customer"] = relationship(back_populates="orders")
    sales_rep: Mapped[Optional["Employee"]] = relationship(back_populates="orders_assisted")
    region: Mapped["Region"] = relationship()
    warehouse: Mapped[Optional["Warehouse"]] = relationship()
    campaign: Mapped[Optional["Campaign"]] = relationship(back_populates="orders")
    items: Mapped[list["OrderItem"]] = relationship(
        back_populates="order", cascade="all, delete-orphan"
    )
    payments: Mapped[list["Payment"]] = relationship(
        back_populates="order", cascade="all, delete-orphan"
    )
    returns: Mapped[list["OrderReturn"]] = relationship(
        back_populates="order", cascade="all, delete-orphan"
    )


class OrderItem(Base):
    """Line item in a sales order."""

    __tablename__ = "order_items"
    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_order_item_qty"),
        CheckConstraint("unit_cost >= 0.00", name="ck_order_item_cost"),
        CheckConstraint("unit_price >= 0.00", name="ck_order_item_price"),
        CheckConstraint("discount_amount >= 0.00", name="ck_order_item_discount"),
        CheckConstraint("total_line_amount >= 0.00", name="ck_order_item_total"),
    )

    organization_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    order_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True
    )
    product_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("products.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_cost: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    discount_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0.00, nullable=False)
    total_line_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)

    order: Mapped["Order"] = relationship(back_populates="items")
    product: Mapped["Product"] = relationship(back_populates="order_items")


class Payment(Base, TimestampMixin):
    """Settlement payment record."""

    __tablename__ = "payments"
    __table_args__ = (
        UniqueConstraint("organization_id", "payment_reference", name="uq_payment_org_ref"),
        CheckConstraint("amount > 0.00", name="ck_payment_amount"),
    )

    organization_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    order_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("orders.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    payment_reference: Mapped[str] = mapped_column(String(60), nullable=False)
    payment_method: Mapped[str] = mapped_column(String(30), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="completed", nullable=False)
    payment_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    order: Mapped["Order"] = relationship(back_populates="payments")


class OrderReturn(Base, TimestampMixin):
    """Reverse logistics case record."""

    __tablename__ = "order_returns"
    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_return_qty"),
        CheckConstraint("refund_amount >= 0.00", name="ck_return_refund"),
    )

    organization_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    order_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("orders.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    product_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("products.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    return_reason: Mapped[str] = mapped_column(String(150), nullable=False)
    refund_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0.00, nullable=False)
    return_status: Mapped[str] = mapped_column(String(20), default="approved", nullable=False)
    return_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    order: Mapped["Order"] = relationship(back_populates="returns")
    product: Mapped["Product"] = relationship(back_populates="order_returns")
