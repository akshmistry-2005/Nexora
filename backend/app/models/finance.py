from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    CheckConstraint,
    Date,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.organization import Department, Region


class Expense(Base, TimestampMixin):
    """Departmental operating expense (OpEx) transaction."""

    __tablename__ = "expenses"
    __table_args__ = (
        CheckConstraint("amount > 0.00", name="ck_expense_amount"),
        CheckConstraint(
            "category IN ('Payroll', 'Marketing', 'Logistics', "
            "'Facilities', 'IT & SaaS', 'General Admin')",
            name="ck_expense_category",
        ),
    )

    organization_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    department_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("departments.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    region_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("regions.id", ondelete="SET NULL"), nullable=True, index=True
    )
    expense_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    description: Mapped[str | None] = mapped_column(String(250), nullable=True)

    department: Mapped["Department"] = relationship(back_populates="expenses")
    region: Mapped[Optional["Region"]] = relationship()


class Budget(Base, TimestampMixin):
    """Periodic target financial allocation."""

    __tablename__ = "budgets"
    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "department_id",
            "fiscal_year",
            "fiscal_quarter",
            "metric_target",
            name="uq_budget_org_dept_quarter",
        ),
        CheckConstraint("budgeted_amount >= 0.00", name="ck_budget_amount"),
        CheckConstraint("fiscal_quarter BETWEEN 1 AND 4", name="ck_budget_quarter"),
    )

    organization_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    department_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("departments.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    region_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("regions.id", ondelete="SET NULL"), nullable=True, index=True
    )
    fiscal_year: Mapped[int] = mapped_column(Integer, nullable=False)
    fiscal_quarter: Mapped[int] = mapped_column(Integer, nullable=False)
    metric_target: Mapped[str] = mapped_column(String(50), nullable=False)
    budgeted_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)

    department: Mapped["Department"] = relationship(back_populates="budgets")
    region: Mapped[Optional["Region"]] = relationship()
