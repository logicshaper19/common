import React, { useState, useEffect } from 'react';
import { CheckIcon, MapPinIcon, CalendarIcon, DocumentTextIcon, XMarkIcon, PlusIcon } from '@heroicons/react/24/outline';
import { Button } from '../ui/Button';
import { Card, CardHeader, CardBody } from '../ui/Card';
import DataTable from '../ui/DataTable';
import Modal from '../ui/Modal';
import { Badge } from '../ui/Badge';
import { useToast } from '../../contexts/ToastContext';
import { harvestApi, HarvestBatch } from '../../services/harvestApi';

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
    setSelectedQuantity(Math.min(requiredQuantity, batch.quantity));
    setShowBatchDetails(true);
  };

  // Handle quantity change
  const handleQuantityChange = (quantity: number) => {
    if (selectedBatch) {
      const maxQuantity = Math.min(requiredQuantity, selectedBatch.quantity);
      setSelectedQuantity(Math.min(quantity, maxQuantity));
    }
  };

  // Handle batch confirmation
  const handleConfirmBatch = () => {
    if (selectedBatch && selectedQuantity > 0) {
      onSelectBatch(selectedBatch, selectedQuantity);
      onClose();
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
                        <label className="text-sm font-medium text-gray-500">Required Quantity</label>
                        <p className="text-gray-900">{requiredQuantity.toLocaleString()} {requiredUnit}</p>
                      </div>
                      <div>
                        <label className="text-sm font-medium text-gray-500">Selected Quantity</label>
                        <p className="text-gray-900">{selectedQuantity.toLocaleString()} {requiredUnit}</p>
                      </div>
                      {selectedBatch && selectedBatch.quantity < requiredQuantity && (
                        <div>
                          <label className="text-sm font-medium text-gray-500">Remaining Balance</label>
                          <p className="text-gray-900 font-medium text-amber-600">
                            {(requiredQuantity - selectedQuantity).toLocaleString()} {requiredUnit}
                          </p>
                        </div>
                      )}
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
                          max={Math.min(requiredQuantity, selectedBatch.quantity)}
                          value={selectedQuantity}
                          onChange={(e) => handleQuantityChange(parseInt(e.target.value) || 0)}
                          className="w-32 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                        <span className="text-sm text-gray-500">
                          of {Math.min(requiredQuantity || 0, selectedBatch.quantity || 0).toLocaleString()} {requiredUnit}
                        </span>
                      </div>
                    </div>
                  </CardBody>
                </Card>

                {/* Remaining Balance Options */}
                {selectedBatch && selectedBatch.quantity < requiredQuantity && (
                  <Card>
                    <CardHeader title="Remaining Balance Options" />
                    <CardBody>
                      <div className="space-y-4">
                        <p className="text-sm text-gray-600">
                          You still need <span className="font-medium text-amber-600">{(requiredQuantity - selectedQuantity).toLocaleString()} {requiredUnit}</span> to fulfill this purchase order.
                        </p>
                        <div className="space-y-3">
                          <div className="flex items-center space-x-3">
                            <input
                              type="radio"
                              id="partial-fulfillment"
                              name="balance-option"
                              value="partial"
                              defaultChecked
                              className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300"
                            />
                            <label htmlFor="partial-fulfillment" className="text-sm text-gray-700">
                              <span className="font-medium">Partial Fulfillment</span> - Confirm with available quantity only
                            </label>
                          </div>
                          <div className="flex items-center space-x-3">
                            <input
                              type="radio"
                              id="create-new-batch"
                              name="balance-option"
                              value="create"
                              className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300"
                            />
                            <label htmlFor="create-new-batch" className="text-sm text-gray-700">
                              <span className="font-medium">Create New Batch</span> - Declare additional harvest for remaining quantity
                            </label>
                          </div>
                        </div>
                      </div>
                    </CardBody>
                  </Card>
                )}

                {/* Action Buttons */}
                <div className="flex justify-end space-x-3">
                  <Button
                    onClick={() => setShowBatchDetails(false)}
                    variant="secondary"
                    disabled={isLoading}
                  >
                    Back to Selection
                  </Button>
                  {selectedBatch && selectedBatch.quantity < requiredQuantity && (
                    <Button
                      onClick={() => {
                        // TODO: Navigate to harvest declaration form
                        showToast({
                          type: 'info',
                          title: 'Create New Batch',
                          message: 'This would open the harvest declaration form to create a new batch for the remaining quantity.'
                        });
                      }}
                      variant="outline"
                      disabled={isLoading}
                    >
                      <PlusIcon className="h-4 w-4 mr-2" />
                      Create New Batch
                    </Button>
                  )}
                  <Button
                    onClick={handleConfirmBatch}
                    variant="primary"
                    disabled={isLoading || selectedQuantity <= 0}
                    isLoading={isLoading}
                  >
                    <CheckIcon className="h-4 w-4 mr-2" />
                    {selectedBatch && selectedBatch.quantity < requiredQuantity 
                      ? 'Confirm Partial Fulfillment' 
                      : 'Confirm Batch Selection'
                    }
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
                    onAction: () => {
                      // This would navigate to harvest declaration
                      console.log('Navigate to harvest declaration');
                    }
                  }}
                />
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default BatchSelectionModal;
