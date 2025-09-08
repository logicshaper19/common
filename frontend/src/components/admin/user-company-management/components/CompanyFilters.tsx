/**
 * Company filtering component
 */
import React from 'react';
import { MagnifyingGlassIcon } from '@heroicons/react/24/outline';
import { CompanyFilter, CompanyType, SubscriptionTier, ComplianceStatus } from '../../../../types/admin';

interface CompanyFiltersProps {
  filters: CompanyFilter;
  onFilterChange: (newFilters: Partial<CompanyFilter>) => void;
}

export function CompanyFilters({ filters, onFilterChange }: CompanyFiltersProps) {
  return (
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
              placeholder="Search companies..."
              value={filters.search || ''}
              onChange={(e) => onFilterChange({ search: e.target.value })}
              className="pl-10 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
            />
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Company Type
          </label>
          <select
            value={filters.company_type || ''}
            onChange={(e) => onFilterChange({ company_type: e.target.value as CompanyType || undefined })}
            className="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
          >
            <option value="">All Types</option>
            <option value="brand">Brand</option>
            <option value="manufacturer">Manufacturer</option>
            <option value="supplier">Supplier</option>
            <option value="distributor">Distributor</option>
            <option value="retailer">Retailer</option>
            <option value="service_provider">Service Provider</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Subscription Tier
          </label>
          <select
            value={filters.subscription_tier || ''}
            onChange={(e) => onFilterChange({ subscription_tier: e.target.value as SubscriptionTier || undefined })}
            className="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
          >
            <option value="">All Tiers</option>
            <option value="free">Free</option>
            <option value="basic">Basic</option>
            <option value="professional">Professional</option>
            <option value="enterprise">Enterprise</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Compliance Status
          </label>
          <select
            value={filters.compliance_status || ''}
            onChange={(e) => onFilterChange({ compliance_status: e.target.value as ComplianceStatus || undefined })}
            className="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
          >
            <option value="">All Statuses</option>
            <option value="compliant">Compliant</option>
            <option value="non_compliant">Non-Compliant</option>
            <option value="pending_review">Pending Review</option>
            <option value="under_review">Under Review</option>
            <option value="requires_action">Requires Action</option>
          </select>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Status
          </label>
          <select
            value={filters.is_active?.toString() || ''}
            onChange={(e) => onFilterChange({ 
              is_active: e.target.value ? e.target.value === 'true' : undefined 
            })}
            className="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
          >
            <option value="">All Statuses</option>
            <option value="true">Active</option>
            <option value="false">Inactive</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Verification Status
          </label>
          <select
            value={filters.is_verified?.toString() || ''}
            onChange={(e) => onFilterChange({ 
              is_verified: e.target.value ? e.target.value === 'true' : undefined 
            })}
            className="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
          >
            <option value="">All Verification Statuses</option>
            <option value="true">Verified</option>
            <option value="false">Unverified</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Country
          </label>
          <input
            type="text"
            placeholder="Filter by country..."
            value={filters.country || ''}
            onChange={(e) => onFilterChange({ country: e.target.value })}
            className="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
          />
        </div>
      </div>
    </div>
  );
}
