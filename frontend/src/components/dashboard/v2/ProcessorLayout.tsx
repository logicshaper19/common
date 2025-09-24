/**
 * Processor V2 Dashboard Content - Four-Pillar Dashboard for Processor Companies
 * Works with main layout system, no duplicate navigation
 */
import React from 'react';
import { useDashboardConfig } from '../../../hooks/useDashboardConfig';
import LoadingSpinner from '../../ui/LoadingSpinner';
import { Button } from '../../ui/Button';
import { 
  IncomingOrdersCard,
  OutgoingOrdersCard,
  InventoryManagementCard,
  TraceabilityCard
} from '../pillars';
import { PlusIcon } from '@heroicons/react/24/outline';

// Removed unused interface definitions

const ProcessorLayout: React.FC = () => {
  const { config, loading: configLoading } = useDashboardConfig();
  // Removed unused metrics and metricsLoading

  if (configLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner size="lg" />
        <span className="ml-3 text-gray-600">Loading dashboard...</span>
      </div>
    );
  }

  if (!config) {
    return (
      <div className="text-center py-12">
        <p className="text-red-600">Failed to load dashboard configuration</p>
      </div>
    );
  }

  // Removed unused processorMetrics

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div className="md:flex md:items-center md:justify-between">
        <div className="min-w-0 flex-1">
          <h2 className="text-2xl font-bold leading-7 text-gray-900 sm:truncate sm:text-3xl sm:tracking-tight">
            Processor Dashboard
          </h2>
          <p className="mt-1 text-sm text-gray-500">
            Four-pillar supply chain management for processors
          </p>
        </div>
        <div className="mt-4 flex md:ml-4 md:mt-0">
          <Button leftIcon={<PlusIcon className="h-4 w-4" />}>
            New Batch
          </Button>
        </div>
      </div>

      {/* Four-Pillar Dashboard */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Pillar 1: Incoming Orders (Sales) */}
        <IncomingOrdersCard maxItems={3} />
        
        {/* Pillar 2: Outgoing Orders (Procurement) */}
        <OutgoingOrdersCard maxItems={3} />
        
        {/* Pillar 3: Inventory Management */}
        <InventoryManagementCard maxItems={3} />
        
        {/* Pillar 4: Supply Chain Traceability */}
        <TraceabilityCard maxItems={3} />
      </div>
    </div>
  );
};

export default ProcessorLayout;