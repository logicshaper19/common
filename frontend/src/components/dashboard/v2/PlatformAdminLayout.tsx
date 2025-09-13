/**
 * Platform Admin V2 Dashboard Content - Role-specific dashboard content for platform administrators
 * Works with main layout system, no duplicate navigation
 */
import React from 'react';
import { useDashboardConfig, useDashboardMetrics } from '../../../hooks/useDashboardConfig';
import LoadingSpinner from '../../ui/LoadingSpinner';
import { Card, CardHeader, CardBody } from '../../ui/Card';
import { Button } from '../../ui/Button';
import { Badge } from '../../ui/Badge';
import { 
  ServerIcon,
  UserGroupIcon,
  ChartBarIcon,
  ExclamationTriangleIcon,
  ClockIcon,
  PlusIcon,
  BuildingOfficeIcon
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

const PlatformAdminLayout: React.FC = () => {
  const { config, loading: configLoading } = useDashboardConfig();
  const { metrics, loading: metricsLoading } = useDashboardMetrics('platform_admin');

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

  const platformMetrics = metrics as PlatformAdminMetrics;

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div className="md:flex md:items-center md:justify-between">
        <div className="min-w-0 flex-1">
          <h2 className="text-2xl font-bold leading-7 text-gray-900 sm:truncate sm:text-3xl sm:tracking-tight">
            Platform Admin Dashboard
          </h2>
          <p className="mt-1 text-sm text-gray-500">
            Platform management and system monitoring
          </p>
        </div>
        <div className="mt-4 flex md:ml-4 md:mt-0">
          <Button>
            <PlusIcon className="h-4 w-4 mr-2" />
            Add Company
          </Button>
        </div>
      </div>

      {/* Dashboard content */}
      {metricsLoading ? (
        <div className="flex items-center justify-center h-64">
          <LoadingSpinner size="lg" />
          <span className="ml-3 text-gray-600">Loading metrics...</span>
        </div>
      ) : (
        <div className="space-y-6">
          {/* Key Metrics */}
          <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
              <Card>
              <CardBody className="p-6">
                    <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <BuildingOfficeIcon className="h-8 w-8 text-primary-600" />
                  </div>
                  <div className="ml-5 w-0 flex-1">
                    <dl>
                      <dt className="text-sm font-medium text-gray-500 truncate">
                        Total Companies
                      </dt>
                      <dd className="text-lg font-medium text-gray-900">
                        {platformMetrics?.platform_overview?.total_companies || 0}
                      </dd>
                    </dl>
                      </div>
                    </div>
                </CardBody>
              </Card>

              <Card>
              <CardBody className="p-6">
                    <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <UserGroupIcon className="h-8 w-8 text-green-600" />
                  </div>
                  <div className="ml-5 w-0 flex-1">
                    <dl>
                      <dt className="text-sm font-medium text-gray-500 truncate">
                        Active Users
                      </dt>
                      <dd className="text-lg font-medium text-gray-900">
                        {platformMetrics?.platform_overview?.active_users || 0}
                      </dd>
                    </dl>
                      </div>
                    </div>
                </CardBody>
              </Card>

              <Card>
              <CardBody className="p-6">
                    <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <ChartBarIcon className="h-8 w-8 text-blue-600" />
                  </div>
                  <div className="ml-5 w-0 flex-1">
                    <dl>
                      <dt className="text-sm font-medium text-gray-500 truncate">
                        Total Purchase Orders
                      </dt>
                      <dd className="text-lg font-medium text-gray-900">
                        {platformMetrics?.platform_overview?.total_pos || 0}
                      </dd>
                    </dl>
                    </div>
                  </div>
                </CardBody>
              </Card>

              <Card>
              <CardBody className="p-6">
                  <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <ServerIcon className="h-8 w-8 text-purple-600" />
                  </div>
                  <div className="ml-5 w-0 flex-1">
                    <dl>
                      <dt className="text-sm font-medium text-gray-500 truncate">
                        System Uptime
                      </dt>
                      <dd className="text-lg font-medium text-gray-900">
                        {platformMetrics?.system_health?.uptime_percentage || 0}%
                      </dd>
                    </dl>
                      </div>
                    </div>
                </CardBody>
              </Card>
            </div>

          {/* System Health */}
          <div className="grid grid-cols-1 gap-5 lg:grid-cols-3">
              <Card>
                <CardHeader>
                <h3 className="text-lg font-medium text-gray-900">System Health</h3>
              </CardHeader>
              <CardBody>
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-500">API Response Time</span>
                    <Badge variant="success">
                      {platformMetrics?.system_health?.api_response_time || 0}ms
                    </Badge>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-500">Error Rate</span>
                    <Badge variant={platformMetrics?.system_health?.error_rate > 5 ? "error" : "success"}>
                      {platformMetrics?.system_health?.error_rate || 0}%
                    </Badge>
                        </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-500">Uptime</span>
                    <Badge variant="success">
                      {platformMetrics?.system_health?.uptime_percentage || 0}%
                    </Badge>
                    </div>
                  </div>
                </CardBody>
              </Card>

              <Card>
                <CardHeader>
                <h3 className="text-lg font-medium text-gray-900">Recent Activity</h3>
                </CardHeader>
                <CardBody>
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-500">New Companies</span>
                    <span className="text-sm font-medium text-gray-900">
                      {platformMetrics?.recent_activity?.new_companies || 0}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-500">Support Tickets</span>
                    <span className="text-sm font-medium text-gray-900">
                      {platformMetrics?.recent_activity?.support_tickets || 0}
                    </span>
                  </div>
                  </div>
                </CardBody>
              </Card>

              <Card>
                <CardHeader>
                <h3 className="text-lg font-medium text-gray-900">Quick Actions</h3>
                </CardHeader>
                <CardBody>
                  <div className="space-y-3">
                  <Button variant="outline" className="w-full justify-start">
                    <PlusIcon className="h-4 w-4 mr-2" />
                    Add Company
                  </Button>
                  <Button variant="outline" className="w-full justify-start">
                    <ExclamationTriangleIcon className="h-4 w-4 mr-2" />
                    System Monitor
                  </Button>
                  <Button variant="outline" className="w-full justify-start">
                    <ChartBarIcon className="h-4 w-4 mr-2" />
                    Platform Analytics
                  </Button>
                  </div>
                </CardBody>
              </Card>
            </div>
          </div>
      )}
    </div>
  );
};

export default PlatformAdminLayout;