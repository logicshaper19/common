/**
 * Supplier Addition Form Component
 * Interface for adding suppliers directly to the platform
 */
import React, { useState } from 'react';
import {
  PlusIcon,
  UserPlusIcon,
  EnvelopeIcon,
  BuildingOfficeIcon,
  Cog6ToothIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
} from '@heroicons/react/24/outline';
import { SupplierInvitation } from '../../types/onboarding';
import { onboardingApi } from '../../lib/onboardingApi';
import { Card, CardHeader, CardBody } from '../ui/Card';
import Button from '../ui/Button';
import Input from '../ui/Input';
import Select from '../ui/Select';

import Badge from '../ui/Badge';

import { cn } from '../../lib/utils';

interface SupplierInvitationFormProps {
  onInvitationSent?: (invitation: SupplierInvitation) => void;
  onCancel?: () => void;
  className?: string;
}

const SupplierAddForm: React.FC<SupplierInvitationFormProps> = ({
  onInvitationSent,
  onCancel,
  className,
}) => {
  const [formData, setFormData] = useState({
    supplier_email: '',
    supplier_name: '',
    company_type: 'originator' as const,
    sector_id: 'palm_oil' as const,
    relationship_type: 'supplier' as const,
    invitation_message: '',
  });

  // Backend-compatible data sharing permissions
  const [permissions, setPermissions] = useState({
    operational_data: true,
    commercial_data: false,
    traceability_data: true,
    quality_data: true,
    location_data: false,
  });

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [currentStep, setCurrentStep] = useState<'basic' | 'permissions' | 'review'>('basic');

  // Handle form field changes
  const handleFieldChange = (field: string, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: '' }));
    }
  };

  // Handle permission changes
  const handlePermissionChange = (permission: string, value: boolean) => {
    setPermissions(prev => ({ ...prev, [permission]: value }));
  };

  // Validate form
  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!formData.supplier_email) {
      newErrors.supplier_email = 'Email is required';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.supplier_email)) {
      newErrors.supplier_email = 'Invalid email format';
    }

    if (!formData.supplier_name) {
      newErrors.supplier_name = 'Company name is required';
    }

    if (!formData.company_type) {
      newErrors.company_type = 'Company type is required';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  // Handle form submission
  const handleSubmit = async () => {
    if (!validateForm()) return;

    setIsSubmitting(true);
    try {
      const invitation = await onboardingApi.sendSupplierInvitation({
        supplier_email: formData.supplier_email,
        supplier_name: formData.supplier_name,
        company_type: formData.company_type,
        sector_id: formData.sector_id,
        relationship_type: formData.relationship_type,
        data_sharing_permissions: permissions,
        invitation_message: formData.invitation_message || undefined
      });

      if (onInvitationSent) {
        onInvitationSent(invitation);
      }
    } catch (error) {
      console.error('Failed to add supplier:', error);
      setErrors({ submit: 'Failed to add supplier. Please try again.' });
    } finally {
      setIsSubmitting(false);
    }
  };

  // Get step indicator
  const getStepIndicator = () => {
    const steps = ['basic', 'permissions', 'review'];
    const stepLabels = ['Basic Info', 'Permissions', 'Review'];
    const currentIndex = steps.indexOf(currentStep);

    return (
      <div className="mb-6">
        <div className="flex items-center justify-between mb-2">
          {steps.map((step, index) => (
            <div key={step} className="flex items-center flex-1">
              <div className="flex items-center">
                <div className={cn(
                  'w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium',
                  index <= currentIndex
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-200 text-gray-600'
                )}>
                  {index < currentIndex ? (
                    <CheckCircleIcon className="h-5 w-5" />
                  ) : (
                    index + 1
                  )}
                </div>
                <span className={cn(
                  'ml-2 text-sm font-medium',
                  index <= currentIndex ? 'text-blue-600' : 'text-gray-500'
                )}>
                  {stepLabels[index]}
                </span>
              </div>
              {index < steps.length - 1 && (
                <div className={cn(
                  'flex-1 h-0.5 mx-4',
                  index < currentIndex ? 'bg-blue-600' : 'bg-gray-200'
                )} />
              )}
            </div>
          ))}
        </div>
      </div>
    );
  };

  // Render basic information step
  const renderBasicStep = () => (
    <div className="space-y-6">
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h4 className="font-medium text-blue-900 mb-2">Supplier Information</h4>
        <p className="text-sm text-blue-800">
          Add a new supplier to your network. They will be able to access shared data based on the permissions you set.
        </p>
      </div>

      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
        <h4 className="font-medium text-yellow-900 mb-2">📋 Requirements Process</h4>
        <p className="text-sm text-yellow-800">
          After adding the supplier, they will receive access to their supplier dashboard where they can upload
          tier-specific requirements based on their company type and sector.
        </p>
      </div>

      <div className="space-y-4">
        <div>
        <div>
          <label className="block text-sm font-medium text-neutral-700 mb-1">
            Supplier Contact Email *
          </label>
          <div className="relative">
            <Input
              type="email"
              value={formData.supplier_email}
              onChange={(e) => handleFieldChange('supplier_email', e.target.value)}
              placeholder="contact@supplier-company.com"
              required
              className={`pl-10 ${errors.supplier_email ? 'border-red-500' : ''}`}
            />
            <EnvelopeIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-neutral-400" />
          </div>
          {errors.supplier_email && (
            <p className="mt-1 text-sm text-red-600">{errors.supplier_email}</p>
          )}
          <p className="mt-1 text-xs text-neutral-600">
            Primary contact email for this supplier company
          </p>
        </div>
      </div>

      <div>
        <div>
          <label className="block text-sm font-medium text-neutral-700 mb-1">
            Company Name *
          </label>
          <div className="relative">
            <Input
              value={formData.supplier_name}
              onChange={(e) => handleFieldChange('supplier_name', e.target.value)}
              placeholder="Supplier Company Name"
              required
              className={`pl-10 ${errors.supplier_name ? 'border-red-500' : ''}`}
            />
            <BuildingOfficeIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-neutral-400" />
          </div>
          {errors.supplier_name && (
            <p className="mt-1 text-sm text-red-600">{errors.supplier_name}</p>
          )}
        </div>
      </div>

      <div>
        <div>
          <label className="block text-sm font-medium text-neutral-700 mb-1">
            Company Type *
          </label>
          <div className="relative">
            <Select
              value={formData.company_type}
              onChange={(e) => handleFieldChange('company_type', e.target.value)}
              required
              className={`pl-10 ${errors.company_type ? 'border-red-500' : ''}`}
              options={[
                { value: 'originator', label: 'Originator (Raw Materials)' },
                { value: 'processor', label: 'Processor (Manufacturing)' },
                { value: 'brand', label: 'Brand (Retail)' },
                { value: 'trader', label: 'Trader (Commodity Trading)' }
              ]}
            />
            <Cog6ToothIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-neutral-400" />
          </div>
          {errors.company_type && (
            <p className="mt-1 text-sm text-red-600">{errors.company_type}</p>
          )}
        </div>
      </div>

      <div>
        <div>
          <label className="block text-sm font-medium text-neutral-700 mb-1">
            Industry Sector *
          </label>
          <div className="relative">
            <Select
              value={formData.sector_id}
              onChange={(e) => handleFieldChange('sector_id', e.target.value)}
              className="pl-10"
              options={[
                { value: 'palm_oil', label: 'Palm Oil' },
                { value: 'apparel', label: 'Apparel & Textiles' },
                { value: 'electronics', label: 'Electronics' }
              ]}
            >
              <option value="palm_oil">Palm Oil</option>
              <option value="apparel">Apparel & Textiles</option>
              <option value="electronics">Electronics</option>
            </Select>
            <BuildingOfficeIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-neutral-400" />
          </div>
        </div>
      </div>

      <div>
        <div>
          <label className="block text-sm font-medium text-neutral-700 mb-1">
            Relationship Type
          </label>
          <div className="relative">
            <Select
              value={formData.relationship_type}
              onChange={(e) => handleFieldChange('relationship_type', e.target.value)}
              className="pl-10"
              options={[
                { value: 'supplier', label: 'Supplier' },
                { value: 'customer', label: 'Customer' },
                { value: 'partner', label: 'Partner' }
              ]}
            >
              <option value="supplier">Supplier</option>
              <option value="customer">Customer</option>
              <option value="partner">Partner</option>
            </Select>
            <UserPlusIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-neutral-400" />
          </div>
        </div>
      </div>
      </div>
    </div>
  );



  // Render permissions step
  const renderPermissionsStep = () => {
    const permissionGroups = [
      {
        title: 'Data Sharing Permissions',
        permissions: [
          { key: 'operational_data', label: 'Operational Data', description: 'Access to quantities, dates, and status information' },
          { key: 'commercial_data', label: 'Commercial Data', description: 'Access to prices, margins, and commercial terms' },
          { key: 'traceability_data', label: 'Traceability Data', description: 'Access to input materials and origin data' },
          { key: 'quality_data', label: 'Quality Data', description: 'Access to quality metrics and certifications' },
          { key: 'location_data', label: 'Location Data', description: 'Access to geographic coordinates and facility information' },
        ],
      },
    ];

    return (
      <div className="space-y-6">
        <div className="text-sm text-neutral-600">
          Configure what data and features this supplier will have access to once they're onboarded.
        </div>

        {permissionGroups.map((group) => (
          <div key={group.title}>
            <h4 className="font-medium text-neutral-900 mb-3">{group.title}</h4>
            <div className="space-y-3">
              {group.permissions.map((perm) => (
                <div key={perm.key} className="flex items-start space-x-3">
                  <input
                    type="checkbox"
                    id={perm.key}
                    checked={permissions[perm.key as keyof typeof permissions]}
                    onChange={(e) => handlePermissionChange(perm.key, e.target.checked)}
                    className="mt-1 h-4 w-4 text-primary-600 focus:ring-primary-500 border-neutral-300 rounded"
                  />
                  <div className="flex-1">
                    <label htmlFor={perm.key} className="text-sm font-medium text-neutral-900 cursor-pointer">
                      {perm.label}
                    </label>
                    <p className="text-xs text-neutral-600">{perm.description}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    );
  };



  // Render review step
  const renderReviewStep = () => (
    <div className="space-y-6">
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
        <h4 className="font-medium text-blue-900 mb-2">Ready to Add Supplier</h4>
        <p className="text-sm text-blue-800">
          This will create a supplier record in your system with the specified permissions.
          The supplier will need to be onboarded separately through your internal processes.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <h4 className="font-medium text-neutral-900 mb-2">Supplier Information</h4>
          <div className="space-y-2 text-sm">
            <div><strong>Contact Email:</strong> {formData.supplier_email}</div>
            <div><strong>Company Name:</strong> {formData.supplier_name}</div>
            <div><strong>Company Type:</strong> {formData.company_type}</div>
            <div><strong>Relationship:</strong> {formData.relationship_type}</div>
          </div>
        </div>

        <div>
          <h4 className="font-medium text-neutral-900 mb-2">Data Sharing Permissions</h4>
          <div className="space-y-1">
            {Object.entries(permissions).filter(([_, value]) => value).map(([key, _]) => (
              <Badge key={key} variant="success" size="sm">
                {key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
              </Badge>
            ))}
          </div>
        </div>
      </div>

      {errors.submit && (
        <div className="flex items-center space-x-2 text-error-600 text-sm">
          <ExclamationTriangleIcon className="h-5 w-5" />
          <span>{errors.submit}</span>
        </div>
      )}
    </div>
  );

  return (
    <Card className={className}>
      <CardHeader
        title="Add Supplier"
        subtitle="Add a new supplier to your supply chain network"
      />

      <CardBody>
        {getStepIndicator()}

        <div className="mb-6">
          {currentStep === 'basic' && renderBasicStep()}
          {currentStep === 'permissions' && renderPermissionsStep()}
          {currentStep === 'review' && renderReviewStep()}
        </div>

        {/* Navigation buttons */}
        <div className="flex justify-between">
          <div>
            {currentStep !== 'basic' && (
              <Button
                variant="outline"
                onClick={() => {
                  const steps = ['basic', 'permissions', 'review'];
                  const currentIndex = steps.indexOf(currentStep);
                  setCurrentStep(steps[currentIndex - 1] as any);
                }}
              >
                Back
              </Button>
            )}
          </div>

          <div className="flex space-x-3">
            {onCancel && (
              <Button variant="outline" onClick={onCancel}>
                Cancel
              </Button>
            )}

            {currentStep === 'review' ? (
              <Button
                variant="primary"
                onClick={handleSubmit}
                disabled={isSubmitting}
                leftIcon={<PlusIcon className="h-4 w-4" />}
              >
                {isSubmitting ? 'Adding...' : 'Add Supplier'}
              </Button>
            ) : (
              <Button
                variant="primary"
                onClick={() => {
                  if (currentStep === 'basic' && !validateForm()) return;

                  const steps = ['basic', 'permissions', 'review'];
                  const currentIndex = steps.indexOf(currentStep);
                  setCurrentStep(steps[currentIndex + 1] as any);
                }}
              >
                Next
              </Button>
            )}
          </div>
        </div>
      </CardBody>
    </Card>
  );
};

export default SupplierAddForm;
