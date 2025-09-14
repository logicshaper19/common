/**
 * Farm Information Manager Component
 * Comprehensive farm data management for originators
 */
import React, { useState, useEffect } from 'react';
import {
  BuildingOfficeIcon,
  MapPinIcon,
  UserIcon,
  CalendarIcon,
  ChartBarIcon,
  PencilIcon,
  PlusIcon,
  TrashIcon,
  EyeIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon
} from '@heroicons/react/24/outline';
import { Card, CardHeader, CardBody } from '../ui/Card';
import DataTable, { DataTableColumn } from '../ui/DataTable';
import Input from '../ui/Input';
import Select from '../ui/Select';
import TextArea from '../ui/Textarea';
import Button from '../ui/Button';
import Badge from '../ui/Badge';
import Modal from '../ui/Modal';
import LoadingSpinner from '../ui/LoadingSpinner';
import { useToast } from '../../contexts/ToastContext';
import { formatDate } from '../../lib/utils';

interface FarmInformation {
  id: string;
  farm_id: string;
  farm_name: string;
  farm_size_hectares: number;
  establishment_year: number;
  owner_name: string;
  owner_contact: string;
  plantation_type: 'own_estate' | 'smallholder' | 'mixed';
  cultivation_methods: string[];
  gps_coordinates: {
    latitude: number;
    longitude: number;
  };
  soil_type?: string;
  irrigation_system?: string;
  annual_production_capacity?: number;
  certification_status: string[];
  last_updated: string;
  is_active: boolean;
}

interface FarmInformationManagerProps {
  companyId?: string;
  className?: string;
}

const FarmInformationManager: React.FC<FarmInformationManagerProps> = ({
  companyId,
  className = ''
}) => {
  const { showToast } = useToast();
  
  // State
  const [farms, setFarms] = useState<FarmInformation[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedFarm, setSelectedFarm] = useState<FarmInformation | null>(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showViewModal, setShowViewModal] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterType, setFilterType] = useState('');

  // Form state for create/edit
  const [formData, setFormData] = useState<Partial<FarmInformation>>({
    farm_id: '',
    farm_name: '',
    farm_size_hectares: 0,
    establishment_year: new Date().getFullYear(),
    owner_name: '',
    owner_contact: '',
    plantation_type: 'smallholder',
    cultivation_methods: [],
    gps_coordinates: { latitude: 0, longitude: 0 },
    soil_type: '',
    irrigation_system: '',
    annual_production_capacity: 0,
    certification_status: [],
    is_active: true
  });

  // Available options
  const plantationTypes = [
    { value: 'smallholder', label: 'Smallholder Farm' },
    { value: 'own_estate', label: 'Own Estate' },
    { value: 'mixed', label: 'Mixed Operations' }
  ];

  const cultivationMethods = [
    { value: 'sustainable', label: 'Sustainable Farming' },
    { value: 'organic', label: 'Organic Methods' },
    { value: 'integrated_pest', label: 'Integrated Pest Management' },
    { value: 'water_conservation', label: 'Water Conservation' },
    { value: 'soil_conservation', label: 'Soil Conservation' },
    { value: 'biodiversity', label: 'Biodiversity Protection' },
    { value: 'precision_agriculture', label: 'Precision Agriculture' },
    { value: 'agroforestry', label: 'Agroforestry' }
  ];

  const certificationOptions = [
    { value: 'RSPO', label: 'RSPO' },
    { value: 'NDPE', label: 'NDPE' },
    { value: 'ISPO', label: 'ISPO' },
    { value: 'MSPO', label: 'MSPO' },
    { value: 'Rainforest Alliance', label: 'Rainforest Alliance' },
    { value: 'Organic', label: 'Organic' },
    { value: 'Fair Trade', label: 'Fair Trade' }
  ];

  // Load farms data
  useEffect(() => {
    loadFarms();
  }, [companyId]);

  const loadFarms = async () => {
    try {
      setIsLoading(true);
      setError(null);
      
      // TODO: Replace with actual API call
      // Simulated data for now
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      const mockFarms: FarmInformation[] = [
        {
          id: '1',
          farm_id: 'FARM-KAL-001',
          farm_name: 'Kalimantan Estate Block A',
          farm_size_hectares: 250.5,
          establishment_year: 2010,
          owner_name: 'PT Kalimantan Plantation',
          owner_contact: '+62-123-456-7890',
          plantation_type: 'own_estate',
          cultivation_methods: ['sustainable', 'integrated_pest', 'water_conservation'],
          gps_coordinates: { latitude: -2.5489, longitude: 118.0149 },
          soil_type: 'Peat soil',
          irrigation_system: 'Drip irrigation',
          annual_production_capacity: 5000,
          certification_status: ['RSPO', 'NDPE'],
          last_updated: '2025-01-10T10:30:00Z',
          is_active: true
        },
        {
          id: '2',
          farm_id: 'FARM-SUM-001',
          farm_name: 'Sumatra Smallholder Cooperative',
          farm_size_hectares: 125.0,
          establishment_year: 2015,
          owner_name: 'Cooperative Sumatra Sejahtera',
          owner_contact: '+62-987-654-3210',
          plantation_type: 'smallholder',
          cultivation_methods: ['organic', 'biodiversity', 'agroforestry'],
          gps_coordinates: { latitude: -0.7893, longitude: 113.9213 },
          soil_type: 'Mineral soil',
          irrigation_system: 'Rain-fed',
          annual_production_capacity: 2500,
          certification_status: ['ISPO', 'Rainforest Alliance'],
          last_updated: '2025-01-09T14:20:00Z',
          is_active: true
        },
        {
          id: '3',
          farm_id: 'FARM-KAL-002',
          farm_name: 'Kalimantan Estate Block B',
          farm_size_hectares: 180.3,
          establishment_year: 2012,
          owner_name: 'PT Kalimantan Plantation',
          owner_contact: '+62-123-456-7890',
          plantation_type: 'own_estate',
          cultivation_methods: ['sustainable', 'precision_agriculture'],
          gps_coordinates: { latitude: -1.2379, longitude: 116.8227 },
          soil_type: 'Mineral soil',
          irrigation_system: 'Sprinkler system',
          annual_production_capacity: 3600,
          certification_status: ['RSPO'],
          last_updated: '2025-01-08T09:15:00Z',
          is_active: false
        }
      ];
      
      setFarms(mockFarms);
      
    } catch (err) {
      console.error('Error loading farms:', err);
      setError('Failed to load farm data. Please try again.');
      showToast({
        type: 'error',
        title: 'Error loading farms',
        message: 'Please try again or contact support if the problem persists.'
      });
    } finally {
      setIsLoading(false);
    }
  };

  // Define table columns
  const farmColumns: DataTableColumn[] = [
    {
      key: 'icon',
      label: '',
      sortable: false,
      searchable: false,
      render: () => <BuildingOfficeIcon className="h-5 w-5 text-gray-400" />,
      className: 'w-12'
    },
    {
      key: 'farm_name',
      label: 'Farm Name',
      sortable: true,
      searchable: true,
      render: (value, farm) => (
        <div>
          <div className="font-medium text-gray-900">{value}</div>
          <div className="text-sm text-gray-500">
            {farm.gps_coordinates.latitude.toFixed(4)}, {farm.gps_coordinates.longitude.toFixed(4)}
          </div>
        </div>
      )
    },
    {
      key: 'farm_id',
      label: 'Farm ID',
      sortable: true,
      searchable: true,
      render: (value) => <div className="text-sm font-medium text-gray-900">{value}</div>
    },
    {
      key: 'owner_name',
      label: 'Owner',
      sortable: true,
      searchable: true,
      render: (value, farm) => (
        <div>
          <div className="text-sm text-gray-900">{value}</div>
          <div className="text-xs text-gray-500">{farm.owner_contact}</div>
        </div>
      )
    },
    {
      key: 'plantation_type',
      label: 'Type',
      sortable: true,
      searchable: false,
      render: (value) => getPlantationTypeBadge(value)
    },
    {
      key: 'farm_size_hectares',
      label: 'Size (ha)',
      sortable: true,
      searchable: false,
      render: (value) => <div className="text-sm text-gray-900">{value} ha</div>
    },
    {
      key: 'establishment_year',
      label: 'Established',
      sortable: true,
      searchable: false,
      render: (value) => <div className="text-sm text-gray-900">{value}</div>
    },
    {
      key: 'annual_production_capacity',
      label: 'Capacity',
      sortable: true,
      searchable: false,
      render: (value) => (
        <div className="text-sm text-gray-900">
          {value?.toLocaleString() || 'N/A'} MT/year
        </div>
      )
    },
    {
      key: 'certification_status',
      label: 'Certifications',
      sortable: false,
      searchable: false,
      render: (value) => (
        <div className="flex flex-wrap gap-1">
          {value.slice(0, 2).map((cert: string) => (
            <Badge key={cert} variant="success" size="sm">
              {cert}
            </Badge>
          ))}
          {value.length > 2 && (
            <Badge variant="neutral" size="sm">
              +{value.length - 2}
            </Badge>
          )}
        </div>
      )
    },
    {
      key: 'is_active',
      label: 'Status',
      sortable: true,
      searchable: false,
      render: (value, farm) => (
        <div className="flex flex-col gap-1">
          {value ? (
            <Badge variant="success">Active</Badge>
          ) : (
            <Badge variant="error">Inactive</Badge>
          )}
          <div className="text-xs text-gray-500">
            Updated {formatDate(farm.last_updated)}
          </div>
        </div>
      )
    },
    {
      key: 'actions',
      label: 'Actions',
      sortable: false,
      searchable: false,
      render: (_, farm) => (
        <div className="flex items-center space-x-1">
          <Button
            variant="outline"
            size="sm"
            onClick={() => openViewModal(farm)}
            title="View details"
          >
            <EyeIcon className="h-4 w-4" />
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => openEditModal(farm)}
            title="Edit farm"
          >
            <PencilIcon className="h-4 w-4" />
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => handleDelete(farm)}
            title="Delete farm"
          >
            <TrashIcon className="h-4 w-4" />
          </Button>
        </div>
      ),
      className: 'w-32'
    }
  ];

  // Handle form submission
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    try {
      // TODO: Implement actual API call
      if (selectedFarm) {
        // Update existing farm
        showToast({
          type: 'success',
          title: 'Farm Updated',
          message: `Farm ${formData.farm_name} has been updated successfully.`
        });
      } else {
        // Create new farm
        showToast({
          type: 'success',
          title: 'Farm Created',
          message: `Farm ${formData.farm_name} has been created successfully.`
        });
      }
      
      setShowCreateModal(false);
      setShowEditModal(false);
      loadFarms();
      
    } catch (error) {
      showToast({
        type: 'error',
        title: 'Error',
        message: 'Failed to save farm information. Please try again.'
      });
    }
  };

  // Handle delete
  const handleDelete = async (farm: FarmInformation) => {
    if (window.confirm(`Are you sure you want to delete farm ${farm.farm_name}?`)) {
      try {
        // TODO: Implement delete API call
        showToast({
          type: 'success',
          title: 'Farm Deleted',
          message: `Farm ${farm.farm_name} has been deleted successfully.`
        });
        loadFarms();
      } catch (error) {
        showToast({
          type: 'error',
          title: 'Error',
          message: 'Failed to delete farm. Please try again.'
        });
      }
    }
  };

  // Open modals
  const openCreateModal = () => {
    setFormData({
      farm_id: '',
      farm_name: '',
      farm_size_hectares: 0,
      establishment_year: new Date().getFullYear(),
      owner_name: '',
      owner_contact: '',
      plantation_type: 'smallholder',
      cultivation_methods: [],
      gps_coordinates: { latitude: 0, longitude: 0 },
      soil_type: '',
      irrigation_system: '',
      annual_production_capacity: 0,
      certification_status: [],
      is_active: true
    });
    setSelectedFarm(null);
    setShowCreateModal(true);
  };

  const openEditModal = (farm: FarmInformation) => {
    setFormData(farm);
    setSelectedFarm(farm);
    setShowEditModal(true);
  };

  const openViewModal = (farm: FarmInformation) => {
    setSelectedFarm(farm);
    setShowViewModal(true);
  };

  // Get plantation type badge variant
  const getPlantationTypeBadge = (type: string) => {
    switch (type) {
      case 'own_estate':
        return <Badge variant="primary">Own Estate</Badge>;
      case 'smallholder':
        return <Badge variant="secondary">Smallholder</Badge>;
      case 'mixed':
        return <Badge variant="neutral">Mixed</Badge>;
      default:
        return <Badge variant="neutral">{type}</Badge>;
    }
  };

  if (isLoading) {
    return (
      <div className={`flex items-center justify-center py-8 ${className}`}>
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  if (error) {
    return (
      <div className={`text-center py-8 ${className}`}>
        <p className="text-red-600 mb-4">{error}</p>
        <Button onClick={loadFarms} variant="primary">
          Try Again
        </Button>
      </div>
    );
  }

  return (
    <div className={className}>
      {/* Header */}
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-gray-900">Farm Information Management</h2>
          <p className="text-gray-600 mt-1">
            Comprehensive farm data management with GPS tracking, certification status, and production capacity monitoring.
          </p>
        </div>
        <Button
          variant="primary"
          leftIcon={<PlusIcon className="h-4 w-4" />}
          onClick={openCreateModal}
        >
          Add Farm
        </Button>
      </div>

      {/* Filters */}
      <Card className="mb-6">
        <CardBody>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Input
              type="text"
              placeholder="Search farms..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
            <Select
              value={filterType}
              onChange={(e) => setFilterType(e.target.value)}
              options={[
                { label: 'All Types', value: '' },
                ...plantationTypes
              ]}
            />
          </div>
        </CardBody>
      </Card>

      {/* Farms Table */}
      <DataTable
        title={`Farms (${farms.length})`}
        data={farms}
        columns={farmColumns}
        searchPlaceholder="Search farm names, IDs, owners..."
        statusFilterOptions={[
          { label: 'Active', value: 'true' },
          { label: 'Inactive', value: 'false' }
        ]}
        onRowClick={(farm) => openViewModal(farm)}
        onExport={() => console.log('Export farms')}
        emptyState={{
          icon: BuildingOfficeIcon,
          title: 'No farms found',
          description: 'Get started by adding your first farm to the system.',
          actionLabel: 'Add Your First Farm',
          onAction: openCreateModal
        }}
      />

      {/* Create/Edit Modal */}
      {(showCreateModal || showEditModal) && (
        <Modal
          isOpen={showCreateModal || showEditModal}
          onClose={() => {
            setShowCreateModal(false);
            setShowEditModal(false);
          }}
          title={selectedFarm ? `Edit Farm - ${selectedFarm.farm_name}` : 'Create New Farm'}
        >
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Input
                label="Farm ID"
                type="text"
                value={formData.farm_id || ''}
                onChange={(e) => setFormData(prev => ({ ...prev, farm_id: e.target.value }))}
                required
                placeholder="FARM-XXX-001"
              />
              <Input
                label="Farm Name"
                type="text"
                value={formData.farm_name || ''}
                onChange={(e) => setFormData(prev => ({ ...prev, farm_name: e.target.value }))}
                required
                placeholder="Farm or plantation name"
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <Input
                label="Farm Size (Hectares)"
                type="number"
                step="0.1"
                value={formData.farm_size_hectares || ''}
                onChange={(e) => setFormData(prev => ({ ...prev, farm_size_hectares: parseFloat(e.target.value) }))}
                required
              />
              <Input
                label="Establishment Year"
                type="number"
                value={formData.establishment_year || ''}
                onChange={(e) => setFormData(prev => ({ ...prev, establishment_year: parseInt(e.target.value) }))}
                required
                min="1900"
                max={new Date().getFullYear()}
              />
              <Select
                label="Plantation Type"
                value={formData.plantation_type || 'smallholder'}
                onChange={(e) => setFormData(prev => ({ ...prev, plantation_type: e.target.value as any }))}
                options={plantationTypes}
                required
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Input
                label="Owner Name"
                type="text"
                value={formData.owner_name || ''}
                onChange={(e) => setFormData(prev => ({ ...prev, owner_name: e.target.value }))}
                required
              />
              <Input
                label="Owner Contact"
                type="text"
                value={formData.owner_contact || ''}
                onChange={(e) => setFormData(prev => ({ ...prev, owner_contact: e.target.value }))}
                placeholder="+62-xxx-xxx-xxxx"
              />
            </div>

            <div className="flex justify-end space-x-3 pt-4">
              <Button
                type="button"
                variant="outline"
                onClick={() => {
                  setShowCreateModal(false);
                  setShowEditModal(false);
                }}
              >
                Cancel
              </Button>
              <Button
                type="submit"
                variant="primary"
                leftIcon={<CheckCircleIcon className="h-4 w-4" />}
              >
                {selectedFarm ? 'Update Farm' : 'Create Farm'}
              </Button>
            </div>
          </form>
        </Modal>
      )}

      {/* View Modal */}
      {showViewModal && selectedFarm && (
        <Modal
          isOpen={showViewModal}
          onClose={() => setShowViewModal(false)}
          title={`Farm Details - ${selectedFarm.farm_name}`}
        >
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <label className="block font-medium text-gray-700">Farm ID</label>
                <p className="text-gray-900">{selectedFarm.farm_id}</p>
              </div>
              <div>
                <label className="block font-medium text-gray-700">Owner</label>
                <p className="text-gray-900">{selectedFarm.owner_name}</p>
              </div>
              <div>
                <label className="block font-medium text-gray-700">Size</label>
                <p className="text-gray-900">{selectedFarm.farm_size_hectares} hectares</p>
              </div>
              <div>
                <label className="block font-medium text-gray-700">Established</label>
                <p className="text-gray-900">{selectedFarm.establishment_year}</p>
              </div>
              <div>
                <label className="block font-medium text-gray-700">GPS Coordinates</label>
                <p className="text-gray-900">
                  {selectedFarm.gps_coordinates.latitude.toFixed(4)}, {selectedFarm.gps_coordinates.longitude.toFixed(4)}
                </p>
              </div>
              <div>
                <label className="block font-medium text-gray-700">Annual Capacity</label>
                <p className="text-gray-900">
                  {selectedFarm.annual_production_capacity?.toLocaleString() || 'N/A'} MT/year
                </p>
              </div>
            </div>

            <div>
              <label className="block font-medium text-gray-700 mb-2">Certifications</label>
              <div className="flex flex-wrap gap-2">
                {selectedFarm.certification_status.map((cert) => (
                  <Badge key={cert} variant="success">
                    {cert}
                  </Badge>
                ))}
              </div>
            </div>

            <div>
              <label className="block font-medium text-gray-700 mb-2">Cultivation Methods</label>
              <div className="flex flex-wrap gap-2">
                {selectedFarm.cultivation_methods.map((method) => (
                  <Badge key={method} variant="secondary">
                    {cultivationMethods.find(m => m.value === method)?.label || method}
                  </Badge>
                ))}
              </div>
            </div>

            <div className="flex justify-end pt-4">
              <Button variant="outline" onClick={() => setShowViewModal(false)}>
                Close
              </Button>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
};

export default FarmInformationManager;
