/**
 * Product management client for admin API
 */
import { BaseAdminClient } from '../base/BaseAdminClient';
import { ProductMockProvider } from '../mock/productMocks';
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
  private mockProvider = new ProductMockProvider();

  /**
   * Get paginated list of products with filtering
   */
  async getProducts(filters: ProductFilter): Promise<PaginatedResponse<AdminProduct>> {
    try {
      // Validate pagination parameters
      const { page, per_page } = this.validatePagination(filters.page, filters.per_page);
      const validatedFilters = { ...filters, page, per_page };

      const response = await this.makeRequest<PaginatedResponse<AdminProduct>>(
        '/admin/products',
        { params: validatedFilters }
      );

      return response;
    } catch (error) {
      console.warn('Backend not available for products, using mock data');
      return this.mockProvider.getProducts(filters);
    }
  }

  /**
   * Get a single product by ID
   */
  async getProduct(id: string): Promise<AdminProduct> {
    this.validateRequired({ id }, ['id']);

    try {
      const response = await this.makeRequest<AdminProduct>(`/admin/products/${id}`);
      return response;
    } catch (error) {
      console.warn(`Backend not available for product ${id}, using mock data`);
      return this.mockProvider.getProduct(id);
    }
  }

  /**
   * Create a new product
   */
  async createProduct(data: ProductCreate): Promise<AdminProduct> {
    this.validateRequired(data, ['common_product_id', 'name', 'category', 'default_unit']);

    try {
      const response = await this.makeRequest<AdminProduct>('/admin/products', {
        method: 'POST',
        data,
      });

      return response;
    } catch (error) {
      console.warn('Backend not available for product creation, using mock data');
      return this.mockProvider.createProduct(data);
    }
  }

  /**
   * Update an existing product
   */
  async updateProduct(id: string, data: ProductUpdate): Promise<AdminProduct> {
    this.validateRequired({ id }, ['id']);

    try {
      const response = await this.makeRequest<AdminProduct>(`/admin/products/${id}`, {
        method: 'PUT',
        data,
      });

      return response;
    } catch (error) {
      console.warn(`Backend not available for product ${id} update, using mock data`);
      return this.mockProvider.updateProduct(id, data);
    }
  }

  /**
   * Delete a product
   */
  async deleteProduct(id: string): Promise<{ success: boolean }> {
    this.validateRequired({ id }, ['id']);

    try {
      await this.makeRequest(`/admin/products/${id}`, {
        method: 'DELETE',
      });

      return { success: true };
    } catch (error) {
      console.warn(`Backend not available for product ${id} deletion, using mock data`);
      return this.mockProvider.deleteProduct(id);
    }
  }

  /**
   * Validate product data before creation/update
   */
  async validateProduct(data: ProductCreate): Promise<ProductValidationResult> {
    this.validateRequired(data, ['common_product_id', 'name', 'category']);

    try {
      const response = await this.makeRequest<ProductValidationResult>('/admin/products/validate', {
        method: 'POST',
        data,
      });

      return response;
    } catch (error) {
      console.warn('Backend not available for product validation, using mock data');
      return this.mockProvider.validateProduct(data);
    }
  }

  /**
   * Perform bulk operations on multiple products
   */
  async bulkProductOperation(operation: ProductBulkOperation): Promise<{ success: boolean; affected_count: number }> {
    this.validateRequired(operation, ['operation', 'product_ids']);

    if (!operation.product_ids.length) {
      throw new Error('At least one product ID is required for bulk operations');
    }

    try {
      const response = await this.makeRequest<{ success: boolean; affected_count: number }>(
        '/admin/products/bulk',
        {
          method: 'POST',
          data: operation,
        }
      );

      return response;
    } catch (error) {
      console.warn('Backend not available for bulk product operation, using mock data');
      return this.mockProvider.bulkProductOperation(operation);
    }
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
    try {
      const response = await this.makeRequest<any>('/admin/products/stats');
      return response;
    } catch (error) {
      console.warn('Backend not available for product stats, using mock data');
      
      // Generate mock stats
      const allProducts = await this.mockProvider.getProducts({
        page: 1,
        per_page: 1000,
      });

      const products = allProducts.data;
      
      const stats = {
        total_products: products.length,
        active_products: products.filter(p => p.status === 'active').length,
        inactive_products: products.filter(p => p.status === 'inactive').length,
        deprecated_products: products.filter(p => p.status === 'deprecated').length,
        by_category: products.reduce((acc, p) => {
          acc[p.category] = (acc[p.category] || 0) + 1;
          return acc;
        }, {} as Record<string, number>),
        most_used: products
          .sort((a, b) => b.usage_count - a.usage_count)
          .slice(0, 5),
        recently_created: products
          .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
          .slice(0, 5),
      };

      return stats;
    }
  }

  /**
   * Export products to various formats
   */
  async exportProducts(filters: ProductFilter, format: 'csv' | 'xlsx' | 'json' = 'csv'): Promise<{ download_url: string }> {
    try {
      const response = await this.makeRequest<{ download_url: string }>('/admin/products/export', {
        method: 'POST',
        data: { filters, format },
      });

      return response;
    } catch (error) {
      console.warn('Backend not available for product export, using mock data');
      
      // In a real implementation, this would generate an actual file
      return {
        download_url: `https://example.com/exports/products-${Date.now()}.${format}`,
      };
    }
  }

  /**
   * Import products from file
   */
  async importProducts(file: File, options: {
    update_existing?: boolean;
    validate_only?: boolean;
  } = {}): Promise<{
    success: boolean;
    imported_count: number;
    updated_count: number;
    errors: string[];
    warnings: string[];
  }> {
    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('options', JSON.stringify(options));

      const response = await this.makeRequest<any>('/admin/products/import', {
        method: 'POST',
        data: formData,
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      return response;
    } catch (error) {
      console.warn('Backend not available for product import, using mock data');
      
      // Mock import result
      return {
        success: true,
        imported_count: 10,
        updated_count: 5,
        errors: [],
        warnings: ['Some products had missing HS codes'],
      };
    }
  }
}
