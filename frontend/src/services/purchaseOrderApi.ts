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

  // Amendment fields (Phase 1 MVP)
  proposed_quantity?: number;
  proposed_quantity_unit?: string;
  amendment_reason?: string;
  amendment_status?: 'none' | 'proposed' | 'approved' | 'rejected';
  amendment_count?: number;
  last_amended_at?: string;

  // ERP integration fields (Phase 2)
  erp_integration_enabled?: boolean;
  erp_sync_status?: 'not_required' | 'pending' | 'synced' | 'failed';
  erp_sync_attempts?: number;
  last_erp_sync_at?: string;
  erp_sync_error?: string;

  created_at: string;
  updated_at: string;
}

export interface Amendment {
  id: string;
  purchase_order_id: string;
  amendment_number: string;
  amendment_type: string;
  status: 'pending' | 'approved' | 'rejected' | 'applied' | 'expired';
  reason: string;
  priority: 'low' | 'medium' | 'high' | 'critical';
  changes: any[];
  proposed_by_company_id: string;
  requires_approval_from_company_id: string;
  proposed_by_user_id: string;
  proposed_at: string;
  approved_at?: string;
  applied_at?: string;
  expires_at?: string;
  notes?: string;
  approval_notes?: string;
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
  amendments?: Amendment[];
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

// Amendment interfaces
export interface ProposeChangesRequest {
  proposed_quantity: number;
  proposed_quantity_unit: string;
  amendment_reason: string;
}

export interface ApproveChangesRequest {
  approve: boolean;
  buyer_notes?: string;
}

export interface AmendmentResponse {
  success: boolean;
  message: string;
  amendment_status: 'none' | 'proposed' | 'approved' | 'rejected';
  purchase_order_id: string;
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
  },

  // Amendment API functions
  proposeChanges: async (id: string, proposal: ProposeChangesRequest): Promise<AmendmentResponse> => {
    const response = await apiClient.put(`/purchase-orders/${id}/propose-changes`, proposal);
    return response.data;
  },

  approveChanges: async (id: string, approval: ApproveChangesRequest): Promise<AmendmentResponse> => {
    const response = await apiClient.put(`/purchase-orders/${id}/approve-changes`, approval);
    return response.data;
  }
};

export default purchaseOrderApi;
