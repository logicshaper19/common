/**
 * Product Catalog Management Tests
 * Test suite for product catalog admin functionality
 */
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { ProductCatalogManagement } from '../product-catalog-management';
import { adminApi } from '../../../lib/adminApi';

// Mock the admin API
jest.mock('../../../lib/adminApi', () => ({
  adminApi: {
    getProducts: jest.fn(),
    createProduct: jest.fn(),
    updateProduct: jest.fn(),
    deleteProduct: jest.fn(),
    validateProduct: jest.fn(),
    bulkProductOperation: jest.fn(),
  },
}));

const mockProducts = [
  {
    id: 'prod-1',
    common_product_id: 'palm_refined_edible',
    name: 'Refined Palm Oil',
    description: 'High-quality refined palm oil for food applications',
    category: 'processed' as const,
    default_unit: 'MT',
    hs_code: '15119010',
    status: 'active' as const,
    can_have_composition: true,
    created_at: '2024-01-15T10:00:00Z',
    updated_at: '2024-01-20T14:30:00Z',
    created_by: 'admin-1',
    updated_by: 'admin-1',
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
    category: 'raw_material' as const,
    default_unit: 'KG',
    hs_code: '15131100',
    status: 'active' as const,
    can_have_composition: false,
    created_at: '2024-01-10T08:00:00Z',
    updated_at: '2024-01-18T12:15:00Z',
    created_by: 'admin-2',
    updated_by: 'admin-1',
    usage_count: 23,
    last_used: '2024-01-17T09:45:00Z',
    material_breakdown: null,
    origin_data_requirements: {
      coordinates: 'optional',
      batch_tracking: false,
      supplier_verification: true,
      certifications: ['Organic'],
    },
  },
];

const mockValidationResult = {
  is_valid: true,
  errors: [],
  warnings: ['Consider adding more detailed description'],
  suggestions: ['Add material breakdown for better traceability'],
};

describe('ProductCatalogManagement', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (adminApi.getProducts as any).mockResolvedValue({
      products: mockProducts,
      total: mockProducts.length,
    });
  });

  it('renders product catalog management interface', async () => {
    render(<ProductCatalogManagement />);
    
    expect(screen.getByText('Product Catalog Management')).toBeInTheDocument();
    expect(screen.getByText('Add Product')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Search products...')).toBeInTheDocument();
    
    await waitFor(() => {
      expect(screen.getByText('Refined Palm Oil')).toBeInTheDocument();
      expect(screen.getByText('Virgin Coconut Oil')).toBeInTheDocument();
    });
  });

  it('loads and displays products', async () => {
    render(<ProductCatalogManagement />);
    
    await waitFor(() => {
      expect(adminApi.getProducts).toHaveBeenCalledWith({
        page: 1,
        per_page: 20,
      });
      
      expect(screen.getByText('palm_refined_edible')).toBeInTheDocument();
      expect(screen.getByText('coconut_oil_virgin')).toBeInTheDocument();
      expect(screen.getByText('Processed')).toBeInTheDocument();
      expect(screen.getByText('Raw Material')).toBeInTheDocument();
    });
  });

  it('filters products by search term', async () => {
    render(<ProductCatalogManagement />);
    
    await waitFor(() => {
      expect(screen.getByText('Refined Palm Oil')).toBeInTheDocument();
    });
    
    const searchInput = screen.getByPlaceholderText('Search products...');
    fireEvent.change(searchInput, { target: { value: 'palm' } });
    
    await waitFor(() => {
      expect(adminApi.getProducts).toHaveBeenCalledWith({
        page: 1,
        per_page: 20,
        search: 'palm',
      });
    });
  });

  it('filters products by category', async () => {
    render(<ProductCatalogManagement />);
    
    await waitFor(() => {
      expect(screen.getByText('Refined Palm Oil')).toBeInTheDocument();
    });
    
    const categorySelect = screen.getByDisplayValue('All Categories');
    fireEvent.change(categorySelect, { target: { value: 'processed' } });
    
    await waitFor(() => {
      expect(adminApi.getProducts).toHaveBeenCalledWith({
        page: 1,
        per_page: 20,
        category: 'processed',
      });
    });
  });

  it('opens create product modal', async () => {
    render(<ProductCatalogManagement />);
    
    fireEvent.click(screen.getByText('Add Product'));
    
    await waitFor(() => {
      expect(screen.getByText('Create New Product')).toBeInTheDocument();
      expect(screen.getByPlaceholderText('e.g., palm_refined_edible')).toBeInTheDocument();
      expect(screen.getByPlaceholderText('e.g., Refined Palm Oil')).toBeInTheDocument();
    });
  });

  it('creates a new product', async () => {
    (adminApi.createProduct as any).mockResolvedValue({ id: 'prod-3' });
    (adminApi.validateProduct as any).mockResolvedValue(mockValidationResult);
    
    render(<ProductCatalogManagement />);
    
    fireEvent.click(screen.getByText('Add Product'));
    
    await waitFor(() => {
      expect(screen.getByText('Create New Product')).toBeInTheDocument();
    });
    
    // Fill in form
    fireEvent.change(screen.getByPlaceholderText('e.g., palm_refined_edible'), {
      target: { value: 'test_product' },
    });
    fireEvent.change(screen.getByPlaceholderText('e.g., Refined Palm Oil'), {
      target: { value: 'Test Product' },
    });
    fireEvent.change(screen.getByPlaceholderText('Product description...'), {
      target: { value: 'Test description' },
    });
    
    // Submit form
    fireEvent.click(screen.getByText('Create Product'));
    
    await waitFor(() => {
      expect(adminApi.createProduct).toHaveBeenCalledWith({
        common_product_id: 'test_product',
        name: 'Test Product',
        description: 'Test description',
        category: 'raw_material',
        default_unit: '',
        hs_code: '',
        can_have_composition: false,
      });
    });
  });

  it('validates product before creation', async () => {
    (adminApi.validateProduct as any).mockResolvedValue({
      is_valid: false,
      errors: ['Product ID already exists'],
      warnings: [],
      suggestions: [],
    });
    
    render(<ProductCatalogManagement />);
    
    fireEvent.click(screen.getByText('Add Product'));
    
    await waitFor(() => {
      expect(screen.getByText('Create New Product')).toBeInTheDocument();
    });
    
    // Fill in form
    fireEvent.change(screen.getByPlaceholderText('e.g., palm_refined_edible'), {
      target: { value: 'existing_product' },
    });
    fireEvent.change(screen.getByPlaceholderText('e.g., Refined Palm Oil'), {
      target: { value: 'Existing Product' },
    });
    
    // Submit form
    fireEvent.click(screen.getByText('Create Product'));
    
    await waitFor(() => {
      expect(adminApi.validateProduct).toHaveBeenCalled();
      expect(screen.getByText('Validation Errors')).toBeInTheDocument();
      expect(screen.getByText('Product ID already exists')).toBeInTheDocument();
    });
  });

  it('opens edit product modal', async () => {
    render(<ProductCatalogManagement />);
    
    await waitFor(() => {
      expect(screen.getByText('Refined Palm Oil')).toBeInTheDocument();
    });
    
    const editButtons = screen.getAllByTitle('Edit Product');
    fireEvent.click(editButtons[0]);
    
    await waitFor(() => {
      expect(screen.getByText('Edit Product: Refined Palm Oil')).toBeInTheDocument();
      expect(screen.getByDisplayValue('palm_refined_edible')).toBeDisabled();
    });
  });

  it('updates an existing product', async () => {
    (adminApi.updateProduct as any).mockResolvedValue({ success: true });
    
    render(<ProductCatalogManagement />);
    
    await waitFor(() => {
      expect(screen.getByText('Refined Palm Oil')).toBeInTheDocument();
    });
    
    const editButtons = screen.getAllByTitle('Edit Product');
    fireEvent.click(editButtons[0]);
    
    await waitFor(() => {
      expect(screen.getByText('Edit Product: Refined Palm Oil')).toBeInTheDocument();
    });
    
    // Update name
    const nameInput = screen.getByDisplayValue('Refined Palm Oil');
    fireEvent.change(nameInput, { target: { value: 'Updated Palm Oil' } });
    
    // Submit form
    fireEvent.click(screen.getByText('Update Product'));
    
    await waitFor(() => {
      expect(adminApi.updateProduct).toHaveBeenCalledWith('prod-1', {
        name: 'Updated Palm Oil',
        description: 'High-quality refined palm oil for food applications',
        category: 'processed',
        default_unit: 'MT',
        hs_code: '15119010',
        can_have_composition: true,
      });
    });
  });

  it('opens view product modal', async () => {
    render(<ProductCatalogManagement />);
    
    await waitFor(() => {
      expect(screen.getByText('Refined Palm Oil')).toBeInTheDocument();
    });
    
    const viewButtons = screen.getAllByTitle('View Product');
    fireEvent.click(viewButtons[0]);
    
    await waitFor(() => {
      expect(screen.getByText('Product Details: Refined Palm Oil')).toBeInTheDocument();
      expect(screen.getByText('palm_refined_edible')).toBeInTheDocument();
      expect(screen.getByText('Material Breakdown')).toBeInTheDocument();
      expect(screen.getByText('Origin Data Requirements')).toBeInTheDocument();
    });
  });

  it('deletes a product', async () => {
    (adminApi.deleteProduct as any).mockResolvedValue({ success: true });
    
    // Mock window.confirm
    const confirmSpy = jest.spyOn(window, 'confirm').mockReturnValue(true);
    
    render(<ProductCatalogManagement />);
    
    await waitFor(() => {
      expect(screen.getByText('Refined Palm Oil')).toBeInTheDocument();
    });
    
    const deleteButtons = screen.getAllByTitle('Delete Product');
    fireEvent.click(deleteButtons[0]);
    
    await waitFor(() => {
      expect(confirmSpy).toHaveBeenCalledWith('Are you sure you want to delete this product?');
      expect(adminApi.deleteProduct).toHaveBeenCalledWith('prod-1');
    });
    
    confirmSpy.mockRestore();
  });

  it('selects products for bulk operations', async () => {
    render(<ProductCatalogManagement />);
    
    await waitFor(() => {
      expect(screen.getByText('Refined Palm Oil')).toBeInTheDocument();
    });
    
    // Select first product
    const checkboxes = screen.getAllByRole('checkbox');
    fireEvent.click(checkboxes[1]); // Skip the "select all" checkbox
    
    await waitFor(() => {
      expect(screen.getByText('1 product selected')).toBeInTheDocument();
      expect(screen.getByText('Activate')).toBeInTheDocument();
      expect(screen.getByText('Deactivate')).toBeInTheDocument();
    });
  });

  it('performs bulk operations on selected products', async () => {
    (adminApi.bulkProductOperation as any).mockResolvedValue({ success: true });
    
    // Mock window.prompt
    const promptSpy = jest.spyOn(window, 'prompt').mockReturnValue('Test reason');
    
    render(<ProductCatalogManagement />);
    
    await waitFor(() => {
      expect(screen.getByText('Refined Palm Oil')).toBeInTheDocument();
    });
    
    // Select first product
    const checkboxes = screen.getAllByRole('checkbox');
    fireEvent.click(checkboxes[1]);
    
    await waitFor(() => {
      expect(screen.getByText('1 product selected')).toBeInTheDocument();
    });
    
    // Perform bulk deactivate
    fireEvent.click(screen.getByText('Deactivate'));
    
    await waitFor(() => {
      expect(promptSpy).toHaveBeenCalledWith('Please provide a reason for deactivate:');
      expect(adminApi.bulkProductOperation).toHaveBeenCalledWith({
        operation: 'deactivate',
        product_ids: ['prod-1'],
        reason: 'Test reason',
      });
    });
    
    promptSpy.mockRestore();
  });

  it('displays loading state', () => {
    (adminApi.getProducts as any).mockImplementation(() => new Promise(() => {}));
    
    render(<ProductCatalogManagement />);
    
    expect(screen.getByText('Loading products...')).toBeInTheDocument();
  });

  it('displays error state', async () => {
    (adminApi.getProducts as any).mockRejectedValue(new Error('API Error'));
    
    render(<ProductCatalogManagement />);
    
    await waitFor(() => {
      expect(screen.getByText('Failed to load products')).toBeInTheDocument();
    });
  });

  it('displays empty state when no products found', async () => {
    (adminApi.getProducts as any).mockResolvedValue({
      products: [],
      total: 0,
    });
    
    render(<ProductCatalogManagement />);
    
    await waitFor(() => {
      expect(screen.getByText('No products found')).toBeInTheDocument();
    });
  });

  it('displays product statistics correctly', async () => {
    render(<ProductCatalogManagement />);
    
    await waitFor(() => {
      expect(screen.getByText('Products (2)')).toBeInTheDocument();
    });
  });

  it('shows validation warnings and suggestions', async () => {
    (adminApi.validateProduct as any).mockResolvedValue({
      is_valid: true,
      errors: [],
      warnings: ['Consider adding more detailed description'],
      suggestions: ['Add material breakdown for better traceability'],
    });
    
    render(<ProductCatalogManagement />);
    
    fireEvent.click(screen.getByText('Add Product'));
    
    await waitFor(() => {
      expect(screen.getByText('Create New Product')).toBeInTheDocument();
    });
    
    // Fill in form to trigger validation
    fireEvent.change(screen.getByPlaceholderText('e.g., palm_refined_edible'), {
      target: { value: 'test_product' },
    });
    fireEvent.change(screen.getByPlaceholderText('e.g., Refined Palm Oil'), {
      target: { value: 'Test Product' },
    });
    
    fireEvent.click(screen.getByText('Create Product'));
    
    await waitFor(() => {
      expect(screen.getByText('Warnings')).toBeInTheDocument();
      expect(screen.getByText('Consider adding more detailed description')).toBeInTheDocument();
      expect(screen.getByText('Suggestions')).toBeInTheDocument();
      expect(screen.getByText('Add material breakdown for better traceability')).toBeInTheDocument();
    });
  });
});
