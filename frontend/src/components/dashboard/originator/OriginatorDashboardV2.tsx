/**
 * Originator Dashboard V2 - Role-specific dashboard for originator companies
 * Focuses on farm management, harvest tracking, and compliance
 */
import React from 'react';
import { useDashboardConfig, useDashboardMetrics } from '../../../hooks/useDashboardConfig';
import LoadingSpinner from '../../ui/LoadingSpinner';
import { Card, CardHeader, CardBody } from '../../ui/Card';
import { Button } from '../../ui/Button';
import { Badge } from '../../ui/Badge';
import TeamManagementWidget from '../shared/TeamManagementWidget';
import CompanyProfileWidget from '../shared/CompanyProfileWidget';
import NotificationCenterWidget from '../shared/NotificationCenterWidget';
import { 
  MapIcon,
  DocumentCheckIcon,
  ExclamationTriangleIcon,
  PlusIcon,
  EyeIcon,
  CalendarIcon
} from '@heroicons/react/24/outline';

interface ProductionTracker {
  recent_harvests: number;
  pending_po_links: number;
}

interface FarmManagement {
  total_farms: number;
  eudr_compliant: number;
  certifications_expiring: number;
}

interface RecentActivity {
  harvests_this_week: number;
  pos_confirmed: number;
}

interface OriginatorMetrics {
  production_tracker: ProductionTracker;
  farm_management: FarmManagement;
  recent_activity: RecentActivity;
}

export const OriginatorDashboardV2: React.FC = () => {
  const { config, loading: configLoading } = useDashboardConfig();
  const { metrics, loading: metricsLoading } = useDashboardMetrics('originator');

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

  const originatorMetrics = metrics as OriginatorMetrics;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white shadow-sm border-b border-gray-200">
        <div className="px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Originator Dashboard</h1>
              <p className="text-gray-600">
                Manage farms, track harvests, and ensure compliance
              </p>
            </div>
            <div className="flex space-x-3">
              <Button variant="outline">
                <MapIcon className="h-4 w-4 mr-2" />
                View Farms
              </Button>
              <Button>
                <PlusIcon className="h-4 w-4 mr-2" />
                Record Harvest
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
            {/* Production Tracker */}
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div className="flex items-center">
                    <CalendarIcon className="h-5 w-5 text-gray-400 mr-2" />
                    <h3 className="text-lg font-medium">Production Tracker</h3>
                  </div>
                  <Button size="sm" variant="outline">
                    View Production
                  </Button>
                </div>
              </CardHeader>
              <CardBody>
                {metricsLoading ? (
                  <div className="flex items-center justify-center py-8">
                    <LoadingSpinner size="md" />
                  </div>
                ) : (
                  <div className="grid grid-cols-2 gap-4">
                    <div className="text-center p-4 bg-green-50 rounded-lg">
                      <div className="text-2xl font-bold text-green-600">
                        {originatorMetrics?.production_tracker?.recent_harvests || 0}
                      </div>
                      <div className="text-sm text-green-700">Recent Harvests</div>
                      <div className="text-xs text-gray-600 mt-1">Last 30 days</div>
                      <Button size="sm" className="mt-2" variant="outline">
                        View Details
                      </Button>
                    </div>
                    <div className="text-center p-4 bg-yellow-50 rounded-lg">
                      <div className="text-2xl font-bold text-yellow-600">
                        {originatorMetrics?.production_tracker?.pending_po_links || 0}
                      </div>
                      <div className="text-sm text-yellow-700">Pending PO Links</div>
                      <div className="text-xs text-gray-600 mt-1">Awaiting connection</div>
                      <Button size="sm" className="mt-2" variant="outline">
                        Link Orders
                      </Button>
                    </div>
                  </div>
                )}
              </CardBody>
            </Card>

            {/* Farm Management */}
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div className="flex items-center">
                    <MapIcon className="h-5 w-5 text-gray-400 mr-2" />
                    <h3 className="text-lg font-medium">Farm Management</h3>
                  </div>
                  <Button size="sm" variant="outline">
                    Manage Farms
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
                      <div className="text-xl font-bold text-blue-600">
                        {originatorMetrics?.farm_management?.total_farms || 0}
                      </div>
                      <div className="text-sm text-blue-700">Total Farms</div>
                      <Badge color="blue" size="sm" className="mt-1">
                        Active
                      </Badge>
                    </div>
                    <div className="text-center p-4 bg-green-50 rounded-lg">
                      <div className="text-xl font-bold text-green-600">
                        {originatorMetrics?.farm_management?.eudr_compliant || 0}
                      </div>
                      <div className="text-sm text-green-700">EUDR Compliant</div>
                      <Badge color="green" size="sm" className="mt-1">
                        Verified
                      </Badge>
                    </div>
                    <div className="text-center p-4 bg-red-50 rounded-lg">
                      <div className="text-xl font-bold text-red-600">
                        {originatorMetrics?.farm_management?.certifications_expiring || 0}
                      </div>
                      <div className="text-sm text-red-700">Expiring Soon</div>
                      <Badge color="red" size="sm" className="mt-1">
                        Action Needed
                      </Badge>
                    </div>
                  </div>
                )}
              </CardBody>
            </Card>

            {/* Compliance Overview */}
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div className="flex items-center">
                    <DocumentCheckIcon className="h-5 w-5 text-gray-400 mr-2" />
                    <h3 className="text-lg font-medium">Compliance Overview</h3>
                  </div>
                  <Button size="sm" variant="outline">
                    View Reports
                  </Button>
                </div>
              </CardHeader>
              <CardBody>
                <div className="space-y-3">
                  <div className="flex items-center justify-between p-3 bg-green-50 rounded-lg">
                    <div className="flex items-center">
                      <DocumentCheckIcon className="h-5 w-5 text-green-600 mr-2" />
                      <div>
                        <div className="font-medium text-green-900">EUDR Compliance</div>
                        <div className="text-sm text-green-700">
                          {((originatorMetrics?.farm_management?.eudr_compliant || 0) / 
                            Math.max(originatorMetrics?.farm_management?.total_farms || 1, 1) * 100).toFixed(1)}% 
                          of farms compliant
                        </div>
                      </div>
                    </div>
                    <Badge color="green">Compliant</Badge>
                  </div>
                  
                  <div className="flex items-center justify-between p-3 bg-yellow-50 rounded-lg">
                    <div className="flex items-center">
                      <ExclamationTriangleIcon className="h-5 w-5 text-yellow-600 mr-2" />
                      <div>
                        <div className="font-medium text-yellow-900">Certification Renewals</div>
                        <div className="text-sm text-yellow-700">
                          {originatorMetrics?.farm_management?.certifications_expiring || 0} certifications expiring soon
                        </div>
                      </div>
                    </div>
                    <Badge color="yellow">Action Required</Badge>
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
                        <div className="font-medium">Harvests This Week</div>
                        <div className="text-sm text-gray-600">
                          New harvest records added
                        </div>
                      </div>
                      <Badge color="green">
                        {originatorMetrics?.recent_activity?.harvests_this_week || 0}
                      </Badge>
                    </div>
                    <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                      <div>
                        <div className="font-medium">Purchase Orders Confirmed</div>
                        <div className="text-sm text-gray-600">
                          Orders linked to harvests
                        </div>
                      </div>
                      <Badge color="blue">
                        {originatorMetrics?.recent_activity?.pos_confirmed || 0}
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

            {/* Team Management */}
            <TeamManagementWidget
              companyId={config.user_info.id}
              userRole={config.user_info.role}
              canManageTeam={config.can_manage_team}
            />

            {/* Company Profile */}
            <CompanyProfileWidget
              companyId={config.user_info.id}
              canManageSettings={config.can_manage_settings}
            />
          </div>
        </div>
      </div>
    </div>
  );
};

export default OriginatorDashboardV2;
