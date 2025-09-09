/**
 * Viral Cascade Analytics Visualization Component
 * Visualize supplier onboarding viral growth and cascade metrics
 */
import React, { useState, useEffect } from 'react';
import { 
  ChartBarIcon,
  GlobeAltIcon,
  ArrowTrendingUpIcon,
  UsersIcon,
  FunnelIcon,
  ArrowPathIcon,
} from '@heroicons/react/24/outline';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  FunnelChart,
  Funnel,
  LabelList,
} from 'recharts';
import { ViralCascadeMetrics } from '../../types/onboarding';
import { onboardingApi } from '../../lib/onboardingApi';
import { Card, CardHeader, CardBody } from '../ui/Card';
import Button from '../ui/Button';
import Badge from '../ui/Badge';
import AnalyticsCard from '../ui/AnalyticsCard';
import { cn, formatCurrency } from '../../lib/utils';

interface ViralCascadeAnalyticsProps {
  companyId?: string;
  className?: string;
}

const ViralCascadeAnalytics: React.FC<ViralCascadeAnalyticsProps> = ({
  companyId,
  className,
}) => {
  const [metrics, setMetrics] = useState<ViralCascadeMetrics | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'overview' | 'cascade' | 'funnel' | 'geographic' | 'trends'>('overview');

  // Load viral cascade metrics
  useEffect(() => {
    loadMetrics();
  }, [companyId]);

  const loadMetrics = async () => {
    setIsLoading(true);
    try {
      const data = await onboardingApi.getViralCascadeMetrics(companyId || 'default-company-id');
      setMetrics(data);
    } catch (error) {
      console.error('Failed to load viral cascade metrics:', error);
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading) {
    return (
      <Card className={className}>
        <CardBody>
          <div className="text-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600 mx-auto"></div>
            <p className="mt-2 text-neutral-600">Loading analytics...</p>
          </div>
        </CardBody>
      </Card>
    );
  }

  if (!metrics) {
    return (
      <Card className={className}>
        <CardBody>
          <div className="text-center py-8">
            <ChartBarIcon className="h-12 w-12 text-neutral-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-neutral-900 mb-2">No Data Available</h3>
            <p className="text-neutral-600">Unable to load viral cascade analytics.</p>
          </div>
        </CardBody>
      </Card>
    );
  }

  // Color palette for charts
  const colors = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4'];

  // Custom tooltip for charts
  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white p-3 border border-neutral-200 rounded-lg shadow-lg">
          <p className="font-medium text-neutral-900 mb-2">{label}</p>
          {payload.map((entry: any, index: number) => (
            <div key={index} className="flex items-center space-x-2">
              <div 
                className="w-3 h-3 rounded-full"
                style={{ backgroundColor: entry.color }}
              />
              <span className="text-sm text-neutral-600">{entry.name}:</span>
              <span className="text-sm font-medium text-neutral-900">
                {typeof entry.value === 'number' && entry.value % 1 !== 0
                  ? entry.value.toFixed(1)
                  : entry.value
                }
                {entry.name.includes('Rate') || entry.name.includes('%') ? '%' : ''}
              </span>
            </div>
          ))}
        </div>
      );
    }
    return null;
  };

  // Render overview tab
  const renderOverview = () => (
    <div className="space-y-6">
      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <AnalyticsCard
          name="Invitations Sent"
          value={metrics.total_invitations_sent.toString()}
          icon={UsersIcon}
          changeType="increase"
          change="+24%"
        />

        <AnalyticsCard
          name="Companies Onboarded"
          value={metrics.total_companies_onboarded.toString()}
          icon={ArrowTrendingUpIcon}
          changeType="increase"
          change="+18%"
        />

        <AnalyticsCard
          name="Conversion Rate"
          value={`${metrics.conversion_rate.toFixed(1)}%`}
          icon={FunnelIcon}
          changeType="increase"
          change="+3%"
        />

        <AnalyticsCard
          name="Avg. Time to Onboard"
          value={`${metrics.average_time_to_onboard.toFixed(1)}d`}
          icon={ChartBarIcon}
          changeType="decrease"
          change="-2d"
        />
      </div>

      {/* Growth Trend */}
      <Card>
        <CardHeader title="Growth Trend" />
        <CardBody>
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={metrics.time_series_data}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
              <XAxis dataKey="date" stroke="#64748b" fontSize={12} />
              <YAxis stroke="#64748b" fontSize={12} />
              <Tooltip content={<CustomTooltip />} />
              <Legend />
              <Area
                type="monotone"
                dataKey="cumulative_companies"
                stroke="#3b82f6"
                fill="#3b82f6"
                fillOpacity={0.1}
                name="Total Companies"
              />
              <Area
                type="monotone"
                dataKey="companies_onboarded"
                stroke="#10b981"
                fill="#10b981"
                fillOpacity={0.2}
                name="New Onboardings"
              />
            </AreaChart>
          </ResponsiveContainer>
        </CardBody>
      </Card>

      {/* Top Inviters */}
      <Card>
        <CardHeader title="Top Inviters" />
        <CardBody>
          <div className="space-y-3">
            {metrics.top_inviters.slice(0, 5).map((inviter, index) => (
              <div key={inviter.company_id} className="flex items-center justify-between p-3 bg-neutral-50 rounded-lg">
                <div className="flex items-center space-x-3">
                  <div className="w-8 h-8 bg-primary-600 rounded-full flex items-center justify-center text-white font-bold text-sm">
                    {index + 1}
                  </div>
                  <div>
                    <h4 className="font-medium text-neutral-900">{inviter.company_name}</h4>
                    <p className="text-sm text-neutral-600">{inviter.company_type}</p>
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-lg font-bold text-primary-600">
                    {inviter.successful_onboardings}
                  </div>
                  <div className="text-xs text-neutral-600">
                    {inviter.conversion_rate.toFixed(1)}% conversion
                  </div>
                </div>
              </div>
            ))}
          </div>
        </CardBody>
      </Card>
    </div>
  );

  // Render cascade levels tab
  const renderCascade = () => (
    <div className="space-y-6">
      <Card>
        <CardHeader title="Cascade Levels Performance" />
        <CardBody>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={metrics.cascade_levels}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
              <XAxis dataKey="level" stroke="#64748b" fontSize={12} />
              <YAxis stroke="#64748b" fontSize={12} />
              <Tooltip content={<CustomTooltip />} />
              <Legend />
              <Bar dataKey="companies_invited" fill="#3b82f6" name="Invited" />
              <Bar dataKey="companies_onboarded" fill="#10b981" name="Onboarded" />
            </BarChart>
          </ResponsiveContainer>
        </CardBody>
      </Card>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {metrics.cascade_levels.map((level) => (
          <Card key={level.level}>
            <CardBody>
              <div className="text-center">
                <div className="text-2xl font-bold text-primary-600 mb-2">
                  Level {level.level}
                </div>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-neutral-600">Invited:</span>
                    <span className="font-medium">{level.companies_invited}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-neutral-600">Onboarded:</span>
                    <span className="font-medium">{level.companies_onboarded}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-neutral-600">Conversion:</span>
                    <span className="font-medium">{level.conversion_rate.toFixed(1)}%</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-neutral-600">Avg. Time:</span>
                    <span className="font-medium">{level.average_time_to_onboard.toFixed(1)}d</span>
                  </div>
                </div>
              </div>
            </CardBody>
          </Card>
        ))}
      </div>
    </div>
  );

  // Render funnel tab
  const renderFunnel = () => (
    <Card>
      <CardHeader title="Onboarding Funnel" />
      <CardBody>
        <div className="space-y-4">
          {metrics.onboarding_funnel.map((step, index) => {
            const isLast = index === metrics.onboarding_funnel.length - 1;
            const nextStep = metrics.onboarding_funnel[index + 1];
            const dropOff = !isLast ? step.companies_entered - nextStep.companies_entered : 0;
            
            return (
              <div key={step.step} className="relative">
                <div className="flex items-center justify-between p-4 bg-neutral-50 rounded-lg">
                  <div className="flex-1">
                    <h4 className="font-medium text-neutral-900 capitalize">
                      {step.step.replace(/_/g, ' ')}
                    </h4>
                    <div className="flex items-center space-x-4 mt-1 text-sm text-neutral-600">
                      <span>{step.companies_entered} companies</span>
                      <span>{step.completion_rate.toFixed(1)}% completion</span>
                      {step.average_time_spent > 0 && (
                        <span>{step.average_time_spent.toFixed(1)} min avg</span>
                      )}
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-lg font-bold text-primary-600">
                      {step.companies_completed}
                    </div>
                    <div className="text-xs text-neutral-600">completed</div>
                  </div>
                </div>
                
                {!isLast && dropOff > 0 && (
                  <div className="flex items-center justify-center py-2">
                    <Badge variant="error" size="sm">
                      -{dropOff} dropped off ({step.drop_off_rate.toFixed(1)}%)
                    </Badge>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </CardBody>
    </Card>
  );

  // Render geographic tab
  const renderGeographic = () => (
    <div className="space-y-6">
      <Card>
        <CardHeader title="Geographic Distribution" />
        <CardBody>
          <div className="space-y-4">
            {metrics.geographic_distribution.map((geo) => (
              <div key={geo.country} className="flex items-center justify-between p-3 border border-neutral-200 rounded-lg">
                <div>
                  <h4 className="font-medium text-neutral-900">{geo.country}</h4>
                  <p className="text-sm text-neutral-600">
                    {geo.companies_count} companies • {geo.invitations_sent} invitations
                  </p>
                </div>
                <div className="text-right">
                  <div className="text-lg font-bold text-primary-600">
                    {geo.onboarding_rate.toFixed(1)}%
                  </div>
                  <div className="text-xs text-neutral-600">onboarding rate</div>
                </div>
              </div>
            ))}
          </div>
        </CardBody>
      </Card>

      <Card>
        <CardHeader title="Company Type Distribution" />
        <CardBody>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={metrics.company_type_distribution}
                cx="50%"
                cy="50%"
                outerRadius={100}
                fill="#8884d8"
                dataKey="count"
                label={({ company_type, percentage }) => `${company_type} (${percentage.toFixed(1)}%)`}
              >
                {metrics.company_type_distribution.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={colors[index % colors.length]} />
                ))}
              </Pie>
              <Tooltip content={<CustomTooltip />} />
            </PieChart>
          </ResponsiveContainer>
        </CardBody>
      </Card>
    </div>
  );

  return (
    <div className={className}>
      <Card>
        <CardHeader 
          title="Viral Cascade Analytics"
          subtitle="Track supplier onboarding growth and viral expansion"
          action={
            <Button
              variant="outline"
              size="sm"
              onClick={loadMetrics}
              leftIcon={<ArrowPathIcon className="h-4 w-4" />}
            >
              Refresh
            </Button>
          }
        />
        
        <CardBody>
          {/* Tab Navigation */}
          <div className="border-b border-neutral-200 mb-6">
            <nav className="-mb-px flex space-x-8">
              {[
                { id: 'overview', label: 'Overview', icon: ChartBarIcon },
                { id: 'cascade', label: 'Cascade Levels', icon: ArrowTrendingUpIcon },
                { id: 'funnel', label: 'Funnel', icon: FunnelIcon },
                { id: 'geographic', label: 'Geographic', icon: GlobeAltIcon },
              ].map((tab) => {
                const Icon = tab.icon;
                const isActive = activeTab === tab.id;
                
                return (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id as any)}
                    className={cn(
                      'flex items-center space-x-2 py-2 px-1 border-b-2 font-medium text-sm transition-colors',
                      isActive
                        ? 'border-primary-500 text-primary-600'
                        : 'border-transparent text-neutral-500 hover:text-neutral-700 hover:border-neutral-300'
                    )}
                  >
                    <Icon className="h-5 w-5" />
                    <span>{tab.label}</span>
                  </button>
                );
              })}
            </nav>
          </div>

          {/* Tab Content */}
          {activeTab === 'overview' && renderOverview()}
          {activeTab === 'cascade' && renderCascade()}
          {activeTab === 'funnel' && renderFunnel()}
          {activeTab === 'geographic' && renderGeographic()}
        </CardBody>
      </Card>
    </div>
  );
};

export default ViralCascadeAnalytics;
