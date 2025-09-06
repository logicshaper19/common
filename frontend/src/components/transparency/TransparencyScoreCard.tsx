/**
 * Transparency Score Card Component
 * Displays TTM/TTP metrics with visual indicators
 */
import React from 'react';
import {
  ChartBarIcon,
  ClockIcon,
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon
} from '@heroicons/react/24/outline';
import { TransparencyMetrics } from '../../types/transparency';
import { Card, CardHeader, CardBody } from '../ui/Card';
import Badge from '../ui/Badge';
import { cn, getTransparencyColor, formatTransparency } from '../../lib/utils';

interface TransparencyScoreCardProps {
  metrics: TransparencyMetrics;
  showTrend?: boolean;
  previousScore?: number;
  className?: string;
  size?: 'sm' | 'md' | 'lg';
}

const TransparencyScoreCard: React.FC<TransparencyScoreCardProps> = ({
  metrics,
  showTrend = false,
  previousScore,
  className,
  size = 'md',
}) => {
  // Calculate trend if previous score is provided
  const trend = previousScore ? metrics.overall_score - previousScore : 0;
  const trendDirection = trend > 0 ? 'up' : trend < 0 ? 'down' : 'stable';

  // Get score color and status
  const scoreColor = getTransparencyColor(metrics.overall_score);
  const confidenceColor = getTransparencyColor(metrics.confidence_level);

  // Size variants
  const sizeClasses = {
    sm: 'text-sm',
    md: 'text-base',
    lg: 'text-lg',
  };

  const scoreSizeClasses = {
    sm: 'text-2xl',
    md: 'text-3xl',
    lg: 'text-4xl',
  };

  return (
    <Card className={cn('relative overflow-hidden', className)}>
      <CardHeader 
        title="Transparency Score"
        subtitle={`Last updated: ${new Date(metrics.last_updated).toLocaleDateString()}`}
        icon={ChartBarIcon}
      />
      
      <CardBody className="space-y-6">
        {/* Overall Score */}
        <div className="text-center">
          <div className="flex items-center justify-center space-x-2 mb-2">
            <span className={cn(
              'font-bold',
              scoreSizeClasses[size],
              scoreColor
            )}>
              {formatTransparency(metrics.overall_score)}
            </span>
            {showTrend && trend !== 0 && (
              <div className="flex items-center space-x-1">
                {trendDirection === 'up' ? (
                  <ArrowTrendingUpIcon className="h-5 w-5 text-success-600" />
                ) : (
                  <ArrowTrendingDownIcon className="h-5 w-5 text-error-600" />
                )}
                <span className={cn(
                  'text-sm font-medium',
                  trendDirection === 'up' ? 'text-success-600' : 'text-error-600'
                )}>
                  {Math.abs(trend).toFixed(1)}%
                </span>
              </div>
            )}
          </div>
          <p className={cn('text-neutral-600', sizeClasses[size])}>
            Overall Transparency
          </p>
        </div>

        {/* TTM and TTP Scores */}
        <div className="grid grid-cols-2 gap-4">
          <div className="text-center p-3 bg-neutral-50 rounded-lg">
            <div className="flex items-center justify-center space-x-1 mb-1">
              <ClockIcon className="h-4 w-4 text-neutral-500" />
              <span className="text-xs font-medium text-neutral-500 uppercase tracking-wide">
                TTM
              </span>
            </div>
            <div className={cn(
              'text-xl font-bold',
              getTransparencyColor(metrics.ttm_score)
            )}>
              {formatTransparency(metrics.ttm_score)}
            </div>
            <p className="text-xs text-neutral-600">Time to Market</p>
          </div>

          <div className="text-center p-3 bg-neutral-50 rounded-lg">
            <div className="flex items-center justify-center space-x-1 mb-1">
              <ChartBarIcon className="h-4 w-4 text-neutral-500" />
              <span className="text-xs font-medium text-neutral-500 uppercase tracking-wide">
                TTP
              </span>
            </div>
            <div className={cn(
              'text-xl font-bold',
              getTransparencyColor(metrics.ttp_score)
            )}>
              {formatTransparency(metrics.ttp_score)}
            </div>
            <p className="text-xs text-neutral-600">Time to Production</p>
          </div>
        </div>

        {/* Confidence Level */}
        <div className="flex items-center justify-between p-3 bg-neutral-50 rounded-lg">
          <div className="flex items-center space-x-2">
            {metrics.confidence_level >= 80 ? (
              <CheckCircleIcon className="h-5 w-5 text-success-600" />
            ) : (
              <ExclamationTriangleIcon className="h-5 w-5 text-warning-600" />
            )}
            <span className="font-medium text-neutral-900">Confidence Level</span>
          </div>
          <div className="flex items-center space-x-2">
            <span className={cn(
              'font-bold',
              confidenceColor
            )}>
              {formatTransparency(metrics.confidence_level)}
            </span>
            <Badge 
              variant={metrics.confidence_level >= 80 ? 'success' : 'warning'}
              size="sm"
            >
              {metrics.confidence_level >= 80 ? 'High' : 'Medium'}
            </Badge>
          </div>
        </div>

        {/* Traceability Breakdown */}
        <div className="space-y-3">
          <h4 className="font-medium text-neutral-900">Supply Chain Traceability</h4>
          
          {/* Progress bar */}
          <div className="relative">
            <div className="flex mb-2 items-center justify-between">
              <span className="text-sm font-medium text-success-700">
                Traced: {formatTransparency(metrics.traced_percentage)}
              </span>
              <span className="text-sm font-medium text-neutral-500">
                Untraced: {formatTransparency(metrics.untraced_percentage)}
              </span>
            </div>
            <div className="w-full bg-neutral-200 rounded-full h-2">
              <div 
                className="bg-success-600 h-2 rounded-full transition-all duration-300"
                style={{ width: `${metrics.traced_percentage}%` }}
              />
            </div>
          </div>

          {/* Breakdown stats */}
          <div className="grid grid-cols-2 gap-3 text-sm">
            <div className="flex justify-between">
              <span className="text-neutral-600">Traced:</span>
              <span className="font-medium text-success-700">
                {formatTransparency(metrics.traced_percentage)}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-neutral-600">Untraced:</span>
              <span className="font-medium text-neutral-500">
                {formatTransparency(metrics.untraced_percentage)}
              </span>
            </div>
          </div>
        </div>
      </CardBody>
    </Card>
  );
};

export default TransparencyScoreCard;
