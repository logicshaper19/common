/**
 * Base class for all admin API clients
 * Provides common functionality like request handling and error management
 */
import { apiClient } from '../../../lib/api';
import { RequestOptions, ApiResponse } from './types';

export abstract class BaseAdminClient {
  /**
   * Simulate network delay for better UX in mock mode
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
      // Use the existing apiClient's request method
      const response = await (apiClient as any).request({
        method,
        url: endpoint,
        params,
        data,
        headers: {
          'Content-Type': 'application/json',
          ...headers
        }
      });

      return response as T;
    } catch (error: any) {
      // Log the error for debugging
      console.warn(`Backend request failed for ${endpoint}:`, error.message);
      
      // Re-throw to let individual clients handle fallback to mock data
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
