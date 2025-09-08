/**
 * Product view modal component
 */
import React from 'react';
import { XMarkIcon } from '@heroicons/react/24/outline';
import { Product } from '../../../../types/admin';
import { formatTimeAgo } from '../../../../lib/utils';
import {
  getCategoryBadge,
  getStatusBadge,
  getCompositionBadge,
} from '../utils/badges';

interface ProductViewModalProps {
  isOpen: boolean;
  onClose: () => void;
  product: Product | null;
}

export function ProductViewModal({ isOpen, onClose, product }: ProductViewModalProps) {
  if (!isOpen || !product) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
        <div className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" onClick={onClose} />

        <span className="hidden sm:inline-block sm:align-middle sm:h-screen">&#8203;</span>

        <div className="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-2xl sm:w-full">
          <div className="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-lg font-medium text-gray-900">Product Details</h3>
              <button
                type="button"
                onClick={onClose}
                className="text-gray-400 hover:text-gray-600"
              >
                <XMarkIcon className="h-6 w-6" />
              </button>
            </div>

            <div className="space-y-6">
              {/* Basic Information */}
              <div>
                <h4 className="text-sm font-medium text-gray-900 mb-3">Basic Information</h4>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-500">Product ID</label>
                    <p className="mt-1 text-sm text-gray-900">{product.common_product_id}</p>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-500">Name</label>
                    <p className="mt-1 text-sm text-gray-900">{product.name}</p>
                  </div>
                  <div className="col-span-2">
                    <label className="block text-sm font-medium text-gray-500">Description</label>
                    <p className="mt-1 text-sm text-gray-900">{product.description || 'No description provided'}</p>
                  </div>
                </div>
              </div>

              {/* Classification */}
              <div>
                <h4 className="text-sm font-medium text-gray-900 mb-3">Classification</h4>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-500">Category</label>
                    <div className="mt-1">
                      {getCategoryBadge(product.category)}
                    </div>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-500">Status</label>
                    <div className="mt-1">
                      {getStatusBadge(product.status)}
                    </div>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-500">Default Unit</label>
                    <p className="mt-1 text-sm text-gray-900">{product.default_unit}</p>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-500">HS Code</label>
                    <p className="mt-1 text-sm text-gray-900">{product.hs_code || 'Not specified'}</p>
                  </div>
                </div>
              </div>

              {/* Properties */}
              <div>
                <h4 className="text-sm font-medium text-gray-900 mb-3">Properties</h4>
                <div className="space-y-2">
                  <div className="flex items-center">
                    <span className="text-sm text-gray-500 w-32">Composition:</span>
                    {getCompositionBadge(product.can_have_composition) || (
                      <span className="text-sm text-gray-900">Not allowed</span>
                    )}
                  </div>
                </div>
              </div>

              {/* Usage Statistics */}
              <div>
                <h4 className="text-sm font-medium text-gray-900 mb-3">Usage Statistics</h4>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-500">Usage Count</label>
                    <p className="mt-1 text-sm text-gray-900">{product.usage_count} times</p>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-500">Last Used</label>
                    <p className="mt-1 text-sm text-gray-900">
                      {product.last_used ? formatTimeAgo(product.last_used) : 'Never'}
                    </p>
                  </div>
                </div>
              </div>

              {/* Timestamps */}
              <div>
                <h4 className="text-sm font-medium text-gray-900 mb-3">Timestamps</h4>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-500">Created</label>
                    <p className="mt-1 text-sm text-gray-900">{formatTimeAgo(product.created_at)}</p>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-500">Last Updated</label>
                    <p className="mt-1 text-sm text-gray-900">{formatTimeAgo(product.updated_at)}</p>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-gray-50 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
            <button
              type="button"
              onClick={onClose}
              className="w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 sm:w-auto sm:text-sm"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
