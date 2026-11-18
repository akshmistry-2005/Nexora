from datetime import date
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, Date, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.finance import Budget, Expense
    from app.models.order import Order


class Organization(Base, TimestampMixin):
    """Fictional enterprise boundary."""

    __tablename__ = "organizations"

    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    base_currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    timezone: Mapped[str] = mapped_column(String(50), default="UTC", nullable=False)

    departments: Mapped[list["Department"]] = relationship(
        back_populates="organization", cascade="all, delete-orphan"
    )
    regions: Mapped[list["Region"]] = relationship(
        back_populates="organization", cascade="all, delete-orphan"
    )


class Department(Base, TimestampMixin):
    """Department division within an organization."""

    __tablename__ = "departments"
    __table_args__ = (
        UniqueConstraint("organization_id", "code", name="uq_department_org_code"),
        UniqueConstraint("organization_id", "name", name="uq_department_org_name"),
    )

    organization_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    code: Mapped[str] = mapped_column(String(20), nullable=False)

    organization: Mapped["Organization"] = relationship(back_populates="departments")
    employees: Mapped[list["Employee"]] = relationship(back_populates="department")
    expenses: Mapped[list["Expense"]] = relationship(back_populates="department")
    budgets: Mapped[list["Budget"]] = relationship(back_populates="department")


class Region(Base, TimestampMixin):
    """Geographic sales or operations territory."""

    __tablename__ = "regions"
    __table_args__ = (UniqueConstraint("organization_id", "code", name="uq_region_org_code"),)

    organization_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    code: Mapped[str] = mapped_column(String(20), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)

    organization: Mapped["Organization"] = relationship(back_populates="regions")
    employees: Mapped[list["Employee"]] = relationship(back_populates="region")


class Employee(Base, TimestampMixin):
    """Internal employee / representative."""

    __tablename__ = "employees"
    __table_args__ = (
        UniqueConstraint("organization_id", "employee_code", name="uq_employee_org_code"),
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
    employee_code: Mapped[str] = mapped_column(String(30), nullable=False)
    first_name: Mapped[str] = mapped_column(String(50), nullable=False)
    last_name: Mapped[str] = mapped_column(String(50), nullable=False)
    email: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    role_title: Mapped[str] = mapped_column(String(100), nullable=False)
    hire_date: Mapped[date] = mapped_column(Date, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    department: Mapped["Department"] = relationship(back_populates="employees")
    region: Mapped[Optional["Region"]] = relationship(back_populates="employees")
    orders_assisted: Mapped[list["Order"]] = relationship(back_populates="sales_rep")
