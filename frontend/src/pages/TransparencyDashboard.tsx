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
import { useToast } from '../contexts/ToastContext';
import { useDeterministicTransparency } from '../hooks/useDeterministicTransparency';
import { 
  TransparencyMetrics,
  SupplyChainVisualization,
  GapAnalysisItem,
  MultiClientDashboard as MultiClientDashboardType,
  ViewOptions,
} from '../types/transparency';
import TransparencyScoreCard from '../components/transparency/TransparencyScoreCard';
import ConsolidatedTransparencyView from '../components/transparency/ConsolidatedTransparencyView';
import SupplyChainGraph from '../components/transparency/SupplyChainGraph';
import GapAnalysisPanel from '../components/transparency/GapAnalysisPanel';
import MultiClientDashboard from '../components/transparency/MultiClientDashboard';
import DeterministicTransparencyDashboard from '../components/transparency/DeterministicTransparencyDashboard';
import { Card, CardHeader, CardBody } from '../components/ui/Card';
import Button from '../components/ui/Button';
import Badge from '../components/ui/Badge';
import LoadingSpinner from '../components/ui/LoadingSpinner';
import { cn } from '../lib/utils';

const TransparencyDashboard: React.FC = () => {
  const { user } = useAuth();
  const { showToast } = useToast();
  const [activeTab, setActiveTab] = useState<'deterministic' | 'overview' | 'visualization' | 'gaps' | 'multi-client'>('deterministic');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Use deterministic transparency hook for consistent API calls
  const {
    metrics: deterministicMetrics,
    gaps: deterministicGaps,
    loading: isTransparencyLoading,
    error: transparencyError,
    fetchTransparencyMetrics,
    refreshTransparencyData,
  } = useDeterministicTransparency(user?.company?.id);

  // Convert deterministic metrics to the expected format
  const transparencyMetrics: TransparencyMetrics | null = deterministicMetrics ? {
    ttm_score: deterministicMetrics.transparency_to_mill_percentage / 100,
    ttp_score: deterministicMetrics.transparency_to_plantation_percentage / 100,
    overall_score: (deterministicMetrics.transparency_to_mill_percentage + deterministicMetrics.transparency_to_plantation_percentage) / 200,
    confidence_level: 1.0,
    traced_percentage: (deterministicMetrics.transparency_to_mill_percentage + deterministicMetrics.transparency_to_plantation_percentage) / 2,
    untraced_percentage: 100 - (deterministicMetrics.transparency_to_mill_percentage + deterministicMetrics.transparency_to_plantation_percentage) / 2,
    last_updated: deterministicMetrics.calculation_timestamp,
  } : null;
  const setTransparencyMetrics = () => {}; // No-op for compatibility
  const isUpdating = false;
  const isRealTimeConnected = false;
  
  const [supplyChainData, setSupplyChainData] = useState<SupplyChainVisualization | null>(null);
  // Convert deterministic gaps to the expected format
  const gapAnalysis: GapAnalysisItem[] = deterministicGaps.map((gap, index) => ({
    id: `gap-${index}`,
    type: gap.gap_type === 'not_traced_to_mill' ? 'incomplete_data' : 'low_transparency',
    severity: 'medium',
    title: `Transparency Gap - ${gap.po_number}`,
    description: `Missing traceability for ${gap.product_name} from ${gap.seller_company_name}`,
    impact: 'medium',
    impact_score: 0.5,
    affected_nodes: [gap.po_id],
    recommendations: [`Improve traceability for ${gap.product_name}`],
    estimated_improvement: 10,
    status: 'open',
    created_at: new Date().toISOString(),
  }));
  const [multiClientData, setMultiClientData] = useState<MultiClientDashboardType | null>(null);

  // Client filtering for consultant users
  const [selectedClient, setSelectedClient] = useState<string>('all');
  const [clientCompanies, setClientCompanies] = useState<any[]>([]);

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
    if (user?.company?.id) {
      loadDashboardData();
    } else {
      setError('User not authenticated or no company ID available');
      setIsLoading(false);
    }
  }, [user]);

  // Load client companies for consultant users
  useEffect(() => {
    if (user?.role === 'consultant') {
      fetchClientCompanies();
    }
  }, [user]);

  const fetchClientCompanies = async () => {
    try {
      // For now, we'll use a mock implementation
      // In a real implementation, you'd call an API endpoint like:
      // const response = await consultantApi.getClientCompanies();

      // Mock client companies for demonstration
      const mockClients = [
        { id: 'client-1', name: 'Acme Palm Oil Co.' },
        { id: 'client-2', name: 'Global Commodities Ltd.' },
        { id: 'client-3', name: 'Sustainable Sourcing Inc.' }
      ];

      setClientCompanies(mockClients);
    } catch (error) {
      console.error('Error fetching client companies:', error);
      showToast({
        type: 'error',
        title: 'Error',
        message: 'Failed to load client companies'
      });
    }
  };

  const loadDashboardData = async () => {
    if (!user?.company?.id) return;

    setIsLoading(true);
    setError(null);

    try {
      // Load transparency metrics using the new v2 API
      await fetchTransparencyMetrics();
      
      // Load supply chain visualization (using a mock PO ID)
      // Note: This would need to be updated to use the new API when available
      // const visualization = await transparencyApi.getSupplyChainVisualization('po-001');
      // setSupplyChainData(visualization);

      // Load multi-client data if user is a consultant
      if (user.role === 'consultant') {
        // Note: This would need to be updated to use the new API when available
        // const multiClient = await transparencyApi.getMultiClientDashboard(user.id);
        // setMultiClientData(multiClient);
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
      await refreshTransparencyData();
      await loadDashboardData();
    } catch (err) {
      setError('Failed to recalculate transparency');
    } finally {
      setIsLoading(false);
    }
  };

  const handleGapAction = async (gapId: string, recommendation: string) => {
    try {
      // Find the gap in our current gap analysis
      const gap = gapAnalysis.find(g => g.id === gapId);
      if (!gap) {
        console.error('Gap not found:', gapId);
        return;
      }

      // Create action based on gap type and recommendation
      let actionMessage = '';
      let actionType = '';

      switch (gap.type) {
        case 'missing_supplier':
          actionMessage = 'Supplier invitation sent. Follow up in 3-5 business days.';
          actionType = 'supplier_invitation';
          break;
        case 'unconfirmed_order':
          actionMessage = 'Reminder sent to seller. Purchase order marked for follow-up.';
          actionType = 'po_reminder';
          break;
        case 'incomplete_data':
          actionMessage = 'Data completion request created. Assigned to data team.';
          actionType = 'data_request';
          break;
        case 'low_transparency':
          actionMessage = 'Transparency improvement plan initiated. Target: +15% transparency.';
          actionType = 'improvement_plan';
          break;
        default:
          actionMessage = 'Action item created and assigned for resolution.';
          actionType = 'general_action';
      }

      // Show success message
      console.log(`Gap Action Taken - ${actionType}:`, {
        gapId,
        gapType: gap.type,
        severity: gap.severity,
        recommendation,
        actionMessage
      });

      // TODO: In a real implementation, this would call an API to:
      // 1. Create action items in a task management system
      // 2. Send notifications to relevant team members
      // 3. Update gap status in the database
      // 4. Track progress and follow-up dates

      // Show user feedback using toast instead of alert
      showToast({
        type: 'success',
        title: 'Gap Action Created',
        message: `${actionMessage} - Gap: ${gap.title}`
      });

      // Refresh gap analysis to reflect any changes
      await loadDashboardData();

    } catch (error) {
      console.error('Failed to handle gap action:', error);
      showToast({
        type: 'error',
        title: 'Action Failed',
        message: 'Failed to process gap action. Please try again.'
      });
    }
  };

  const handleClientSelect = (clientId: string) => {
    console.log('Selected client:', clientId);
    // TODO: Load client-specific data
  };

  const handleViewDetails = (clientId: string) => {
    console.log('View details for client:', clientId);
    // TODO: Navigate to client details page
  };

  // Client selector component for consultant users
  const ClientSelector = () => {
    if (user?.role !== 'consultant') return null;

    return (
      <div className="mb-6">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Select Client
        </label>
        <select
          value={selectedClient}
          onChange={(e) => setSelectedClient(e.target.value)}
          className="w-full border border-gray-300 rounded-md px-3 py-2 bg-white shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        >
          <option value="all">All Clients</option>
          {clientCompanies.map(client => (
            <option key={client.id} value={client.id}>
              {client.name}
            </option>
          ))}
        </select>
        {selectedClient !== 'all' && (
          <p className="text-sm text-gray-500 mt-1">
            Viewing data for: {clientCompanies.find(c => c.id === selectedClient)?.name}
          </p>
        )}
      </div>
    );
  };

  // Determine which tabs to show based on user role
  const availableTabs = [
    { id: 'deterministic', label: 'Deterministic Metrics', icon: ChartBarIcon },
    { id: 'overview', label: 'Legacy Overview', icon: ChartBarIcon },
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

  if (isLoading || isTransparencyLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner size="lg" />
        <span className="ml-3 text-gray-600">Loading transparency data...</span>
      </div>
    );
  }

  if (error || transparencyError) {
    const isDatabaseError = (error || transparencyError)?.includes('materialized view') || 
                           (error || transparencyError)?.includes('supply_chain_traceability');
    
    return (
      <div className="text-center py-12">
        <ExclamationTriangleIcon className="h-12 w-12 text-error-600 mx-auto mb-4" />
        <h3 className="text-lg font-medium text-error-900 mb-2">Error Loading Dashboard</h3>
        
        {isDatabaseError ? (
          <div className="text-error-600 mb-4">
            <p className="font-medium">Database Setup Required</p>
            <p className="text-sm mt-2">
              The transparency system requires database initialization. Please contact your administrator 
              to refresh the supply chain traceability data.
            </p>
          </div>
        ) : (
          <p className="text-error-600 mb-4">{error || transparencyError}</p>
        )}
        
        <div className="text-sm text-gray-500 mb-4">
          <p>User: {user?.email || 'Not authenticated'}</p>
          <p>Company ID: {user?.company?.id || 'No company'}</p>
          <p>Role: {user?.role || 'Unknown'}</p>
        </div>
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

      {/* Client Selector for Consultant Users */}
      <ClientSelector />

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
        {activeTab === 'deterministic' && (
          <DeterministicTransparencyDashboard
            companyId={user?.company?.id}
            className="max-w-7xl mx-auto"
          />
        )}

        {activeTab === 'overview' && transparencyMetrics && (
          <div className="max-w-4xl mx-auto">
            <ConsolidatedTransparencyView
              metrics={transparencyMetrics}
              gapAnalysis={gapAnalysis}
              isRealTimeConnected={isRealTimeConnected}
              showTrend={true}
              className={cn(
                'transition-all duration-500',
                isUpdating && 'ring-2 ring-primary-500 ring-opacity-50'
              )}
            />
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
