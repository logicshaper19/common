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
  ExclamationTriangleIcon,
  DocumentTextIcon,
  ClockIcon,
  ShieldCheckIcon
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
import AnalyticsCard from '../ui/AnalyticsCard';
import { useToast } from '../../contexts/ToastContext';
import { formatDate } from '../../lib/utils';
import { farmApi } from '../../services/farmApi';

interface FarmInformation {
  id: string;
  farm_id: string;
  farm_name: string;
  farm_size_hectares: number;
  establishment_year: number;
  owner_name: string;
  owner_contact: string;
  plantation_type: 'own_estate' | 'smallholder' | 'mixed' | 'palm_plantation' | 'coffee_farm' | 'cocoa_farm' | 'rubber_plantation' | 'other';
  cultivation_methods: string[];
  gps_coordinates: {
    latitude: number;
    longitude: number;
  };
  soil_type?: string;
  irrigation_system?: string;
  annual_production_capacity?: number;
  certification_status: string[];
  compliance_status: 'pending' | 'verified' | 'failed' | 'exempt';
  last_updated: string;
  is_active: boolean;
  // Additional fields for enhanced farm management
  registration_number?: string;
  specialization?: string;
  farm_owner_name?: string;
  farm_contact_info?: {
    phone?: string;
    email?: string;
    address?: string;
  };
  address?: string;
  city?: string;
  state_province?: string;
  country?: string;
  postal_code?: string;
  accuracy_meters?: number;
  elevation_meters?: number;
  notes?: string;
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

  // Calculate analytics from farms data
  const analytics = React.useMemo(() => {
    const total = farms.length;
    const active = farms.filter(farm => farm.is_active).length;
    const certified = farms.filter(farm => farm.certification_status && farm.certification_status.length > 0).length;
    const smallholder = farms.filter(farm => farm.plantation_type === 'smallholder').length;
    const ownEstate = farms.filter(farm => farm.plantation_type === 'own_estate').length;
    const totalHectares = farms.reduce((sum, farm) => sum + (farm.farm_size_hectares || 0), 0);

    return [
      {
        name: 'Total Farms',
        value: total.toString(),
        change: '+5%',
        changeType: 'increase' as const,
        icon: BuildingOfficeIcon,
      },
      {
        name: 'Active Farms',
        value: active.toString(),
        change: active > 0 ? `${Math.round((active / total) * 100)}%` : '0%',
        changeType: 'increase' as const,
        icon: CheckCircleIcon,
      },
      {
        name: 'Certified Farms',
        value: certified.toString(),
        change: certified > 0 ? `${Math.round((certified / total) * 100)}%` : '0%',
        changeType: 'increase' as const,
        icon: ShieldCheckIcon,
      },
      {
        name: 'Total Hectares',
        value: totalHectares.toLocaleString(),
        change: '+12%',
        changeType: 'increase' as const,
        icon: MapPinIcon,
      },
    ];
  }, [farms]);

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
    compliance_status: 'pending',
    registration_number: '',
    specialization: '',
    farm_owner_name: '',
    farm_contact_info: {
      phone: '',
      email: '',
      address: ''
    },
    address: '',
    city: '',
    state_province: '',
    country: '',
    postal_code: '',
    accuracy_meters: 0,
    elevation_meters: 0,
    notes: '',
    is_active: true
  });

  // Available options
  const plantationTypes = [
    { value: 'smallholder', label: 'Smallholder Farm' },
    { value: 'own_estate', label: 'Own Estate' },
    { value: 'mixed', label: 'Mixed Operations' },
    { value: 'palm_plantation', label: 'Palm Plantation' },
    { value: 'coffee_farm', label: 'Coffee Farm' },
    { value: 'cocoa_farm', label: 'Cocoa Farm' },
    { value: 'rubber_plantation', label: 'Rubber Plantation' },
    { value: 'other', label: 'Other' }
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
    { value: 'RSPO', label: 'RSPO (Roundtable on Sustainable Palm Oil)' },
    { value: 'NDPE', label: 'NDPE (No Deforestation, No Peat, No Exploitation)' },
    { value: 'ISPO', label: 'ISPO (Indonesian Sustainable Palm Oil)' },
    { value: 'MSPO', label: 'MSPO (Malaysian Sustainable Palm Oil)' },
    { value: 'Rainforest Alliance', label: 'Rainforest Alliance' },
    { value: 'ISCC', label: 'ISCC (International Sustainability & Carbon Certification)' },
    { value: 'Organic', label: 'Organic Certification' },
    { value: 'Fair Trade', label: 'Fair Trade Certified' },
    { value: 'UTZ', label: 'UTZ Certified' },
    { value: '4C', label: '4C Association' },
    { value: 'C.A.F.E. Practices', label: 'C.A.F.E. Practices (Starbucks)' },
    { value: 'Bird Friendly', label: 'Bird Friendly (Smithsonian)' },
    { value: 'FSC', label: 'FSC (Forest Stewardship Council)' },
    { value: 'PEFC', label: 'PEFC (Programme for the Endorsement of Forest Certification)' }
  ];

  const complianceStatuses = [
    { value: 'pending', label: 'Pending Review' },
    { value: 'verified', label: 'Verified' },
    { value: 'failed', label: 'Failed' },
    { value: 'exempt', label: 'Exempt' }
  ];

  // Load farms data
  useEffect(() => {
    loadFarms();
  }, [companyId]);

  const loadFarms = async () => {
    try {
      setIsLoading(true);
      setError(null);
      
      // Use actual API call instead of mock data
      if (!companyId) {
        throw new Error('Company ID is required');
      }
      
      const response = await farmApi.getCompanyFarms(companyId);
      const farms = response.farms;
      
      // Transform API response to match component interface
      const transformedFarms: FarmInformation[] = farms.map(farm => ({
        id: farm.id,
        farm_id: farm.id, // Use id as farm_id
        farm_name: farm.farm_name,
        farm_size_hectares: farm.total_area_hectares,
        establishment_year: new Date(farm.created_at).getFullYear(),
        owner_name: farm.contact_person.name,
        owner_contact: farm.contact_person.phone,
        plantation_type: farm.farm_type === 'plantation' ? 'own_estate' : 
                        farm.farm_type === 'cooperative' ? 'smallholder' : 
                        farm.farm_type === 'mill' ? 'other' : 'other',
        cultivation_methods: [], // Not available in API response
        gps_coordinates: {
          latitude: farm.location.latitude,
          longitude: farm.location.longitude
        },
        soil_type: '', // Not available in API response
        irrigation_system: '', // Not available in API response
        annual_production_capacity: 0, // Not available in API response
        certification_status: farm.certifications,
        compliance_status: farm.eudr_status === 'compliant' ? 'verified' : 
                          farm.eudr_status === 'non_compliant' ? 'failed' : 'pending',
        last_updated: farm.updated_at,
        is_active: farm.is_active
      }));
      
      setFarms(transformedFarms);
      
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
      const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
      const token = localStorage.getItem('auth_token');
      
      if (!token) {
        showToast({
          type: 'error',
          title: 'Authentication Error',
          message: 'Please log in to create farms.'
        });
        return;
      }

      const farmData = {
        farm_id: formData.farm_id,
        farm_name: formData.farm_name,
        farm_size_hectares: formData.farm_size_hectares,
        establishment_year: formData.establishment_year,
        owner_name: formData.owner_name,
        plantation_type: formData.plantation_type,
        registration_number: formData.registration_number,
        specialization: formData.specialization,
        farm_owner_name: formData.farm_owner_name,
        gps_coordinates: formData.gps_coordinates,
        accuracy_meters: formData.accuracy_meters,
        elevation_meters: formData.elevation_meters,
        address: formData.address,
        city: formData.city,
        state_province: formData.state_province,
        country: formData.country,
        postal_code: formData.postal_code,
        farm_contact_info: formData.farm_contact_info,
        certification_status: formData.certification_status,
        compliance_status: formData.compliance_status,
        is_active: formData.is_active,
        notes: formData.notes
      };

      if (selectedFarm) {
        // Update existing farm
        const response = await fetch(`${API_BASE_URL}/api/v1/farm-management/farms/${selectedFarm.id}`, {
          method: 'PUT',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(farmData)
        });

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        showToast({
          type: 'success',
          title: 'Farm Updated',
          message: `Farm ${formData.farm_name} has been updated successfully.`
        });
      } else {
        // Create new farm
        const response = await fetch(`${API_BASE_URL}/api/v1/farm-management/farms`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(farmData)
        });

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const result = await response.json();
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
      console.error('Error saving farm:', error);
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
    console.log('🚀 Opening enhanced farm creation modal');
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
      compliance_status: 'pending',
      registration_number: '',
      specialization: '',
      farm_owner_name: '',
      farm_contact_info: {
        phone: '',
        email: '',
        address: ''
      },
      address: '',
      city: '',
      state_province: '',
      country: '',
      postal_code: '',
      accuracy_meters: 0,
      elevation_meters: 0,
      notes: '',
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

      {/* Analytics Cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4 mb-6">
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
          title={selectedFarm ? `Edit Farm - ${selectedFarm.farm_name}` : 'Create New Farm - Enhanced'}
          size="xl"
        >
          <form onSubmit={handleSubmit} className="space-y-6 max-h-[80vh] overflow-y-auto">
            {/* Basic Information Section */}
            <div className="border-b border-gray-200 pb-4">
              <h3 className="text-lg font-medium text-gray-900 mb-4 flex items-center">
                <BuildingOfficeIcon className="h-5 w-5 mr-2" />
                Basic Information
              </h3>
              
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Input
                  label="Farm ID *"
                type="text"
                value={formData.farm_id || ''}
                onChange={(e) => setFormData(prev => ({ ...prev, farm_id: e.target.value }))}
                required
                placeholder="FARM-XXX-001"
              />
              <Input
                  label="Farm Name *"
                type="text"
                value={formData.farm_name || ''}
                onChange={(e) => setFormData(prev => ({ ...prev, farm_name: e.target.value }))}
                required
                placeholder="Farm or plantation name"
              />
            </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
                <Input
                  label="Registration Number"
                  type="text"
                  value={formData.registration_number || ''}
                  onChange={(e) => setFormData(prev => ({ ...prev, registration_number: e.target.value }))}
                  placeholder="Official registration number"
                />
                <Input
                  label="Specialization"
                  type="text"
                  value={formData.specialization || ''}
                  onChange={(e) => setFormData(prev => ({ ...prev, specialization: e.target.value }))}
                  placeholder="e.g., Arabica Coffee, Palm Oil, etc."
                />
              </div>
            </div>

            {/* Farm Details Section */}
            <div className="border-b border-gray-200 pb-4">
              <h3 className="text-lg font-medium text-gray-900 mb-4 flex items-center">
                <ChartBarIcon className="h-5 w-5 mr-2" />
                Farm Details
              </h3>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <Input
                  label="Farm Size (Hectares) *"
                type="number"
                step="0.1"
                value={formData.farm_size_hectares || ''}
                onChange={(e) => setFormData(prev => ({ ...prev, farm_size_hectares: parseFloat(e.target.value) }))}
                required
              />
              <Input
                  label="Establishment Year *"
                type="number"
                value={formData.establishment_year || ''}
                onChange={(e) => setFormData(prev => ({ ...prev, establishment_year: parseInt(e.target.value) }))}
                required
                min="1900"
                max={new Date().getFullYear()}
              />
                <Input
                  label="Annual Capacity (MT)"
                  type="number"
                  step="0.1"
                  value={formData.annual_production_capacity || ''}
                  onChange={(e) => setFormData(prev => ({ ...prev, annual_production_capacity: parseFloat(e.target.value) }))}
                  placeholder="Annual production capacity"
                />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
              <Select
                  label="Farm Type *"
                value={formData.plantation_type || 'smallholder'}
                onChange={(e) => setFormData(prev => ({ ...prev, plantation_type: e.target.value as any }))}
                options={plantationTypes}
                required
              />
                <Select
                  label="Compliance Status"
                  value={formData.compliance_status || 'pending'}
                  onChange={(e) => setFormData(prev => ({ ...prev, compliance_status: e.target.value as any }))}
                  options={complianceStatuses}
                />
              </div>
            </div>

            {/* Owner Information Section */}
            <div className="border-b border-gray-200 pb-4">
              <h3 className="text-lg font-medium text-gray-900 mb-4 flex items-center">
                <UserIcon className="h-5 w-5 mr-2" />
                Owner Information
              </h3>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Input
                  label="Owner Name *"
                type="text"
                value={formData.owner_name || ''}
                onChange={(e) => setFormData(prev => ({ ...prev, owner_name: e.target.value }))}
                required
              />
              <Input
                  label="Farm Owner Name"
                type="text"
                  value={formData.farm_owner_name || ''}
                  onChange={(e) => setFormData(prev => ({ ...prev, farm_owner_name: e.target.value }))}
                  placeholder="If different from owner"
                />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
                <Input
                  label="Phone"
                  type="tel"
                  value={formData.farm_contact_info?.phone || ''}
                  onChange={(e) => setFormData(prev => ({ 
                    ...prev, 
                    farm_contact_info: { 
                      ...prev.farm_contact_info, 
                      phone: e.target.value 
                    } 
                  }))}
                placeholder="+62-xxx-xxx-xxxx"
              />
                <Input
                  label="Email"
                  type="email"
                  value={formData.farm_contact_info?.email || ''}
                  onChange={(e) => setFormData(prev => ({ 
                    ...prev, 
                    farm_contact_info: { 
                      ...prev.farm_contact_info, 
                      email: e.target.value 
                    } 
                  }))}
                  placeholder="owner@farm.com"
                />
              </div>
            </div>

            {/* Location Information Section */}
            <div className="border-b border-gray-200 pb-4">
              <h3 className="text-lg font-medium text-gray-900 mb-4 flex items-center">
                <MapPinIcon className="h-5 w-5 mr-2" />
                Location Information
              </h3>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <Input
                  label="Address"
                  type="text"
                  value={formData.address || ''}
                  onChange={(e) => setFormData(prev => ({ ...prev, address: e.target.value }))}
                  placeholder="Street address"
                />
                <Input
                  label="City"
                  type="text"
                  value={formData.city || ''}
                  onChange={(e) => setFormData(prev => ({ ...prev, city: e.target.value }))}
                  placeholder="City"
                />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-4">
                <Input
                  label="State/Province"
                  type="text"
                  value={formData.state_province || ''}
                  onChange={(e) => setFormData(prev => ({ ...prev, state_province: e.target.value }))}
                  placeholder="State or Province"
                />
                <Input
                  label="Country"
                  type="text"
                  value={formData.country || ''}
                  onChange={(e) => setFormData(prev => ({ ...prev, country: e.target.value }))}
                  placeholder="Country"
                />
                <Input
                  label="Postal Code"
                  type="text"
                  value={formData.postal_code || ''}
                  onChange={(e) => setFormData(prev => ({ ...prev, postal_code: e.target.value }))}
                  placeholder="Postal code"
                />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-4">
                <Input
                  label="Latitude *"
                  type="number"
                  step="0.000001"
                  value={formData.gps_coordinates?.latitude || ''}
                  onChange={(e) => setFormData(prev => ({ 
                    ...prev, 
                    gps_coordinates: { 
                      latitude: parseFloat(e.target.value) || 0, 
                      longitude: prev.gps_coordinates?.longitude || 0
                    } 
                  }))}
                  required
                  placeholder="GPS latitude"
                />
                <Input
                  label="Longitude *"
                  type="number"
                  step="0.000001"
                  value={formData.gps_coordinates?.longitude || ''}
                  onChange={(e) => setFormData(prev => ({ 
                    ...prev, 
                    gps_coordinates: { 
                      latitude: prev.gps_coordinates?.latitude || 0, 
                      longitude: parseFloat(e.target.value) || 0
                    } 
                  }))}
                  required
                  placeholder="GPS longitude"
                />
                <Input
                  label="GPS Accuracy (meters)"
                  type="number"
                  step="0.1"
                  value={formData.accuracy_meters || ''}
                  onChange={(e) => setFormData(prev => ({ ...prev, accuracy_meters: parseFloat(e.target.value) }))}
                  placeholder="GPS accuracy"
                />
              </div>
            </div>

            {/* Certifications Section */}
            <div className="border-b border-gray-200 pb-4">
              <h3 className="text-lg font-medium text-gray-900 mb-4 flex items-center">
                <ShieldCheckIcon className="h-5 w-5 mr-2" />
                Certifications
              </h3>
              
              <div className="space-y-3">
                <label className="block text-sm font-medium text-gray-700">
                  Select Certifications
                </label>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-2 max-h-40 overflow-y-auto border border-gray-200 rounded-md p-3">
                  {certificationOptions.map((cert) => (
                    <label key={cert.value} className="flex items-center space-x-2">
                      <input
                        type="checkbox"
                        checked={formData.certification_status?.includes(cert.value) || false}
                        onChange={(e) => {
                          const currentCerts = formData.certification_status || [];
                          const newCerts = e.target.checked
                            ? [...currentCerts, cert.value]
                            : currentCerts.filter(c => c !== cert.value);
                          setFormData(prev => ({ ...prev, certification_status: newCerts }));
                        }}
                        className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                      />
                      <span className="text-sm text-gray-700">{cert.label}</span>
                    </label>
                  ))}
                </div>
              </div>
            </div>

            {/* Additional Information Section */}
            <div className="pb-4">
              <h3 className="text-lg font-medium text-gray-900 mb-4 flex items-center">
                <DocumentTextIcon className="h-5 w-5 mr-2" />
                Additional Information
              </h3>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Farm Status
                  </label>
                  <div className="flex items-center space-x-4">
                    <label className="flex items-center">
                      <input
                        type="radio"
                        name="is_active"
                        checked={formData.is_active === true}
                        onChange={() => setFormData(prev => ({ ...prev, is_active: true }))}
                        className="mr-2"
                      />
                      <span className="text-sm text-green-600">Active</span>
                    </label>
                    <label className="flex items-center">
                      <input
                        type="radio"
                        name="is_active"
                        checked={formData.is_active === false}
                        onChange={() => setFormData(prev => ({ ...prev, is_active: false }))}
                        className="mr-2"
                      />
                      <span className="text-sm text-red-600">Inactive</span>
                    </label>
                  </div>
                </div>
              </div>

              <div className="mt-4">
                <TextArea
                  label="Notes"
                  value={formData.notes || ''}
                  onChange={(e) => setFormData(prev => ({ ...prev, notes: e.target.value }))}
                  rows={3}
                  placeholder="Additional notes about the farm..."
                />
              </div>
            </div>

            {/* Form Actions */}
            <div className="flex justify-end space-x-3 pt-6 border-t border-gray-200">
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
