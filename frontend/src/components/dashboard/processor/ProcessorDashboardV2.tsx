/**
 * Processor Dashboard V2 - Role-specific dashboard for processor companies
 * Focuses on incoming orders, production management, and batch tracking
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
  CogIcon,
  ClipboardDocumentListIcon,
  BeakerIcon,
  ExclamationCircleIcon,
  CheckCircleIcon,
  ClockIcon
} from '@heroicons/react/24/outline';

interface IncomingPOs {
  pending_confirmation: number;
  urgent_orders: number;
}

interface ProductionOverview {
  active_batches: number;
  capacity_utilization: number;
  quality_score: number;
}

interface RecentActivity {
  orders_confirmed_today: number;
  batches_completed: number;
}

interface ProcessorMetrics {
  incoming_pos: IncomingPOs;
  production_overview: ProductionOverview;
  recent_activity: RecentActivity;
}

export const ProcessorDashboardV2: React.FC = () => {
  const { config, loading: configLoading } = useDashboardConfig();
  const { metrics, loading: metricsLoading } = useDashboardMetrics('processor');

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

  const processorMetrics = metrics as ProcessorMetrics;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white shadow-sm border-b border-gray-200">
        <div className="px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Processor Dashboard</h1>
              <p className="text-gray-600">
                Manage incoming orders, production batches, and quality control
              </p>
            </div>
            <div className="flex space-x-3">
              <Button variant="outline">
                <ClipboardDocumentListIcon className="h-4 w-4 mr-2" />
                View Orders
              </Button>
              <Button>
                <BeakerIcon className="h-4 w-4 mr-2" />
                Create Batch
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
            {/* Incoming Purchase Orders */}
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div className="flex items-center">
                    <ClipboardDocumentListIcon className="h-5 w-5 text-gray-400 mr-2" />
                    <h3 className="text-lg font-medium">Incoming Purchase Orders</h3>
                  </div>
                  <Button size="sm" variant="outline">
                    View All Orders
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
                    <div className="text-center p-4 bg-yellow-50 rounded-lg">
                      <div className="flex items-center justify-center mb-2">
                        <ClockIcon className="h-6 w-6 text-yellow-600" />
                      </div>
                      <div className="text-2xl font-bold text-yellow-600">
                        {processorMetrics?.incoming_pos?.pending_confirmation || 0}
                      </div>
                      <div className="text-sm text-yellow-700">Pending Confirmation</div>
                      <Button size="sm" className="mt-2" variant="outline">
                        Review Orders
                      </Button>
                    </div>
                    <div className="text-center p-4 bg-red-50 rounded-lg">
                      <div className="flex items-center justify-center mb-2">
                        <ExclamationCircleIcon className="h-6 w-6 text-red-600" />
                      </div>
                      <div className="text-2xl font-bold text-red-600">
                        {processorMetrics?.incoming_pos?.urgent_orders || 0}
                      </div>
                      <div className="text-sm text-red-700">Urgent Orders</div>
                      <Button size="sm" className="mt-2" variant="outline">
                        Handle Urgent
                      </Button>
                    </div>
                  </div>
                )}
              </CardBody>
            </Card>

            {/* Production Overview */}
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div className="flex items-center">
                    <CogIcon className="h-5 w-5 text-gray-400 mr-2" />
                    <h3 className="text-lg font-medium">Production Overview</h3>
                  </div>
                  <Button size="sm" variant="outline">
                    Production Dashboard
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
                    <div className="text-center">
                      <div className="text-2xl font-bold text-blue-600">
                        {processorMetrics?.production_overview?.active_batches || 0}
                      </div>
                      <div className="text-sm text-gray-600">Active Batches</div>
                      <div className="mt-2">
                        <Badge color="blue" size="sm">In Production</Badge>
                      </div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-green-600">
                        {processorMetrics?.production_overview?.capacity_utilization?.toFixed(1) || 0}%
                      </div>
                      <div className="text-sm text-gray-600">Capacity Utilization</div>
                      <div className="mt-2">
                        <div className="w-full bg-gray-200 rounded-full h-2">
                          <div 
                            className="bg-green-600 h-2 rounded-full" 
                            style={{ 
                              width: `${processorMetrics?.production_overview?.capacity_utilization || 0}%` 
                            }}
                          ></div>
                        </div>
                      </div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-purple-600">
                        {processorMetrics?.production_overview?.quality_score?.toFixed(1) || 0}
                      </div>
                      <div className="text-sm text-gray-600">Quality Score</div>
                      <div className="mt-2">
                        <Badge 
                          color={
                            (processorMetrics?.production_overview?.quality_score || 0) >= 4.5 
                              ? 'green' 
                              : (processorMetrics?.production_overview?.quality_score || 0) >= 3.5 
                                ? 'yellow' 
                                : 'red'
                          } 
                          size="sm"
                        >
                          {(processorMetrics?.production_overview?.quality_score || 0) >= 4.5 
                            ? 'Excellent' 
                            : (processorMetrics?.production_overview?.quality_score || 0) >= 3.5 
                              ? 'Good' 
                              : 'Needs Attention'
                          }
                        </Badge>
                      </div>
                    </div>
                  </div>
                )}
              </CardBody>
            </Card>

            {/* Recent Activity */}
            <Card>
              <CardHeader>
                <div className="flex items-center">
                  <CheckCircleIcon className="h-5 w-5 text-gray-400 mr-2" />
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
                        <div className="font-medium">Orders Confirmed Today</div>
                        <div className="text-sm text-gray-600">
                          Purchase orders processed and confirmed
                        </div>
                      </div>
                      <Badge color="green">
                        {processorMetrics?.recent_activity?.orders_confirmed_today || 0}
                      </Badge>
                    </div>
                    <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                      <div>
                        <div className="font-medium">Batches Completed</div>
                        <div className="text-sm text-gray-600">
                          Production batches finished this week
                        </div>
                      </div>
                      <Badge color="blue">
                        {processorMetrics?.recent_activity?.batches_completed || 0}
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
              canManageTeam={config.permissions.can_manage_team}
            />

            {/* Company Profile */}
            <CompanyProfileWidget
              companyId={config.user_info.id}
              canManageSettings={config.permissions.can_manage_settings}
            />
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProcessorDashboardV2;
