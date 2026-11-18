from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class CustomerRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    organization_id: int
    region_id: int
    customer_code: str
    company_name: str | None
    contact_name: str
    email: str
    phone: str | None
    customer_type: str
    acquisition_channel: str
    signup_date: date
    is_active: bool
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
