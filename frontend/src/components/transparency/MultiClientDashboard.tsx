/**
 * Multi-Client Dashboard Component
 * Consultant view showing multiple client transparency metrics
 */
import React, { useState } from 'react';
import {
  BuildingOfficeIcon,
  ChartBarIcon,
  ExclamationTriangleIcon,
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon,
  ClockIcon,
  CheckCircleIcon,
  EyeIcon,
} from '@heroicons/react/24/outline';
import { MultiClientDashboard as MultiClientDashboardType, CompanyTransparencySummary } from '../../types/transparency';
import { Card, CardHeader, CardBody } from '../ui/Card';
import Badge from '../ui/Badge';
import Button from '../ui/Button';
import AnalyticsCard from '../ui/AnalyticsCard';
import TransparencyScoreCard from './TransparencyScoreCard';
import { cn, getTransparencyColor, formatTransparency } from '../../lib/utils';

interface MultiClientDashboardProps {
  data: MultiClientDashboardType;
  onClientSelect?: (clientId: string) => void;
  onViewDetails?: (clientId: string) => void;
  className?: string;
}

const MultiClientDashboard: React.FC<MultiClientDashboardProps> = ({
  data,
  onClientSelect,
  onViewDetails,
  className,
}) => {
  const [selectedClient, setSelectedClient] = useState<string | null>(null);
  const [sortBy, setSortBy] = useState<'name' | 'transparency' | 'gaps' | 'orders'>('transparency');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');

  // Sort clients
  const sortedClients = [...data.clients].sort((a, b) => {
    let aValue: number | string;
    let bValue: number | string;

    switch (sortBy) {
      case 'name':
        aValue = a.company_name;
        bValue = b.company_name;
        break;
      case 'transparency':
        aValue = a.current_metrics.overall_score;
        bValue = b.current_metrics.overall_score;
        break;
      case 'gaps':
        aValue = a.critical_gaps;
        bValue = b.critical_gaps;
        break;
      case 'orders':
        aValue = a.total_purchase_orders;
        bValue = b.total_purchase_orders;
        break;
      default:
        aValue = a.current_metrics.overall_score;
        bValue = b.current_metrics.overall_score;
    }

    if (typeof aValue === 'string' && typeof bValue === 'string') {
      return sortOrder === 'asc' 
        ? aValue.localeCompare(bValue)
        : bValue.localeCompare(aValue);
    }

    return sortOrder === 'asc' 
      ? (aValue as number) - (bValue as number)
      : (bValue as number) - (aValue as number);
  });

  const handleClientClick = (client: CompanyTransparencySummary) => {
    setSelectedClient(client.company_id);
    if (onClientSelect) {
      onClientSelect(client.company_id);
    }
  };

  const getCompanyTypeIcon = (type: string) => {
    return BuildingOfficeIcon; // Could be expanded with specific icons
  };

  const getCompanyTypeBadge = (type: string) => {
    switch (type) {
      case 'brand':
        return 'primary';
      case 'processor':
        return 'secondary';
      case 'originator':
        return 'success';
      default:
        return 'neutral';
    }
  };

  return (
    <div className={cn('space-y-6', className)}>
      {/* Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <AnalyticsCard
          name="Total Clients"
          value={data.total_clients.toString()}
          icon={BuildingOfficeIcon}
          changeType="increase"
          change="+12%"
        />

        <AnalyticsCard
          name="Avg Transparency"
          value={formatTransparency(data.aggregate_metrics.average_transparency)}
          icon={ChartBarIcon}
          changeType="increase"
          change="+5%"
        />

        <AnalyticsCard
          name="Gaps Identified"
          value={data.aggregate_metrics.total_gaps_identified.toString()}
          icon={ExclamationTriangleIcon}
          changeType="decrease"
          change="-8%"
        />

        <AnalyticsCard
          name="Improvements"
          value={data.aggregate_metrics.total_improvements_implemented.toString()}
          icon={CheckCircleIcon}
          changeType="increase"
          change="+15%"
        />
      </div>

      {/* Alerts */}
      {data.alerts.length > 0 && (
        <Card>
          <CardHeader 
            title="Active Alerts"
            subtitle={`${data.alerts.length} items requiring attention`}
          />
          <CardBody>
            <div className="space-y-3">
              {data.alerts.slice(0, 3).map((alert) => (
                <div 
                  key={alert.id}
                  className="flex items-start space-x-3 p-3 bg-warning-50 border border-warning-200 rounded-lg"
                >
                  <ExclamationTriangleIcon className="h-5 w-5 text-warning-600 mt-0.5 flex-shrink-0" />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center space-x-2 mb-1">
                      <h4 className="font-medium text-warning-900">{alert.title}</h4>
                      <Badge variant="warning" size="sm">{alert.severity}</Badge>
                    </div>
                    <p className="text-sm text-warning-800 mb-2">{alert.message}</p>
                    <div className="flex items-center justify-between">
                      <span className="text-xs text-warning-700">{alert.company_name}</span>
                      {alert.deadline && (
                        <span className="text-xs text-warning-700">
                          Due: {new Date(alert.deadline).toLocaleDateString()}
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              ))}
              {data.alerts.length > 3 && (
                <Button variant="outline" size="sm" className="w-full">
                  View All {data.alerts.length} Alerts
                </Button>
              )}
            </div>
          </CardBody>
        </Card>
      )}

      {/* Client List */}
      <Card>
        <CardHeader 
          title="Client Overview"
          subtitle={`${data.clients.length} active clients`}
          action={
            <div className="flex items-center space-x-2">
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value as any)}
                className="text-sm border border-neutral-300 rounded px-2 py-1"
              >
                <option value="transparency">Transparency</option>
                <option value="name">Name</option>
                <option value="gaps">Gaps</option>
                <option value="orders">Orders</option>
              </select>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')}
              >
                {sortOrder === 'asc' ? '↑' : '↓'}
              </Button>
            </div>
          }
        />
        <CardBody>
          <div className="space-y-3">
            {sortedClients.map((client) => {
              const isSelected = selectedClient === client.company_id;
              const CompanyIcon = getCompanyTypeIcon(client.company_type);
              
              // Calculate trend from trend data
              const trend = client.trend_data.length >= 2 
                ? client.trend_data[client.trend_data.length - 1].overall_score - 
                  client.trend_data[client.trend_data.length - 2].overall_score
                : 0;

              return (
                <div
                  key={client.company_id}
                  className={cn(
                    'p-4 border rounded-lg cursor-pointer transition-all duration-200',
                    isSelected 
                      ? 'border-primary-500 bg-primary-50 shadow-md' 
                      : 'border-neutral-200 hover:border-neutral-300 hover:shadow-sm'
                  )}
                  onClick={() => handleClientClick(client)}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3 flex-1">
                      <CompanyIcon className="h-8 w-8 text-neutral-600" />
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center space-x-2 mb-1">
                          <h3 className="font-medium text-neutral-900 truncate">
                            {client.company_name}
                          </h3>
                          <Badge 
                            variant={getCompanyTypeBadge(client.company_type) as any} 
                            size="sm"
                          >
                            {client.company_type}
                          </Badge>
                        </div>
                        
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-2">
                          <div className="text-center">
                            <div className={cn(
                              'text-lg font-bold',
                              getTransparencyColor(client.current_metrics.overall_score)
                            )}>
                              {formatTransparency(client.current_metrics.overall_score)}
                            </div>
                            <div className="text-xs text-neutral-500">Transparency</div>
                          </div>
                          
                          <div className="text-center">
                            <div className="text-lg font-bold text-neutral-900">
                              {client.total_purchase_orders}
                            </div>
                            <div className="text-xs text-neutral-500">Orders</div>
                          </div>
                          
                          <div className="text-center">
                            <div className="text-lg font-bold text-warning-600">
                              {client.critical_gaps}
                            </div>
                            <div className="text-xs text-neutral-500">Critical Gaps</div>
                          </div>
                          
                          <div className="text-center">
                            <div className="text-lg font-bold text-success-600">
                              {client.improvement_opportunities}
                            </div>
                            <div className="text-xs text-neutral-500">Opportunities</div>
                          </div>
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center space-x-3 ml-4">
                      {/* Trend Indicator */}
                      {trend !== 0 && (
                        <div className="flex items-center space-x-1">
                          {trend > 0 ? (
                            <ArrowTrendingUpIcon className="h-4 w-4 text-success-600" />
                          ) : (
                            <ArrowTrendingDownIcon className="h-4 w-4 text-error-600" />
                          )}
                          <span className={cn(
                            'text-sm font-medium',
                            trend > 0 ? 'text-success-600' : 'text-error-600'
                          )}>
                            {Math.abs(trend).toFixed(1)}%
                          </span>
                        </div>
                      )}

                      {/* Action Buttons */}
                      <div className="flex space-x-1">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={(e) => {
                            e.stopPropagation();
                            if (onViewDetails) onViewDetails(client.company_id);
                          }}
                        >
                          <EyeIcon className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </CardBody>
      </Card>

      {/* Selected Client Details */}
      {selectedClient && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {(() => {
            const client = data.clients.find(c => c.company_id === selectedClient);
            if (!client) return null;

            return (
              <>
                <TransparencyScoreCard 
                  metrics={client.current_metrics}
                  showTrend={true}
                  previousScore={client.trend_data.length >= 2 
                    ? client.trend_data[client.trend_data.length - 2].overall_score 
                    : undefined
                  }
                />
                
                <Card>
                  <CardHeader title="Recent Activity" />
                  <CardBody>
                    <div className="space-y-3">
                      {data.recent_activities
                        .filter(activity => activity.company_id === selectedClient)
                        .slice(0, 5)
                        .map((activity) => (
                          <div key={activity.id} className="flex items-start space-x-3">
                            <div className={cn(
                              'w-2 h-2 rounded-full mt-2',
                              activity.impact === 'positive' ? 'bg-success-600' :
                              activity.impact === 'negative' ? 'bg-error-600' : 'bg-neutral-400'
                            )} />
                            <div className="flex-1 min-w-0">
                              <h4 className="text-sm font-medium text-neutral-900">
                                {activity.title}
                              </h4>
                              <p className="text-xs text-neutral-600 mt-1">
                                {activity.description}
                              </p>
                              <p className="text-xs text-neutral-500 mt-1">
                                {new Date(activity.timestamp).toLocaleDateString()}
                              </p>
                            </div>
                          </div>
                        ))}
                    </div>
                  </CardBody>
                </Card>
              </>
            );
          })()}
        </div>
      )}
    </div>
  );
};

export default MultiClientDashboard;
