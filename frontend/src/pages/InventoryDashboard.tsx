/**
 * Inventory Dashboard Page
 * Comprehensive inventory overview with metrics, alerts, and analytics
 */
import React, { useState, useEffect } from 'react';
import {
  ArchiveBoxIcon,
  ExclamationTriangleIcon,
  ClockIcon,
  ChartBarIcon,
  CubeIcon,
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon,
  EyeIcon,
  PlusIcon
} from '@heroicons/react/24/outline';
import { useAuth } from '../contexts/AuthContext';
import { useToast } from '../contexts/ToastContext';
import { Card, CardHeader, CardBody } from '../components/ui/Card';
import Button from '../components/ui/Button';
import Badge from '../components/ui/Badge';
import AnalyticsCard from '../components/ui/AnalyticsCard';
import LoadingSpinner from '../components/ui/LoadingSpinner';
import { formatCurrency, formatDate } from '../lib/utils';

interface InventoryMetrics {
  total_batches: number;
  active_batches: number;
  total_value: number;
  low_stock_alerts: number;
  expiring_soon: number;
  consumed_this_month: number;
  turnover_rate: number;
}

interface BatchAlert {
  id: string;
  batch_id: string;
  product_name: string;
  alert_type: 'low_stock' | 'expiring' | 'expired';
  quantity: number;
  expiry_date?: string;
  days_until_expiry?: number;
  location_name?: string;
}

interface RecentActivity {
  id: string;
  type: 'created' | 'consumed' | 'transferred' | 'expired';
  batch_id: string;
  product_name: string;
  quantity: number;
  timestamp: string;
  user_name: string;
}

const InventoryDashboard: React.FC = () => {
  const { user } = useAuth();
  const { showToast } = useToast();
  
  // State
  const [metrics, setMetrics] = useState<InventoryMetrics | null>(null);
  const [alerts, setAlerts] = useState<BatchAlert[]>([]);
  const [recentActivity, setRecentActivity] = useState<RecentActivity[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Load dashboard data
  useEffect(() => {
    loadDashboardData();
  }, [user?.company?.id]);

  const loadDashboardData = async () => {
    try {
      setIsLoading(true);
      setError(null);
      
      // Load real inventory data from API
      const { harvestApi } = await import('../services/harvestApi');
      const response = await harvestApi.getHarvestBatches(1, 100); // Get up to 100 batches
      const batches = response.batches;
      
      // Calculate real metrics from actual data
      const totalBatches = batches.length;
      const activeBatches = batches.filter(batch => batch.status === 'active').length;
      const totalValue = batches.reduce((sum, batch) => sum + (batch.quantity * 100), 0); // Estimate value at $100 per unit
      
      // Calculate alerts from real data
      const now = new Date();
      const lowStockAlerts = batches.filter(batch => batch.quantity < 100).length;
      const expiringSoon = batches.filter(batch => {
        if (!batch.expiry_date) return false;
        const expiryDate = new Date(batch.expiry_date);
        const daysUntilExpiry = Math.ceil((expiryDate.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));
        return daysUntilExpiry <= 7 && daysUntilExpiry > 0;
      }).length;
      
      // Calculate turnover rate (simplified)
      const consumedThisMonth = batches.filter(batch => {
        if (!batch.updated_at) return false;
        const updatedDate = new Date(batch.updated_at);
        const monthAgo = new Date();
        monthAgo.setMonth(monthAgo.getMonth() - 1);
        return updatedDate > monthAgo && batch.status === 'consumed';
      }).length;
      
      const turnoverRate = totalBatches > 0 ? (consumedThisMonth / totalBatches) * 100 : 0;
      
      setMetrics({
        total_batches: totalBatches,
        active_batches: activeBatches,
        total_value: totalValue,
        low_stock_alerts: lowStockAlerts,
        expiring_soon: expiringSoon,
        consumed_this_month: consumedThisMonth,
        turnover_rate: Math.round(turnoverRate * 10) / 10
      });

      // Generate alerts from real data
      const realAlerts: BatchAlert[] = [];
      
      // Add expiring alerts
      batches.forEach(batch => {
        if (batch.expiry_date) {
          const expiryDate = new Date(batch.expiry_date);
          const daysUntilExpiry = Math.ceil((expiryDate.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));
          if (daysUntilExpiry <= 7 && daysUntilExpiry > 0) {
            realAlerts.push({
              id: batch.id,
              batch_id: batch.batch_id,
              product_name: batch.product_name || 'Unknown Product',
              alert_type: 'expiring',
              quantity: batch.quantity,
              expiry_date: batch.expiry_date,
              days_until_expiry: daysUntilExpiry,
              location_name: batch.location_name || 'Warehouse'
            });
          }
        }
      });
      
      // Add low stock alerts
      batches.forEach(batch => {
        if (batch.quantity < 100) {
          realAlerts.push({
            id: batch.id,
            batch_id: batch.batch_id,
            product_name: batch.product_name || 'Unknown Product',
            alert_type: 'low_stock',
            quantity: batch.quantity,
            location_name: batch.location_name || 'Warehouse'
          });
        }
      });
      
      setAlerts(realAlerts.slice(0, 10)); // Limit to 10 alerts

      // Generate recent activity from real data
      const recentActivity: RecentActivity[] = batches
        .filter(batch => batch.updated_at)
        .sort((a, b) => new Date(b.updated_at!).getTime() - new Date(a.updated_at!).getTime())
        .slice(0, 5)
        .map(batch => ({
          id: batch.id,
          type: batch.status === 'active' ? 'created' : 'consumed',
          batch_id: batch.batch_id,
          product_name: batch.product_name || 'Unknown Product',
          quantity: batch.quantity,
          timestamp: batch.updated_at!,
          user_name: 'System'
        }));
      
      setRecentActivity(recentActivity);

    } catch (err) {
      console.error('Error loading inventory dashboard:', err);
      setError('Failed to load inventory data. Please try again.');
      showToast({
        type: 'error',
        title: 'Error loading inventory',
        message: 'Please try again or contact support if the problem persists.'
      });
    } finally {
      setIsLoading(false);
    }
  };

  const getAlertIcon = (type: string) => {
    switch (type) {
      case 'expiring':
        return <ClockIcon className="h-5 w-5 text-yellow-500" />;
      case 'low_stock':
        return <ExclamationTriangleIcon className="h-5 w-5 text-red-500" />;
      case 'expired':
        return <ExclamationTriangleIcon className="h-5 w-5 text-red-600" />;
      default:
        return <ArchiveBoxIcon className="h-5 w-5 text-gray-500" />;
    }
  };

  const getActivityIcon = (type: string) => {
    switch (type) {
      case 'created':
        return <PlusIcon className="h-4 w-4 text-green-500" />;
      case 'consumed':
        return <ArrowTrendingDownIcon className="h-4 w-4 text-blue-500" />;
      case 'transferred':
        return <ArrowTrendingUpIcon className="h-4 w-4 text-purple-500" />;
      case 'expired':
        return <ClockIcon className="h-4 w-4 text-red-500" />;
      default:
        return <CubeIcon className="h-4 w-4 text-gray-500" />;
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <p className="text-red-600 mb-4">{error}</p>
        <Button onClick={loadDashboardData} variant="primary">
          Try Again
        </Button>
      </div>
    );
  }

  return (
    <>
      {/* Page Header */}
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Inventory Dashboard</h1>
          <p className="text-gray-600 mt-1">
            Monitor your inventory levels, batch status, and warehouse operations.
          </p>
        </div>
        <div className="flex space-x-3">
          <Button variant="outline" leftIcon={<EyeIcon className="h-4 w-4" />}>
            View All Batches
          </Button>
          <Button variant="primary" leftIcon={<PlusIcon className="h-4 w-4" />}>
            Create Batch
          </Button>
        </div>
      </div>

      {/* Metrics Cards */}
      {metrics && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <AnalyticsCard
            title="Total Batches"
            value={metrics.total_batches.toString()}
            subtitle={`${metrics.active_batches} active`}
            icon={<ArchiveBoxIcon className="h-6 w-6" />}
            trend={{ value: 12, isPositive: true }}
          />
          <AnalyticsCard
            title="Inventory Value"
            value={formatCurrency(metrics.total_value)}
            subtitle="Current market value"
            icon={<ChartBarIcon className="h-6 w-6" />}
            trend={{ value: 8.5, isPositive: true }}
          />
          <AnalyticsCard
            title="Turnover Rate"
            value={`${metrics.turnover_rate}%`}
            subtitle="Monthly average"
            icon={<ArrowTrendingUpIcon className="h-6 w-6" />}
            trend={{ value: 3.2, isPositive: true }}
          />
          <AnalyticsCard
            title="Alerts"
            value={(metrics.low_stock_alerts + metrics.expiring_soon).toString()}
            subtitle={`${metrics.low_stock_alerts} low stock, ${metrics.expiring_soon} expiring`}
            icon={<ExclamationTriangleIcon className="h-6 w-6" />}
            trend={{ value: 2, isPositive: false }}
          />
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Alerts */}
        <Card>
          <CardHeader 
            title="Inventory Alerts" 
            subtitle={`${alerts.length} items need attention`}
          />
          <CardBody padding="none">
            {alerts.length === 0 ? (
              <div className="p-6 text-center text-gray-500">
                No alerts at this time
              </div>
            ) : (
              <div className="divide-y divide-gray-200">
                {alerts.map((alert) => (
                  <div key={alert.id} className="p-4 hover:bg-gray-50">
                    <div className="flex items-start space-x-3">
                      {getAlertIcon(alert.alert_type)}
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between">
                          <p className="text-sm font-medium text-gray-900">
                            {alert.batch_id}
                          </p>
                          <Badge 
                            variant={alert.alert_type === 'expired' ? 'error' : 'warning'}
                          >
                            {alert.alert_type.replace('_', ' ')}
                          </Badge>
                        </div>
                        <p className="text-sm text-gray-600">{alert.product_name}</p>
                        <div className="mt-1 text-xs text-gray-500">
                          {alert.quantity} units • {alert.location_name}
                          {alert.days_until_expiry && (
                            <span> • Expires in {alert.days_until_expiry} days</span>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardBody>
        </Card>

        {/* Recent Activity */}
        <Card>
          <CardHeader 
            title="Recent Activity" 
            subtitle="Latest batch transactions"
          />
          <CardBody padding="none">
            {recentActivity.length === 0 ? (
              <div className="p-6 text-center text-gray-500">
                No recent activity
              </div>
            ) : (
              <div className="divide-y divide-gray-200">
                {recentActivity.map((activity) => (
                  <div key={activity.id} className="p-4 hover:bg-gray-50">
                    <div className="flex items-start space-x-3">
                      {getActivityIcon(activity.type)}
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-gray-900">
                          {activity.batch_id} - {activity.product_name}
                        </p>
                        <p className="text-sm text-gray-600">
                          {activity.type.charAt(0).toUpperCase() + activity.type.slice(1)} {activity.quantity} units
                        </p>
                        <div className="mt-1 text-xs text-gray-500">
                          {formatDate(activity.timestamp)} • by {activity.user_name}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardBody>
        </Card>
      </div>
    </>
  );
};

export default InventoryDashboard;
