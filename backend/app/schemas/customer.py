from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class CustomerBase(BaseModel):
    region_id: int = Field(..., description="Geographic territory region ID")
    customer_code: str = Field(..., max_length=40, description="Unique customer code")
    company_name: str | None = Field(default=None, max_length=150)
    contact_name: str = Field(..., max_length=100)
    email: str = Field(..., max_length=120)
    phone: str | None = Field(default=None, max_length=40)
    customer_type: Literal["B2B", "B2C", "Enterprise"] = Field(default="B2B")
    acquisition_channel: str = Field(..., max_length=50)
    signup_date: date = Field(default_factory=date.today)
    is_active: bool = Field(default=True)


class CustomerCreate(CustomerBase):
    """Payload to create a customer record (Owner-only)."""

    pass


class CustomerUpdate(BaseModel):
    """Payload to update a customer record (Owner-only)."""

    company_name: str | None = None
    contact_name: str | None = None
    phone: str | None = None
    customer_type: Literal["B2B", "B2C", "Enterprise"] | None = None
    is_active: bool | None = None


class CustomerRead(CustomerBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    organization_id: int
    created_at: datetime


class CustomerFilterParams(BaseModel):
    """Query filters for customers endpoint."""

    region_id: int | None = Field(default=None, description="Filter by geographic region ID")
    customer_type: Literal["B2B", "B2C", "Enterprise"] | None = Field(
        default=None, description="Filter customer segment"
    )
    is_active: bool | None = Field(default=None, description="Filter active status")
    search: str | None = Field(default=None, description="Search by name, company, email or code")
    sort_by: Literal["id", "customer_code", "contact_name", "signup_date", "created_at"] = "id"
    sort_dir: Literal["asc", "desc"] = "asc"
