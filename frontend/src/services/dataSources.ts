import { DataSource, ImportJob, ImportResultResponse, PreviewResponse } from '../types/dataSources';
import { apiClient } from './api';

export const dataSourcesService = {
  async uploadPreview(file: File, targetEntity: string): Promise<PreviewResponse> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('target_entity', targetEntity);

    return apiClient<PreviewResponse>('/api/v1/data-sources/upload-preview', {
      method: 'POST',
      body: formData,
    });
  },

  async importData(
    file: File,
    targetEntity: string,
    customMapping?: Record<string, string>,
    allowDuplicate = false,
  ): Promise<ImportResultResponse> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('target_entity', targetEntity);
    formData.append('allow_duplicate', String(allowDuplicate));

    if (customMapping) {
      formData.append('custom_mapping', JSON.stringify(customMapping));
    }

    return apiClient<ImportResultResponse>('/api/v1/data-sources/import', {
      method: 'POST',
      body: formData,
    });
  },

  async getImportHistory(page = 1, pageSize = 10): Promise<ImportJob[]> {
    return apiClient<ImportJob[]>(
      `/api/v1/data-sources/history?page=${page}&page_size=${pageSize}`,
    );
  },

  async getDataSources(page = 1, pageSize = 10): Promise<DataSource[]> {
    return apiClient<DataSource[]>(
      `/api/v1/data-sources/?page=${page}&page_size=${pageSize}`,
    );
  },
};
