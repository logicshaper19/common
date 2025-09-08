/**
 * Product management section component
 */
import React, { useState } from 'react';
import { PlusIcon, ArrowUpTrayIcon, ArrowDownTrayIcon } from '@heroicons/react/24/outline';
import { Product, ProductCreate, ProductUpdate } from '../../../../types/admin';
import { useProductManagement } from '../hooks/useProductManagement';
import { ProductFilters } from './ProductFilters';
import { ProductTable } from './ProductTable';
import { ProductBulkActions } from './ProductBulkActions';
import { ProductModal } from './ProductModal';
import { ProductViewModal } from './ProductViewModal';
import { ValidationResultModal } from './ValidationResultModal';
import { Pagination } from '../../user-company-management/components/Pagination';

export function ProductManagementSection() {
  const {
    products,
    loading,
    error,
    selectedProducts,
    totalPages,
    totalProducts,
    filters,
    validationResult,
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
  } = useProductManagement();

  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showViewModal, setShowViewModal] = useState(false);
  const [selectedProduct, setSelectedProduct] = useState<Product | null>(null);

  const handleCreateProduct = async (productData: ProductCreate) => {
    try {
      await createProduct(productData);
      setShowCreateModal(false);
    } catch (err) {
      // Error is handled by the hook
    }
  };

  const handleEditProduct = async (productData: ProductUpdate) => {
    if (!selectedProduct) return;

    try {
      await updateProduct(selectedProduct.id, productData);
      setShowEditModal(false);
      setSelectedProduct(null);
    } catch (err) {
      // Error is handled by the hook
    }
  };

  const openEditModal = (product: Product) => {
    setSelectedProduct(product);
    setShowEditModal(true);
  };

  const openViewModal = (product: Product) => {
    setSelectedProduct(product);
    setShowViewModal(true);
  };

  const handleCloseCreateModal = () => {
    setShowCreateModal(false);
  };

  const handleCloseEditModal = () => {
    setShowEditModal(false);
    setSelectedProduct(null);
  };

  const handleCloseViewModal = () => {
    setShowViewModal(false);
    setSelectedProduct(null);
  };

  const handleExportSelected = () => {
    // Implementation for exporting selected products
    console.log('Exporting selected products:', Array.from(selectedProducts));
  };

  const handleImportProducts = () => {
    // Implementation for importing products
    console.log('Importing products');
  };

  const handleExportAll = () => {
    // Implementation for exporting all products
    console.log('Exporting all products');
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-lg font-medium text-gray-900">Product Catalog Management</h2>
          <p className="text-sm text-gray-500">
            Manage product catalog and validation ({totalProducts} total)
          </p>
        </div>
        <div className="flex space-x-3">
          <button
            onClick={handleImportProducts}
            className="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
          >
            <ArrowUpTrayIcon className="h-4 w-4 mr-2" />
            Import
          </button>
          <button
            onClick={handleExportAll}
            className="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
          >
            <ArrowDownTrayIcon className="h-4 w-4 mr-2" />
            Export All
          </button>
          <button
            onClick={() => setShowCreateModal(true)}
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
          >
            <PlusIcon className="h-4 w-4 mr-2" />
            Create Product
          </button>
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="rounded-md bg-red-50 p-4">
          <div className="flex">
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800">Error</h3>
              <div className="mt-2 text-sm text-red-700">{error}</div>
              <div className="mt-4">
                <button
                  onClick={clearError}
                  className="text-sm font-medium text-red-800 hover:text-red-600"
                >
                  Dismiss
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Filters */}
      <ProductFilters filters={filters} onFilterChange={handleFilterChange} />

      {/* Bulk Actions */}
      {selectedProducts.size > 0 && (
        <ProductBulkActions
          selectedCount={selectedProducts.size}
          onBulkOperation={bulkOperation}
          onClearSelection={clearSelection}
          onExportSelected={handleExportSelected}
        />
      )}

      {/* Product Table */}
      <ProductTable
        products={products}
        selectedProducts={selectedProducts}
        onSelectProduct={handleSelectProduct}
        onSelectAllProducts={handleSelectAllProducts}
        onEditProduct={openEditModal}
        onViewProduct={openViewModal}
        onDeleteProduct={deleteProduct}
        onValidateProduct={validateProduct}
        loading={loading}
      />

      {/* Pagination */}
      {totalPages > 1 && (
        <Pagination
          currentPage={filters.page}
          totalPages={totalPages}
          onPageChange={handlePageChange}
        />
      )}

      {/* Create Product Modal */}
      <ProductModal
        isOpen={showCreateModal}
        onClose={handleCloseCreateModal}
        onSubmit={handleCreateProduct}
        title="Create New Product"
        submitLabel="Create Product"
        mode="create"
      />

      {/* Edit Product Modal */}
      <ProductModal
        isOpen={showEditModal}
        onClose={handleCloseEditModal}
        onSubmit={handleEditProduct}
        title="Edit Product"
        submitLabel="Update Product"
        product={selectedProduct}
        mode="edit"
      />

      {/* View Product Modal */}
      <ProductViewModal
        isOpen={showViewModal}
        onClose={handleCloseViewModal}
        product={selectedProduct}
      />

      {/* Validation Result Modal */}
      <ValidationResultModal
        isOpen={!!validationResult}
        onClose={clearValidationResult}
        validationResult={validationResult}
      />
    </div>
  );
}
