/**
 * Brand V2 Dashboard Content - Role-specific dashboard content for brand companies
 * Works with main layout system, no duplicate navigation
 */
import React from 'react';
import { useDashboardConfig, useDashboardMetrics } from '../../../hooks/useDashboardConfig';
import LoadingSpinner from '../../ui/LoadingSpinner';
import { Card, CardHeader, CardBody } from '../../ui/Card';
import { Button } from '../../ui/Button';
import { Badge } from '../../ui/Badge';
import { 
  ChartBarIcon,
  BuildingOfficeIcon,
  TruckIcon,
  DocumentCheckIcon,
  PlusIcon
} from '@heroicons/react/24/outline';

interface SupplyChainMetrics {
  total_pos: number;
  traced_to_mill: number;
  traced_to_farm: number;
  transparency_percentage: number;
}

interface SupplierPortfolio {
  active_suppliers: number;
  pending_onboarding: number;
  risk_alerts: number;
}

interface RecentActivity {
  new_pos_this_week: number;
  confirmations_pending: number;
}

interface BrandMetrics {
  supply_chain_overview: SupplyChainMetrics;
  supplier_portfolio: SupplierPortfolio;
  recent_activity: RecentActivity;
}

const BrandLayout: React.FC = () => {
  const { config, loading: configLoading } = useDashboardConfig();
  const { metrics, loading: metricsLoading } = useDashboardMetrics('brand');

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

  const brandMetrics = metrics as BrandMetrics;

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div className="md:flex md:items-center md:justify-between">
        <div className="min-w-0 flex-1">
          <h2 className="text-2xl font-bold leading-7 text-gray-900 sm:truncate sm:text-3xl sm:tracking-tight">
            Brand Dashboard
          </h2>
          <p className="mt-1 text-sm text-gray-500">
            Supply chain transparency and supplier management
          </p>
        </div>
        <div className="mt-4 flex md:ml-4 md:mt-0">
          <Button>
            <PlusIcon className="h-4 w-4 mr-2" />
            New Purchase Order
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
                    <DocumentCheckIcon className="h-8 w-8 text-primary-600" />
                  </div>
                  <div className="ml-5 w-0 flex-1">
                    <dl>
                      <dt className="text-sm font-medium text-gray-500 truncate">
                        Total Purchase Orders
                      </dt>
                      <dd className="text-lg font-medium text-gray-900">
                        {brandMetrics?.supply_chain_overview?.total_pos || 0}
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
                    <TruckIcon className="h-8 w-8 text-green-600" />
                  </div>
                  <div className="ml-5 w-0 flex-1">
                    <dl>
                      <dt className="text-sm font-medium text-gray-500 truncate">
                        Traced to Mill
                      </dt>
                      <dd className="text-lg font-medium text-gray-900">
                        {brandMetrics?.supply_chain_overview?.traced_to_mill || 0}
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
                        Traced to Farm
                      </dt>
                      <dd className="text-lg font-medium text-gray-900">
                        {brandMetrics?.supply_chain_overview?.traced_to_farm || 0}
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
                        Transparency %
                      </dt>
                      <dd className="text-lg font-medium text-gray-900">
                        {brandMetrics?.supply_chain_overview?.transparency_percentage || 0}%
                      </dd>
                    </dl>
                  </div>
                </div>
              </CardBody>
            </Card>
          </div>

          {/* Supplier Portfolio */}
          <div className="grid grid-cols-1 gap-5 lg:grid-cols-3">
            <Card>
              <CardHeader>
                <h3 className="text-lg font-medium text-gray-900">Supplier Portfolio</h3>
              </CardHeader>
              <CardBody>
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-500">Active Suppliers</span>
                    <Badge variant="success">
                      {brandMetrics?.supplier_portfolio?.active_suppliers || 0}
                    </Badge>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-500">Pending Onboarding</span>
                    <Badge variant="warning">
                      {brandMetrics?.supplier_portfolio?.pending_onboarding || 0}
                    </Badge>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-500">Risk Alerts</span>
                    <Badge variant="error">
                      {brandMetrics?.supplier_portfolio?.risk_alerts || 0}
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
                    <span className="text-sm text-gray-500">New POs This Week</span>
                    <span className="text-sm font-medium text-gray-900">
                      {brandMetrics?.recent_activity?.new_pos_this_week || 0}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-500">Confirmations Pending</span>
                    <span className="text-sm font-medium text-gray-900">
                      {brandMetrics?.recent_activity?.confirmations_pending || 0}
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
                    Create Purchase Order
                  </Button>
                  <Button variant="outline" className="w-full justify-start">
                    <BuildingOfficeIcon className="h-4 w-4 mr-2" />
                    Manage Suppliers
                  </Button>
                  <Button variant="outline" className="w-full justify-start">
                    <ChartBarIcon className="h-4 w-4 mr-2" />
                    View Analytics
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

export default BrandLayout;