from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.organization import Department, Employee, Organization, Region
from app.repositories.base import BaseRepository


class OrganizationRepository(BaseRepository[Organization]):
    def __init__(self) -> None:
        super().__init__(Organization)

    def get_first_org(self, session: Session) -> Organization | None:
        return session.scalar(select(Organization).limit(1))

    def list_departments(self, session: Session, organization_id: int) -> list[Department]:
        stmt = (
            select(Department)
            .where(Department.organization_id == organization_id)
            .order_by(Department.id)
        )
        return list(session.scalars(stmt).all())

    def list_regions(self, session: Session, organization_id: int) -> list[Region]:
        stmt = select(Region).where(Region.organization_id == organization_id).order_by(Region.id)
        return list(session.scalars(stmt).all())

    def list_employees(self, session: Session, organization_id: int) -> list[Employee]:
        stmt = (
            select(Employee)
            .where(Employee.organization_id == organization_id)
            .order_by(Employee.id)
        )
        return list(session.scalars(stmt).all())


organization_repo = OrganizationRepository()
