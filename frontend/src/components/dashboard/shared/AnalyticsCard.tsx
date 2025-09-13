/**
 * Enhanced Analytics Card Component
 * Reusable card for displaying metrics with trends and actions
 */
import React from 'react';
import { Card, CardHeader, CardBody } from '../../ui/Card';
import { Button } from '../../ui/Button';

import { 
  ArrowUpIcon, 
  ArrowDownIcon, 
  MinusIcon,
  EyeIcon,
  ChartBarIcon
} from '@heroicons/react/24/outline';

export interface AnalyticsCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  trend?: {
    value: number;
    label: string;
    direction: 'up' | 'down' | 'neutral';
  };
  icon?: React.ComponentType<{ className?: string }>;
  color?: 'blue' | 'green' | 'yellow' | 'red' | 'purple' | 'gray';
  actionLabel?: string;
  onAction?: () => void;
  loading?: boolean;
  className?: string;
}

export const AnalyticsCard: React.FC<AnalyticsCardProps> = ({
  title,
  value,
  subtitle,
  trend,
  icon: Icon = ChartBarIcon,
  color = 'blue',
  actionLabel,
  onAction,
  loading = false,
  className = ''
}) => {
  const getColorClasses = (color: string) => {
    const colorMap: Record<string, { bg: string; text: string; icon: string }> = {
      blue: {
        bg: 'bg-blue-50',
        text: 'text-blue-600',
        icon: 'text-blue-500'
      },
      green: {
        bg: 'bg-green-50',
        text: 'text-green-600',
        icon: 'text-green-500'
      },
      yellow: {
        bg: 'bg-yellow-50',
        text: 'text-yellow-600',
        icon: 'text-yellow-500'
      },
      red: {
        bg: 'bg-red-50',
        text: 'text-red-600',
        icon: 'text-red-500'
      },
      purple: {
        bg: 'bg-purple-50',
        text: 'text-purple-600',
        icon: 'text-purple-500'
      },
      gray: {
        bg: 'bg-gray-50',
        text: 'text-gray-600',
        icon: 'text-gray-500'
      }
    };
    return colorMap[color] || colorMap.blue;
  };

  const getTrendIcon = (direction: string) => {
    switch (direction) {
      case 'up':
        return <ArrowUpIcon className="h-4 w-4 text-green-500" />;
      case 'down':
        return <ArrowDownIcon className="h-4 w-4 text-red-500" />;
      default:
        return <MinusIcon className="h-4 w-4 text-gray-500" />;
    }
  };

  const getTrendColor = (direction: string) => {
    switch (direction) {
      case 'up':
        return 'text-green-600';
      case 'down':
        return 'text-red-600';
      default:
        return 'text-gray-600';
    }
  };

  const colors = getColorClasses(color);

  if (loading) {
    return (
      <Card className={className}>
        <CardBody>
          <div className="animate-pulse">
            <div className="flex items-center justify-between mb-4">
              <div className="h-4 bg-gray-200 rounded w-1/2"></div>
              <div className="h-8 w-8 bg-gray-200 rounded"></div>
            </div>
            <div className="h-8 bg-gray-200 rounded w-1/3 mb-2"></div>
            <div className="h-4 bg-gray-200 rounded w-2/3"></div>
          </div>
        </CardBody>
      </Card>
    );
  }

  return (
    <Card className={className}>
      <CardBody>
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-medium text-gray-600">{title}</h3>
          <div className={`p-2 rounded-lg ${colors.bg}`}>
            <Icon className={`h-5 w-5 ${colors.icon}`} />
          </div>
        </div>
        
        <div className="mb-2">
          <div className={`text-2xl font-bold ${colors.text}`}>
            {typeof value === 'number' ? value.toLocaleString() : value}
          </div>
          {subtitle && (
            <div className="text-sm text-gray-600">{subtitle}</div>
          )}
        </div>

        {trend && (
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-1">
              {getTrendIcon(trend.direction)}
              <span className={`text-sm font-medium ${getTrendColor(trend.direction)}`}>
                {Math.abs(trend.value)}%
              </span>
              <span className="text-sm text-gray-600">{trend.label}</span>
            </div>
          </div>
        )}

        {actionLabel && onAction && (
          <div className="mt-4 pt-4 border-t border-gray-200">
            <Button 
              size="sm" 
              variant="outline" 
              onClick={onAction}
              className="w-full"
            >
              <EyeIcon className="h-4 w-4 mr-2" />
              {actionLabel}
            </Button>
          </div>
        )}
      </CardBody>
    </Card>
  );
};

/**
 * Grid container for analytics cards
 */
interface AnalyticsGridProps {
  children: React.ReactNode;
  columns?: 2 | 3 | 4;
  className?: string;
}

export const AnalyticsGrid: React.FC<AnalyticsGridProps> = ({
  children,
  columns = 3,
  className = ''
}) => {
  const getGridClasses = (cols: number) => {
    switch (cols) {
      case 2:
        return 'grid-cols-1 md:grid-cols-2';
      case 3:
        return 'grid-cols-1 md:grid-cols-2 lg:grid-cols-3';
      case 4:
        return 'grid-cols-1 md:grid-cols-2 lg:grid-cols-4';
      default:
        return 'grid-cols-1 md:grid-cols-2 lg:grid-cols-3';
    }
  };

  return (
    <div className={`grid ${getGridClasses(columns)} gap-4 ${className}`}>
      {children}
    </div>
  );
};

/**
 * Metric comparison card for showing before/after or target vs actual
 */
interface MetricComparisonCardProps {
  title: string;
  current: {
    label: string;
    value: string | number;
    color?: string;
  };
  comparison: {
    label: string;
    value: string | number;
    color?: string;
  };
  icon?: React.ComponentType<{ className?: string }>;
  className?: string;
}

export const MetricComparisonCard: React.FC<MetricComparisonCardProps> = ({
  title,
  current,
  comparison,
  icon: Icon = ChartBarIcon,
  className = ''
}) => {
  return (
    <Card className={className}>
      <CardHeader>
        <div className="flex items-center">
          <Icon className="h-5 w-5 text-gray-400 mr-2" />
          <h3 className="text-lg font-medium">{title}</h3>
        </div>
      </CardHeader>
      <CardBody>
        <div className="grid grid-cols-2 gap-4">
          <div className="text-center">
            <div className={`text-xl font-bold ${current.color || 'text-gray-900'}`}>
              {typeof current.value === 'number' ? current.value.toLocaleString() : current.value}
            </div>
            <div className="text-sm text-gray-600">{current.label}</div>
          </div>
          <div className="text-center">
            <div className={`text-xl font-bold ${comparison.color || 'text-gray-900'}`}>
              {typeof comparison.value === 'number' ? comparison.value.toLocaleString() : comparison.value}
            </div>
            <div className="text-sm text-gray-600">{comparison.label}</div>
          </div>
        </div>
      </CardBody>
    </Card>
  );
};

export default AnalyticsCard;
