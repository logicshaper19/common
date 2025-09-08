/**
 * Company edit modal component
 */
import React, { useState, useEffect } from 'react';
import { XMarkIcon } from '@heroicons/react/24/outline';
import {
  Company,
  CompanyCreate,
  CompanyUpdate,
  CompanyType,
  SubscriptionTier,
  ComplianceStatus,
} from '../../../../types/admin';
import { INDUSTRY_SECTORS, getSubcategoriesForSector } from '../../../../constants/industries';

interface CompanyModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: CompanyCreate | CompanyUpdate) => void;
  company: Company | null;
  mode: 'create' | 'edit';
}

export function CompanyModal({
  isOpen,
  onClose,
  onSubmit,
  company,
  mode,
}: CompanyModalProps) {
  const [formData, setFormData] = useState<CompanyCreate | CompanyUpdate>({
    name: '',
    email: '',
    company_type: 'trader_aggregator',
    subscription_tier: 'free',
    compliance_status: 'pending_review',
    is_active: true,
    is_verified: false,
    industry_sector: '',
    industry_subcategory: '',
    address_street: '',
    address_city: '',
    address_state: '',
    address_postal_code: '',
    address_country: '',
  });

  useEffect(() => {
    if (mode === 'edit' && company) {
      setFormData({
        name: company.name,
        email: company.email,
        company_type: company.company_type,
        subscription_tier: company.subscription_tier,
        compliance_status: company.compliance_status,
        is_active: company.is_active,
        is_verified: company.is_verified,
        phone: company.phone || undefined,
        website: company.website || undefined,
        country: company.country || undefined,
        industry_sector: company.industry_sector || '',
        industry_subcategory: company.industry_subcategory || '',
        address_street: company.address_street || '',
        address_city: company.address_city || '',
        address_state: company.address_state || '',
        address_postal_code: company.address_postal_code || '',
        address_country: company.address_country || '',
      });
    } else if (mode === 'create') {
      setFormData({
        name: '',
        email: '',
        company_type: 'trader_aggregator',
        subscription_tier: 'free',
        compliance_status: 'pending_review',
        is_active: true,
        is_verified: false,
        industry_sector: '',
        industry_subcategory: '',
        address_street: '',
        address_city: '',
        address_state: '',
        address_postal_code: '',
        address_country: '',
      });
    }
  }, [company, mode]);

  if (!isOpen) return null;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit(formData);
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
        <div className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" onClick={onClose} />

        <span className="hidden sm:inline-block sm:align-middle sm:h-screen">&#8203;</span>

        <div className="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full">
          <form onSubmit={handleSubmit}>
            <div className="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-medium text-gray-900">
                  {mode === 'create' ? 'Create New Company' : 'Edit Company'}
                </h3>
                <button
                  type="button"
                  onClick={onClose}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <XMarkIcon className="h-6 w-6" />
                </button>
              </div>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Company Name
                  </label>
                  <input
                    type="text"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    className="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Email Address
                  </label>
                  <input
                    type="email"
                    value={formData.email || ''}
                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                    className="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
                    required
                    disabled={mode === 'edit'}
                  />
                  {mode === 'edit' && (
                    <p className="mt-1 text-sm text-gray-500">Email cannot be changed after creation</p>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Company Type
                  </label>
                  <select
                    value={formData.company_type}
                    onChange={(e) => setFormData({ ...formData, company_type: e.target.value as CompanyType })}
                    className="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
                    required
                  >
                    <option value="plantation_grower">Plantation / Grower</option>
                    <option value="smallholder_cooperative">Smallholder / Cooperative</option>
                    <option value="mill_processor">Mill / Processor</option>
                    <option value="refinery_crusher">Refinery / Crusher</option>
                    <option value="trader_aggregator">Trader / Aggregator</option>
                    <option value="oleochemical_producer">Oleochemical Producer</option>
                    <option value="manufacturer">Manufacturer</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Subscription Tier
                  </label>
                  <select
                    value={formData.subscription_tier}
                    onChange={(e) => setFormData({ ...formData, subscription_tier: e.target.value as SubscriptionTier })}
                    className="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
                    required
                  >
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
                    value={formData.compliance_status}
                    onChange={(e) => setFormData({ ...formData, compliance_status: e.target.value as ComplianceStatus })}
                    className="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
                    required
                  >
                    <option value="compliant">Compliant</option>
                    <option value="non_compliant">Non-Compliant</option>
                    <option value="pending_review">Pending Review</option>
                    <option value="under_review">Under Review</option>
                    <option value="requires_action">Requires Action</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Phone Number
                  </label>
                  <input
                    type="tel"
                    value={formData.phone || ''}
                    onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                    className="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
                    placeholder="+1 (555) 123-4567"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Website
                  </label>
                  <input
                    type="url"
                    value={formData.website || ''}
                    onChange={(e) => setFormData({ ...formData, website: e.target.value })}
                    className="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
                    placeholder="https://example.com"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Country
                  </label>
                  <input
                    type="text"
                    value={formData.country || ''}
                    onChange={(e) => setFormData({ ...formData, country: e.target.value })}
                    className="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
                    placeholder="United States"
                  />
                </div>

                {/* Industry Information */}
                <div className="col-span-2">
                  <h3 className="text-lg font-medium text-gray-900 mb-4 border-b border-gray-200 pb-2">
                    Industry Information
                  </h3>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Industry Sector
                  </label>
                  <select
                    value={formData.industry_sector || ''}
                    onChange={(e) => {
                      setFormData({
                        ...formData,
                        industry_sector: e.target.value,
                        industry_subcategory: '' // Reset subcategory when sector changes
                      });
                    }}
                    className="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
                  >
                    <option value="">Select Industry Sector</option>
                    {INDUSTRY_SECTORS.map((sector) => (
                      <option key={sector} value={sector}>
                        {sector}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Industry Subcategory
                  </label>
                  <select
                    value={formData.industry_subcategory || ''}
                    onChange={(e) => setFormData({ ...formData, industry_subcategory: e.target.value })}
                    className="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
                    disabled={!formData.industry_sector}
                  >
                    <option value="">Select Industry Subcategory</option>
                    {formData.industry_sector && getSubcategoriesForSector(formData.industry_sector).map((subcategory) => (
                      <option key={subcategory} value={subcategory}>
                        {subcategory}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Address Information */}
                <div className="col-span-2">
                  <h3 className="text-lg font-medium text-gray-900 mb-4 border-b border-gray-200 pb-2">
                    Address Information
                  </h3>
                </div>

                <div className="col-span-2">
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Street Address
                  </label>
                  <input
                    type="text"
                    value={formData.address_street || ''}
                    onChange={(e) => setFormData({ ...formData, address_street: e.target.value })}
                    className="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
                    placeholder="123 Main Street"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    City
                  </label>
                  <input
                    type="text"
                    value={formData.address_city || ''}
                    onChange={(e) => setFormData({ ...formData, address_city: e.target.value })}
                    className="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
                    placeholder="New York"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    State/Province
                  </label>
                  <input
                    type="text"
                    value={formData.address_state || ''}
                    onChange={(e) => setFormData({ ...formData, address_state: e.target.value })}
                    className="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
                    placeholder="NY"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Postal Code
                  </label>
                  <input
                    type="text"
                    value={formData.address_postal_code || ''}
                    onChange={(e) => setFormData({ ...formData, address_postal_code: e.target.value })}
                    className="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
                    placeholder="10001"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Address Country
                  </label>
                  <input
                    type="text"
                    value={formData.address_country || ''}
                    onChange={(e) => setFormData({ ...formData, address_country: e.target.value })}
                    className="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
                    placeholder="United States"
                  />
                </div>

                <div className="flex space-x-4">
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={formData.is_active}
                      onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                      className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                    />
                    <span className="ml-2 text-sm text-gray-700">Active</span>
                  </label>

                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={formData.is_verified}
                      onChange={(e) => setFormData({ ...formData, is_verified: e.target.checked })}
                      className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                    />
                    <span className="ml-2 text-sm text-gray-700">Verified</span>
                  </label>
                </div>
              </div>
            </div>

            <div className="bg-gray-50 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
              <button
                type="submit"
                className="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-primary-600 text-base font-medium text-white hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 sm:ml-3 sm:w-auto sm:text-sm"
              >
                {mode === 'create' ? 'Create Company' : 'Update Company'}
              </button>
              <button
                type="button"
                onClick={onClose}
                className="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 sm:mt-0 sm:ml-3 sm:w-auto sm:text-sm"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
