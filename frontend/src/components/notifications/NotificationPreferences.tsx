/**
 * Notification Preferences Component
 * User preference management interface for notifications
 */
import React, { useState, useEffect } from 'react';
import { 
  BellIcon,
  EnvelopeIcon,
  DevicePhoneMobileIcon,
  ComputerDesktopIcon,
  ClockIcon,
  CheckCircleIcon,
} from '@heroicons/react/24/outline';
import { notificationApi } from '../../lib/notificationApi';
import { Card, CardHeader, CardBody } from '../ui/Card';
import Button from '../ui/Button';
import Select from '../ui/Select';
import Badge from '../ui/Badge';
import { 
  NotificationPreferences as NotificationPreferencesType,
  NotificationType,
  NotificationChannel,
  NotificationPriority,
} from '../../types/notifications';
import { cn } from '../../lib/utils';

interface NotificationPreferencesProps {
  className?: string;
}

const NotificationPreferences: React.FC<NotificationPreferencesProps> = ({
  className,
}) => {
  const [preferences, setPreferences] = useState<NotificationPreferencesType | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [hasChanges, setHasChanges] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // Load preferences on mount
  useEffect(() => {
    loadPreferences();
  }, []);

  const loadPreferences = async () => {
    setIsLoading(true);
    try {
      const data = await notificationApi.getNotificationPreferences();
      setPreferences(data);
    } catch (error) {
      console.error('Failed to load preferences:', error);
      setError('Failed to load notification preferences');
    } finally {
      setIsLoading(false);
    }
  };

  // Handle preference changes
  const updatePreference = (
    notificationType: NotificationType,
    field: string,
    value: any
  ) => {
    if (!preferences) return;

    setPreferences(prev => ({
      ...prev!,
      preferences: {
        ...prev!.preferences,
        [notificationType]: {
          ...prev!.preferences[notificationType],
          [field]: value,
        },
      },
    }));
    setHasChanges(true);
  };

  // Handle global settings changes
  const updateGlobalSetting = (section: string, field: string, value: any) => {
    if (!preferences) return;

    setPreferences(prev => {
      if (!prev) return prev;
      return {
        ...prev,
        global_settings: {
          ...prev.global_settings,
          [section]: {
            ...(prev.global_settings[section as keyof typeof prev.global_settings] as any || {}),
            [field]: value,
          },
        },
      };
    });
    setHasChanges(true);
  };

  // Save preferences
  const savePreferences = async () => {
    if (!preferences || !hasChanges) return;

    setIsSaving(true);
    setError(null);
    try {
      await notificationApi.updateNotificationPreferences(preferences);
      setHasChanges(false);
      setSuccessMessage('Preferences saved successfully');
      setTimeout(() => setSuccessMessage(null), 3000);
    } catch (error) {
      console.error('Failed to save preferences:', error);
      setError('Failed to save preferences');
    } finally {
      setIsSaving(false);
    }
  };

  // Reset preferences
  const resetPreferences = () => {
    loadPreferences();
    setHasChanges(false);
  };

  // Notification type labels
  const notificationTypeLabels: Record<NotificationType, string> = {
    po_created: 'Purchase Order Created',
    po_confirmed: 'Purchase Order Confirmed',
    po_shipped: 'Purchase Order Shipped',
    po_delivered: 'Purchase Order Delivered',
    po_cancelled: 'Purchase Order Cancelled',
    transparency_updated: 'Transparency Score Updated',
    supplier_invited: 'Supplier Invited',
    supplier_joined: 'Supplier Joined',
    system_alert: 'System Alerts',
    user_mention: 'User Mentions',
    deadline_reminder: 'Deadline Reminders',
    quality_issue: 'Quality Issues',
    compliance_alert: 'Compliance Alerts',
  };

  // Channel icons
  const channelIcons: Record<NotificationChannel, React.ComponentType<any>> = {
    in_app: BellIcon,
    email: EnvelopeIcon,
    sms: DevicePhoneMobileIcon,
    webhook: ComputerDesktopIcon,
  };

  // Priority colors
  const priorityColors: Record<NotificationPriority, string> = {
    urgent: 'text-error-600',
    high: 'text-warning-600',
    normal: 'text-primary-600',
    low: 'text-neutral-600',
  };

  if (isLoading) {
    return (
      <Card className={className}>
        <CardBody>
          <div className="text-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600 mx-auto"></div>
            <p className="mt-2 text-neutral-600">Loading preferences...</p>
          </div>
        </CardBody>
      </Card>
    );
  }

  if (!preferences) {
    return (
      <Card className={className}>
        <CardBody>
          <div className="text-center py-8">
            <BellIcon className="h-12 w-12 text-neutral-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-neutral-900 mb-2">Unable to Load Preferences</h3>
            <p className="text-neutral-600 mb-4">There was an error loading your notification preferences.</p>
            <Button variant="primary" onClick={loadPreferences}>
              Try Again
            </Button>
          </div>
        </CardBody>
      </Card>
    );
  }

  return (
    <div className={className}>
      <Card>
        <CardHeader
          title="Notification Preferences"
          subtitle="Configure how and when you receive notifications"
          action={<BellIcon className="h-5 w-5 text-neutral-400" />}
        />
        
        <CardBody>
          {/* Error/Success Messages */}
          {error && (
            <div className="mb-4 p-3 bg-error-50 border border-error-200 rounded-lg text-error-800">
              {error}
            </div>
          )}
          
          {successMessage && (
            <div className="mb-4 p-3 bg-success-50 border border-success-200 rounded-lg text-success-800 flex items-center">
              <CheckCircleIcon className="h-5 w-5 mr-2" />
              {successMessage}
            </div>
          )}

          {/* Global Settings */}
          <div className="mb-8">
            <h3 className="text-lg font-medium text-neutral-900 mb-4">Global Settings</h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Email Digest */}
              <div className="space-y-3">
                <h4 className="font-medium text-neutral-900">Email Digest</h4>
                <div className="space-y-2">
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={preferences?.global_settings?.email_digest?.enabled || false}
                      onChange={(e) => updateGlobalSetting('email_digest', 'enabled', e.target.checked)}
                      className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-neutral-300 rounded"
                    />
                    <span className="ml-2 text-sm text-neutral-700">Enable email digest</span>
                  </label>
                  
                  {(preferences?.global_settings?.email_digest?.enabled || false) && (
                    <div className="ml-6 space-y-2">
                      <Select
                        value={preferences?.global_settings?.email_digest?.frequency || 'daily'}
                        onChange={(e) => updateGlobalSetting('email_digest', 'frequency', e.target.value)}
                        size="sm"
                        options={[
                          { label: 'Immediate', value: 'immediate' },
                          { label: 'Hourly', value: 'hourly' },
                          { label: 'Daily', value: 'daily' },
                          { label: 'Weekly', value: 'weekly' }
                        ]}
                      />
                      
                      {((preferences?.global_settings?.email_digest?.frequency || 'daily') === 'daily' || 
                        (preferences?.global_settings?.email_digest?.frequency || 'daily') === 'weekly') && (
                        <input
                          type="time"
                          value={preferences?.global_settings?.email_digest?.time || '09:00'}
                          onChange={(e) => updateGlobalSetting('email_digest', 'time', e.target.value)}
                          className="block w-full px-3 py-2 border border-neutral-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                        />
                      )}
                    </div>
                  )}
                </div>
              </div>

              {/* Desktop Notifications */}
              <div className="space-y-3">
                <h4 className="font-medium text-neutral-900">Desktop Notifications</h4>
                <div className="space-y-2">
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={preferences?.global_settings?.desktop_notifications?.enabled || false}
                      onChange={(e) => updateGlobalSetting('desktop_notifications', 'enabled', e.target.checked)}
                      className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-neutral-300 rounded"
                    />
                    <span className="ml-2 text-sm text-neutral-700">Enable desktop notifications</span>
                  </label>
                  
                  {(preferences?.global_settings?.desktop_notifications?.enabled || false) && (
                    <label className="flex items-center ml-6">
                      <input
                        type="checkbox"
                        checked={preferences?.global_settings?.desktop_notifications?.sound || false}
                        onChange={(e) => updateGlobalSetting('desktop_notifications', 'sound', e.target.checked)}
                        className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-neutral-300 rounded"
                      />
                      <span className="ml-2 text-sm text-neutral-700">Play sound</span>
                    </label>
                  )}
                </div>
              </div>
            </div>
          </div>

          {/* Notification Type Preferences */}
          <div className="mb-8">
            <h3 className="text-lg font-medium text-neutral-900 mb-4">Notification Types</h3>
            
            <div className="space-y-4">
              {Object.entries(preferences?.preferences || {}).map(([type, pref]) => {
                const notificationType = type as NotificationType;
                
                return (
                  <div key={type} className="border border-neutral-200 rounded-lg p-4">
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center space-x-3">
                        <input
                          type="checkbox"
                          checked={pref.enabled}
                          onChange={(e) => updatePreference(notificationType, 'enabled', e.target.checked)}
                          className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-neutral-300 rounded"
                        />
                        <h4 className="font-medium text-neutral-900">
                          {notificationTypeLabels[notificationType]}
                        </h4>
                      </div>
                      
                      <Badge 
                        variant={pref.priority_threshold === 'urgent' ? 'error' : 
                               pref.priority_threshold === 'high' ? 'warning' : 'primary'}
                        size="sm"
                      >
                        {pref.priority_threshold}+ priority
                      </Badge>
                    </div>
                    
                    {pref.enabled && (
                      <div className="ml-7 space-y-3">
                        {/* Channels */}
                        <div>
                          <label className="block text-sm font-medium text-neutral-700 mb-2">
                            Delivery Channels
                          </label>
                          <div className="flex flex-wrap gap-2">
                            {(['in_app', 'email', 'sms'] as NotificationChannel[]).map((channel) => {
                              const Icon = channelIcons[channel];
                              const isSelected = pref.channels.includes(channel);
                              
                              return (
                                <button
                                  key={channel}
                                  onClick={() => {
                                    const newChannels = isSelected
                                      ? pref.channels.filter(c => c !== channel)
                                      : [...pref.channels, channel];
                                    updatePreference(notificationType, 'channels', newChannels);
                                  }}
                                  className={cn(
                                    'flex items-center space-x-2 px-3 py-2 rounded-lg border text-sm font-medium transition-colors',
                                    isSelected
                                      ? 'bg-primary-50 border-primary-200 text-primary-700'
                                      : 'bg-white border-neutral-300 text-neutral-700 hover:bg-neutral-50'
                                  )}
                                >
                                  <Icon className="h-4 w-4" />
                                  <span className="capitalize">{channel.replace('_', ' ')}</span>
                                </button>
                              );
                            })}
                          </div>
                        </div>
                        
                        {/* Priority Threshold */}
                        <div>
                          <label className="block text-sm font-medium text-neutral-700 mb-2">
                            Minimum Priority
                          </label>
                          <Select
                            value={pref.priority_threshold}
                            onChange={(e) => updatePreference(notificationType, 'priority_threshold', e.target.value)}
                            size="sm"
                            className="w-32"
                            options={[
                              { label: 'Low', value: 'low' },
                              { label: 'Normal', value: 'normal' },
                              { label: 'High', value: 'high' },
                              { label: 'Urgent', value: 'urgent' }
                            ]}
                          />
                        </div>
                        
                        {/* Quiet Hours (for specific types) */}
                        {(notificationType === 'deadline_reminder' || notificationType === 'system_alert') && (
                          <div>
                            <label className="flex items-center mb-2">
                              <input
                                type="checkbox"
                                checked={pref.quiet_hours?.enabled || false}
                                onChange={(e) => updatePreference(notificationType, 'quiet_hours', {
                                  ...pref.quiet_hours,
                                  enabled: e.target.checked,
                                })}
                                className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-neutral-300 rounded"
                              />
                              <span className="ml-2 text-sm font-medium text-neutral-700">
                                Enable quiet hours
                              </span>
                            </label>
                            
                            {pref.quiet_hours?.enabled && (
                              <div className="ml-6 flex items-center space-x-2">
                                <ClockIcon className="h-4 w-4 text-neutral-500" />
                                <input
                                  type="time"
                                  value={pref.quiet_hours?.start_time || '22:00'}
                                  onChange={(e) => updatePreference(notificationType, 'quiet_hours', {
                                    ...pref.quiet_hours,
                                    start_time: e.target.value,
                                  })}
                                  className="px-2 py-1 border border-neutral-300 rounded text-sm"
                                />
                                <span className="text-sm text-neutral-500">to</span>
                                <input
                                  type="time"
                                  value={pref.quiet_hours?.end_time || '08:00'}
                                  onChange={(e) => updatePreference(notificationType, 'quiet_hours', {
                                    ...pref.quiet_hours,
                                    end_time: e.target.value,
                                  })}
                                  className="px-2 py-1 border border-neutral-300 rounded text-sm"
                                />
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>

          {/* Actions */}
          <div className="flex justify-between">
            <Button
              variant="outline"
              onClick={resetPreferences}
              disabled={!hasChanges || isSaving}
            >
              Reset Changes
            </Button>
            
            <Button
              variant="primary"
              onClick={savePreferences}
              disabled={!hasChanges || isSaving}
            >
              {isSaving ? 'Saving...' : 'Save Preferences'}
            </Button>
          </div>
        </CardBody>
      </Card>
    </div>
  );
};

export default NotificationPreferences;
