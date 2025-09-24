/**
 * Brand Dashboard V2 - Role-specific dashboard for brand companies
 * Focuses on supply chain transparency, supplier management, and compliance
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
import { AnalyticsCard, AnalyticsGrid, MetricComparisonCard } from '../shared/AnalyticsCard';
import {
  ChartBarIcon,
  TruckIcon,
  ShieldCheckIcon,
  ExclamationTriangleIcon,
  PlusIcon,
  EyeIcon,
  UsersIcon,
  DocumentCheckIcon,
  BuildingOfficeIcon
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

export const BrandDashboardV2: React.FC = () => {
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
      {/* Header */}
      <div className="bg-white shadow-sm border-b border-gray-200">
        <div className="px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Brand Dashboard</h1>
              <p className="text-gray-600">
                Monitor your supply chain transparency and manage suppliers
              </p>
            </div>
            <div className="flex space-x-3">
              <Button variant="outline">
                <EyeIcon className="h-4 w-4 mr-2" />
                View Supply Chain
              </Button>
              <Button>
                <PlusIcon className="h-4 w-4 mr-2" />
                Create Purchase Order
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
            {/* Supply Chain Overview - Enhanced Analytics */}
            <div>
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-medium text-gray-900">Supply Chain Overview</h3>
                <Button size="sm" variant="outline">
                  <EyeIcon className="h-4 w-4 mr-2" />
                  View Details
                </Button>
              </div>
              <AnalyticsGrid columns={4}>
                <AnalyticsCard
                  title="Total Purchase Orders"
                  value={brandMetrics?.supply_chain_overview?.total_pos || 0}
                  icon={DocumentCheckIcon}
                  color="blue"
                  trend={{
                    value: 12.5,
                    label: 'vs last month',
                    direction: 'up'
                  }}
                  actionLabel="View Orders"
                  onAction={() => console.log('Navigate to POs')}
                  loading={metricsLoading}
                />
                <AnalyticsCard
                  title="Traced to Mill"
                  value={brandMetrics?.supply_chain_overview?.traced_to_mill || 0}
                  subtitle="Supply chain visibility"
                  icon={BuildingOfficeIcon}
                  color="green"
                  trend={{
                    value: 8.3,
                    label: 'improvement',
                    direction: 'up'
                  }}
                  loading={metricsLoading}
                />
                <AnalyticsCard
                  title="Traced to Farm"
                  value={brandMetrics?.supply_chain_overview?.traced_to_farm || 0}
                  subtitle="Full traceability"
                  icon={TruckIcon}
                  color="purple"
                  trend={{
                    value: 15.2,
                    label: 'vs last quarter',
                    direction: 'up'
                  }}
                  loading={metricsLoading}
                />
                <AnalyticsCard
                  title="Transparency Score"
                  value={`${brandMetrics?.supply_chain_overview?.transparency_percentage?.toFixed(1) || 0}%`}
                  subtitle="Overall transparency"
                  icon={ShieldCheckIcon}
                  color={
                    (brandMetrics?.supply_chain_overview?.transparency_percentage || 0) >= 80
                      ? 'green'
                      : (brandMetrics?.supply_chain_overview?.transparency_percentage || 0) >= 60
                        ? 'yellow'
                        : 'red'
                  }
                  trend={{
                    value: 5.7,
                    label: 'this month',
                    direction: 'up'
                  }}
                  actionLabel="Improve Score"
                  onAction={() => console.log('Navigate to transparency')}
                  loading={metricsLoading}
                />
              </AnalyticsGrid>
            </div>

            {/* Supplier Portfolio */}
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div className="flex items-center">
                    <TruckIcon className="h-5 w-5 text-gray-400 mr-2" />
                    <h3 className="text-lg font-medium">Supplier Portfolio</h3>
                  </div>
                  <Button size="sm" variant="outline">
                    Manage Suppliers
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
                        {brandMetrics?.supplier_portfolio?.active_suppliers || 0}
                      </div>
                      <div className="text-sm text-blue-700">Active Suppliers</div>
                    </div>
                    <div className="text-center p-4 bg-yellow-50 rounded-lg">
                      <div className="text-xl font-bold text-yellow-600">
                        {brandMetrics?.supplier_portfolio?.pending_onboarding || 0}
                      </div>
                      <div className="text-sm text-yellow-700">Pending Onboarding</div>
                    </div>
                    <div className="text-center p-4 bg-red-50 rounded-lg">
                      <div className="text-xl font-bold text-red-600">
                        {brandMetrics?.supplier_portfolio?.risk_alerts || 0}
                      </div>
                      <div className="text-sm text-red-700">Risk Alerts</div>
                    </div>
                  </div>
                )}
              </CardBody>
            </Card>

            {/* Recent Activity */}
            <Card>
              <CardHeader>
                <div className="flex items-center">
                  <ShieldCheckIcon className="h-5 w-5 text-gray-400 mr-2" />
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
                        <div className="font-medium">New Purchase Orders This Week</div>
                        <div className="text-sm text-gray-600">
                          {brandMetrics?.recent_activity?.new_pos_this_week || 0} orders created
                        </div>
                      </div>
                      <Badge color="blue">
                        {brandMetrics?.recent_activity?.new_pos_this_week || 0}
                      </Badge>
                    </div>
                    <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                      <div>
                        <div className="font-medium">Pending Confirmations</div>
                        <div className="text-sm text-gray-600">
                          Awaiting supplier confirmation
                        </div>
                      </div>
                      <Badge color="yellow">
                        {brandMetrics?.recent_activity?.confirmations_pending || 0}
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

export default BrandDashboardV2;
