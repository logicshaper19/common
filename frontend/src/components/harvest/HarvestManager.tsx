import React, { useState, useEffect } from 'react';
import { PlusIcon, DocumentTextIcon, MapPinIcon, CalendarIcon } from '@heroicons/react/24/outline';
import { Button } from '../ui/Button';
import { Card, CardHeader, CardBody } from '../ui/Card';
import DataTable from '../ui/DataTable';
import Modal from '../ui/Modal';
import { Badge } from '../ui/Badge';
import { useToast } from '../../contexts/ToastContext';
import HarvestDeclarationForm from './HarvestDeclarationForm';

interface HarvestBatch {
  id: string;
  batch_id: string;
  product_type: string;
  harvest_date: string;
  farm_name: string;
  farm_id: string;
  plantation_type: string;
  quantity: number;
  unit: string;
  location_coordinates?: {
    latitude: number;
    longitude: number;
  };
  certifications: string[];
  quality_parameters: Record<string, any>;
  status: 'active' | 'consumed' | 'expired';
  created_at: string;
}

interface HarvestManagerProps {
  companyId: string;
  className?: string;
}

const HarvestManager: React.FC<HarvestManagerProps> = ({
  companyId,
  className = ''
}) => {
  const { showToast } = useToast();
  
  // State
  const [harvestBatches, setHarvestBatches] = useState<HarvestBatch[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showViewModal, setShowViewModal] = useState(false);
  const [selectedBatch, setSelectedBatch] = useState<HarvestBatch | null>(null);

  // Load harvest batches only once on mount
  useEffect(() => {
    loadHarvestBatches();
  }, []); // Empty dependency array - only run once on mount

  const loadHarvestBatches = async () => {
    try {
      setLoading(true);
      // TODO: Replace with actual API call
      // const response = await harvestApi.getHarvestBatches(companyId);
      // setHarvestBatches(response.data);
      
      // Load initial mock data
      setHarvestBatches([
        {
          id: '1',
          batch_id: 'H-20241201-001',
          product_type: 'fresh_fruit_bunches',
          harvest_date: '2024-12-01',
          farm_name: 'Sumatra Smallholder Farm A',
          farm_id: 'FARM-001',
          plantation_type: 'smallholder',
          quantity: 1000,
          unit: 'KGM',
          location_coordinates: {
            latitude: -0.7893,
            longitude: 100.3491
          },
          certifications: ['RSPO', 'NDPE'],
          quality_parameters: {
            oil_content: 22.5,
            moisture_content: 18.2
          },
          status: 'active',
          created_at: '2024-12-01T08:00:00Z'
        },
        {
          id: '2',
          batch_id: 'H-20241128-002',
          product_type: 'fresh_fruit_bunches',
          harvest_date: '2024-11-28',
          farm_name: 'Sumatra Smallholder Farm B',
          farm_id: 'FARM-002',
          plantation_type: 'smallholder',
          quantity: 750,
          unit: 'KGM',
          location_coordinates: {
            latitude: -0.8123,
            longitude: 100.3123
          },
          certifications: ['RSPO', 'Organic'],
          quality_parameters: {
            oil_content: 24.1,
            moisture_content: 16.8
          },
          status: 'active',
          created_at: '2024-11-28T10:30:00Z'
        }
      ]);
    } catch (error) {
      console.error('Error loading harvest batches:', error);
      showToast({ title: 'Error', message: 'Failed to load harvest batches', type: 'error' });
    } finally {
      setLoading(false);
    }
  };

  // Handle harvest declaration submission
  const handleHarvestSubmit = async (harvestData: any) => {
    try {
      // TODO: Replace with actual API call
      // await harvestApi.createHarvestBatch(companyId, harvestData);
      
      // Mock success
      console.log('Creating harvest batch:', harvestData);
      
      // Add to local state
      const newBatch: HarvestBatch = {
        id: Date.now().toString(),
        batch_id: harvestData.batch_number,
        product_type: harvestData.product_type,
        harvest_date: harvestData.harvest_date,
        farm_name: harvestData.farm_information.farm_name,
        farm_id: harvestData.farm_information.farm_id,
        plantation_type: harvestData.farm_information.plantation_type,
        quantity: harvestData.quantity,
        unit: harvestData.unit,
        location_coordinates: harvestData.geographic_coordinates,
        certifications: harvestData.certifications,
        quality_parameters: harvestData.quality_parameters,
        status: 'active',
        created_at: new Date().toISOString()
      };
      
      setHarvestBatches(prev => [newBatch, ...prev]);
      
      setShowCreateModal(false);
      showToast({ title: 'Success', message: 'Harvest batch created successfully', type: 'success' });
    } catch (error) {
      console.error('Error creating harvest batch:', error);
      showToast({ title: 'Error', message: 'Failed to create harvest batch', type: 'error' });
    }
  };

  // Handle form cancellation
  const handleFormCancel = () => {
    setShowCreateModal(false);
    setSelectedBatch(null);
  };

  // Handle row click
  const handleRowClick = (batch: HarvestBatch) => {
    setSelectedBatch(batch);
    setShowViewModal(true);
  };

  // Table columns
  const harvestColumns = [
    {
      key: 'batch_id',
      label: 'Batch ID',
      render: (value: any, batch: HarvestBatch) => (
        <div className="font-medium text-gray-900">{batch?.batch_id || 'N/A'}</div>
      )
    },
    {
      key: 'product_type',
      label: 'Product Type',
      render: (value: any, batch: HarvestBatch) => (
        <div className="text-sm">
          <Badge variant="secondary" size="sm">
            {batch?.product_type ? batch.product_type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()) : 'N/A'}
          </Badge>
        </div>
      )
    },
    {
      key: 'harvest_date',
      label: 'Harvest Date',
      render: (value: any, batch: HarvestBatch) => (
        <div className="flex items-center space-x-2">
          <CalendarIcon className="h-4 w-4 text-gray-400" />
          <span>{batch?.harvest_date ? new Date(batch.harvest_date).toLocaleDateString() : 'N/A'}</span>
        </div>
      )
    },
    {
      key: 'farm_name',
      label: 'Farm',
      render: (value: any, batch: HarvestBatch) => (
        <div>
          <div className="font-medium text-gray-900">{batch?.farm_name || 'N/A'}</div>
          <div className="text-sm text-gray-500">ID: {batch?.farm_id || 'N/A'}</div>
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
            {batch?.location_coordinates 
              ? `${batch.location_coordinates.latitude.toFixed(4)}, ${batch.location_coordinates.longitude.toFixed(4)}`
              : 'No coordinates'
            }
          </span>
        </div>
      )
    },
    {
      key: 'quantity',
      label: 'Quantity',
      render: (value: any, batch: HarvestBatch) => (
        <div className="text-right">
          <div className="font-medium">{batch?.quantity?.toLocaleString() || 'N/A'}</div>
          <div className="text-sm text-gray-500">{batch?.unit || 'N/A'}</div>
        </div>
      )
    },
    {
      key: 'certifications',
      label: 'Certifications',
      render: (value: any, batch: HarvestBatch) => (
        <div className="flex flex-wrap gap-1">
          {batch?.certifications?.slice(0, 2).map((cert) => (
            <Badge key={cert} variant="secondary" size="sm">
              {cert}
            </Badge>
          )) || []}
          {batch?.certifications && batch.certifications.length > 2 && (
            <Badge variant="secondary" size="sm">
              +{batch.certifications.length - 2}
            </Badge>
          )}
        </div>
      )
    },
    {
      key: 'status',
      label: 'Status',
      render: (value: any, batch: HarvestBatch) => (
        <Badge 
          variant={batch?.status === 'active' ? 'success' : 'secondary'}
          size="sm"
        >
          {batch?.status || 'unknown'}
        </Badge>
      )
    }
  ];

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Production Tracking</h1>
          <p className="text-gray-600">Track harvest declarations and production batches</p>
        </div>
        <Button
          onClick={() => setShowCreateModal(true)}
          variant="primary"
          size="lg"
        >
          <PlusIcon className="h-5 w-5 mr-2" />
          Declare New Harvest
        </Button>
      </div>

      {/* Harvest Batches Table */}
      <DataTable
        title={`Harvest Batches (${harvestBatches.length})`}
        data={harvestBatches.filter(batch => batch != null)}
        columns={harvestColumns}
        searchPlaceholder="Search batch IDs, farm names, harvest dates..."
        statusFilterOptions={[
          { label: 'Active', value: 'active' },
          { label: 'Consumed', value: 'consumed' },
          { label: 'Expired', value: 'expired' }
        ]}
        onRowClick={handleRowClick}
        onExport={() => console.log('Export harvest data')}
        emptyState={{
          icon: DocumentTextIcon,
          title: 'No harvest batches found',
          description: 'Get started by declaring your first harvest to create a batch.',
          actionLabel: 'Declare Your First Harvest',
          onAction: () => setShowCreateModal(true)
        }}
      />

      {/* Create Harvest Modal */}
      {showCreateModal && (
        <Modal
          isOpen={showCreateModal}
          onClose={handleFormCancel}
          title="Declare New Harvest"
          size="xl"
        >
          <HarvestDeclarationForm
            productType="Fresh Fruit Bunches"
            onSubmit={handleHarvestSubmit}
            onCancel={handleFormCancel}
          />
        </Modal>
      )}

      {/* View Batch Modal */}
      {showViewModal && selectedBatch && (
        <Modal
          isOpen={showViewModal}
          onClose={() => setShowViewModal(false)}
          title={`Harvest Batch: ${selectedBatch.batch_id}`}
          size="lg"
        >
          <div className="space-y-6">
            {/* Basic Information */}
            <Card>
              <CardHeader title="Basic Information" />
              <CardBody className="space-y-3">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-sm font-medium text-gray-500">Batch ID</label>
                    <p className="text-gray-900">{selectedBatch.batch_id}</p>
                  </div>
                  <div>
                    <label className="text-sm font-medium text-gray-500">Product Type</label>
                    <p className="text-gray-900">
                      <Badge variant="secondary" size="sm">
                        {selectedBatch.product_type ? selectedBatch.product_type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()) : 'N/A'}
                      </Badge>
                    </p>
                  </div>
                  <div>
                    <label className="text-sm font-medium text-gray-500">Harvest Date</label>
                    <p className="text-gray-900">{new Date(selectedBatch.harvest_date).toLocaleDateString()}</p>
                  </div>
                  <div>
                    <label className="text-sm font-medium text-gray-500">Farm Name</label>
                    <p className="text-gray-900">{selectedBatch.farm_name}</p>
                  </div>
                  <div>
                    <label className="text-sm font-medium text-gray-500">Farm ID</label>
                    <p className="text-gray-900">{selectedBatch.farm_id}</p>
                  </div>
                </div>
              </CardBody>
            </Card>

            {/* Location Information */}
            <Card>
              <CardHeader title="Location" />
              <CardBody>
                <div className="flex items-center space-x-2">
                  <MapPinIcon className="h-5 w-5 text-gray-400" />
                  <span className="text-gray-900">
                    {selectedBatch.location_coordinates 
                      ? `${selectedBatch.location_coordinates?.latitude.toFixed(6)}, ${selectedBatch.location_coordinates?.longitude.toFixed(6)}`
                      : 'No coordinates available'
                    }
                  </span>
                </div>
              </CardBody>
            </Card>

            {/* Quality Parameters */}
            <Card>
              <CardHeader title="Quality Parameters" />
              <CardBody>
                <div className="grid grid-cols-2 gap-4">
                  {selectedBatch.quality_parameters.oil_content !== undefined && (
                    <div>
                      <label className="text-sm font-medium text-gray-500">
                        Oil Content
                      </label>
                      <p className="text-gray-900">{selectedBatch.quality_parameters.oil_content}%</p>
                    </div>
                  )}
                  {selectedBatch.quality_parameters.moisture_content !== undefined && (
                    <div>
                      <label className="text-sm font-medium text-gray-500">
                        Moisture Content
                      </label>
                      <p className="text-gray-900">{selectedBatch.quality_parameters.moisture_content}%</p>
                    </div>
                  )}
                  {selectedBatch.quality_parameters.free_fatty_acid !== undefined && (
                    <div>
                      <label className="text-sm font-medium text-gray-500">
                        Free Fatty Acid
                      </label>
                      <p className="text-gray-900">{selectedBatch.quality_parameters.free_fatty_acid}%</p>
                    </div>
                  )}
                  {selectedBatch.quality_parameters.dirt_content !== undefined && (
                    <div>
                      <label className="text-sm font-medium text-gray-500">
                        Dirt Content
                      </label>
                      <p className="text-gray-900">{selectedBatch.quality_parameters.dirt_content}%</p>
                    </div>
                  )}
                  {selectedBatch.quality_parameters.kernel_to_fruit_ratio !== undefined && (
                    <div>
                      <label className="text-sm font-medium text-gray-500">
                        Kernel to Fruit Ratio
                      </label>
                      <p className="text-gray-900">{selectedBatch.quality_parameters.kernel_to_fruit_ratio}%</p>
                    </div>
                  )}
                </div>
              </CardBody>
            </Card>

            {/* Certifications */}
            <Card>
              <CardHeader title="Certifications" />
              <CardBody>
                <div className="flex flex-wrap gap-2">
                  {selectedBatch.certifications.map((cert) => (
                    <Badge key={cert} variant="primary">
                      {cert}
                    </Badge>
                  ))}
                </div>
              </CardBody>
            </Card>
          </div>
        </Modal>
      )}
    </div>
  );
};

export default HarvestManager;
