from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.db.session import get_db
from app.permissions.dependencies import AuthenticatedUser, require_permission
from app.repositories.organization import organization_repo
from app.repositories.product import product_repo
from app.schemas.common import PaginatedResponse, PaginationParams, StandardResponse
from app.schemas.product import CategoryRead, ProductFilterParams, ProductRead

router = APIRouter(tags=["Products & Catalog"])


@router.get(
    "/categories",
    response_model=StandardResponse[list[CategoryRead]],
    summary="List product catalog categories",
)
def list_categories(
    session: Session = Depends(get_db),
    _: AuthenticatedUser = Depends(require_permission("sales.view")),
) -> StandardResponse[list[CategoryRead]]:
    org = organization_repo.get_first_org(session)
    if not org:
        raise NotFoundError("Organization not found.")
    cats = product_repo.list_categories(session, org.id)
    return StandardResponse(data=[CategoryRead.model_validate(c) for c in cats])


@router.get(
    "/products",
    response_model=PaginatedResponse[ProductRead],
    summary="List and filter catalog products (paginated)",
)
def list_products(
    pagination: PaginationParams = Depends(),
    filters: ProductFilterParams = Depends(),
    session: Session = Depends(get_db),
    _: AuthenticatedUser = Depends(require_permission("sales.view")),
) -> PaginatedResponse[ProductRead]:
    org = organization_repo.get_first_org(session)
    if not org:
        raise NotFoundError("Organization not found.")

    items, meta = product_repo.filter_products(
        session=session,
        organization_id=org.id,
        filters=filters,
        page=pagination.page,
        page_size=pagination.page_size,
    )
    return PaginatedResponse(
        data=[ProductRead.model_validate(p) for p in items],
        meta=meta,
    )


@router.get(
    "/products/{product_id}",
    response_model=StandardResponse[ProductRead],
    summary="Get single product by ID",
)
def get_product(
    product_id: int,
    session: Session = Depends(get_db),
    _: AuthenticatedUser = Depends(require_permission("sales.view")),
) -> StandardResponse[ProductRead]:
    p = product_repo.get_by_id(session, product_id)
    if not p:
        raise NotFoundError(f"Product with ID {product_id} not found.")
    return StandardResponse(data=ProductRead.model_validate(p))
