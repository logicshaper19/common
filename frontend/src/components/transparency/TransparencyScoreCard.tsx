/**
 * Transparency Score Card Component
 * Displays deterministic transparency percentages with visual indicators
 *
 * SINGLE SOURCE OF TRUTH: All metrics are calculated from explicit user-created links.
 * No algorithmic guessing, 100% auditable.
 */
import React from 'react';
import {
  ChartBarIcon,
  ClockIcon,
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon,
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
            <p className="text-xs text-neutral-600">Mill Transparency</p>
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
            <p className="text-xs text-neutral-600">Plantation Transparency</p>
          </div>
        </div>

        {/* Data Quality - Always 100% for deterministic system */}
        <div className="flex items-center justify-between p-3 bg-success-50 rounded-lg">
          <div className="flex items-center space-x-2">
            <CheckCircleIcon className="h-5 w-5 text-success-600" />
            <span className="font-medium text-neutral-900">Data Quality</span>
          </div>
          <div className="flex items-center space-x-2">
            <span className="font-bold text-success-600">
              100%
            </span>
            <Badge variant="success" size="sm">
              Auditable
            </Badge>
          </div>
        </div>

        {/* Last Updated */}
        <div className="text-center pt-4 border-t border-neutral-200">
          <div className="text-xs text-neutral-500">
            Last updated: {new Date(metrics.last_updated).toLocaleDateString()}
          </div>
        </div>
      </CardBody>
    </Card>
  );
};

export default TransparencyScoreCard;
