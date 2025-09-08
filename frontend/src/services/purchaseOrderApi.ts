import { apiClient } from '../lib/api';

export interface PurchaseOrder {
  id: string;
  po_number: string;
  buyer_company_id: string;
  seller_company_id: string;
  product_id: string;
  quantity: number;
  unit_price: number;
  total_amount: number;
  unit: string;
  delivery_date: string;
  delivery_location: string;
  status: string;
  composition?: Record<string, number>;
  input_materials?: any[];
  origin_data?: any;
  notes?: string;
  
  // Seller confirmation fields
  confirmed_quantity?: number;
  confirmed_unit_price?: number;
  confirmed_delivery_date?: string;
  confirmed_delivery_location?: string;
  seller_notes?: string;
  seller_confirmed_at?: string;
  
  created_at: string;
  updated_at: string;
}

export interface PurchaseOrderWithDetails extends PurchaseOrder {
  buyer_company: {
    id: string;
    name: string;
    company_type: string;
  };
  seller_company: {
    id: string;
    name: string;
    company_type: string;
  };
  product: {
    id: string;
    name: string;
    description: string;
    default_unit: string;
  };
}

export interface PurchaseOrderFilters {
  buyer_company_id?: string;
  seller_company_id?: string;
  product_id?: string;
  status?: string;
  delivery_date_from?: string;
  delivery_date_to?: string;
  search?: string;
  page?: number;
  per_page?: number;
}

export interface PurchaseOrderListResponse {
  purchase_orders: PurchaseOrderWithDetails[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
}

export interface SellerConfirmation {
  confirmed_quantity: number;
  confirmed_unit_price?: number;
  confirmed_delivery_date?: string;
  confirmed_delivery_location?: string;
  seller_notes?: string;
}

export interface PurchaseOrderCreate {
  buyer_company_id: string;
  seller_company_id: string;
  product_id: string;
  quantity: number;
  unit_price: number;
  unit: string;
  delivery_date: string;
  delivery_location: string;
  composition?: Record<string, number>;
  input_materials?: any[];
  origin_data?: any;
  notes?: string;
}

export interface PurchaseOrderUpdate {
  quantity?: number;
  unit_price?: number;
  delivery_date?: string;
  delivery_location?: string;
  status?: string;
  composition?: Record<string, number>;
  input_materials?: any[];
  origin_data?: any;
  notes?: string;
  
  // Seller confirmation fields
  confirmed_quantity?: number;
  confirmed_unit_price?: number;
  confirmed_delivery_date?: string;
  confirmed_delivery_location?: string;
  seller_notes?: string;
}

export const purchaseOrderApi = {
  // Get all purchase orders with filtering
  getPurchaseOrders: async (filters?: PurchaseOrderFilters): Promise<PurchaseOrderListResponse> => {
    const params = new URLSearchParams();
    
    if (filters) {
      Object.entries(filters).forEach(([key, value]) => {
        if (value !== undefined && value !== null && value !== '') {
          params.append(key, value.toString());
        }
      });
    }
    
    const response = await apiClient.get(`/purchase-orders?${params.toString()}`);
    return response.data;
  },

  // Get a specific purchase order by ID
  getPurchaseOrder: async (id: string): Promise<PurchaseOrderWithDetails> => {
    const response = await apiClient.get(`/purchase-orders/${id}`);
    return response.data;
  },

  // Create a new purchase order
  createPurchaseOrder: async (data: PurchaseOrderCreate): Promise<PurchaseOrder> => {
    const response = await apiClient.post('/purchase-orders', data);
    return response.data;
  },

  // Update a purchase order
  updatePurchaseOrder: async (id: string, data: PurchaseOrderUpdate): Promise<PurchaseOrder> => {
    const response = await apiClient.put(`/purchase-orders/${id}`, data);
    return response.data;
  },

  // Seller confirmation of purchase order
  sellerConfirmPurchaseOrder: async (id: string, confirmation: SellerConfirmation): Promise<PurchaseOrder> => {
    const response = await apiClient.post(`/purchase-orders/${id}/seller-confirm`, confirmation);
    return response.data;
  },

  // Delete a purchase order
  deletePurchaseOrder: async (id: string): Promise<void> => {
    await apiClient.delete(`/purchase-orders/${id}`);
  },

  // Get traceability information for a purchase order
  getTraceability: async (id: string): Promise<any> => {
    const response = await apiClient.get(`/purchase-orders/${id}/traceability`);
    return response.data;
  }
};

export default purchaseOrderApi;
