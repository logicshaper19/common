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
  
  // Commercial chain linking
  parent_po_id?: string;
  is_drop_shipment?: boolean;
  
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

  // Delivery tracking fields
  delivery_status?: 'pending' | 'in_transit' | 'delivered' | 'failed';
  delivered_at?: string;
  delivery_confirmed_by?: string;
  delivery_notes?: string;

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
    category: string;
  };
  amendments?: Amendment[];
}

// Extended interface for components that need the related objects
export interface PurchaseOrderWithRelations extends PurchaseOrder {
  buyer_company?: {
    id: string;
    name: string;
    company_type: string;
  };
  seller_company?: {
    id: string;
    name: string;
    company_type: string;
  };
  product?: {
    id: string;
    name: string;
    description: string;
    default_unit: string;
    category: string;
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
  // Commercial chain linking
  parent_po_id?: string;
  is_drop_shipment?: boolean;
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
  proposed_quantity?: number;
  proposed_quantity_unit?: string;
  proposed_delivery_date?: string;
  proposed_delivery_location?: string;
  amendment_reason: string;
  amendment_type?: 'quantity_change' | 'delivery_date_change' | 'delivery_location_change';
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

export interface PurchaseOrderConfirmation {
  delivery_date?: string;
  notes?: string;
  confirmed_quantity?: number;
  confirmed_unit?: string;
  confirmed_unit_price?: number;
  delivery_location?: string;
  stock_batches?: Array<{
    batch_id: string;
    quantity_to_use: number;
  }>;
}

export interface ConfirmationResponse {
  success: boolean;
  message: string;
  purchase_order_id: string;
  status: string;
  confirmed_at?: string;
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
    
    const response = await apiClient.get(`/purchase-orders/?${params.toString()}`);
    return response.data;
  },

  // Get a specific purchase order by ID
  getPurchaseOrder: async (id: string): Promise<PurchaseOrderWithDetails> => {
    const response = await apiClient.get(`/purchase-orders/${id}`);
    return response.data;
  },

  // Create a new purchase order
  createPurchaseOrder: async (data: PurchaseOrderCreate): Promise<PurchaseOrder> => {
    console.log('📤 Sending purchase order data to API:', data);
    const response = await apiClient.post('/purchase-orders/', data);
    console.log('📥 Purchase order created successfully:', response.data);
    return response.data;
  },

  // Get incoming purchase orders (where current user's company is the SELLER - orders to fulfill)
  getIncomingPurchaseOrders: async (): Promise<PurchaseOrderWithRelations[]> => {
    // Use the simple API endpoint that exists
    const response = await apiClient.get('/purchase-orders', {
      params: {
        per_page: 100,
        sort_by: 'created_at',
        sort_order: 'desc'
      }
    });
    
    const allOrders = response.data?.purchase_orders || [];
    
    // Get current user's company ID from localStorage (stored by AuthContext)
    const userData = localStorage.getItem('user_data');
    const currentUserCompanyId = userData ? JSON.parse(userData).company?.id : null;
    
    // Also try to get from auth_token if user_data doesn't work
    const token = localStorage.getItem('auth_token');
    let fallbackCompanyId = null;
    if (token && !currentUserCompanyId) {
      try {
        // Decode JWT token to get user info
        const payload = JSON.parse(atob(token.split('.')[1]));
        fallbackCompanyId = payload.company_id;
      } catch (e) {
        console.log('Could not decode token for company ID');
      }
    }
    
    const finalCompanyId = currentUserCompanyId || fallbackCompanyId;
    
    console.log('🔍 getIncomingPurchaseOrders - Debug Info:');
    console.log('  Current User Company ID (from user_data):', currentUserCompanyId);
    console.log('  Fallback Company ID (from token):', fallbackCompanyId);
    console.log('  Final Company ID:', finalCompanyId);
    console.log('  Total POs fetched:', allOrders.length);
    console.log('  All POs:', allOrders.map((po: any) => ({ 
      po_number: po.po_number, 
      seller_company_id: po.seller_company_id, 
      buyer_company_id: po.buyer_company_id,
      status: po.status,
      // Show all available properties
      all_properties: Object.keys(po)
    })));
    
    // Filter for incoming orders (where current user's company is the SELLER)
    // and status is pending (not confirmed, rejected, etc.)
    const incomingOrders = allOrders.filter((po: any) => {
      // Try different possible property names for company IDs
      const sellerCompanyId = po.seller_company_id || po.sellerCompanyId || po.seller_company?.id;
      const buyerCompanyId = po.buyer_company_id || po.buyerCompanyId || po.buyer_company?.id;
      
      const isIncoming = buyerCompanyId && sellerCompanyId; // Has both buyer and seller
      const isCurrentUserSeller = finalCompanyId && sellerCompanyId === finalCompanyId;
      const isPending = po.status && 
        (po.status.toLowerCase() === 'pending' || 
         po.status.toLowerCase() === 'awaiting_acceptance' ||
         po.status.toLowerCase() === 'awaiting_confirmation');
      
      console.log(`  PO ${po.po_number}: isIncoming=${isIncoming}, isCurrentUserSeller=${isCurrentUserSeller}, isPending=${isPending}`);
      console.log(`    - po.seller_company_id: ${po.seller_company_id}`);
      console.log(`    - po.sellerCompanyId: ${po.sellerCompanyId}`);
      console.log(`    - po.seller_company?.id: ${po.seller_company?.id}`);
      console.log(`    - sellerCompanyId (final): ${sellerCompanyId}`);
      console.log(`    - po.buyer_company_id: ${po.buyer_company_id}`);
      console.log(`    - po.buyerCompanyId: ${po.buyerCompanyId}`);
      console.log(`    - po.buyer_company?.id: ${po.buyer_company?.id}`);
      console.log(`    - buyerCompanyId (final): ${buyerCompanyId}`);
      console.log(`    - finalCompanyId: ${finalCompanyId}`);
      
      return isIncoming && isCurrentUserSeller && isPending;
    });
    
    console.log('  Filtered incoming orders:', incomingOrders.length);
    
    return incomingOrders;
  },

  // Get outgoing purchase orders (where current user's company is the BUYER - orders placed with suppliers)
  getOutgoingPurchaseOrders: async (): Promise<PurchaseOrderWithRelations[]> => {
    // Use the simple API endpoint that exists
    const response = await apiClient.get('/purchase-orders', {
      params: {
        per_page: 100,
        sort_by: 'created_at',
        sort_order: 'desc'
      }
    });
    
    const allOrders = response.data?.purchase_orders || [];
    
    // Get current user's company ID from localStorage (stored by AuthContext)
    const userData = localStorage.getItem('user_data');
    const currentUserCompanyId = userData ? JSON.parse(userData).company?.id : null;
    
    // Also try to get from auth_token if user_data doesn't work
    const token = localStorage.getItem('auth_token');
    let fallbackCompanyId = null;
    if (token && !currentUserCompanyId) {
      try {
        // Decode JWT token to get user info
        const payload = JSON.parse(atob(token.split('.')[1]));
        fallbackCompanyId = payload.company_id;
      } catch (e) {
        console.log('Could not decode token for company ID');
      }
    }
    
    const finalCompanyId = currentUserCompanyId || fallbackCompanyId;
    
    console.log('🔍 getOutgoingPurchaseOrders - Debug Info:');
    console.log('  Current User Company ID (from user_data):', currentUserCompanyId);
    console.log('  Fallback Company ID (from token):', fallbackCompanyId);
    console.log('  Final Company ID:', finalCompanyId);
    console.log('  Total POs fetched:', allOrders.length);
    
    // Filter for outgoing orders (where current user's company is the BUYER)
    const outgoingOrders = allOrders.filter((po: any) => {
      // Try different possible property names for company IDs
      const sellerCompanyId = po.seller_company_id || po.sellerCompanyId || po.seller_company?.id;
      const buyerCompanyId = po.buyer_company_id || po.buyerCompanyId || po.buyer_company?.id;
      
      const isOutgoing = buyerCompanyId && sellerCompanyId; // Has both buyer and seller
      const isCurrentUserBuyer = finalCompanyId && buyerCompanyId === finalCompanyId;
      return isOutgoing && isCurrentUserBuyer;
    });
    
    console.log('  Filtered outgoing orders:', outgoingOrders.length);
    
    return outgoingOrders;
  },

  // Update a purchase order (not available in simplified API yet)
  updatePurchaseOrder: async (id: string, data: PurchaseOrderUpdate): Promise<PurchaseOrder> => {
    // TODO: Implement in simplified API
    throw new Error('Update purchase order not yet available in simplified API');
  },

  // Seller confirmation of purchase order (using simplified confirm endpoint)
  sellerConfirmPurchaseOrder: async (id: string, confirmation: SellerConfirmation): Promise<PurchaseOrder> => {
    const response = await apiClient.post(`/purchase-orders/${id}/confirm`, {});
    return response.data;
  },

  // Delete a purchase order (not available in simplified API yet)
  deletePurchaseOrder: async (id: string): Promise<void> => {
    // TODO: Implement in simplified API
    throw new Error('Delete purchase order not yet available in simplified API');
  },

  // Get traceability information for a purchase order (not available in simplified API yet)
  getTraceability: async (id: string): Promise<any> => {
    // TODO: Implement in simplified API
    throw new Error('Traceability not yet available in simplified API');
  },

  // Amendment API functions
  proposeChanges: async (id: string, proposal: ProposeChangesRequest): Promise<AmendmentResponse> => {
    // TODO: Implement in simplified API
    throw new Error('Amendment functions not yet available in simplified API');
  },

  approveChanges: async (id: string, approval: ApproveChangesRequest): Promise<AmendmentResponse> => {
    // TODO: Implement in simplified API
    throw new Error('Amendment functions not yet available in simplified API');
  },

  // Simple confirmation API function
  confirmPurchaseOrder: async (id: string, confirmation: PurchaseOrderConfirmation): Promise<ConfirmationResponse> => {
    const response = await apiClient.post(`/purchase-orders/${id}/confirm`, confirmation);
    return {
      success: true,
      message: "Purchase order confirmed successfully",
      purchase_order_id: id,
      status: "confirmed"
    };
  },

  // New acceptance and editing API functions
  acceptPurchaseOrder: async (id: string, acceptance: any): Promise<any> => {
    const response = await apiClient.put(`/purchase-orders/${id}/approve`, {});
    return response.data;
  },

  rejectPurchaseOrder: async (id: string, rejection: any): Promise<any> => {
    // TODO: Implement in simplified API
    throw new Error('Reject purchase order not yet available in simplified API');
  },

  editPurchaseOrder: async (id: string, editRequest: any): Promise<any> => {
    // TODO: Implement in simplified API
    throw new Error('Edit purchase order not yet available in simplified API');
  },

  approvePurchaseOrderEdit: async (id: string, approval: any): Promise<any> => {
    // TODO: Implement in simplified API
    throw new Error('Edit approval not yet available in simplified API');
  }
};

export default purchaseOrderApi;
