import { CreateSavedViewPayload, ReportCatalogueItem, ReportData, SavedView } from '../types/reports';
import { apiClient, getStoredToken } from './api';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';

export const reportsService = {
  async getCatalogue(): Promise<ReportCatalogueItem[]> {
    return apiClient<ReportCatalogueItem[]>('/api/v1/reports/catalogue');
  },

  async getReportData(
    reportId: string,
    filters?: {
      start_date?: string;
      end_date?: string;
      region_id?: number;
      sales_channel?: string;
      limit?: number;
    },
  ): Promise<ReportData> {
    const search = new URLSearchParams();
    if (filters?.start_date) search.append('start_date', filters.start_date);
    if (filters?.end_date) search.append('end_date', filters.end_date);
    if (filters?.region_id) search.append('region_id', String(filters.region_id));
    if (filters?.sales_channel) search.append('sales_channel', filters.sales_channel);
    if (filters?.limit) search.append('limit', String(filters.limit));
    const qs = search.toString();
    return apiClient<ReportData>(`/api/v1/reports/${reportId}/data${qs ? `?${qs}` : ''}`);
  },

  async downloadCsv(
    reportId: string,
    filters?: {
      start_date?: string;
      end_date?: string;
      region_id?: number;
      sales_channel?: string;
      limit?: number;
    },
  ): Promise<void> {
    const search = new URLSearchParams();
    if (filters?.start_date) search.append('start_date', filters.start_date);
    if (filters?.end_date) search.append('end_date', filters.end_date);
    if (filters?.region_id) search.append('region_id', String(filters.region_id));
    if (filters?.sales_channel) search.append('sales_channel', filters.sales_channel);
    if (filters?.limit) search.append('limit', String(filters.limit));
    const qs = search.toString();

    const token = getStoredToken();
    const headers: Record<string, string> = {};
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(`${API_BASE_URL}/api/v1/reports/${reportId}/export/csv${qs ? `?${qs}` : ''}`, {
      headers,
    });

    if (!response.ok) {
      throw new Error(`Export failed with status ${response.status}`);
    }

    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${reportId}_${new Date().toISOString().slice(0, 10)}.csv`;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
  },

  async listSavedViews(section?: string): Promise<SavedView[]> {
    const qs = section ? `?section=${encodeURIComponent(section)}` : '';
    return apiClient<SavedView[]>(`/api/v1/reports/saved-views${qs}`);
  },

  async createSavedView(payload: CreateSavedViewPayload): Promise<SavedView> {
    return apiClient<SavedView>('/api/v1/reports/saved-views', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  async deleteSavedView(viewId: number): Promise<{ deleted: boolean; id: number }> {
    return apiClient<{ deleted: boolean; id: number }>(`/api/v1/reports/saved-views/${viewId}`, {
      method: 'DELETE',
    });
  },
};
