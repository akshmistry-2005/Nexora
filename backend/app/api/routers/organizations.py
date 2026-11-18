from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.db.session import get_db
from app.repositories.organization import organization_repo
from app.schemas.common import StandardResponse
from app.schemas.organization import DepartmentRead, EmployeeRead, OrganizationRead, RegionRead

router = APIRouter(tags=["Organizations & Reference Data"])


@router.get(
    "/organizations/current",
    response_model=StandardResponse[OrganizationRead],
    summary="Get current demonstration organization",
)
def get_current_organization(
    session: Session = Depends(get_db),
) -> StandardResponse[OrganizationRead]:
    org = organization_repo.get_first_org(session)
    if not org:
        raise NotFoundError("Organization not found. Database must be seeded.")
    return StandardResponse(data=OrganizationRead.model_validate(org))


@router.get(
    "/departments",
    response_model=StandardResponse[list[DepartmentRead]],
    summary="List organization departments",
)
def list_departments(session: Session = Depends(get_db)) -> StandardResponse[list[DepartmentRead]]:
    org = organization_repo.get_first_org(session)
    if not org:
        raise NotFoundError("Organization not found.")
    depts = organization_repo.list_departments(session, org.id)
    return StandardResponse(data=[DepartmentRead.model_validate(d) for d in depts])


@router.get(
    "/regions",
    response_model=StandardResponse[list[RegionRead]],
    summary="List organization geographic regions",
)
def list_regions(session: Session = Depends(get_db)) -> StandardResponse[list[RegionRead]]:
    org = organization_repo.get_first_org(session)
    if not org:
        raise NotFoundError("Organization not found.")
    regions = organization_repo.list_regions(session, org.id)
    return StandardResponse(data=[RegionRead.model_validate(r) for r in regions])


@router.get(
    "/employees",
    response_model=StandardResponse[list[EmployeeRead]],
    summary="List organization internal personnel",
)
def list_employees(session: Session = Depends(get_db)) -> StandardResponse[list[EmployeeRead]]:
    org = organization_repo.get_first_org(session)
    if not org:
        raise NotFoundError("Organization not found.")
    employees = organization_repo.list_employees(session, org.id)
    return StandardResponse(data=[EmployeeRead.model_validate(e) for e in employees])
