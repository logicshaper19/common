import React, { useState, useEffect } from 'react';
import { PlusIcon, DocumentTextIcon, MapPinIcon, CalendarIcon, ChartBarIcon, CheckCircleIcon, ClockIcon, TruckIcon, PencilIcon } from '@heroicons/react/24/outline';
import { Button } from '../ui/Button';
import { Card, CardHeader, CardBody } from '../ui/Card';
import DataTable from '../ui/DataTable';
import Modal from '../ui/Modal';
import { Badge } from '../ui/Badge';
import AnalyticsCard from '../ui/AnalyticsCard';
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
  // Enhanced allocation tracking
  allocated_quantity?: number;
  available_quantity?: number;
  allocated_orders?: Array<{
    po_id: string;
    po_number: string;
    allocated_quantity: number;
    buyer_company: string;
  }>;
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
  const [showEditModal, setShowEditModal] = useState(false);
  const [selectedBatch, setSelectedBatch] = useState<HarvestBatch | null>(null);

  // Calculate analytics from harvest batches data
  const analytics = React.useMemo(() => {
    const total = harvestBatches.length;
    const active = harvestBatches.filter(batch => batch.status === 'active').length;
    const consumed = harvestBatches.filter(batch => batch.status === 'consumed').length;
    const totalQuantity = harvestBatches.reduce((sum, batch) => sum + (batch.quantity || 0), 0);
    const recentHarvests = harvestBatches.filter(batch => {
      const harvestDate = new Date(batch.harvest_date);
      const thirtyDaysAgo = new Date();
      thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);
      return harvestDate >= thirtyDaysAgo;
    }).length;

    return [
      {
        name: 'Total Batches',
        value: total.toString(),
        change: '+8%',
        changeType: 'increase' as const,
        icon: DocumentTextIcon,
      },
      {
        name: 'Active Batches',
        value: active.toString(),
        change: active > 0 ? `${Math.round((active / total) * 100)}%` : '0%',
        changeType: 'increase' as const,
        icon: CheckCircleIcon,
      },
      {
        name: 'Recent Harvests',
        value: recentHarvests.toString(),
        change: recentHarvests > 0 ? `${Math.round((recentHarvests / total) * 100)}%` : '0%',
        changeType: 'increase' as const,
        icon: CalendarIcon,
      },
      {
        name: 'Total Quantity',
        value: totalQuantity.toLocaleString(),
        change: '+15%',
        changeType: 'increase' as const,
        icon: ChartBarIcon,
      },
    ];
  }, [harvestBatches]);

  // Load harvest batches only once on mount
  useEffect(() => {
    loadHarvestBatches();
  }, []); // Empty dependency array - only run once on mount

  const loadHarvestBatches = async () => {
    try {
      setLoading(true);
      
      // Import harvestApi to use real API
      const { harvestApi } = await import('../../services/harvestApi');
      
      // Get harvest batches from the real API
      const response = await harvestApi.getHarvestBatches(1, 100); // Get first 100 batches
      const apiBatches = response.batches || [];
      
      // Transform API data to match the expected interface
      const transformedBatches = apiBatches.map((batch: any) => {
        // Mock allocation data for demonstration - in real implementation, this would come from the API
        const totalQuantity = batch.quantity || 0;
        const mockAllocatedQuantity = Math.random() > 0.5 ? Math.floor(totalQuantity * 0.3) : 0; // 30% chance of being allocated
        const mockAllocatedOrders = mockAllocatedQuantity > 0 ? [
          {
            po_id: 'po-123',
            po_number: 'PO-20250922-276EFA9D',
            allocated_quantity: mockAllocatedQuantity,
            buyer_company: 'Tani Maju Cooperative'
          }
        ] : [];
        
        return {
          id: batch.id,
          batch_id: batch.batch_id,
          product_type: batch.product_name || 'Fresh Fruit Bunches',
          harvest_date: batch.origin_data?.harvest_date || batch.production_date,
          farm_name: batch.origin_data?.farm_information?.farm_name || batch.location_name || 'Unknown Farm',
          farm_id: batch.origin_data?.farm_information?.farm_id || batch.facility_code || 'N/A',
          plantation_type: batch.origin_data?.farm_information?.plantation_type || 'smallholder',
          quantity: totalQuantity,
          unit: batch.unit || 'KGM',
          location_coordinates: batch.origin_data?.geographic_coordinates || batch.location_coordinates,
          certifications: batch.certifications || [],
          quality_parameters: batch.quality_metrics || {},
          status: batch.status || 'active',
          created_at: batch.created_at,
          // Enhanced allocation tracking
          allocated_quantity: mockAllocatedQuantity,
          available_quantity: totalQuantity - mockAllocatedQuantity,
          allocated_orders: mockAllocatedOrders
        };
      });
      
      setHarvestBatches(transformedBatches);
      
      if (transformedBatches.length === 0) {
        showToast({
          type: 'info',
          title: 'No Harvest Batches',
          message: 'No harvest batches found. Create a harvest declaration to get started.'
        });
      }
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
        farm_name: harvestData.farm_information?.farm_name || '',
        farm_id: harvestData.farm_information?.farm_id || '',
        plantation_type: harvestData.farm_information?.plantation_type || '',
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

  // Handle edit batch
  const handleEditBatch = (batch: HarvestBatch) => {
    setSelectedBatch(batch);
    setShowEditModal(true);
  };

  // Handle edit form submission
  const handleEditSubmit = async (harvestData: any) => {
    try {
      // TODO: Replace with actual API call
      // await harvestApi.updateHarvestBatch(selectedBatch?.id, harvestData);
      
      console.log('Updating harvest batch:', harvestData);
      
      // Update local state
      setHarvestBatches(prev => prev.map(batch => 
        batch.id === selectedBatch?.id 
          ? {
              ...batch,
              batch_id: harvestData.batch_number,
              product_type: harvestData.product_type,
              harvest_date: harvestData.harvest_date,
              farm_name: harvestData.farm_information?.farm_name || '',
              farm_id: harvestData.farm_information?.farm_id || '',
              plantation_type: harvestData.farm_information?.plantation_type || '',
              quantity: harvestData.quantity,
              unit: harvestData.unit,
              location_coordinates: harvestData.geographic_coordinates,
              certifications: harvestData.certifications,
              quality_parameters: harvestData.quality_parameters,
            }
          : batch
      ));
      
      setShowEditModal(false);
      setSelectedBatch(null);
      showToast({ title: 'Success', message: 'Harvest batch updated successfully', type: 'success' });
    } catch (error) {
      console.error('Error updating harvest batch:', error);
      showToast({ title: 'Error', message: 'Failed to update harvest batch', type: 'error' });
    }
  };

  // Handle edit form cancel
  const handleEditCancel = () => {
    setShowEditModal(false);
    setSelectedBatch(null);
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
      label: 'Quantity & Availability',
      render: (value: any, batch: HarvestBatch) => {
        const totalQuantity = batch?.quantity || 0;
        const allocatedQuantity = batch?.allocated_quantity || 0;
        const availableQuantity = batch?.available_quantity || (totalQuantity - allocatedQuantity);
        const utilizationPercentage = totalQuantity > 0 ? (allocatedQuantity / totalQuantity) * 100 : 0;
        
        return (
          <div className="min-w-[200px]">
            <div className="flex justify-between items-center mb-1">
              <span className="text-sm font-medium text-gray-900">
                {availableQuantity.toLocaleString()} / {totalQuantity.toLocaleString()}
              </span>
              <span className="text-xs text-gray-500">{batch?.unit || 'N/A'}</span>
            </div>
            
            {/* Progress bar */}
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div 
                className={`h-2 rounded-full transition-all duration-300 ${
                  utilizationPercentage === 0 ? 'bg-green-500' :
                  utilizationPercentage < 50 ? 'bg-yellow-500' :
                  utilizationPercentage < 90 ? 'bg-orange-500' : 'bg-red-500'
                }`}
                style={{ width: `${utilizationPercentage}%` }}
              />
            </div>
            
            <div className="flex justify-between items-center mt-1">
              <span className="text-xs text-gray-500">
                {allocatedQuantity > 0 ? `${allocatedQuantity.toLocaleString()} allocated` : 'Fully available'}
              </span>
              <span className="text-xs text-gray-500">
                {Math.round(utilizationPercentage)}% used
              </span>
            </div>
        </div>
        );
      }
    },
    {
      key: 'certifications',
      label: 'Certifications',
      render: (value: any, batch: HarvestBatch) => (
        <div className="flex flex-wrap gap-1">
          {(batch?.certifications || []).slice(0, 2).map((cert) => (
            <Badge key={cert} variant="secondary" size="sm">
              {cert}
            </Badge>
          ))}
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
      label: 'Status & Utilization',
      render: (value: any, batch: HarvestBatch) => {
        const totalQuantity = batch?.quantity || 0;
        const allocatedQuantity = batch?.allocated_quantity || 0;
        const availableQuantity = batch?.available_quantity || (totalQuantity - allocatedQuantity);
        const utilizationPercentage = totalQuantity > 0 ? (allocatedQuantity / totalQuantity) * 100 : 0;
        
        // Determine status based on utilization
        let statusText = 'Active';
        let statusVariant: 'success' | 'warning' | 'secondary' = 'success';
        
        if (batch?.status === 'consumed') {
          statusText = 'Fully Consumed';
          statusVariant = 'secondary';
        } else if (batch?.status === 'expired') {
          statusText = 'Expired';
          statusVariant = 'secondary';
        } else if (utilizationPercentage === 100) {
          statusText = 'Fully Allocated';
          statusVariant = 'warning';
        } else if (utilizationPercentage > 0) {
          statusText = 'Partially Allocated';
          statusVariant = 'warning';
        } else {
          statusText = 'Available';
          statusVariant = 'success';
        }
        
        return (
          <div className="space-y-1">
            <Badge variant={statusVariant} size="sm">
              {statusText}
            </Badge>
            {allocatedQuantity > 0 && (
              <div className="text-xs text-gray-500">
                {batch?.allocated_orders?.length || 0} order(s)
              </div>
            )}
          </div>
        );
      }
    },
    {
      key: 'allocations',
      label: 'Allocations',
      render: (value: any, batch: HarvestBatch) => {
        const allocatedOrders = batch?.allocated_orders || [];
        
        if (allocatedOrders.length === 0) {
          return (
            <div className="text-sm text-gray-500">
              No allocations
            </div>
          );
        }
        
        return (
          <div className="space-y-1">
            {allocatedOrders.slice(0, 2).map((order, index) => (
              <div key={index} className="text-xs">
                <div className="font-medium text-gray-900">
                  {order.po_number}
                </div>
                <div className="text-gray-500">
                  {order.allocated_quantity.toLocaleString()} {batch?.unit} → {order.buyer_company}
                </div>
              </div>
            ))}
            {allocatedOrders.length > 2 && (
              <div className="text-xs text-gray-500">
                +{allocatedOrders.length - 2} more order(s)
              </div>
            )}
          </div>
        );
      }
    },
    {
      key: 'actions',
      label: 'Actions',
      render: (value: any, batch: HarvestBatch) => (
        <div className="flex space-x-2">
          <Button
            onClick={(e) => {
              e.stopPropagation();
              handleEditBatch(batch);
            }}
            variant="outline"
          size="sm"
        >
            <PencilIcon className="h-4 w-4" />
          </Button>
        </div>
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

      {/* Analytics Cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {analytics.map((stat) => (
          <AnalyticsCard
            key={stat.name}
            name={stat.name}
            value={stat.value}
            change={stat.change}
            changeType={stat.changeType}
            icon={stat.icon}
          />
        ))}
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

      {/* Edit Harvest Modal */}
      {showEditModal && selectedBatch && (
        <Modal
          isOpen={showEditModal}
          onClose={handleEditCancel}
          title="Edit Harvest Batch"
          size="xl"
        >
          <HarvestDeclarationForm
            productType={selectedBatch.product_type}
            initialData={{
              product_type: selectedBatch.product_type,
              geographic_coordinates: selectedBatch.location_coordinates || { latitude: 0, longitude: 0 },
              certifications: selectedBatch.certifications,
              harvest_date: selectedBatch.harvest_date,
              farm_information: {
                farm_id: selectedBatch.farm_id,
                farm_name: selectedBatch.farm_name,
                plantation_type: selectedBatch.plantation_type as 'smallholder' | 'estate' | 'cooperative',
                cultivation_methods: []
              },
              batch_number: selectedBatch.batch_id,
              quantity: selectedBatch.quantity,
              unit: selectedBatch.unit,
              quality_parameters: selectedBatch.quality_parameters,
              processing_notes: ''
            }}
            onSubmit={handleEditSubmit}
            onCancel={handleEditCancel}
            isLoading={loading}
          />
        </Modal>
      )}
    </div>
  );
};

export default HarvestManager;
