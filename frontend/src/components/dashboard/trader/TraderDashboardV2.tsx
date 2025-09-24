/**
 * Trader Dashboard V2 - Role-specific dashboard for trader companies
 * Focuses on order book management, risk analysis, and margin tracking
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
  ChartBarIcon,
  ExclamationTriangleIcon,
  CurrencyDollarIcon,
  ArrowTrendingUpIcon,
  PlusIcon,
  EyeIcon
} from '@heroicons/react/24/outline';

interface OrderBook {
  incoming_orders: number;
  outgoing_orders: number;
  unfulfilled_orders: number;
}

interface PortfolioRisk {
  total_exposure: number;
  margin_at_risk: number;
  risk_score: number;
}

interface RecentActivity {
  orders_fulfilled: number;
  new_opportunities: number;
}

interface TraderMetrics {
  order_book: OrderBook;
  portfolio_risk: PortfolioRisk;
  recent_activity: RecentActivity;
}

export const TraderDashboardV2: React.FC = () => {
  const { config, loading: configLoading } = useDashboardConfig();
  const { metrics, loading: metricsLoading } = useDashboardMetrics('trader');

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

  const traderMetrics = metrics as TraderMetrics;

  const getRiskScoreColor = (score: number) => {
    if (score >= 4) return 'red';
    if (score >= 3) return 'yellow';
    if (score >= 2) return 'blue';
    return 'green';
  };

  const getRiskScoreLabel = (score: number) => {
    if (score >= 4) return 'High Risk';
    if (score >= 3) return 'Medium Risk';
    if (score >= 2) return 'Low Risk';
    return 'Minimal Risk';
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white shadow-sm border-b border-gray-200">
        <div className="px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Trader Dashboard</h1>
              <p className="text-gray-600">
                Manage order book, monitor risk, and track trading opportunities
              </p>
            </div>
            <div className="flex space-x-3">
              <Button variant="outline">
                <ChartBarIcon className="h-4 w-4 mr-2" />
                Risk Analysis
              </Button>
              <Button>
                <PlusIcon className="h-4 w-4 mr-2" />
                New Trade
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
            {/* Order Book */}
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div className="flex items-center">
                    <ChartBarIcon className="h-5 w-5 text-gray-400 mr-2" />
                    <h3 className="text-lg font-medium">Order Book</h3>
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
                  <div className="grid grid-cols-3 gap-4">
                    <div className="text-center p-4 bg-blue-50 rounded-lg">
                      <div className="text-2xl font-bold text-blue-600">
                        {traderMetrics?.order_book?.incoming_orders || 0}
                      </div>
                      <div className="text-sm text-blue-700">Incoming Orders</div>
                      <div className="text-xs text-gray-600 mt-1">Buy orders</div>
                    </div>
                    <div className="text-center p-4 bg-green-50 rounded-lg">
                      <div className="text-2xl font-bold text-green-600">
                        {traderMetrics?.order_book?.outgoing_orders || 0}
                      </div>
                      <div className="text-sm text-green-700">Outgoing Orders</div>
                      <div className="text-xs text-gray-600 mt-1">Sell orders</div>
                    </div>
                    <div className="text-center p-4 bg-yellow-50 rounded-lg">
                      <div className="text-2xl font-bold text-yellow-600">
                        {traderMetrics?.order_book?.unfulfilled_orders || 0}
                      </div>
                      <div className="text-sm text-yellow-700">Unfulfilled</div>
                      <div className="text-xs text-gray-600 mt-1">Pending</div>
                    </div>
                  </div>
                )}
              </CardBody>
            </Card>

            {/* Portfolio Risk */}
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div className="flex items-center">
                    <ExclamationTriangleIcon className="h-5 w-5 text-gray-400 mr-2" />
                    <h3 className="text-lg font-medium">Portfolio Risk</h3>
                  </div>
                  <Button size="sm" variant="outline">
                    Risk Dashboard
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
                        <div className="text-xl font-bold text-gray-900">
                          ${(traderMetrics?.portfolio_risk?.total_exposure || 0).toLocaleString()}
                        </div>
                        <div className="text-sm text-gray-600">Total Exposure</div>
                      </div>
                      <div className="text-center">
                        <div className="text-xl font-bold text-orange-600">
                          ${(traderMetrics?.portfolio_risk?.margin_at_risk || 0).toLocaleString()}
                        </div>
                        <div className="text-sm text-gray-600">Margin at Risk</div>
                      </div>
                      <div className="text-center">
                        <div className="text-xl font-bold">
                          <Badge 
                            color={getRiskScoreColor(traderMetrics?.portfolio_risk?.risk_score || 0)}
                            size="lg"
                          >
                            {traderMetrics?.portfolio_risk?.risk_score?.toFixed(1) || 0}
                          </Badge>
                        </div>
                        <div className="text-sm text-gray-600">Risk Score</div>
                        <div className="text-xs text-gray-500 mt-1">
                          {getRiskScoreLabel(traderMetrics?.portfolio_risk?.risk_score || 0)}
                        </div>
                      </div>
                    </div>
                    
                    {/* Risk Breakdown */}
                    <div className="pt-4 border-t border-gray-200">
                      <div className="space-y-2">
                        <div className="flex justify-between items-center">
                          <span className="text-sm text-gray-600">Market Risk</span>
                          <Badge color="yellow" size="sm">Medium</Badge>
                        </div>
                        <div className="flex justify-between items-center">
                          <span className="text-sm text-gray-600">Credit Risk</span>
                          <Badge color="green" size="sm">Low</Badge>
                        </div>
                        <div className="flex justify-between items-center">
                          <span className="text-sm text-gray-600">Operational Risk</span>
                          <Badge color="green" size="sm">Low</Badge>
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </CardBody>
            </Card>

            {/* Trading Performance */}
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div className="flex items-center">
                    <ArrowTrendingUpIcon className="h-5 w-5 text-gray-400 mr-2" />
                    <h3 className="text-lg font-medium">Trading Performance</h3>
                  </div>
                  <Button size="sm" variant="outline">
                    View Analytics
                  </Button>
                </div>
              </CardHeader>
              <CardBody>
                <div className="grid grid-cols-2 gap-4">
                  <div className="text-center p-4 bg-green-50 rounded-lg">
                    <div className="flex items-center justify-center mb-2">
                      <CurrencyDollarIcon className="h-6 w-6 text-green-600" />
                    </div>
                    <div className="text-xl font-bold text-green-600">
                      +12.5%
                    </div>
                    <div className="text-sm text-green-700">Monthly Return</div>
                    <div className="text-xs text-gray-600 mt-1">vs last month</div>
                  </div>
                  <div className="text-center p-4 bg-blue-50 rounded-lg">
                    <div className="flex items-center justify-center mb-2">
                      <ArrowTrendingUpIcon className="h-6 w-6 text-blue-600" />
                    </div>
                    <div className="text-xl font-bold text-blue-600">
                      87.3%
                    </div>
                    <div className="text-sm text-blue-700">Success Rate</div>
                    <div className="text-xs text-gray-600 mt-1">profitable trades</div>
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
                        <div className="font-medium">Orders Fulfilled</div>
                        <div className="text-sm text-gray-600">
                          Successfully completed trades
                        </div>
                      </div>
                      <Badge color="green">
                        {traderMetrics?.recent_activity?.orders_fulfilled || 0}
                      </Badge>
                    </div>
                    <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                      <div>
                        <div className="font-medium">New Opportunities</div>
                        <div className="text-sm text-gray-600">
                          Potential trading opportunities identified
                        </div>
                      </div>
                      <Badge color="blue">
                        {traderMetrics?.recent_activity?.new_opportunities || 0}
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

export default TraderDashboardV2;
