import React, { useState, useEffect } from 'react';
import { CheckIcon, MapPinIcon, CalendarIcon, DocumentTextIcon, XMarkIcon, PlusIcon } from '@heroicons/react/24/outline';
import { Button } from '../ui/Button';
import { Card, CardHeader, CardBody } from '../ui/Card';
import DataTable from '../ui/DataTable';
import Modal from '../ui/Modal';
import { Badge } from '../ui/Badge';
import { useToast } from '../../contexts/ToastContext';
import { harvestApi, HarvestBatch } from '../../services/harvestApi';
import HarvestDeclarationForm from '../harvest/HarvestDeclarationForm';

// Using HarvestBatch from harvestApi service

interface BatchSelectionModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSelectBatch: (batch: HarvestBatch, selectedQuantity: number) => void;
  productId: string;
  requiredQuantity: number;
  requiredUnit: string;
  isLoading?: boolean;
}

const BatchSelectionModal: React.FC<BatchSelectionModalProps> = ({
  isOpen,
  onClose,
  onSelectBatch,
  productId,
  requiredQuantity,
  requiredUnit,
  isLoading = false
}) => {
  const { showToast } = useToast();
  
  // State
  const [harvestBatches, setHarvestBatches] = useState<HarvestBatch[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedBatch, setSelectedBatch] = useState<HarvestBatch | null>(null);
  const [selectedQuantity, setSelectedQuantity] = useState<number>(0);
  const [showBatchDetails, setShowBatchDetails] = useState(false);
  
  // Multi-batch allocation state
  const [allocatedBatches, setAllocatedBatches] = useState<Array<{
    batch: HarvestBatch;
    quantity: number;
  }>>([]);
  const [remainingQuantity, setRemainingQuantity] = useState<number>(requiredQuantity);
  
  // Harvest declaration modal state
  const [showHarvestModal, setShowHarvestModal] = useState(false);

  // Load available harvest batches
  useEffect(() => {
    if (isOpen) {
      loadHarvestBatches();
    }
  }, [isOpen, productId]);

  const loadHarvestBatches = async () => {
    try {
      setLoading(true);
      console.log('🔍 Loading harvest batches with params:', {
        productId,
        requiredQuantity,
        requiredUnit
      });
      
      // Get available harvest batches from the API
      const batches = await harvestApi.getAvailableHarvestBatches(
        productId,
        requiredQuantity,
        requiredUnit
      );
      
      console.log('📦 Received batches:', batches);
      console.log('📦 Batch count:', batches.length);
      
      // Debug: Log the first batch in detail
      if (batches.length > 0) {
        console.log('🔍 First batch details:', {
          id: batches[0].id,
          batch_id: batches[0].batch_id,
          quantity: batches[0].quantity,
          unit: batches[0].unit,
          production_date: batches[0].production_date,
          location_name: batches[0].location_name,
          origin_data: batches[0].origin_data,
          certifications: batches[0].certifications
        });
      }
      
      setHarvestBatches(batches);
      
      if (batches.length === 0) {
        showToast({
          type: 'info',
          title: 'No Harvest Batches Available',
          message: 'No harvest batches found for this product. Please create a harvest batch first.'
        });
      } else {
        console.log('✅ Successfully loaded', batches.length, 'harvest batches');
      }
    } catch (error) {
      console.error('Error loading harvest batches:', error);
      showToast({ title: 'Error', message: 'Failed to load available harvest batches', type: 'error' });
    } finally {
      setLoading(false);
    }
  };

  // Handle batch selection
  const handleBatchSelect = (batch: HarvestBatch) => {
    setSelectedBatch(batch);
    setSelectedQuantity(Math.min(remainingQuantity, batch.quantity));
    setShowBatchDetails(true);
  };

  // Handle adding batch to allocation
  const handleAddToAllocation = () => {
    if (!selectedBatch || selectedQuantity <= 0) return;

    const newAllocation = {
      batch: selectedBatch,
      quantity: selectedQuantity
    };

    setAllocatedBatches(prev => [...prev, newAllocation]);
    setRemainingQuantity(prev => prev - selectedQuantity);
    
    // Remove the allocated batch from available batches
    setHarvestBatches(prev => prev.filter(b => b.id !== selectedBatch.id));
    
    // Reset selection
    setSelectedBatch(null);
    setSelectedQuantity(0);
    setShowBatchDetails(false);

    showToast({
      type: 'success',
      title: 'Batch Added',
      message: `Added ${selectedQuantity.toLocaleString()} ${requiredUnit} from ${selectedBatch.batch_id}`
    });
  };

  // Handle quantity change
  const handleQuantityChange = (quantity: number) => {
    if (selectedBatch) {
      const maxQuantity = Math.min(remainingQuantity, selectedBatch.quantity);
      setSelectedQuantity(Math.min(quantity, maxQuantity));
    }
  };

  // Handle final confirmation of all allocations
  const handleConfirmAllocation = () => {
    if (allocatedBatches.length === 0) return;
    
    // For now, we'll use the first batch as the primary batch
    // In a more sophisticated implementation, this would handle multiple batches
    const primaryBatch = allocatedBatches[0];
    const totalQuantity = allocatedBatches.reduce((sum, allocation) => sum + allocation.quantity, 0);
    
    onSelectBatch(primaryBatch.batch, totalQuantity);
    onClose();
  };

  // Handle harvest declaration submission
  const handleHarvestSubmit = async (harvestData: any) => {
    try {
      setLoading(true);
      
      // Import harvestApi to declare the harvest
      const { harvestApi } = await import('../../services/harvestApi');
      
      // Declare the harvest
      const newBatch = await harvestApi.declareHarvest(harvestData);
      
      showToast({
        type: 'success',
        title: 'Harvest Declared',
        message: `New batch ${newBatch.batch_id} created successfully`
      });
      
      // Close the harvest modal
      setShowHarvestModal(false);
      
      // Reload harvest batches to include the new one
      await loadHarvestBatches();
      
    } catch (error) {
      console.error('Error declaring harvest:', error);
      showToast({
        type: 'error',
        title: 'Error',
        message: 'Failed to declare harvest. Please try again.'
      });
    } finally {
      setLoading(false);
    }
  };

  // Table columns
  const batchColumns = [
    {
      key: 'batch_id',
      label: 'Batch ID',
      render: (value: any, batch: HarvestBatch) => {
        console.log('🔍 Batch ID render - value:', value, 'batch:', batch);
        return (
          <div className="font-medium text-gray-900">{batch?.batch_id || 'N/A'}</div>
        );
      }
    },
    {
      key: 'harvest_date',
      label: 'Harvest Date',
      render: (value: any, batch: HarvestBatch) => (
        <div className="flex items-center space-x-2">
          <CalendarIcon className="h-4 w-4 text-gray-400" />
          <span>{batch ? new Date(batch.origin_data?.harvest_date || batch.production_date || batch.created_at).toLocaleDateString() : 'N/A'}</span>
        </div>
      )
    },
    {
      key: 'farm_name',
      label: 'Farm',
      render: (value: any, batch: HarvestBatch) => (
        <div>
          <div className="font-medium text-gray-900">{batch ? (batch.origin_data?.farm_information?.farm_name || batch.location_name || 'N/A') : 'N/A'}</div>
          <div className="text-sm text-gray-500">ID: {batch ? (batch.origin_data?.farm_information?.farm_id || batch.facility_code || batch.batch_id || 'N/A') : 'N/A'}</div>
        </div>
      )
    },
    {
      key: 'location',
      label: 'Location',
      render: (value: any, batch: HarvestBatch) => (
        <div className="flex items-center space-x-2">
          <MapPinIcon className="h-4 w-4 text-gray-400" />
          <span className="text-sm">
            {batch ? (batch.origin_data?.farm_information?.farm_name || batch.location_name || 'N/A') : 'N/A'}
          </span>
        </div>
      )
    },
    {
      key: 'quantity',
      label: 'Available',
      render: (value: any, batch: HarvestBatch) => (
        <div className="text-right">
          <div className="font-medium">{(batch.quantity || 0).toLocaleString()}</div>
          <div className="text-sm text-gray-500">{batch.unit || 'N/A'}</div>
        </div>
      )
    },
    {
      key: 'certifications',
      label: 'Certifications',
      render: (value: any, batch: HarvestBatch) => (
        <div className="flex flex-wrap gap-1">
          {batch ? (
            <>
              {(batch.certifications || []).slice(0, 2).map((cert) => (
                <Badge key={cert} variant="secondary" size="sm">
                  {cert}
                </Badge>
              ))}
              {batch.certifications && batch.certifications.length > 2 && (
                <Badge variant="secondary" size="sm">
                  +{batch.certifications.length - 2}
                </Badge>
              )}
            </>
          ) : (
            <span className="text-gray-500">N/A</span>
          )}
        </div>
      )
    },
    {
      key: 'actions',
      label: 'Actions',
      render: (value: any, batch: HarvestBatch) => (
        <Button
          onClick={() => batch && handleBatchSelect(batch)}
          variant="outline"
          size="sm"
          disabled={!batch || batch.quantity <= 0}
        >
          Select Batch
        </Button>
      )
    }
  ];

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex items-center justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
        <div className="fixed inset-0 bg-neutral-500 bg-opacity-75 transition-opacity" onClick={onClose} />

        <div className="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-6xl sm:w-full">
          <div className="bg-white px-4 pt-5 pb-4 sm:p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-medium text-neutral-900">
                Select Harvest Batch for Purchase Order
              </h3>
              <button
                onClick={onClose}
                className="text-neutral-400 hover:text-neutral-600"
              >
                <XMarkIcon className="h-6 w-6" />
              </button>
            </div>

            <div className="mb-4 p-4 bg-blue-50 rounded-lg">
              <div className="flex items-center space-x-2">
                <DocumentTextIcon className="h-5 w-5 text-blue-600" />
                <div>
                  <p className="text-sm font-medium text-blue-900">
                    Required: {(requiredQuantity || 0).toLocaleString()} {requiredUnit}
                  </p>
                  <p className="text-sm text-blue-700">
                    Select a harvest batch with origin data to fulfill this purchase order
                  </p>
                </div>
              </div>
            </div>

            {/* Allocation Progress */}
            {allocatedBatches.length > 0 && (
              <div className="mb-6 p-4 bg-gray-50 rounded-lg">
                <div className="flex items-center justify-between mb-2">
                  <h3 className="text-sm font-medium text-gray-900">Allocation Progress</h3>
                  <span className="text-sm text-gray-600">
                    {((requiredQuantity - remainingQuantity) / requiredQuantity * 100).toFixed(0)}% Complete
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2 mb-3">
                  <div 
                    className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                    style={{ width: `${((requiredQuantity - remainingQuantity) / requiredQuantity) * 100}%` }}
                  ></div>
                </div>
                <div className="flex justify-between text-sm text-gray-600">
                  <span>Allocated: {(requiredQuantity - remainingQuantity).toLocaleString()} {requiredUnit}</span>
                  <span>Remaining: {remainingQuantity.toLocaleString()} {requiredUnit}</span>
                </div>
              </div>
            )}

            {/* Allocated Batches */}
            {allocatedBatches.length > 0 && (
              <div className="mb-6">
                <h3 className="text-sm font-medium text-gray-900 mb-3">Allocated Batches</h3>
                <div className="space-y-2">
                  {allocatedBatches.map((allocation, index) => (
                    <div key={index} className="flex items-center justify-between p-3 bg-green-50 border border-green-200 rounded-lg">
                      <div className="flex items-center space-x-3">
                        <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                        <div>
                          <p className="text-sm font-medium text-gray-900">{allocation.batch.batch_id}</p>
                          <p className="text-xs text-gray-600">
                            {allocation.batch.origin_data?.farm_information?.farm_name || allocation.batch.location_name || 'Unknown Farm'}
                          </p>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className="text-sm font-medium text-gray-900">
                          {allocation.quantity.toLocaleString()} {requiredUnit}
                        </p>
                        <button
                          onClick={() => {
                            setAllocatedBatches(prev => prev.filter((_, i) => i !== index));
                            setRemainingQuantity(prev => prev + allocation.quantity);
                            setHarvestBatches(prev => [...prev, allocation.batch]);
                          }}
                          className="text-xs text-red-600 hover:text-red-800"
                        >
                          Remove
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {showBatchDetails && selectedBatch ? (
              <div className="space-y-6">
                {/* Selected Batch Details */}
                <Card>
                  <CardHeader title={`Selected Batch: ${selectedBatch?.batch_id || 'N/A'}`} />
                  <CardBody className="space-y-4">
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="text-sm font-medium text-gray-500">Farm Name</label>
                        <p className="text-gray-900">{selectedBatch?.origin_data?.farm_information?.farm_name || selectedBatch?.location_name || 'N/A'}</p>
                      </div>
                      <div>
                        <label className="text-sm font-medium text-gray-500">Harvest Date</label>
                        <p className="text-gray-900">{selectedBatch ? new Date(selectedBatch.origin_data?.harvest_date || selectedBatch.production_date || selectedBatch.created_at).toLocaleDateString() : 'N/A'}</p>
                      </div>
                      <div>
                        <label className="text-sm font-medium text-gray-500">Available Quantity</label>
                        <p className="text-gray-900">{selectedBatch ? `${(selectedBatch.quantity || 0).toLocaleString()} ${selectedBatch.unit || 'N/A'}` : 'N/A'}</p>
                      </div>
                      <div>
                        <label className="text-sm font-medium text-gray-500">Remaining to Allocate</label>
                        <p className="text-gray-900 font-medium text-blue-600">{remainingQuantity.toLocaleString()} {requiredUnit}</p>
                      </div>
                      <div>
                        <label className="text-sm font-medium text-gray-500">Certifications</label>
                        <div className="flex flex-wrap gap-1">
                          {(selectedBatch?.certifications || []).map((cert) => (
                            <Badge key={cert} variant="primary" size="sm">
                              {cert}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    </div>

                    {/* Quantity Selection */}
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Quantity to Allocate
                      </label>
                      <div className="flex items-center space-x-4">
                        <input
                          type="number"
                          min="1"
                          max={Math.min(remainingQuantity, selectedBatch.quantity)}
                          value={selectedQuantity}
                          onChange={(e) => handleQuantityChange(parseInt(e.target.value) || 0)}
                          className="w-32 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                        <span className="text-sm text-gray-500">
                          of {Math.min(remainingQuantity, selectedBatch.quantity).toLocaleString()} {requiredUnit}
                        </span>
                      </div>
                      <div className="mt-2 flex space-x-2">
                        <button
                          onClick={() => setSelectedQuantity(Math.min(remainingQuantity, selectedBatch.quantity))}
                          className="text-xs text-blue-600 hover:text-blue-800"
                        >
                          Use All Available
                        </button>
                        <button
                          onClick={() => setSelectedQuantity(remainingQuantity)}
                          className="text-xs text-blue-600 hover:text-blue-800"
                        >
                          Fill Remaining
                        </button>
                      </div>
                    </div>
                  </CardBody>
                </Card>

                {/* Add to Allocation */}
                <Card>
                  <CardBody>
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm font-medium text-gray-900">
                          Add {selectedQuantity.toLocaleString()} {requiredUnit} to allocation
                        </p>
                        {remainingQuantity - selectedQuantity > 0 && (
                          <p className="text-xs text-gray-600">
                            {remainingQuantity - selectedQuantity} {requiredUnit} still needed
                          </p>
                        )}
                      </div>
                      <Button
                        onClick={handleAddToAllocation}
                        variant="primary"
                        disabled={selectedQuantity <= 0}
                      >
                        Add to Allocation
                      </Button>
                    </div>
                  </CardBody>
                </Card>

                {/* Action Buttons */}
                <div className="flex justify-end space-x-3">
                  <Button
                    onClick={() => setShowBatchDetails(false)}
                    variant="secondary"
                    disabled={isLoading}
                  >
                    Back to Selection
                  </Button>
                </div>
              </div>
            ) : (
              <div>
                {/* Available Batches Table */}
                <DataTable
                  title="Available Harvest Batches"
                  data={harvestBatches}
                  columns={batchColumns}
                  searchPlaceholder="Search batch IDs, farm names..."
                  emptyState={{
                    icon: DocumentTextIcon,
                    title: 'No harvest batches available',
                    description: 'No harvest batches are available for this product. Declare a harvest first.',
                    actionLabel: 'Declare New Harvest',
                    onAction: () => setShowHarvestModal(true)
                  }}
                />
              </div>
            )}

            {/* Final Confirmation and Completion Options */}
            {allocatedBatches.length > 0 && (
              <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                <div className="flex items-center justify-between mb-4">
                  <div>
                    <h3 className="text-sm font-medium text-blue-900">Ready to Confirm</h3>
                    <p className="text-sm text-blue-700">
                      {allocatedBatches.length} batch{allocatedBatches.length > 1 ? 'es' : ''} allocated
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-medium text-blue-900">
                      Total: {(requiredQuantity - remainingQuantity).toLocaleString()} {requiredUnit}
                    </p>
                    {remainingQuantity > 0 && (
                      <p className="text-xs text-blue-600">
                        {remainingQuantity.toLocaleString()} {requiredUnit} remaining
                      </p>
                    )}
                  </div>
                </div>
                
                <div className="flex items-center justify-between">
                  <div className="flex space-x-3">
                    {remainingQuantity > 0 && (
                      <Button
                        onClick={() => setShowHarvestModal(true)}
                        variant="outline"
                        size="sm"
                      >
                        <PlusIcon className="h-4 w-4 mr-2" />
                        Create Batch for Remaining
                      </Button>
                    )}
                    <Button
                      onClick={() => {
                        const totalAllocated = allocatedBatches.reduce((sum, allocation) => sum + allocation.quantity, 0);
                        showToast({
                          type: 'info',
                          title: 'Use All Available',
                          message: `This would allocate all remaining available inventory (${totalAllocated.toLocaleString()} ${requiredUnit} total).`
                        });
                      }}
                      variant="outline"
                      size="sm"
                    >
                      Use All Available
                    </Button>
                  </div>
                  
                  <Button
                    onClick={handleConfirmAllocation}
                    variant="primary"
                    disabled={isLoading}
                    isLoading={isLoading}
                  >
                    <CheckIcon className="h-4 w-4 mr-2" />
                    {remainingQuantity > 0 ? 'Confirm Partial Fulfillment' : 'Confirm Complete Fulfillment'}
                  </Button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Harvest Declaration Modal */}
      {showHarvestModal && (
        <Modal
          isOpen={showHarvestModal}
          onClose={() => setShowHarvestModal(false)}
          title="Declare New Harvest"
          size="xl"
        >
          <HarvestDeclarationForm
            productType="fresh_fruit_bunches"
            onSubmit={handleHarvestSubmit}
            onCancel={() => setShowHarvestModal(false)}
            isLoading={loading}
          />
        </Modal>
      )}
    </div>
  );
};

export default BatchSelectionModal;
