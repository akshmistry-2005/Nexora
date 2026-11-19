export interface StandardResponse<T> {
  success: boolean;
  data: T;
  error?: {
    code: string;
    message: string;
    details?: Record<string, unknown>[];
  };
}

export interface PaginationMeta {
  page: number;
  page_size: number;
  total_items: number;
  total_pages: number;
  has_next: boolean;
  has_previous: boolean;
}

export interface PaginatedResponse<T> {
  success: boolean;
  data: T[];
  meta: PaginationMeta;
  error?: {
    code: string;
    message: string;
    details?: Record<string, unknown>[];
  };
}

export type SortDirection = 'asc' | 'desc';

export interface DateRange {
  startDate: string;
  endDate: string;
  preset?: '7d' | '30d' | '90d' | 'ytd' | 'custom';
}
