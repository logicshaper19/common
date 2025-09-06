/**
 * Mock data provider for products
 */
import { MockDataProvider } from './MockDataProvider';
import { PaginatedResponse } from '../base/types';
import {
  Product as AdminProduct,
  ProductFilter,
  ProductCreate,
  ProductUpdate,
  ProductValidationResult,
  ProductBulkOperation,
} from '../../../types/admin';

export class ProductMockProvider extends MockDataProvider {
  private mockProducts: AdminProduct[] = [
    {
      id: 'prod-1',
      common_product_id: 'palm_refined_edible',
      name: 'Refined Palm Oil',
      description: 'High-quality refined palm oil for food applications',
      category: 'processed',
      default_unit: 'MT',
      hs_code: '15119010',
      status: 'active',
      can_have_composition: true,
      created_at: '2024-01-15T10:00:00Z',
      updated_at: '2024-01-20T14:30:00Z',
      usage_count: 45,
      last_used: '2024-01-19T16:20:00Z',
      material_breakdown: {
        'Palm Oil': {
          min_percentage: 95,
          max_percentage: 100,
          required: true,
        },
      },
      origin_data_requirements: {
        coordinates: 'required',
        batch_tracking: true,
        supplier_verification: true,
        certifications: ['RSPO', 'ISCC'],
      },
    },
    {
      id: 'prod-2',
      common_product_id: 'coconut_oil_virgin',
      name: 'Virgin Coconut Oil',
      description: 'Cold-pressed virgin coconut oil',
      category: 'raw_material',
      default_unit: 'KG',
      hs_code: '15131100',
      status: 'active',
      can_have_composition: false,
      created_at: '2024-01-10T08:00:00Z',
      updated_at: '2024-01-18T12:15:00Z',
      usage_count: 23,
      last_used: '2024-01-17T09:45:00Z',
      origin_data_requirements: {
        coordinates: 'optional',
        batch_tracking: false,
        supplier_verification: true,
        certifications: ['Organic'],
      },
    },
    {
      id: 'prod-3',
      common_product_id: 'soybean_oil_crude',
      name: 'Crude Soybean Oil',
      description: 'Unrefined soybean oil for processing',
      category: 'raw_material',
      default_unit: 'MT',
      hs_code: '15071000',
      status: 'active',
      can_have_composition: false,
      created_at: '2024-01-05T14:00:00Z',
      updated_at: '2024-01-15T09:30:00Z',
      usage_count: 67,
      last_used: '2024-01-20T11:15:00Z',
      origin_data_requirements: {
        coordinates: 'required',
        batch_tracking: true,
        supplier_verification: true,
        certifications: ['Non-GMO', 'Organic'],
      },
    },
    {
      id: 'prod-4',
      common_product_id: 'chocolate_dark_70',
      name: 'Dark Chocolate 70%',
      description: 'Premium dark chocolate with 70% cocoa content',
      category: 'finished_good',
      default_unit: 'KG',
      hs_code: '18063100',
      status: 'active',
      can_have_composition: true,
      created_at: '2024-01-08T16:45:00Z',
      updated_at: '2024-01-22T13:20:00Z',
      usage_count: 12,
      last_used: '2024-01-21T15:30:00Z',
      material_breakdown: {
        'Cocoa Mass': {
          min_percentage: 70,
          max_percentage: 75,
          required: true,
        },
        'Sugar': {
          min_percentage: 20,
          max_percentage: 25,
          required: true,
        },
        'Cocoa Butter': {
          min_percentage: 5,
          max_percentage: 10,
          required: false,
        },
      },
      origin_data_requirements: {
        coordinates: 'required',
        batch_tracking: true,
        supplier_verification: true,
        certifications: ['Fair Trade', 'Rainforest Alliance'],
      },
    },
    {
      id: 'prod-5',
      common_product_id: 'wheat_flour_all_purpose',
      name: 'All-Purpose Wheat Flour',
      description: 'Versatile wheat flour for baking and cooking',
      category: 'processed',
      default_unit: 'KG',
      hs_code: '11010000',
      status: 'inactive',
      can_have_composition: false,
      created_at: '2023-12-20T10:00:00Z',
      updated_at: '2024-01-10T14:00:00Z',
      usage_count: 89,
      last_used: '2024-01-09T08:45:00Z',
      origin_data_requirements: {
        coordinates: 'optional',
        batch_tracking: false,
        supplier_verification: false,
        certifications: [],
      },
    },
  ];

  async getProducts(filters: ProductFilter): Promise<PaginatedResponse<AdminProduct>> {
    await this.delay();

    let filtered = [...this.mockProducts];

    // Apply filters
    if (filters.search) {
      filtered = this.applySearch(filtered, filters.search, ['name', 'description', 'common_product_id']);
    }

    if (filters.category) {
      filtered = this.applyEnumFilter(filtered, 'category', filters.category);
    }

    if (filters.status) {
      filtered = this.applyEnumFilter(filtered, 'status', filters.status);
    }

    if (filters.can_have_composition !== undefined) {
      filtered = this.applyBooleanFilter(filtered, 'can_have_composition', filters.can_have_composition);
    }

    if (filters.hs_code) {
      filtered = filtered.filter(p => p.hs_code?.includes(filters.hs_code!));
    }

    if (filters.created_after) {
      filtered = this.applyDateRange(filtered, 'created_at', filters.created_after);
    }

    if (filters.created_before) {
      filtered = this.applyDateRange(filtered, 'created_at', undefined, filters.created_before);
    }

    if (filters.usage_min !== undefined || filters.usage_max !== undefined) {
      filtered = this.applyNumericRange(filtered, 'usage_count', filters.usage_min, filters.usage_max);
    }

    // Apply sorting (default by name)
    const sortBy = filters.sort_by || 'name';
    const sortOrder = filters.sort_order || 'asc';
    filtered = this.applySorting(filtered, sortBy as keyof AdminProduct, sortOrder);

    // Apply pagination
    return this.applyPagination(filtered, filters.page, filters.per_page);
  }

  async getProduct(id: string): Promise<AdminProduct> {
    await this.delay();

    const product = this.mockProducts.find(p => p.id === id);
    if (!product) {
      throw new Error(`Product with id ${id} not found`);
    }

    return this.deepClone(product);
  }

  async createProduct(data: ProductCreate): Promise<AdminProduct> {
    await this.delay();

    // Check if product ID already exists
    if (this.mockProducts.some(p => p.common_product_id === data.common_product_id)) {
      throw new Error('Product with this ID already exists');
    }

    const newProduct: AdminProduct = {
      id: this.generateId('prod'),
      ...data,
      status: 'active',
      created_at: this.getCurrentTimestamp(),
      updated_at: this.getCurrentTimestamp(),
      usage_count: 0,
    };

    this.mockProducts.push(newProduct);
    return this.deepClone(newProduct);
  }

  async updateProduct(id: string, data: ProductUpdate): Promise<AdminProduct> {
    await this.delay();

    const productIndex = this.mockProducts.findIndex(p => p.id === id);
    if (productIndex === -1) {
      throw new Error(`Product with id ${id} not found`);
    }

    this.mockProducts[productIndex] = {
      ...this.mockProducts[productIndex],
      ...data,
      updated_at: this.getCurrentTimestamp(),
    };

    return this.deepClone(this.mockProducts[productIndex]);
  }

  async deleteProduct(id: string): Promise<{ success: boolean }> {
    await this.delay();

    const productIndex = this.mockProducts.findIndex(p => p.id === id);
    if (productIndex === -1) {
      throw new Error(`Product with id ${id} not found`);
    }

    this.mockProducts.splice(productIndex, 1);
    return { success: true };
  }

  async validateProduct(data: ProductCreate): Promise<ProductValidationResult> {
    await this.delay();

    const validation: ProductValidationResult = {
      is_valid: true,
      errors: [],
      warnings: [],
      suggestions: [],
    };

    // Check if product ID already exists
    if (this.mockProducts.some(p => p.common_product_id === data.common_product_id)) {
      validation.is_valid = false;
      validation.errors.push('Product ID already exists');
    }

    // Validate required fields
    if (!data.name || data.name.trim().length === 0) {
      validation.is_valid = false;
      validation.errors.push('Product name is required');
    }

    if (!data.common_product_id || data.common_product_id.trim().length === 0) {
      validation.is_valid = false;
      validation.errors.push('Product ID is required');
    }

    // Add warnings
    if (!data.description || data.description.length < 10) {
      validation.warnings.push('Consider adding a more detailed description');
    }

    if (!data.hs_code) {
      validation.warnings.push('HS code is recommended for customs processing');
    }

    // Add suggestions
    if (data.category === 'processed' && !data.can_have_composition) {
      validation.suggestions.push('Processed products typically have composition data');
    }

    if (!data.origin_data_requirements?.certifications?.length) {
      validation.suggestions.push('Consider adding certification requirements for better traceability');
    }

    return validation;
  }

  async bulkProductOperation(operation: ProductBulkOperation): Promise<{ success: boolean; affected_count: number }> {
    await this.delay();

    let affectedCount = 0;

    for (const productId of operation.product_ids) {
      const productIndex = this.mockProducts.findIndex(p => p.id === productId);
      if (productIndex === -1) continue;

      switch (operation.operation) {
        case 'activate':
          this.mockProducts[productIndex].status = 'active';
          affectedCount++;
          break;
        case 'deactivate':
          this.mockProducts[productIndex].status = 'inactive';
          affectedCount++;
          break;
        case 'deprecate':
          this.mockProducts[productIndex].status = 'deprecated';
          affectedCount++;
          break;
        case 'delete':
          this.mockProducts.splice(productIndex, 1);
          affectedCount++;
          break;
        case 'export':
          // In a real implementation, this would generate an export file
          affectedCount++;
          break;
      }
    }

    return {
      success: true,
      affected_count: affectedCount,
    };
  }
}
