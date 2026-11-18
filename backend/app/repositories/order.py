from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.order import Order
from app.repositories.base import BaseRepository
from app.schemas.common import PaginationMeta
from app.schemas.order import OrderFilterParams


class OrderRepository(BaseRepository[Order]):
    def __init__(self) -> None:
        super().__init__(Order)

    def get_order_with_items(self, session: Session, order_id: int) -> Order | None:
        stmt = select(Order).options(selectinload(Order.items)).where(Order.id == order_id)
        return session.scalar(stmt)

    def filter_orders(
        self,
        session: Session,
        organization_id: int,
        filters: OrderFilterParams,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Order], PaginationMeta]:
        stmt = select(Order).where(Order.organization_id == organization_id)

        if filters.status is not None:
            stmt = stmt.where(Order.status == filters.status)

        if filters.region_id is not None:
            stmt = stmt.where(Order.region_id == filters.region_id)

        if filters.sales_channel is not None:
            stmt = stmt.where(Order.sales_channel == filters.sales_channel)

        if filters.customer_id is not None:
            stmt = stmt.where(Order.customer_id == filters.customer_id)

        if filters.start_date is not None:
            stmt = stmt.where(Order.order_date >= filters.start_date)

        if filters.end_date is not None:
            stmt = stmt.where(Order.order_date <= filters.end_date)

        sort_col = getattr(Order, filters.sort_by, Order.order_date)
        return self.paginate(
            session=session,
            stmt=stmt,
            page=page,
            page_size=page_size,
            sort_column=sort_col,
            sort_dir=filters.sort_dir,
        )


order_repo = OrderRepository()
