from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    Date,
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
    from app.models.product import Supplier, Warehouse


class PurchaseOrder(Base, TimestampMixin):
    """Inbound supplier procurement order."""

    __tablename__ = "purchase_orders"
    __table_args__ = (
        UniqueConstraint("organization_id", "po_number", name="uq_po_org_number"),
        CheckConstraint("ordered_units > 0", name="ck_po_ordered_units"),
        CheckConstraint("received_units >= 0", name="ck_po_received_units"),
        CheckConstraint("defective_units >= 0", name="ck_po_defective_units"),
        CheckConstraint("total_cost >= 0.00", name="ck_po_total_cost"),
    )

    organization_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    supplier_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("suppliers.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    warehouse_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("warehouses.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    po_number: Mapped[str] = mapped_column(String(40), nullable=False)
    order_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expected_delivery_date: Mapped[date] = mapped_column(Date, nullable=False)
    actual_delivery_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    ordered_units: Mapped[int] = mapped_column(Integer, nullable=False)
    received_units: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    defective_units: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_cost: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    status: Mapped[str] = mapped_column(String(25), default="issued", nullable=False)

    supplier: Mapped["Supplier"] = relationship(back_populates="purchase_orders")
    warehouse: Mapped["Warehouse"] = relationship(back_populates="purchase_orders")
