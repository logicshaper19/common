/**
 * Company table component
 */
import React from 'react';
import {
  PencilIcon,
  EyeIcon,
  EnvelopeIcon,
  PhoneIcon,
  GlobeAltIcon,
} from '@heroicons/react/24/outline';
import { Company } from '../../../../types/admin';
import { formatTimeAgo } from '../../../../lib/utils';
import {
  getCompanyTypeBadge,
  getSubscriptionBadge,
  getComplianceBadge,
  getStatusIcon,
  getVerificationBadge,
} from '../utils/badges';

interface CompanyTableProps {
  companies: Company[];
  selectedCompanies: Set<string>;
  onSelectCompany: (companyId: string) => void;
  onSelectAllCompanies: () => void;
  onEditCompany: (company: Company) => void;
  loading: boolean;
}

export function CompanyTable({
  companies,
  selectedCompanies,
  onSelectCompany,
  onSelectAllCompanies,
  onEditCompany,
  loading,
}: CompanyTableProps) {
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
                checked={selectedCompanies.size === companies.length && companies.length > 0}
                onChange={onSelectAllCompanies}
                className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
              />
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Company
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Type
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Subscription
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Status
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Compliance
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Created
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Actions
            </th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {companies.map((company) => (
            <tr key={company.id} className="hover:bg-gray-50">
              <td className="px-6 py-4">
                <input
                  type="checkbox"
                  checked={selectedCompanies.has(company.id)}
                  onChange={() => onSelectCompany(company.id)}
                  className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                />
              </td>
              <td className="px-6 py-4">
                <div className="flex items-center">
                  <div className="flex-shrink-0 h-10 w-10">
                    <div className="h-10 w-10 rounded-lg bg-gray-300 flex items-center justify-center">
                      <span className="text-sm font-medium text-gray-700">
                        {company.name.charAt(0).toUpperCase()}
                      </span>
                    </div>
                  </div>
                  <div className="ml-4">
                    <div className="text-sm font-medium text-gray-900">
                      {company.name}
                    </div>
                    <div className="text-sm text-gray-500">
                      {company.country && (
                        <span className="inline-flex items-center">
                          <GlobeAltIcon className="h-4 w-4 mr-1" />
                          {company.country}
                        </span>
                      )}
                    </div>
                    {company.website && (
                      <div className="text-sm text-gray-500">
                        <a
                          href={company.website}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-primary-600 hover:text-primary-900"
                        >
                          {company.website}
                        </a>
                      </div>
                    )}
                  </div>
                </div>
              </td>
              <td className="px-6 py-4">
                {getCompanyTypeBadge(company.company_type)}
              </td>
              <td className="px-6 py-4">
                {getSubscriptionBadge(company.subscription_tier)}
              </td>
              <td className="px-6 py-4">
                <div className="flex flex-col space-y-1">
                  <div className="flex items-center">
                    {getStatusIcon(company.is_active)}
                    <span className={`ml-2 text-sm ${company.is_active ? 'text-green-600' : 'text-red-600'}`}>
                      {company.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </div>
                  {getVerificationBadge(company.is_verified)}
                </div>
              </td>
              <td className="px-6 py-4">
                {getComplianceBadge(company.compliance_status)}
              </td>
              <td className="px-6 py-4 text-sm text-gray-500">
                {formatTimeAgo(company.created_at)}
              </td>
              <td className="px-6 py-4 text-sm font-medium">
                <div className="flex space-x-2">
                  <button
                    onClick={() => onEditCompany(company)}
                    className="text-primary-600 hover:text-primary-900"
                    title="Edit company"
                  >
                    <PencilIcon className="h-4 w-4" />
                  </button>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      {companies.length === 0 && (
        <div className="text-center py-12">
          <EyeIcon className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">No companies found</h3>
          <p className="mt-1 text-sm text-gray-500">
            Try adjusting your search or filter criteria.
          </p>
        </div>
      )}
    </div>
  );
}
