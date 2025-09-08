/**
 * Custom hook for product management operations
 */
import { useState, useCallback, useEffect } from 'react';
import { adminApi } from '../../../../api/admin';
import {
  Product,
  ProductFilter,
  ProductCreate,
  ProductUpdate,
  ProductBulkOperation,
  ProductValidationResult,
} from '../../../../types/admin';

export interface UseProductManagementReturn {
  // State
  products: Product[];
  loading: boolean;
  error: string | null;
  selectedProducts: Set<string>;
  totalPages: number;
  totalProducts: number;
  filters: ProductFilter;
  validationResult: ProductValidationResult | null;
  
  // Actions
  loadProducts: () => Promise<void>;
  handleFilterChange: (newFilters: Partial<ProductFilter>) => void;
  handlePageChange: (page: number) => void;
  handleSelectProduct: (productId: string) => void;
  handleSelectAllProducts: () => void;
  createProduct: (productData: ProductCreate) => Promise<void>;
  updateProduct: (productId: string, productData: ProductUpdate) => Promise<void>;
  deleteProduct: (productId: string) => Promise<void>;
  bulkOperation: (operation: ProductBulkOperation['operation']) => Promise<void>;
  validateProduct: (productId: string) => Promise<void>;
  clearSelection: () => void;
  clearError: () => void;
  clearValidationResult: () => void;
}

export function useProductManagement(): UseProductManagementReturn {
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedProducts, setSelectedProducts] = useState<Set<string>>(new Set());
  const [totalPages, setTotalPages] = useState(1);
  const [totalProducts, setTotalProducts] = useState(0);
  const [validationResult, setValidationResult] = useState<ProductValidationResult | null>(null);
  const [filters, setFilters] = useState<ProductFilter>({
    page: 1,
    per_page: 20,
  });

  const loadProducts = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await adminApi.getProducts(filters);
      setProducts(response.data);
      setTotalPages(response.total_pages);
      setTotalProducts(response.total);
    } catch (err) {
      setError('Failed to load products');
      console.error('Error loading products:', err);
    } finally {
      setLoading(false);
    }
  }, [filters]);

  const handleFilterChange = useCallback((newFilters: Partial<ProductFilter>) => {
    setFilters(prev => ({ ...prev, ...newFilters, page: 1 }));
  }, []);

  const handlePageChange = useCallback((page: number) => {
    setFilters(prev => ({ ...prev, page }));
  }, []);

  const handleSelectProduct = useCallback((productId: string) => {
    setSelectedProducts(prev => {
      const newSet = new Set(prev);
      if (newSet.has(productId)) {
        newSet.delete(productId);
      } else {
        newSet.add(productId);
      }
      return newSet;
    });
  }, []);

  const handleSelectAllProducts = useCallback(() => {
    if (selectedProducts.size === products.length) {
      setSelectedProducts(new Set());
    } else {
      setSelectedProducts(new Set(products.map(product => product.id)));
    }
  }, [selectedProducts.size, products]);

  const createProduct = useCallback(async (productData: ProductCreate) => {
    try {
      setError(null);
      await adminApi.createProduct(productData);
      await loadProducts(); // Reload products after creation
    } catch (err) {
      setError('Failed to create product');
      console.error('Error creating product:', err);
      throw err;
    }
  }, [loadProducts]);

  const updateProduct = useCallback(async (productId: string, productData: ProductUpdate) => {
    try {
      setError(null);
      await adminApi.updateProduct(productId, productData);
      await loadProducts(); // Reload products after update
    } catch (err) {
      setError('Failed to update product');
      console.error('Error updating product:', err);
      throw err;
    }
  }, [loadProducts]);

  const deleteProduct = useCallback(async (productId: string) => {
    if (!window.confirm('Are you sure you want to delete this product?')) return;

    try {
      setError(null);
      await adminApi.deleteProduct(productId);
      await loadProducts(); // Reload products after deletion
    } catch (err) {
      setError('Failed to delete product');
      console.error('Error deleting product:', err);
    }
  }, [loadProducts]);

  const bulkOperation = useCallback(async (operation: ProductBulkOperation['operation']) => {
    if (selectedProducts.size === 0) return;

    const reason = prompt(`Please provide a reason for ${operation}:`);
    if (!reason) return;

    try {
      setError(null);
      await adminApi.bulkProductOperation({
        operation,
        product_ids: Array.from(selectedProducts),
        reason,
      });
      setSelectedProducts(new Set()); // Clear selection
      await loadProducts(); // Reload products
    } catch (err) {
      setError(`Failed to ${operation} products`);
      console.error(`Error performing bulk ${operation}:`, err);
    }
  }, [selectedProducts, loadProducts]);

  const validateProduct = useCallback(async (productId: string) => {
    try {
      setError(null);
      const result = await adminApi.validateProduct(productId);
      setValidationResult(result);
    } catch (err) {
      setError('Failed to validate product');
      console.error('Error validating product:', err);
    }
  }, []);

  const clearSelection = useCallback(() => {
    setSelectedProducts(new Set());
  }, []);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  const clearValidationResult = useCallback(() => {
    setValidationResult(null);
  }, []);

  // Load products when filters change
  useEffect(() => {
    loadProducts();
  }, [loadProducts]);

  return {
    // State
    products,
    loading,
    error,
    selectedProducts,
    totalPages,
    totalProducts,
    filters,
    validationResult,
    
    // Actions
    loadProducts,
    handleFilterChange,
    handlePageChange,
    handleSelectProduct,
    handleSelectAllProducts,
    createProduct,
    updateProduct,
    deleteProduct,
    bulkOperation,
    validateProduct,
    clearSelection,
    clearError,
    clearValidationResult,
  };
}
