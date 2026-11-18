from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models.customer import Customer
from app.repositories.base import BaseRepository
from app.schemas.common import PaginationMeta
from app.schemas.customer import CustomerFilterParams


class CustomerRepository(BaseRepository[Customer]):
    def __init__(self) -> None:
        super().__init__(Customer)

    def filter_customers(
        self,
        session: Session,
        organization_id: int,
        filters: CustomerFilterParams,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Customer], PaginationMeta]:
        stmt = select(Customer).where(Customer.organization_id == organization_id)

        if filters.region_id is not None:
            stmt = stmt.where(Customer.region_id == filters.region_id)

        if filters.customer_type is not None:
            stmt = stmt.where(Customer.customer_type == filters.customer_type)

        if filters.is_active is not None:
            stmt = stmt.where(Customer.is_active == filters.is_active)

        if filters.search:
            search_term = f"%{filters.search.strip()}%"
            stmt = stmt.where(
                or_(
                    Customer.contact_name.ilike(search_term),
                    Customer.company_name.ilike(search_term),
                    Customer.email.ilike(search_term),
                    Customer.customer_code.ilike(search_term),
                )
            )

        sort_col = getattr(Customer, filters.sort_by, Customer.id)
        return self.paginate(
            session=session,
            stmt=stmt,
            page=page,
            page_size=page_size,
            sort_column=sort_col,
            sort_dir=filters.sort_dir,
        )


customer_repo = CustomerRepository()
