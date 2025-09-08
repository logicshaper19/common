/**
 * Product filtering component
 */
import React from 'react';
import { MagnifyingGlassIcon, FunnelIcon } from '@heroicons/react/24/outline';
import { ProductFilter, ProductCategory, ProductStatus } from '../../../../types/admin';

interface ProductFiltersProps {
  filters: ProductFilter;
  onFilterChange: (newFilters: Partial<ProductFilter>) => void;
}

export function ProductFilters({ filters, onFilterChange }: ProductFiltersProps) {
  return (
    <div className="bg-white shadow rounded-lg p-6">
      <div className="flex items-center mb-4">
        <FunnelIcon className="h-5 w-5 text-gray-400 mr-2" />
        <h3 className="text-lg font-medium text-gray-900">Filters</h3>
      </div>

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
              onChange={(e) => onFilterChange({ search: e.target.value })}
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
            onChange={(e) => onFilterChange({ category: e.target.value as ProductCategory || undefined })}
            className="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
          >
            <option value="">All Categories</option>
            <option value="raw_material">Raw Material</option>
            <option value="intermediate_product">Intermediate Product</option>
            <option value="finished_product">Finished Product</option>
            <option value="packaging">Packaging</option>
            <option value="service">Service</option>
            <option value="component">Component</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Status
          </label>
          <select
            value={filters.status || ''}
            onChange={(e) => onFilterChange({ status: e.target.value as ProductStatus || undefined })}
            className="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
          >
            <option value="">All Statuses</option>
            <option value="active">Active</option>
            <option value="inactive">Inactive</option>
            <option value="pending_approval">Pending Approval</option>
            <option value="deprecated">Deprecated</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            HS Code
          </label>
          <input
            type="text"
            placeholder="Filter by HS code..."
            value={filters.hs_code || ''}
            onChange={(e) => onFilterChange({ hs_code: e.target.value })}
            className="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
          />
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Composition
          </label>
          <select
            value={filters.can_have_composition?.toString() || ''}
            onChange={(e) => onFilterChange({ 
              can_have_composition: e.target.value ? e.target.value === 'true' : undefined 
            })}
            className="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
          >
            <option value="">All Products</option>
            <option value="true">Can Have Composition</option>
            <option value="false">No Composition</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Usage Count (Min)
          </label>
          <input
            type="number"
            placeholder="Minimum usage..."
            value={filters.min_usage_count || ''}
            onChange={(e) => onFilterChange({ 
              min_usage_count: e.target.value ? parseInt(e.target.value) : undefined 
            })}
            className="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
            min="0"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Default Unit
          </label>
          <input
            type="text"
            placeholder="Filter by unit..."
            value={filters.default_unit || ''}
            onChange={(e) => onFilterChange({ default_unit: e.target.value })}
            className="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
          />
        </div>
      </div>

      {/* Clear Filters */}
      {(filters.search || filters.category || filters.status || filters.hs_code || 
        filters.can_have_composition !== undefined || filters.min_usage_count || filters.default_unit) && (
        <div className="mt-4 pt-4 border-t border-gray-200">
          <button
            onClick={() => onFilterChange({
              search: undefined,
              category: undefined,
              status: undefined,
              hs_code: undefined,
              can_have_composition: undefined,
              min_usage_count: undefined,
              default_unit: undefined,
            })}
            className="text-sm text-primary-600 hover:text-primary-900"
          >
            Clear all filters
          </button>
        </div>
      )}
    </div>
  );
}
