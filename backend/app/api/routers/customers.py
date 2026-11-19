from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.db.session import get_db
from app.models.customer import Customer
from app.permissions.dependencies import AuthenticatedUser, require_permission
from app.repositories.customer import customer_repo
from app.repositories.organization import organization_repo
from app.schemas.common import PaginatedResponse, PaginationParams, StandardResponse
from app.schemas.customer import CustomerCreate, CustomerFilterParams, CustomerRead, CustomerUpdate

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
    _: AuthenticatedUser = Depends(require_permission("customer.view")),
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
    _: AuthenticatedUser = Depends(require_permission("customer.view")),
) -> StandardResponse[CustomerRead]:
    c = customer_repo.get_by_id(session, customer_id)
    if not c:
        raise NotFoundError(f"Customer with ID {customer_id} not found.")
    return StandardResponse(data=CustomerRead.model_validate(c))


@router.post(
    "/customers",
    response_model=StandardResponse[CustomerRead],
    status_code=status.HTTP_201_CREATED,
    summary="Create a new customer (Owner-only mutation)",
)
def create_customer(
    payload: CustomerCreate,
    session: Session = Depends(get_db),
    _: AuthenticatedUser = Depends(require_permission("customer.create")),
) -> StandardResponse[CustomerRead]:
    org = organization_repo.get_first_org(session)
    if not org:
        raise NotFoundError("Organization not found.")

    new_cust = Customer(
        organization_id=org.id,
        region_id=payload.region_id,
        customer_code=payload.customer_code,
        company_name=payload.company_name,
        contact_name=payload.contact_name,
        email=payload.email,
        phone=payload.phone,
        customer_type=payload.customer_type,
        acquisition_channel=payload.acquisition_channel,
        signup_date=payload.signup_date,
        is_active=payload.is_active,
    )
    session.add(new_cust)
    session.commit()
    session.refresh(new_cust)
    return StandardResponse(data=CustomerRead.model_validate(new_cust))


@router.put(
    "/customers/{customer_id}",
    response_model=StandardResponse[CustomerRead],
    summary="Update customer attributes (Owner-only mutation)",
)
def update_customer(
    customer_id: int,
    payload: CustomerUpdate,
    session: Session = Depends(get_db),
    _: AuthenticatedUser = Depends(require_permission("customer.update")),
) -> StandardResponse[CustomerRead]:
    cust = customer_repo.get_by_id(session, customer_id)
    if not cust:
        raise NotFoundError(f"Customer with ID {customer_id} not found.")

    update_data = payload.model_dump(exclude_unset=True)
    for field, val in update_data.items():
        setattr(cust, field, val)

    session.commit()
    session.refresh(cust)
    return StandardResponse(data=CustomerRead.model_validate(cust))


@router.delete(
    "/customers/{customer_id}",
    response_model=StandardResponse[dict[str, str]],
    summary="Delete customer record (Owner-only mutation)",
)
def delete_customer(
    customer_id: int,
    session: Session = Depends(get_db),
    _: AuthenticatedUser = Depends(require_permission("customer.delete")),
) -> StandardResponse[dict[str, str]]:
    cust = customer_repo.get_by_id(session, customer_id)
    if not cust:
        raise NotFoundError(f"Customer with ID {customer_id} not found.")

    session.delete(cust)
    session.commit()
    return StandardResponse(data={"message": f"Customer {customer_id} successfully deleted."})
