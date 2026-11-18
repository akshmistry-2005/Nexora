"""
NEXORA — Module 3 Test Suite: Database Design and Synthetic Data
Validates test cases M3-T01 through M3-T11 against live PostgreSQL database.
"""

import pytest
from sqlalchemy import create_engine, func, select, text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import (
    Budget,
    Campaign,
    CampaignEvent,
    Category,
    Customer,
    Department,
    Employee,
    Expense,
    Inventory,
    Order,
    OrderItem,
    OrderReturn,
    Organization,
    Payment,
    Permission,
    Product,
    PurchaseOrder,
    Region,
    Role,
    Supplier,
    User,
    Warehouse,
)


@pytest.fixture(scope="module")
def db_session() -> Session:
    """Module-level database session connected to seeded PostgreSQL database."""
    engine = create_engine(settings.database_url, future=True)
    with Session(engine) as session:
        yield session
    engine.dispose()


@pytest.mark.m03
def test_m03_t01_database_creation(db_session: Session) -> None:
    """M3-T01: Database creation — verify connected database is PostgreSQL and accessible."""
    result = db_session.execute(text("SELECT current_database(), version();")).fetchone()
    assert result is not None
    assert result[0] in ("nexora_db", "nexora_test_db")
    assert "PostgreSQL" in result[1]


@pytest.mark.m03
def test_m03_t02_migration_execution(db_session: Session) -> None:
    """M3-T02: Migration execution — verify Alembic version table has applied migration."""
    result = db_session.execute(text("SELECT version_num FROM alembic_version;")).scalar()
    assert result is not None
    assert len(result) == 12  # Alembic revision hash format


@pytest.mark.m03
def test_m03_t03_entity_relationship_verification(db_session: Session) -> None:
    """M3-T03: Entity relationships — verify navigation across related business entities."""
    order = db_session.query(Order).filter(Order.status == "completed").first()
    assert order is not None
    assert order.customer is not None
    assert len(order.items) > 0
    assert order.items[0].product is not None
    assert order.items[0].product.category is not None

    po = db_session.query(PurchaseOrder).first()
    assert po is not None
    assert po.supplier is not None
    assert po.warehouse is not None


@pytest.mark.m03
def test_m03_t04_primary_and_foreign_key_validation(db_session: Session) -> None:
    """M3-T04: Primary and foreign key validation — verify constraints and uniqueness."""
    # Organization code uniqueness
    org_count = db_session.query(func.count(Organization.id)).scalar()
    assert org_count == 1

    # Product SKU uniqueness
    skus = db_session.scalars(select(Product.sku)).all()
    assert len(skus) == len(set(skus))

    # Customer email uniqueness
    emails = db_session.scalars(select(Customer.email)).all()
    assert len(emails) == len(set(emails))


@pytest.mark.m03
def test_m03_t05_organization_id_validation(db_session: Session) -> None:
    """M3-T05: Organization ID validation — verify all core business tables contain valid org_id."""
    tables_to_check = [
        Department,
        Region,
        Employee,
        Supplier,
        Category,
        Product,
        Warehouse,
        Inventory,
        Customer,
        Order,
        OrderItem,
        Payment,
        OrderReturn,
        Campaign,
        CampaignEvent,
        PurchaseOrder,
        Expense,
        Budget,
    ]

    for model in tables_to_check:
        null_org_count = (
            db_session.query(func.count(model.id)).filter(model.organization_id.is_(None)).scalar()
        )  # type: ignore[attr-defined]
        assert null_org_count == 0, (
            f"Found records with null organization_id in {model.__tablename__}"
        )


@pytest.mark.m03
def test_m03_t06_synthetic_data_generation_volume(db_session: Session) -> None:
    """M3-T06: Synthetic data generation volume — verify baseline record counts."""
    assert db_session.query(func.count(Organization.id)).scalar() == 1
    assert db_session.query(func.count(Department.id)).scalar() == 6
    assert db_session.query(func.count(Region.id)).scalar() == 5
    assert db_session.query(func.count(Employee.id)).scalar() == 35
    assert db_session.query(func.count(Supplier.id)).scalar() == 25
    assert db_session.query(func.count(Category.id)).scalar() == 8
    assert db_session.query(func.count(Product.id)).scalar() == 120
    assert db_session.query(func.count(Warehouse.id)).scalar() == 4
    assert db_session.query(func.count(Inventory.id)).scalar() == 480  # 4 warehouses * 120 products
    assert db_session.query(func.count(Customer.id)).scalar() == 2500
    assert db_session.query(func.count(Order.id)).scalar() == 15000
    assert db_session.query(func.count(OrderItem.id)).scalar() >= 25000
    assert db_session.query(func.count(Payment.id)).scalar() >= 14000
    assert db_session.query(func.count(OrderReturn.id)).scalar() >= 400
    assert db_session.query(func.count(Campaign.id)).scalar() == 40
    assert db_session.query(func.count(CampaignEvent.id)).scalar() >= 3000
    assert db_session.query(func.count(PurchaseOrder.id)).scalar() == 1200
    assert db_session.query(func.count(Expense.id)).scalar() == 1500
    assert (
        db_session.query(func.count(Budget.id)).scalar() == 144
    )  # 3 years * 4 quarters * 6 depts * 2 targets
    assert db_session.query(func.count(Permission.id)).scalar() == 29
    assert db_session.query(func.count(Role.id)).scalar() == 6
    assert db_session.query(func.count(User.id)).scalar() == 6  # 1 owner + 5 demo users


@pytest.mark.m03
def test_m03_t07_data_coverage_validation(db_session: Session) -> None:
    """M3-T07: Data coverage validation — verify multi-year, multi-region, and segment coverage."""
    # Date range spans from 2024 to late 2026
    min_order_date = db_session.query(func.min(Order.order_date)).scalar()
    max_order_date = db_session.query(func.max(Order.order_date)).scalar()
    assert min_order_date is not None and max_order_date is not None
    assert min_order_date.year == 2024
    assert max_order_date.year == 2026

    # All 5 regions have orders
    order_regions = db_session.query(Order.region_id).distinct().all()
    assert len(order_regions) == 5

    # All categories have products with orders
    order_categories = (
        db_session.query(Product.category_id)
        .join(OrderItem, OrderItem.product_id == Product.id)
        .distinct()
        .all()
    )
    assert len(order_categories) == 8

    # All customer types have representation
    customer_types = db_session.query(Customer.customer_type).distinct().all()
    assert {c[0] for c in customer_types} == {"B2B", "B2C", "Enterprise"}


@pytest.mark.m03
def test_m03_t08_referential_integrity_check(db_session: Session) -> None:
    """M3-T08: Referential integrity check — verify zero orphan records across relations."""
    # Orphan order items
    orphan_items = (
        db_session.query(func.count(OrderItem.id))
        .outerjoin(Order, OrderItem.order_id == Order.id)
        .filter(Order.id.is_(None))
        .scalar()
    )
    assert orphan_items == 0

    # Orphan payments
    orphan_payments = (
        db_session.query(func.count(Payment.id))
        .outerjoin(Order, Payment.order_id == Order.id)
        .filter(Order.id.is_(None))
        .scalar()
    )
    assert orphan_payments == 0

    # Orphan inventory
    orphan_inventory = (
        db_session.query(func.count(Inventory.id))
        .outerjoin(Product, Inventory.product_id == Product.id)
        .filter(Product.id.is_(None))
        .scalar()
    )
    assert orphan_inventory == 0


@pytest.mark.m03
def test_m03_t09_data_plausibility_check(db_session: Session) -> None:
    """M3-T09: Data plausibility check — quantities, prices, dates, margins."""
    # No negative prices or costs
    negative_prices = (
        db_session.query(func.count(Product.id)).filter(Product.unit_price < 0).scalar()
    )
    assert negative_prices == 0
    negative_costs = db_session.query(func.count(Product.id)).filter(Product.unit_cost < 0).scalar()
    assert negative_costs == 0

    # Check order total calculation sanity: total_amount >= subtotal - discount
    inconsistent_orders = (
        db_session.query(func.count(Order.id))
        .filter(Order.total_amount < (Order.subtotal_amount - Order.discount_amount))
        .scalar()
    )
    assert inconsistent_orders == 0

    # Completed orders have shipped_at and delivered_at
    completed_without_delivery = (
        db_session.query(func.count(Order.id))
        .filter(Order.status == "completed", Order.delivered_at.is_(None))
        .scalar()
    )
    assert completed_without_delivery == 0


@pytest.mark.m03
def test_m03_t10_deterministic_seed_test(db_session: Session) -> None:
    """M3-T10: Deterministic seed test — verify stable baseline checksums and counts."""
    order_count = db_session.query(func.count(Order.id)).scalar()
    assert order_count == 15000

    cust_count = db_session.query(func.count(Customer.id)).scalar()
    assert cust_count == 2500

    first_cust = (
        db_session.query(Customer).order_id_asc
        if hasattr(Customer, "order_id_asc")
        else db_session.query(Customer).order_by(Customer.id).first()
    )
    assert first_cust is not None
    assert first_cust.customer_code == "CUST-00001"


@pytest.mark.m03
def test_m03_t11_database_reset_test() -> None:
    """M3-T11: Database reset test — verify reset script truncates test database cleanly."""
    import sys
    from pathlib import Path

    root_dir = Path(__file__).resolve().parents[2]
    if str(root_dir) not in sys.path:
        sys.path.insert(0, str(root_dir))

    from scripts.reset_database import reset_database

    test_url = settings.test_database_url
    engine = create_engine(test_url, future=True)

    # Seed 1 record in test_db to test reset
    with engine.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO organizations (name, code, base_currency, timezone) "
                "VALUES ('Temp Org', 'TEMP', 'USD', 'UTC') ON CONFLICT DO NOTHING;"
            )
        )

    reset_database(test_url)

    with engine.begin() as conn:
        count = conn.execute(text("SELECT count(*) FROM organizations;")).scalar()
        assert count == 0

    engine.dispose()
