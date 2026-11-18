import math
from typing import Any, Generic, TypeVar

from sqlalchemy import Select, asc, desc, func, select
from sqlalchemy.orm import Session

from app.models.base import Base
from app.schemas.common import PaginationMeta

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """Generic base repository providing paginated, filtered, and sorted queries."""

    def __init__(self, model: type[ModelType]):
        self.model = model

    def get_by_id(self, session: Session, item_id: int) -> ModelType | None:
        return session.get(self.model, item_id)

    def list_all(
        self,
        session: Session,
        organization_id: int | None = None,
        limit: int = 100,
    ) -> list[ModelType]:
        stmt = select(self.model)
        if organization_id is not None and hasattr(self.model, "organization_id"):
            stmt = stmt.where(self.model.organization_id == organization_id)  # type: ignore[attr-defined]
        return list(session.scalars(stmt.limit(limit)).all())

    def paginate(
        self,
        session: Session,
        stmt: Select[Any],
        page: int = 1,
        page_size: int = 20,
        sort_column: Any = None,
        sort_dir: str = "asc",
    ) -> tuple[list[ModelType], PaginationMeta]:
        """Execute a paginated query with total items and metadata."""
        # Count total matching rows
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_items: int = session.scalar(count_stmt) or 0

        total_pages = max(1, math.ceil(total_items / page_size))
        current_page = max(1, min(page, total_pages)) if total_items > 0 else 1

        # Apply sorting
        if sort_column is not None:
            order_func = desc if sort_dir.lower() == "desc" else asc
            stmt = stmt.order_by(order_func(sort_column))

        # Apply limit and offset
        offset = (current_page - 1) * page_size
        results: list[ModelType] = list(session.scalars(stmt.offset(offset).limit(page_size)).all())

        meta = PaginationMeta(
            page=current_page,
            page_size=page_size,
            total_items=total_items,
            total_pages=total_pages,
            has_next=current_page < total_pages,
            has_prev=current_page > 1,
        )
        return results, meta
