export interface OverviewAnalytics {
  net_revenue: number;
  total_orders: number;
  total_customers: number;
  active_customers: number;
  average_order_value: number;
  gross_profit: number;
  gross_margin_pct: number;
  total_expenses: number;
  net_profit: number;
  net_margin_pct: number;
  inventory_valuation: number;
  fulfilment_rate: number;
  marketing_spend: number;
  revenue_trend: { month: string; revenue: number; orders: number }[];
  regional_breakdown: { region: string; revenue: number; orders: number }[];
  top_products: { name: string; revenue: number; units: number }[];
}

export interface SalesAnalytics {
  gross_revenue: number;
  total_discounts: number;
  total_refunds: number;
  net_revenue: number;
  order_count: number;
  units_sold: number;
  aov: number;
  discount_rate_pct: number;
  channel_breakdown: { channel: string; revenue: number; orders: number }[];
  regional_breakdown: { region: string; revenue: number; orders: number }[];
  category_breakdown: { category: string; revenue: number; units: number }[];
  monthly_trend: { month: string; revenue: number; orders: number }[];
  sales_rep_leaderboard: { rep_name: string; revenue: number; orders: number }[];
}

export interface CustomerAnalytics {
  total_customers: number;
  active_customers: number;
  new_customers: number;
  churn_count: number;
  churn_rate_pct: number;
  arpu: number;
  segment_breakdown: { segment: string; count: number }[];
  acquisition_breakdown: { channel: string; count: number }[];
  regional_breakdown: { region: string; count: number }[];
  top_customers: { name: string; company: string; spend: number; orders: number }[];
}

export interface FinanceAnalytics {
  net_revenue: number;
  cogs: number;
  gross_profit: number;
  gross_margin_pct: number;
  operating_expenses: number;
  net_profit: number;
  net_margin_pct: number;
  total_allocated_budget: number;
  total_actual_spend: number;
  budget_variance_amount: number;
  budget_variance_pct: number;
  expense_categories: { category: string; amount: number }[];
  department_budgets: { department: string; budget: number; actual: number; variance: number }[];
}

export interface AnalyticsLedgerItem extends Record<string, unknown> {
  id: number;
  order_number: string;
  customer_name: string;
  sales_channel: string;
  order_date: string;
  status: string;
  region: string;
  total_amount: number;
}
