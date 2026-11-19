from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.permissions.dependencies import AuthenticatedUser, require_permission
from app.schemas.analytics import (
    AnalyticsFilterParams,
    AnalyticsLedgerItem,
    CustomerAnalyticsResponse,
    FinanceAnalyticsResponse,
    InventoryAnalyticsResponse,
    MarketingAnalyticsResponse,
    OperationsAnalyticsResponse,
    OverviewAnalyticsResponse,
    SalesAnalyticsResponse,
    SupplierAnalyticsResponse,
)
from app.schemas.common import PaginatedResponse, PaginationMeta, StandardResponse
from app.services.analytics import analytics_service

router = APIRouter(prefix="/analytics", tags=["Core Business Intelligence"])


@router.get(
    "/overview",
    response_model=StandardResponse[OverviewAnalyticsResponse],
    summary="Get Overview Dashboard analytics",
)
def get_overview_analytics(
    start_date: str | None = Query(default=None),
    end_date: str | None = Query(default=None),
    region_id: int | None = Query(default=None),
    session: Session = Depends(get_db),
    _: AuthenticatedUser = Depends(require_permission("dashboard.view")),
) -> StandardResponse[OverviewAnalyticsResponse]:
    filters = AnalyticsFilterParams(start_date=start_date, end_date=end_date, region_id=region_id)
    data = analytics_service.get_overview_analytics(session, filters)
    return StandardResponse(data=data)


@router.get(
    "/sales",
    response_model=StandardResponse[SalesAnalyticsResponse],
    summary="Get Sales Intelligence analytics",
)
def get_sales_analytics(
    start_date: str | None = Query(default=None),
    end_date: str | None = Query(default=None),
    region_id: int | None = Query(default=None),
    sales_channel: str | None = Query(default=None),
    session: Session = Depends(get_db),
    _: AuthenticatedUser = Depends(require_permission("sales.view")),
) -> StandardResponse[SalesAnalyticsResponse]:
    filters = AnalyticsFilterParams(
        start_date=start_date,
        end_date=end_date,
        region_id=region_id,
        sales_channel=sales_channel,
    )
    data = analytics_service.get_sales_analytics(session, filters)
    return StandardResponse(data=data)


@router.get(
    "/customers",
    response_model=StandardResponse[CustomerAnalyticsResponse],
    summary="Get Customer Intelligence analytics",
)
def get_customer_analytics(
    start_date: str | None = Query(default=None),
    end_date: str | None = Query(default=None),
    region_id: int | None = Query(default=None),
    session: Session = Depends(get_db),
    _: AuthenticatedUser = Depends(require_permission("customer.view")),
) -> StandardResponse[CustomerAnalyticsResponse]:
    filters = AnalyticsFilterParams(start_date=start_date, end_date=end_date, region_id=region_id)
    data = analytics_service.get_customer_analytics(session, filters)
    return StandardResponse(data=data)


@router.get(
    "/marketing",
    response_model=StandardResponse[MarketingAnalyticsResponse],
    summary="Get Marketing Intelligence analytics",
)
def get_marketing_analytics(
    start_date: str | None = Query(default=None),
    end_date: str | None = Query(default=None),
    session: Session = Depends(get_db),
    _: AuthenticatedUser = Depends(require_permission("marketing.view")),
) -> StandardResponse[MarketingAnalyticsResponse]:
    filters = AnalyticsFilterParams(start_date=start_date, end_date=end_date)
    data = analytics_service.get_marketing_analytics(session, filters)
    return StandardResponse(data=data)


@router.get(
    "/finance",
    response_model=StandardResponse[FinanceAnalyticsResponse],
    summary="Get Financial Intelligence analytics",
)
def get_finance_analytics(
    start_date: str | None = Query(default=None),
    end_date: str | None = Query(default=None),
    region_id: int | None = Query(default=None),
    session: Session = Depends(get_db),
    _: AuthenticatedUser = Depends(require_permission("finance.view")),
) -> StandardResponse[FinanceAnalyticsResponse]:
    filters = AnalyticsFilterParams(start_date=start_date, end_date=end_date, region_id=region_id)
    data = analytics_service.get_finance_analytics(session, filters)
    return StandardResponse(data=data)


@router.get(
    "/inventory",
    response_model=StandardResponse[InventoryAnalyticsResponse],
    summary="Get Inventory Intelligence analytics",
)
def get_inventory_analytics(
    session: Session = Depends(get_db),
    _: AuthenticatedUser = Depends(require_permission("inventory.view")),
) -> StandardResponse[InventoryAnalyticsResponse]:
    data = analytics_service.get_inventory_analytics(session)
    return StandardResponse(data=data)


@router.get(
    "/operations",
    response_model=StandardResponse[OperationsAnalyticsResponse],
    summary="Get Operations Intelligence analytics",
)
def get_operations_analytics(
    start_date: str | None = Query(default=None),
    end_date: str | None = Query(default=None),
    session: Session = Depends(get_db),
    _: AuthenticatedUser = Depends(require_permission("operations.view")),
) -> StandardResponse[OperationsAnalyticsResponse]:
    filters = AnalyticsFilterParams(start_date=start_date, end_date=end_date)
    data = analytics_service.get_operations_analytics(session, filters)
    return StandardResponse(data=data)


@router.get(
    "/suppliers",
    response_model=StandardResponse[SupplierAnalyticsResponse],
    summary="Get Supplier Intelligence analytics",
)
def get_supplier_analytics(
    session: Session = Depends(get_db),
    _: AuthenticatedUser = Depends(require_permission("supplier.view")),
) -> StandardResponse[SupplierAnalyticsResponse]:
    data = analytics_service.get_supplier_analytics(session)
    return StandardResponse(data=data)


@router.get(
    "/ledger",
    response_model=PaginatedResponse[AnalyticsLedgerItem],
    summary="Paginated drill-down transaction ledger",
)
def get_drill_down_ledger(
    start_date: str | None = Query(default=None),
    end_date: str | None = Query(default=None),
    region_id: int | None = Query(default=None),
    sales_channel: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=500),
    session: Session = Depends(get_db),
    _: AuthenticatedUser = Depends(require_permission("sales.view")),
) -> PaginatedResponse[AnalyticsLedgerItem]:
    filters = AnalyticsFilterParams(
        start_date=start_date,
        end_date=end_date,
        region_id=region_id,
        sales_channel=sales_channel,
    )
    offset = (page - 1) * page_size
    items, total_count = analytics_service.get_ledger(
        session, filters, limit=page_size, offset=offset
    )
    total_pages = (total_count + page_size - 1) // page_size if total_count > 0 else 1

    return PaginatedResponse(
        data=items,
        meta=PaginationMeta(
            page=page,
            page_size=page_size,
            total_items=total_count,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1,
        ),
    )
