import { apiClient } from '../lib/api';

export interface Product {
  id: string;
  name: string;
  common_product_id: string;
  category: string;
  default_unit: string;
  description?: string;
  can_have_composition: boolean;
  hs_code?: string;
  created_at: string;
  updated_at: string;
}

export interface ProductListResponse {
  products: Product[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
}

export interface ProductFilter {
  category?: string;
  can_have_composition?: boolean;
  search?: string;
  page?: number;
  per_page?: number;
}

export const productsApi = {
  // Get all products with filtering
  getProducts: async (filters?: ProductFilter): Promise<ProductListResponse> => {
    const params = new URLSearchParams();
    
    if (filters) {
      Object.entries(filters).forEach(([key, value]) => {
        if (value !== undefined && value !== null && value !== '') {
          params.append(key, value.toString());
        }
      });
    }
    
    console.log('📦 Fetching products...');
    const response = await apiClient.get(`/products?${params.toString()}`);
    console.log('📦 Raw response:', response);
    
    // Handle the unusual array format from the backend
    if (response.data.data && Array.isArray(response.data.data)) {
      // Convert array of key-value pairs to object
      const dataObj: Record<string, any> = {};
      response.data.data.forEach(([key, value]: [string, any]) => {
        dataObj[key] = value;
      });
      
      const result = {
        products: dataObj.products || [],
        total: dataObj.total || 0,
        page: dataObj.page || 1,
        per_page: dataObj.per_page || 20,
        total_pages: dataObj.total_pages || 1
      };
      console.log('📦 Transformed products (array format):', result);
      return result;
    }
    
    // Handle new standardized response format
    if (response.data.data && response.data.meta?.pagination) {
      const pagination = response.data.meta.pagination;
      const result = {
        products: response.data.data,
        total: pagination.total,
        page: pagination.page,
        per_page: pagination.per_page,
        total_pages: pagination.total_pages
      };
      console.log('📦 Transformed products (new format):', result);
      return result;
    }
    
    // Fallback to old format
    console.log('📦 Using old format:', response.data);
    return response.data;
  },

  // Get a specific product by ID
  getProduct: async (id: string): Promise<Product> => {
    const response = await apiClient.get(`/products/${id}`);
    return response.data;
  }
};
