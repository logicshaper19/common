/**
 * Base class for mock data providers
 * Provides common functionality for filtering, pagination, and search
 */
import { PaginatedResponse, MockProviderOptions } from '../base/types';

export abstract class MockDataProvider {
  protected options: MockProviderOptions;

  constructor(options: MockProviderOptions = {}) {
    this.options = {
      enableDelay: true,
      delayMs: 300,
      ...options
    };
  }

  /**
   * Simulate API delay for better UX
   */
  protected async delay(): Promise<void> {
    if (this.options.enableDelay) {
      return new Promise(resolve => 
        setTimeout(resolve, this.options.delayMs)
      );
    }
  }

  /**
   * Apply pagination to a dataset
   */
  protected applyPagination<T>(
    items: T[], 
    page: number, 
    perPage: number
  ): PaginatedResponse<T> {
    const validPage = Math.max(1, page);
    const validPerPage = Math.min(100, Math.max(1, perPage));
    
    const startIndex = (validPage - 1) * validPerPage;
    const endIndex = startIndex + validPerPage;
    const totalPages = Math.ceil(items.length / validPerPage);
    
    return {
      data: items.slice(startIndex, endIndex),
      total: items.length,
      page: validPage,
      per_page: validPerPage,
      total_pages: totalPages
    };
  }

  /**
   * Apply search filter to items
   */
  protected applySearch<T>(
    items: T[],
    search: string,
    searchFields: (keyof T)[]
  ): T[] {
    if (!search || !search.trim()) {
      return items;
    }
    
    const searchLower = search.toLowerCase().trim();
    
    return items.filter(item =>
      searchFields.some(field => {
        const value = item[field];
        if (value === null || value === undefined) {
          return false;
        }
        return String(value).toLowerCase().includes(searchLower);
      })
    );
  }

  /**
   * Apply date range filter
   */
  protected applyDateRange<T>(
    items: T[],
    dateField: keyof T,
    startDate?: string,
    endDate?: string
  ): T[] {
    if (!startDate && !endDate) {
      return items;
    }

    return items.filter(item => {
      const itemDate = item[dateField] as string;
      if (!itemDate) return false;

      const date = new Date(itemDate);
      
      if (startDate && date < new Date(startDate)) {
        return false;
      }
      
      if (endDate && date > new Date(endDate)) {
        return false;
      }
      
      return true;
    });
  }

  /**
   * Apply enum filter (status, category, etc.)
   */
  protected applyEnumFilter<T>(
    items: T[],
    field: keyof T,
    value?: string | string[]
  ): T[] {
    if (!value) {
      return items;
    }

    const values = Array.isArray(value) ? value : [value];
    
    return items.filter(item => {
      const itemValue = item[field];
      return values.includes(itemValue as string);
    });
  }

  /**
   * Apply boolean filter
   */
  protected applyBooleanFilter<T>(
    items: T[],
    field: keyof T,
    value?: boolean
  ): T[] {
    if (value === undefined) {
      return items;
    }

    return items.filter(item => item[field] === value);
  }

  /**
   * Apply numeric range filter
   */
  protected applyNumericRange<T>(
    items: T[],
    field: keyof T,
    min?: number,
    max?: number
  ): T[] {
    if (min === undefined && max === undefined) {
      return items;
    }

    return items.filter(item => {
      const value = item[field] as number;
      if (typeof value !== 'number') return false;

      if (min !== undefined && value < min) return false;
      if (max !== undefined && value > max) return false;

      return true;
    });
  }

  /**
   * Sort items by field
   */
  protected applySorting<T>(
    items: T[],
    sortBy?: keyof T,
    sortOrder: 'asc' | 'desc' = 'asc'
  ): T[] {
    if (!sortBy) {
      return items;
    }

    return [...items].sort((a, b) => {
      const aValue = a[sortBy];
      const bValue = b[sortBy];

      // Handle null/undefined values
      if (aValue === null || aValue === undefined) return 1;
      if (bValue === null || bValue === undefined) return -1;

      // Handle different data types
      if (typeof aValue === 'string' && typeof bValue === 'string') {
        const result = aValue.localeCompare(bValue);
        return sortOrder === 'asc' ? result : -result;
      }

      if (typeof aValue === 'number' && typeof bValue === 'number') {
        const result = aValue - bValue;
        return sortOrder === 'asc' ? result : -result;
      }

      if (aValue instanceof Date && bValue instanceof Date) {
        const result = aValue.getTime() - bValue.getTime();
        return sortOrder === 'asc' ? result : -result;
      }

      // Fallback to string comparison
      const result = String(aValue).localeCompare(String(bValue));
      return sortOrder === 'asc' ? result : -result;
    });
  }

  /**
   * Generate a new ID for mock data
   */
  protected generateId(prefix: string = 'item'): string {
    return `${prefix}-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * Get current timestamp in ISO format
   */
  protected getCurrentTimestamp(): string {
    return new Date().toISOString();
  }

  /**
   * Deep clone an object
   */
  protected deepClone<T>(obj: T): T {
    return JSON.parse(JSON.stringify(obj));
  }
}
