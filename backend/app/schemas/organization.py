from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class OrganizationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    code: str
    base_currency: str
    timezone: str
    created_at: datetime


class DepartmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    organization_id: int
    name: str
    code: str
    created_at: datetime


class RegionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    organization_id: int
    name: str
    code: str
    currency: str
    created_at: datetime


class EmployeeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    organization_id: int
    department_id: int
    region_id: int | None
    employee_code: str
    first_name: str
    last_name: str
    email: str
    role_title: str
    hire_date: date
    is_active: bool
