import React, { useState, useEffect } from 'react';
import { CheckIcon, MapPinIcon, CalendarIcon, DocumentTextIcon, XMarkIcon } from '@heroicons/react/24/outline';
import { Button } from '../ui/Button';
import { Card, CardHeader, CardBody } from '../ui/Card';
import DataTable from '../ui/DataTable';
import Modal from '../ui/Modal';
import { Badge } from '../ui/Badge';
import { useToast } from '../../contexts/ToastContext';

interface HarvestBatch {
  id: string;
  batch_id: string;
  harvest_date: string;
  farm_name: string;
  farm_id: string;
  plantation_type: string;
  quantity: number;
  unit: string;
  available_quantity: number;
  location_coordinates?: {
    latitude: number;
    longitude: number;
  };
  certifications: string[];
  quality_parameters: Record<string, any>;
  origin_data: Record<string, any>;
  status: 'active' | 'consumed' | 'expired';
  created_at: string;
}

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
      // TODO: Replace with actual API call
      // const response = await harvestApi.getAvailableHarvestBatches(productId);
      // setHarvestBatches(response.data);
      
      // Mock data for now
      setHarvestBatches([
        {
          id: '1',
          batch_id: 'H-20241201-001',
          harvest_date: '2024-12-01',
          farm_name: 'Sumatra Smallholder Farm A',
          farm_id: 'FARM-001',
          plantation_type: 'smallholder',
          quantity: 1000,
          unit: 'KGM',
          available_quantity: 1000,
          location_coordinates: {
            latitude: -0.7893,
            longitude: 100.3491
          },
          certifications: ['RSPO', 'NDPE'],
          quality_parameters: {
            oil_content: 22.5,
            moisture_content: 18.2
          },
          origin_data: {
            harvest_date: '2024-12-01',
            farm_information: {
              farm_name: 'Sumatra Smallholder Farm A',
              farm_id: 'FARM-001',
              plantation_type: 'smallholder',
              cultivation_methods: ['sustainable', 'organic']
            },
            geographic_coordinates: {
              latitude: -0.7893,
              longitude: 100.3491
            },
            certifications: ['RSPO', 'NDPE'],
            processing_notes: 'Harvested in optimal conditions'
          },
          status: 'active',
          created_at: '2024-12-01T08:00:00Z'
        },
        {
          id: '2',
          batch_id: 'H-20241128-002',
          harvest_date: '2024-11-28',
          farm_name: 'Sumatra Smallholder Farm B',
          farm_id: 'FARM-002',
          plantation_type: 'smallholder',
          quantity: 750,
          unit: 'KGM',
          available_quantity: 750,
          location_coordinates: {
            latitude: -0.8123,
            longitude: 100.3123
          },
          certifications: ['RSPO', 'Organic'],
          quality_parameters: {
            oil_content: 24.1,
            moisture_content: 16.8
          },
          origin_data: {
            harvest_date: '2024-11-28',
            farm_information: {
              farm_name: 'Sumatra Smallholder Farm B',
              farm_id: 'FARM-002',
              plantation_type: 'smallholder',
              cultivation_methods: ['organic', 'biodiversity']
            },
            geographic_coordinates: {
              latitude: -0.8123,
              longitude: 100.3123
            },
            certifications: ['RSPO', 'Organic'],
            processing_notes: 'Organic harvest with biodiversity protection'
          },
          status: 'active',
          created_at: '2024-11-28T10:30:00Z'
        }
      ]);
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
    setSelectedQuantity(Math.min(requiredQuantity, batch.available_quantity));
    setShowBatchDetails(true);
  };

  // Handle quantity change
  const handleQuantityChange = (quantity: number) => {
    if (selectedBatch) {
      const maxQuantity = Math.min(requiredQuantity, selectedBatch.available_quantity);
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
      render: (batch: HarvestBatch) => (
        <div className="font-medium text-gray-900">{batch.batch_id}</div>
      )
    },
    {
      key: 'harvest_date',
      label: 'Harvest Date',
      render: (batch: HarvestBatch) => (
        <div className="flex items-center space-x-2">
          <CalendarIcon className="h-4 w-4 text-gray-400" />
          <span>{new Date(batch.harvest_date).toLocaleDateString()}</span>
        </div>
      )
    },
    {
      key: 'farm_name',
      label: 'Farm',
      render: (batch: HarvestBatch) => (
        <div>
          <div className="font-medium text-gray-900">{batch.farm_name}</div>
          <div className="text-sm text-gray-500">ID: {batch.farm_id}</div>
        </div>
      )
    },
    {
      key: 'location',
      label: 'Location',
      render: (batch: HarvestBatch) => (
        <div className="flex items-center space-x-2">
          <MapPinIcon className="h-4 w-4 text-gray-400" />
          <span className="text-sm">
            {batch.location_coordinates 
              ? `${batch.location_coordinates.latitude.toFixed(4)}, ${batch.location_coordinates.longitude.toFixed(4)}`
              : 'No coordinates'
            }
          </span>
        </div>
      )
    },
    {
      key: 'available_quantity',
      label: 'Available',
      render: (batch: HarvestBatch) => (
        <div className="text-right">
          <div className="font-medium">{batch.available_quantity.toLocaleString()}</div>
          <div className="text-sm text-gray-500">{batch.unit}</div>
        </div>
      )
    },
    {
      key: 'certifications',
      label: 'Certifications',
      render: (batch: HarvestBatch) => (
        <div className="flex flex-wrap gap-1">
          {batch.certifications.slice(0, 2).map((cert) => (
            <Badge key={cert} variant="secondary" size="sm">
              {cert}
            </Badge>
          ))}
          {batch.certifications.length > 2 && (
            <Badge variant="secondary" size="sm">
              +{batch.certifications.length - 2}
            </Badge>
          )}
        </div>
      )
    },
    {
      key: 'actions',
      label: 'Actions',
      render: (batch: HarvestBatch) => (
        <Button
          onClick={() => handleBatchSelect(batch)}
          variant="outline"
          size="sm"
          disabled={batch.available_quantity < requiredQuantity}
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
                    Required: {requiredQuantity.toLocaleString()} {requiredUnit}
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
                  <CardHeader title={`Selected Batch: ${selectedBatch.batch_id}`} />
                  <CardBody className="space-y-4">
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="text-sm font-medium text-gray-500">Farm Name</label>
                        <p className="text-gray-900">{selectedBatch.farm_name}</p>
                      </div>
                      <div>
                        <label className="text-sm font-medium text-gray-500">Harvest Date</label>
                        <p className="text-gray-900">{new Date(selectedBatch.harvest_date).toLocaleDateString()}</p>
                      </div>
                      <div>
                        <label className="text-sm font-medium text-gray-500">Available Quantity</label>
                        <p className="text-gray-900">{selectedBatch.available_quantity.toLocaleString()} {selectedBatch.unit}</p>
                      </div>
                      <div>
                        <label className="text-sm font-medium text-gray-500">Certifications</label>
                        <div className="flex flex-wrap gap-1">
                          {selectedBatch.certifications.map((cert) => (
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
                          max={Math.min(requiredQuantity, selectedBatch.available_quantity)}
                          value={selectedQuantity}
                          onChange={(e) => handleQuantityChange(parseInt(e.target.value) || 0)}
                          className="w-32 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                        <span className="text-sm text-gray-500">
                          of {Math.min(requiredQuantity, selectedBatch.available_quantity).toLocaleString()} {requiredUnit}
                        </span>
                      </div>
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
                  <Button
                    onClick={handleConfirmBatch}
                    variant="primary"
                    disabled={isLoading || selectedQuantity <= 0}
                    isLoading={isLoading}
                  >
                    <CheckIcon className="h-4 w-4 mr-2" />
                    Confirm Batch Selection
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
