/**
 * Originator Confirmation Form
 * Specialized form for originators to capture origin data during PO confirmation
 */
import React, { useState, useEffect } from 'react';
import {
  CalendarIcon,
  DocumentTextIcon,
  ShieldCheckIcon,
  BeakerIcon,
  BuildingOfficeIcon,
  MapPinIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon
} from '@heroicons/react/24/outline';
import { Card, CardHeader, CardBody } from '../ui/Card';
import Input from '../ui/Input';
import Select from '../ui/Select';
import TextArea from '../ui/Textarea';
import Button from '../ui/Button';
import Badge from '../ui/Badge';
import MapInput from './MapInput';
import { useToast } from '../../contexts/ToastContext';

interface GeographicCoordinates {
  latitude: number;
  longitude: number;
  accuracy?: number;
  elevation?: number;
  timestamp?: string;
}

interface FarmInformation {
  farm_id: string;
  farm_name: string;
  farm_size_hectares?: number;
  establishment_year?: number;
  owner_name?: string;
  plantation_type: 'own_estate' | 'smallholder' | 'mixed';
  cultivation_methods: string[];
}

interface QualityParameters {
  oil_content?: number;
  moisture_content?: number;
  free_fatty_acid?: number;
  dirt_content?: number;
  kernel_to_fruit_ratio?: number;
}

interface OriginData {
  geographic_coordinates: GeographicCoordinates;
  certifications: string[];
  harvest_date?: string;
  farm_information?: FarmInformation;
  batch_number?: string;
  quality_parameters?: QualityParameters;
  processing_notes?: string;
}

interface OriginatorConfirmationFormProps {
  purchaseOrderId: string;
  productType: string;
  onSubmit: (originData: OriginData) => void;
  onCancel: () => void;
  isLoading?: boolean;
  disabled?: boolean;
}

const OriginatorConfirmationForm: React.FC<OriginatorConfirmationFormProps> = ({
  purchaseOrderId,
  productType,
  onSubmit,
  onCancel,
  isLoading = false,
  disabled = false
}) => {
  const { showToast } = useToast();

  // Form state
  const [originData, setOriginData] = useState<OriginData>({
    geographic_coordinates: { latitude: 0, longitude: 0 },
    certifications: [],
    harvest_date: '',
    farm_information: {
      farm_id: '',
      farm_name: '',
      plantation_type: 'smallholder',
      cultivation_methods: []
    },
    batch_number: '',
    quality_parameters: {},
    processing_notes: ''
  });

  const [errors, setErrors] = useState<Record<string, string>>({});
  const [isValidating, setIsValidating] = useState(false);

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

  // Generate batch number
  useEffect(() => {
    if (!originData.batch_number) {
      const today = new Date();
      const dateStr = today.toISOString().split('T')[0].replace(/-/g, '');
      const randomSuffix = Math.random().toString(36).substr(2, 4).toUpperCase();
      const batchNumber = `HARVEST-${dateStr}-${randomSuffix}`;
      
      setOriginData(prev => ({
        ...prev,
        batch_number: batchNumber
      }));
    }
  }, [originData.batch_number]);

  // Validate form
  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    // Required fields validation
    if (!originData.geographic_coordinates.latitude || !originData.geographic_coordinates.longitude) {
      newErrors.coordinates = 'GPS coordinates are required';
    }

    if (!originData.harvest_date) {
      newErrors.harvest_date = 'Harvest date is required';
    } else {
      const harvestDate = new Date(originData.harvest_date);
      const today = new Date();
      const maxAge = new Date();
      maxAge.setDate(today.getDate() - 30); // Max 30 days old

      if (harvestDate > today) {
        newErrors.harvest_date = 'Harvest date cannot be in the future';
      } else if (harvestDate < maxAge) {
        newErrors.harvest_date = 'Harvest date cannot be more than 30 days old';
      }
    }

    if (!originData.farm_information?.farm_id) {
      newErrors.farm_id = 'Farm ID is required';
    }

    if (!originData.farm_information?.farm_name) {
      newErrors.farm_name = 'Farm name is required';
    }

    if (originData.certifications.length === 0) {
      newErrors.certifications = 'At least one certification is required';
    }

    // Quality parameters validation
    if (originData.quality_parameters?.oil_content && 
        (originData.quality_parameters.oil_content < 0 || originData.quality_parameters.oil_content > 100)) {
      newErrors.oil_content = 'Oil content must be between 0-100%';
    }

    if (originData.quality_parameters?.moisture_content && 
        (originData.quality_parameters.moisture_content < 0 || originData.quality_parameters.moisture_content > 100)) {
      newErrors.moisture_content = 'Moisture content must be between 0-100%';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  // Handle form submission
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) {
      showToast({
        type: 'error',
        title: 'Validation Error',
        message: 'Please correct the errors before submitting.'
      });
      return;
    }

    setIsValidating(true);
    
    try {
      await onSubmit(originData);
    } catch (error) {
      console.error('Submission error:', error);
      showToast({
        type: 'error',
        title: 'Submission Failed',
        message: 'Failed to submit origin data. Please try again.'
      });
    } finally {
      setIsValidating(false);
    }
  };

  // Update origin data
  const updateOriginData = (field: string, value: any) => {
    setOriginData(prev => ({
      ...prev,
      [field]: value
    }));
    
    // Clear related errors
    if (errors[field]) {
      setErrors(prev => {
        const newErrors = { ...prev };
        delete newErrors[field];
        return newErrors;
      });
    }
  };

  // Update farm information
  const updateFarmInfo = (field: string, value: any) => {
    setOriginData(prev => ({
      ...prev,
      farm_information: {
        ...prev.farm_information!,
        [field]: value
      }
    }));
    
    if (errors[field]) {
      setErrors(prev => {
        const newErrors = { ...prev };
        delete newErrors[field];
        return newErrors;
      });
    }
  };

  // Update quality parameters
  const updateQualityParams = (field: string, value: number) => {
    setOriginData(prev => ({
      ...prev,
      quality_parameters: {
        ...prev.quality_parameters,
        [field]: value
      }
    }));
    
    if (errors[field]) {
      setErrors(prev => {
        const newErrors = { ...prev };
        delete newErrors[field];
        return newErrors;
      });
    }
  };

  // Handle certification selection
  const handleCertificationChange = (certificationValue: string, checked: boolean) => {
    setOriginData(prev => ({
      ...prev,
      certifications: checked
        ? [...prev.certifications, certificationValue]
        : prev.certifications.filter(c => c !== certificationValue)
    }));
    
    if (errors.certifications) {
      setErrors(prev => {
        const newErrors = { ...prev };
        delete newErrors.certifications;
        return newErrors;
      });
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* Header */}
      <div className="text-center mb-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">
          Origin Data Capture
        </h2>
        <p className="text-gray-600">
          Provide detailed origin information for Purchase Order {purchaseOrderId}
        </p>
        <Badge variant="primary" className="mt-2">
          {productType} - Originator Confirmation
        </Badge>
      </div>

      {/* GPS Coordinates */}
      <Card>
        <CardHeader 
          title="Geographic Location" 
          subtitle="Precise GPS coordinates of origin"
          icon={<MapPinIcon className="h-5 w-5" />}
        />
        <CardBody>
          <MapInput
            value={originData.geographic_coordinates}
            onChange={(coords) => updateOriginData('geographic_coordinates', coords)}
            required
            disabled={disabled}
            validationRegion="southeast_asia"
          />
          {errors.coordinates && (
            <div className="mt-2 flex items-center space-x-2 text-red-600">
              <ExclamationTriangleIcon className="h-4 w-4" />
              <span className="text-sm">{errors.coordinates}</span>
            </div>
          )}
        </CardBody>
      </Card>

      {/* Harvest Information */}
      <Card>
        <CardHeader 
          title="Harvest Information" 
          subtitle="Date and batch details"
          icon={<CalendarIcon className="h-5 w-5" />}
        />
        <CardBody>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Harvest Date <span className="text-red-500">*</span>
              </label>
              <Input
                type="date"
                value={originData.harvest_date}
                onChange={(e) => updateOriginData('harvest_date', e.target.value)}
                disabled={disabled}
                errorMessage={errors.harvest_date}
                max={new Date().toISOString().split('T')[0]}
              />
              {errors.harvest_date && (
                <div className="mt-1 text-sm text-red-600">{errors.harvest_date}</div>
              )}
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Batch Number
              </label>
              <Input
                type="text"
                value={originData.batch_number}
                onChange={(e) => updateOriginData('batch_number', e.target.value)}
                disabled={disabled}
                placeholder="Auto-generated"
              />
            </div>
          </div>
        </CardBody>
      </Card>

      {/* Farm Information */}
      <Card>
        <CardHeader 
          title="Farm Information" 
          subtitle="Detailed farm and plantation data"
          icon={<BuildingOfficeIcon className="h-5 w-5" />}
        />
        <CardBody>
          <div className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Farm ID <span className="text-red-500">*</span>
                </label>
                <Input
                  type="text"
                  value={originData.farm_information?.farm_id || ''}
                  onChange={(e) => updateFarmInfo('farm_id', e.target.value)}
                  disabled={disabled}
                  errorMessage={errors.farm_id}
                  placeholder="FARM-KAL-001"
                />
                {errors.farm_id && (
                  <div className="mt-1 text-sm text-red-600">{errors.farm_id}</div>
                )}
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Farm Name <span className="text-red-500">*</span>
                </label>
                <Input
                  type="text"
                  value={originData.farm_information?.farm_name || ''}
                  onChange={(e) => updateFarmInfo('farm_name', e.target.value)}
                  disabled={disabled}
                  errorMessage={errors.farm_name}
                  placeholder="Plantation Name"
                />
                {errors.farm_name && (
                  <div className="mt-1 text-sm text-red-600">{errors.farm_name}</div>
                )}
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Plantation Type
                </label>
                <Select
                  value={originData.farm_information?.plantation_type || 'smallholder'}
                  onChange={(e) => updateFarmInfo('plantation_type', e.target.value)}
                  disabled={disabled}
                  options={[
                    { label: 'Smallholder', value: 'smallholder' },
                    { label: 'Own Estate', value: 'own_estate' },
                    { label: 'Mixed Operations', value: 'mixed' }
                  ]}
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Farm Size (Hectares)
                </label>
                <Input
                  type="number"
                  step="0.1"
                  value={originData.farm_information?.farm_size_hectares || ''}
                  onChange={(e) => updateFarmInfo('farm_size_hectares', parseFloat(e.target.value))}
                  disabled={disabled}
                  placeholder="100.5"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Establishment Year
                </label>
                <Input
                  type="number"
                  value={originData.farm_information?.establishment_year || ''}
                  onChange={(e) => updateFarmInfo('establishment_year', parseInt(e.target.value))}
                  disabled={disabled}
                  placeholder="2010"
                  min="1900"
                  max={new Date().getFullYear()}
                />
              </div>
            </div>
          </div>
        </CardBody>
      </Card>

      {/* Certifications */}
      <Card>
        <CardHeader 
          title="Certifications" 
          subtitle="Sustainability and quality certifications"
          icon={<ShieldCheckIcon className="h-5 w-5" />}
        />
        <CardBody>
          <div className="space-y-3">
            {availableCertifications.map((cert) => (
              <label key={cert.value} className="flex items-center space-x-3">
                <input
                  type="checkbox"
                  checked={originData.certifications.includes(cert.value)}
                  onChange={(e) => handleCertificationChange(cert.value, e.target.checked)}
                  disabled={disabled}
                  className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
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
          subtitle="Product quality measurements"
          icon={<BeakerIcon className="h-5 w-5" />}
        />
        <CardBody>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Oil Content (%)
              </label>
              <Input
                type="number"
                step="0.1"
                value={originData.quality_parameters?.oil_content || ''}
                onChange={(e) => updateQualityParams('oil_content', parseFloat(e.target.value))}
                disabled={disabled}
                placeholder="22.5"
                min="0"
                max="100"
                errorMessage={errors.oil_content}
              />
              {errors.oil_content && (
                <div className="mt-1 text-sm text-red-600">{errors.oil_content}</div>
              )}
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Moisture Content (%)
              </label>
              <Input
                type="number"
                step="0.1"
                value={originData.quality_parameters?.moisture_content || ''}
                onChange={(e) => updateQualityParams('moisture_content', parseFloat(e.target.value))}
                disabled={disabled}
                placeholder="18.2"
                min="0"
                max="100"
                errorMessage={errors.moisture_content}
              />
              {errors.moisture_content && (
                <div className="mt-1 text-sm text-red-600">{errors.moisture_content}</div>
              )}
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Free Fatty Acid (%)
              </label>
              <Input
                type="number"
                step="0.1"
                value={originData.quality_parameters?.free_fatty_acid || ''}
                onChange={(e) => updateQualityParams('free_fatty_acid', parseFloat(e.target.value))}
                disabled={disabled}
                placeholder="2.1"
                min="0"
                max="100"
              />
            </div>
          </div>
        </CardBody>
      </Card>

      {/* Processing Notes */}
      <Card>
        <CardHeader 
          title="Processing Notes" 
          subtitle="Additional information and handling notes"
          icon={<DocumentTextIcon className="h-5 w-5" />}
        />
        <CardBody>
          <TextArea
            value={originData.processing_notes || ''}
            onChange={(e) => updateOriginData('processing_notes', e.target.value)}
            disabled={disabled}
            placeholder="Enter any additional processing notes, handling instructions, or relevant information..."
            rows={4}
          />
        </CardBody>
      </Card>

      {/* Form Actions */}
      <div className="flex justify-end space-x-4 pt-6 border-t border-gray-200">
        <Button
          type="button"
          variant="outline"
          onClick={onCancel}
          disabled={isLoading || isValidating}
        >
          Cancel
        </Button>
        <Button
          type="submit"
          variant="primary"
          isLoading={isLoading || isValidating}
          disabled={disabled}
          leftIcon={<CheckCircleIcon className="h-4 w-4" />}
        >
          Confirm with Origin Data
        </Button>
      </div>
    </form>
  );
};

export default OriginatorConfirmationForm;
