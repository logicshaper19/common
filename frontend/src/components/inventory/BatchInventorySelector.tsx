import React, { useState, useEffect, useCallback } from 'react';
import { Package, Calendar, MapPin, AlertTriangle, CheckCircle, Info } from 'lucide-react';
import { api } from '../../services/api';
import { toast } from 'react-hot-toast';
import useBatchValidation from '../../hooks/useBatchValidation';
import BatchValidationDisplay from './BatchValidationDisplay';

/**
 * @fileoverview BatchInventorySelector - A component that provides warehouse-like inventory selection
 *
 * This component transforms the abstract "enter quantity" experience into a physical
 * "select from warehouse shelves" experience. Users can see actual available batches,
 * their expiry dates, locations, and select specific quantities from each batch.
 *
 * Key Features:
 * - FIFO (First In, First Out) automatic allocation
 * - Real-time quantity validation
 * - Expiry date warnings
 * - Batch utilization tracking
 * - Smart auto-allocation based on target quantity
 *
 * @example
 * ```tsx
 * <BatchInventorySelector
 *   companyId="company-uuid"
 *   productId="product-uuid"
 *   targetQuantity={1950}
 *   onBatchesSelected={(selections, total) => {
 *     console.log('Selected batches:', selections);
 *     console.log('Total quantity:', total);
 *   }}
 * />
 * ```
 */

/**
 * Represents a batch of inventory available for selection
 */
interface Batch {
  /** Unique identifier for the batch */
  id: string;
  /** Human-readable batch identifier (e.g., "PO-LOREAL-003-BATCH-1") */
  batch_id: string;
  /** Available quantity in the batch */
  quantity: number;
  /** Unit of measurement (e.g., "kg", "tons") */
  unit: string;
  /** Date when the batch was produced */
  production_date: string;
  /** Optional expiry date for the batch */
  expiry_date?: string;
  /** Physical location of the batch */
  location_name?: string;
  /** Facility code where batch is stored */
  facility_code?: string;
  /** Quality metrics and certifications */
  quality_metrics?: Record<string, any>;
  /** Enhanced metadata for UI display */
  batch_metadata?: {
    /** Days until expiry (calculated) */
    days_until_expiry?: number;
    /** Whether batch expires within 30 days */
    is_expiring_soon?: boolean;
    /** FIFO priority order (1 = use first) */
    fifo_priority?: number;
  };
}

/**
 * Represents a user's selection of quantity from a specific batch
 */
interface BatchSelection {
  /** ID of the selected batch */
  batchId: string;
  /** Quantity selected from this batch */
  quantityToUse: number;
  /** Full batch object for reference */
  batch: Batch;
}

/**
 * Props for the BatchInventorySelector component
 */
interface BatchInventorySelectorProps {
  /** ID of the company whose inventory to display */
  companyId: string;
  /** ID of the product to filter inventory by */
  productId: string;
  /** Target quantity for auto-allocation (optional) */
  targetQuantity?: number;
  /** Callback fired when batch selections change */
  onBatchesSelected: (selections: BatchSelection[], totalQuantity: number) => void;
  /** Whether the component is disabled */
  disabled?: boolean;
  /** Additional CSS classes */
  className?: string;
}

/**
 * BatchInventorySelector Component
 *
 * Provides a warehouse-like interface for selecting inventory batches to fulfill purchase orders.
 * Features automatic FIFO allocation, real-time validation, and comprehensive batch information.
 *
 * @param props - Component props
 * @returns JSX element representing the batch inventory selector
 *
 * @example
 * ```tsx
 * // Basic usage for PO confirmation
 * <BatchInventorySelector
 *   companyId="company-123"
 *   productId="product-456"
 *   targetQuantity={1950}
 *   onBatchesSelected={(selections, total) => {
 *     setConfirmedQuantity(total);
 *     setBatchSelections(selections);
 *   }}
 * />
 *
 * // Disabled state during loading
 * <BatchInventorySelector
 *   companyId="company-123"
 *   productId="product-456"
 *   disabled={isSubmitting}
 *   onBatchesSelected={handleBatchSelection}
 * />
 * ```
 */
const BatchInventorySelector: React.FC<BatchInventorySelectorProps> = ({
  companyId,
  productId,
  targetQuantity = 0,
  onBatchesSelected,
  disabled = false,
  className = ''
}) => {
  const [availableBatches, setAvailableBatches] = useState<Batch[]>([]);
  const [selectedBatches, setSelectedBatches] = useState<Record<string, number>>({});
  const [isLoading, setIsLoading] = useState(true);
  const [autoAllocated, setAutoAllocated] = useState(false);

  // Fetch available inventory when component mounts or dependencies change
  useEffect(() => {
    fetchInventory();
  }, [companyId, productId]);

  // Auto-allocate batches when target quantity changes (FIFO)
  useEffect(() => {
    if (targetQuantity > 0 && availableBatches.length > 0 && !autoAllocated) {
      autoAllocateBatches(targetQuantity);
      setAutoAllocated(true);
    }
  }, [targetQuantity, availableBatches, autoAllocated]);

  const fetchInventory = async () => {
    try {
      setIsLoading(true);
      const response = await api.get(`/api/v1/batches/companies/${companyId}/inventory`, {
        params: { product_id: productId }
      });
      setAvailableBatches(response.data);
    } catch (error) {
      console.error('Error fetching inventory:', error);
      toast.error('Failed to load available inventory');
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * Automatically allocates batches using FIFO (First In, First Out) strategy
   *
   * This method implements smart allocation by:
   * 1. Prioritizing batches that expire soonest
   * 2. Using full batches when possible to minimize fragmentation
   * 3. Stopping when target quantity is reached
   *
   * @param targetQty - The target quantity to allocate across batches
   *
   * @example
   * ```typescript
   * // Auto-allocate 1950 kg across available batches
   * autoAllocateBatches(1950);
   * // Result: Batch-1 (500kg, expires Jan 15) + Batch-2 (750kg, expires Jan 20) + Batch-3 (700kg, expires Feb 1)
   * ```
   */
  const autoAllocateBatches = (targetQty: number) => {
    const newSelections: Record<string, number> = {};
    let remainingQty = targetQty;

    // FIFO allocation - use batches in expiry order
    for (const batch of availableBatches) {
      if (remainingQty <= 0) break;

      const quantityToUse = Math.min(remainingQty, batch.quantity);
      newSelections[batch.id] = quantityToUse;
      remainingQty -= quantityToUse;
    }

    setSelectedBatches(newSelections);
    notifyParent(newSelections);
  };

  const handleQuantityChange = (batchId: string, quantity: number) => {
    if (disabled) return;

    const batch = availableBatches.find(b => b.id === batchId);
    if (!batch) return;

    // Validate quantity doesn't exceed available
    const validQuantity = Math.max(0, Math.min(quantity, batch.quantity));
    
    const newSelections = {
      ...selectedBatches,
      [batchId]: validQuantity
    };

    // Remove zero quantities
    if (validQuantity === 0) {
      delete newSelections[batchId];
    }

    setSelectedBatches(newSelections);
    notifyParent(newSelections);
  };

  const notifyParent = useCallback((selections: Record<string, number>) => {
    const batchSelections: BatchSelection[] = Object.entries(selections)
      .filter(([_, qty]) => qty > 0)
      .map(([batchId, quantityToUse]) => {
        const batch = availableBatches.find(b => b.id === batchId)!;
        return { batchId, quantityToUse, batch };
      });

    const totalQuantity = batchSelections.reduce((sum, sel) => sum + sel.quantityToUse, 0);
    onBatchesSelected(batchSelections, totalQuantity);
  }, [availableBatches, onBatchesSelected]);

  // Get current batch selections for validation
  const currentSelections: BatchSelection[] = Object.entries(selectedBatches)
    .filter(([_, qty]) => qty > 0)
    .map(([batchId, quantityToUse]) => {
      const batch = availableBatches.find(b => b.id === batchId)!;
      return { batchId, quantityToUse, batch };
    });

  // Validate current selections
  const validation = useBatchValidation(currentSelections, targetQuantity);

  const getTotalSelected = () => {
    return Object.values(selectedBatches).reduce((sum, qty) => sum + qty, 0);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString();
  };

  const getBatchStatusColor = (batch: Batch) => {
    if (batch.batch_metadata?.is_expiring_soon) return 'border-amber-300 bg-amber-50';
    if (selectedBatches[batch.id] > 0) return 'border-blue-300 bg-blue-50';
    return 'border-gray-200 bg-white';
  };

  const getBatchStatusIcon = (batch: Batch) => {
    if (batch.batch_metadata?.is_expiring_soon) {
      return <AlertTriangle className="h-4 w-4 text-amber-500" />;
    }
    if (selectedBatches[batch.id] > 0) {
      return <CheckCircle className="h-4 w-4 text-blue-500" />;
    }
    return <Package className="h-4 w-4 text-gray-400" />;
  };

  if (isLoading) {
    return (
      <div className={`space-y-4 ${className}`}>
        <h4 className="text-lg font-medium text-gray-900 flex items-center space-x-2">
          <Package className="h-5 w-5" />
          <span>Available Inventory</span>
        </h4>
        <div className="animate-pulse space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-20 bg-gray-200 rounded-lg"></div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className={`space-y-4 ${className}`}>
      <div className="flex items-center justify-between">
        <h4 className="text-lg font-medium text-gray-900 flex items-center space-x-2">
          <Package className="h-5 w-5" />
          <span>Select from Available Inventory</span>
        </h4>
        <div className="text-sm text-gray-600">
          Total Selected: <span className="font-medium">{getTotalSelected().toFixed(3)} kg</span>
        </div>
      </div>

      {availableBatches.length === 0 ? (
        <div className="text-center py-8 text-gray-500">
          <Package className="h-12 w-12 mx-auto mb-4 text-gray-300" />
          <p>No available inventory for this product</p>
        </div>
      ) : (
        <div className="space-y-3 max-h-96 overflow-y-auto">
          {availableBatches.map((batch) => (
            <div
              key={batch.id}
              className={`border rounded-lg p-4 transition-colors ${getBatchStatusColor(batch)}`}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-2 mb-2">
                    {getBatchStatusIcon(batch)}
                    <span className="font-medium text-gray-900">{batch.batch_id}</span>
                    {batch.batch_metadata?.is_expiring_soon && (
                      <span className="text-xs bg-amber-100 text-amber-800 px-2 py-1 rounded-full">
                        Expires Soon
                      </span>
                    )}
                  </div>
                  
                  <div className="grid grid-cols-2 gap-4 text-sm text-gray-600 mb-3">
                    <div className="flex items-center space-x-1">
                      <Package className="h-3 w-3" />
                      <span>Available: {batch.quantity.toFixed(3)} {batch.unit}</span>
                    </div>
                    {batch.expiry_date && (
                      <div className="flex items-center space-x-1">
                        <Calendar className="h-3 w-3" />
                        <span>Expires: {formatDate(batch.expiry_date)}</span>
                      </div>
                    )}
                    {batch.location_name && (
                      <div className="flex items-center space-x-1">
                        <MapPin className="h-3 w-3" />
                        <span>{batch.location_name}</span>
                      </div>
                    )}
                    {batch.facility_code && (
                      <div className="flex items-center space-x-1">
                        <Info className="h-3 w-3" />
                        <span>Facility: {batch.facility_code}</span>
                      </div>
                    )}
                  </div>
                </div>

                <div className="ml-4">
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Quantity to Use
                  </label>
                  <div className="flex items-center space-x-2">
                    <input
                      type="number"
                      min="0"
                      max={batch.quantity}
                      step="0.001"
                      value={selectedBatches[batch.id] || 0}
                      onChange={(e) => handleQuantityChange(batch.id, parseFloat(e.target.value) || 0)}
                      disabled={disabled}
                      className="w-24 px-2 py-1 border border-gray-300 rounded text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100"
                    />
                    <span className="text-sm text-gray-500">{batch.unit}</span>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Validation Display */}
      {currentSelections.length > 0 && (
        <BatchValidationDisplay
          validation={validation}
          targetQuantity={targetQuantity}
          className="mt-4"
        />
      )}
    </div>
  );
};

export default BatchInventorySelector;
