/**
 * Traceability Card - Pillar 4 of Four-Pillar Dashboard
 * Shows supply chain connections and traceability
 */
import React, { useState, useEffect, useCallback } from 'react';
import { 
  LinkIcon,
  ArrowPathIcon,
  ExclamationTriangleIcon,
  EyeIcon,
  ChartBarIcon,
  GlobeAltIcon
} from '@heroicons/react/24/outline';
import { Card, CardHeader, CardBody } from '../../ui/Card';
import { Button } from '../../ui/Button';
import { Badge } from '../../ui/Badge';
import LoadingSpinner from '../../ui/LoadingSpinner';
// Removed unused useAuth import
import { useToast } from '../../../contexts/ToastContext';
import { STATUS_CONFIGS } from './constants';

interface TraceabilityNode {
  po_id: string;
  po_number: string;
  company_name: string;
  company_type: string;
  depth: number;
  trace_path: string;
  chain_type: 'COMMERCIAL' | 'PHYSICAL';
}

interface TraceabilitySummary {
  total_nodes: number;
  max_depth: number;
  commercial_chain_length: number;
  physical_chain_length: number;
  compliance_score: number;
}

interface TraceabilityCardProps {
  className?: string;
  maxItems?: number;
}

const TraceabilityCard: React.FC<TraceabilityCardProps> = ({ 
  className = '',
  maxItems = 5 
}) => {
  // Removed unused user variable
  const { showToast } = useToast();
  const [traceabilityData, setTraceabilityData] = useState<{
    nodes: TraceabilityNode[];
    summary: TraceabilitySummary;
  } | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadTraceabilityData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      
      // For now, show empty state since we need a real PO ID to trace
      // In a real implementation, this would be passed as a prop or selected from recent POs
      setTraceabilityData({
        nodes: [],
        summary: {
          total_nodes: 0,
          max_depth: 0,
          commercial_chain_length: 0,
          physical_chain_length: 0,
          compliance_score: 0
        }
      });
    } catch (err: any) {
      const errorMessage = err.message || 'Failed to load traceability data';
      setError(errorMessage);
      showToast({ type: 'error', title: errorMessage });
    } finally {
      setLoading(false);
    }
  }, [showToast]);

  useEffect(() => {
    loadTraceabilityData();
  }, [loadTraceabilityData]);

  const getChainTypeBadge = (chainType: string) => {
    const typeConfig = STATUS_CONFIGS.CHAIN_TYPE[chainType as keyof typeof STATUS_CONFIGS.CHAIN_TYPE] || { variant: 'neutral' as const, label: chainType };
    return <Badge variant={typeConfig.variant} size="sm">{typeConfig.label}</Badge>;
  };

  const getCompanyTypeIcon = (companyType: string) => {
    switch (companyType) {
      case 'brand':
        return <GlobeAltIcon className="h-4 w-4 text-primary-600" />;
      case 'processor':
        return <ChartBarIcon className="h-4 w-4 text-blue-600" />;
      case 'originator':
        return <LinkIcon className="h-4 w-4 text-green-600" />;
      default:
        return <LinkIcon className="h-4 w-4 text-neutral-600" />;
    }
  };

  const getComplianceScoreColor = (score: number) => {
    if (score >= 90) return 'text-success-600';
    if (score >= 70) return 'text-warning-600';
    return 'text-error-600';
  };

  if (loading) {
    return (
      <Card className={className}>
        <CardHeader title="Supply Chain Traceability" />
        <CardBody>
          <div className="flex items-center justify-center h-32">
            <LoadingSpinner size="md" />
            <span className="ml-2 text-neutral-600">Loading traceability data...</span>
          </div>
        </CardBody>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className={className}>
        <CardHeader title="Supply Chain Traceability" />
        <CardBody>
          <div className="text-center py-8">
            <ExclamationTriangleIcon className="h-12 w-12 text-error-600 mx-auto mb-4" />
            <p className="text-error-600 mb-4">{error}</p>
            <Button onClick={loadTraceabilityData} variant="outline">
              Try Again
            </Button>
          </div>
        </CardBody>
      </Card>
    );
  }

  return (
    <Card className={className}>
      <CardHeader 
        title="Supply Chain Traceability"
        subtitle={`${traceabilityData?.summary.total_nodes || 0} nodes in chain • Compliance: ${traceabilityData?.summary.compliance_score || 0}%`}
        action={
          <div className="flex items-center space-x-2">
            <Badge variant="primary">{traceabilityData?.summary.total_nodes || 0}</Badge>
            <Badge 
              variant={traceabilityData?.summary.compliance_score && traceabilityData.summary.compliance_score >= 90 ? 'success' : 'warning'}
            >
              {traceabilityData?.summary.compliance_score || 0}%
            </Badge>
          </div>
        }
      />
      <CardBody>
        {!traceabilityData || traceabilityData.nodes.length === 0 ? (
          <div className="text-center py-8">
            <LinkIcon className="h-12 w-12 text-neutral-400 mx-auto mb-4" />
            <p className="text-neutral-500 mb-4">No traceability data found</p>
            <p className="text-sm text-neutral-400 mb-4">
              Traceability information will appear here when you have connected supply chains.
            </p>
            <Button leftIcon={<ArrowPathIcon className="h-4 w-4" />}>
              Trace Supply Chain
            </Button>
          </div>
        ) : (
          <div className="space-y-4">
            {/* Summary Stats */}
            <div className="grid grid-cols-2 gap-4 mb-6">
              <div className="text-center p-3 bg-neutral-50 rounded-lg">
                <div className="text-2xl font-bold text-primary-600">
                  {traceabilityData.summary.commercial_chain_length}
                </div>
                <div className="text-sm text-neutral-600">Commercial Links</div>
              </div>
              <div className="text-center p-3 bg-neutral-50 rounded-lg">
                <div className={`text-2xl font-bold ${getComplianceScoreColor(traceabilityData.summary.compliance_score)}`}>
                  {traceabilityData.summary.compliance_score}%
                </div>
                <div className="text-sm text-neutral-600">Compliance Score</div>
              </div>
            </div>

            {/* Chain Nodes */}
            {traceabilityData.nodes.slice(0, maxItems).map((node, index) => (
              <div key={node.po_id} className="border rounded-lg p-4 hover:bg-neutral-50 transition-colors">
                <div className="flex items-start justify-between">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center space-x-2 mb-2">
                      {getCompanyTypeIcon(node.company_type)}
                      <span className="font-medium text-neutral-900">{node.po_number}</span>
                      {getChainTypeBadge(node.chain_type)}
                      <Badge variant="neutral" size="sm">Level {node.depth}</Badge>
                    </div>
                    <p className="text-sm text-neutral-600 mb-1">
                      <span className="font-medium">{node.company_name}</span>
                      <span className="ml-2 text-xs text-neutral-500 capitalize">({node.company_type})</span>
                    </p>
                    <p className="text-xs text-neutral-500 truncate">
                      {node.trace_path}
                    </p>
                  </div>
                  <div className="flex items-center space-x-1 ml-4">
                    <Button size="sm" variant="outline">
                      <EyeIcon className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              </div>
            ))}
            
            <div className="flex space-x-2 pt-4">
              <Button variant="outline" className="flex-1">
                View Full Chain
              </Button>
              <Button leftIcon={<ArrowPathIcon className="h-4 w-4" />}>
                Trace New
              </Button>
            </div>
          </div>
        )}
      </CardBody>
    </Card>
  );
};

export default TraceabilityCard;
