/**
 * Refactored User and Company Management Dashboard
 * Clean, modular architecture with focused components and custom hooks
 */
import React, { useState } from 'react';
import {
  UserIcon,
  BuildingOfficeIcon,
  ExclamationTriangleIcon,
} from '@heroicons/react/24/outline';
import { UserManagementSection } from './components/UserManagementSection';
import { CompanyManagementSection } from './components/CompanyManagementSection';

interface UserCompanyManagementProps {
  className?: string;
}

export function UserCompanyManagement({ className = '' }: UserCompanyManagementProps) {
  const [activeTab, setActiveTab] = useState<'users' | 'companies'>('users');

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">User & Company Management</h1>
        <p className="text-gray-600">
          Comprehensive admin interface for user and company oversight
        </p>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          <button
            onClick={() => setActiveTab('users')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'users'
                ? 'border-primary-500 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            <UserIcon className="h-5 w-5 inline mr-2" />
            Users
          </button>
          <button
            onClick={() => setActiveTab('companies')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'companies'
                ? 'border-primary-500 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            <BuildingOfficeIcon className="h-5 w-5 inline mr-2" />
            Companies
          </button>
        </nav>
      </div>

      {/* Tab Content */}
      {activeTab === 'users' && <UserManagementSection />}
      {activeTab === 'companies' && <CompanyManagementSection />}
    </div>
  );
}
