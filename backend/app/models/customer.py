from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, CheckConstraint, Date, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.order import Order
    from app.models.organization import Region


class Customer(Base, TimestampMixin):
    """Business and retail customer record."""

    __tablename__ = "customers"
    __table_args__ = (
        UniqueConstraint("organization_id", "customer_code", name="uq_customer_org_code"),
        UniqueConstraint("organization_id", "email", name="uq_customer_org_email"),
        CheckConstraint("customer_type IN ('B2B', 'B2C', 'Enterprise')", name="ck_customer_type"),
    )

    organization_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    region_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("regions.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    customer_code: Mapped[str] = mapped_column(String(40), nullable=False)
    company_name: Mapped[str | None] = mapped_column(String(150), nullable=True)
    contact_name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(120), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(40), nullable=True)
    customer_type: Mapped[str] = mapped_column(String(20), default="B2B", nullable=False)
    acquisition_channel: Mapped[str] = mapped_column(String(50), nullable=False)
    signup_date: Mapped[date] = mapped_column(Date, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    region: Mapped["Region"] = relationship()
    orders: Mapped[list["Order"]] = relationship(back_populates="customer")
