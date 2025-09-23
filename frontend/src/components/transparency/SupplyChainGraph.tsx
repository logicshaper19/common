/**
 * Supply Chain Graph Component
 * Interactive visualization of supply chain paths with transparency metrics
 */
import React, { useState, useCallback, useMemo } from 'react';
import { 
  ReactFlow, 
  Node, 
  Edge, 
  Controls, 
  Background, 
  useNodesState, 
  useEdgesState,
  ConnectionMode,
  Panel,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import {
  BuildingOfficeIcon,
  CogIcon,
  SparklesIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  ClockIcon,
} from '@heroicons/react/24/outline';
import { SupplyChainVisualization, SupplyChainNode, ViewOptions } from '../../types/transparency';
import { Card, CardHeader, CardBody } from '../ui/Card';
import Badge from '../ui/Badge';
import Button from '../ui/Button';
import { cn, getTransparencyColor, formatTransparency } from '../../lib/utils';

interface SupplyChainGraphProps {
  data: SupplyChainVisualization;
  viewOptions?: ViewOptions;
  onNodeClick?: (node: SupplyChainNode) => void;
  onViewOptionsChange?: (options: ViewOptions) => void;
  className?: string;
  height?: number;
}

// Custom node component
const CustomNode: React.FC<{ data: any }> = ({ data }) => {
  const { node, isSelected } = data;
  
  const getCompanyIcon = (type: string) => {
    switch (type) {
      case 'brand':
        return BuildingOfficeIcon;
      case 'processor':
        return CogIcon;
      case 'originator':
        return SparklesIcon;
      default:
        return BuildingOfficeIcon;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'confirmed':
        return 'success';
      case 'pending':
        return 'warning';
      case 'missing':
        return 'error';
      case 'partial':
        return 'neutral';
      default:
        return 'neutral';
    }
  };

  const Icon = getCompanyIcon(node.company_type);
  const transparencyColor = getTransparencyColor(node.transparency_score);

  return (
    <div className={cn(
      'bg-white border-2 rounded-lg shadow-lg p-3 min-w-[200px] transition-all duration-200',
      isSelected ? 'border-primary-500 shadow-xl' : 'border-neutral-200',
      'hover:shadow-xl hover:border-primary-300'
    )}>
      {/* Header */}
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center space-x-2">
          <Icon className="h-5 w-5 text-neutral-600" />
          <Badge variant={getStatusColor(node.status)} size="sm">
            {node.status}
          </Badge>
        </div>
        <div className="text-right">
          <div className={cn('text-sm font-bold', transparencyColor)}>
            {formatTransparency(node.transparency_score)}
          </div>
          <div className="text-xs text-neutral-500">Score</div>
        </div>
      </div>

      {/* Company Info */}
      <div className="mb-2">
        <h4 className="font-medium text-neutral-900 text-sm truncate">
          {node.company_name}
        </h4>
        <p className="text-xs text-neutral-600 capitalize">
          {node.company_type}
        </p>
      </div>

      {/* Product Info */}
      <div className="mb-2">
        <p className="text-sm font-medium text-neutral-800 truncate">
          {node.product_name}
        </p>
        <p className="text-xs text-neutral-600">
          {(node.quantity || 0).toLocaleString()} {node.unit || 'N/A'}
        </p>
      </div>

      {/* Status Indicator */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-1">
          {node.status === 'confirmed' ? (
            <CheckCircleIcon className="h-4 w-4 text-success-600" />
          ) : node.status === 'pending' ? (
            <ClockIcon className="h-4 w-4 text-warning-600" />
          ) : (
            <ExclamationTriangleIcon className="h-4 w-4 text-error-600" />
          )}
          <span className="text-xs text-neutral-600">
            Level {node.level}
          </span>
        </div>
        {node.po_id && (
          <span className="text-xs text-neutral-500 font-mono">
            {node.po_id.slice(-6)}
          </span>
        )}
      </div>
    </div>
  );
};

const nodeTypes = {
  custom: CustomNode,
};

const SupplyChainGraph: React.FC<SupplyChainGraphProps> = ({
  data,
  viewOptions = {
    layout: 'hierarchical',
    show_labels: true,
    show_metrics: true,
    highlight_gaps: true,
    color_by: 'transparency',
    zoom_level: 1,
  },
  onNodeClick,
  onViewOptionsChange,
  className,
  height = 600,
}) => {
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [showControls, setShowControls] = useState(false);

  // Convert supply chain data to React Flow format
  const { nodes: flowNodes, edges: flowEdges } = useMemo(() => {
    const nodes: Node[] = data.nodes.map((node) => ({
      id: node.id,
      type: 'custom',
      position: node.position,
      data: { 
        node, 
        isSelected: selectedNodeId === node.id 
      },
      draggable: true,
    }));

    const edges: Edge[] = data.edges.map((edge) => ({
      id: edge.id,
      source: edge.source,
      target: edge.target,
      type: 'smoothstep',
      animated: edge.confirmation_status === 'pending',
      style: {
        stroke: edge.confirmation_status === 'confirmed' 
          ? '#10b981' 
          : edge.confirmation_status === 'pending'
          ? '#f59e0b'
          : '#ef4444',
        strokeWidth: 2,
      },
      label: viewOptions.show_labels ? `${edge.quantity_flow} ${edge.unit}` : undefined,
      labelStyle: { fontSize: 12, fontWeight: 500 },
    }));

    return { nodes, edges };
  }, [data, selectedNodeId, viewOptions.show_labels]);

  const [nodes, setNodes, onNodesChange] = useNodesState(flowNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(flowEdges);

  // Update nodes when data changes
  React.useEffect(() => {
    setNodes(flowNodes);
    setEdges(flowEdges);
  }, [flowNodes, flowEdges, setNodes, setEdges]);

  const handleNodeClick = useCallback((event: React.MouseEvent, node: Node) => {
    setSelectedNodeId(node.id);
    if (onNodeClick) {
      const supplyChainNode = data.nodes.find(n => n.id === node.id);
      if (supplyChainNode) {
        onNodeClick(supplyChainNode);
      }
    }
  }, [data.nodes, onNodeClick]);

  const handleLayoutChange = (layout: string) => {
    if (onViewOptionsChange) {
      onViewOptionsChange({ ...viewOptions, layout: layout as any });
    }
  };

  return (
    <Card className={cn('relative', className)}>
      <CardHeader 
        title="Supply Chain Visualization"
        subtitle={`${data.nodes.length} companies • ${data.edges.length} connections`}
        action={
          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowControls(!showControls)}
          >
            Controls
          </Button>
        }
      />
      
      <CardBody className="p-0">
        <div style={{ height }} className="relative">
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onNodeClick={handleNodeClick}
            nodeTypes={nodeTypes}
            connectionMode={ConnectionMode.Loose}
            fitView
            fitViewOptions={{ padding: 0.2 }}
          >
            <Background />
            <Controls />
            
            {/* Custom Panel */}
            <Panel position="top-right" className="bg-white rounded-lg shadow-lg p-3 m-2">
              <div className="space-y-2">
                <div className="text-sm font-medium text-neutral-900">
                  Transparency: {formatTransparency(data.overall_ttm_score)}
                </div>
                <div className="text-xs text-neutral-600">
                  {data.traced_percentage.toFixed(1)}% traced
                </div>
                {data.gap_analysis.length > 0 && (
                  <Badge variant="warning" size="sm">
                    {data.gap_analysis.length} gaps
                  </Badge>
                )}
              </div>
            </Panel>

            {/* Layout Controls */}
            {showControls && (
              <Panel position="top-left" className="bg-white rounded-lg shadow-lg p-3 m-2">
                <div className="space-y-3">
                  <h4 className="text-sm font-medium text-neutral-900">Layout</h4>
                  <div className="space-y-1">
                    {['hierarchical', 'force', 'circular'].map((layout) => (
                      <button
                        key={layout}
                        onClick={() => handleLayoutChange(layout)}
                        className={cn(
                          'block w-full text-left px-2 py-1 text-xs rounded',
                          viewOptions.layout === layout
                            ? 'bg-primary-100 text-primary-700'
                            : 'hover:bg-neutral-100'
                        )}
                      >
                        {layout.charAt(0).toUpperCase() + layout.slice(1)}
                      </button>
                    ))}
                  </div>
                </div>
              </Panel>
            )}
          </ReactFlow>
        </div>
      </CardBody>
    </Card>
  );
};

export default SupplyChainGraph;
