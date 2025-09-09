/**
 * Consolidated Transparency View Component
 * Clean, single-view design that eliminates information redundancy
 */
import React from 'react';
import {
  ChartBarIcon,
  ClockIcon,
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  SignalIcon,
} from '@heroicons/react/24/outline';
import { TransparencyMetrics, GapAnalysisItem } from '../../types/transparency';
import { Card, CardHeader, CardBody } from '../ui/Card';
import Badge from '../ui/Badge';
import Button from '../ui/Button';
import { cn, getTransparencyColor, formatTransparency } from '../../lib/utils';

interface ConsolidatedTransparencyViewProps {
  metrics: TransparencyMetrics;
  gapAnalysis: GapAnalysisItem[];
  isRealTimeConnected: boolean;
  showTrend?: boolean;
  previousScore?: number;
  className?: string;
}

const ConsolidatedTransparencyView: React.FC<ConsolidatedTransparencyViewProps> = ({
  metrics,
  gapAnalysis,
  isRealTimeConnected,
  showTrend = false,
  previousScore,
  className,
}) => {
  // Calculate trend if previous score is provided
  const trend = previousScore ? metrics.overall_score - previousScore : 0;
  const trendDirection = trend > 0 ? 'up' : trend < 0 ? 'down' : 'stable';

  // Get score color and status
  const scoreColor = getTransparencyColor(metrics.overall_score);
  const confidenceColor = getTransparencyColor(metrics.confidence_level);

  // Check if this is an empty state (all scores are 0)
  const isEmpty = metrics.overall_score === 0 && metrics.ttm_score === 0 && metrics.ttp_score === 0;

  if (isEmpty) {
    return (
      <div className={cn('space-y-6', className)}>
        <Card>
          <CardBody className="text-center py-12">
            <div className="space-y-4">
              <div className="mx-auto w-16 h-16 bg-neutral-100 rounded-full flex items-center justify-center">
                <ChartBarIcon className="h-8 w-8 text-neutral-400" />
              </div>
              <div>
                <h3 className="text-lg font-medium text-neutral-900 mb-2">
                  Getting Started with Transparency
                </h3>
                <p className="text-neutral-600 max-w-md mx-auto">
                  Upload purchase orders and supply chain data to begin tracking transparency metrics for your organization.
                </p>
              </div>
              <div className="flex items-center justify-center space-x-1 mt-4">
                <div className={cn(
                  'w-2 h-2 rounded-full',
                  isRealTimeConnected ? 'bg-success-500' : 'bg-error-500'
                )} />
                <span className="text-sm text-neutral-500">
                  System {isRealTimeConnected ? 'connected' : 'offline'}
                </span>
              </div>
            </div>
          </CardBody>
        </Card>
      </div>
    );
  }

  return (
    <div className={cn('space-y-6', className)}>
      {/* Main Transparency Score */}
      <Card>
        <CardBody className="text-center py-8">
          <div className="space-y-4">
            {/* Overall Score with Trend */}
            <div className="flex items-center justify-center space-x-3">
              <span className={cn(
                'text-5xl font-bold',
                scoreColor
              )}>
                {formatTransparency(metrics.overall_score)}
              </span>
              {showTrend && trend !== 0 && (
                <div className="flex items-center space-x-1">
                  {trendDirection === 'up' ? (
                    <ArrowTrendingUpIcon className="h-6 w-6 text-success-600" />
                  ) : (
                    <ArrowTrendingDownIcon className="h-6 w-6 text-error-600" />
                  )}
                  <span className={cn(
                    'text-lg font-medium',
                    trendDirection === 'up' ? 'text-success-600' : 'text-error-600'
                  )}>
                    {Math.abs(trend).toFixed(1)}%
                  </span>
                </div>
              )}
            </div>
            
            <div className="text-lg text-neutral-600">Overall Transparency</div>
            
            {/* Sub-metrics in a clean row */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6 pt-6 border-t border-neutral-200">
              <div className="text-center">
                <div className="flex items-center justify-center space-x-1 mb-1">
                  <ClockIcon className="h-4 w-4 text-neutral-500" />
                  <span className="text-sm text-neutral-500">TTM</span>
                </div>
                <div className="text-xl font-semibold text-neutral-900">
                  {formatTransparency(metrics.ttm_score)}
                </div>
              </div>
              
              <div className="text-center">
                <div className="flex items-center justify-center space-x-1 mb-1">
                  <ChartBarIcon className="h-4 w-4 text-neutral-500" />
                  <span className="text-sm text-neutral-500">TTP</span>
                </div>
                <div className="text-xl font-semibold text-neutral-900">
                  {formatTransparency(metrics.ttp_score)}
                </div>
              </div>
              
              <div className="text-center">
                <div className="flex items-center justify-center space-x-1 mb-1">
                  <CheckCircleIcon className="h-4 w-4 text-neutral-500" />
                  <span className="text-sm text-neutral-500">Confidence</span>
                </div>
                <Badge 
                  variant={metrics.confidence_level >= 80 ? 'success' : 'warning'}
                  className="text-sm"
                >
                  {formatTransparency(metrics.confidence_level)}
                </Badge>
              </div>
              
              <div className="text-center">
                <div className="flex items-center justify-center space-x-1 mb-1">
                  <SignalIcon className="h-4 w-4 text-neutral-500" />
                  <span className="text-sm text-neutral-500">Status</span>
                </div>
                <div className="flex items-center justify-center space-x-1">
                  <div className={cn(
                    'w-2 h-2 rounded-full',
                    isRealTimeConnected ? 'bg-success-500' : 'bg-error-500'
                  )} />
                  <span className="text-sm text-neutral-600">
                    {isRealTimeConnected ? 'Live' : 'Offline'}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </CardBody>
      </Card>

      {/* Supply Chain Traceability */}
      <Card>
        <CardHeader title="Supply Chain Traceability" />
        <CardBody>
          <div className="space-y-4">
            {/* Single progress bar with labels */}
            <div className="relative">
              <div className="flex mb-2 items-center justify-between">
                <span className="text-sm font-medium text-success-700">
                  {formatTransparency(metrics.traced_percentage)} Traced
                </span>
                <span className="text-sm font-medium text-neutral-500">
                  {formatTransparency(metrics.untraced_percentage)} Untraced
                </span>
              </div>
              <div className="w-full bg-neutral-200 rounded-full h-3">
                <div 
                  className="bg-success-600 h-3 rounded-full transition-all duration-300"
                  style={{ width: `${metrics.traced_percentage}%` }}
                />
              </div>
            </div>
            
            <div className="text-xs text-neutral-500 text-center">
              Last updated: {new Date(metrics.last_updated).toLocaleDateString()}
            </div>
          </div>
        </CardBody>
      </Card>

      {/* Critical Gaps - Only show if there are gaps */}
      {gapAnalysis.length > 0 && (
        <Card>
          <CardHeader 
            title="Critical Gaps" 
            action={
              <Badge variant="warning" size="sm">
                {gapAnalysis.length}
              </Badge>
            }
          />
          <CardBody>
            <div className="space-y-3">
              {gapAnalysis.slice(0, 3).map((gap) => (
                <div key={gap.id} className="flex items-center justify-between p-3 bg-warning-50 rounded-lg">
                  <div className="flex items-center space-x-3">
                    <ExclamationTriangleIcon className="h-5 w-5 text-warning-600" />
                    <div>
                      <div className="font-medium text-warning-900">{gap.title}</div>
                      <div className="text-sm text-warning-700">{gap.description}</div>
                    </div>
                  </div>
                  <Badge variant="warning" size="sm">
                    {gap.severity}
                  </Badge>
                </div>
              ))}
              
              {gapAnalysis.length > 3 && (
                <Button
                  variant="outline"
                  size="sm"
                  className="w-full mt-3"
                >
                  View All {gapAnalysis.length} Gaps
                </Button>
              )}
            </div>
          </CardBody>
        </Card>
      )}
    </div>
  );
};

export default ConsolidatedTransparencyView;
