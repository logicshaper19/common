import React, { useState, useEffect } from 'react';
import { MapPinIcon, CalendarIcon, DocumentTextIcon, CheckCircleIcon, ExclamationTriangleIcon, BeakerIcon, BuildingOfficeIcon } from '@heroicons/react/24/outline';
import { Card, CardHeader, CardBody } from '../ui/Card';
import { Button } from '../ui/Button';
import { Badge } from '../ui/Badge';
import Select from '../ui/Select';
import { useToast } from '../../contexts/ToastContext';
import { apiClient } from '../../lib/api';

interface GeographicCoordinates {
  latitude: number;
  longitude: number;
  accuracy?: number;
  elevation?: number;
  timestamp?: string;
}

interface FarmLocation {
  id: string;
  name: string;
  registration_number: string;
  farm_type: string;
  farm_size_hectares: number;
  latitude: number;
  longitude: number;
  accuracy_meters: number;
  address: string;
  city: string;
  state_province: string;
  country: string;
  certifications: string[];
  compliance_data: any;
  farm_contact_info: any;
}

interface HarvestData {
  product_id: string;
  selected_farm_id: string;
  certifications: string[];
  harvest_date: string;
  batch_number: string;
  quantity: number;
  unit: string;
  quality_parameters: {
    oil_content?: number;
    moisture_content?: number;
    free_fatty_acid?: number;
    dirt_content?: number;
    kernel_to_fruit_ratio?: number;
  };
  processing_notes: string;
}

interface HarvestDeclarationFormProps {
  productType?: string;
  initialData?: Partial<HarvestData>;
  onSubmit: (harvestData: HarvestData) => void;
  onCancel: () => void;
  isLoading?: boolean;
  disabled?: boolean;
}

const HarvestDeclarationForm: React.FC<HarvestDeclarationFormProps> = ({
  productType: initialProductType,
  initialData,
  onSubmit,
  onCancel,
  isLoading = false,
  disabled = false
}) => {
  const { showToast } = useToast();
  
  // State for farms and products
  const [farms, setFarms] = useState<FarmLocation[]>([]);
  const [products, setProducts] = useState<any[]>([]);
  const [loadingFarms, setLoadingFarms] = useState(true);
  const [selectedFarm, setSelectedFarm] = useState<FarmLocation | null>(null);

  // Product type options
  const productTypeOptions = [
    { value: 'fresh_fruit_bunches', label: 'Fresh Fruit Bunches' },
    { value: 'crude_palm_oil', label: 'Crude Palm Oil' },
    { value: 'palm_kernel_oil', label: 'Palm Kernel Oil' },
    { value: 'palm_kernel_cake', label: 'Palm Kernel Cake' },
    { value: 'empty_fruit_bunches', label: 'Empty Fruit Bunches' },
    { value: 'palm_oil_mill_effluent', label: 'Palm Oil Mill Effluent' },
    { value: 'other', label: 'Other' }
  ];

  // Selected product type state
  const [selectedProductType, setSelectedProductType] = useState(
    initialProductType || productTypeOptions[0].value
  );

  // Form state
  const [harvestData, setHarvestData] = useState<HarvestData>({
    product_id: initialData?.product_id || '',
    selected_farm_id: initialData?.selected_farm_id || '',
    certifications: initialData?.certifications || [],
    harvest_date: initialData?.harvest_date || '',
    batch_number: initialData?.batch_number || '',
    quantity: initialData?.quantity || 0,
    unit: initialData?.unit || 'KGM',
    quality_parameters: initialData?.quality_parameters || {
      oil_content: undefined,
      moisture_content: undefined,
      free_fatty_acid: undefined,
      dirt_content: undefined,
      kernel_to_fruit_ratio: undefined
    },
    processing_notes: initialData?.processing_notes || ''
  });

  const [errors, setErrors] = useState<Record<string, string>>({});
  const [isValidating, setIsValidating] = useState(false);

  // Load farms and products on component mount
  useEffect(() => {
    loadFarms();
    loadProducts();
  }, []);

  // Load farms from the database
  const loadFarms = async () => {
    try {
      setLoadingFarms(true);
      // Use direct API call with full URL since harvest router is mounted at /api, not /api/v1
      const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
      const response = await fetch(`${API_BASE_URL}/api/harvest/farms`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('auth_token')}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      console.log('Loaded farms:', data.farms?.length || 0, 'farms');
      setFarms(data.farms || []);
    } catch (error) {
      console.error('Error loading farms:', error);
      showToast({ 
        title: 'Error', 
        message: 'Failed to load farms. Please try again.', 
        type: 'error' 
      });
    } finally {
      setLoadingFarms(false);
    }
  };

  // Load products from the database
  const loadProducts = async () => {
    try {
      const response = await apiClient.get('/products');
      const data = response.data;
      
      // Handle the complex nested response format from the products API
      let productsArray = [];
      if (data && data.status === 'success' && data.data && Array.isArray(data.data)) {
        // Find the products array in the nested data structure
        for (const item of data.data) {
          if (Array.isArray(item) && item.length >= 2 && item[0] === 'products' && Array.isArray(item[1])) {
            productsArray = item[1];
            break;
          }
        }
      } else if (Array.isArray(data)) {
        productsArray = data;
      } else if (data && Array.isArray(data.data)) {
        productsArray = data.data;
      } else if (data && Array.isArray(data.products)) {
        productsArray = data.products;
      }
      
      console.log('Loaded products:', productsArray.length, 'products');
      setProducts(productsArray);
    } catch (error) {
      console.error('Error loading products:', error);
      setProducts([]); // Ensure products is always an array
      showToast({ 
        title: 'Error', 
        message: 'Failed to load products. Please try again.', 
        type: 'error' 
      });
    }
  };

  // Update selected farm when farm selection changes
  useEffect(() => {
    if (harvestData.selected_farm_id) {
      const farm = farms.find(f => f.id === harvestData.selected_farm_id);
      setSelectedFarm(farm || null);
    } else {
      setSelectedFarm(null);
    }
  }, [harvestData.selected_farm_id, farms]);

  // Update harvestData when initialData changes
  useEffect(() => {
    if (initialData) {
    setHarvestData(prev => ({
      ...prev,
        ...initialData
    }));
    }
  }, [initialData]);

  // Available certifications
  const availableCertifications = [
    { value: 'RSPO', label: 'RSPO (Roundtable on Sustainable Palm Oil)' },
    { value: 'NDPE', label: 'NDPE (No Deforestation, No Peat, No Exploitation)' },
    { value: 'ISPO', label: 'ISPO (Indonesian Sustainable Palm Oil)' },
    { value: 'MSPO', label: 'MSPO (Malaysian Sustainable Palm Oil)' },
    { value: 'Rainforest Alliance', label: 'Rainforest Alliance' },
    { value: 'ISCC', label: 'ISCC (International Sustainability & Carbon Certification)' },
    { value: 'Organic', label: 'Organic Certification' },
    { value: 'Fair Trade', label: 'Fair Trade Certified' }
  ];

  // Cultivation methods
  const cultivationMethods = [
    { value: 'sustainable', label: 'Sustainable Farming' },
    { value: 'organic', label: 'Organic Methods' },
    { value: 'integrated_pest', label: 'Integrated Pest Management' },
    { value: 'water_conservation', label: 'Water Conservation' },
    { value: 'soil_conservation', label: 'Soil Conservation' },
    { value: 'biodiversity', label: 'Biodiversity Protection' }
  ];

  // Generate batch number automatically
  useEffect(() => {
    if (!harvestData.batch_number) {
      const today = new Date();
      const year = today.getFullYear();
      const month = String(today.getMonth() + 1).padStart(2, '0');
      const day = String(today.getDate()).padStart(2, '0');
      const hours = String(today.getHours()).padStart(2, '0');
      const minutes = String(today.getMinutes()).padStart(2, '0');
      const seconds = String(today.getSeconds()).padStart(2, '0');
      const random = Math.floor(Math.random() * 100).toString().padStart(2, '0');
      
      // Generate a more unique batch ID: H-YYYYMMDD-HHMMSS-XX
      const batchNumber = `H-${year}${month}${day}-${hours}${minutes}${seconds}-${random}`;
      
      setHarvestData(prev => ({
        ...prev,
        batch_number: batchNumber
      }));
    }
  }, [harvestData.batch_number]);

  // Update harvest data
  const updateHarvestData = (field: string, value: any) => {
    setHarvestData(prev => ({
      ...prev,
      [field]: value
    }));
    
    // Clear error when user starts typing
    if (errors[field]) {
      setErrors(prev => {
        const newErrors = { ...prev };
        delete newErrors[field];
        return newErrors;
      });
    }
  };

  // Handle farm selection
  const handleFarmSelection = (farmId: string) => {
    updateHarvestData('selected_farm_id', farmId);
  };

  // Handle certification changes
  const handleCertificationChange = (certification: string, checked: boolean) => {
    const newCertifications = checked
      ? [...harvestData.certifications, certification]
      : harvestData.certifications.filter(c => c !== certification);
    
    updateHarvestData('certifications', newCertifications);
    
    // Clear certification error
    if (errors.certifications) {
      setErrors(prev => {
        const newErrors = { ...prev };
        delete newErrors.certifications;
        return newErrors;
      });
    }
  };


  // Validate form
  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    // Validate product selection
    if (!harvestData.product_id) {
      newErrors.product_id = 'Product selection is required';
    }

    // Validate farm selection
    if (!harvestData.selected_farm_id) {
      newErrors.selected_farm_id = 'Farm selection is required';
    }

    // Validate harvest date
    if (!harvestData.harvest_date) {
      newErrors.harvest_date = 'Harvest date is required';
    }

    // Validate batch number
    if (!harvestData.batch_number.trim()) {
      newErrors.batch_number = 'Batch number is required';
    }

    // Validate quantity
    if (!harvestData.quantity || harvestData.quantity <= 0) {
      newErrors.quantity = 'Quantity must be greater than 0';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  // Handle form submission
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    console.log('Form submitted with data:', harvestData);
    
    if (!validateForm()) {
      console.log('Form validation failed');
      showToast({ title: 'Validation Error', message: 'Please fix the errors before submitting', type: 'error' });
      return;
    }

    console.log('Form validation passed, calling onSubmit');
    setIsValidating(true);
    
    try {
      await onSubmit(harvestData);
      console.log('onSubmit completed successfully');
      
      // Reset form after successful submission
      setHarvestData({
        product_id: '',
        selected_farm_id: '',
        certifications: [],
        harvest_date: '',
        batch_number: '',
        quantity: 0,
        unit: 'KGM',
        quality_parameters: {
          oil_content: undefined,
          moisture_content: undefined,
          free_fatty_acid: undefined,
          dirt_content: undefined,
          kernel_to_fruit_ratio: undefined
        },
        processing_notes: ''
      });
      setSelectedFarm(null);
      setErrors({});
      
      showToast({ title: 'Success', message: 'Harvest declaration submitted successfully', type: 'success' });
    } catch (error) {
      console.error('Error submitting harvest declaration:', error);
      showToast({ title: 'Error', message: 'Failed to submit harvest declaration', type: 'error' });
    } finally {
      setIsValidating(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* Header */}
      <div className="text-center mb-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">
          Declare Harvest
        </h2>
        <p className="text-gray-600 mb-4">
          Record a new harvest event to create a batch with origin data
        </p>
        
        {/* Product Selection */}
        <div className="max-w-md mx-auto">
          <label htmlFor="product-selection" className="block text-sm font-medium text-gray-700 mb-2">
            Select Product
          </label>
          <select
            id="product-selection"
            value={harvestData.product_id}
            onChange={(e) => updateHarvestData('product_id', e.target.value)}
            disabled={disabled}
            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-purple-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
          >
            <option value="">Select a product...</option>
            {Array.isArray(products) && products.map((product) => (
              <option key={product.id} value={product.id}>
                {product.name} ({product.category})
              </option>
            ))}
          </select>
          {errors.product_id && (
            <div className="mt-1 flex items-center space-x-2 text-red-600">
              <ExclamationTriangleIcon className="h-4 w-4" />
              <span className="text-sm">{errors.product_id}</span>
            </div>
          )}
        </div>
        
        <Badge variant="primary" className="mt-3">
          Harvest Declaration
        </Badge>
      </div>

      {/* Farm Selection */}
      <Card>
        <CardHeader 
          title="Farm Selection" 
          subtitle="Select the farm where this harvest took place"
          icon={<BuildingOfficeIcon className="h-5 w-5" />}
        />
        <CardBody>
          {loadingFarms ? (
            <div className="text-center py-4">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-600 mx-auto"></div>
              <p className="mt-2 text-gray-600">Loading farms...</p>
            </div>
          ) : (
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Select Farm *
                </label>
                <select
                  value={harvestData.selected_farm_id}
                  onChange={(e) => handleFarmSelection(e.target.value)}
            disabled={disabled}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
                >
                  <option value="">Select a farm...</option>
                  {Array.isArray(farms) && farms.map((farm) => (
                    <option key={farm.id} value={farm.id}>
                      {farm.name} ({farm.registration_number}) - {farm.farm_size_hectares} hectares
                    </option>
                  ))}
                </select>
                {errors.selected_farm_id && (
                  <div className="mt-1 flex items-center space-x-2 text-red-600">
              <ExclamationTriangleIcon className="h-4 w-4" />
                    <span className="text-sm">{errors.selected_farm_id}</span>
                  </div>
                )}
              </div>

              {/* Selected Farm Details */}
              {selectedFarm && (
                <div className="bg-gray-50 rounded-lg p-4">
                  <h4 className="font-medium text-gray-900 mb-2">Selected Farm Details</h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="font-medium text-gray-700">Farm Name:</span>
                      <p className="text-gray-600">{selectedFarm.name}</p>
                    </div>
                    <div>
                      <span className="font-medium text-gray-700">Registration:</span>
                      <p className="text-gray-600">{selectedFarm.registration_number}</p>
                    </div>
                    <div>
                      <span className="font-medium text-gray-700">Size:</span>
                      <p className="text-gray-600">{selectedFarm.farm_size_hectares} hectares</p>
                    </div>
                    <div>
                      <span className="font-medium text-gray-700">Type:</span>
                      <p className="text-gray-600 capitalize">{selectedFarm.farm_type.replace('_', ' ')}</p>
                    </div>
                    <div>
                      <span className="font-medium text-gray-700">Location:</span>
                      <p className="text-gray-600">{selectedFarm.city}, {selectedFarm.state_province}, {selectedFarm.country}</p>
                    </div>
                    <div>
                      <span className="font-medium text-gray-700">Coordinates:</span>
                      <p className="text-gray-600">{selectedFarm.latitude}, {selectedFarm.longitude}</p>
                    </div>
                    <div className="md:col-span-2">
                      <span className="font-medium text-gray-700">Certifications:</span>
                      <div className="flex flex-wrap gap-1 mt-1">
                        {selectedFarm.certifications.map((cert) => (
                          <Badge key={cert} variant="secondary" size="sm">
                            {cert}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}
        </CardBody>
      </Card>

      {/* Harvest Information */}
      <Card>
        <CardHeader 
          title="Harvest Information" 
          subtitle="Details about the harvest event"
          icon={<CalendarIcon className="h-5 w-5" />}
        />
        <CardBody className="space-y-4">
          {/* Harvest Date */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Harvest Date *
            </label>
            <input
              type="date"
              value={harvestData.harvest_date}
              onChange={(e) => updateHarvestData('harvest_date', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
              disabled={disabled}
            />
            {errors.harvest_date && (
              <div className="mt-1 flex items-center space-x-2 text-red-600">
                <ExclamationTriangleIcon className="h-4 w-4" />
                <span className="text-sm">{errors.harvest_date}</span>
              </div>
            )}
          </div>

          {/* Batch Number */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Batch Number * (Auto-generated)
            </label>
            <input
              type="text"
              value={harvestData.batch_number}
              className="w-full px-3 py-2 border border-gray-300 rounded-md bg-gray-50 text-gray-600"
              required
              disabled={true}
              readOnly
            />
            <p className="mt-1 text-xs text-gray-500">
              Batch number is automatically generated for traceability
            </p>
          </div>

          {/* Quantity and Unit */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Quantity *
              </label>
              <input
                type="number"
                min="0"
                step="0.01"
                value={harvestData.quantity}
                onChange={(e) => updateHarvestData('quantity', parseFloat(e.target.value) || 0)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                required
                disabled={disabled}
                placeholder="Enter quantity"
              />
              {errors.quantity && (
                <div className="mt-1 flex items-center space-x-2 text-red-600">
                  <ExclamationTriangleIcon className="h-4 w-4" />
                  <span className="text-sm">{errors.quantity}</span>
                </div>
              )}
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Unit *
              </label>
              <select
                value={harvestData.unit}
                onChange={(e) => updateHarvestData('unit', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                required
                disabled={disabled}
              >
                <option value="KGM">Kilograms (KGM)</option>
                <option value="TON">Metric Tons (TON)</option>
                <option value="LBS">Pounds (LBS)</option>
                <option value="LTR">Liters (LTR)</option>
                <option value="M3">Cubic Meters (M3)</option>
              </select>
            </div>
          </div>
        </CardBody>
      </Card>


      {/* Certifications */}
      <Card>
        <CardHeader 
          title="Certifications" 
          subtitle="Select applicable certifications for this harvest"
        />
        <CardBody>
          <div className="grid grid-cols-1 gap-2">
            {availableCertifications.map((cert) => (
              <label key={cert.value} className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  checked={harvestData.certifications.includes(cert.value)}
                  onChange={(e) => handleCertificationChange(cert.value, e.target.checked)}
                  className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  disabled={disabled}
                />
                <span className="text-sm text-gray-700">{cert.label}</span>
              </label>
            ))}
          </div>
          {errors.certifications && (
            <div className="mt-2 flex items-center space-x-2 text-red-600">
              <ExclamationTriangleIcon className="h-4 w-4" />
              <span className="text-sm">{errors.certifications}</span>
            </div>
          )}
        </CardBody>
      </Card>

      {/* Quality Parameters */}
      <Card>
        <CardHeader 
          title="Quality Parameters" 
          subtitle="Quality measurements for this harvest"
          icon={<BeakerIcon className="h-5 w-5" />}
        />
        <CardBody className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Oil Content (%)
              </label>
              <input
                type="number"
                step="0.1"
                min="0"
                max="100"
                value={harvestData.quality_parameters.oil_content || ''}
                onChange={(e) => updateHarvestData('quality_parameters', {
                  ...harvestData.quality_parameters,
                  oil_content: parseFloat(e.target.value) || 0
                })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                disabled={disabled}
                placeholder="22.5"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Moisture Content (%)
              </label>
              <input
                type="number"
                step="0.1"
                min="0"
                max="100"
                value={harvestData.quality_parameters.moisture_content || ''}
                onChange={(e) => updateHarvestData('quality_parameters', {
                  ...harvestData.quality_parameters,
                  moisture_content: parseFloat(e.target.value) || 0
                })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                disabled={disabled}
                placeholder="18.2"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Free Fatty Acid (%)
              </label>
              <input
                type="number"
                step="0.1"
                min="0"
                max="100"
                value={harvestData.quality_parameters.free_fatty_acid || ''}
                onChange={(e) => updateHarvestData('quality_parameters', {
                  ...harvestData.quality_parameters,
                  free_fatty_acid: parseFloat(e.target.value) || 0
                })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                disabled={disabled}
                placeholder="2.1"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Dirt Content (%)
              </label>
              <input
                type="number"
                step="0.1"
                min="0"
                max="100"
                value={harvestData.quality_parameters.dirt_content || ''}
                onChange={(e) => updateHarvestData('quality_parameters', {
                  ...harvestData.quality_parameters,
                  dirt_content: parseFloat(e.target.value) || 0
                })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                disabled={disabled}
                placeholder="1.5"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Kernel to Fruit Ratio (%)
              </label>
              <input
                type="number"
                step="0.1"
                min="0"
                max="100"
                value={harvestData.quality_parameters.kernel_to_fruit_ratio || ''}
                onChange={(e) => updateHarvestData('quality_parameters', {
                  ...harvestData.quality_parameters,
                  kernel_to_fruit_ratio: parseFloat(e.target.value) || 0
                })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                disabled={disabled}
                placeholder="65.0"
              />
            </div>
          </div>
        </CardBody>
      </Card>

      {/* Processing Notes */}
      <Card>
        <CardHeader 
          title="Processing Notes" 
          subtitle="Additional notes about this harvest"
        />
        <CardBody>
          <textarea
            value={harvestData.processing_notes}
            onChange={(e) => updateHarvestData('processing_notes', e.target.value)}
            rows={3}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="Add any additional notes about this harvest..."
            disabled={disabled}
          />
        </CardBody>
      </Card>

      {/* Form Actions */}
      <div className="flex justify-end space-x-3 pt-6">
        <Button
          type="button"
          variant="secondary"
          onClick={onCancel}
          disabled={isLoading || disabled}
        >
          Cancel
        </Button>
        <Button
          type="submit"
          variant="primary"
          disabled={isLoading || disabled || isValidating}
          isLoading={isLoading || isValidating}
        >
          <CheckCircleIcon className="h-4 w-4 mr-2" />
          Declare Harvest
        </Button>
      </div>
    </form>
  );
};

export default HarvestDeclarationForm;
