/**
 * Product Catalog Management Interface
 * Comprehensive admin interface for managing products, categories, and validation
 */
import React, { useState, useEffect, useCallback } from 'react';
import {
  MagnifyingGlassIcon,
  PlusIcon,
  PencilIcon,
  TrashIcon,
  EyeIcon,
  FunnelIcon,
  ArrowDownTrayIcon,
  ArrowUpTrayIcon,
  CheckIcon,
  XMarkIcon,
  ExclamationTriangleIcon,
  InformationCircleIcon,
} from '@heroicons/react/24/outline';
import { adminApi } from '../../api/admin';
import {
  Product,
  ProductFilter,
  ProductCreate,
  ProductUpdate,
  ProductBulkOperation,
  ProductValidationResult,
  ProductCategory,
} from '../../types/admin';

interface ProductCatalogManagementProps {
  className?: string;
}

export function ProductCatalogManagement({ className = '' }: ProductCatalogManagementProps) {
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedProducts, setSelectedProducts] = useState<Set<string>>(new Set());
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showViewModal, setShowViewModal] = useState(false);
  const [selectedProduct, setSelectedProduct] = useState<Product | null>(null);
  const [validationResult, setValidationResult] = useState<ProductValidationResult | null>(null);
  
  // Filters and pagination
  const [filters, setFilters] = useState<ProductFilter>({
    page: 1,
    per_page: 20,
  });
  const [totalPages, setTotalPages] = useState(1);
  const [totalProducts, setTotalProducts] = useState(0);

  // Form state
  const [formData, setFormData] = useState<ProductCreate>({
    common_product_id: '',
    name: '',
    description: '',
    category: 'raw_material',
    can_have_composition: false,
    default_unit: 'MT',
    hs_code: '',
  });

  const loadProducts = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await adminApi.getProducts(filters);
      setProducts(response.products);
      setTotalPages(response.total_pages);
      setTotalProducts(response.total);
    } catch (err) {
      setError('Failed to load products');
      console.error('Error loading products:', err);
    } finally {
      setLoading(false);
    }
  }, [filters]);

  useEffect(() => {
    loadProducts();
  }, [loadProducts]);

  const handleFilterChange = (newFilters: Partial<ProductFilter>) => {
    setFilters(prev => ({ ...prev, ...newFilters, page: 1 }));
  };

  const handlePageChange = (page: number) => {
    setFilters(prev => ({ ...prev, page }));
  };

  const handleSelectProduct = (productId: string) => {
    setSelectedProducts(prev => {
      const newSet = new Set(prev);
      if (newSet.has(productId)) {
        newSet.delete(productId);
      } else {
        newSet.add(productId);
      }
      return newSet;
    });
  };

  const handleSelectAll = () => {
    if (selectedProducts.size === products.length) {
      setSelectedProducts(new Set());
    } else {
      setSelectedProducts(new Set(products.map(p => p.id)));
    }
  };

  const handleCreateProduct = async () => {
    try {
      setError(null);
      
      // Validate product first
      const validation = await adminApi.validateProduct(formData);
      setValidationResult(validation);
      
      if (!validation.is_valid) {
        return;
      }

      await adminApi.createProduct(formData);
      setShowCreateModal(false);
      setFormData({
        common_product_id: '',
        name: '',
        description: '',
        category: 'raw_material',
        can_have_composition: false,
        default_unit: 'MT',
        hs_code: '',
      });
      setValidationResult(null);
      await loadProducts();
    } catch (err) {
      setError('Failed to create product');
      console.error('Error creating product:', err);
    }
  };

  const handleEditProduct = async () => {
    if (!selectedProduct) return;

    try {
      setError(null);
      const updateData: ProductUpdate = {
        name: formData.name,
        description: formData.description,
        category: formData.category,
        can_have_composition: formData.can_have_composition,
        default_unit: formData.default_unit,
        hs_code: formData.hs_code,
      };

      await adminApi.updateProduct(selectedProduct.id, updateData);
      setShowEditModal(false);
      setSelectedProduct(null);
      await loadProducts();
    } catch (err) {
      setError('Failed to update product');
      console.error('Error updating product:', err);
    }
  };

  const handleDeleteProduct = async (productId: string) => {
    if (!confirm('Are you sure you want to delete this product?')) return;

    try {
      setError(null);
      await adminApi.deleteProduct(productId);
      await loadProducts();
    } catch (err) {
      setError('Failed to delete product');
      console.error('Error deleting product:', err);
    }
  };

  const handleBulkOperation = async (operation: ProductBulkOperation['operation']) => {
    if (selectedProducts.size === 0) return;

    const reason = prompt(`Please provide a reason for ${operation}:`);
    if (!reason) return;

    try {
      setError(null);
      const bulkOp: ProductBulkOperation = {
        operation,
        product_ids: Array.from(selectedProducts),
        reason,
      };

      await adminApi.bulkProductOperation(bulkOp);
      setSelectedProducts(new Set());
      await loadProducts();
    } catch (err) {
      setError(`Failed to ${operation} products`);
      console.error(`Error with bulk ${operation}:`, err);
    }
  };

  const openEditModal = (product: Product) => {
    setSelectedProduct(product);
    setFormData({
      common_product_id: product.common_product_id,
      name: product.name,
      description: product.description || '',
      category: product.category,
      can_have_composition: product.can_have_composition,
      default_unit: product.default_unit,
      hs_code: product.hs_code || '',
      material_breakdown: product.material_breakdown,
      origin_data_requirements: product.origin_data_requirements,
    });
    setShowEditModal(true);
  };

  const openViewModal = (product: Product) => {
    setSelectedProduct(product);
    setShowViewModal(true);
  };

  const getStatusBadge = (status: Product['status']) => {
    const styles = {
      active: 'bg-green-100 text-green-800',
      inactive: 'bg-gray-100 text-gray-800',
      deprecated: 'bg-red-100 text-red-800',
    };

    return (
      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${styles[status]}`}>
        {status}
      </span>
    );
  };

  const getCategoryBadge = (category: ProductCategory) => {
    const styles = {
      raw_material: 'bg-blue-100 text-blue-800',
      processed: 'bg-yellow-100 text-yellow-800',
      finished_good: 'bg-purple-100 text-purple-800',
    };

    const labels = {
      raw_material: 'Raw Material',
      processed: 'Processed',
      finished_good: 'Finished Good',
    };

    return (
      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${styles[category]}`}>
        {labels[category]}
      </span>
    );
  };

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Product Catalog Management</h1>
          <p className="mt-1 text-sm text-gray-500">
            Manage products, categories, and validation rules
          </p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
        >
          <PlusIcon className="h-4 w-4 mr-2" />
          Add Product
        </button>
      </div>

      {/* Error Alert */}
      {error && (
        <div className="rounded-md bg-red-50 p-4">
          <div className="flex">
            <ExclamationTriangleIcon className="h-5 w-5 text-red-400" />
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800">Error</h3>
              <div className="mt-2 text-sm text-red-700">{error}</div>
            </div>
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="bg-white shadow rounded-lg p-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Search
            </label>
            <div className="relative">
              <MagnifyingGlassIcon className="h-5 w-5 absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
              <input
                type="text"
                placeholder="Search products..."
                value={filters.search || ''}
                onChange={(e) => handleFilterChange({ search: e.target.value })}
                className="pl-10 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Category
            </label>
            <select
              value={filters.category || ''}
              onChange={(e) => handleFilterChange({ category: e.target.value as ProductCategory || undefined })}
              className="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
            >
              <option value="">All Categories</option>
              <option value="raw_material">Raw Material</option>
              <option value="processed">Processed</option>
              <option value="finished_good">Finished Good</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Status
            </label>
            <select
              value={filters.status || ''}
              onChange={(e) => handleFilterChange({ status: e.target.value as Product['status'] || undefined })}
              className="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
            >
              <option value="">All Statuses</option>
              <option value="active">Active</option>
              <option value="inactive">Inactive</option>
              <option value="deprecated">Deprecated</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Composition
            </label>
            <select
              value={filters.can_have_composition?.toString() || ''}
              onChange={(e) => handleFilterChange({ 
                can_have_composition: e.target.value ? e.target.value === 'true' : undefined 
              })}
              className="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
            >
              <option value="">All Types</option>
              <option value="true">Can Have Composition</option>
              <option value="false">Simple Product</option>
            </select>
          </div>
        </div>
      </div>

      {/* Bulk Actions */}
      {selectedProducts.size > 0 && (
        <div className="bg-white shadow rounded-lg p-4">
          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-700">
              {selectedProducts.size} product{selectedProducts.size !== 1 ? 's' : ''} selected
            </span>
            <div className="flex space-x-2">
              <button
                onClick={() => handleBulkOperation('activate')}
                className="inline-flex items-center px-3 py-1.5 border border-gray-300 shadow-sm text-xs font-medium rounded text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
              >
                <CheckIcon className="h-4 w-4 mr-1" />
                Activate
              </button>
              <button
                onClick={() => handleBulkOperation('deactivate')}
                className="inline-flex items-center px-3 py-1.5 border border-gray-300 shadow-sm text-xs font-medium rounded text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
              >
                <XMarkIcon className="h-4 w-4 mr-1" />
                Deactivate
              </button>
              <button
                onClick={() => handleBulkOperation('export')}
                className="inline-flex items-center px-3 py-1.5 border border-gray-300 shadow-sm text-xs font-medium rounded text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
              >
                <ArrowDownTrayIcon className="h-4 w-4 mr-1" />
                Export
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Products Table */}
      <div className="bg-white shadow rounded-lg overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-medium text-gray-900">
            Products ({totalProducts})
          </h3>
        </div>

        {loading ? (
          <div className="p-8 text-center">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
            <p className="mt-2 text-sm text-gray-500">Loading products...</p>
          </div>
        ) : products.length === 0 ? (
          <div className="p-8 text-center">
            <p className="text-gray-500">No products found</p>
          </div>
        ) : (
          <>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left">
                      <input
                        type="checkbox"
                        checked={selectedProducts.size === products.length && products.length > 0}
                        onChange={handleSelectAll}
                        className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                      />
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Product
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Category
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Status
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Usage
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {products.map((product) => (
                    <tr key={product.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4">
                        <input
                          type="checkbox"
                          checked={selectedProducts.has(product.id)}
                          onChange={() => handleSelectProduct(product.id)}
                          className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                        />
                      </td>
                      <td className="px-6 py-4">
                        <div>
                          <div className="text-sm font-medium text-gray-900">
                            {product.name}
                          </div>
                          <div className="text-sm text-gray-500">
                            ID: {product.common_product_id}
                          </div>
                          {product.hs_code && (
                            <div className="text-xs text-gray-400">
                              HS Code: {product.hs_code}
                            </div>
                          )}
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        {getCategoryBadge(product.category)}
                        {product.can_have_composition && (
                          <div className="mt-1">
                            <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-50 text-blue-700">
                              Composition
                            </span>
                          </div>
                        )}
                      </td>
                      <td className="px-6 py-4">
                        {getStatusBadge(product.status)}
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-900">
                        <div>{product.usage_count} times</div>
                        {product.last_used && (
                          <div className="text-xs text-gray-500">
                            Last: {new Date(product.last_used).toLocaleDateString()}
                          </div>
                        )}
                      </td>
                      <td className="px-6 py-4">
                        <div className="flex space-x-2">
                          <button
                            onClick={() => openViewModal(product)}
                            className="text-gray-400 hover:text-gray-600"
                            title="View Details"
                          >
                            <EyeIcon className="h-4 w-4" />
                          </button>
                          <button
                            onClick={() => openEditModal(product)}
                            className="text-primary-400 hover:text-primary-600"
                            title="Edit Product"
                          >
                            <PencilIcon className="h-4 w-4" />
                          </button>
                          <button
                            onClick={() => handleDeleteProduct(product.id)}
                            className="text-red-400 hover:text-red-600"
                            title="Delete Product"
                          >
                            <TrashIcon className="h-4 w-4" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="bg-white px-4 py-3 border-t border-gray-200 sm:px-6">
                <div className="flex items-center justify-between">
                  <div className="flex-1 flex justify-between sm:hidden">
                    <button
                      onClick={() => handlePageChange(filters.page - 1)}
                      disabled={filters.page <= 1}
                      className="relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      Previous
                    </button>
                    <button
                      onClick={() => handlePageChange(filters.page + 1)}
                      disabled={filters.page >= totalPages}
                      className="ml-3 relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      Next
                    </button>
                  </div>
                  <div className="hidden sm:flex-1 sm:flex sm:items-center sm:justify-between">
                    <div>
                      <p className="text-sm text-gray-700">
                        Showing{' '}
                        <span className="font-medium">
                          {(filters.page - 1) * filters.per_page + 1}
                        </span>{' '}
                        to{' '}
                        <span className="font-medium">
                          {Math.min(filters.page * filters.per_page, totalProducts)}
                        </span>{' '}
                        of{' '}
                        <span className="font-medium">{totalProducts}</span>{' '}
                        results
                      </p>
                    </div>
                    <div>
                      <nav className="relative z-0 inline-flex rounded-md shadow-sm -space-x-px">
                        <button
                          onClick={() => handlePageChange(filters.page - 1)}
                          disabled={filters.page <= 1}
                          className="relative inline-flex items-center px-2 py-2 rounded-l-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                          Previous
                        </button>
                        {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                          const page = i + 1;
                          return (
                            <button
                              key={page}
                              onClick={() => handlePageChange(page)}
                              className={`relative inline-flex items-center px-4 py-2 border text-sm font-medium ${
                                page === filters.page
                                  ? 'z-10 bg-primary-50 border-primary-500 text-primary-600'
                                  : 'bg-white border-gray-300 text-gray-500 hover:bg-gray-50'
                              }`}
                            >
                              {page}
                            </button>
                          );
                        })}
                        <button
                          onClick={() => handlePageChange(filters.page + 1)}
                          disabled={filters.page >= totalPages}
                          className="relative inline-flex items-center px-2 py-2 rounded-r-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                          Next
                        </button>
                      </nav>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </>
        )}
      </div>

      {/* Create Product Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 overflow-y-auto">
          <div className="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
            <div className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" onClick={() => setShowCreateModal(false)}></div>

            <div className="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full">
              <div className="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
                <div className="sm:flex sm:items-start">
                  <div className="w-full">
                    <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
                      Create New Product
                    </h3>

                    <div className="space-y-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Product ID *
                        </label>
                        <input
                          type="text"
                          value={formData.common_product_id}
                          onChange={(e) => setFormData(prev => ({ ...prev, common_product_id: e.target.value }))}
                          className="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
                          placeholder="e.g., palm_refined_edible"
                        />
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Product Name *
                        </label>
                        <input
                          type="text"
                          value={formData.name}
                          onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                          className="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
                          placeholder="e.g., Refined Palm Oil"
                        />
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Description
                        </label>
                        <textarea
                          value={formData.description}
                          onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                          rows={3}
                          className="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
                          placeholder="Product description..."
                        />
                      </div>

                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">
                            Category *
                          </label>
                          <select
                            value={formData.category}
                            onChange={(e) => setFormData(prev => ({ ...prev, category: e.target.value as ProductCategory }))}
                            className="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
                          >
                            <option value="raw_material">Raw Material</option>
                            <option value="processed">Processed</option>
                            <option value="finished_good">Finished Good</option>
                          </select>
                        </div>

                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">
                            Default Unit *
                          </label>
                          <input
                            type="text"
                            value={formData.default_unit}
                            onChange={(e) => setFormData(prev => ({ ...prev, default_unit: e.target.value }))}
                            className="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
                            placeholder="e.g., MT, KG, L"
                          />
                        </div>
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          HS Code
                        </label>
                        <input
                          type="text"
                          value={formData.hs_code}
                          onChange={(e) => setFormData(prev => ({ ...prev, hs_code: e.target.value }))}
                          className="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
                          placeholder="e.g., 15119010"
                        />
                      </div>

                      <div>
                        <label className="flex items-center">
                          <input
                            type="checkbox"
                            checked={formData.can_have_composition}
                            onChange={(e) => setFormData(prev => ({ ...prev, can_have_composition: e.target.checked }))}
                            className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                          />
                          <span className="ml-2 text-sm text-gray-700">
                            Can have composition (multiple materials)
                          </span>
                        </label>
                      </div>

                      {/* Validation Results */}
                      {validationResult && (
                        <div className="space-y-2">
                          {validationResult.errors.length > 0 && (
                            <div className="rounded-md bg-red-50 p-3">
                              <div className="flex">
                                <ExclamationTriangleIcon className="h-5 w-5 text-red-400" />
                                <div className="ml-3">
                                  <h4 className="text-sm font-medium text-red-800">Validation Errors</h4>
                                  <ul className="mt-1 text-sm text-red-700 list-disc list-inside">
                                    {validationResult.errors.map((error, index) => (
                                      <li key={index}>{error}</li>
                                    ))}
                                  </ul>
                                </div>
                              </div>
                            </div>
                          )}

                          {validationResult.warnings.length > 0 && (
                            <div className="rounded-md bg-yellow-50 p-3">
                              <div className="flex">
                                <ExclamationTriangleIcon className="h-5 w-5 text-yellow-400" />
                                <div className="ml-3">
                                  <h4 className="text-sm font-medium text-yellow-800">Warnings</h4>
                                  <ul className="mt-1 text-sm text-yellow-700 list-disc list-inside">
                                    {validationResult.warnings.map((warning, index) => (
                                      <li key={index}>{warning}</li>
                                    ))}
                                  </ul>
                                </div>
                              </div>
                            </div>
                          )}

                          {validationResult.suggestions.length > 0 && (
                            <div className="rounded-md bg-blue-50 p-3">
                              <div className="flex">
                                <InformationCircleIcon className="h-5 w-5 text-blue-400" />
                                <div className="ml-3">
                                  <h4 className="text-sm font-medium text-blue-800">Suggestions</h4>
                                  <ul className="mt-1 text-sm text-blue-700 list-disc list-inside">
                                    {validationResult.suggestions.map((suggestion, index) => (
                                      <li key={index}>{suggestion}</li>
                                    ))}
                                  </ul>
                                </div>
                              </div>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </div>
              <div className="bg-gray-50 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
                <button
                  onClick={handleCreateProduct}
                  disabled={!formData.common_product_id || !formData.name || !formData.category}
                  className="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-primary-600 text-base font-medium text-white hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 sm:ml-3 sm:w-auto sm:text-sm disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Create Product
                </button>
                <button
                  onClick={() => {
                    setShowCreateModal(false);
                    setValidationResult(null);
                  }}
                  className="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 sm:mt-0 sm:ml-3 sm:w-auto sm:text-sm"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Edit Product Modal */}
      {showEditModal && selectedProduct && (
        <div className="fixed inset-0 z-50 overflow-y-auto">
          <div className="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
            <div className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" onClick={() => setShowEditModal(false)}></div>

            <div className="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full">
              <div className="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
                <div className="sm:flex sm:items-start">
                  <div className="w-full">
                    <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
                      Edit Product: {selectedProduct.name}
                    </h3>

                    <div className="space-y-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Product ID
                        </label>
                        <input
                          type="text"
                          value={formData.common_product_id}
                          disabled
                          className="block w-full rounded-md border-gray-300 bg-gray-50 shadow-sm sm:text-sm"
                        />
                        <p className="mt-1 text-xs text-gray-500">Product ID cannot be changed</p>
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Product Name *
                        </label>
                        <input
                          type="text"
                          value={formData.name}
                          onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                          className="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
                        />
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Description
                        </label>
                        <textarea
                          value={formData.description}
                          onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                          rows={3}
                          className="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
                        />
                      </div>

                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">
                            Category *
                          </label>
                          <select
                            value={formData.category}
                            onChange={(e) => setFormData(prev => ({ ...prev, category: e.target.value as ProductCategory }))}
                            className="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
                          >
                            <option value="raw_material">Raw Material</option>
                            <option value="processed">Processed</option>
                            <option value="finished_good">Finished Good</option>
                          </select>
                        </div>

                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">
                            Default Unit *
                          </label>
                          <input
                            type="text"
                            value={formData.default_unit}
                            onChange={(e) => setFormData(prev => ({ ...prev, default_unit: e.target.value }))}
                            className="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
                          />
                        </div>
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          HS Code
                        </label>
                        <input
                          type="text"
                          value={formData.hs_code}
                          onChange={(e) => setFormData(prev => ({ ...prev, hs_code: e.target.value }))}
                          className="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
                        />
                      </div>

                      <div>
                        <label className="flex items-center">
                          <input
                            type="checkbox"
                            checked={formData.can_have_composition}
                            onChange={(e) => setFormData(prev => ({ ...prev, can_have_composition: e.target.checked }))}
                            className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                          />
                          <span className="ml-2 text-sm text-gray-700">
                            Can have composition (multiple materials)
                          </span>
                        </label>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
              <div className="bg-gray-50 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
                <button
                  onClick={handleEditProduct}
                  disabled={!formData.name || !formData.category}
                  className="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-primary-600 text-base font-medium text-white hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 sm:ml-3 sm:w-auto sm:text-sm disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Update Product
                </button>
                <button
                  onClick={() => setShowEditModal(false)}
                  className="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 sm:mt-0 sm:ml-3 sm:w-auto sm:text-sm"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* View Product Modal */}
      {showViewModal && selectedProduct && (
        <div className="fixed inset-0 z-50 overflow-y-auto">
          <div className="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
            <div className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" onClick={() => setShowViewModal(false)}></div>

            <div className="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-2xl sm:w-full">
              <div className="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
                <div className="sm:flex sm:items-start">
                  <div className="w-full">
                    <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
                      Product Details: {selectedProduct.name}
                    </h3>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <div className="space-y-4">
                        <div>
                          <label className="block text-sm font-medium text-gray-700">Product ID</label>
                          <p className="mt-1 text-sm text-gray-900">{selectedProduct.common_product_id}</p>
                        </div>

                        <div>
                          <label className="block text-sm font-medium text-gray-700">Name</label>
                          <p className="mt-1 text-sm text-gray-900">{selectedProduct.name}</p>
                        </div>

                        <div>
                          <label className="block text-sm font-medium text-gray-700">Description</label>
                          <p className="mt-1 text-sm text-gray-900">{selectedProduct.description || 'No description'}</p>
                        </div>

                        <div>
                          <label className="block text-sm font-medium text-gray-700">Category</label>
                          <div className="mt-1">{getCategoryBadge(selectedProduct.category)}</div>
                        </div>

                        <div>
                          <label className="block text-sm font-medium text-gray-700">Status</label>
                          <div className="mt-1">{getStatusBadge(selectedProduct.status)}</div>
                        </div>
                      </div>

                      <div className="space-y-4">
                        <div>
                          <label className="block text-sm font-medium text-gray-700">Default Unit</label>
                          <p className="mt-1 text-sm text-gray-900">{selectedProduct.default_unit}</p>
                        </div>

                        <div>
                          <label className="block text-sm font-medium text-gray-700">HS Code</label>
                          <p className="mt-1 text-sm text-gray-900">{selectedProduct.hs_code || 'Not specified'}</p>
                        </div>

                        <div>
                          <label className="block text-sm font-medium text-gray-700">Composition</label>
                          <p className="mt-1 text-sm text-gray-900">
                            {selectedProduct.can_have_composition ? 'Can have composition' : 'Simple product'}
                          </p>
                        </div>

                        <div>
                          <label className="block text-sm font-medium text-gray-700">Usage</label>
                          <p className="mt-1 text-sm text-gray-900">
                            {selectedProduct.usage_count} times
                            {selectedProduct.last_used && (
                              <span className="block text-xs text-gray-500">
                                Last used: {new Date(selectedProduct.last_used).toLocaleDateString()}
                              </span>
                            )}
                          </p>
                        </div>

                        <div>
                          <label className="block text-sm font-medium text-gray-700">Created</label>
                          <p className="mt-1 text-sm text-gray-900">
                            {new Date(selectedProduct.created_at).toLocaleDateString()}
                          </p>
                        </div>

                        <div>
                          <label className="block text-sm font-medium text-gray-700">Last Updated</label>
                          <p className="mt-1 text-sm text-gray-900">
                            {new Date(selectedProduct.updated_at).toLocaleDateString()}
                          </p>
                        </div>
                      </div>
                    </div>

                    {/* Material Breakdown */}
                    {selectedProduct.material_breakdown && (
                      <div className="mt-6">
                        <label className="block text-sm font-medium text-gray-700 mb-2">Material Breakdown</label>
                        <div className="bg-gray-50 rounded-lg p-4">
                          <div className="space-y-2">
                            {Object.entries(selectedProduct.material_breakdown).map(([material, breakdown]) => (
                              <div key={material} className="flex justify-between items-center">
                                <span className="text-sm font-medium text-gray-900">{material}</span>
                                <span className="text-sm text-gray-600">
                                  {breakdown.min_percentage}% - {breakdown.max_percentage}%
                                  {breakdown.required && <span className="text-red-500 ml-1">*</span>}
                                </span>
                              </div>
                            ))}
                          </div>
                        </div>
                      </div>
                    )}

                    {/* Origin Data Requirements */}
                    {selectedProduct.origin_data_requirements && (
                      <div className="mt-6">
                        <label className="block text-sm font-medium text-gray-700 mb-2">Origin Data Requirements</label>
                        <div className="bg-gray-50 rounded-lg p-4">
                          <div className="grid grid-cols-2 gap-4 text-sm">
                            <div>
                              <span className="font-medium">Coordinates:</span>
                              <span className="ml-2">{selectedProduct.origin_data_requirements.coordinates || 'Not specified'}</span>
                            </div>
                            <div>
                              <span className="font-medium">Batch Tracking:</span>
                              <span className="ml-2">{selectedProduct.origin_data_requirements.batch_tracking ? 'Required' : 'Not required'}</span>
                            </div>
                            <div>
                              <span className="font-medium">Supplier Verification:</span>
                              <span className="ml-2">{selectedProduct.origin_data_requirements.supplier_verification ? 'Required' : 'Not required'}</span>
                            </div>
                            {selectedProduct.origin_data_requirements.certifications && (
                              <div className="col-span-2">
                                <span className="font-medium">Certifications:</span>
                                <div className="mt-1 flex flex-wrap gap-1">
                                  {selectedProduct.origin_data_requirements.certifications.map((cert, index) => (
                                    <span key={index} className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800">
                                      {cert}
                                    </span>
                                  ))}
                                </div>
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>
              <div className="bg-gray-50 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
                <button
                  onClick={() => openEditModal(selectedProduct)}
                  className="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-primary-600 text-base font-medium text-white hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 sm:ml-3 sm:w-auto sm:text-sm"
                >
                  Edit Product
                </button>
                <button
                  onClick={() => setShowViewModal(false)}
                  className="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 sm:mt-0 sm:ml-3 sm:w-auto sm:text-sm"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
