/**
 * Common types and interfaces for admin API clients
 */

export interface RequestOptions {
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH';
  params?: Record<string, any>;
  data?: any;
  headers?: Record<string, string>;
}

export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
}

export interface ApiResponse<T = any> {
  data: T;
  message?: string;
  status: string;
}

export interface BulkOperationResult {
  success: boolean;
  affected_count: number;
  errors?: string[];
}

export interface FilterBase {
  page: number;
  per_page: number;
  search?: string;
}

export interface MockProviderOptions {
  enableDelay?: boolean;
  delayMs?: number;
}
