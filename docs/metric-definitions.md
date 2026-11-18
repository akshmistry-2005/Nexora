# NEXORA — Canonical Data Vocabulary & Metric Definitions

**Document Status:** Approved Baseline (Module 1)  
**Single Source of Truth Principle:** Every KPI and analytical calculation in Nexora MUST be implemented in backend Python/SQL service modules matching the exact formulas documented below. Frontend components must never re-implement business metric formulas independently.

---

## 1. Global Data Conventions & Assumptions

| Convention | Specification |
| :--- | :--- |
| **Base Currency** | `USD` (`$`), stored in PostgreSQL as exact `NUMERIC(14, 2)` (never floating-point binary currency). |
| **Timestamps & Dates** | Stored in PostgreSQL as `TIMESTAMPTZ` in `UTC`; calendar date aggregations (`day`, `month`, `quarter`, `year`) use UTC dates. |
| **Tenant Boundary** | Every business table includes `organization_id` (UUID/INT FK to `organizations`). Initial v1 data belongs to one fictional organization: **Nexora Technologies**. |
| **Synthetic Data Notice** | All baseline datasets are deterministically generated synthetic records. Every dashboard, report, and export displays a synthetic-data indicator. |
| **Qualifying Orders (Revenue)** | Unless explicitly stated otherwise, qualifying sales orders exclude orders with `status = 'cancelled'`. Returned items are deducted via `order_returns.refund_amount` when computing **Net Revenue**. |
| **Tax Treatment** | `tax_amount` is tracked on `orders` for payment reconciliation, but **Gross Revenue** and **Net Revenue** exclude sales tax (standard accounting practice). |
| **Division-by-Zero Policy** | Whenever a denominator is `0` (e.g., `clicks = 0`, `orders = 0`, `budget = 0`), the backend returns `null` (rendered in UI as `—` / `N/A`) rather than `0`, `Infinity`, or `NaN`. |
| **Period-over-Period Comparison** | For a selected date window $[t_{\text{start}}, t_{\text{end}}]$ spanning $D$ days, the default prior period is $[t_{\text{start}} - D, t_{\text{start}} - 1\text{ day}]$. Growth % $= \frac{\text{Current} - \text{Prior}}{|\text{Prior}|} \times 100$ (or `null` if $\text{Prior} = 0$). |

---

## 2. Core Data Vocabulary

| Term | Canonical Definition | Primary Source Table(s) |
| :--- | :--- | :--- |
| **Qualifying Order** | An order whose `status` is in `('completed', 'shipped', 'processing', 'pending', 'returned')` (i.e., `status != 'cancelled'`). | `orders` |
| **Completed Order** | An order with `status = 'completed'` (delivered and not fully cancelled). | `orders` |
| **Active Customer** | A customer with at least 1 qualifying order within the selected analysis period (or within the last 90 days relative to reference date for snapshot KPIs). | `customers`, `orders` |
| **New Customer** | A customer whose first-ever qualifying order (or `signup_date`, clearly labeled by metric) falls inside the selected date range. | `customers`, `orders` |
| **Returning Customer** | A customer placing a qualifying order in the selected date range who already placed at least 1 qualifying order prior to the date range (or $\ge 2$ lifetime orders). | `customers`, `orders` |
| **Churned Customer** | A customer with $\ge 1$ historical qualifying order whose most recent qualifying order occurred $> 90$ days before the reference snapshot date. | `customers`, `orders` |
| **At-Risk Customer** | A customer whose most recent qualifying order occurred between $60$ and $90$ days (inclusive) before the reference snapshot date. | `customers`, `orders` |
| **COGS (Cost of Goods Sold)** | Historical cost of items sold: $\sum (\text{order\_items.quantity} \times \text{order\_items.unit\_cost})$ for qualifying orders, net of returned restocked units where applicable. | `order_items`, `orders`, `order_returns` |
| **Raw / Staging Record** | Unmodified ingested record stored with `import_job_id` and `raw_payload` before cleaning rules are applied. | `staging_records`, `import_jobs` |
| **Curated Record** | Validated, cleaned business record stored in core PostgreSQL tables linked to its originating `data_source_id` / `import_job_id`. | Core business tables |

---

## 3. Business Intelligence Metric Dictionary

### 3.1 Overview & Sales Intelligence Metrics

| Metric | Formula | Unit | Source Table(s) & Columns | Assumptions & Notes |
| :--- | :--- | :---: | :--- | :--- |
| **Gross Revenue** | $\sum (\text{quantity} \times \text{unit\_price})$ where `orders.status != 'cancelled'` | USD | `order_items`, `orders` | Excludes sales tax and cancelled orders; before discounts and refunds. |
| **Total Discounts** | $\sum \text{order\_items.discount\_amount}$ where `orders.status != 'cancelled'` | USD | `order_items`, `orders` | Line-level discounts on qualifying orders. |
| **Total Refunds** | $\sum \text{order\_returns.refund\_amount}$ where `return_status = 'approved'` | USD | `order_returns`, `orders` | Matched by return date (Finance) or order date (Order cohort); default filter uses order date for Sales reconciliation and return date where specified. |
| **Net Revenue** | $\text{Gross Revenue} - \text{Total Discounts} - \text{Total Refunds}$ | USD | `order_items`, `orders`, `order_returns` | Primary headline **Revenue** metric reconciled identically across Overview, Sales, and Finance. |
| **Order Count** | $\text{COUNT}(\text{DISTINCT } \text{orders.id})$ where `status != 'cancelled'` | Count | `orders` | Excludes cancelled orders; total submitted orders (including cancelled) are tracked in Operations. |
| **Units Sold** | $\sum \text{order\_items.quantity}$ where `orders.status != 'cancelled'` | Units | `order_items`, `orders` | Total item units across qualifying orders. |
| **Average Order Value (AOV)** | $\frac{\text{Net Revenue}}{\text{Order Count}}$ | USD | `orders`, `order_items`, `order_returns` | Returns `null` if `Order Count = 0`. |
| **Sales Growth Rate** | $\frac{\text{Net Revenue}_{\text{current}} - \text{Net Revenue}_{\text{prior}}}{|\text{Net Revenue}_{\text{prior}}|} \times 100$ | % | `orders`, `order_items`, `order_returns` | Compared against equal-length immediately preceding period. |
| **Discount Rate** | $\frac{\text{Total Discounts}}{\text{Gross Revenue}} \times 100$ | % | `order_items`, `orders` | Returns `null` if `Gross Revenue = 0`. |

### 3.2 Customer Intelligence Metrics

| Metric | Formula | Unit | Source Table(s) & Columns | Assumptions & Notes |
| :--- | :--- | :---: | :--- | :--- |
| **Total Customers** | $\text{COUNT}(\text{DISTINCT } \text{customers.id})$ | Count | `customers` | Cumulative registered customers up to `end_date`. |
| **New Customers** | $\text{COUNT}(\text{DISTINCT } \text{customers.id})$ where `signup_date` $\in [\text{start}, \text{end}]$ | Count | `customers` | Measures acquisition volume in period. |
| **Active Customers** | $\text{COUNT}(\text{DISTINCT } \text{orders.customer\_id})$ for qualifying orders in period | Count | `orders` | Distinct purchasing customers in selected window. |
| **Inactive Customers** | $\text{Total Customers} - \text{Active Customers}$ | Count | `customers`, `orders` | Customers with zero qualifying orders in selected window. |
| **Repeat Purchase Rate** | $\frac{\text{Customers with } \ge 2 \text{ qualifying orders}}{\text{Customers with } \ge 1 \text{ qualifying order}} \times 100$ | % | `orders` | Evaluated within selected window or lifetime (explicitly labeled). |
| **Purchase Frequency** | $\frac{\text{Order Count}}{\text{Active Customers}}$ | Orders / Customer | `orders` | Average orders per active customer in period. |
| **Average Customer Spend** | $\frac{\text{Net Revenue}}{\text{Active Customers}}$ | USD | `orders`, `order_items`, `order_returns` | Average net revenue per active customer in period. |
| **Customer Retention Rate (Period)** | $\frac{\text{Active customers in both Period } t-1 \text{ and Period } t}{\text{Active customers in Period } t-1} \times 100$ | % | `orders` | Cohort matrix computes retention at Month $+1, +2, \dots, +N$ from first-order month. |
| **Customer Churn Rate (90-Day)** | $\frac{\text{Customers with last qualifying order } > 90 \text{ days ago}}{\text{All customers with } \ge 1 \text{ historical qualifying order}} \times 100$ | % | `orders` | Snapshot evaluated as of `end_date` (or max dataset date). |
| **Historical CLV** | $\sum \text{Net Revenue}_{\text{customer}}$ across all lifetime qualifying orders | USD | `orders`, `order_items`, `order_returns` | Actual observed cumulative net revenue per customer. |
| **Estimated 12-Month CLV** | $\text{AOV} \times \text{Annualized Purchase Frequency} \times \text{Retention Factor}$ | USD | `orders`, `order_items` | Explicitly labeled as a **heuristic estimate** (`Retention Factor` capped at observed cohort retention, max 3 years). |

#### Documented Rule-Based Customer Segmentation Criteria (Evaluated as of Reference Date)
1. **High-Value:** Lifetime Net Spend $\ge \text{P80}$ (top 20% of customers) AND last order $\le 90$ days ago.
2. **At-Risk:** Lifetime orders $\ge 2$ AND last order between $60$ and $90$ days ago.
3. **Inactive / Churned:** Last qualifying order $> 90$ days ago (or signed up $> 90$ days ago with 0 orders).
4. **New:** Signed up $\le 30$ days ago (or first order $\le 30$ days ago with 1 order) and not in High-Value.
5. **Regular:** All remaining active customers (last order $\le 60$ days ago, not High-Value or New).

### 3.3 Marketing Intelligence Metrics

| Metric | Formula | Unit | Source Table(s) & Columns | Assumptions & Notes |
| :--- | :--- | :---: | :--- | :--- |
| **Total Marketing Spend** | $\sum \text{campaign\_events.spend}$ | USD | `campaign_events`, `campaigns` | Actual daily spend recorded across campaigns in date range. |
| **Impressions / Clicks / Conversions** | $\sum \text{impressions}$, $\sum \text{clicks}$, $\sum \text{conversions}$ | Count | `campaign_events` | Summed across filtered campaigns and dates. |
| **Click-Through Rate (CTR)** | $\frac{\text{Clicks}}{\text{Impressions}} \times 100$ | % | `campaign_events` | Returns `null` if `Impressions = 0`. |
| **Conversion Rate (CVR)** | $\frac{\text{Conversions}}{\text{Clicks}} \times 100$ | % | `campaign_events` | Click-to-conversion rate; returns `null` if `Clicks = 0`. |
| **Cost Per Click (CPC)** | $\frac{\text{Total Marketing Spend}}{\text{Clicks}}$ | USD | `campaign_events` | Returns `null` if `Clicks = 0`. |
| **Cost Per Acquisition (CPA)** | $\frac{\text{Total Marketing Spend}}{\text{Conversions}}$ | USD | `campaign_events` | Returns `null` if `Conversions = 0`. |
| **Return on Ad Spend (ROAS)** | $\frac{\sum \text{campaign\_events.attributed\_revenue}}{\text{Total Marketing Spend}}$ | Ratio ($\times$) | `campaign_events` | Uses attributed campaign revenue; returns `null` if `Spend = 0` or `attributed_revenue` missing (explicitly flagged). |

### 3.4 Financial Intelligence Metrics

| Metric | Formula | Unit | Source Table(s) & Columns | Assumptions & Notes |
| :--- | :--- | :---: | :--- | :--- |
| **Net Revenue** | Same as Section 3.1 | USD | `orders`, `order_items`, `order_returns` | Reconciles 1:1 with Overview and Sales Intelligence. |
| **COGS** | $\sum (\text{quantity} \times \text{unit\_cost})$ on qualifying orders (adjusted for restocked returns) | USD | `order_items`, `orders`, `order_returns` | Unit cost frozen at order time on `order_items.unit_cost`. |
| **Gross Profit** | $\text{Net Revenue} - \text{COGS}$ | USD | Derived from above | Never confused with Revenue. |
| **Gross Margin %** | $\frac{\text{Gross Profit}}{\text{Net Revenue}} \times 100$ | % | Derived from above | Returns `null` if `Net Revenue = 0`. |
| **Operating Expenses (OpEx)** | $\sum \text{expenses.amount}$ (includes Marketing Spend, Payroll, Logistics, SaaS/IT, Facilities, Admin) | USD | `expenses` | Clearly tagged as synthetic operational expense ledger; marketing expense rows reconcile with `campaign_events.spend`. |
| **Net Profit (Operating Net Income)** | $\text{Gross Profit} - \text{Operating Expenses}$ | USD | Derived from above | Synthetic pre-tax operating net profit; tax/interest assumptions explicitly stated in UI banner. |
| **Net Margin %** | $\frac{\text{Net Profit}}{\text{Net Revenue}} \times 100$ | % | Derived from above | Returns `null` if `Net Revenue = 0`. |
| **Budget Variance ($)** | $\text{Actual Amount} - \text{Budgeted Amount}$ | USD | `budgets`, `expenses`, `orders` | For Revenue: positive is favorable. For Expenses: negative is favorable (explicitly indicated). |
| **Budget Variance (%)** | $\frac{\text{Actual} - \text{Budget}}{\text{Budget}} \times 100$ | % | `budgets`, `expenses`, `orders` | Returns `null` if `Budget = 0`. |

### 3.5 Inventory Intelligence Metrics

| Metric | Formula | Unit | Source Table(s) & Columns | Assumptions & Notes |
| :--- | :--- | :---: | :--- | :--- |
| **Available Stock Units** | $\sum (\text{quantity\_on\_hand} - \text{quantity\_reserved})$ | Units | `inventory` | Floored at 0 if reserved temporarily equals on-hand. |
| **Inventory Valuation** | $\sum (\text{inventory.quantity\_on\_hand} \times \text{products.unit\_cost})$ | USD | `inventory`, `products` | Valued at standard product unit cost. |
| **Out-of-Stock Products** | $\text{COUNT}(\text{inventory rows where } \text{available\_stock} \le 0)$ | Count | `inventory` | Warehouse-SKU level (and distinct SKU count shown). |
| **Low-Stock Products** | $\text{COUNT}(\text{inventory rows where } 0 < \text{available\_stock} \le \text{reorder\_point})$ | Count | `inventory` | Triggers Reorder Alerts queue. |
| **Inventory Turnover** | $\frac{\text{COGS (period)}}{\text{Average Inventory Valuation}}$ | Ratio ($\times$) | `order_items`, `inventory`, `products` | Annualized when period $< 365$ days (explicitly labeled as annualized). Uses current valuation as proxy when historical daily snapshots are unavailable (documented assumption). |
| **Stock Ageing** | $\text{Reference Date} - \text{inventory.last\_restocked\_at}$ grouped into `0–30d`, `31–60d`, `61–90d`, `90+d` | Days / Buckets | `inventory` | Identifies slow-moving stock across warehouses. |

### 3.6 Operations Intelligence Metrics

| Metric | Formula | Unit | Source Table(s) & Columns | Assumptions & Notes |
| :--- | :--- | :---: | :--- | :--- |
| **Total Orders Processed** | $\text{COUNT}(\text{orders.id})$ across all statuses | Count | `orders` | Includes completed, pending, shipped, cancelled, returned. |
| **Order Fulfilment Rate** | $\frac{\text{Completed + Shipped Orders}}{\text{Total Orders Processed} - \text{Cancelled Orders}} \times 100$ | % | `orders` | Returns `null` if denominator is 0. |
| **Average Fulfilment Time** | $\text{AVG}(\text{shipped\_at} - \text{order\_date})$ | Hours / Days | `orders` | Computed over orders with non-null `shipped_at`. |
| **Average Delivery Time** | $\text{AVG}(\text{delivered\_at} - \text{order\_date})$ | Days | `orders` | Computed over orders with non-null `delivered_at`. |
| **On-Time Delivery Rate (SLA)** | $\frac{\text{Orders where } \text{delivered\_at} \le \text{promised\_delivery\_at}}{\text{Orders with non-null } \text{delivered\_at}} \times 100$ | % | `orders` | SLA threshold defined per order via `promised_delivery_at`. |
| **Order Return Rate** | $\frac{\text{COUNT(DISTINCT order\_returns.order\_id)}}{\text{Qualifying Order Count}} \times 100$ | % | `order_returns`, `orders` | Percentage of qualifying orders with an approved/logged return. |
| **Cancellation Rate** | $\frac{\text{Cancelled Orders}}{\text{Total Orders Processed}} \times 100$ | % | `orders` | Percentage of all submitted orders cancelled. |

### 3.7 Supplier Intelligence Metrics

| Metric | Formula | Unit | Source Table(s) & Columns | Assumptions & Notes |
| :--- | :--- | :---: | :--- | :--- |
| **Total Supplier Spend** | $\sum \text{purchase\_orders.total\_cost}$ where `status != 'cancelled'` | USD | `purchase_orders` | Total procurement spend in date range. |
| **Average Supplier Lead Time** | $\text{AVG}(\text{actual\_delivery\_date} - \text{order\_date})$ | Days | `purchase_orders` | Computed over received POs (`actual_delivery_date IS NOT NULL`). |
| **Supplier On-Time Delivery Rate** | $\frac{\text{POs where } \text{actual\_delivery\_date} \le \text{expected\_delivery\_date}}{\text{Received POs}} \times 100$ | % | `purchase_orders` | Measures supplier schedule reliability. |
| **Supplier Defect Rate** | $\frac{\sum \text{purchase\_orders.defective\_units}}{\sum \text{purchase\_orders.received\_units}} \times 100$ | % | `purchase_orders` | Returns `null` if `received_units = 0`. |

---

## 4. Data Quality Dimensions (Module 8)

Each dimension is computed on a 0–100% scale from explicit rule evaluations over staged/imported records:

| Dimension | Formula | Description |
| :--- | :--- | :--- |
| **Completeness** | $\left(1 - \frac{\text{Missing required cells}}{\text{Total required cells}}\right) \times 100$ | Measures presence of non-null, non-empty required values. |
| **Validity** | $\left(1 - \frac{\text{Type / format / range / FK rule violations}}{\text{Total evaluated field checks}}\right) \times 100$ | Measures conformance to dates, numeric ranges, and referential integrity. |
| **Uniqueness** | $\left(1 - \frac{\text{Duplicate records beyond first occurrence}}{\text{Total records}}\right) \times 100$ | Measures absence of duplicate business keys or exact duplicate rows. |
| **Consistency** | $\left(1 - \frac{\text{Category/casing/whitespace/cross-field inconsistencies}}{\text{Total consistency checks}}\right) \times 100$ | Measures adherence to canonical categories and cross-field logic (e.g., `shipped_at >= order_date`). |
| **Timeliness** | Percentage of records within configured freshness SLA (or `100%` when latest timestamp is within expected freshness window, decaying per documented SLA lag rule). | Measures data freshness relative to expected ingestion cadence. |
| **Overall Quality Score** | Weighted average: `0.25*Completeness + 0.25*Validity + 0.20*Uniqueness + 0.20*Consistency + 0.10*Timeliness` | Clearly displayed alongside individual dimension scores so no single weakness is hidden. |

---

## 5. Statistical, ML & Anomaly Evaluation Metrics (Modules 11–13)

| Domain | Metric / Convention | Specification |
| :--- | :--- | :--- |
| **Descriptive Stats** | Sample Variance & SD (`ddof=1` default, `ddof=0` optional); Quartiles via linear interpolation (`numpy.percentile` default); Multi-mode returns all tied modes or explicitly notes "no unique mode". | Always reports `n_total`, `n_valid`, `n_missing` alongside statistics. |
| **Correlation & Regression** | Pearson $r$ (linear, continuous) & Spearman $\rho$ (monotonic/rank) with two-sided $p$-values; OLS $R^2$, Adj. $R^2$, coefficients, SE, $p$-values. | UI & API always include explicit guardrail: *"Correlation measures association and does not establish causation."* |
| **Confidence Intervals** | Two-sided $(1-\alpha)$ CI for mean using Student's $t$-distribution (`scipy.stats.t.interval`, default 95%). | Requires $n \ge 2$; rejects/warns on insufficient sample size. |
| **Forecasting / Regression ML** | **MAE** $= \frac{1}{n}\sum|y_i - \hat{y}_i|$, **RMSE** $= \sqrt{\frac{1}{n}\sum(y_i - \hat{y}_i)^2}$, **MAPE** (where $y_i > 0$). | Evaluated strictly on **temporal held-out test split** (no random shuffling on time series) and compared against a naive/seasonal baseline. |
| **Classification ML (Churn)** | **Precision**, **Recall**, **F1-Score**, **ROC-AUC**, Confusion Matrix. | Evaluated strictly on held-out test set constructed with temporal cutoff to prevent target leakage; compared against majority/logistic baseline. |
| **Anomaly Detection** | **Deviation** $= \text{Observed} - \text{Baseline}$; **Z-Score** $= \frac{\text{Observed} - \mu_{\text{baseline}}}{\sigma_{\text{baseline}}}$; **Severity Thresholds:** Low ($|z| \in [2.0, 2.5)$), Medium ($[2.5, 3.0)$), High ($[3.0, 4.0)$), Critical ($\ge 4.0$). | Minimum-volume floor prevents noisy alerts on tiny denominators. Alerts never label anomalies as "fraud" automatically. |
