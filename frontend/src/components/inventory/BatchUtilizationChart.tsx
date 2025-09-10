/**
 * Batch Utilization Chart Component
 * Visual analytics for batch utilization, turnover, and optimization insights
 */
import React, { useState, useEffect } from 'react';
import {
  ChartBarIcon,
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon,
  ClockIcon,
  ExclamationTriangleIcon
} from '@heroicons/react/24/outline';
import { Card, CardHeader, CardBody } from '../ui/Card';
import Badge from '../ui/Badge';
import LoadingSpinner from '../ui/LoadingSpinner';
import Select from '../ui/Select';

interface UtilizationData {
  period: string;
  utilization_rate: number;
  turnover_rate: number;
  average_age: number;
  waste_rate: number;
  total_batches: number;
  active_batches: number;
}

interface ProductUtilization {
  product_name: string;
  utilization_rate: number;
  turnover_rate: number;
  average_age: number;
  total_value: number;
  trend: 'up' | 'down' | 'stable';
}

interface BatchUtilizationChartProps {
  companyId?: string;
  className?: string;
}

const BatchUtilizationChart: React.FC<BatchUtilizationChartProps> = ({ 
  companyId, 
  className = '' 
}) => {
  // State
  const [utilizationData, setUtilizationData] = useState<UtilizationData[]>([]);
  const [productData, setProductData] = useState<ProductUtilization[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [timeRange, setTimeRange] = useState('30d');
  const [selectedMetric, setSelectedMetric] = useState('utilization_rate');

  // Load utilization data
  useEffect(() => {
    loadUtilizationData();
  }, [companyId, timeRange]);

  const loadUtilizationData = async () => {
    try {
      setIsLoading(true);
      setError(null);
      
      // TODO: Replace with actual API calls
      // Simulated data for now
      await new Promise(resolve => setTimeout(resolve, 800));
      
      setUtilizationData([
        {
          period: 'Week 1',
          utilization_rate: 88.5,
          turnover_rate: 82.1,
          average_age: 14.2,
          waste_rate: 3.8,
          total_batches: 45,
          active_batches: 42
        },
        {
          period: 'Week 2',
          utilization_rate: 91.2,
          turnover_rate: 85.7,
          average_age: 12.8,
          waste_rate: 2.9,
          total_batches: 52,
          active_batches: 48
        },
        {
          period: 'Week 3',
          utilization_rate: 89.8,
          turnover_rate: 87.3,
          average_age: 13.5,
          waste_rate: 3.2,
          total_batches: 48,
          active_batches: 45
        },
        {
          period: 'Week 4',
          utilization_rate: 93.1,
          turnover_rate: 89.6,
          average_age: 11.9,
          waste_rate: 2.1,
          total_batches: 55,
          active_batches: 52
        }
      ]);

      setProductData([
        {
          product_name: 'Fresh Fruit Bunches',
          utilization_rate: 95.2,
          turnover_rate: 92.1,
          average_age: 8.2,
          total_value: 450000,
          trend: 'up'
        },
        {
          product_name: 'Crude Palm Oil',
          utilization_rate: 87.8,
          turnover_rate: 78.4,
          average_age: 15.6,
          total_value: 1200000,
          trend: 'stable'
        },
        {
          product_name: 'Refined Palm Oil',
          utilization_rate: 91.5,
          turnover_rate: 85.7,
          average_age: 22.1,
          total_value: 800000,
          trend: 'up'
        },
        {
          product_name: 'Palm Kernel Oil',
          utilization_rate: 82.3,
          turnover_rate: 74.2,
          average_age: 28.4,
          total_value: 320000,
          trend: 'down'
        }
      ]);

    } catch (err) {
      console.error('Error loading utilization data:', err);
      setError('Failed to load utilization data. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  // Get metric value for chart display
  const getMetricValue = (data: UtilizationData, metric: string): number => {
    switch (metric) {
      case 'utilization_rate':
        return data.utilization_rate;
      case 'turnover_rate':
        return data.turnover_rate;
      case 'average_age':
        return data.average_age;
      case 'waste_rate':
        return data.waste_rate;
      default:
        return data.utilization_rate;
    }
  };

  // Get metric label
  const getMetricLabel = (metric: string): string => {
    switch (metric) {
      case 'utilization_rate':
        return 'Utilization Rate (%)';
      case 'turnover_rate':
        return 'Turnover Rate (%)';
      case 'average_age':
        return 'Average Age (Days)';
      case 'waste_rate':
        return 'Waste Rate (%)';
      default:
        return 'Utilization Rate (%)';
    }
  };

  // Get trend icon
  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case 'up':
        return <ArrowTrendingUpIcon className="h-4 w-4 text-green-500" />;
      case 'down':
        return <ArrowTrendingDownIcon className="h-4 w-4 text-red-500" />;
      default:
        return <ClockIcon className="h-4 w-4 text-gray-500" />;
    }
  };

  // Get utilization color
  const getUtilizationColor = (rate: number): string => {
    if (rate >= 90) return 'bg-green-500';
    if (rate >= 80) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  // Calculate max value for chart scaling
  const maxValue = Math.max(...utilizationData.map(d => getMetricValue(d, selectedMetric)));
  const chartHeight = 200;

  if (isLoading) {
    return (
      <div className={`flex items-center justify-center py-8 ${className}`}>
        <LoadingSpinner size="md" />
      </div>
    );
  }

  if (error) {
    return (
      <div className={`text-center py-8 ${className}`}>
        <p className="text-red-600 mb-4">{error}</p>
      </div>
    );
  }

  return (
    <div className={className}>
      {/* Chart Controls */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-4">
          <Select
            value={selectedMetric}
            onChange={(e) => setSelectedMetric(e.target.value)}
            options={[
              { label: 'Utilization Rate', value: 'utilization_rate' },
              { label: 'Turnover Rate', value: 'turnover_rate' },
              { label: 'Average Age', value: 'average_age' },
              { label: 'Waste Rate', value: 'waste_rate' }
            ]}
          />
        </div>
        <div>
          <Select
            value={timeRange}
            onChange={(e) => setTimeRange(e.target.value)}
            options={[
              { label: 'Last 7 days', value: '7d' },
              { label: 'Last 30 days', value: '30d' },
              { label: 'Last 90 days', value: '90d' }
            ]}
          />
        </div>
      </div>

      {/* Utilization Trend Chart */}
      <Card className="mb-6">
        <CardHeader 
          title={getMetricLabel(selectedMetric)} 
          subtitle="Trend over time"
        />
        <CardBody>
          <div className="relative" style={{ height: chartHeight }}>
            <div className="flex items-end justify-between h-full space-x-2">
              {utilizationData.map((data, index) => {
                const value = getMetricValue(data, selectedMetric);
                const height = (value / maxValue) * (chartHeight - 40);
                
                return (
                  <div key={index} className="flex flex-col items-center flex-1">
                    <div className="flex flex-col items-center justify-end h-full">
                      <div className="text-xs font-medium text-gray-700 mb-1">
                        {value.toFixed(1)}
                        {selectedMetric.includes('rate') ? '%' : selectedMetric === 'average_age' ? 'd' : ''}
                      </div>
                      <div
                        className={`w-full rounded-t ${
                          selectedMetric === 'waste_rate' 
                            ? value > 5 ? 'bg-red-500' : value > 3 ? 'bg-yellow-500' : 'bg-green-500'
                            : getUtilizationColor(value)
                        } transition-all duration-300`}
                        style={{ height: `${height}px`, minHeight: '4px' }}
                      ></div>
                    </div>
                    <div className="text-xs text-gray-500 mt-2 text-center">
                      {data.period}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </CardBody>
      </Card>

      {/* Product Performance */}
      <Card>
        <CardHeader 
          title="Product Performance" 
          subtitle="Utilization by product type"
        />
        <CardBody padding="none">
          <div className="divide-y divide-gray-200">
            {productData.map((product, index) => (
              <div key={index} className="p-4 hover:bg-gray-50">
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <div className="flex items-center justify-between mb-2">
                      <h4 className="font-medium text-gray-900">{product.product_name}</h4>
                      <div className="flex items-center space-x-2">
                        {getTrendIcon(product.trend)}
                        <span className="text-sm font-medium text-gray-900">
                          {product.utilization_rate.toFixed(1)}%
                        </span>
                      </div>
                    </div>
                    
                    <div className="grid grid-cols-3 gap-4 text-sm">
                      <div>
                        <span className="text-gray-500">Turnover:</span>
                        <span className="ml-1 font-medium">{product.turnover_rate.toFixed(1)}%</span>
                      </div>
                      <div>
                        <span className="text-gray-500">Avg Age:</span>
                        <span className="ml-1 font-medium">{product.average_age.toFixed(1)}d</span>
                      </div>
                      <div>
                        <span className="text-gray-500">Value:</span>
                        <span className="ml-1 font-medium">
                          ${(product.total_value / 1000).toFixed(0)}K
                        </span>
                      </div>
                    </div>
                    
                    <div className="mt-3">
                      <div className="flex justify-between text-xs text-gray-500 mb-1">
                        <span>Utilization</span>
                        <span>{product.utilization_rate.toFixed(1)}%</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div 
                          className={`h-2 rounded-full ${getUtilizationColor(product.utilization_rate)}`}
                          style={{ width: `${product.utilization_rate}%` }}
                        ></div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </CardBody>
      </Card>

      {/* Optimization Insights */}
      <Card className="mt-6">
        <CardHeader title="Optimization Insights" subtitle="AI-powered recommendations" />
        <CardBody>
          <div className="space-y-3">
            <div className="flex items-start space-x-3 p-3 bg-green-50 rounded-lg">
              <ArrowTrendingUpIcon className="h-5 w-5 text-green-500 mt-0.5" />
              <div>
                <div className="font-medium text-green-900">Excellent FFB Performance</div>
                <div className="text-sm text-green-700">
                  Fresh Fruit Bunches show 95.2% utilization with fast turnover. Consider increasing capacity.
                </div>
              </div>
            </div>
            
            <div className="flex items-start space-x-3 p-3 bg-yellow-50 rounded-lg">
              <ExclamationTriangleIcon className="h-5 w-5 text-yellow-500 mt-0.5" />
              <div>
                <div className="font-medium text-yellow-900">Palm Kernel Oil Optimization</div>
                <div className="text-sm text-yellow-700">
                  PKO has lower utilization (82.3%) and longer age (28.4d). Review production scheduling.
                </div>
              </div>
            </div>
            
            <div className="flex items-start space-x-3 p-3 bg-blue-50 rounded-lg">
              <ChartBarIcon className="h-5 w-5 text-blue-500 mt-0.5" />
              <div>
                <div className="font-medium text-blue-900">Overall Trend Positive</div>
                <div className="text-sm text-blue-700">
                  Utilization improved 4.6% this month. Waste rate decreased to 2.1%.
                </div>
              </div>
            </div>
          </div>
        </CardBody>
      </Card>
    </div>
  );
};

export default BatchUtilizationChart;
