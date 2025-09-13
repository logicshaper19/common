/**
 * Trader V2 Dashboard Content - Role-specific dashboard content for trader companies
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
  ExclamationTriangleIcon,
  ArrowTrendingUpIcon,
  DocumentCheckIcon,
  PlusIcon,
  BuildingOfficeIcon
} from '@heroicons/react/24/outline';

interface TradingMetrics {
  total_orders: number;
  active_positions: number;
  profit_margin: number;
  risk_score: number;
}

interface PortfolioRisk {
  overall_risk: number;
  high_risk_positions: number;
  medium_risk_positions: number;
  low_risk_positions: number;
}

interface RecentActivity {
  new_orders_today: number;
  completed_trades: number;
}

interface TraderMetrics {
  trading_metrics: TradingMetrics;
  portfolio_risk: PortfolioRisk;
  recent_activity: RecentActivity;
}

const TraderLayout: React.FC = () => {
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
      {/* Page header */}
      <div className="md:flex md:items-center md:justify-between">
        <div className="min-w-0 flex-1">
          <h2 className="text-2xl font-bold leading-7 text-gray-900 sm:truncate sm:text-3xl sm:tracking-tight">
            Trader Dashboard
          </h2>
          <p className="mt-1 text-sm text-gray-500">
            Trading operations and portfolio management
          </p>
        </div>
        <div className="mt-4 flex md:ml-4 md:mt-0">
          <Button>
            <PlusIcon className="h-4 w-4 mr-2" />
            New Trade
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
                        Total Orders
                      </dt>
                      <dd className="text-lg font-medium text-gray-900">
                        {traderMetrics?.trading_metrics?.total_orders || 0}
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
                    <ArrowTrendingUpIcon className="h-8 w-8 text-green-600" />
                  </div>
                  <div className="ml-5 w-0 flex-1">
                    <dl>
                      <dt className="text-sm font-medium text-gray-500 truncate">
                        Active Positions
                      </dt>
                      <dd className="text-lg font-medium text-gray-900">
                        {traderMetrics?.trading_metrics?.active_positions || 0}
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
                        Profit Margin
                      </dt>
                      <dd className="text-lg font-medium text-gray-900">
                        {traderMetrics?.trading_metrics?.profit_margin || 0}%
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
                    <ExclamationTriangleIcon className={`h-8 w-8 text-${getRiskScoreColor(traderMetrics?.trading_metrics?.risk_score || 0)}-600`} />
                  </div>
                  <div className="ml-5 w-0 flex-1">
                    <dl>
                      <dt className="text-sm font-medium text-gray-500 truncate">
                        Risk Score
                      </dt>
                      <dd className="text-lg font-medium text-gray-900">
                        {traderMetrics?.trading_metrics?.risk_score || 0}/5
                      </dd>
                    </dl>
                      </div>
                    </div>
                </CardBody>
              </Card>
            </div>

          {/* Portfolio Risk */}
          <div className="grid grid-cols-1 gap-5 lg:grid-cols-3">
              <Card>
                <CardHeader>
                <h3 className="text-lg font-medium text-gray-900">Portfolio Risk</h3>
              </CardHeader>
              <CardBody>
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-500">Overall Risk</span>
                    <Badge variant={getRiskScoreColor(traderMetrics?.portfolio_risk?.overall_risk || 0) as any}>
                      {getRiskScoreLabel(traderMetrics?.portfolio_risk?.overall_risk || 0)}
                    </Badge>
                  </div>
                      <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-500">High Risk Positions</span>
                    <Badge variant="error">
                      {traderMetrics?.portfolio_risk?.high_risk_positions || 0}
                    </Badge>
                        </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-500">Medium Risk Positions</span>
                    <Badge variant="warning">
                      {traderMetrics?.portfolio_risk?.medium_risk_positions || 0}
                    </Badge>
                      </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-500">Low Risk Positions</span>
                    <Badge variant="success">
                      {traderMetrics?.portfolio_risk?.low_risk_positions || 0}
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
                    <span className="text-sm text-gray-500">New Orders Today</span>
                    <span className="text-sm font-medium text-gray-900">
                      {traderMetrics?.recent_activity?.new_orders_today || 0}
                    </span>
                        </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-500">Completed Trades</span>
                    <span className="text-sm font-medium text-gray-900">
                      {traderMetrics?.recent_activity?.completed_trades || 0}
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
                      New Trade
                    </Button>
                  <Button variant="outline" className="w-full justify-start">
                      <ExclamationTriangleIcon className="h-4 w-4 mr-2" />
                      Risk Analysis
                    </Button>
                  <Button variant="outline" className="w-full justify-start">
                      <ChartBarIcon className="h-4 w-4 mr-2" />
                    Portfolio View
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

export default TraderLayout;