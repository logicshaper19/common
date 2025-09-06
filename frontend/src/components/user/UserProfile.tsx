/**
 * User Profile Component
 * User profile and account settings management
 */
import React, { useState, useEffect } from 'react';
import {
  UserCircleIcon,
  PencilIcon,
  CameraIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  ShieldCheckIcon,
  ClockIcon,
  Cog6ToothIcon,
} from '@heroicons/react/24/outline';
import { useAuth } from '../../contexts/AuthContext';
import { notificationApi } from '../../lib/notificationApi';
import { Card, CardHeader, CardBody } from '../ui/Card';
import Button from '../ui/Button';
import Input from '../ui/Input';
import Select from '../ui/Select';
import Textarea from '../ui/Textarea';
import Badge from '../ui/Badge';
import { UserProfile as UserProfileType } from '../../types/notifications';
import { cn, formatDate } from '../../lib/utils';

interface UserProfileProps {
  className?: string;
}

const UserProfile: React.FC<UserProfileProps> = ({
  className,
}) => {
  const { user, refreshUser } = useAuth();
  const [profile, setProfile] = useState<UserProfileType | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [hasChanges, setHasChanges] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'profile' | 'security' | 'preferences'>('profile');

  // Load profile on mount
  useEffect(() => {
    loadProfile();
  }, []);

  const loadProfile = async () => {
    setIsLoading(true);
    try {
      const data = await notificationApi.getUserProfile();
      setProfile(data);
    } catch (error) {
      console.error('Failed to load profile:', error);
      setError('Failed to load user profile');
    } finally {
      setIsLoading(false);
    }
  };

  // Handle profile field changes
  const updateProfile = (field: string, value: any) => {
    if (!profile) return;

    setProfile(prev => ({ ...prev!, [field]: value }));
    setHasChanges(true);
  };

  // Save profile changes
  const saveProfile = async () => {
    if (!profile || !hasChanges) return;

    setIsSaving(true);
    setError(null);
    try {
      const updatedProfile = await notificationApi.updateUserProfile(profile);
      setProfile(updatedProfile);
      setHasChanges(false);
      setSuccessMessage('Profile updated successfully');
      setTimeout(() => setSuccessMessage(null), 3000);
      
      // Refresh auth context
      await refreshUser();
    } catch (error) {
      console.error('Failed to save profile:', error);
      setError('Failed to save profile changes');
    } finally {
      setIsSaving(false);
    }
  };

  // Reset changes
  const resetChanges = () => {
    loadProfile();
    setHasChanges(false);
  };

  // Calculate profile completion
  const calculateProfileCompletion = (profile: UserProfileType): number => {
    const fields = [
      profile.full_name,
      profile.email,
      profile.title,
      profile.phone,
      profile.department,
      profile.timezone,
      profile.language,
    ];
    
    const completedFields = fields.filter(field => field && field.trim() !== '').length;
    return Math.round((completedFields / fields.length) * 100);
  };

  if (isLoading) {
    return (
      <Card className={className}>
        <CardBody>
          <div className="text-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600 mx-auto"></div>
            <p className="mt-2 text-neutral-600">Loading profile...</p>
          </div>
        </CardBody>
      </Card>
    );
  }

  if (!profile) {
    return (
      <Card className={className}>
        <CardBody>
          <div className="text-center py-8">
            <UserCircleIcon className="h-12 w-12 text-neutral-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-neutral-900 mb-2">Unable to Load Profile</h3>
            <p className="text-neutral-600 mb-4">There was an error loading your profile.</p>
            <Button variant="primary" onClick={loadProfile}>
              Try Again
            </Button>
          </div>
        </CardBody>
      </Card>
    );
  }

  const profileCompletion = calculateProfileCompletion(profile);

  return (
    <div className={className}>
      <Card>
        <CardHeader 
          title="User Profile"
          subtitle="Manage your account information and preferences"
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

          {/* Profile Completion */}
          <div className="mb-6 p-4 bg-primary-50 border border-primary-200 rounded-lg">
            <div className="flex items-center justify-between mb-2">
              <h3 className="font-medium text-primary-900">Profile Completion</h3>
              <Badge variant="primary">{profileCompletion}%</Badge>
            </div>
            <div className="w-full bg-primary-200 rounded-full h-2">
              <div 
                className="bg-primary-600 h-2 rounded-full transition-all duration-300"
                style={{ width: `${profileCompletion}%` }}
              />
            </div>
            <p className="text-sm text-primary-800 mt-2">
              Complete your profile to improve your experience on the platform.
            </p>
          </div>

          {/* Tab Navigation */}
          <div className="border-b border-neutral-200 mb-6">
            <nav className="-mb-px flex space-x-8">
              {[
                { id: 'profile', label: 'Profile Information', icon: UserCircleIcon },
                { id: 'security', label: 'Security', icon: ShieldCheckIcon },
                { id: 'preferences', label: 'Preferences', icon: Cog6ToothIcon },
              ].map((tab) => {
                const Icon = tab.icon;
                const isActive = activeTab === tab.id;
                
                return (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id as any)}
                    className={cn(
                      'flex items-center space-x-2 py-2 px-1 border-b-2 font-medium text-sm transition-colors',
                      isActive
                        ? 'border-primary-500 text-primary-600'
                        : 'border-transparent text-neutral-500 hover:text-neutral-700 hover:border-neutral-300'
                    )}
                  >
                    <Icon className="h-5 w-5" />
                    <span>{tab.label}</span>
                  </button>
                );
              })}
            </nav>
          </div>

          {/* Tab Content */}
          {activeTab === 'profile' && (
            <div className="space-y-6">
              {/* Avatar Section */}
              <div className="flex items-center space-x-4">
                <div className="relative">
                  <div className="h-20 w-20 bg-primary-100 rounded-full flex items-center justify-center">
                    {profile.avatar_url ? (
                      <img
                        src={profile.avatar_url}
                        alt={profile.full_name}
                        className="h-20 w-20 rounded-full object-cover"
                      />
                    ) : (
                      <span className="text-2xl font-medium text-primary-700">
                        {profile.full_name.charAt(0)}
                      </span>
                    )}
                  </div>
                  <button className="absolute -bottom-1 -right-1 h-8 w-8 bg-white border-2 border-neutral-300 rounded-full flex items-center justify-center hover:bg-neutral-50">
                    <CameraIcon className="h-4 w-4 text-neutral-600" />
                  </button>
                </div>
                
                <div>
                  <h3 className="text-lg font-medium text-neutral-900">{profile.full_name}</h3>
                  <p className="text-neutral-600">{profile.title || 'No title set'}</p>
                  <p className="text-sm text-neutral-500">{profile.company_name}</p>
                </div>
              </div>

              {/* Basic Information */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <Input
                  label="Full Name"
                  value={profile.full_name}
                  onChange={(e) => updateProfile('full_name', e.target.value)}
                  required
                />
                
                <Input
                  label="Email"
                  type="email"
                  value={profile.email}
                  onChange={(e) => updateProfile('email', e.target.value)}
                  required
                />
                
                <Input
                  label="Job Title"
                  value={profile.title || ''}
                  onChange={(e) => updateProfile('title', e.target.value)}
                  placeholder="e.g., Supply Chain Manager"
                />
                
                <Input
                  label="Phone"
                  type="tel"
                  value={profile.phone || ''}
                  onChange={(e) => updateProfile('phone', e.target.value)}
                  placeholder="+1 (555) 123-4567"
                />
                
                <Input
                  label="Department"
                  value={profile.department || ''}
                  onChange={(e) => updateProfile('department', e.target.value)}
                  placeholder="e.g., Supply Chain"
                />
                
                <Select
                  label="Role"
                  value={profile.role}
                  onChange={(e) => updateProfile('role', e.target.value)}
                  disabled
                  options={[
                    { value: 'admin', label: 'Administrator' },
                    { value: 'buyer', label: 'Buyer' },
                    { value: 'seller', label: 'Seller' },
                    { value: 'viewer', label: 'Viewer' }
                  ]}
                />
              </div>

              {/* Preferences */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <Select
                  label="Timezone"
                  value={profile.timezone}
                  onChange={(e) => updateProfile('timezone', e.target.value)}
                  options={[
                    { value: 'America/New_York', label: 'Eastern Time (ET)' },
                    { value: 'America/Chicago', label: 'Central Time (CT)' },
                    { value: 'America/Denver', label: 'Mountain Time (MT)' },
                    { value: 'America/Los_Angeles', label: 'Pacific Time (PT)' },
                    { value: 'UTC', label: 'UTC' }
                  ]}
                />
                
                <Select
                  label="Language"
                  value={profile.language}
                  onChange={(e) => updateProfile('language', e.target.value)}
                  options={[
                    { value: 'en', label: 'English' },
                    { value: 'es', label: 'Spanish' },
                    { value: 'fr', label: 'French' },
                    { value: 'de', label: 'German' }
                  ]}
                />
                
                <Select
                  label="Date Format"
                  value={profile.date_format}
                  onChange={(e) => updateProfile('date_format', e.target.value)}
                  options={[
                    { value: 'MM/DD/YYYY', label: 'MM/DD/YYYY' },
                    { value: 'DD/MM/YYYY', label: 'DD/MM/YYYY' },
                    { value: 'YYYY-MM-DD', label: 'YYYY-MM-DD' }
                  ]}
                />
                
                <Select
                  label="Time Format"
                  value={profile.time_format}
                  onChange={(e) => updateProfile('time_format', e.target.value)}
                  options={[
                    { value: '12h', label: '12 Hour' },
                    { value: '24h', label: '24 Hour' }
                  ]}
                />
              </div>
            </div>
          )}

          {activeTab === 'security' && (
            <div className="space-y-6">
              {/* Security Status */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="p-4 border border-neutral-200 rounded-lg">
                  <div className="flex items-center justify-between mb-2">
                    <h4 className="font-medium text-neutral-900">Two-Factor Authentication</h4>
                    <Badge variant={profile.two_factor_enabled ? 'success' : 'warning'}>
                      {profile.two_factor_enabled ? 'Enabled' : 'Disabled'}
                    </Badge>
                  </div>
                  <p className="text-sm text-neutral-600 mb-3">
                    Add an extra layer of security to your account.
                  </p>
                  <Button
                    variant={profile.two_factor_enabled ? 'outline' : 'primary'}
                    size="sm"
                  >
                    {profile.two_factor_enabled ? 'Disable 2FA' : 'Enable 2FA'}
                  </Button>
                </div>

                <div className="p-4 border border-neutral-200 rounded-lg">
                  <div className="flex items-center justify-between mb-2">
                    <h4 className="font-medium text-neutral-900">Password</h4>
                    <ClockIcon className="h-5 w-5 text-neutral-400" />
                  </div>
                  <p className="text-sm text-neutral-600 mb-1">
                    Last changed: {formatDate(profile.password_changed_at)}
                  </p>
                  <p className="text-sm text-neutral-600 mb-3">
                    Regular password updates help keep your account secure.
                  </p>
                  <Button variant="outline" size="sm">
                    Change Password
                  </Button>
                </div>
              </div>

              {/* Login Activity */}
              <div>
                <h4 className="font-medium text-neutral-900 mb-3">Recent Activity</h4>
                <div className="space-y-2">
                  <div className="flex items-center justify-between p-3 bg-neutral-50 rounded-lg">
                    <div>
                      <p className="text-sm font-medium text-neutral-900">Last login</p>
                      <p className="text-sm text-neutral-600">
                        {profile.last_login_at ? formatDate(profile.last_login_at) : 'Never'}
                      </p>
                    </div>
                    <Badge variant="success" size="sm">Current session</Badge>
                  </div>
                  
                  <div className="flex items-center justify-between p-3 bg-neutral-50 rounded-lg">
                    <div>
                      <p className="text-sm font-medium text-neutral-900">Account created</p>
                      <p className="text-sm text-neutral-600">{formatDate(profile.created_at)}</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'preferences' && (
            <div className="space-y-6">
              <div className="text-center py-8">
                <p className="text-neutral-600">
                  Notification preferences are managed in the 
                  <Button variant="link" className="mx-1">
                    Notification Settings
                  </Button>
                  section.
                </p>
              </div>
            </div>
          )}

          {/* Actions */}
          {activeTab === 'profile' && (
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
                onClick={saveProfile}
                disabled={!hasChanges || isSaving}
              >
                {isSaving ? 'Saving...' : 'Save Changes'}
              </Button>
            </div>
          )}
        </CardBody>
      </Card>
    </div>
  );
};

export default UserProfile;
