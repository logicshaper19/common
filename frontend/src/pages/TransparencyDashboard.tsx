/**
 * Transparency Dashboard Page
 * Main dashboard for transparency visualization and analysis
 */
import React, { useState, useEffect } from 'react';
import { 
  ChartBarIcon,
  MapIcon,
  ExclamationTriangleIcon,
  ArrowPathIcon,
  Cog6ToothIcon,
} from '@heroicons/react/24/outline';
import { useAuth } from '../contexts/AuthContext';
import { transparencyApi } from '../lib/transparencyApi';
import { useTransparencyMetricsWithUpdates } from '../hooks/useTransparencyUpdates';
import { 
  TransparencyMetrics,
  SupplyChainVisualization,
  GapAnalysisItem,
  MultiClientDashboard as MultiClientDashboardType,
  ViewOptions,
} from '../types/transparency';
import TransparencyScoreCard from '../components/transparency/TransparencyScoreCard';
import SupplyChainGraph from '../components/transparency/SupplyChainGraph';
import GapAnalysisPanel from '../components/transparency/GapAnalysisPanel';
import MultiClientDashboard from '../components/transparency/MultiClientDashboard';
import { Card, CardHeader, CardBody } from '../components/ui/Card';
import Button from '../components/ui/Button';
import Badge from '../components/ui/Badge';
import LoadingSpinner from '../components/ui/LoadingSpinner';
import { cn } from '../lib/utils';

const TransparencyDashboard: React.FC = () => {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState<'overview' | 'visualization' | 'gaps' | 'multi-client'>('overview');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Real-time transparency metrics with updates
  const {
    metrics: transparencyMetrics,
    setMetrics: setTransparencyMetrics,
    isUpdating,
    isConnected: isRealTimeConnected,
  } = useTransparencyMetricsWithUpdates(user?.company?.id || '');
  const [supplyChainData, setSupplyChainData] = useState<SupplyChainVisualization | null>(null);
  const [gapAnalysis, setGapAnalysis] = useState<GapAnalysisItem[]>([]);
  const [multiClientData, setMultiClientData] = useState<MultiClientDashboardType | null>(null);
  
  // View options
  const [viewOptions, setViewOptions] = useState<ViewOptions>({
    layout: 'hierarchical',
    show_labels: true,
    show_metrics: true,
    highlight_gaps: true,
    color_by: 'transparency',
    zoom_level: 1,
  });

  // Load data on component mount
  useEffect(() => {
    loadDashboardData();
  }, [user]);

  const loadDashboardData = async () => {
    if (!user?.company?.id) return;

    setIsLoading(true);
    setError(null);

    try {
      // Load transparency metrics
      const metrics = await transparencyApi.getTransparencyMetrics(user.company.id);
      setTransparencyMetrics(metrics);

      // Load supply chain visualization (using a mock PO ID)
      const visualization = await transparencyApi.getSupplyChainVisualization('po-001');
      setSupplyChainData(visualization);

      // Load gap analysis
      const gaps = await transparencyApi.getGapAnalysis(user.company.id);
      setGapAnalysis(gaps);

      // Load multi-client data if user is a consultant
      if (user.role === 'consultant') {
        const multiClient = await transparencyApi.getMultiClientDashboard(user.id);
        setMultiClientData(multiClient);
        setActiveTab('multi-client');
      }
    } catch (err) {
      setError('Failed to load transparency data');
      console.error('Dashboard loading error:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleRefresh = () => {
    loadDashboardData();
  };

  const handleRecalculate = async () => {
    if (!user?.company?.id) return;

    setIsLoading(true);
    try {
      await transparencyApi.recalculateTransparency(user.company.id);
      await loadDashboardData();
    } catch (err) {
      setError('Failed to recalculate transparency');
    } finally {
      setIsLoading(false);
    }
  };

  const handleGapAction = (gapId: string, recommendation: string) => {
    console.log('Taking action on gap:', gapId, recommendation);
    // TODO: Implement gap action handling
  };

  const handleClientSelect = (clientId: string) => {
    console.log('Selected client:', clientId);
    // TODO: Load client-specific data
  };

  const handleViewDetails = (clientId: string) => {
    console.log('View details for client:', clientId);
    // TODO: Navigate to client details page
  };

  // Determine which tabs to show based on user role
  const availableTabs = [
    { id: 'overview', label: 'Overview', icon: ChartBarIcon },
    { id: 'visualization', label: 'Supply Chain', icon: MapIcon },
    { id: 'gaps', label: 'Gap Analysis', icon: ExclamationTriangleIcon },
  ];

  if (user?.role === 'consultant' && multiClientData) {
    availableTabs.push({ 
      id: 'multi-client', 
      label: 'Multi-Client', 
      icon: Cog6ToothIcon 
    });
  }

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
        <ExclamationTriangleIcon className="h-12 w-12 text-error-600 mx-auto mb-4" />
        <h3 className="text-lg font-medium text-error-900 mb-2">Error Loading Dashboard</h3>
        <p className="text-error-600 mb-4">{error}</p>
        <Button onClick={handleRefresh} variant="primary">
          Try Again
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-neutral-900">
            Transparency Dashboard
          </h1>
          <p className="text-neutral-600">
            Monitor and analyze supply chain transparency metrics
          </p>
        </div>
        <div className="flex items-center space-x-3">
          {/* Real-time connection indicator */}
          <div className="flex items-center space-x-2">
            <div className={cn(
              'w-2 h-2 rounded-full',
              isRealTimeConnected ? 'bg-success-600' : 'bg-neutral-400'
            )} />
            <span className="text-xs text-neutral-600">
              {isRealTimeConnected ? 'Live' : 'Offline'}
            </span>
          </div>

          <Button
            variant="outline"
            onClick={handleRefresh}
            disabled={isLoading}
          >
            <ArrowPathIcon className={cn(
              'h-4 w-4 mr-2',
              isLoading && 'animate-spin'
            )} />
            Refresh
          </Button>
          <Button
            variant="primary"
            onClick={handleRecalculate}
            disabled={isLoading}
          >
            Recalculate
          </Button>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="border-b border-neutral-200">
        <nav className="-mb-px flex space-x-8">
          {availableTabs.map((tab) => {
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
                {tab.id === 'gaps' && gapAnalysis.length > 0 && (
                  <Badge variant="warning" size="sm">
                    {gapAnalysis.length}
                  </Badge>
                )}
              </button>
            );
          })}
        </nav>
      </div>

      {/* Tab Content */}
      <div className="space-y-6">
        {activeTab === 'overview' && transparencyMetrics && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2">
              <TransparencyScoreCard
                metrics={transparencyMetrics}
                showTrend={true}
                size="lg"
                className={cn(
                  'transition-all duration-500',
                  isUpdating && 'ring-2 ring-primary-500 ring-opacity-50'
                )}
              />
            </div>
            <div className="space-y-4">
              <Card>
                <CardHeader title="Quick Stats" />
                <CardBody>
                  <div className="space-y-3">
                    <div className="flex justify-between">
                      <span className="text-neutral-600">TTM Score:</span>
                      <span className="font-medium">{transparencyMetrics.ttm_score.toFixed(1)}%</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-neutral-600">TTP Score:</span>
                      <span className="font-medium">{transparencyMetrics.ttp_score.toFixed(1)}%</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-neutral-600">Confidence:</span>
                      <span className="font-medium">{transparencyMetrics.confidence_level.toFixed(1)}%</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-neutral-600">Traced:</span>
                      <span className="font-medium">{transparencyMetrics.traced_percentage.toFixed(1)}%</span>
                    </div>
                  </div>
                </CardBody>
              </Card>
              
              {gapAnalysis.length > 0 && (
                <Card>
                  <CardHeader title="Critical Gaps" />
                  <CardBody>
                    <div className="space-y-2">
                      {gapAnalysis.slice(0, 3).map((gap) => (
                        <div key={gap.id} className="flex items-center justify-between">
                          <span className="text-sm text-neutral-600 truncate">
                            {gap.title}
                          </span>
                          <Badge variant="warning" size="sm">
                            {gap.severity}
                          </Badge>
                        </div>
                      ))}
                      {gapAnalysis.length > 3 && (
                        <Button
                          variant="outline"
                          size="sm"
                          className="w-full mt-2"
                          onClick={() => setActiveTab('gaps')}
                        >
                          View All {gapAnalysis.length} Gaps
                        </Button>
                      )}
                    </div>
                  </CardBody>
                </Card>
              )}
            </div>
          </div>
        )}

        {activeTab === 'visualization' && supplyChainData && (
          <SupplyChainGraph
            data={supplyChainData}
            viewOptions={viewOptions}
            onViewOptionsChange={setViewOptions}
            height={700}
          />
        )}

        {activeTab === 'gaps' && (
          <GapAnalysisPanel
            gaps={gapAnalysis}
            onRecommendationAction={handleGapAction}
            showRecommendations={true}
          />
        )}

        {activeTab === 'multi-client' && multiClientData && (
          <MultiClientDashboard
            data={multiClientData}
            onClientSelect={handleClientSelect}
            onViewDetails={handleViewDetails}
          />
        )}
      </div>
    </div>
  );
};

export default TransparencyDashboard;
