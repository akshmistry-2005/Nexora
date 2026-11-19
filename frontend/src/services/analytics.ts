import {
  AnalyticsLedgerItem,
  CustomerAnalytics,
  FinanceAnalytics,
  OverviewAnalytics,
  SalesAnalytics,
} from '../types/analytics';
import { PaginatedResponse } from '../types/common';
import { apiClient } from './api';

export const analyticsService = {
  async getOverview(params?: {
    start_date?: string;
    end_date?: string;
    region_id?: number;
  }): Promise<OverviewAnalytics> {
    const search = new URLSearchParams();
    if (params?.start_date) search.append('start_date', params.start_date);
    if (params?.end_date) search.append('end_date', params.end_date);
    if (params?.region_id) search.append('region_id', String(params.region_id));
    const qs = search.toString();
    return apiClient<OverviewAnalytics>(`/api/v1/analytics/overview${qs ? `?${qs}` : ''}`);
  },

  async getSales(params?: {
    start_date?: string;
    end_date?: string;
    region_id?: number;
    sales_channel?: string;
  }): Promise<SalesAnalytics> {
    const search = new URLSearchParams();
    if (params?.start_date) search.append('start_date', params.start_date);
    if (params?.end_date) search.append('end_date', params.end_date);
    if (params?.region_id) search.append('region_id', String(params.region_id));
    if (params?.sales_channel) search.append('sales_channel', params.sales_channel);
    const qs = search.toString();
    return apiClient<SalesAnalytics>(`/api/v1/analytics/sales${qs ? `?${qs}` : ''}`);
  },

  async getCustomers(params?: {
    start_date?: string;
    end_date?: string;
    region_id?: number;
  }): Promise<CustomerAnalytics> {
    const search = new URLSearchParams();
    if (params?.start_date) search.append('start_date', params.start_date);
    if (params?.end_date) search.append('end_date', params.end_date);
    if (params?.region_id) search.append('region_id', String(params.region_id));
    const qs = search.toString();
    return apiClient<CustomerAnalytics>(`/api/v1/analytics/customers${qs ? `?${qs}` : ''}`);
  },

  async getFinance(params?: {
    start_date?: string;
    end_date?: string;
    region_id?: number;
  }): Promise<FinanceAnalytics> {
    const search = new URLSearchParams();
    if (params?.start_date) search.append('start_date', params.start_date);
    if (params?.end_date) search.append('end_date', params.end_date);
    if (params?.region_id) search.append('region_id', String(params.region_id));
    const qs = search.toString();
    return apiClient<FinanceAnalytics>(`/api/v1/analytics/finance${qs ? `?${qs}` : ''}`);
  },

  async getLedger(params?: {
    start_date?: string;
    end_date?: string;
    region_id?: number;
    sales_channel?: string;
    page?: number;
    page_size?: number;
  }): Promise<PaginatedResponse<AnalyticsLedgerItem>> {
    const search = new URLSearchParams();
    if (params?.start_date) search.append('start_date', params.start_date);
    if (params?.end_date) search.append('end_date', params.end_date);
    if (params?.region_id) search.append('region_id', String(params.region_id));
    if (params?.sales_channel) search.append('sales_channel', params.sales_channel);
    if (params?.page) search.append('page', String(params.page));
    if (params?.page_size) search.append('page_size', String(params.page_size));
    const qs = search.toString();
    return apiClient<PaginatedResponse<AnalyticsLedgerItem>>(`/api/v1/analytics/ledger${qs ? `?${qs}` : ''}`);
  },
};
