from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.db.session import get_db
from app.permissions.dependencies import AuthenticatedUser, require_permission
from app.repositories.order import order_repo
from app.repositories.organization import organization_repo
from app.schemas.common import PaginatedResponse, PaginationParams, StandardResponse
from app.schemas.order import OrderDetailRead, OrderFilterParams, OrderRead

router = APIRouter(tags=["Orders"])


@router.get(
    "/orders",
    response_model=PaginatedResponse[OrderRead],
    summary="List and filter sales orders (paginated)",
)
def list_orders(
    pagination: PaginationParams = Depends(),
    filters: OrderFilterParams = Depends(),
    session: Session = Depends(get_db),
    _: AuthenticatedUser = Depends(require_permission("sales.view")),
) -> PaginatedResponse[OrderRead]:
    org = organization_repo.get_first_org(session)
    if not org:
        raise NotFoundError("Organization not found.")

    items, meta = order_repo.filter_orders(
        session=session,
        organization_id=org.id,
        filters=filters,
        page=pagination.page,
        page_size=pagination.page_size,
    )
    return PaginatedResponse(
        data=[OrderRead.model_validate(o) for o in items],
        meta=meta,
    )


@router.get(
    "/orders/{order_id}",
    response_model=StandardResponse[OrderDetailRead],
    summary="Get single order with line items",
)
def get_order(
    order_id: int,
    session: Session = Depends(get_db),
    _: AuthenticatedUser = Depends(require_permission("sales.view")),
) -> StandardResponse[OrderDetailRead]:
    order = order_repo.get_order_with_items(session, order_id)
    if not order:
        raise NotFoundError(f"Order with ID {order_id} not found.")
    return StandardResponse(data=OrderDetailRead.model_validate(order))
