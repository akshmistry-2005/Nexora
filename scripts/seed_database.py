#!/usr/bin/env python3
"""
NEXORA — Deterministic Synthetic Data Seeder
Generates realistic, internally consistent synthetic business and platform data across 24-30 months.
All values are deterministic (seed = 42) for 100% reproducible test gates and environments.
"""

from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
import os
from pathlib import Path
import random
import sys

# Ensure backend root is on sys.path
backend_dir = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(backend_dir))

import numpy as np
from passlib.hash import argon2
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import (
    AnomalyAlert,
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
    SavedView,
    StockMovement,
    Supplier,
    User,
    Warehouse,
    role_permissions,
    user_roles,
)

# Set global deterministic random seed
SEED = 42
random.seed(SEED)
np.random.seed(SEED)


def get_deterministic_argon2_hash(secret: str) -> str:
    """Generate reproducible password hash using Argon2."""
    return argon2.using(rounds=2, memory_cost=10240, parallelism=1).hash(secret)


def seed_database(database_url: str | None = None) -> None:
    target_url = database_url or os.getenv("DATABASE_URL", settings.database_url)
    print(f"Connecting to database for seeding: {target_url}")
    engine = create_engine(target_url, future=True)

    with Session(engine) as session:
        # Check if already seeded
        org_check = session.query(Organization).first()
        if org_check:
            print("Database already contains data. Run scripts/reset_database.py first if a clean reseed is required.")
            return

        print("--- Step 1: Seeding Organization, Departments, Regions ---")
        org = Organization(
            name="Nexora Technologies Inc.",
            code="NEXORA",
            base_currency="USD",
            timezone="UTC",
        )
        session.add(org)
        session.flush()

        depts_data = [
            ("Executive", "EXEC"),
            ("Sales", "SALES"),
            ("Marketing", "MKTG"),
            ("Finance", "FIN"),
            ("Operations", "OPS"),
            ("Inventory & Supply", "INV"),
        ]
        depts = []
        for name, code in depts_data:
            d = Department(organization_id=org.id, name=name, code=code)
            session.add(d)
            depts.append(d)
        session.flush()

        regions_data = [
            ("North America", "NA", "USD"),
            ("Europe", "EU", "USD"),
            ("Asia-Pacific", "APAC", "USD"),
            ("Latin America", "LATAM", "USD"),
            ("Middle East & Africa", "MEA", "USD"),
        ]
        regions = []
        for name, code, curr in regions_data:
            r = Region(organization_id=org.id, name=name, code=code, currency=curr)
            session.add(r)
            regions.append(r)
        session.flush()

        print("--- Step 2: Seeding Employees (35 internal reps) ---")
        sales_dept = next(d for d in depts if d.code == "SALES")
        ops_dept = next(d for d in depts if d.code == "OPS")
        mktg_dept = next(d for d in depts if d.code == "MKTG")
        fin_dept = next(d for d in depts if d.code == "FIN")
        exec_dept = next(d for d in depts if d.code == "EXEC")

        first_names = ["James", "Emma", "Liam", "Olivia", "Noah", "Ava", "Oliver", "Sophia", "Lucas", "Isabella",
                       "Ethan", "Mia", "Alexander", "Charlotte", "Daniel", "Amelia", "Matthew", "Harper", "David", "Evelyn"]
        last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez",
                      "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin"]

        employees = []
        emp_idx = 1
        # 1 CEO / Exec
        employees.append(Employee(
            organization_id=org.id, department_id=exec_dept.id, region_id=regions[0].id,
            employee_code=f"EMP-{emp_idx:04d}", first_name="Arthur", last_name="Vane",
            email="arthur.vane@nexora.local", role_title="Chief Executive Officer",
            hire_date=date(2023, 1, 15), is_active=True
        ))
        emp_idx += 1

        # 18 Sales Reps
        sales_reps = []
        for i in range(18):
            fn = first_names[i % len(first_names)]
            ln = last_names[(i * 3) % len(last_names)]
            reg = regions[i % len(regions)]
            rep = Employee(
                organization_id=org.id, department_id=sales_dept.id, region_id=reg.id,
                employee_code=f"EMP-{emp_idx:04d}", first_name=fn, last_name=ln,
                email=f"{fn.lower()}.{ln.lower()}{emp_idx}@nexora.local",
                role_title="Senior Account Executive" if i % 2 == 0 else "Sales Representative",
                hire_date=date(2023, 3, 1) + timedelta(days=i * 25), is_active=True
            )
            employees.append(rep)
            sales_reps.append(rep)
            emp_idx += 1

        # Remaining depts employees (16)
        dept_pool = [ops_dept, mktg_dept, fin_dept]
        for i in range(16):
            d = dept_pool[i % len(dept_pool)]
            fn = first_names[(i + 7) % len(first_names)]
            ln = last_names[(i * 2 + 5) % len(last_names)]
            reg = regions[i % len(regions)]
            employees.append(Employee(
                organization_id=org.id, department_id=d.id, region_id=reg.id,
                employee_code=f"EMP-{emp_idx:04d}", first_name=fn, last_name=ln,
                email=f"{fn.lower()}.{ln.lower()}{emp_idx}@nexora.local",
                role_title=f"{d.name} Specialist",
                hire_date=date(2023, 4, 1) + timedelta(days=i * 30), is_active=True
            ))
            emp_idx += 1

        session.add_all(employees)
        session.flush()

        print("--- Step 3: Seeding Suppliers & Categories & Products ---")
        suppliers_data = [
            ("Apex Silicon Solutions", "SUP-0001", 10, Decimal("4.85")),
            ("Global Display Corp", "SUP-0002", 14, Decimal("4.60")),
            ("Nexus Semiconductor", "SUP-0003", 21, Decimal("4.25")),
            ("Vanguard Power & Cooling", "SUP-0004", 12, Decimal("4.75")),
            ("Shenzhen Precision Tech", "SUP-0005", 18, Decimal("4.10")),
            ("Tokyo Sensor Systems", "SUP-0006", 8, Decimal("4.90")),
            ("Bavaria Micro Electronics", "SUP-0007", 15, Decimal("4.70")),
            ("Pacific Memory Fabricators", "SUP-0008", 14, Decimal("4.35")),
            ("Cascade Fiber Optics", "SUP-0009", 11, Decimal("4.55")),
            ("Titanium Chassis Works", "SUP-0010", 20, Decimal("3.95")),
            ("Delta Circuit Labs", "SUP-0011", 12, Decimal("4.40")),
            ("Nordic Audio Engineering", "SUP-0012", 16, Decimal("4.65")),
            ("Seiko Electronic Components", "SUP-0013", 9, Decimal("4.80")),
            ("Seoul Display Foundry", "SUP-0014", 14, Decimal("4.50")),
            ("Veritas Security Chips", "SUP-0015", 10, Decimal("4.92")),
            ("Kyoto Thermal Materials", "SUP-0016", 13, Decimal("4.45")),
            ("Silicon Valley Logic", "SUP-0017", 7, Decimal("4.88")),
            ("Eindhoven Lithography", "SUP-0018", 25, Decimal("4.15")),
            ("Atlas Cable Assemblies", "SUP-0019", 12, Decimal("4.30")),
            ("Pinnacle Power Supplies", "SUP-0020", 14, Decimal("4.50")),
            ("Meridian Optoelectronics", "SUP-0021", 16, Decimal("4.20")),
            ("Hanseatic Fasteners", "SUP-0022", 10, Decimal("4.75")),
            ("Zurich Sensorics", "SUP-0023", 11, Decimal("4.85")),
            ("Orion Battery Technologies", "SUP-0024", 17, Decimal("4.05")),
            ("Summit Enterprise Metals", "SUP-0025", 19, Decimal("4.10")),
        ]
        suppliers = []
        for name, scode, sla, qual in suppliers_data:
            s = Supplier(
                organization_id=org.id, supplier_code=scode, name=name,
                contact_email=f"procurement@{scode.lower()}.vendor.local",
                lead_time_days_sla=sla, quality_rating=qual, is_active=True
            )
            session.add(s)
            suppliers.append(s)
        session.flush()

        categories_data = [
            ("Laptops & Workstations", "LAPTOPS", "Enterprise developer and designer notebooks and mobile workstations."),
            ("Enterprise Servers", "SERVERS", "Rackmount blade servers, GPU nodes, and virtualization hosts."),
            ("Networking & Mesh", "NETWORK", "Core switches, PoE routers, and multi-gigabit mesh access points."),
            ("Smart Peripherals", "PERIPHERAL", "Ergonomic mechanical keyboards, docking hubs, and 4K webcams."),
            ("Cloud Storage Devices", "STORAGE", "High-throughput NVMe SAN arrays and direct-attached storage units."),
            ("Security Keys & Tokens", "SECURITY", "FIDO2 hardware security keys, smart card readers, and HSM appliances."),
            ("Monitors & Displays", "MONITORS", "Color-calibrated 4K/5K displays and ultra-wide productivity panels."),
            ("Power & Rack Solutions", "POWER", "Smart rack PDUs, online UPS systems, and environmental sensors."),
        ]
        categories = []
        for cname, ccode, cdesc in categories_data:
            c = Category(organization_id=org.id, name=cname, code=ccode, description=cdesc)
            session.add(c)
            categories.append(c)
        session.flush()

        # 120 Products (15 per category)
        products = []
        sku_counter = 100
        product_cost_bases = {
            "LAPTOPS": (Decimal("750.00"), Decimal("1499.00")),
            "SERVERS": (Decimal("1800.00"), Decimal("3899.00")),
            "NETWORK": (Decimal("120.00"), Decimal("299.00")),
            "PERIPHERAL": (Decimal("35.00"), Decimal("89.00")),
            "STORAGE": (Decimal("280.00"), Decimal("649.00")),
            "SECURITY": (Decimal("18.00"), Decimal("49.00")),
            "MONITORS": (Decimal("220.00"), Decimal("499.00")),
            "POWER": (Decimal("160.00"), Decimal("379.00")),
        }

        for cat in categories:
            cost_min, price_min = product_cost_bases[cat.code]
            for p_idx in range(1, 16):
                sku = f"SKU-{cat.code}-{p_idx:02d}"
                multiplier = Decimal(str(1.0 + (p_idx - 1) * 0.12))
                cost = (cost_min * multiplier).quantize(Decimal("0.01"))
                price = (price_min * multiplier).quantize(Decimal("0.01"))
                p = Product(
                    organization_id=org.id, category_id=cat.id, sku=sku,
                    name=f"Nexora {cat.name.split()[0]} {p_idx * 100} Pro",
                    unit_cost=cost, unit_price=price,
                    reorder_point=40 + (p_idx % 4) * 15,
                    target_stock=200 + (p_idx % 5) * 50,
                    is_active=True
                )
                session.add(p)
                products.append(p)
        session.flush()

        print("--- Step 4: Seeding Warehouses & Inventory (480 rows) ---")
        warehouses_data = [
            ("WH-NA-EAST", "East Coast Distribution Center", regions[0].id, 100000),
            ("WH-NA-WEST", "West Coast Logistics Hub", regions[0].id, 80000),
            ("WH-EU-CENTRAL", "Central Europe Warehouse Frankfurt", regions[1].id, 90000),
            ("WH-APAC-SING", "APAC Distribution Singapore", regions[2].id, 85000),
        ]
        warehouses = []
        for wcode, wname, reg_id, cap in warehouses_data:
            w = Warehouse(
                organization_id=org.id, region_id=reg_id, warehouse_code=wcode,
                name=wname, capacity_units=cap
            )
            session.add(w)
            warehouses.append(w)
        session.flush()

        inventory_rows = []
        stock_movements = []
        for w in warehouses:
            for p in products:
                # Deterministic inventory levels
                base_qty = int(np.random.randint(15, 320))
                # Inject a few intentional low stock and out-of-stock items for Module 9/13 testing
                if p.id in (5, 23, 77) and w.id == warehouses[0].id:
                    base_qty = 0  # Out of stock
                elif p.id in (12, 44, 91) and w.id == warehouses[1].id:
                    base_qty = 15  # Low stock below reorder point

                reserved = int(min(base_qty, np.random.randint(0, 10))) if base_qty > 0 else 0
                inv = Inventory(
                    organization_id=org.id, warehouse_id=w.id, product_id=p.id,
                    quantity_on_hand=base_qty, quantity_reserved=reserved,
                    reorder_point=p.reorder_point,
                    last_restocked_at=datetime(2026, 10, 15, tzinfo=UTC) - timedelta(days=int(np.random.randint(1, 120)))
                )
                inventory_rows.append(inv)
                stock_movements.append(StockMovement(
                    organization_id=org.id, warehouse_id=w.id, product_id=p.id,
                    movement_type="receipt", quantity_delta=base_qty,
                    reference_id="INIT-SEED-RESTOCK", notes="Initial baseline warehouse inventory."
                ))

        session.add_all(inventory_rows)
        session.add_all(stock_movements)
        session.flush()

        print("--- Step 5: Seeding Customers (2,500 customers) ---")
        acq_channels = ["Organic Search", "Google Search Ads", "LinkedIn Ads", "Direct Sales", "Partner Referral", "Webinar / Events"]
        customer_types = ["B2B", "B2C", "Enterprise"]
        type_weights = [0.55, 0.30, 0.15]

        start_date = date(2024, 1, 1)
        customers = []
        for c_idx in range(1, 2501):
            ctype = np.random.choice(customer_types, p=type_weights)
            reg = regions[np.random.choice(len(regions), p=[0.40, 0.25, 0.20, 0.08, 0.07])]
            chan = random.choice(acq_channels)
            signup_offset = int(np.random.randint(0, 1040))  # within last ~34 months
            c_signup = start_date + timedelta(days=signup_offset)

            fn = first_names[c_idx % len(first_names)]
            ln = last_names[(c_idx * 7) % len(last_names)]
            cname = f"{ln} Technologies LLC" if ctype != "B2C" else None

            customers.append(Customer(
                organization_id=org.id, region_id=reg.id,
                customer_code=f"CUST-{c_idx:05d}", company_name=cname,
                contact_name=f"{fn} {ln}", email=f"cust{c_idx}_{fn.lower()}@clientdomain.local",
                customer_type=ctype, acquisition_channel=chan, signup_date=c_signup,
                is_active=True
            ))

        session.add_all(customers)
        session.flush()

        print("--- Step 6: Seeding Campaigns (40 campaigns) & Daily Events ---")
        campaign_channels = ["Google Search", "LinkedIn Ads", "Email", "Display", "Events", "Partner"]
        campaigns = []
        campaign_events = []

        cmp_base_date = date(2024, 1, 15)
        for cmp_idx in range(1, 41):
            c_chan = campaign_channels[cmp_idx % len(campaign_channels)]
            c_start = cmp_base_date + timedelta(days=(cmp_idx - 1) * 25)
            c_dur = int(np.random.randint(75, 120))
            c_end = c_start + timedelta(days=c_dur)
            budget = Decimal(str(np.random.randint(15, 80) * 1000.00))

            cmp = Campaign(
                organization_id=org.id, campaign_code=f"CMP-{c_start.year}-{cmp_idx:03d}-{c_chan.split()[0].upper()}",
                name=f"Nexora {c_chan} Q{((c_start.month - 1)//3) + 1} Growth Initiative",
                channel=c_chan, target_segment="Enterprise IT & Developers",
                start_date=c_start, end_date=c_end, budget_amount=budget, is_active=True
            )
            campaigns.append(cmp)

        session.add_all(campaigns)
        session.flush()

        # Daily campaign events (~3,600 events)
        for cmp in campaigns:
            cur_d = cmp.start_date
            c_end = min(cmp.end_date or cur_d, date(2026, 11, 15))
            daily_budget = float(cmp.budget_amount) / max(1, (cmp.end_date - cmp.start_date).days if cmp.end_date else 30)

            while cur_d <= c_end:
                # Add weekly cycle and occasional spike for anomaly testing
                is_spike = (cmp.id == 3 and cur_d == date(2025, 6, 12))  # Intentional marketing anomaly
                spend_mult = 4.5 if is_spike else np.random.uniform(0.7, 1.3)
                day_spend = round(daily_budget * spend_mult, 2)
                day_impr = int(day_spend * np.random.uniform(40, 80))
                day_clicks = int(day_impr * np.random.uniform(0.015, 0.045))
                day_conv = int(day_clicks * np.random.uniform(0.04, 0.12))
                day_rev = round(day_conv * np.random.uniform(180.0, 520.0), 2)

                campaign_events.append(CampaignEvent(
                    organization_id=org.id, campaign_id=cmp.id, date=cur_d,
                    spend=Decimal(str(day_spend)), impressions=day_impr,
                    clicks=day_clicks, conversions=day_conv,
                    attributed_revenue=Decimal(str(day_rev))
                ))
                cur_d += timedelta(days=1)

        session.add_all(campaign_events)
        session.flush()

        print("--- Step 7: Seeding Orders (15,000 orders) & OrderItems (~38,000) ---")
        sales_channels = ["Direct", "Online", "Partner", "Field Sales"]
        order_statuses = ["completed", "shipped", "processing", "pending", "cancelled", "returned"]
        status_weights = [0.80, 0.08, 0.03, 0.02, 0.03, 0.04]

        # Pre-assign orders per customer to produce realistic repeat purchase and churn distributions
        order_start = datetime(2024, 1, 1, 8, 0, 0, tzinfo=UTC)
        total_days = (datetime(2026, 11, 15, tzinfo=UTC) - order_start).days

        orders = []
        order_items = []
        payments = []
        order_returns = []

        order_counter = 1
        return_counter = 1

        # High-value customers get more orders; inactive customers get 1 early order
        customer_order_counts = np.random.choice([1, 2, 3, 5, 8, 14], size=len(customers), p=[0.45, 0.25, 0.15, 0.09, 0.04, 0.02])

        # Generate orders chronologically up to target_orders
        generated_orders = 0
        target_orders = 15000

        # Create order pool targeting ~15,000 orders across customers
        while generated_orders < target_orders:
            for c_idx, cust in enumerate(customers):
                if generated_orders >= target_orders:
                    break

                num_orders_batch = int(np.random.choice([1, 2, 3], p=[0.70, 0.20, 0.10]))
                c_signup_dt = datetime.combine(cust.signup_date, datetime.min.time()).replace(tzinfo=UTC)

                for _ in range(num_orders_batch):
                    if generated_orders >= target_orders:
                        break

                    # Order date after customer signup date
                    max_days = max(1, (datetime(2026, 11, 15, tzinfo=UTC) - c_signup_dt).days)
                    day_offset = int(np.random.randint(0, max_days))
                    o_date = c_signup_dt + timedelta(days=day_offset, hours=int(np.random.randint(8, 20)), minutes=int(np.random.randint(0, 59)))

                    # Status
                    status = np.random.choice(order_statuses, p=status_weights)
                    if (datetime(2026, 11, 15, tzinfo=UTC) - o_date).days < 3 and status in ("completed", "shipped"):
                        status = "processing"

                    channel = random.choice(sales_channels)
                    s_rep = random.choice(sales_reps) if channel in ("Direct", "Field Sales") else None
                    wh = random.choice(warehouses)
                    cmp = random.choice(campaigns) if random.random() < 0.35 else None

                    o_num = f"ORD-{o_date.year}-{order_counter:06d}"
                    shipped_at = o_date + timedelta(hours=int(np.random.randint(12, 48))) if status in ("shipped", "completed", "returned") else None
                    promised_del = o_date + timedelta(days=int(np.random.randint(3, 7)))
                    delivered_at = shipped_at + timedelta(days=int(np.random.randint(1, 4))) if status in ("completed", "returned") else None
                    cancelled_at = o_date + timedelta(hours=int(np.random.randint(1, 12))) if status == "cancelled" else None
                    cancel_reason = "Customer changed mind before dispatch" if status == "cancelled" else None

                    # Generate 1 to 4 order items (average ~2.5 items per order)
                    num_items = int(np.random.choice([1, 2, 3, 4], p=[0.40, 0.35, 0.18, 0.07]))
                    selected_products = random.sample(products, num_items)

                    subtotal = Decimal("0.00")
                    order_item_records = []
                    for sp in selected_products:
                        qty = int(np.random.choice([1, 2, 3, 5], p=[0.70, 0.18, 0.08, 0.04]))
                        line_disc = Decimal("0.00") if np.random.random() > 0.15 else (sp.unit_price * Decimal(str(qty * 0.10))).quantize(Decimal("0.01"))
                        line_tot = ((sp.unit_price * Decimal(str(qty))) - line_disc).quantize(Decimal("0.01"))
                        subtotal += line_tot

                        order_item_records.append((sp, qty, sp.unit_cost, sp.unit_price, line_disc, line_tot))

                    ord_disc = Decimal("0.00")
                    tax = (subtotal * Decimal("0.075")).quantize(Decimal("0.01"))
                    shipping = Decimal("15.00") if subtotal < Decimal("300.00") else Decimal("0.00")
                    total = (subtotal - ord_disc + tax + shipping).quantize(Decimal("0.01"))

                    ord_obj = Order(
                        organization_id=org.id, order_number=o_num, customer_id=cust.id,
                        sales_rep_id=s_rep.id if s_rep else None, region_id=cust.region_id,
                        warehouse_id=wh.id, campaign_id=cmp.id if cmp else None,
                        order_date=o_date, status=status, sales_channel=channel,
                        subtotal_amount=subtotal, discount_amount=ord_disc,
                        tax_amount=tax, shipping_amount=shipping, total_amount=total,
                        promised_delivery_at=promised_del, shipped_at=shipped_at,
                        delivered_at=delivered_at, cancelled_at=cancelled_at,
                        cancellation_reason=cancel_reason
                    )
                    session.add(ord_obj)
                    session.flush()

                    for sp, qty, cost, price, l_disc, l_tot in order_item_records:
                        order_items.append(OrderItem(
                            organization_id=org.id, order_id=ord_obj.id, product_id=sp.id,
                            quantity=qty, unit_cost=cost, unit_price=price,
                            discount_amount=l_disc, total_line_amount=l_tot
                        ))

                    # Payment for non-cancelled orders
                    if status != "cancelled":
                        payments.append(Payment(
                            organization_id=org.id, order_id=ord_obj.id,
                            payment_reference=f"PAY-{o_date.year}-{order_counter:06d}",
                            payment_method=random.choice(["Corporate Net 30", "Credit Card", "Wire", "ACH"]),
                            amount=total,
                            status="refunded" if status == "returned" else "completed",
                            payment_date=o_date + timedelta(minutes=int(np.random.randint(5, 120)))
                        ))

                    # Return record if status is returned
                    if status == "returned":
                        order_returns.append(OrderReturn(
                            organization_id=org.id, order_id=ord_obj.id,
                            product_id=order_item_records[0][0].id,
                            quantity=order_item_records[0][1],
                            return_reason=random.choice(["Defective on arrival", "Wrong specification ordered", "Compatibility mismatch"]),
                            refund_amount=order_item_records[0][5],
                            return_status="approved",
                            return_date=delivered_at + timedelta(days=int(np.random.randint(2, 10))) if delivered_at else o_date + timedelta(days=5)
                        ))
                        return_counter += 1

                    order_counter += 1
                    generated_orders += 1

        session.add_all(order_items)
        session.add_all(payments)
        session.add_all(order_returns)
        session.flush()

        print(f"Generated {generated_orders} orders, {len(order_items)} items, {len(payments)} payments, {len(order_returns)} returns.")

        print("--- Step 8: Seeding Purchase Orders (1,200 POs) ---")
        purchase_orders = []
        po_start = datetime(2024, 1, 10, tzinfo=UTC)
        for po_idx in range(1, 1201):
            sup = random.choice(suppliers)
            wh = random.choice(warehouses)
            po_date = po_start + timedelta(days=int(po_idx * 0.85), hours=int(np.random.randint(9, 17)))
            exp_delivery = po_date.date() + timedelta(days=sup.lead_time_days_sla)

            # Some delayed delivery to test lead-time SLAs
            is_delayed = np.random.random() < 0.18
            lead_jitter = int(np.random.randint(1, 6)) if is_delayed else -int(np.random.randint(0, 3))
            act_delivery = exp_delivery + timedelta(days=lead_jitter) if po_date < datetime(2026, 11, 1, tzinfo=UTC) else None

            ord_units = int(np.random.randint(50, 500))
            rec_units = ord_units if act_delivery else 0
            def_units = int(rec_units * np.random.uniform(0.005, 0.04)) if rec_units > 0 else 0
            unit_cost = Decimal(str(np.random.uniform(35.0, 450.0))).quantize(Decimal("0.01"))
            po_total = (unit_cost * Decimal(str(ord_units))).quantize(Decimal("0.01"))

            status = "received" if act_delivery else ("issued" if po_date > datetime(2026, 10, 15, tzinfo=UTC) else "partially_received")

            purchase_orders.append(PurchaseOrder(
                organization_id=org.id, supplier_id=sup.id, warehouse_id=wh.id,
                po_number=f"PO-{po_date.year}-{po_idx:05d}", order_date=po_date,
                expected_delivery_date=exp_delivery, actual_delivery_date=act_delivery,
                ordered_units=ord_units, received_units=rec_units,
                defective_units=def_units, total_cost=po_total, status=status
            ))

        session.add_all(purchase_orders)
        session.flush()

        print("--- Step 9: Seeding Operating Expenses (1,500) & Budgets (600) ---")
        expense_categories = ["Payroll", "Marketing", "Logistics", "Facilities", "IT & SaaS", "General Admin"]
        expenses = []
        cur_exp_date = date(2024, 1, 1)
        end_exp_date = date(2026, 11, 15)

        exp_counter = 1
        while cur_exp_date <= end_exp_date:
            # 1 to 3 expenses per day across departments
            for _ in range(random.choice([1, 2])):
                dept = random.choice(depts)
                cat = "Marketing" if dept.code == "MKTG" else random.choice(expense_categories)
                amount = Decimal(str(np.random.randint(400, 12000) * 1.0)).quantize(Decimal("0.01"))
                expenses.append(Expense(
                    organization_id=org.id, department_id=dept.id, region_id=random.choice(regions).id,
                    expense_date=cur_exp_date, category=cat, amount=amount,
                    description=f"{cat} operational expenditure - {dept.name}"
                ))
                exp_counter += 1
            cur_exp_date += timedelta(days=1)

        session.add_all(expenses[:1500])
        session.flush()

        # Budgets across 2024, 2025, 2026 for each dept and quarter
        budgets = []
        for yr in [2024, 2025, 2026]:
            for qtr in [1, 2, 3, 4]:
                for d in depts:
                    for target in ["Revenue", "OpEx"]:
                        b_amt = Decimal(str(np.random.randint(250, 1500) * 1000.0)).quantize(Decimal("0.01"))
                        budgets.append(Budget(
                            organization_id=org.id, department_id=d.id, region_id=None,
                            fiscal_year=yr, fiscal_quarter=qtr, metric_target=target,
                            budgeted_amount=b_amt
                        ))

        session.add_all(budgets)
        session.flush()

        print("--- Step 10: Seeding RBAC Permissions, Roles & Users ---")
        # 28 Permissions from Product Requirements §3.2
        permissions_data = [
            ("dashboard.view", "analytics", "View Overview Dashboard"),
            ("sales.view", "analytics", "View Sales Intelligence & order drill-downs"),
            ("customer.view", "analytics", "View Customer Intelligence & segments"),
            ("customer.create", "operations", "Create customer records"),
            ("customer.update", "operations", "Update customer records"),
            ("customer.delete", "operations", "Delete customer records"),
            ("marketing.view", "analytics", "View Marketing Intelligence"),
            ("finance.view", "analytics", "View Financial Intelligence"),
            ("inventory.view", "analytics", "View Inventory Intelligence"),
            ("operations.view", "analytics", "View Operations Intelligence"),
            ("supplier.view", "analytics", "View Supplier Intelligence"),
            ("statistics.view", "advanced_analytics", "View & execute read-only statistical analyses"),
            ("predictions.view", "advanced_analytics", "View & run read-only ML predictions/forecasts"),
            ("predictions.manage", "advanced_analytics", "Trigger model training/reload metadata"),
            ("anomaly.view", "advanced_analytics", "View Anomaly & Risk Intelligence feed"),
            ("anomaly.acknowledge", "advanced_analytics", "Acknowledge or update anomaly alert status"),
            ("datasource.view", "data_ops", "View data source registry & import history"),
            ("datasource.import", "data_ops", "Upload CSV, map columns, execute imports"),
            ("dataquality.view", "data_ops", "View data quality scores & pipeline runs"),
            ("dataquality.manage", "data_ops", "Approve/reject cleaning runs & retry pipelines"),
            ("report.view", "reporting", "View report catalogue & pre-saved views"),
            ("report.export", "reporting", "Export permitted report CSV"),
            ("report.sensitive_fields", "reporting", "Include internal cost/margin fields in exports"),
            ("saved_view.manage", "reporting", "Create, update, delete DB-persisted saved views"),
            ("user.manage", "administration", "View/create/toggle users & assign roles"),
            ("role.manage", "administration", "View/modify non-owner role permissions"),
            ("audit.view", "administration", "View append-only audit logs"),
            ("settings.manage", "administration", "Manage org settings, departments & system config"),
            ("system.reset_demo", "administration", "Reset & reseed local demonstration dataset"),
        ]

        perms_dict = {}
        for pcode, pcat, pdesc in permissions_data:
            p = Permission(code=pcode, category=pcat, description=pdesc)
            session.add(p)
            perms_dict[pcode] = p
        session.flush()

        # 6 Roles
        roles_data = [
            ("owner", "Owner / Administrator", "Full unrestricted administrative and data operations control."),
            ("executive", "Executive (CEO)", "High-level company performance, financial health, and strategic analytics."),
            ("department_manager", "Department Manager", "Departmental performance, sales, inventory, and operations tracking."),
            ("data_analyst", "Data Analyst", "Exploratory analytics, multi-filters, reports, and data exports."),
            ("data_scientist", "Data Scientist", "Statistical testing, predictive models, evaluations, and anomalies."),
            ("general_viewer", "General Viewer", "Basic read-only dashboard exploration without export capabilities."),
        ]

        roles_dict = {}
        for rname, rdisp, rdesc in roles_data:
            r = Role(name=rname, display_name=rdisp, description=rdesc, is_system=True)
            session.add(r)
            roles_dict[rname] = r
        session.flush()

        # Assign permissions per §3.2 Role Matrix
        # Owner gets all permissions
        for p in perms_dict.values():
            session.execute(role_permissions.insert().values(role_id=roles_dict["owner"].id, permission_id=p.id))

        # Executive
        exec_perms = ["dashboard.view", "sales.view", "customer.view", "marketing.view", "finance.view",
                      "inventory.view", "operations.view", "supplier.view", "statistics.view", "predictions.view",
                      "anomaly.view", "datasource.view", "dataquality.view", "report.view", "report.export", "report.sensitive_fields"]
        for pc in exec_perms:
            session.execute(role_permissions.insert().values(role_id=roles_dict["executive"].id, permission_id=perms_dict[pc].id))

        # Department Manager (Sales-focused, no finance or sensitive margin export)
        mgr_perms = ["dashboard.view", "sales.view", "customer.view", "marketing.view",
                     "inventory.view", "operations.view", "supplier.view", "statistics.view", "predictions.view",
                     "anomaly.view", "report.view", "report.export"]
        for pc in mgr_perms:
            session.execute(role_permissions.insert().values(role_id=roles_dict["department_manager"].id, permission_id=perms_dict[pc].id))

        # Data Analyst
        analyst_perms = ["dashboard.view", "sales.view", "customer.view", "marketing.view", "finance.view",
                         "inventory.view", "operations.view", "supplier.view", "statistics.view", "predictions.view",
                         "anomaly.view", "datasource.view", "dataquality.view", "report.view", "report.export", "report.sensitive_fields"]
        for pc in analyst_perms:
            session.execute(role_permissions.insert().values(role_id=roles_dict["data_analyst"].id, permission_id=perms_dict[pc].id))

        # Data Scientist
        scientist_perms = ["dashboard.view", "sales.view", "customer.view", "marketing.view", "finance.view",
                           "inventory.view", "operations.view", "supplier.view", "statistics.view", "predictions.view",
                           "anomaly.view", "datasource.view", "dataquality.view", "report.view", "report.export", "report.sensitive_fields"]
        for pc in scientist_perms:
            session.execute(role_permissions.insert().values(role_id=roles_dict["data_scientist"].id, permission_id=perms_dict[pc].id))

        # General Viewer (No export, no finance, no stats/predictions)
        viewer_perms = ["dashboard.view", "sales.view", "customer.view", "marketing.view",
                        "inventory.view", "operations.view", "supplier.view", "anomaly.view", "report.view"]
        for pc in viewer_perms:
            session.execute(role_permissions.insert().values(role_id=roles_dict["general_viewer"].id, permission_id=perms_dict[pc].id))

        session.flush()

        # Users: Owner + Demo Users
        common_password_hash = get_deterministic_argon2_hash("NexoraDemoPass2026!")
        owner_password_hash = get_deterministic_argon2_hash("NexoraOwnerPass2026!")

        owner_user = User(
            organization_id=org.id, email="owner@nexora.local", password_hash=owner_password_hash,
            full_name="Nexora Platform Owner", is_active=True, is_owner=True
        )
        session.add(owner_user)
        session.flush()
        session.execute(user_roles.insert().values(user_id=owner_user.id, role_id=roles_dict["owner"].id))

        demo_users_data = [
            ("demo_executive@nexora.local", "Elena Vance (CEO)", "executive"),
            ("demo_dept_manager@nexora.local", "Marcus Bradley (Sales Lead)", "department_manager"),
            ("demo_analyst@nexora.local", "Maya Lin (Senior Analyst)", "data_analyst"),
            ("demo_scientist@nexora.local", "Dr. Julian Patel (Lead Data Scientist)", "data_scientist"),
            ("demo_viewer@nexora.local", "Taylor Reed (General Viewer)", "general_viewer"),
        ]

        for d_email, d_name, d_role in demo_users_data:
            u = User(
                organization_id=org.id, email=d_email, password_hash=common_password_hash,
                full_name=d_name, is_active=True, is_owner=False
            )
            session.add(u)
            session.flush()
            session.execute(user_roles.insert().values(user_id=u.id, role_id=roles_dict[d_role].id))

        print("--- Step 11: Seeding Saved Views & Injected Anomalies ---")
        saved_view = SavedView(
            user_id=owner_user.id, section="sales", name="North America Enterprise Q3",
            filter_config={"region": "NA", "customer_segment": "Enterprise", "year": 2025},
            is_shared=True
        )
        session.add(saved_view)

        # Baseline injected anomalies for Module 13 verification
        anomalies_data = [
            ("sales", "2025-04-18", "daily_revenue", Decimal("1420.00"), Decimal("8950.00"), Decimal("-7530.00"), Decimal("-3.85"), "critical",
             "Observed daily sales revenue dropped by 84% compared to the 30-day baseline average ($8,950.00). Injected for risk detection validation."),
            ("transaction", "ORD-2025-008412", "order_total", Decimal("14890.00"), Decimal("1420.00"), Decimal("13470.00"), Decimal("4.20"), "high",
             "Order total is 10.5x above standard customer order size. Flagged for review; not confirmed fraud."),
            ("inventory", "SKU-LAPTOPS-01", "unit_depletion", Decimal("95.00"), Decimal("12.00"), Decimal("83.00"), Decimal("3.40"), "high",
             "Unusually rapid inventory depletion over 48 hours in East Coast Distribution Center."),
            ("marketing", "CMP-2025-003-GOOGLE", "daily_spend", Decimal("4850.00"), Decimal("1100.00"), Decimal("3750.00"), Decimal("3.90"), "critical",
             "Daily campaign expenditure spiked 4.4x above daily allocation threshold."),
        ]

        for dom, ident, met, obs, base, dev, z, sev, exp in anomalies_data:
            session.add(AnomalyAlert(
                organization_id=org.id, domain=dom, entity_identifier=ident,
                metric_name=met, observed_value=obs, baseline_value=base,
                deviation_amount=dev, z_score=z, severity=sev, explanation=exp,
                status="open", detected_at=datetime(2025, 6, 12, 12, 0, 0, tzinfo=UTC)
            ))

        session.commit()
        print("--- Seeding complete successfully! ---")


if __name__ == "__main__":
    url_arg = sys.argv[1] if len(sys.argv) > 1 else None
    seed_database(url_arg)
