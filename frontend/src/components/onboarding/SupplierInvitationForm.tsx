/**
 * Supplier Invitation Form Component
 * Interface for inviting suppliers with email integration
 */
import React, { useState } from 'react';
import { 
  PaperAirplaneIcon,
  UserPlusIcon,
  EnvelopeIcon,
  BuildingOfficeIcon,
  Cog6ToothIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
} from '@heroicons/react/24/outline';
import { SupplierInvitation, DataSharingPermissions } from '../../types/onboarding';
import { onboardingApi } from '../../lib/onboardingApi';
import { Card, CardHeader, CardBody } from '../ui/Card';
import Button from '../ui/Button';
import Input from '../ui/Input';
import Select from '../ui/Select';
import Textarea from '../ui/Textarea';
import Badge from '../ui/Badge';
import { cn } from '../../lib/utils';

interface SupplierInvitationFormProps {
  onInvitationSent?: (invitation: SupplierInvitation) => void;
  onCancel?: () => void;
  className?: string;
}

const SupplierInvitationForm: React.FC<SupplierInvitationFormProps> = ({
  onInvitationSent,
  onCancel,
  className,
}) => {
  const [formData, setFormData] = useState({
    supplier_email: '',
    supplier_name: '',
    company_type: 'originator' as const,
    relationship_type: 'supplier' as const,
    invitation_message: '',
  });

  const [permissions, setPermissions] = useState<DataSharingPermissions>({
    view_purchase_orders: true,
    view_product_details: true,
    view_pricing: false,
    view_delivery_schedules: true,
    view_quality_metrics: true,
    view_sustainability_data: true,
    view_transparency_scores: true,
    edit_order_confirmations: true,
    edit_delivery_updates: true,
    edit_quality_reports: true,
    receive_notifications: true,
    access_analytics: false,
  });

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [currentStep, setCurrentStep] = useState<'basic' | 'permissions' | 'message' | 'review'>('basic');

  // Handle form field changes
  const handleFieldChange = (field: string, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: '' }));
    }
  };

  // Handle permission changes
  const handlePermissionChange = (permission: keyof DataSharingPermissions, value: boolean) => {
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
        ...formData,
        data_sharing_permissions: permissions,
      });

      if (onInvitationSent) {
        onInvitationSent(invitation);
      }
    } catch (error) {
      console.error('Failed to send invitation:', error);
      setErrors({ submit: 'Failed to send invitation. Please try again.' });
    } finally {
      setIsSubmitting(false);
    }
  };

  // Get step indicator
  const getStepIndicator = () => {
    const steps = ['basic', 'permissions', 'message', 'review'];
    const currentIndex = steps.indexOf(currentStep);

    return (
      <div className="flex items-center space-x-2 mb-6">
        {steps.map((step, index) => (
          <div key={step} className="flex items-center">
            <div className={cn(
              'w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium',
              index <= currentIndex
                ? 'bg-primary-600 text-white'
                : 'bg-neutral-200 text-neutral-600'
            )}>
              {index < currentIndex ? (
                <CheckCircleIcon className="h-5 w-5" />
              ) : (
                index + 1
              )}
            </div>
            {index < steps.length - 1 && (
              <div className={cn(
                'w-8 h-0.5 mx-2',
                index < currentIndex ? 'bg-primary-600' : 'bg-neutral-200'
              )} />
            )}
          </div>
        ))}
      </div>
    );
  };

  // Render basic information step
  const renderBasicStep = () => (
    <div className="space-y-4">
      <div>
        <Input
          label="Supplier Email"
          type="email"
          value={formData.supplier_email}
          onChange={(e) => handleFieldChange('supplier_email', e.target.value)}
          error={errors.supplier_email}
          placeholder="supplier@example.com"
          required
          icon={EnvelopeIcon}
        />
      </div>

      <div>
        <Input
          label="Company Name"
          value={formData.supplier_name}
          onChange={(e) => handleFieldChange('supplier_name', e.target.value)}
          error={errors.supplier_name}
          placeholder="Supplier Company Name"
          required
          icon={BuildingOfficeIcon}
        />
      </div>

      <div>
        <Select
          label="Company Type"
          value={formData.company_type}
          onChange={(e) => handleFieldChange('company_type', e.target.value)}
          error={errors.company_type}
          required
          icon={Cog6ToothIcon}
        >
          <option value="originator">Originator (Raw Materials)</option>
          <option value="processor">Processor (Manufacturing)</option>
          <option value="brand">Brand (Retail)</option>
        </Select>
      </div>

      <div>
        <Select
          label="Relationship Type"
          value={formData.relationship_type}
          onChange={(e) => handleFieldChange('relationship_type', e.target.value)}
          icon={UserPlusIcon}
        >
          <option value="supplier">Supplier</option>
          <option value="customer">Customer</option>
          <option value="partner">Partner</option>
        </Select>
      </div>
    </div>
  );

  // Render permissions step
  const renderPermissionsStep = () => {
    const permissionGroups = [
      {
        title: 'View Permissions',
        permissions: [
          { key: 'view_purchase_orders', label: 'Purchase Orders', description: 'View order details and status' },
          { key: 'view_product_details', label: 'Product Details', description: 'View product specifications' },
          { key: 'view_pricing', label: 'Pricing Information', description: 'View pricing and costs' },
          { key: 'view_delivery_schedules', label: 'Delivery Schedules', description: 'View delivery timelines' },
          { key: 'view_quality_metrics', label: 'Quality Metrics', description: 'View quality assessments' },
          { key: 'view_sustainability_data', label: 'Sustainability Data', description: 'View environmental metrics' },
          { key: 'view_transparency_scores', label: 'Transparency Scores', description: 'View transparency ratings' },
        ],
      },
      {
        title: 'Edit Permissions',
        permissions: [
          { key: 'edit_order_confirmations', label: 'Order Confirmations', description: 'Confirm and update orders' },
          { key: 'edit_delivery_updates', label: 'Delivery Updates', description: 'Update delivery status' },
          { key: 'edit_quality_reports', label: 'Quality Reports', description: 'Submit quality reports' },
        ],
      },
      {
        title: 'System Access',
        permissions: [
          { key: 'receive_notifications', label: 'Notifications', description: 'Receive system notifications' },
          { key: 'access_analytics', label: 'Analytics', description: 'Access analytics dashboard' },
        ],
      },
    ];

    return (
      <div className="space-y-6">
        <div className="text-sm text-neutral-600">
          Configure what data and features this supplier will have access to.
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
                    checked={permissions[perm.key as keyof DataSharingPermissions]}
                    onChange={(e) => handlePermissionChange(perm.key as keyof DataSharingPermissions, e.target.checked)}
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

  // Render message step
  const renderMessageStep = () => (
    <div className="space-y-4">
      <div>
        <Textarea
          label="Invitation Message (Optional)"
          value={formData.invitation_message}
          onChange={(e) => handleFieldChange('invitation_message', e.target.value)}
          placeholder="Add a personal message to your invitation..."
          rows={4}
        />
      </div>

      <div className="bg-primary-50 border border-primary-200 rounded-lg p-4">
        <h4 className="font-medium text-primary-900 mb-2">Email Preview</h4>
        <div className="text-sm text-primary-800">
          <p className="mb-2">
            <strong>Subject:</strong> Invitation to join Common Supply Chain Platform
          </p>
          <div className="bg-white border border-primary-200 rounded p-3">
            <p className="mb-2">Hello {formData.supplier_name},</p>
            <p className="mb-2">
              You've been invited to join the Common Supply Chain Platform to enhance transparency 
              and collaboration in our supply chain.
            </p>
            {formData.invitation_message && (
              <div className="mb-2 p-2 bg-neutral-50 rounded border-l-4 border-primary-500">
                <p className="italic">"{formData.invitation_message}"</p>
              </div>
            )}
            <p className="mb-2">
              Click the link below to accept the invitation and complete your registration.
            </p>
            <Button variant="primary" size="sm" disabled>
              Accept Invitation
            </Button>
          </div>
        </div>
      </div>
    </div>
  );

  // Render review step
  const renderReviewStep = () => (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <h4 className="font-medium text-neutral-900 mb-2">Supplier Information</h4>
          <div className="space-y-2 text-sm">
            <div><strong>Email:</strong> {formData.supplier_email}</div>
            <div><strong>Company:</strong> {formData.supplier_name}</div>
            <div><strong>Type:</strong> {formData.company_type}</div>
            <div><strong>Relationship:</strong> {formData.relationship_type}</div>
          </div>
        </div>

        <div>
          <h4 className="font-medium text-neutral-900 mb-2">Data Sharing Summary</h4>
          <div className="space-y-1">
            {Object.entries(permissions).filter(([_, value]) => value).map(([key, _]) => (
              <Badge key={key} variant="success" size="sm">
                {key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
              </Badge>
            ))}
          </div>
        </div>
      </div>

      {formData.invitation_message && (
        <div>
          <h4 className="font-medium text-neutral-900 mb-2">Custom Message</h4>
          <div className="bg-neutral-50 border border-neutral-200 rounded p-3 text-sm">
            {formData.invitation_message}
          </div>
        </div>
      )}

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
        title="Invite Supplier"
        subtitle="Send an invitation to join your supply chain network"
        icon={PaperAirplaneIcon}
      />
      
      <CardBody>
        {getStepIndicator()}

        <div className="mb-6">
          {currentStep === 'basic' && renderBasicStep()}
          {currentStep === 'permissions' && renderPermissionsStep()}
          {currentStep === 'message' && renderMessageStep()}
          {currentStep === 'review' && renderReviewStep()}
        </div>

        {/* Navigation buttons */}
        <div className="flex justify-between">
          <div>
            {currentStep !== 'basic' && (
              <Button
                variant="outline"
                onClick={() => {
                  const steps = ['basic', 'permissions', 'message', 'review'];
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
                icon={PaperAirplaneIcon}
              >
                {isSubmitting ? 'Sending...' : 'Send Invitation'}
              </Button>
            ) : (
              <Button
                variant="primary"
                onClick={() => {
                  if (currentStep === 'basic' && !validateForm()) return;
                  
                  const steps = ['basic', 'permissions', 'message', 'review'];
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

export default SupplierInvitationForm;
