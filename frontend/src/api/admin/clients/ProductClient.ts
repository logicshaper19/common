/**
 * Product management client for admin API
 */
import { BaseAdminClient } from '../base/BaseAdminClient';
import { PaginatedResponse } from '../base/types';
import {
  Product as AdminProduct,
  ProductFilter,
  ProductCreate,
  ProductUpdate,
  ProductValidationResult,
  ProductBulkOperation,
} from '../../../types/admin';

export class ProductClient extends BaseAdminClient {

  /**
   * Get paginated list of products with filtering
   */
  async getProducts(filters: ProductFilter): Promise<PaginatedResponse<AdminProduct>> {
    // Validate pagination parameters
    const { page, per_page } = this.validatePagination(filters.page, filters.per_page);
    const validatedFilters = { ...filters, page, per_page };

    const response = await this.makeRequest<PaginatedResponse<AdminProduct>>(
      '/admin/products',
      { params: validatedFilters }
    );

    return response;
  }

  /**
   * Get a single product by ID
   */
  async getProduct(id: string): Promise<AdminProduct> {
    this.validateRequired({ id }, ['id']);

    const response = await this.makeRequest<AdminProduct>(`/admin/products/${id}`);
    return response;
  }

  /**
   * Create a new product
   */
  async createProduct(data: ProductCreate): Promise<AdminProduct> {
    this.validateRequired(data, ['common_product_id', 'name', 'category', 'default_unit']);

    const response = await this.makeRequest<AdminProduct>('/admin/products', {
      method: 'POST',
      data,
    });

    return response;
  }

  /**
   * Update an existing product
   */
  async updateProduct(id: string, data: ProductUpdate): Promise<AdminProduct> {
    this.validateRequired({ id }, ['id']);

    const response = await this.makeRequest<AdminProduct>(`/admin/products/${id}`, {
      method: 'PUT',
      data,
    });

    return response;
  }

  /**
   * Delete a product
   */
  async deleteProduct(id: string): Promise<{ success: boolean }> {
    this.validateRequired({ id }, ['id']);

    const response = await this.makeRequest<{ success: boolean }>(`/admin/products/${id}`, {
      method: 'DELETE',
    });

    return { success: true };
  }

  /**
   * Validate product data before creation/update
   */
  async validateProduct(data: ProductCreate): Promise<ProductValidationResult> {
    this.validateRequired(data, ['common_product_id', 'name', 'category']);

    const response = await this.makeRequest<ProductValidationResult>('/admin/products/validate', {
      method: 'POST',
      data,
    });

    return response;
  }

  /**
   * Perform bulk operations on multiple products
   */
  async bulkProductOperation(operation: ProductBulkOperation): Promise<{ success: boolean; affected_count: number }> {
    this.validateRequired(operation, ['operation', 'product_ids']);

    if (!operation.product_ids.length) {
      throw new Error('At least one product ID is required for bulk operations');
    }

    const response = await this.makeRequest<{ success: boolean; affected_count: number }>(
      '/admin/products/bulk',
      {
        method: 'POST',
        data: operation,
      }
    );

    return response;
  }

  /**
   * Get product statistics
   */
  async getProductStats(): Promise<{
    total_products: number;
    active_products: number;
    inactive_products: number;
    deprecated_products: number;
    by_category: Record<string, number>;
    most_used: AdminProduct[];
    recently_created: AdminProduct[];
  }> {
    const response = await this.makeRequest<any>('/admin/products/stats');
    return response;
  }

  /**
   * Export products to various formats
   */
  async exportProducts(filters: ProductFilter, format: 'csv' | 'xlsx' | 'json'): Promise<{ download_url: string }> {
    const response = await this.makeRequest<{ download_url: string }>('/admin/products/export', {
      method: 'POST',
      data: { filters, format },
    });

    return response;
  }

  /**
   * Import products from file
   */
  async importProducts(file: File, options?: {
    update_existing?: boolean;
    validate_only?: boolean;
  }): Promise<{
    success: boolean;
    imported_count: number;
    updated_count: number;
    errors: Array<{
      row: number;
      field: string;
      message: string;
    }>;
  }> {
    const formData = new FormData();
    formData.append('file', file);
    if (options) {
      formData.append('options', JSON.stringify(options));
    }

    const response = await this.makeRequest<any>('/admin/products/import', {
      method: 'POST',
      data: formData,
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });

    return response;
  }

  /**
   * Get product usage analytics
   */
  async getProductAnalytics(id: string, timeRange: string = '30d'): Promise<{
    usage_count: number;
    purchase_orders: number;
    companies_using: number;
    trend_data: Array<{
      date: string;
      usage_count: number;
      purchase_orders: number;
    }>;
    top_buyers: Array<{
      company_id: string;
      company_name: string;
      usage_count: number;
    }>;
  }> {
    this.validateRequired({ id }, ['id']);

    const response = await this.makeRequest<any>(`/admin/products/${id}/analytics`, {
      params: { time_range: timeRange },
    });

    return response;
  }

  /**
   * Update product status
   */
  async updateProductStatus(id: string, status: 'active' | 'inactive' | 'deprecated'): Promise<{ success: boolean }> {
    this.validateRequired({ id, status }, ['id', 'status']);

    const response = await this.makeRequest<{ success: boolean }>(`/admin/products/${id}/status`, {
      method: 'PUT',
      data: { status },
    });

    return response;
  }

  /**
   * Get product composition requirements
   */
  async getProductComposition(id: string): Promise<{
    material_breakdown: Record<string, {
      min_percentage: number;
      max_percentage: number;
      required: boolean;
    }>;
    origin_data_requirements: {
      coordinates: 'required' | 'optional' | 'none';
      batch_tracking: boolean;
      supplier_verification: boolean;
      certifications: string[];
    };
  }> {
    this.validateRequired({ id }, ['id']);

    const response = await this.makeRequest<any>(`/admin/products/${id}/composition`);
    return response;
  }

  /**
   * Update product composition requirements
   */
  async updateProductComposition(id: string, composition: any): Promise<{ success: boolean }> {
    this.validateRequired({ id }, ['id']);

    const response = await this.makeRequest<{ success: boolean }>(`/admin/products/${id}/composition`, {
      method: 'PUT',
      data: composition,
    });

    return response;
  }
}
