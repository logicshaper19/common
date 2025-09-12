/**
 * Platform Admin Dashboard V2 - Role-specific dashboard for platform administrators
 * Focuses on platform health, user management, and system oversight
 */
import React from 'react';
import { useDashboardConfig, useDashboardMetrics } from '../../../hooks/useDashboardConfig';
import LoadingSpinner from '../../ui/LoadingSpinner';
import { Card, CardHeader, CardBody } from '../../ui/Card';
import { Button } from '../../ui/Button';
import { Badge } from '../../ui/Badge';
import TeamManagementWidget from '../shared/TeamManagementWidget';
import NotificationCenterWidget from '../shared/NotificationCenterWidget';
import { 
  ServerIcon,
  UsersIcon,
  ChartBarIcon,
  ExclamationTriangleIcon,
  CogIcon,
  EyeIcon,
  ClockIcon
} from '@heroicons/react/24/outline';

interface PlatformOverview {
  total_companies: number;
  active_users: number;
  total_pos: number;
}

interface SystemHealth {
  api_response_time: number;
  error_rate: number;
  uptime_percentage: number;
}

interface RecentActivity {
  new_companies: number;
  support_tickets: number;
}

interface PlatformAdminMetrics {
  platform_overview: PlatformOverview;
  system_health: SystemHealth;
  recent_activity: RecentActivity;
}

export const PlatformAdminDashboardV2: React.FC = () => {
  const { config, loading: configLoading } = useDashboardConfig();
  const { metrics, loading: metricsLoading } = useDashboardMetrics('platform-admin');

  if (configLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner size="lg" />
        <span className="ml-3 text-gray-600">Loading dashboard...</span>
      </div>
    );
  }

  if (!config) {
    return (
      <div className="text-center py-12">
        <p className="text-red-600">Failed to load dashboard configuration</p>
      </div>
    );
  }

  const adminMetrics = metrics as PlatformAdminMetrics;

  const getHealthStatusColor = (value: number, type: 'uptime' | 'response_time' | 'error_rate') => {
    switch (type) {
      case 'uptime':
        if (value >= 99.9) return 'green';
        if (value >= 99.5) return 'yellow';
        return 'red';
      case 'response_time':
        if (value <= 200) return 'green';
        if (value <= 500) return 'yellow';
        return 'red';
      case 'error_rate':
        if (value <= 0.1) return 'green';
        if (value <= 1.0) return 'yellow';
        return 'red';
      default:
        return 'gray';
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white shadow-sm border-b border-gray-200">
        <div className="px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Platform Admin Dashboard</h1>
              <p className="text-gray-600">
                Monitor platform health, manage users, and oversee system operations
              </p>
            </div>
            <div className="flex space-x-3">
              <Button variant="outline">
                <CogIcon className="h-4 w-4 mr-2" />
                System Settings
              </Button>
              <Button>
                <UsersIcon className="h-4 w-4 mr-2" />
                User Management
              </Button>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="px-6">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column - Main Metrics */}
          <div className="lg:col-span-2 space-y-6">
            {/* Platform Overview */}
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div className="flex items-center">
                    <ChartBarIcon className="h-5 w-5 text-gray-400 mr-2" />
                    <h3 className="text-lg font-medium">Platform Overview</h3>
                  </div>
                  <Button size="sm" variant="outline">
                    View Analytics
                  </Button>
                </div>
              </CardHeader>
              <CardBody>
                {metricsLoading ? (
                  <div className="flex items-center justify-center py-8">
                    <LoadingSpinner size="md" />
                  </div>
                ) : (
                  <div className="grid grid-cols-3 gap-4">
                    <div className="text-center p-4 bg-blue-50 rounded-lg">
                      <div className="text-2xl font-bold text-blue-600">
                        {adminMetrics?.platform_overview?.total_companies || 0}
                      </div>
                      <div className="text-sm text-blue-700">Total Companies</div>
                      <div className="text-xs text-gray-600 mt-1">Registered</div>
                    </div>
                    <div className="text-center p-4 bg-green-50 rounded-lg">
                      <div className="text-2xl font-bold text-green-600">
                        {adminMetrics?.platform_overview?.active_users || 0}
                      </div>
                      <div className="text-sm text-green-700">Active Users</div>
                      <div className="text-xs text-gray-600 mt-1">Last 30 days</div>
                    </div>
                    <div className="text-center p-4 bg-purple-50 rounded-lg">
                      <div className="text-2xl font-bold text-purple-600">
                        {adminMetrics?.platform_overview?.total_pos || 0}
                      </div>
                      <div className="text-sm text-purple-700">Total Purchase Orders</div>
                      <div className="text-xs text-gray-600 mt-1">All time</div>
                    </div>
                  </div>
                )}
              </CardBody>
            </Card>

            {/* System Health */}
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div className="flex items-center">
                    <ServerIcon className="h-5 w-5 text-gray-400 mr-2" />
                    <h3 className="text-lg font-medium">System Health</h3>
                  </div>
                  <Button size="sm" variant="outline">
                    System Monitor
                  </Button>
                </div>
              </CardHeader>
              <CardBody>
                {metricsLoading ? (
                  <div className="flex items-center justify-center py-8">
                    <LoadingSpinner size="md" />
                  </div>
                ) : (
                  <div className="space-y-4">
                    <div className="grid grid-cols-3 gap-4">
                      <div className="text-center">
                        <div className="text-xl font-bold">
                          <Badge 
                            color={getHealthStatusColor(
                              adminMetrics?.system_health?.uptime_percentage || 0, 
                              'uptime'
                            )}
                            size="lg"
                          >
                            {adminMetrics?.system_health?.uptime_percentage?.toFixed(2) || 0}%
                          </Badge>
                        </div>
                        <div className="text-sm text-gray-600">Uptime</div>
                      </div>
                      <div className="text-center">
                        <div className="text-xl font-bold">
                          <Badge 
                            color={getHealthStatusColor(
                              adminMetrics?.system_health?.api_response_time || 0, 
                              'response_time'
                            )}
                            size="lg"
                          >
                            {adminMetrics?.system_health?.api_response_time || 0}ms
                          </Badge>
                        </div>
                        <div className="text-sm text-gray-600">Response Time</div>
                      </div>
                      <div className="text-center">
                        <div className="text-xl font-bold">
                          <Badge 
                            color={getHealthStatusColor(
                              adminMetrics?.system_health?.error_rate || 0, 
                              'error_rate'
                            )}
                            size="lg"
                          >
                            {adminMetrics?.system_health?.error_rate?.toFixed(2) || 0}%
                          </Badge>
                        </div>
                        <div className="text-sm text-gray-600">Error Rate</div>
                      </div>
                    </div>
                    
                    {/* Health Status Details */}
                    <div className="pt-4 border-t border-gray-200">
                      <div className="space-y-2">
                        <div className="flex justify-between items-center">
                          <span className="text-sm text-gray-600">Database</span>
                          <Badge color="green" size="sm">Healthy</Badge>
                        </div>
                        <div className="flex justify-between items-center">
                          <span className="text-sm text-gray-600">Redis Cache</span>
                          <Badge color="green" size="sm">Healthy</Badge>
                        </div>
                        <div className="flex justify-between items-center">
                          <span className="text-sm text-gray-600">Background Jobs</span>
                          <Badge color="green" size="sm">Running</Badge>
                        </div>
                        <div className="flex justify-between items-center">
                          <span className="text-sm text-gray-600">External APIs</span>
                          <Badge color="yellow" size="sm">Degraded</Badge>
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </CardBody>
            </Card>

            {/* User Activity */}
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div className="flex items-center">
                    <UsersIcon className="h-5 w-5 text-gray-400 mr-2" />
                    <h3 className="text-lg font-medium">User Activity</h3>
                  </div>
                  <Button size="sm" variant="outline">
                    User Analytics
                  </Button>
                </div>
              </CardHeader>
              <CardBody>
                <div className="space-y-3">
                  <div className="flex items-center justify-between p-3 bg-blue-50 rounded-lg">
                    <div>
                      <div className="font-medium">Daily Active Users</div>
                      <div className="text-sm text-gray-600">Users active in last 24 hours</div>
                    </div>
                    <div className="text-right">
                      <div className="text-xl font-bold text-blue-600">1,247</div>
                      <div className="text-xs text-green-600">+5.2%</div>
                    </div>
                  </div>
                  <div className="flex items-center justify-between p-3 bg-green-50 rounded-lg">
                    <div>
                      <div className="font-medium">New Registrations</div>
                      <div className="text-sm text-gray-600">This week</div>
                    </div>
                    <div className="text-right">
                      <div className="text-xl font-bold text-green-600">23</div>
                      <div className="text-xs text-green-600">+12.1%</div>
                    </div>
                  </div>
                </div>
              </CardBody>
            </Card>

            {/* Recent Activity */}
            <Card>
              <CardHeader>
                <div className="flex items-center">
                  <EyeIcon className="h-5 w-5 text-gray-400 mr-2" />
                  <h3 className="text-lg font-medium">Recent Activity</h3>
                </div>
              </CardHeader>
              <CardBody>
                {metricsLoading ? (
                  <div className="flex items-center justify-center py-8">
                    <LoadingSpinner size="md" />
                  </div>
                ) : (
                  <div className="space-y-3">
                    <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                      <div>
                        <div className="font-medium">New Companies</div>
                        <div className="text-sm text-gray-600">
                          Companies registered this week
                        </div>
                      </div>
                      <Badge color="blue">
                        {adminMetrics?.recent_activity?.new_companies || 0}
                      </Badge>
                    </div>
                    <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                      <div>
                        <div className="font-medium">Support Tickets</div>
                        <div className="text-sm text-gray-600">
                          Open support requests
                        </div>
                      </div>
                      <Badge color="yellow">
                        {adminMetrics?.recent_activity?.support_tickets || 0}
                      </Badge>
                    </div>
                  </div>
                )}
              </CardBody>
            </Card>
          </div>

          {/* Right Column - Widgets */}
          <div className="space-y-6">
            {/* Notifications */}
            <NotificationCenterWidget />

            {/* System Alerts */}
            <Card>
              <CardHeader>
                <div className="flex items-center">
                  <ExclamationTriangleIcon className="h-5 w-5 text-gray-400 mr-2" />
                  <h3 className="text-lg font-medium">System Alerts</h3>
                </div>
              </CardHeader>
              <CardBody>
                <div className="space-y-3">
                  <div className="p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
                    <div className="flex items-center">
                      <ExclamationTriangleIcon className="h-4 w-4 text-yellow-600 mr-2" />
                      <div className="text-sm font-medium text-yellow-800">
                        High Memory Usage
                      </div>
                    </div>
                    <div className="text-xs text-yellow-700 mt-1">
                      Server memory at 85% capacity
                    </div>
                  </div>
                  <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
                    <div className="flex items-center">
                      <ClockIcon className="h-4 w-4 text-blue-600 mr-2" />
                      <div className="text-sm font-medium text-blue-800">
                        Scheduled Maintenance
                      </div>
                    </div>
                    <div className="text-xs text-blue-700 mt-1">
                      Database maintenance in 2 hours
                    </div>
                  </div>
                </div>
              </CardBody>
            </Card>

            {/* Quick Actions */}
            <Card>
              <CardHeader>
                <div className="flex items-center">
                  <CogIcon className="h-5 w-5 text-gray-400 mr-2" />
                  <h3 className="text-lg font-medium">Quick Actions</h3>
                </div>
              </CardHeader>
              <CardBody>
                <div className="space-y-2">
                  <Button variant="outline" size="sm" className="w-full justify-start">
                    <UsersIcon className="h-4 w-4 mr-2" />
                    Manage Users
                  </Button>
                  <Button variant="outline" size="sm" className="w-full justify-start">
                    <ServerIcon className="h-4 w-4 mr-2" />
                    System Logs
                  </Button>
                  <Button variant="outline" size="sm" className="w-full justify-start">
                    <ChartBarIcon className="h-4 w-4 mr-2" />
                    Analytics
                  </Button>
                  <Button variant="outline" size="sm" className="w-full justify-start">
                    <CogIcon className="h-4 w-4 mr-2" />
                    Settings
                  </Button>
                </div>
              </CardBody>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PlatformAdminDashboardV2;
