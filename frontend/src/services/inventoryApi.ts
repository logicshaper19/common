/**
 * Inventory API Service
 * Handles all inventory-related API calls
 */
import { apiClient } from '../lib/api';

export interface InventoryBatch {
  batch_id: string;
  batch_type: string;
  product_id: string;
  product_name?: string;
  product_code?: string;
  quantity: number;
  available_quantity: number;
  allocated_quantity: number;
  unit: string;
  status: string;
  production_date: string;
  expiry_date?: string;
  location_name?: string;
  facility_code?: string;
  quality_metrics?: any;
  batch_metadata?: any;
}

export interface InventoryGroup {
  [key: string]: any;
  batches: InventoryBatch[];
  total_quantity: number;
  batch_count?: number;
}

export interface InventorySummary {
  total_batches: number;
  total_quantity: number;
  available_quantity: number;
  allocated_quantity: number;
  expiring_soon: number;
  status_breakdown: { [status: string]: number };
  type_breakdown: { [type: string]: number };
  product_breakdown: { [productId: string]: number };
}

export interface InventoryFilters {
  status?: string[];
  batch_types?: string[];
  product_ids?: string[];
  facility_ids?: string[];
  production_date_from?: string;
  production_date_to?: string;
  expiry_warning_days?: number | null;
  group_by?: string;
  sort_by?: string;
  sort_order?: string;
  limit?: number;
  offset?: number;
}

export interface InventoryResponse {
  total_count: number;
  limit: number;
  offset: number;
  group_by: string;
  results: InventoryGroup[];
  summary: InventorySummary;
  filters_applied: any;
}

export interface Product {
  id: string;
  name: string;
  code: string;
  description?: string;
}

export const inventoryApi = {
  /**
   * Get inventory with comprehensive filtering
   */
  getInventory: async (filters: InventoryFilters = {}): Promise<InventoryResponse> => {
    const params = new URLSearchParams();
    
    // Add filters to params
    if (filters.status) {
      filters.status.forEach(status => params.append('status', status));
    }
    if (filters.batch_types) {
      filters.batch_types.forEach(type => params.append('batch_types', type));
    }
    if (filters.product_ids) {
      filters.product_ids.forEach(id => params.append('product_ids', id));
    }
    if (filters.facility_ids) {
      filters.facility_ids.forEach(id => params.append('facility_ids', id));
    }
    if (filters.production_date_from) {
      params.append('production_date_from', filters.production_date_from);
    }
    if (filters.production_date_to) {
      params.append('production_date_to', filters.production_date_to);
    }
    if (filters.expiry_warning_days) {
      params.append('expiry_warning_days', filters.expiry_warning_days.toString());
    }
    if (filters.group_by) {
      params.append('group_by', filters.group_by);
    }
    if (filters.sort_by) {
      params.append('sort_by', filters.sort_by);
    }
    if (filters.sort_order) {
      params.append('sort_order', filters.sort_order);
    }
    if (filters.limit) {
      params.append('limit', filters.limit.toString());
    }
    if (filters.offset) {
      params.append('offset', filters.offset.toString());
    }

    try {
      const response = await apiClient.get(`/inventory/?${params.toString()}`);
      
      // Check if response is successful
      if (!response.data) {
        throw new Error('Invalid response from server');
      }
      
      return response.data;
    } catch (error: any) {
      // Enhanced error handling
      if (error.response) {
        // Server responded with error status
        const status = error.response.status;
        const message = error.response.data?.detail || error.response.data?.message || 'Server error';
        
        switch (status) {
          case 401:
            throw new Error('Authentication required. Please log in again.');
          case 403:
            throw new Error('Access denied. You do not have permission to view inventory.');
          case 404:
            throw new Error('Inventory data not found.');
          case 422:
            throw new Error(`Invalid request parameters: ${message}`);
          case 429:
            throw new Error('Too many requests. Please wait a moment and try again.');
          case 500:
            throw new Error('Server error. Please try again later.');
          default:
            throw new Error(`API error (${status}): ${message}`);
        }
      } else if (error.request) {
        // Network error
        throw new Error('Network error. Please check your connection and try again.');
      } else {
        // Other error
        throw new Error(error.message || 'An unexpected error occurred.');
      }
    }
  },

  /**
   * Get inventory summary for dashboard
   */
  getInventorySummary: async (): Promise<{ company_id: string; summary: InventorySummary; last_updated: string }> => {
    try {
      const response = await apiClient.get('/inventory/summary');
      
      if (!response.data) {
        throw new Error('Invalid response from server');
      }
      
      return response.data;
    } catch (error: any) {
      // Enhanced error handling for summary endpoint
      if (error.response) {
        const status = error.response.status;
        const message = error.response.data?.detail || error.response.data?.message || 'Server error';
        
        switch (status) {
          case 401:
            throw new Error('Authentication required. Please log in again.');
          case 403:
            throw new Error('Access denied. You do not have permission to view inventory summary.');
          case 404:
            throw new Error('Inventory summary not found.');
          case 429:
            throw new Error('Too many requests. Please wait a moment and try again.');
          case 500:
            throw new Error('Server error. Please try again later.');
          default:
            throw new Error(`API error (${status}): ${message}`);
        }
      } else if (error.request) {
        throw new Error('Network error. Please check your connection and try again.');
      } else {
        throw new Error(error.message || 'An unexpected error occurred.');
      }
    }
  },

  /**
   * Get products that have inventory
   */
  getInventoryProducts: async (): Promise<{ products: Product[] }> => {
    const response = await apiClient.get('/api/inventory/products');
    return response.data;
  },

  /**
   * Quick filter presets
   */
  getQuickFilters: () => ({
    status: [
      { value: 'available', label: 'Available Stock', color: 'green' },
      { value: 'reserved', label: 'Reserved Stock', color: 'yellow' },
      { value: 'allocated', label: 'Allocated Stock', color: 'blue' },
      { value: 'incoming', label: 'Incoming Stock', color: 'purple' },
      { value: 'sold', label: 'Sold & Shipped', color: 'red' }
    ],
    groupBy: [
      { value: 'product', label: 'By Product' },
      { value: 'facility', label: 'By Facility' },
      { value: 'status', label: 'By Status' },
      { value: 'date', label: 'By Date' }
    ],
    sortBy: [
      { value: 'production_date', label: 'Production Date' },
      { value: 'expiry_date', label: 'Expiry Date' },
      { value: 'quantity', label: 'Quantity' },
      { value: 'batch_id', label: 'Batch ID' }
    ]
  })
};

export default inventoryApi;
