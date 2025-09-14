/**
 * API client for Common Supply Chain Platform
 * Handles communication with FastAPI backend
 */
import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios';

// API Configuration
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://127.0.0.1:8000';
const API_VERSION = 'v1';

// Types
export interface ApiResponse<T = any> {
  data: T;
  message?: string;
  status: string;
}

export interface ApiError {
  error: {
    code: string;
    message: string;
    details?: any[];
  };
  request_id: string;
  timestamp: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  access_expires_in: number;
  refresh_expires_in: number;
}

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: string;
  is_active: boolean;
  company: Company;
  sectorId?: string;
  tierLevel?: number;
  sector_id?: string;
  tier_level?: number;
  permissions?: string[];
}

export interface Company {
  id: string;
  name: string;
  company_type: 'brand' | 'processor' | 'originator' | 'plantation' | 'plantation_grower' | 'smallholder_cooperative' | 'mill_processor' | 'refinery_crusher' | 'trader_aggregator' | 'oleochemical_producer' | 'manufacturer';
  email: string;
  phone?: string;
  address?: string;
  country?: string;
  website?: string;
  description?: string;
}

export interface Product {
  id: string;
  common_product_id: string;
  name: string;
  category: 'raw_material' | 'processed' | 'finished_good';
  description?: string;
  hs_code?: string;
  default_unit: string;
  can_have_composition: boolean;
  sustainability_certifications: string[];
  origin_data_requirements: Record<string, any>;
}

export interface PurchaseOrder {
  id: string;
  buyer_company_id: string;
  seller_company_id: string;
  product_id: string;
  quantity: number;
  unit: string;
  status: 'draft' | 'pending' | 'confirmed' | 'shipped' | 'delivered' | 'cancelled';
  delivery_date?: string;
  notes?: string;
  confirmed_quantity?: number;
  confirmation_notes?: string;
  created_at: string;
  updated_at: string;
  confirmed_at?: string;
  buyer_company?: Company;
  seller_company?: Company;
  product?: Product;
}

export interface TransparencyScore {
  id: string;
  purchase_order_id: string;
  transparency_to_mill?: number;
  transparency_to_plantation?: number;
  calculation_metadata: Record<string, any>;
  calculated_at: string;
}



// API Client Class
class ApiClient {
  private client: AxiosInstance;
  private token: string | null = null;

  constructor() {
    this.client = axios.create({
      baseURL: `${API_BASE_URL}/api/${API_VERSION}`,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Load token from localStorage on initialization
    this.loadToken();

  // Request interceptor to add auth token
  this.client.interceptors.request.use(
    (config) => {
      if (this.token) {
        config.headers.Authorization = `Bearer ${this.token}`;
      }
      return config;
    },
    (error) => {
      return Promise.reject(error);
    }
  );

    // Response interceptor for error handling
    this.client.interceptors.response.use(
      (response: AxiosResponse) => {
        return response;
      },
      (error) => {
        if (error.response?.status === 401) {
          // Token expired or invalid
          this.clearToken();
          window.location.href = '/login';
        }
        return Promise.reject(error);
      }
    );

    // Load token from localStorage on initialization
    this.loadToken();
  }

  // Token management
  setToken(token: string): void {
    this.token = token;
    localStorage.setItem('auth_token', token);
  }

  clearToken(): void {
    this.token = null;
    localStorage.removeItem('auth_token');
    localStorage.removeItem('refresh_token');
  }

  getToken(): string | null {
    return this.token;
  }

  private loadToken(): void {
    const token = localStorage.getItem('auth_token');
    if (token) {
      this.token = token;
    }
  }

  // Generic request method
  private async request<T>(config: AxiosRequestConfig): Promise<T> {
    try {
      const response = await this.client.request<T>(config);
      return response.data;
    } catch (error: any) {
      if (error.response?.data) {
        throw error.response.data as ApiError;
      }
      throw {
        error: {
          code: 'NETWORK_ERROR',
          message: 'Network error occurred',
        },
        request_id: 'unknown',
        timestamp: new Date().toISOString(),
      } as ApiError;
    }
  }

  // Public HTTP methods
  async get<T = any>(url: string, config?: AxiosRequestConfig): Promise<{ data: T }> {
    const response = await this.client.get<T>(url, config);
    return { data: response.data };
  }

  async post<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<{ data: T }> {
    const response = await this.client.post<T>(url, data, config);
    return { data: response.data };
  }

  async put<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<{ data: T }> {
    const response = await this.client.put<T>(url, data, config);
    return { data: response.data };
  }

  async delete<T = any>(url: string, config?: AxiosRequestConfig): Promise<{ data: T }> {
    const response = await this.client.delete<T>(url, config);
    return { data: response.data };
  }

  // Authentication endpoints
  async login(credentials: LoginRequest): Promise<LoginResponse> {
    const response = await this.request<LoginResponse>({
      method: 'POST',
      url: '/auth/login',
      data: {
        email: credentials.email,
        password: credentials.password,
      },
    });

    this.setToken(response.access_token);
    // Store refresh token for future use
    localStorage.setItem('refresh_token', response.refresh_token);
    return response;
  }



  async logout(): Promise<void> {
    try {
      await this.request({
        method: 'POST',
        url: '/auth/logout',
      });
    } finally {
      this.clearToken();
    }
  }

  async getCurrentUser(): Promise<User> {
    return this.request<User>({
      method: 'GET',
      url: '/auth/me',
    });
  }

  // Company endpoints
  async getCompanies(): Promise<Company[]> {
    return this.request<Company[]>({
      method: 'GET',
      url: '/companies',
    });
  }

  async getCompany(id: string): Promise<Company> {
    return this.request<Company>({
      method: 'GET',
      url: `/companies/${id}`,
    });
  }

  // Product endpoints
  async getProducts(): Promise<Product[]> {
    return this.request<Product[]>({
      method: 'GET',
      url: '/products',
    });
  }

  async getProduct(id: string): Promise<Product> {
    return this.request<Product>({
      method: 'GET',
      url: `/products/${id}`,
    });
  }

  // Purchase Order endpoints
  async getPurchaseOrders(): Promise<PurchaseOrder[]> {
    return this.request<PurchaseOrder[]>({
      method: 'GET',
      url: '/purchase-orders',
    });
  }

  async getPurchaseOrder(id: string): Promise<PurchaseOrder> {
    return this.request<PurchaseOrder>({
      method: 'GET',
      url: `/purchase-orders/${id}`,
    });
  }

  async createPurchaseOrder(data: Partial<PurchaseOrder>): Promise<PurchaseOrder> {
    return this.request<PurchaseOrder>({
      method: 'POST',
      url: '/purchase-orders',
      data,
    });
  }

  async updatePurchaseOrder(id: string, data: Partial<PurchaseOrder>): Promise<PurchaseOrder> {
    return this.request<PurchaseOrder>({
      method: 'PUT',
      url: `/purchase-orders/${id}`,
      data,
    });
  }

  async confirmPurchaseOrder(id: string, data: {
    confirmed_quantity: number;
    input_materials?: Array<{
      source_po_id: string;
      quantity_used: number;
      percentage_contribution: number;
    }>;
    quality_notes?: string;
    processing_notes?: string;
  }): Promise<PurchaseOrder> {
    return this.request<PurchaseOrder>({
      method: 'POST',
      url: `/purchase-orders/${id}/confirm`,
      data,
    });
  }

  // Transparency endpoints
  async getTransparencyScore(purchaseOrderId: string): Promise<TransparencyScore> {
    return this.request<TransparencyScore>({
      method: 'GET',
      url: `/transparency/${purchaseOrderId}`,
    });
  }

  async getDetailedTransparency(purchaseOrderId: string): Promise<any> {
    return this.request<any>({
      method: 'GET',
      url: `/transparency/${purchaseOrderId}/detailed`,
    });
  }

  // Health check
  async healthCheck(): Promise<{ status: string; timestamp: string }> {
    return this.request<{ status: string; timestamp: string }>({
      method: 'GET',
      url: '/health',
    });
  }
}

// Export singleton instance
export const apiClient = new ApiClient();
export default apiClient;
