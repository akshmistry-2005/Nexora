from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.db.session import get_db
from app.repositories.customer import customer_repo
from app.repositories.organization import organization_repo
from app.schemas.common import PaginatedResponse, PaginationParams, StandardResponse
from app.schemas.customer import CustomerFilterParams, CustomerRead

router = APIRouter(tags=["Customers"])


@router.get(
    "/customers",
    response_model=PaginatedResponse[CustomerRead],
    summary="List and filter customers (paginated)",
)
def list_customers(
    pagination: PaginationParams = Depends(),
    filters: CustomerFilterParams = Depends(),
    session: Session = Depends(get_db),
) -> PaginatedResponse[CustomerRead]:
    org = organization_repo.get_first_org(session)
    if not org:
        raise NotFoundError("Organization not found.")

    items, meta = customer_repo.filter_customers(
        session=session,
        organization_id=org.id,
        filters=filters,
        page=pagination.page,
        page_size=pagination.page_size,
    )
    return PaginatedResponse(
        data=[CustomerRead.model_validate(c) for c in items],
        meta=meta,
    )


@router.get(
    "/customers/{customer_id}",
    response_model=StandardResponse[CustomerRead],
    summary="Get single customer by ID",
)
def get_customer(
    customer_id: int,
    session: Session = Depends(get_db),
) -> StandardResponse[CustomerRead]:
    c = customer_repo.get_by_id(session, customer_id)
    if not c:
        raise NotFoundError(f"Customer with ID {customer_id} not found.")
    return StandardResponse(data=CustomerRead.model_validate(c))
