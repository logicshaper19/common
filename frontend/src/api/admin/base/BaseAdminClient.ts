/**
 * Base class for all admin API clients
 * Provides common functionality like request handling and error management
 */
import { apiClient } from '../../../lib/api';
import { RequestOptions, ApiResponse } from './types';

export abstract class BaseAdminClient {
  /**
   * Utility method for adding delays in development/testing
   */
  protected async delay(ms: number = 500): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  /**
   * Make an HTTP request to the backend API
   * Throws error if backend is unavailable - clients should handle fallback
   */
  protected async makeRequest<T>(
    endpoint: string,
    options: RequestOptions = {}
  ): Promise<T> {
    const {
      method = 'GET',
      params,
      data,
      headers = {}
    } = options;

    try {
      let response: { data: T };

      // Use the appropriate HTTP method from apiClient
      switch (method.toUpperCase()) {
        case 'GET':
          response = await apiClient.get<T>(endpoint, { params, headers });
          break;
        case 'POST':
          response = await apiClient.post<T>(endpoint, data, { params, headers });
          break;
        case 'PUT':
          response = await apiClient.put<T>(endpoint, data, { params, headers });
          break;
        case 'DELETE':
          response = await apiClient.delete<T>(endpoint, { params, headers });
          break;
        default:
          throw new Error(`Unsupported HTTP method: ${method}`);
      }

      return response.data;
    } catch (error: any) {
      // Log the error for debugging
      console.warn(`Backend request failed for ${endpoint}:`, error.message);

      // Re-throw to let individual clients handle the error
      throw error;
    }
  }

  /**
   * Build query string from parameters
   */
  protected buildQueryString(params: Record<string, any>): string {
    const searchParams = new URLSearchParams();
    
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') {
        if (Array.isArray(value)) {
          value.forEach(v => searchParams.append(key, v.toString()));
        } else {
          searchParams.append(key, value.toString());
        }
      }
    });
    
    return searchParams.toString();
  }

  /**
   * Handle common error scenarios
   */
  protected handleError(error: any, context: string): never {
    console.error(`Error in ${context}:`, error);
    
    if (error.response?.status === 401) {
      throw new Error('Authentication required');
    } else if (error.response?.status === 403) {
      throw new Error('Insufficient permissions');
    } else if (error.response?.status === 404) {
      throw new Error('Resource not found');
    } else if (error.response?.status >= 500) {
      throw new Error('Server error occurred');
    } else {
      throw new Error(error.message || 'An unexpected error occurred');
    }
  }

  /**
   * Validate required parameters
   */
  protected validateRequired(params: Record<string, any>, requiredFields: string[]): void {
    const missing = requiredFields.filter(field => 
      params[field] === undefined || params[field] === null || params[field] === ''
    );
    
    if (missing.length > 0) {
      throw new Error(`Missing required parameters: ${missing.join(', ')}`);
    }
  }

  /**
   * Sanitize and validate pagination parameters
   */
  protected validatePagination(page: number, perPage: number): { page: number; per_page: number } {
    const validPage = Math.max(1, Math.floor(page) || 1);
    const validPerPage = Math.min(100, Math.max(1, Math.floor(perPage) || 20));
    
    return {
      page: validPage,
      per_page: validPerPage
    };
  }
}
