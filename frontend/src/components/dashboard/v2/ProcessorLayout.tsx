/**
 * Processor V2 Dashboard Content - Role-specific dashboard content for processor companies
 * Works with main layout system, no duplicate navigation
 */
import React from 'react';
import { useDashboardConfig, useDashboardMetrics } from '../../../hooks/useDashboardConfig';
import LoadingSpinner from '../../ui/LoadingSpinner';
import { Card, CardHeader, CardBody } from '../../ui/Card';
import { Button } from '../../ui/Button';
import { Badge } from '../../ui/Badge';
import { 
  CheckCircleIcon,
  ClockIcon,
  ExclamationCircleIcon,
  BeakerIcon,
  PlusIcon,
  ChartBarIcon
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

const ProcessorLayout: React.FC = () => {
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
      {/* Page header */}
      <div className="md:flex md:items-center md:justify-between">
        <div className="min-w-0 flex-1">
          <h2 className="text-2xl font-bold leading-7 text-gray-900 sm:truncate sm:text-3xl sm:tracking-tight">
            Processor Dashboard
          </h2>
          <p className="mt-1 text-sm text-gray-500">
            Production management and order processing
          </p>
        </div>
        <div className="mt-4 flex md:ml-4 md:mt-0">
          <Button>
            <PlusIcon className="h-4 w-4 mr-2" />
            New Batch
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
                    <ClockIcon className="h-8 w-8 text-primary-600" />
                  </div>
                  <div className="ml-5 w-0 flex-1">
                    <dl>
                      <dt className="text-sm font-medium text-gray-500 truncate">
                        Pending Confirmation
                      </dt>
                      <dd className="text-lg font-medium text-gray-900">
                          {processorMetrics?.incoming_pos?.pending_confirmation || 0}
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
                    <ExclamationCircleIcon className="h-8 w-8 text-red-600" />
                        </div>
                  <div className="ml-5 w-0 flex-1">
                    <dl>
                      <dt className="text-sm font-medium text-gray-500 truncate">
                        Urgent Orders
                      </dt>
                      <dd className="text-lg font-medium text-gray-900">
                          {processorMetrics?.incoming_pos?.urgent_orders || 0}
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
                    <BeakerIcon className="h-8 w-8 text-blue-600" />
                  </div>
                  <div className="ml-5 w-0 flex-1">
                    <dl>
                      <dt className="text-sm font-medium text-gray-500 truncate">
                        Active Batches
                      </dt>
                      <dd className="text-lg font-medium text-gray-900">
                          {processorMetrics?.production_overview?.active_batches || 0}
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
                    <ChartBarIcon className="h-8 w-8 text-purple-600" />
                  </div>
                  <div className="ml-5 w-0 flex-1">
                    <dl>
                      <dt className="text-sm font-medium text-gray-500 truncate">
                        Capacity Utilization
                      </dt>
                      <dd className="text-lg font-medium text-gray-900">
                        {processorMetrics?.production_overview?.capacity_utilization || 0}%
                      </dd>
                    </dl>
                      </div>
                    </div>
                </CardBody>
              </Card>
            </div>

          {/* Production Overview */}
          <div className="grid grid-cols-1 gap-5 lg:grid-cols-3">
              <Card>
                <CardHeader>
                <h3 className="text-lg font-medium text-gray-900">Production Overview</h3>
              </CardHeader>
              <CardBody>
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-500">Active Batches</span>
                    <Badge variant="primary">
                      {processorMetrics?.production_overview?.active_batches || 0}
                    </Badge>
                  </div>
                      <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-500">Capacity Utilization</span>
                    <Badge variant="success">
                      {processorMetrics?.production_overview?.capacity_utilization || 0}%
                    </Badge>
                    </div>
                      <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-500">Quality Score</span>
                    <Badge variant="success">
                      {processorMetrics?.production_overview?.quality_score || 0}/100
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
                    <span className="text-sm text-gray-500">Orders Confirmed Today</span>
                    <span className="text-sm font-medium text-gray-900">
                      {processorMetrics?.recent_activity?.orders_confirmed_today || 0}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-500">Batches Completed</span>
                    <span className="text-sm font-medium text-gray-900">
                      {processorMetrics?.recent_activity?.batches_completed || 0}
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
                    New Batch
                  </Button>
                  <Button variant="outline" className="w-full justify-start">
                    <CheckCircleIcon className="h-4 w-4 mr-2" />
                    Confirm Orders
                  </Button>
                  <Button variant="outline" className="w-full justify-start">
                    <ChartBarIcon className="h-4 w-4 mr-2" />
                    Production Analytics
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

export default ProcessorLayout;