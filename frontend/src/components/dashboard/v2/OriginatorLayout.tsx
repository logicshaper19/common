/**
 * Originator V2 Dashboard Content - Role-specific dashboard content for originator companies
 * Works with main layout system, no duplicate navigation
 */
import React from 'react';
import { useDashboardConfig, useDashboardMetrics } from '../../../hooks/useDashboardConfig';
import LoadingSpinner from '../../ui/LoadingSpinner';
import { Card, CardHeader, CardBody } from '../../ui/Card';
import { Button } from '../../ui/Button';
import { Badge } from '../../ui/Badge';
import { 
  MapIcon,
  ShieldCheckIcon,
  ChartBarIcon,
  DocumentCheckIcon,
  PlusIcon,
  BuildingOfficeIcon,
  ExclamationTriangleIcon,
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

const OriginatorLayout: React.FC = () => {
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
      {/* Page header */}
      <div className="md:flex md:items-center md:justify-between">
        <div className="min-w-0 flex-1">
          <h2 className="text-2xl font-bold leading-7 text-gray-900 sm:truncate sm:text-3xl sm:tracking-tight">
            Originator Dashboard
          </h2>
          <p className="mt-1 text-sm text-gray-500">
            Farm management and certification tracking
          </p>
        </div>
        <div className="mt-4 flex md:ml-4 md:mt-0">
          <Button>
            <PlusIcon className="h-4 w-4 mr-2" />
            Add New Farm
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
                    <MapIcon className="h-8 w-8 text-primary-600" />
                  </div>
                  <div className="ml-5 w-0 flex-1">
                    <dl>
                      <dt className="text-sm font-medium text-gray-500 truncate">
                        Total Farms
                      </dt>
                      <dd className="text-lg font-medium text-gray-900">
                        {originatorMetrics?.farm_management?.total_farms || 0}
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
                    <ShieldCheckIcon className="h-8 w-8 text-green-600" />
                  </div>
                  <div className="ml-5 w-0 flex-1">
                    <dl>
                      <dt className="text-sm font-medium text-gray-500 truncate">
                        EUDR Compliant
                      </dt>
                      <dd className="text-lg font-medium text-gray-900">
                          {originatorMetrics?.farm_management?.eudr_compliant || 0}
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
                    <BuildingOfficeIcon className="h-8 w-8 text-blue-600" />
                  </div>
                  <div className="ml-5 w-0 flex-1">
                    <dl>
                      <dt className="text-sm font-medium text-gray-500 truncate">
                        Recent Harvests
                      </dt>
                      <dd className="text-lg font-medium text-gray-900">
                        {originatorMetrics?.production_tracker?.recent_harvests || 0}
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
                        POs Confirmed
                      </dt>
                      <dd className="text-lg font-medium text-gray-900">
                          {originatorMetrics?.recent_activity?.pos_confirmed || 0}
                      </dd>
                    </dl>
                      </div>
                    </div>
                </CardBody>
              </Card>
            </div>

          {/* Farm Management */}
          <div className="grid grid-cols-1 gap-5 lg:grid-cols-3">
              <Card>
                <CardHeader>
                <h3 className="text-lg font-medium text-gray-900">Production Tracker</h3>
              </CardHeader>
              <CardBody>
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-500">Recent Harvests</span>
                    <Badge variant="primary">
                      {originatorMetrics?.production_tracker?.recent_harvests || 0}
                    </Badge>
                  </div>
                      <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-500">Pending PO Links</span>
                    <Badge variant="warning">
                      {originatorMetrics?.production_tracker?.pending_po_links || 0}
                    </Badge>
                      </div>
                    </div>
              </CardBody>
            </Card>

            <Card>
              <CardHeader>
                <h3 className="text-lg font-medium text-gray-900">Farm Management</h3>
              </CardHeader>
              <CardBody>
                <div className="space-y-4">
                      <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-500">Total Farms</span>
                    <Badge variant="primary">
                      {originatorMetrics?.farm_management?.total_farms || 0}
                    </Badge>
                        </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-500">EUDR Compliant</span>
                    <Badge variant="success">
                      {originatorMetrics?.farm_management?.eudr_compliant || 0}
                    </Badge>
                      </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-500">Certifications Expiring</span>
                    <Badge variant="error">
                      {originatorMetrics?.farm_management?.certifications_expiring || 0}
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
                    <span className="text-sm text-gray-500">Harvests This Week</span>
                    <span className="text-sm font-medium text-gray-900">
                      {originatorMetrics?.recent_activity?.harvests_this_week || 0}
                    </span>
                        </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-500">POs Confirmed</span>
                    <span className="text-sm font-medium text-gray-900">
                      {originatorMetrics?.recent_activity?.pos_confirmed || 0}
                    </span>
                    </div>
                  </div>
                </CardBody>
              </Card>
          </div>

              {/* Quick Actions */}
              <Card>
                <CardHeader>
              <h3 className="text-lg font-medium text-gray-900">Quick Actions</h3>
                </CardHeader>
                <CardBody>
              <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
                <Button variant="outline" className="w-full justify-start">
                      <PlusIcon className="h-4 w-4 mr-2" />
                  Add New Farm
                    </Button>
                <Button variant="outline" className="w-full justify-start">
                  <ShieldCheckIcon className="h-4 w-4 mr-2" />
                  Manage Certifications
                    </Button>
                <Button variant="outline" className="w-full justify-start">
                  <ChartBarIcon className="h-4 w-4 mr-2" />
                  View Farm Analytics
                    </Button>
                <Button variant="outline" className="w-full justify-start">
                  <DocumentCheckIcon className="h-4 w-4 mr-2" />
                  Report Harvest Data
                    </Button>
                  </div>
                </CardBody>
              </Card>
            </div>
      )}
    </div>
  );
};

export default OriginatorLayout;