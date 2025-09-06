/**
 * Company Settings Component
 * Company-wide settings and configuration management
 */
import React, { useState, useEffect } from 'react';
import { 
  BuildingOfficeIcon,
  GlobeAltIcon,
  CurrencyDollarIcon,
  ClockIcon,
  PaintBrushIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  CogIcon,
} from '@heroicons/react/24/outline';
import { useAuth } from '../../contexts/AuthContext';
import { notificationApi } from '../../lib/notificationApi';
import { Card, CardHeader, CardBody } from '../ui/Card';
import Button from '../ui/Button';
import Input from '../ui/Input';
import Select from '../ui/Select';
import Textarea from '../ui/Textarea';
import Badge from '../ui/Badge';
import { CompanySettings as CompanySettingsType } from '../../types/notifications';
import { cn } from '../../lib/utils';

interface CompanySettingsProps {
  className?: string;
}

const CompanySettings: React.FC<CompanySettingsProps> = ({
  className,
}) => {
  const { user } = useAuth();
  const [settings, setSettings] = useState<CompanySettingsType | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [hasChanges, setHasChanges] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [activeSection, setActiveSection] = useState<'basic' | 'business' | 'platform' | 'features'>('basic');

  // Load company settings on mount
  useEffect(() => {
    if (user?.company_id) {
      loadSettings();
    }
  }, [user?.company_id]);

  const loadSettings = async () => {
    if (!user?.company_id) return;

    setIsLoading(true);
    try {
      const data = await notificationApi.getCompanySettings(user.company_id);
      setSettings(data);
    } catch (error) {
      console.error('Failed to load company settings:', error);
      setError('Failed to load company settings');
    } finally {
      setIsLoading(false);
    }
  };

  // Handle settings field changes
  const updateSetting = (field: string, value: any) => {
    if (!settings) return;

    // Handle nested fields
    if (field.includes('.')) {
      const [parent, child] = field.split('.');
      setSettings(prev => ({
        ...prev!,
        [parent]: {
          ...prev![parent as keyof CompanySettingsType],
          [child]: value,
        },
      }));
    } else {
      setSettings(prev => ({ ...prev!, [field]: value }));
    }
    
    setHasChanges(true);
  };

  // Save settings changes
  const saveSettings = async () => {
    if (!settings || !hasChanges) return;

    setIsSaving(true);
    setError(null);
    try {
      // In a real implementation, this would call the API
      console.log('Saving company settings:', settings);
      
      setHasChanges(false);
      setSuccessMessage('Company settings updated successfully');
      setTimeout(() => setSuccessMessage(null), 3000);
    } catch (error) {
      console.error('Failed to save company settings:', error);
      setError('Failed to save company settings');
    } finally {
      setIsSaving(false);
    }
  };

  // Reset changes
  const resetChanges = () => {
    loadSettings();
    setHasChanges(false);
  };

  if (isLoading) {
    return (
      <Card className={className}>
        <CardBody>
          <div className="text-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600 mx-auto"></div>
            <p className="mt-2 text-neutral-600">Loading company settings...</p>
          </div>
        </CardBody>
      </Card>
    );
  }

  if (!settings) {
    return (
      <Card className={className}>
        <CardBody>
          <div className="text-center py-8">
            <BuildingOfficeIcon className="h-12 w-12 text-neutral-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-neutral-900 mb-2">Unable to Load Settings</h3>
            <p className="text-neutral-600 mb-4">There was an error loading your company settings.</p>
            <Button variant="primary" onClick={loadSettings}>
              Try Again
            </Button>
          </div>
        </CardBody>
      </Card>
    );
  }

  const sections = [
    { id: 'basic', label: 'Basic Information', icon: BuildingOfficeIcon },
    { id: 'business', label: 'Business Details', icon: GlobeAltIcon },
    { id: 'platform', label: 'Platform Settings', icon: CogIcon },
    { id: 'features', label: 'Features & Permissions', icon: CheckCircleIcon },
  ];

  return (
    <div className={className}>
      <Card>
        <CardHeader 
          title="Company Settings"
          subtitle="Manage your company information and platform configuration"
          icon={BuildingOfficeIcon}
        />
        
        <CardBody>
          {/* Error/Success Messages */}
          {error && (
            <div className="mb-4 p-3 bg-error-50 border border-error-200 rounded-lg text-error-800 flex items-center">
              <ExclamationTriangleIcon className="h-5 w-5 mr-2" />
              {error}
            </div>
          )}
          
          {successMessage && (
            <div className="mb-4 p-3 bg-success-50 border border-success-200 rounded-lg text-success-800 flex items-center">
              <CheckCircleIcon className="h-5 w-5 mr-2" />
              {successMessage}
            </div>
          )}

          {/* Section Navigation */}
          <div className="border-b border-neutral-200 mb-6">
            <nav className="-mb-px flex space-x-8">
              {sections.map((section) => {
                const Icon = section.icon;
                const isActive = activeSection === section.id;
                
                return (
                  <button
                    key={section.id}
                    onClick={() => setActiveSection(section.id as any)}
                    className={cn(
                      'flex items-center space-x-2 py-2 px-1 border-b-2 font-medium text-sm transition-colors',
                      isActive
                        ? 'border-primary-500 text-primary-600'
                        : 'border-transparent text-neutral-500 hover:text-neutral-700 hover:border-neutral-300'
                    )}
                  >
                    <Icon className="h-5 w-5" />
                    <span>{section.label}</span>
                  </button>
                );
              })}
            </nav>
          </div>

          {/* Section Content */}
          {activeSection === 'basic' && (
            <div className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <Input
                  label="Company Name"
                  value={settings.company_name}
                  onChange={(e) => updateSetting('company_name', e.target.value)}
                  required
                />
                
                <Input
                  label="Website"
                  type="url"
                  value={settings.website || ''}
                  onChange={(e) => updateSetting('website', e.target.value)}
                  placeholder="https://example.com"
                />
                
                <Input
                  label="Phone"
                  type="tel"
                  value={settings.phone || ''}
                  onChange={(e) => updateSetting('phone', e.target.value)}
                  placeholder="+1 (555) 123-4567"
                />
                
                <Select
                  label="Company Size"
                  value={settings.company_size}
                  onChange={(e) => updateSetting('company_size', e.target.value)}
                >
                  <option value="startup">Startup (1-10 employees)</option>
                  <option value="small">Small (11-50 employees)</option>
                  <option value="medium">Medium (51-200 employees)</option>
                  <option value="large">Large (201-1000 employees)</option>
                  <option value="enterprise">Enterprise (1000+ employees)</option>
                </Select>
              </div>
              
              <Textarea
                label="Description"
                value={settings.description || ''}
                onChange={(e) => updateSetting('description', e.target.value)}
                placeholder="Brief description of your company..."
                rows={3}
              />

              {/* Address */}
              <div>
                <h4 className="font-medium text-neutral-900 mb-3">Address</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="md:col-span-2">
                    <Input
                      label="Street Address"
                      value={settings.address.street}
                      onChange={(e) => updateSetting('address.street', e.target.value)}
                    />
                  </div>
                  
                  <Input
                    label="City"
                    value={settings.address.city}
                    onChange={(e) => updateSetting('address.city', e.target.value)}
                  />
                  
                  <Input
                    label="State/Province"
                    value={settings.address.state}
                    onChange={(e) => updateSetting('address.state', e.target.value)}
                  />
                  
                  <Input
                    label="Postal Code"
                    value={settings.address.postal_code}
                    onChange={(e) => updateSetting('address.postal_code', e.target.value)}
                  />
                  
                  <Input
                    label="Country"
                    value={settings.address.country}
                    onChange={(e) => updateSetting('address.country', e.target.value)}
                  />
                </div>
              </div>
            </div>
          )}

          {activeSection === 'business' && (
            <div className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <Input
                  label="Business Registration Number"
                  value={settings.business_registration_number || ''}
                  onChange={(e) => updateSetting('business_registration_number', e.target.value)}
                />
                
                <Input
                  label="Tax ID"
                  value={settings.tax_id || ''}
                  onChange={(e) => updateSetting('tax_id', e.target.value)}
                />
                
                <Input
                  label="Industry Sector"
                  value={settings.industry_sector || ''}
                  onChange={(e) => updateSetting('industry_sector', e.target.value)}
                  placeholder="e.g., Fashion, Food & Beverage"
                />
              </div>
            </div>
          )}

          {activeSection === 'platform' && (
            <div className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <Select
                  label="Default Currency"
                  value={settings.default_currency}
                  onChange={(e) => updateSetting('default_currency', e.target.value)}
                >
                  <option value="USD">USD - US Dollar</option>
                  <option value="EUR">EUR - Euro</option>
                  <option value="GBP">GBP - British Pound</option>
                  <option value="CAD">CAD - Canadian Dollar</option>
                  <option value="AUD">AUD - Australian Dollar</option>
                </Select>
                
                <Select
                  label="Default Timezone"
                  value={settings.default_timezone}
                  onChange={(e) => updateSetting('default_timezone', e.target.value)}
                >
                  <option value="America/New_York">Eastern Time (ET)</option>
                  <option value="America/Chicago">Central Time (CT)</option>
                  <option value="America/Denver">Mountain Time (MT)</option>
                  <option value="America/Los_Angeles">Pacific Time (PT)</option>
                  <option value="UTC">UTC</option>
                </Select>
              </div>

              {/* Branding */}
              <div>
                <h4 className="font-medium text-neutral-900 mb-3">Branding</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <Input
                    label="Logo URL"
                    value={settings.logo_url || ''}
                    onChange={(e) => updateSetting('logo_url', e.target.value)}
                    placeholder="https://example.com/logo.png"
                  />
                  
                  <Input
                    label="Primary Color"
                    type="color"
                    value={settings.primary_color || '#3B82F6'}
                    onChange={(e) => updateSetting('primary_color', e.target.value)}
                  />
                </div>
              </div>

              {/* Notification Settings */}
              <div>
                <h4 className="font-medium text-neutral-900 mb-3">Notification Settings</h4>
                <div className="space-y-3">
                  <div className="flex items-center space-x-3">
                    <input
                      type="checkbox"
                      checked={settings.notification_settings.default_channels.includes('in_app')}
                      onChange={(e) => {
                        const channels = e.target.checked
                          ? [...settings.notification_settings.default_channels, 'in_app']
                          : settings.notification_settings.default_channels.filter(c => c !== 'in_app');
                        updateSetting('notification_settings.default_channels', channels);
                      }}
                      className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-neutral-300 rounded"
                    />
                    <label className="text-sm text-neutral-700">In-app notifications</label>
                  </div>
                  
                  <div className="flex items-center space-x-3">
                    <input
                      type="checkbox"
                      checked={settings.notification_settings.default_channels.includes('email')}
                      onChange={(e) => {
                        const channels = e.target.checked
                          ? [...settings.notification_settings.default_channels, 'email']
                          : settings.notification_settings.default_channels.filter(c => c !== 'email');
                        updateSetting('notification_settings.default_channels', channels);
                      }}
                      className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-neutral-300 rounded"
                    />
                    <label className="text-sm text-neutral-700">Email notifications</label>
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeSection === 'features' && (
            <div className="space-y-6">
              <div>
                <h4 className="font-medium text-neutral-900 mb-3">Platform Features</h4>
                <div className="space-y-3">
                  {Object.entries(settings.features_enabled).map(([feature, enabled]) => (
                    <div key={feature} className="flex items-center justify-between p-3 border border-neutral-200 rounded-lg">
                      <div>
                        <h5 className="font-medium text-neutral-900 capitalize">
                          {feature.replace(/_/g, ' ')}
                        </h5>
                        <p className="text-sm text-neutral-600">
                          {getFeatureDescription(feature)}
                        </p>
                      </div>
                      
                      <div className="flex items-center space-x-2">
                        <Badge variant={enabled ? 'success' : 'neutral'} size="sm">
                          {enabled ? 'Enabled' : 'Disabled'}
                        </Badge>
                        <input
                          type="checkbox"
                          checked={enabled}
                          onChange={(e) => updateSetting(`features_enabled.${feature}`, e.target.checked)}
                          className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-neutral-300 rounded"
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Actions */}
          <div className="flex justify-between pt-6 border-t border-neutral-200">
            <Button
              variant="outline"
              onClick={resetChanges}
              disabled={!hasChanges || isSaving}
            >
              Reset Changes
            </Button>
            
            <Button
              variant="primary"
              onClick={saveSettings}
              disabled={!hasChanges || isSaving}
            >
              {isSaving ? 'Saving...' : 'Save Settings'}
            </Button>
          </div>
        </CardBody>
      </Card>
    </div>
  );
};

// Helper function to get feature descriptions
function getFeatureDescription(feature: string): string {
  const descriptions: Record<string, string> = {
    transparency_tracking: 'Track and monitor supply chain transparency metrics',
    supplier_onboarding: 'Enable supplier invitation and onboarding workflows',
    advanced_analytics: 'Access to advanced analytics and reporting features',
    api_access: 'Programmatic access to platform APIs',
    webhook_notifications: 'Receive notifications via webhook endpoints',
  };
  
  return descriptions[feature] || 'Feature description not available';
}

export default CompanySettings;
