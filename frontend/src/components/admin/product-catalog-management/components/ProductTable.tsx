/**
 * Product table component
 */
import React from 'react';
import {
  PencilIcon,
  TrashIcon,
  EyeIcon,
  CheckIcon,
} from '@heroicons/react/24/outline';
import { Product } from '../../../../types/admin';
import { formatTimeAgo } from '../../../../lib/utils';
import {
  getCategoryBadge,
  getStatusBadge,
  getCompositionBadge,
} from '../utils/badges';

interface ProductTableProps {
  products: Product[];
  selectedProducts: Set<string>;
  onSelectProduct: (productId: string) => void;
  onSelectAllProducts: () => void;
  onEditProduct: (product: Product) => void;
  onViewProduct: (product: Product) => void;
  onDeleteProduct: (productId: string) => void;
  onValidateProduct: (productId: string) => void;
  loading: boolean;
}

export function ProductTable({
  products,
  selectedProducts,
  onSelectProduct,
  onSelectAllProducts,
  onEditProduct,
  onViewProduct,
  onDeleteProduct,
  onValidateProduct,
  loading,
}: ProductTableProps) {
  if (loading) {
    return (
      <div className="bg-white shadow rounded-lg p-6">
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-1/4 mb-4"></div>
          <div className="space-y-3">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="h-4 bg-gray-200 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white shadow rounded-lg overflow-hidden">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-6 py-3 text-left">
              <input
                type="checkbox"
                checked={selectedProducts.size === products.length && products.length > 0}
                onChange={onSelectAllProducts}
                className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
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
                  onChange={() => onSelectProduct(product.id)}
                  className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
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
                  <div className="text-xs text-gray-400">
                    Unit: {product.default_unit}
                  </div>
                </div>
              </td>
              <td className="px-6 py-4">
                <div className="space-y-1">
                  {getCategoryBadge(product.category)}
                  {getCompositionBadge(product.can_have_composition)}
                </div>
              </td>
              <td className="px-6 py-4">
                {getStatusBadge(product.status)}
              </td>
              <td className="px-6 py-4 text-sm text-gray-900">
                <div>{product.usage_count} times</div>
                {product.last_used && (
                  <div className="text-xs text-gray-500">
                    Last: {formatTimeAgo(product.last_used)}
                  </div>
                )}
              </td>
              <td className="px-6 py-4">
                <div className="flex space-x-2">
                  <button
                    onClick={() => onViewProduct(product)}
                    className="text-gray-400 hover:text-gray-600"
                    title="View Details"
                  >
                    <EyeIcon className="h-4 w-4" />
                  </button>
                  <button
                    onClick={() => onEditProduct(product)}
                    className="text-primary-600 hover:text-primary-900"
                    title="Edit product"
                  >
                    <PencilIcon className="h-4 w-4" />
                  </button>
                  <button
                    onClick={() => onValidateProduct(product.id)}
                    className="text-blue-600 hover:text-blue-900"
                    title="Validate product"
                  >
                    <CheckIcon className="h-4 w-4" />
                  </button>
                  <button
                    onClick={() => onDeleteProduct(product.id)}
                    className="text-red-600 hover:text-red-900"
                    title="Delete product"
                  >
                    <TrashIcon className="h-4 w-4" />
                  </button>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      {products.length === 0 && (
        <div className="text-center py-12">
          <EyeIcon className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">No products found</h3>
          <p className="mt-1 text-sm text-gray-500">
            Try adjusting your search or filter criteria.
          </p>
        </div>
      )}
    </div>
  );
}
