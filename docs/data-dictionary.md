# NEXORA — Canonical Data Dictionary

**Document Status:** Approved Baseline (Module 3)  
**Database Engine:** PostgreSQL 16  
**Timezone:** UTC (`TIMESTAMPTZ`)  
**Currency:** USD (`NUMERIC(14,2)`)

---

## 1. Core Reference Entities

### 1.1 `organizations`
| Column | Type | Nullable | Constraints / Default | Description |
| :--- | :--- | :---: | :--- | :--- |
| `id` | `INTEGER` | No | PK, Auto-increment | Organization identifier |
| `name` | `VARCHAR(100)` | No | Unique | Company legal/operating name |
| `code` | `VARCHAR(20)` | No | Unique | Short identifier code (e.g., `NEXORA`) |
| `base_currency` | `VARCHAR(3)` | No | Default `'USD'` | ISO currency code |
| `timezone` | `VARCHAR(50)` | No | Default `'UTC'` | Operating timezone |
| `created_at` | `TIMESTAMPTZ` | No | Default `CURRENT_TIMESTAMP` | Record creation timestamp |

### 1.2 `departments`
| Column | Type | Nullable | Constraints / Default | Description |
| :--- | :--- | :---: | :--- | :--- |
| `id` | `INTEGER` | No | PK, Auto-increment | Department identifier |
| `organization_id` | `INTEGER` | No | FK $\rightarrow$ `organizations.id` | Tenant boundary |
| `name` | `VARCHAR(100)` | No | Unique per org | Department name (Sales, Finance, etc.) |
| `code` | `VARCHAR(20)` | No | Unique per org | Department code (e.g., `SALES`, `MKTG`) |
| `created_at` | `TIMESTAMPTZ` | No | Default `CURRENT_TIMESTAMP` | Record creation timestamp |

### 1.3 `regions`
| Column | Type | Nullable | Constraints / Default | Description |
| :--- | :--- | :---: | :--- | :--- |
| `id` | `INTEGER` | No | PK, Auto-increment | Region identifier |
| `organization_id` | `INTEGER` | No | FK $\rightarrow$ `organizations.id` | Tenant boundary |
| `name` | `VARCHAR(100)` | No | — | Region name (North America, Europe, etc.) |
| `code` | `VARCHAR(20)` | No | Unique per org | Territory code (e.g., `NA`, `EU`, `APAC`) |
| `currency` | `VARCHAR(3)` | No | Default `'USD'` | Regional operational currency |
| `created_at` | `TIMESTAMPTZ` | No | Default `CURRENT_TIMESTAMP` | Record creation timestamp |

### 1.4 `employees`
| Column | Type | Nullable | Constraints / Default | Description |
| :--- | :--- | :---: | :--- | :--- |
| `id` | `INTEGER` | No | PK, Auto-increment | Employee identifier |
| `organization_id` | `INTEGER` | No | FK $\rightarrow$ `organizations.id` | Tenant boundary |
| `department_id` | `INTEGER` | No | FK $\rightarrow$ `departments.id` | Department affiliation |
| `region_id` | `INTEGER` | Yes | FK $\rightarrow$ `regions.id` | Primary region base |
| `employee_code` | `VARCHAR(30)` | No | Unique per org | Unique corporate employee code |
| `first_name` | `VARCHAR(50)` | No | — | First name |
| `last_name` | `VARCHAR(50)` | No | — | Last name |
| `email` | `VARCHAR(120)` | No | Unique | Corporate email address |
| `role_title` | `VARCHAR(100)` | No | — | Job title (e.g., Senior Account Exec) |
| `hire_date` | `DATE` | No | — | Employment start date |
| `is_active` | `BOOLEAN` | No | Default `TRUE` | Active employment status |
| `created_at` | `TIMESTAMPTZ` | No | Default `CURRENT_TIMESTAMP` | Record creation timestamp |

---

## 2. Supply & Product Catalog Entities

### 2.1 `suppliers`
| Column | Type | Nullable | Constraints / Default | Description |
| :--- | :--- | :---: | :--- | :--- |
| `id` | `INTEGER` | No | PK, Auto-increment | Supplier identifier |
| `organization_id` | `INTEGER` | No | FK $\rightarrow$ `organizations.id` | Tenant boundary |
| `region_id` | `INTEGER` | Yes | FK $\rightarrow$ `regions.id` | Geographic supplier base |
| `supplier_code` | `VARCHAR(30)` | No | Unique per org | Vendor code (e.g., `SUP-001`) |
| `name` | `VARCHAR(120)` | No | — | Vendor legal name |
| `contact_email` | `VARCHAR(120)` | Yes | — | Vendor primary contact email |
| `lead_time_days_sla` | `INTEGER` | No | Check $\ge 1$, Default `14` | Expected lead time SLA in days |
| `quality_rating` | `NUMERIC(3,2)` | Yes | Check $0.00$ to $5.00$ | Supplier quality score rating |
| `is_active` | `BOOLEAN` | No | Default `TRUE` | Active supplier flag |
| `created_at` | `TIMESTAMPTZ` | No | Default `CURRENT_TIMESTAMP` | Record creation timestamp |

### 2.2 `categories`
| Column | Type | Nullable | Constraints / Default | Description |
| :--- | :--- | :---: | :--- | :--- |
| `id` | `INTEGER` | No | PK, Auto-increment | Category identifier |
| `organization_id` | `INTEGER` | No | FK $\rightarrow$ `organizations.id` | Tenant boundary |
| `name` | `VARCHAR(100)` | No | Unique per org | Category name (Hardware, Software, etc.) |
| `code` | `VARCHAR(30)` | No | Unique per org | Category slug code |
| `description` | `TEXT` | Yes | — | Category description |
| `created_at` | `TIMESTAMPTZ` | No | Default `CURRENT_TIMESTAMP` | Record creation timestamp |

### 2.3 `products`
| Column | Type | Nullable | Constraints / Default | Description |
| :--- | :--- | :---: | :--- | :--- |
| `id` | `INTEGER` | No | PK, Auto-increment | Product identifier |
| `organization_id` | `INTEGER` | No | FK $\rightarrow$ `organizations.id` | Tenant boundary |
| `category_id` | `INTEGER` | No | FK $\rightarrow$ `categories.id` | Category classification |
| `sku` | `VARCHAR(50)` | No | Unique per org | Stock Keeping Unit |
| `name` | `VARCHAR(150)` | No | — | Commercial product name |
| `unit_cost` | `NUMERIC(14,2)` | No | Check $\ge 0.00$ | Standard manufacturing / procurement cost |
| `unit_price` | `NUMERIC(14,2)` | No | Check $\ge 0.00$ | Standard retail / catalog sales price |
| `reorder_point` | `INTEGER` | No | Default `50` | Low-stock alert threshold in units |
| `target_stock` | `INTEGER` | No | Default `250` | Target replenishing level in units |
| `is_active` | `BOOLEAN` | No | Default `TRUE` | Active for sales flag |
| `created_at` | `TIMESTAMPTZ` | No | Default `CURRENT_TIMESTAMP` | Record creation timestamp |

### 2.4 `warehouses`
| Column | Type | Nullable | Constraints / Default | Description |
| :--- | :--- | :---: | :--- | :--- |
| `id` | `INTEGER` | No | PK, Auto-increment | Warehouse identifier |
| `organization_id` | `INTEGER` | No | FK $\rightarrow$ `organizations.id` | Tenant boundary |
| `region_id` | `INTEGER` | No | FK $\rightarrow$ `regions.id` | Region located in |
| `warehouse_code` | `VARCHAR(30)` | No | Unique per org | Warehouse code (e.g., `WH-NA-EAST`) |
| `name` | `VARCHAR(100)` | No | — | Facility name |
| `capacity_units` | `INTEGER` | No | Check $\ge 0$ | Total storage capacity |
| `created_at` | `TIMESTAMPTZ` | No | Default `CURRENT_TIMESTAMP` | Record creation timestamp |

### 2.5 `inventory`
| Column | Type | Nullable | Constraints / Default | Description |
| :--- | :--- | :---: | :--- | :--- |
| `id` | `INTEGER` | No | PK, Auto-increment | Inventory row identifier |
| `organization_id` | `INTEGER` | No | FK $\rightarrow$ `organizations.id` | Tenant boundary |
| `warehouse_id` | `INTEGER` | No | FK $\rightarrow$ `warehouses.id` | Storage warehouse |
| `product_id` | `INTEGER` | No | FK $\rightarrow$ `products.id` | Product SKU stocked |
| `quantity_on_hand` | `INTEGER` | No | Check $\ge 0$ | Physical stock units present |
| `quantity_reserved` | `INTEGER` | No | Check $\ge 0$, Default `0` | Units allocated to pending orders |
| `reorder_point` | `INTEGER` | No | Check $\ge 0$ | Warehouse-specific reorder point |
| `last_restocked_at` | `TIMESTAMPTZ` | Yes | — | Timestamp of most recent inbound receipt |
| `updated_at` | `TIMESTAMPTZ` | No | Default `CURRENT_TIMESTAMP` | Last updated timestamp |

---

## 3. Sales, Orders & Customer Entities

### 3.1 `customers`
| Column | Type | Nullable | Constraints / Default | Description |
| :--- | :--- | :---: | :--- | :--- |
| `id` | `INTEGER` | No | PK, Auto-increment | Customer identifier |
| `organization_id` | `INTEGER` | No | FK $\rightarrow$ `organizations.id` | Tenant boundary |
| `region_id` | `INTEGER` | No | FK $\rightarrow$ `regions.id` | Geographic region of customer |
| `customer_code` | `VARCHAR(40)` | No | Unique per org | Customer business code (e.g., `CUST-10492`) |
| `company_name` | `VARCHAR(150)` | Yes | — | Business account name (for B2B) |
| `contact_name` | `VARCHAR(100)` | No | — | Primary contact name |
| `email` | `VARCHAR(120)` | No | Unique per org | Primary email address |
| `phone` | `VARCHAR(40)` | Yes | — | Contact phone number |
| `customer_type` | `VARCHAR(20)` | No | Check in `('B2B', 'B2C', 'Enterprise')` | Customer classification type |
| `acquisition_channel` | `VARCHAR(50)` | No | — | Acquisition origin (e.g., Paid Search, Referral) |
| `signup_date` | `DATE` | No | — | Account creation / registration date |
| `is_active` | `BOOLEAN` | No | Default `TRUE` | Account active flag |
| `created_at` | `TIMESTAMPTZ` | No | Default `CURRENT_TIMESTAMP` | Record creation timestamp |

### 3.2 `orders`
| Column | Type | Nullable | Constraints / Default | Description |
| :--- | :--- | :---: | :--- | :--- |
| `id` | `INTEGER` | No | PK, Auto-increment | Order identifier |
| `organization_id` | `INTEGER` | No | FK $\rightarrow$ `organizations.id` | Tenant boundary |
| `order_number` | `VARCHAR(40)` | No | Unique per org | Commercial order code (e.g., `ORD-2025-00124`) |
| `customer_id` | `INTEGER` | No | FK $\rightarrow$ `customers.id`, RESTRICT | Purchasing customer |
| `sales_rep_id` | `INTEGER` | Yes | FK $\rightarrow$ `employees.id`, SET NULL | Assigned sales representative |
| `region_id` | `INTEGER` | No | FK $\rightarrow$ `regions.id` | Destination sales region |
| `warehouse_id` | `INTEGER` | Yes | FK $\rightarrow$ `warehouses.id` | Fulfilment warehouse |
| `campaign_id` | `INTEGER` | Yes | FK $\rightarrow$ `campaigns.id`, SET NULL | Attributed marketing campaign |
| `order_date` | `TIMESTAMPTZ` | No | — | Order submission timestamp |
| `status` | `VARCHAR(25)` | No | Check in `('pending', 'processing', 'shipped', 'completed', 'cancelled', 'returned')` | Current lifecycle status |
| `sales_channel` | `VARCHAR(30)` | No | Check in `('Direct', 'Online', 'Partner', 'Field Sales')` | Sales channel |
| `subtotal_amount` | `NUMERIC(14,2)` | No | Check $\ge 0.00$ | Sum of order items price before discount |
| `discount_amount` | `NUMERIC(14,2)` | No | Check $\ge 0.00$, Default `0.00` | Order-level discount deduction |
| `tax_amount` | `NUMERIC(14,2)` | No | Check $\ge 0.00$, Default `0.00` | Sales tax collected |
| `shipping_amount` | `NUMERIC(14,2)` | No | Check $\ge 0.00$, Default `0.00` | Shipping fees charged |
| `total_amount` | `NUMERIC(14,2)` | No | Check $\ge 0.00$ | Net total payable (`subtotal - discount + tax + shipping`) |
| `promised_delivery_at` | `TIMESTAMPTZ` | Yes | — | SLA target delivery timestamp |
| `shipped_at` | `TIMESTAMPTZ` | Yes | — | Actual shipment dispatched timestamp |
| `delivered_at` | `TIMESTAMPTZ` | Yes | — | Actual delivery confirmed timestamp |
| `cancelled_at` | `TIMESTAMPTZ` | Yes | — | Cancellation timestamp |
| `cancellation_reason` | `VARCHAR(200)` | Yes | — | Reason for cancellation if applicable |
| `created_at` | `TIMESTAMPTZ` | No | Default `CURRENT_TIMESTAMP` | Record creation timestamp |

### 3.3 `order_items`
| Column | Type | Nullable | Constraints / Default | Description |
| :--- | :--- | :---: | :--- | :--- |
| `id` | `INTEGER` | No | PK, Auto-increment | Order item line identifier |
| `organization_id` | `INTEGER` | No | FK $\rightarrow$ `organizations.id` | Tenant boundary |
| `order_id` | `INTEGER` | No | FK $\rightarrow$ `orders.id`, CASCADE | Parent order |
| `product_id` | `INTEGER` | No | FK $\rightarrow$ `products.id`, RESTRICT | Ordered product |
| `quantity` | `INTEGER` | No | Check $> 0$ | Units ordered |
| `unit_cost` | `NUMERIC(14,2)` | No | Check $\ge 0.00$ | Unit manufacturing cost at purchase time |
| `unit_price` | `NUMERIC(14,2)` | No | Check $\ge 0.00$ | Unit sales price at purchase time |
| `discount_amount` | `NUMERIC(14,2)` | No | Check $\ge 0.00$, Default `0.00` | Line-item discount amount |
| `total_line_amount` | `NUMERIC(14,2)` | No | Check $\ge 0.00$ | Calculated line amount: `(quantity * unit_price) - discount` |

### 3.4 `payments`
| Column | Type | Nullable | Constraints / Default | Description |
| :--- | :--- | :---: | :--- | :--- |
| `id` | `INTEGER` | No | PK, Auto-increment | Payment transaction identifier |
| `organization_id` | `INTEGER` | No | FK $\rightarrow$ `organizations.id` | Tenant boundary |
| `order_id` | `INTEGER` | No | FK $\rightarrow$ `orders.id`, RESTRICT | Associated order |
| `payment_reference` | `VARCHAR(60)` | No | Unique per org | Settlement gateway reference code |
| `payment_method` | `VARCHAR(30)` | No | Check in `('Credit Card', 'Bank Transfer', 'Wire', 'ACH', 'Corporate Net 30')` | Method of payment |
| `amount` | `NUMERIC(14,2)` | No | Check $> 0.00$ | Payment amount collected |
| `status` | `VARCHAR(20)` | No | Check in `('completed', 'pending', 'failed', 'refunded')` | Settlement status |
| `payment_date` | `TIMESTAMPTZ` | No | — | Settlement transaction timestamp |
| `created_at` | `TIMESTAMPTZ` | No | Default `CURRENT_TIMESTAMP` | Record creation timestamp |

### 3.5 `order_returns`
| Column | Type | Nullable | Constraints / Default | Description |
| :--- | :--- | :---: | :--- | :--- |
| `id` | `INTEGER` | No | PK, Auto-increment | Return case identifier |
| `organization_id` | `INTEGER` | No | FK $\rightarrow$ `organizations.id` | Tenant boundary |
| `order_id` | `INTEGER` | No | FK $\rightarrow$ `orders.id`, RESTRICT | Associated order |
| `product_id` | `INTEGER` | No | FK $\rightarrow$ `products.id`, RESTRICT | Returned product item |
| `quantity` | `INTEGER` | No | Check $> 0$ | Units returned |
| `return_reason` | `VARCHAR(150)` | No | — | Reason (Defective, Wrong Item, Unsatisfied) |
| `refund_amount` | `NUMERIC(14,2)` | No | Check $\ge 0.00$ | Net refund credited to customer |
| `return_status` | `VARCHAR(20)` | No | Check in `('pending', 'approved', 'rejected', 'restocked')` | Status of return workflow |
| `return_date` | `TIMESTAMPTZ` | No | — | Timestamp return initiated |
| `created_at` | `TIMESTAMPTZ` | No | Default `CURRENT_TIMESTAMP` | Record creation timestamp |

---

## 4. Marketing, Procurement & Financial Entities

### 4.1 `campaigns`
| Column | Type | Nullable | Constraints / Default | Description |
| :--- | :--- | :---: | :--- | :--- |
| `id` | `INTEGER` | No | PK, Auto-increment | Campaign identifier |
| `organization_id` | `INTEGER` | No | FK $\rightarrow$ `organizations.id` | Tenant boundary |
| `campaign_code` | `VARCHAR(40)` | No | Unique per org | Campaign code (e.g., `CMP-2025-Q1-SEARCH`) |
| `name` | `VARCHAR(150)` | No | — | Campaign initiative name |
| `channel` | `VARCHAR(50)` | No | Check in `('Google Search', 'LinkedIn Ads', 'Email', 'Display', 'Events', 'Partner')` | Primary marketing channel |
| `target_segment` | `VARCHAR(50)` | Yes | — | Intended audience segment |
| `start_date` | `DATE` | No | — | Campaign launch flight date |
| `end_date` | `DATE` | Yes | — | Campaign conclusion date |
| `budget_amount` | `NUMERIC(14,2)` | No | Check $\ge 0.00$ | Total allocated campaign budget |
| `is_active` | `BOOLEAN` | No | Default `TRUE` | Active campaign flag |
| `created_at` | `TIMESTAMPTZ` | No | Default `CURRENT_TIMESTAMP` | Record creation timestamp |

### 4.2 `campaign_events` (Daily Performance Tracking)
| Column | Type | Nullable | Constraints / Default | Description |
| :--- | :--- | :---: | :--- | :--- |
| `id` | `INTEGER` | No | PK, Auto-increment | Daily event identifier |
| `organization_id` | `INTEGER` | No | FK $\rightarrow$ `organizations.id` | Tenant boundary |
| `campaign_id` | `INTEGER` | No | FK $\rightarrow$ `campaigns.id`, CASCADE | Parent campaign |
| `date` | `DATE` | No | — | Activity tracking calendar date |
| `spend` | `NUMERIC(14,2)` | No | Check $\ge 0.00$ | Actual media spend incurred on date |
| `impressions` | `INTEGER` | No | Check $\ge 0$ | Total ad impressions served |
| `clicks` | `INTEGER` | No | Check $\ge 0$ | Total clicks registered |
| `conversions` | `INTEGER` | No | Check $\ge 0$ | Total tracked conversion goals |
| `attributed_revenue` | `NUMERIC(14,2)` | No | Check $\ge 0.00$, Default `0.00` | Revenue attributed to day's events |

### 4.3 `purchase_orders`
| Column | Type | Nullable | Constraints / Default | Description |
| :--- | :--- | :---: | :--- | :--- |
| `id` | `INTEGER` | No | PK, Auto-increment | Purchase order identifier |
| `organization_id` | `INTEGER` | No | FK $\rightarrow$ `organizations.id` | Tenant boundary |
| `supplier_id` | `INTEGER` | No | FK $\rightarrow$ `suppliers.id`, RESTRICT | Fulfilling supplier |
| `warehouse_id` | `INTEGER` | No | FK $\rightarrow$ `warehouses.id`, RESTRICT | Receiving warehouse |
| `po_number` | `VARCHAR(40)` | No | Unique per org | Purchase order code (e.g., `PO-2025-0043`) |
| `order_date` | `TIMESTAMPTZ` | No | — | Purchase order issuance timestamp |
| `expected_delivery_date` | `DATE` | No | — | Promised delivery SLA date |
| `actual_delivery_date` | `DATE` | Yes | — | Actual receipt date |
| `ordered_units` | `INTEGER` | No | Check $> 0$ | Total inventory units ordered |
| `received_units` | `INTEGER` | No | Check $\ge 0$, Default `0` | Actual units received |
| `defective_units` | `INTEGER` | No | Check $\ge 0$, Default `0` | Defective units detected upon QC |
| `total_cost` | `NUMERIC(14,2)` | No | Check $\ge 0.00$ | Total procurement cost payable |
| `status` | `VARCHAR(25)` | No | Check in `('draft', 'issued', 'partially_received', 'received', 'cancelled')` | PO status |
| `created_at` | `TIMESTAMPTZ` | No | Default `CURRENT_TIMESTAMP` | Record creation timestamp |

### 4.4 `expenses` (Operating Expenses / OpEx Ledger)
| Column | Type | Nullable | Constraints / Default | Description |
| :--- | :--- | :---: | :--- | :--- |
| `id` | `INTEGER` | No | PK, Auto-increment | Expense record identifier |
| `organization_id` | `INTEGER` | No | FK $\rightarrow$ `organizations.id` | Tenant boundary |
| `department_id` | `INTEGER` | No | FK $\rightarrow$ `departments.id` | Incurring department |
| `region_id` | `INTEGER` | Yes | FK $\rightarrow$ `regions.id` | Regional division |
| `expense_date` | `DATE` | No | — | Expense posting date |
| `category` | `VARCHAR(50)` | No | Check in `('Payroll', 'Marketing', 'Logistics', 'Facilities', 'IT & SaaS', 'General Admin')` | Operating expense category |
| `amount` | `NUMERIC(14,2)` | No | Check $> 0.00$ | Expense amount posted |
| `description` | `VARCHAR(250)` | Yes | — | Expense description note |
| `created_at` | `TIMESTAMPTZ` | No | Default `CURRENT_TIMESTAMP` | Record creation timestamp |

### 4.5 `budgets`
| Column | Type | Nullable | Constraints / Default | Description |
| :--- | :--- | :---: | :--- | :--- |
| `id` | `INTEGER` | No | PK, Auto-increment | Budget allocation identifier |
| `organization_id` | `INTEGER` | No | FK $\rightarrow$ `organizations.id` | Tenant boundary |
| `department_id` | `INTEGER` | No | FK $\rightarrow$ `departments.id` | Allocated department |
| `region_id` | `INTEGER` | Yes | FK $\rightarrow$ `regions.id` | Allocated region |
| `fiscal_year` | `INTEGER` | No | Check $\ge 2020$ | Fiscal year (e.g., `2025`) |
| `fiscal_quarter` | `INTEGER` | No | Check 1 to 4 | Fiscal quarter (1–4) |
| `metric_target` | `VARCHAR(50)` | No | Check in `('Revenue', 'OpEx', 'Payroll', 'Marketing', 'Logistics')` | Target financial metric |
| `budgeted_amount` | `NUMERIC(14,2)` | No | Check $\ge 0.00$ | Allocated budget threshold |

---

## 5. Platform Governance, RBAC, Data Ops & Analytics Entities

### 5.1 `users`
| Column | Type | Nullable | Constraints / Default | Description |
| :--- | :--- | :---: | :--- | :--- |
| `id` | `INTEGER` | No | PK, Auto-increment | User account identifier |
| `organization_id` | `INTEGER` | No | FK $\rightarrow$ `organizations.id` | Tenant boundary |
| `email` | `VARCHAR(120)` | No | Unique | Account login email |
| `password_hash` | `VARCHAR(255)` | No | — | Argon2 secure password hash |
| `full_name` | `VARCHAR(100)` | No | — | Display full name |
| `is_active` | `BOOLEAN` | No | Default `TRUE` | Account active flag |
| `is_owner` | `BOOLEAN` | No | Default `FALSE` | Owner / Master administrator flag |
| `created_at` | `TIMESTAMPTZ` | No | Default `CURRENT_TIMESTAMP` | Record creation timestamp |

### 5.2 `roles`
| Column | Type | Nullable | Constraints / Default | Description |
| :--- | :--- | :---: | :--- | :--- |
| `id` | `INTEGER` | No | PK, Auto-increment | Role identifier |
| `name` | `VARCHAR(50)` | No | Unique | Role slug (`owner`, `executive`, `data_analyst`, etc.) |
| `display_name` | `VARCHAR(100)` | No | — | Human-readable role title |
| `description` | `TEXT` | Yes | — | Role purpose summary |
| `is_system` | `BOOLEAN` | No | Default `TRUE` | System role flag (protected from deletion) |
| `created_at` | `TIMESTAMPTZ` | No | Default `CURRENT_TIMESTAMP` | Record creation timestamp |

### 5.3 `permissions`
| Column | Type | Nullable | Constraints / Default | Description |
| :--- | :--- | :---: | :--- | :--- |
| `id` | `INTEGER` | No | PK, Auto-increment | Permission identifier |
| `code` | `VARCHAR(80)` | No | Unique | Action permission code (`sales.view`, etc.) |
| `category` | `VARCHAR(50)` | No | — | Functional group (`analytics`, `admin`, etc.) |
| `description` | `TEXT` | Yes | — | Permission description |

### 5.4 `role_permissions`
| Column | Type | Nullable | Constraints / Default | Description |
| :--- | :--- | :---: | :--- | :--- |
| `role_id` | `INTEGER` | No | FK $\rightarrow$ `roles.id`, CASCADE | Parent role |
| `permission_id` | `INTEGER` | No | FK $\rightarrow$ `permissions.id`, CASCADE | Granted permission |
| — | — | — | PK (`role_id`, `permission_id`) | Composite primary key |

### 5.5 `user_roles`
| Column | Type | Nullable | Constraints / Default | Description |
| :--- | :--- | :---: | :--- | :--- |
| `user_id` | `INTEGER` | No | FK $\rightarrow$ `users.id`, CASCADE | Parent user |
| `role_id` | `INTEGER` | No | FK $\rightarrow$ `roles.id`, CASCADE | Assigned role |
| — | — | — | PK (`user_id`, `role_id`) | Composite primary key |

### 5.6 `data_sources`
| Column | Type | Nullable | Constraints / Default | Description |
| :--- | :--- | :---: | :--- | :--- |
| `id` | `INTEGER` | No | PK, Auto-increment | Data source registry identifier |
| `organization_id` | `INTEGER` | No | FK $\rightarrow$ `organizations.id` | Tenant boundary |
| `name` | `VARCHAR(100)` | No | — | Source display title |
| `source_type` | `VARCHAR(30)` | No | Default `'CSV'` | Format / integration type |
| `file_name` | `VARCHAR(255)` | No | — | Original uploaded file name |
| `file_size_bytes` | `BIGINT` | No | Check $\ge 0$ | File size in bytes |
| `file_checksum` | `VARCHAR(64)` | No | — | SHA-256 hash for deduplication/idempotency |
| `uploaded_by_id` | `INTEGER` | No | FK $\rightarrow$ `users.id` | Owner/admin who uploaded |
| `created_at` | `TIMESTAMPTZ` | No | Default `CURRENT_TIMESTAMP` | Record creation timestamp |

### 5.7 `import_jobs`
| Column | Type | Nullable | Constraints / Default | Description |
| :--- | :--- | :---: | :--- | :--- |
| `id` | `INTEGER` | No | PK, Auto-increment | Import execution identifier |
| `data_source_id` | `INTEGER` | No | FK $\rightarrow$ `data_sources.id`, CASCADE | Origin source |
| `target_entity` | `VARCHAR(50)` | No | — | Target table (customers, orders, inventory, etc.) |
| `status` | `VARCHAR(25)` | No | Check in `('queued', 'validating', 'staging', 'cleaning', 'completed', 'failed', 'rolled_back')` | Processing lifecycle state |
| `total_rows` | `INTEGER` | No | Check $\ge 0$, Default `0` | Total rows in source |
| `loaded_rows` | `INTEGER` | No | Check $\ge 0$, Default `0` | Curated rows inserted |
| `rejected_rows` | `INTEGER` | No | Check $\ge 0$, Default `0` | Rows rejected by validation |
| `mapping_config` | `JSONB` | No | Default `'{}'` | Column-to-canonical mapping JSON |
| `error_details` | `JSONB` | Yes | — | Failure details and stack if failed |
| `started_at` | `TIMESTAMPTZ` | Yes | — | Processing start time |
| `completed_at` | `TIMESTAMPTZ` | Yes | — | Processing end time |

### 5.8 `staging_records`
| Column | Type | Nullable | Constraints / Default | Description |
| :--- | :--- | :---: | :--- | :--- |
| `id` | `INTEGER` | No | PK, Auto-increment | Staging row identifier |
| `import_job_id` | `INTEGER` | No | FK $\rightarrow$ `import_jobs.id`, CASCADE | Parent import job |
| `row_number` | `INTEGER` | No | Check $> 0$ | Original row index in source file |
| `raw_data` | `JSONB` | No | — | Unmodified raw row dictionary |
| `cleaned_data` | `JSONB` | Yes | — | Transformed values after cleaning rules |
| `validation_status` | `VARCHAR(20)` | No | Check in `('valid', 'invalid', 'cleaned', 'curated')` | Row validation outcome |
| `issues` | `JSONB` | Yes | — | Array of detected quality issues |

### 5.9 `pipeline_runs`
| Column | Type | Nullable | Constraints / Default | Description |
| :--- | :--- | :---: | :--- | :--- |
| `id` | `INTEGER` | No | PK, Auto-increment | Pipeline run identifier |
| `import_job_id` | `INTEGER` | Yes | FK $\rightarrow$ `import_jobs.id`, SET NULL | Associated import job |
| `pipeline_name` | `VARCHAR(100)` | No | — | Execution name (e.g., Ingestion-Customers) |
| `status` | `VARCHAR(20)` | No | Check in `('running', 'success', 'failed', 'retried')` | Pipeline execution status |
| `duration_ms` | `INTEGER` | Yes | Check $\ge 0$ | Duration in milliseconds |
| `metrics` | `JSONB` | No | Default `'{}'` | Quality scores and row metrics |
| `started_at` | `TIMESTAMPTZ` | No | Default `CURRENT_TIMESTAMP` | Pipeline start time |
| `ended_at` | `TIMESTAMPTZ` | Yes | — | Pipeline completion time |

### 5.10 `saved_views`
| Column | Type | Nullable | Constraints / Default | Description |
| :--- | :--- | :---: | :--- | :--- |
| `id` | `INTEGER` | No | PK, Auto-increment | Saved view identifier |
| `user_id` | `INTEGER` | No | FK $\rightarrow$ `users.id`, CASCADE | Creator user |
| `section` | `VARCHAR(50)` | No | — | Target section (e.g., `sales`, `reports`) |
| `name` | `VARCHAR(100)` | No | — | Preset name (e.g., `Q1 Enterprise High-Value`) |
| `filter_config` | `JSONB` | No | — | Serialized filter parameters JSON |
| `is_shared` | `BOOLEAN` | No | Default `FALSE` | Shared across demo roles |
| `created_at` | `TIMESTAMPTZ` | No | Default `CURRENT_TIMESTAMP` | Record creation timestamp |

### 5.11 `audit_logs` (Append-Only)
| Column | Type | Nullable | Constraints / Default | Description |
| :--- | :--- | :---: | :--- | :--- |
| `id` | `BIGINT` | No | PK, Auto-increment | Audit event sequential identifier |
| `organization_id` | `INTEGER` | Yes | FK $\rightarrow$ `organizations.id` | Tenant boundary |
| `actor_user_id` | `INTEGER` | Yes | FK $\rightarrow$ `users.id`, SET NULL | Actor user ID (null for system/demo) |
| `actor_role` | `VARCHAR(50)` | No | — | Role active during event |
| `action_type` | `VARCHAR(80)` | No | — | Action tag (`login.success`, `csv.import`, etc.) |
| `entity_type` | `VARCHAR(50)` | Yes | — | Target entity (`order`, `user`, `role`, etc.) |
| `entity_id` | `VARCHAR(50)` | Yes | — | Affected record identifier |
| `ip_address` | `VARCHAR(45)` | Yes | — | Client IP address |
| `details` | `JSONB` | Yes | — | Action context and metadata JSON |
| `created_at` | `TIMESTAMPTZ` | No | Default `CURRENT_TIMESTAMP` | Audit timestamp (immutable) |

### 5.12 `anomaly_alerts`
| Column | Type | Nullable | Constraints / Default | Description |
| :--- | :--- | :---: | :--- | :--- |
| `id` | `INTEGER` | No | PK, Auto-increment | Anomaly alert identifier |
| `organization_id` | `INTEGER` | No | FK $\rightarrow$ `organizations.id` | Tenant boundary |
| `domain` | `VARCHAR(40)` | No | Check in `('sales', 'transaction', 'inventory', 'marketing', 'operations')` | Business domain |
| `entity_identifier` | `VARCHAR(100)` | No | — | Target entity reference (SKU, Campaign, Date, Region) |
| `metric_name` | `VARCHAR(80)` | No | — | Analyzed metric (e.g., `daily_revenue`, `unit_depletion`) |
| `observed_value` | `NUMERIC(14,2)` | No | — | Actual calculated value |
| `baseline_value` | `NUMERIC(14,2)` | No | — | Expected historical / seasonal baseline |
| `deviation_amount` | `NUMERIC(14,2)` | No | — | `observed - baseline` |
| `z_score` | `NUMERIC(6,2)` | Yes | — | Normalized standard score |
| `severity` | `VARCHAR(20)` | No | Check in `('low', 'medium', 'high', 'critical')` | Severity classification |
| `explanation` | `TEXT` | No | — | Plain-language reason for alert (never falsely labeled fraud) |
| `status` | `VARCHAR(20)` | No | Check in `('open', 'acknowledged', 'resolved', 'dismissed')` | Workflow state |
| `detected_at` | `TIMESTAMPTZ` | No | Default `CURRENT_TIMESTAMP` | Detection timestamp |
| `acknowledged_at` | `TIMESTAMPTZ` | Yes | — | Acknowledgment timestamp |
| `acknowledged_by_id` | `INTEGER` | Yes | FK $\rightarrow$ `users.id` | Authorized reviewer |
