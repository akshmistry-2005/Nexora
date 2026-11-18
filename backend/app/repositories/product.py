from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models.product import Category, Product
from app.repositories.base import BaseRepository
from app.schemas.common import PaginationMeta
from app.schemas.product import ProductFilterParams


class ProductRepository(BaseRepository[Product]):
    def __init__(self) -> None:
        super().__init__(Product)

    def list_categories(self, session: Session, organization_id: int) -> list[Category]:
        stmt = (
            select(Category)
            .where(Category.organization_id == organization_id)
            .order_by(Category.id)
        )
        return list(session.scalars(stmt).all())

    def filter_products(
        self,
        session: Session,
        organization_id: int,
        filters: ProductFilterParams,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Product], PaginationMeta]:
        stmt = select(Product).where(Product.organization_id == organization_id)

        if filters.category_id is not None:
            stmt = stmt.where(Product.category_id == filters.category_id)

        if filters.is_active is not None:
            stmt = stmt.where(Product.is_active == filters.is_active)

        if filters.search:
            search_term = f"%{filters.search.strip()}%"
            stmt = stmt.where(
                or_(
                    Product.name.ilike(search_term),
                    Product.sku.ilike(search_term),
                )
            )

        sort_col = getattr(Product, filters.sort_by, Product.id)
        return self.paginate(
            session=session,
            stmt=stmt,
            page=page,
            page_size=page_size,
            sort_column=sort_col,
            sort_dir=filters.sort_dir,
        )


product_repo = ProductRepository()
