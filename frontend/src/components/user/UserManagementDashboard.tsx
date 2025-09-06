/**
 * User Management Dashboard
 * Main dashboard for notification and user management
 */
import React, { useState } from 'react';
import { 
  BellIcon,
  UserCircleIcon,
  Cog6ToothIcon,
  ClockIcon,
  ChartBarIcon,
  BuildingOfficeIcon,
} from '@heroicons/react/24/outline';
import { useNotifications } from '../../contexts/NotificationContext';
import { useUIPermissions, PermissionGate } from '../../hooks/useUIPermissions';
import { Card, CardHeader, CardBody } from '../ui/Card';
import Button from '../ui/Button';
import Badge from '../ui/Badge';
import NotificationCenter from '../notifications/NotificationCenter';
import NotificationPreferences from '../notifications/NotificationPreferences';
import NotificationHistory from '../notifications/NotificationHistory';
import UserProfile from './UserProfile';
import CompanySettings from './CompanySettings';
import { cn } from '../../lib/utils';

interface UserManagementDashboardProps {
  className?: string;
}

type TabType = 'overview' | 'notifications' | 'preferences' | 'history' | 'profile' | 'company';

const UserManagementDashboard: React.FC<UserManagementDashboardProps> = ({
  className,
}) => {
  const { summary, isConnected } = useNotifications();
  const { permissions } = useUIPermissions();
  const [activeTab, setActiveTab] = useState<TabType>('overview');
  const [showNotificationCenter, setShowNotificationCenter] = useState(false);

  // Tab configuration
  const tabs = [
    {
      id: 'overview' as TabType,
      label: 'Overview',
      icon: ChartBarIcon,
      description: 'Dashboard overview and quick actions',
    },
    {
      id: 'notifications' as TabType,
      label: 'Notifications',
      icon: BellIcon,
      description: 'Real-time notification center',
      badge: summary?.unread_count || 0,
    },
    {
      id: 'preferences' as TabType,
      label: 'Preferences',
      icon: Cog6ToothIcon,
      description: 'Notification and communication preferences',
    },
    {
      id: 'history' as TabType,
      label: 'History',
      icon: ClockIcon,
      description: 'View and manage notification history',
    },
    {
      id: 'profile' as TabType,
      label: 'Profile',
      icon: UserCircleIcon,
      description: 'User profile and account settings',
    },
    {
      id: 'company' as TabType,
      label: 'Company',
      icon: BuildingOfficeIcon,
      description: 'Company settings and configuration',
      permission: { type: 'feature' as const, permission: 'manage_company_settings' as const },
    },
  ];

  // Filter tabs based on permissions
  const availableTabs = tabs.filter(tab => {
    if (!tab.permission) return true;
    
    if (tab.permission.type === 'feature') {
      return permissions?.features[tab.permission.permission as keyof typeof permissions.features];
    }
    
    return true;
  });

  // Render tab content
  const renderTabContent = () => {
    switch (activeTab) {
      case 'overview':
        return <OverviewTab />;
      case 'notifications':
        return <NotificationCenter isOpen={true} onClose={() => {}} />;
      case 'preferences':
        return <NotificationPreferences />;
      case 'history':
        return <NotificationHistory />;
      case 'profile':
        return <UserProfile />;
      case 'company':
        return <CompanySettings />;
      default:
        return <OverviewTab />;
    }
  };

  return (
    <div className={cn('space-y-6', className)}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-neutral-900">User Management</h1>
          <p className="text-neutral-600">
            Manage your notifications, profile, and account settings
          </p>
        </div>
        
        <div className="flex items-center space-x-3">
          {/* Connection status */}
          <div className="flex items-center space-x-2">
            <div className={cn(
              'h-2 w-2 rounded-full',
              isConnected ? 'bg-success-500' : 'bg-error-500'
            )} />
            <span className="text-sm text-neutral-600">
              {isConnected ? 'Connected' : 'Disconnected'}
            </span>
          </div>
          
          {/* Quick notification access */}
          <Button
            variant="outline"
            onClick={() => setShowNotificationCenter(true)}
            leftIcon={<BellIcon className="h-4 w-4" />}
            className="relative"
          >
            Notifications
            {summary && summary.unread_count > 0 && (
              <Badge variant="error" size="sm" className="absolute -top-2 -right-2">
                {summary.unread_count}
              </Badge>
            )}
          </Button>
        </div>
      </div>

      {/* Tab Navigation */}
      <Card>
        <CardBody className="p-0">
          <div className="border-b border-neutral-200">
            <nav className="flex space-x-8 px-6">
              {availableTabs.map((tab) => {
                const Icon = tab.icon;
                const isActive = activeTab === tab.id;
                
                return (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={cn(
                      'flex items-center space-x-2 py-4 px-1 border-b-2 font-medium text-sm transition-colors relative',
                      isActive
                        ? 'border-primary-500 text-primary-600'
                        : 'border-transparent text-neutral-500 hover:text-neutral-700 hover:border-neutral-300'
                    )}
                  >
                    <Icon className="h-5 w-5" />
                    <span>{tab.label}</span>
                    {tab.badge && tab.badge > 0 && (
                      <Badge variant="primary" size="sm">
                        {tab.badge}
                      </Badge>
                    )}
                  </button>
                );
              })}
            </nav>
          </div>
          
          {/* Tab description */}
          <div className="px-6 py-3 bg-neutral-50">
            <p className="text-sm text-neutral-600">
              {availableTabs.find(tab => tab.id === activeTab)?.description}
            </p>
          </div>
        </CardBody>
      </Card>

      {/* Tab Content */}
      <div className="min-h-[600px]">
        {renderTabContent()}
      </div>

      {/* Notification Center Modal */}
      <NotificationCenter
        isOpen={showNotificationCenter}
        onClose={() => setShowNotificationCenter(false)}
      />
    </div>
  );
};

// Overview Tab Component
const OverviewTab: React.FC = () => {
  const { summary } = useNotifications();
  const { permissions } = useUIPermissions();

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      {/* Notification Summary */}
      <Card>
        <CardHeader 
          title="Notifications"
          subtitle="Recent activity summary"
        />
        <CardBody>
          {summary ? (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="text-center">
                  <div className="text-2xl font-bold text-primary-600">
                    {summary.unread_count}
                  </div>
                  <div className="text-sm text-neutral-600">Unread</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-neutral-900">
                    {summary.total_count}
                  </div>
                  <div className="text-sm text-neutral-600">Total</div>
                </div>
              </div>
              
              {summary.high_priority_count > 0 && (
                <div className="p-3 bg-warning-50 border border-warning-200 rounded-lg">
                  <div className="flex items-center space-x-2">
                    <div className="h-2 w-2 bg-warning-500 rounded-full" />
                    <span className="text-sm font-medium text-warning-800">
                      {summary.high_priority_count} high priority notifications
                    </span>
                  </div>
                </div>
              )}
              
              <div className="space-y-2">
                <h4 className="font-medium text-neutral-900">Recent Notifications</h4>
                {summary.recent_notifications.slice(0, 3).map((notification) => (
                  <div key={notification.id} className="text-sm">
                    <div className="font-medium text-neutral-900 truncate">
                      {notification.title}
                    </div>
                    <div className="text-neutral-600 truncate">
                      {notification.message}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="text-center py-4">
              <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary-600 mx-auto"></div>
              <p className="mt-2 text-sm text-neutral-600">Loading...</p>
            </div>
          )}
        </CardBody>
      </Card>

      {/* User Info */}
      <Card>
        <CardHeader 
          title="Profile"
          subtitle="Your account information"
        />
        <CardBody>
          <div className="space-y-4">
            <div className="flex items-center space-x-3">
              <div className="h-12 w-12 bg-primary-100 rounded-full flex items-center justify-center">
                <span className="text-primary-700 font-medium">
                  {permissions?.user_role?.charAt(0).toUpperCase() || 'U'}
                </span>
              </div>
              <div>
                <div className="font-medium text-neutral-900">User Profile</div>
                <div className="text-sm text-neutral-600 capitalize">
                  {permissions?.user_role || 'User'} Role
                </div>
              </div>
            </div>
            
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-neutral-600">Profile Completion</span>
                <span className="font-medium">85%</span>
              </div>
              <div className="w-full bg-neutral-200 rounded-full h-2">
                <div className="bg-primary-600 h-2 rounded-full" style={{ width: '85%' }} />
              </div>
            </div>
            
            <Button variant="outline" size="sm" className="w-full">
              Edit Profile
            </Button>
          </div>
        </CardBody>
      </Card>

      {/* Quick Actions */}
      <Card>
        <CardHeader 
          title="Quick Actions"
          subtitle="Common tasks and settings"
        />
        <CardBody>
          <div className="space-y-3">
            <Button variant="outline" size="sm" className="w-full justify-start">
              <BellIcon className="h-4 w-4 mr-2" />
              Notification Preferences
            </Button>
            
            <Button variant="outline" size="sm" className="w-full justify-start">
              <ClockIcon className="h-4 w-4 mr-2" />
              View History
            </Button>
            
            <Button variant="outline" size="sm" className="w-full justify-start">
              <UserCircleIcon className="h-4 w-4 mr-2" />
              Update Profile
            </Button>
            
            <PermissionGate feature="manage_company_settings">
              <Button variant="outline" size="sm" className="w-full justify-start">
                <BuildingOfficeIcon className="h-4 w-4 mr-2" />
                Company Settings
              </Button>
            </PermissionGate>
          </div>
        </CardBody>
      </Card>
    </div>
  );
};

export default UserManagementDashboard;
