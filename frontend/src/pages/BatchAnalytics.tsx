/**
 * Batch Analytics Page
 * Analytics and insights for batch utilization, turnover, and optimization
 */
import React, { useState, useEffect } from 'react';
import {
  ChartBarIcon,
  ClockIcon,
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon,
  CubeIcon,
  ExclamationTriangleIcon
} from '@heroicons/react/24/outline';
import { useAuth } from '../contexts/AuthContext';
import { useToast } from '../contexts/ToastContext';
import { Card, CardHeader, CardBody } from '../components/ui/Card';
import AnalyticsCard from '../components/ui/AnalyticsCard';
import LoadingSpinner from '../components/ui/LoadingSpinner';
import Button from '../components/ui/Button';
import Select from '../components/ui/Select';

interface BatchAnalyticsData {
  turnover_rate: number;
  average_batch_age: number;
  utilization_rate: number;
  waste_percentage: number;
  total_batches_created: number;
  total_batches_consumed: number;
  expiry_rate: number;
  fifo_compliance: number;
}

interface TurnoverTrend {
  month: string;
  turnover_rate: number;
  batches_created: number;
  batches_consumed: number;
}

interface ProductAnalytics {
  product_name: string;
  total_batches: number;
  average_age: number;
  turnover_rate: number;
  waste_rate: number;
}

const BatchAnalytics: React.FC = () => {
  const { user } = useAuth();
  const { showToast } = useToast();
  
  // State
  const [analytics, setAnalytics] = useState<BatchAnalyticsData | null>(null);
  const [trends, setTrends] = useState<TurnoverTrend[]>([]);
  const [productAnalytics, setProductAnalytics] = useState<ProductAnalytics[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [timeRange, setTimeRange] = useState('30d');

  // Load analytics data
  useEffect(() => {
    loadAnalyticsData();
  }, [user?.company?.id, timeRange]);

  const loadAnalyticsData = async () => {
    try {
      setIsLoading(true);
      setError(null);
      
      // TODO: Replace with actual API calls
      // Simulated data for now
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      setAnalytics({
        turnover_rate: 85.2,
        average_batch_age: 12.5,
        utilization_rate: 92.3,
        waste_percentage: 3.2,
        total_batches_created: 156,
        total_batches_consumed: 142,
        expiry_rate: 2.1,
        fifo_compliance: 94.7
      });

      setTrends([
        { month: 'Dec 2024', turnover_rate: 82.1, batches_created: 45, batches_consumed: 42 },
        { month: 'Jan 2025', turnover_rate: 85.2, batches_created: 52, batches_consumed: 48 },
        { month: 'Feb 2025', turnover_rate: 87.8, batches_created: 48, batches_consumed: 46 }
      ]);

      setProductAnalytics([
        {
          product_name: 'Fresh Fruit Bunches',
          total_batches: 45,
          average_age: 8.2,
          turnover_rate: 92.1,
          waste_rate: 1.8
        },
        {
          product_name: 'Crude Palm Oil',
          total_batches: 32,
          average_age: 15.6,
          turnover_rate: 78.4,
          waste_rate: 4.2
        },
        {
          product_name: 'Refined Palm Oil',
          total_batches: 28,
          average_age: 22.1,
          turnover_rate: 85.7,
          waste_rate: 2.9
        }
      ]);

    } catch (err) {
      console.error('Error loading analytics:', err);
      setError('Failed to load analytics data. Please try again.');
      showToast({
        type: 'error',
        title: 'Error loading analytics',
        message: 'Please try again or contact support if the problem persists.'
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleTimeRangeChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
    setTimeRange(event.target.value);
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
        <Button onClick={loadAnalyticsData} variant="primary">
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
          <h1 className="text-2xl font-bold text-gray-900">Batch Analytics</h1>
          <p className="text-gray-600 mt-1">
            Analyze batch performance, turnover rates, and optimization opportunities.
          </p>
        </div>
        <div className="flex items-center space-x-4">
          <Select
            value={timeRange}
            onChange={handleTimeRangeChange}
            options={[
              { label: 'Last 7 days', value: '7d' },
              { label: 'Last 30 days', value: '30d' },
              { label: 'Last 90 days', value: '90d' },
              { label: 'Last 12 months', value: '12m' }
            ]}
          />
        </div>
      </div>

      {/* Key Metrics */}
      {analytics && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <AnalyticsCard
            title="Turnover Rate"
            value={`${analytics.turnover_rate}%`}
            subtitle="Monthly average"
            icon={<ArrowTrendingUpIcon className="h-6 w-6" />}
            trend={{ value: 3.2, isPositive: true }}
          />
          <AnalyticsCard
            title="Utilization Rate"
            value={`${analytics.utilization_rate}%`}
            subtitle="Inventory efficiency"
            icon={<CubeIcon className="h-6 w-6" />}
            trend={{ value: 1.8, isPositive: true }}
          />
          <AnalyticsCard
            title="Average Batch Age"
            value={`${analytics.average_batch_age} days`}
            subtitle="From production to consumption"
            icon={<ClockIcon className="h-6 w-6" />}
            trend={{ value: 2.1, isPositive: false }}
          />
          <AnalyticsCard
            title="Waste Rate"
            value={`${analytics.waste_percentage}%`}
            subtitle="Expired/recalled batches"
            icon={<ExclamationTriangleIcon className="h-6 w-6" />}
            trend={{ value: 0.8, isPositive: false }}
          />
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
        {/* Batch Flow Metrics */}
        <Card>
          <CardHeader title="Batch Flow" subtitle="Creation vs consumption trends" />
          <CardBody>
            {analytics && (
              <div className="space-y-6">
                <div className="grid grid-cols-2 gap-4">
                  <div className="text-center">
                    <div className="text-2xl font-bold text-green-600">
                      {analytics.total_batches_created}
                    </div>
                    <div className="text-sm text-gray-600">Batches Created</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-blue-600">
                      {analytics.total_batches_consumed}
                    </div>
                    <div className="text-sm text-gray-600">Batches Consumed</div>
                  </div>
                </div>
                
                <div className="space-y-3">
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600">FIFO Compliance</span>
                    <span className="text-sm font-medium">{analytics.fifo_compliance}%</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div 
                      className="bg-green-600 h-2 rounded-full" 
                      style={{ width: `${analytics.fifo_compliance}%` }}
                    ></div>
                  </div>
                </div>

                <div className="space-y-3">
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600">Expiry Rate</span>
                    <span className="text-sm font-medium">{analytics.expiry_rate}%</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div 
                      className="bg-red-500 h-2 rounded-full" 
                      style={{ width: `${analytics.expiry_rate}%` }}
                    ></div>
                  </div>
                </div>
              </div>
            )}
          </CardBody>
        </Card>

        {/* Turnover Trends */}
        <Card>
          <CardHeader title="Turnover Trends" subtitle="Monthly performance" />
          <CardBody>
            <div className="space-y-4">
              {trends.map((trend, index) => (
                <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div>
                    <div className="font-medium text-gray-900">{trend.month}</div>
                    <div className="text-sm text-gray-600">
                      {trend.batches_created} created, {trend.batches_consumed} consumed
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="font-medium text-gray-900">{trend.turnover_rate}%</div>
                    <div className="text-xs text-gray-500">Turnover</div>
                  </div>
                </div>
              ))}
            </div>
          </CardBody>
        </Card>
      </div>

      {/* Product Performance */}
      <Card>
        <CardHeader title="Product Performance" subtitle="Batch analytics by product type" />
        <CardBody padding="none">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Product
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Total Batches
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Avg Age (Days)
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Turnover Rate
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Waste Rate
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {productAnalytics.map((product, index) => (
                  <tr key={index} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-gray-900">
                        {product.product_name}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {product.total_batches}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {product.average_age}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <span className="text-sm text-gray-900 mr-2">
                          {product.turnover_rate}%
                        </span>
                        <div className="w-16 bg-gray-200 rounded-full h-2">
                          <div 
                            className="bg-blue-600 h-2 rounded-full" 
                            style={{ width: `${product.turnover_rate}%` }}
                          ></div>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <span className="text-sm text-gray-900 mr-2">
                          {product.waste_rate}%
                        </span>
                        <div className="w-16 bg-gray-200 rounded-full h-2">
                          <div 
                            className={`h-2 rounded-full ${
                              product.waste_rate > 5 ? 'bg-red-500' : 
                              product.waste_rate > 3 ? 'bg-yellow-500' : 'bg-green-500'
                            }`}
                            style={{ width: `${Math.min(product.waste_rate * 10, 100)}%` }}
                          ></div>
                        </div>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardBody>
      </Card>

      {/* Optimization Recommendations */}
      <Card className="mt-8">
        <CardHeader title="Optimization Recommendations" subtitle="AI-powered insights" />
        <CardBody>
          <div className="space-y-4">
            <div className="flex items-start space-x-3 p-4 bg-blue-50 rounded-lg">
              <ArrowTrendingUpIcon className="h-5 w-5 text-blue-500 mt-0.5" />
              <div>
                <div className="font-medium text-blue-900">Improve FIFO Compliance</div>
                <div className="text-sm text-blue-700">
                  Consider implementing automated batch selection to improve FIFO compliance from 94.7% to 98%+
                </div>
              </div>
            </div>
            
            <div className="flex items-start space-x-3 p-4 bg-yellow-50 rounded-lg">
              <ClockIcon className="h-5 w-5 text-yellow-500 mt-0.5" />
              <div>
                <div className="font-medium text-yellow-900">Reduce Batch Age</div>
                <div className="text-sm text-yellow-700">
                  Crude Palm Oil batches have higher average age (15.6 days). Consider adjusting production schedules.
                </div>
              </div>
            </div>
            
            <div className="flex items-start space-x-3 p-4 bg-green-50 rounded-lg">
              <ChartBarIcon className="h-5 w-5 text-green-500 mt-0.5" />
              <div>
                <div className="font-medium text-green-900">Excellent Utilization</div>
                <div className="text-sm text-green-700">
                  Your 92.3% utilization rate is above industry average. Keep up the good work!
                </div>
              </div>
            </div>
          </div>
        </CardBody>
      </Card>
    </>
  );
};

export default BatchAnalytics;
