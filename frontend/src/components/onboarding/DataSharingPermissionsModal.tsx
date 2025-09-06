/**
 * Data Sharing Permissions Modal Component
 * Configure data sharing permissions for business relationships
 */
import React, { useState } from 'react';
import { 
  ShieldCheckIcon,
  EyeIcon,
  PencilIcon,
  BellIcon,
  ChartBarIcon,
  XMarkIcon,
} from '@heroicons/react/24/outline';
import { BusinessRelationship, DataSharingPermissions } from '../../types/onboarding';
import { Card, CardHeader, CardBody } from '../ui/Card';
import Button from '../ui/Button';
import Badge from '../ui/Badge';
import { cn } from '../../lib/utils';

interface DataSharingPermissionsModalProps {
  relationship: BusinessRelationship;
  onSave: (permissions: DataSharingPermissions) => void;
  onCancel: () => void;
}

const DataSharingPermissionsModal: React.FC<DataSharingPermissionsModalProps> = ({
  relationship,
  onSave,
  onCancel,
}) => {
  const [permissions, setPermissions] = useState<DataSharingPermissions>(
    relationship.data_sharing_permissions
  );
  const [hasChanges, setHasChanges] = useState(false);

  // Permission categories with descriptions
  const permissionCategories = [
    {
      id: 'view',
      title: 'View Permissions',
      description: 'What data this partner can view',
      icon: EyeIcon,
      permissions: [
        {
          key: 'view_purchase_orders',
          label: 'Purchase Orders',
          description: 'View order details, quantities, and delivery schedules',
          impact: 'high',
        },
        {
          key: 'view_product_details',
          label: 'Product Details',
          description: 'View product specifications, materials, and requirements',
          impact: 'medium',
        },
        {
          key: 'view_pricing',
          label: 'Pricing Information',
          description: 'View pricing, costs, and financial terms',
          impact: 'high',
        },
        {
          key: 'view_delivery_schedules',
          label: 'Delivery Schedules',
          description: 'View delivery timelines and logistics information',
          impact: 'medium',
        },
        {
          key: 'view_quality_metrics',
          label: 'Quality Metrics',
          description: 'View quality standards, test results, and assessments',
          impact: 'medium',
        },
        {
          key: 'view_sustainability_data',
          label: 'Sustainability Data',
          description: 'View environmental impact and sustainability metrics',
          impact: 'low',
        },
        {
          key: 'view_transparency_scores',
          label: 'Transparency Scores',
          description: 'View supply chain transparency ratings and analytics',
          impact: 'low',
        },
      ],
    },
    {
      id: 'edit',
      title: 'Edit Permissions',
      description: 'What data this partner can modify',
      icon: PencilIcon,
      permissions: [
        {
          key: 'edit_order_confirmations',
          label: 'Order Confirmations',
          description: 'Confirm orders, update quantities, and modify delivery dates',
          impact: 'high',
        },
        {
          key: 'edit_delivery_updates',
          label: 'Delivery Updates',
          description: 'Update delivery status, tracking, and logistics information',
          impact: 'medium',
        },
        {
          key: 'edit_quality_reports',
          label: 'Quality Reports',
          description: 'Submit quality reports, test results, and certifications',
          impact: 'medium',
        },
      ],
    },
    {
      id: 'system',
      title: 'System Access',
      description: 'System features and notifications',
      icon: BellIcon,
      permissions: [
        {
          key: 'receive_notifications',
          label: 'Notifications',
          description: 'Receive email and system notifications about orders and updates',
          impact: 'low',
        },
        {
          key: 'access_analytics',
          label: 'Analytics Dashboard',
          description: 'Access analytics, reports, and business intelligence features',
          impact: 'medium',
        },
      ],
    },
  ];

  // Handle permission change
  const handlePermissionChange = (key: keyof DataSharingPermissions, value: boolean) => {
    setPermissions(prev => ({ ...prev, [key]: value }));
    setHasChanges(true);
  };

  // Get permission impact color
  const getImpactColor = (impact: string) => {
    switch (impact) {
      case 'high': return 'text-error-600';
      case 'medium': return 'text-warning-600';
      case 'low': return 'text-success-600';
      default: return 'text-neutral-600';
    }
  };

  // Get permission impact badge
  const getImpactBadge = (impact: string) => {
    switch (impact) {
      case 'high': return { variant: 'error' as const, label: 'High Impact' };
      case 'medium': return { variant: 'warning' as const, label: 'Medium Impact' };
      case 'low': return { variant: 'success' as const, label: 'Low Impact' };
      default: return { variant: 'neutral' as const, label: 'Unknown' };
    }
  };

  // Handle save
  const handleSave = () => {
    onSave(permissions);
  };

  // Calculate permission summary
  const enabledPermissions = Object.values(permissions).filter(Boolean).length;
  const totalPermissions = Object.keys(permissions).length;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-hidden">
        <Card>
          <CardHeader
            title="Data Sharing Permissions"
            subtitle={`Configure access for ${relationship.seller_company_name}`}
            action={
              <div className="flex items-center space-x-2">
                <ShieldCheckIcon className="h-5 w-5 text-neutral-400" />
                <Button
                  variant="outline"
                  size="sm"
                  onClick={onCancel}
                  leftIcon={<XMarkIcon className="h-4 w-4" />}
                >
                  Close
                </Button>
              </div>
            }
          />
          
          <CardBody className="max-h-[60vh] overflow-y-auto">
            {/* Permission Summary */}
            <div className="mb-6 p-4 bg-neutral-50 rounded-lg">
              <div className="flex items-center justify-between mb-2">
                <h3 className="font-medium text-neutral-900">Permission Summary</h3>
                <Badge variant="primary">
                  {enabledPermissions} of {totalPermissions} enabled
                </Badge>
              </div>
              <div className="w-full bg-neutral-200 rounded-full h-2">
                <div 
                  className="bg-primary-600 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${(enabledPermissions / totalPermissions) * 100}%` }}
                />
              </div>
              <p className="text-sm text-neutral-600 mt-2">
                This partner will have access to {enabledPermissions} out of {totalPermissions} available data types.
              </p>
            </div>

            {/* Permission Categories */}
            <div className="space-y-6">
              {permissionCategories.map((category) => {
                const CategoryIcon = category.icon;
                const categoryPermissions = category.permissions.filter(perm => 
                  permissions[perm.key as keyof DataSharingPermissions]
                ).length;

                return (
                  <div key={category.id} className="border border-neutral-200 rounded-lg">
                    <div className="p-4 border-b border-neutral-200 bg-neutral-50">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-3">
                          <CategoryIcon className="h-5 w-5 text-neutral-600" />
                          <div>
                            <h4 className="font-medium text-neutral-900">{category.title}</h4>
                            <p className="text-sm text-neutral-600">{category.description}</p>
                          </div>
                        </div>
                        <Badge variant="neutral" size="sm">
                          {categoryPermissions} of {category.permissions.length}
                        </Badge>
                      </div>
                    </div>

                    <div className="p-4 space-y-4">
                      {category.permissions.map((perm) => {
                        const isEnabled = permissions[perm.key as keyof DataSharingPermissions];
                        const impactBadge = getImpactBadge(perm.impact);

                        return (
                          <div key={perm.key} className="flex items-start space-x-3">
                            <input
                              type="checkbox"
                              id={perm.key}
                              checked={isEnabled}
                              onChange={(e) => handlePermissionChange(
                                perm.key as keyof DataSharingPermissions, 
                                e.target.checked
                              )}
                              className="mt-1 h-4 w-4 text-primary-600 focus:ring-primary-500 border-neutral-300 rounded"
                            />
                            <div className="flex-1">
                              <div className="flex items-center space-x-2 mb-1">
                                <label 
                                  htmlFor={perm.key} 
                                  className="text-sm font-medium text-neutral-900 cursor-pointer"
                                >
                                  {perm.label}
                                </label>
                                <Badge variant={impactBadge.variant} size="sm">
                                  {impactBadge.label}
                                </Badge>
                              </div>
                              <p className="text-xs text-neutral-600">{perm.description}</p>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Security Notice */}
            <div className="mt-6 p-4 bg-warning-50 border border-warning-200 rounded-lg">
              <div className="flex items-start space-x-2">
                <ShieldCheckIcon className="h-5 w-5 text-warning-600 mt-0.5 flex-shrink-0" />
                <div>
                  <h4 className="font-medium text-warning-900 mb-1">Security Notice</h4>
                  <p className="text-sm text-warning-800">
                    These permissions control what data this partner can access in your system. 
                    High impact permissions should be granted carefully as they provide access to 
                    sensitive business information. You can modify these permissions at any time.
                  </p>
                </div>
              </div>
            </div>
          </CardBody>

          {/* Footer */}
          <div className="border-t border-neutral-200 p-4">
            <div className="flex justify-between items-center">
              <div className="text-sm text-neutral-600">
                {hasChanges ? 'You have unsaved changes' : 'No changes made'}
              </div>
              
              <div className="flex space-x-3">
                <Button variant="outline" onClick={onCancel}>
                  Cancel
                </Button>
                <Button 
                  variant="primary" 
                  onClick={handleSave}
                  disabled={!hasChanges}
                >
                  Save Permissions
                </Button>
              </div>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
};

export default DataSharingPermissionsModal;
