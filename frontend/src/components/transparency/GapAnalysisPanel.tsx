/**
 * Gap Analysis Panel Component
 * Displays transparency gaps and improvement recommendations
 */
import React, { useState } from 'react';
import {
  ExclamationTriangleIcon,
  ExclamationCircleIcon,
  InformationCircleIcon,
  CheckCircleIcon,
  ChevronDownIcon,
  ChevronRightIcon,
  LightBulbIcon,
  ArrowTrendingUpIcon,
} from '@heroicons/react/24/outline';
import { GapAnalysisItem } from '../../types/transparency';
import { Card, CardHeader, CardBody } from '../ui/Card';
import Badge from '../ui/Badge';
import Button from '../ui/Button';
import { cn } from '../../lib/utils';

// Backend gap format (temporary adapter)
interface BackendGapItem {
  gap_id: string;
  category: string;
  severity: 'critical' | 'high' | 'medium' | 'low';
  description: string;
  recommendation: string;
  impact_score: number;
  implementation_effort: string;
}

interface GapAnalysisPanelProps {
  gaps: GapAnalysisItem[] | BackendGapItem[];
  onGapClick?: (gap: GapAnalysisItem) => void;
  onRecommendationAction?: (gapId: string, recommendation: string) => void;
  className?: string;
  showRecommendations?: boolean;
}

const GapAnalysisPanel: React.FC<GapAnalysisPanelProps> = ({
  gaps,
  onGapClick,
  onRecommendationAction,
  className,
  showRecommendations = true,
}) => {
  const [expandedGaps, setExpandedGaps] = useState<Set<string>>(new Set());
  const [filter, setFilter] = useState<'all' | 'critical' | 'high' | 'medium' | 'low'>('all');

  // Adapter function to normalize gap data
  const normalizeGap = (gap: any): GapAnalysisItem => {
    if ('gap_id' in gap) {
      // Backend format
      return {
        id: gap.gap_id,
        type: gap.category as any,
        severity: gap.severity,
        title: gap.category.replace('_', ' ').replace(/\b\w/g, (l: string) => l.toUpperCase()),
        description: gap.description,
        impact_score: gap.impact_score,
        affected_nodes: [],
        recommendations: [gap.recommendation],
        estimated_improvement: gap.impact_score * 1.5 // Estimate based on impact
      };
    }
    return gap; // Frontend format
  };

  const normalizedGaps = gaps.map(normalizeGap);

  // Filter gaps by severity
  const filteredGaps = normalizedGaps.filter(gap =>
    filter === 'all' || gap.severity === filter
  );

  // Sort gaps by severity and impact
  const sortedGaps = [...filteredGaps].sort((a, b) => {
    const severityOrder = { critical: 4, high: 3, medium: 2, low: 1 };
    const severityDiff = severityOrder[b.severity] - severityOrder[a.severity];
    if (severityDiff !== 0) return severityDiff;
    return b.impact_score - a.impact_score;
  });

  const toggleGapExpansion = (gapId: string) => {
    const newExpanded = new Set(expandedGaps);
    if (newExpanded.has(gapId)) {
      newExpanded.delete(gapId);
    } else {
      newExpanded.add(gapId);
    }
    setExpandedGaps(newExpanded);
  };

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'critical':
        return ExclamationCircleIcon;
      case 'high':
        return ExclamationTriangleIcon;
      case 'medium':
        return InformationCircleIcon;
      case 'low':
        return CheckCircleIcon;
      default:
        return InformationCircleIcon;
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical':
        return 'text-error-600';
      case 'high':
        return 'text-warning-600';
      case 'medium':
        return 'text-primary-600';
      case 'low':
        return 'text-success-600';
      default:
        return 'text-neutral-600';
    }
  };

  const getSeverityBadgeVariant = (severity: string) => {
    switch (severity) {
      case 'critical':
        return 'error' as const;
      case 'high':
        return 'warning' as const;
      case 'medium':
        return 'primary' as const;
      case 'low':
        return 'success' as const;
      default:
        return 'neutral' as const;
    }
  };

  const getTypeLabel = (type: string) => {
    switch (type) {
      case 'missing_supplier':
        return 'Missing Supplier';
      case 'unconfirmed_order':
        return 'Unconfirmed Order';
      case 'incomplete_data':
        return 'Incomplete Data';
      case 'low_transparency':
        return 'Low Transparency';
      default:
        return type.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase());
    }
  };

  // Calculate summary stats
  const criticalCount = normalizedGaps.filter(g => g.severity === 'critical').length;
  const highCount = normalizedGaps.filter(g => g.severity === 'high').length;
  const totalImpact = normalizedGaps.reduce((sum, gap) => sum + gap.impact_score, 0);
  const totalImprovement = normalizedGaps.reduce((sum, gap) => sum + gap.estimated_improvement, 0);

  // Show empty state for zero gaps
  if (normalizedGaps.length === 0) {
    return (
      <Card className={cn('', className)}>
        <CardBody className="text-center py-12">
          <div className="space-y-4">
            <div className="mx-auto w-16 h-16 bg-success-100 rounded-full flex items-center justify-center">
              <CheckCircleIcon className="h-8 w-8 text-success-600" />
            </div>
            <div>
              <h3 className="text-lg font-medium text-success-900 mb-2">
                No Gaps Found
              </h3>
              <p className="text-neutral-600 max-w-md mx-auto">
                Your supply chain transparency is excellent. All critical areas are properly tracked and documented.
              </p>
            </div>
          </div>
        </CardBody>
      </Card>
    );
  }

  return (
    <Card className={cn('', className)}>
      <CardHeader
        title="Gap Analysis"
        action={
          <div className="flex items-center space-x-2">
            {/* Consolidated Priority Issues */}
            {(criticalCount + highCount) > 0 && (
              <Badge variant="error" size="sm">
                {criticalCount + highCount} Priority Issues
              </Badge>
            )}
            {/* Total with potential improvement */}
            <Badge variant="neutral" size="sm">
              {normalizedGaps.length} gaps • +{totalImprovement.toFixed(0)}% potential
            </Badge>
          </div>
        }
      />

      <CardBody className="space-y-4">
        {/* Only show filters if there are many gaps and mix of severities */}
        {normalizedGaps.length > 3 && (criticalCount > 0 || highCount > 0) && (
          <div className="flex gap-2">
            <Button
              variant={filter === 'all' ? 'primary' : 'outline'}
              size="sm"
              onClick={() => setFilter('all')}
            >
              All
            </Button>
            {criticalCount > 0 && (
              <Button
                variant={filter === 'critical' ? 'primary' : 'outline'}
                size="sm"
                onClick={() => setFilter('critical')}
              >
                Critical
              </Button>
            )}
            {highCount > 0 && (
              <Button
                variant={filter === 'high' ? 'primary' : 'outline'}
                size="sm"
                onClick={() => setFilter('high')}
              >
                High Priority
              </Button>
            )}
          </div>
        )}

        {/* Gap List */}
        <div className="space-y-3">
          {sortedGaps.length === 0 ? (
            <div className="text-center py-8 text-neutral-500">
              <p className="text-neutral-600">No {filter !== 'all' ? filter : ''} gaps found.</p>
            </div>
          ) : (
            sortedGaps.map((gap) => {
              const isExpanded = expandedGaps.has(gap.id);
              const SeverityIcon = getSeverityIcon(gap.severity);
              
              return (
                <div
                  key={gap.id}
                  className="border border-neutral-200 rounded-lg overflow-hidden hover:shadow-sm transition-shadow"
                >
                  {/* Compact Gap Header */}
                  <div
                    className="p-3 cursor-pointer hover:bg-neutral-50"
                    onClick={() => {
                      toggleGapExpansion(gap.id);
                      if (onGapClick) onGapClick(gap);
                    }}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-3 flex-1 min-w-0">
                        <SeverityIcon className={cn('h-4 w-4 flex-shrink-0', getSeverityColor(gap.severity))} />
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center space-x-2 mb-1">
                            <h4 className="font-medium text-neutral-900 truncate">
                              {gap.title}
                            </h4>
                            <Badge variant={getSeverityBadgeVariant(gap.severity)} size="sm">
                              {gap.severity}
                            </Badge>
                          </div>
                          <p className="text-sm text-neutral-600 line-clamp-1">
                            {gap.description}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center space-x-2 ml-3 flex-shrink-0">
                        <div className="text-right">
                          <div className="text-sm font-medium text-success-600">
                            +{gap.estimated_improvement.toFixed(0)}%
                          </div>
                        </div>
                        {isExpanded ? (
                          <ChevronDownIcon className="h-4 w-4 text-neutral-400" />
                        ) : (
                          <ChevronRightIcon className="h-4 w-4 text-neutral-400" />
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Simplified Expanded Content */}
                  {isExpanded && showRecommendations && (
                    <div className="border-t border-neutral-200 bg-neutral-50 p-3">
                      <div className="space-y-3">
                        {/* Single Recommendation */}
                        <div className="flex items-start justify-between">
                          <div className="flex items-start space-x-2 flex-1">
                            <LightBulbIcon className="h-4 w-4 text-primary-600 mt-0.5 flex-shrink-0" />
                            <p className="text-sm text-neutral-700">{gap.recommendations[0]}</p>
                          </div>
                          {onRecommendationAction && (
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => onRecommendationAction(gap.id, gap.recommendations[0])}
                              className="ml-3 flex-shrink-0"
                            >
                              Take Action
                            </Button>
                          )}
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              );
            })
          )}
        </div>
      </CardBody>
    </Card>
  );
};

export default GapAnalysisPanel;
