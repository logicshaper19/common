/**
 * Admin Purchase Order API Client
 * Handles all admin purchase order operations
 */

import { BaseAdminClient } from '../base/BaseAdminClient';
import { PaginatedResponse } from '../base/types';

// Purchase Order interfaces for admin
export interface AdminPurchaseOrder {
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
  
  // Timestamps
  created_at: string;
  updated_at: string;
  
  // Related data for admin view
  buyer_company_name?: string;
  seller_company_name?: string;
  product_name?: string;
}

export interface AdminPurchaseOrderFilter {
  page?: number;
  per_page?: number;
  search?: string;
  status?: string;
  buyer_company_id?: string;
  seller_company_id?: string;
  product_id?: string;
}

export class PurchaseOrderClient extends BaseAdminClient {

  /**
   * Get paginated list of all purchase orders (admin view)
   */
  async getPurchaseOrders(filters: AdminPurchaseOrderFilter): Promise<PaginatedResponse<AdminPurchaseOrder>> {
    // Validate pagination parameters
    const { page, per_page } = this.validatePagination(filters.page || 1, filters.per_page || 20);
    const validatedFilters = { ...filters, page, per_page };

    const response = await this.makeRequest<PaginatedResponse<AdminPurchaseOrder>>(
      '/admin/purchase-orders',
      { params: validatedFilters }
    );

    return response;
  }

  /**
   * Get a single purchase order by ID (admin view)
   */
  async getPurchaseOrder(id: string): Promise<AdminPurchaseOrder> {
    this.validateRequired({ id }, ['id']);

    const response = await this.makeRequest<AdminPurchaseOrder>(`/admin/purchase-orders/${id}`);
    return response;
  }

  /**
   * Delete a purchase order (admin only)
   */
  async deletePurchaseOrder(id: string): Promise<{ message: string }> {
    this.validateRequired({ id }, ['id']);

    const response = await this.makeRequest<{ message: string }>(`/admin/purchase-orders/${id}`, {
      method: 'DELETE',
    });

    return response;
  }

  /**
   * Get purchase order statistics for admin dashboard
   */
  async getPurchaseOrderStats(): Promise<{
    total_count: number;
    status_counts: Record<string, number>;
    total_value: number;
    recent_count: number;
  }> {
    const response = await this.makeRequest<{
      total_count: number;
      status_counts: Record<string, number>;
      total_value: number;
      recent_count: number;
    }>('/admin/purchase-orders/stats');

    return response;
  }

  /**
   * Bulk operations on purchase orders (admin only)
   */
  async bulkOperation(operation: 'delete' | 'cancel' | 'export', ids: string[]): Promise<{ message: string; affected_count: number }> {
    this.validateRequired({ operation, ids }, ['operation', 'ids']);

    if (ids.length === 0) {
      throw new Error('At least one purchase order ID is required');
    }

    const response = await this.makeRequest<{ message: string; affected_count: number }>('/admin/purchase-orders/bulk', {
      method: 'POST',
      data: {
        operation,
        purchase_order_ids: ids
      }
    });

    return response;
  }
}
