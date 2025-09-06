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

interface GapAnalysisPanelProps {
  gaps: GapAnalysisItem[];
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

  // Filter gaps by severity
  const filteredGaps = gaps.filter(gap => 
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
  const criticalCount = gaps.filter(g => g.severity === 'critical').length;
  const highCount = gaps.filter(g => g.severity === 'high').length;
  const totalImpact = gaps.reduce((sum, gap) => sum + gap.impact_score, 0);
  const totalImprovement = gaps.reduce((sum, gap) => sum + gap.estimated_improvement, 0);

  return (
    <Card className={cn('', className)}>
      <CardHeader 
        title="Gap Analysis"
        subtitle={`${gaps.length} gaps identified • ${totalImprovement.toFixed(1)}% potential improvement`}
      />
      
      <CardBody className="space-y-4">
        {/* Summary Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <div className="text-center p-3 bg-error-50 rounded-lg">
            <div className="text-2xl font-bold text-error-600">{criticalCount}</div>
            <div className="text-xs text-error-700">Critical</div>
          </div>
          <div className="text-center p-3 bg-warning-50 rounded-lg">
            <div className="text-2xl font-bold text-warning-600">{highCount}</div>
            <div className="text-xs text-warning-700">High Priority</div>
          </div>
          <div className="text-center p-3 bg-neutral-50 rounded-lg">
            <div className="text-2xl font-bold text-neutral-600">{totalImpact.toFixed(1)}</div>
            <div className="text-xs text-neutral-700">Total Impact</div>
          </div>
          <div className="text-center p-3 bg-success-50 rounded-lg">
            <div className="text-2xl font-bold text-success-600">+{totalImprovement.toFixed(1)}%</div>
            <div className="text-xs text-success-700">Potential Gain</div>
          </div>
        </div>

        {/* Filter Buttons */}
        <div className="flex flex-wrap gap-2">
          {['all', 'critical', 'high', 'medium', 'low'].map((severity) => (
            <Button
              key={severity}
              variant={filter === severity ? 'primary' : 'outline'}
              size="sm"
              onClick={() => setFilter(severity as any)}
            >
              {severity.charAt(0).toUpperCase() + severity.slice(1)}
              {severity !== 'all' && (
                <span className="ml-1">
                  ({gaps.filter(g => g.severity === severity).length})
                </span>
              )}
            </Button>
          ))}
        </div>

        {/* Gap List */}
        <div className="space-y-3">
          {sortedGaps.length === 0 ? (
            <div className="text-center py-8 text-neutral-500">
              <CheckCircleIcon className="h-12 w-12 mx-auto mb-3 text-success-600" />
              <p className="text-lg font-medium text-success-600">No gaps found!</p>
              <p className="text-sm">Your supply chain transparency is excellent.</p>
            </div>
          ) : (
            sortedGaps.map((gap) => {
              const isExpanded = expandedGaps.has(gap.id);
              const SeverityIcon = getSeverityIcon(gap.severity);
              
              return (
                <div
                  key={gap.id}
                  className="border border-neutral-200 rounded-lg overflow-hidden hover:shadow-md transition-shadow"
                >
                  {/* Gap Header */}
                  <div 
                    className="p-4 cursor-pointer hover:bg-neutral-50"
                    onClick={() => {
                      toggleGapExpansion(gap.id);
                      if (onGapClick) onGapClick(gap);
                    }}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex items-start space-x-3 flex-1">
                        <SeverityIcon className={cn('h-5 w-5 mt-0.5', getSeverityColor(gap.severity))} />
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center space-x-2 mb-1">
                            <h4 className="font-medium text-neutral-900 truncate">
                              {gap.title}
                            </h4>
                            <Badge variant={getSeverityBadgeVariant(gap.severity)} size="sm">
                              {gap.severity}
                            </Badge>
                            <Badge variant="neutral" size="sm">
                              {getTypeLabel(gap.type)}
                            </Badge>
                          </div>
                          <p className="text-sm text-neutral-600 line-clamp-2">
                            {gap.description}
                          </p>
                          <div className="flex items-center space-x-4 mt-2 text-xs text-neutral-500">
                            <span>Impact: {gap.impact_score.toFixed(1)}</span>
                            <span>Improvement: +{gap.estimated_improvement.toFixed(1)}%</span>
                            <span>{gap.affected_nodes.length} nodes affected</span>
                          </div>
                        </div>
                      </div>
                      <div className="flex items-center space-x-2 ml-3">
                        <div className="text-right">
                          <div className="text-sm font-medium text-success-600">
                            +{gap.estimated_improvement.toFixed(1)}%
                          </div>
                          <div className="text-xs text-neutral-500">potential</div>
                        </div>
                        {isExpanded ? (
                          <ChevronDownIcon className="h-5 w-5 text-neutral-400" />
                        ) : (
                          <ChevronRightIcon className="h-5 w-5 text-neutral-400" />
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Expanded Content */}
                  {isExpanded && showRecommendations && (
                    <div className="border-t border-neutral-200 bg-neutral-50 p-4">
                      <div className="space-y-4">
                        {/* Recommendations */}
                        <div>
                          <div className="flex items-center space-x-2 mb-3">
                            <LightBulbIcon className="h-4 w-4 text-primary-600" />
                            <h5 className="font-medium text-neutral-900">Recommendations</h5>
                          </div>
                          <div className="space-y-2">
                            {gap.recommendations.map((recommendation, index) => (
                              <div 
                                key={index}
                                className="flex items-start justify-between p-3 bg-white rounded border"
                              >
                                <div className="flex items-start space-x-2 flex-1">
                                  <div className="w-2 h-2 bg-primary-600 rounded-full mt-2 flex-shrink-0" />
                                  <p className="text-sm text-neutral-700">{recommendation}</p>
                                </div>
                                {onRecommendationAction && (
                                  <Button
                                    variant="outline"
                                    size="sm"
                                    onClick={() => onRecommendationAction(gap.id, recommendation)}
                                    className="ml-3 flex-shrink-0"
                                  >
                                    Take Action
                                  </Button>
                                )}
                              </div>
                            ))}
                          </div>
                        </div>

                        {/* Potential Impact */}
                        <div className="flex items-center justify-between p-3 bg-success-50 rounded-lg">
                          <div className="flex items-center space-x-2">
                            <ArrowTrendingUpIcon className="h-5 w-5 text-success-600" />
                            <span className="font-medium text-success-900">
                              Potential Transparency Improvement
                            </span>
                          </div>
                          <span className="text-lg font-bold text-success-600">
                            +{gap.estimated_improvement.toFixed(1)}%
                          </span>
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
