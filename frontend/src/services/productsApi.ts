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
    
    const response = await apiClient.get(`/products?${params.toString()}`);
    return response.data;
  },

  // Get a specific product by ID
  getProduct: async (id: string): Promise<Product> => {
    const response = await apiClient.get(`/products/${id}`);
    return response.data;
  }
};
