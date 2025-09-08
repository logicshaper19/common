/**
 * User filtering component
 */
import React from 'react';
import { MagnifyingGlassIcon } from '@heroicons/react/24/outline';
import { UserFilter, UserRole } from '../../../../types/admin';

interface UserFiltersProps {
  filters: UserFilter;
  onFilterChange: (newFilters: Partial<UserFilter>) => void;
}

export function UserFilters({ filters, onFilterChange }: UserFiltersProps) {
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
              placeholder="Search users..."
              value={filters.search || ''}
              onChange={(e) => onFilterChange({ search: e.target.value })}
              className="pl-10 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
            />
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Role
          </label>
          <select
            value={filters.role || ''}
            onChange={(e) => onFilterChange({ role: e.target.value as UserRole || undefined })}
            className="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
          >
            <option value="">All Roles</option>
            <option value="admin">Admin</option>
            <option value="buyer">Buyer</option>
            <option value="seller">Seller</option>
            <option value="viewer">Viewer</option>
            <option value="support">Support</option>
          </select>
        </div>

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
            2FA Status
          </label>
          <select
            value={filters.has_two_factor?.toString() || ''}
            onChange={(e) => onFilterChange({ 
              has_two_factor: e.target.value ? e.target.value === 'true' : undefined 
            })}
            className="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
          >
            <option value="">All 2FA Statuses</option>
            <option value="true">2FA Enabled</option>
            <option value="false">2FA Disabled</option>
          </select>
        </div>
      </div>
    </div>
  );
}
