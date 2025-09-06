/**
 * Originator Confirmation Form Component
 * Handles originator-specific confirmation workflow with origin data and location input
 */
import React from 'react';
import { ConfirmationConfig, OriginatorConfirmationData } from '../../types/confirmation';
import { PurchaseOrder } from '../../lib/api';
import Input from '../ui/Input';
import Select from '../ui/Select';
import Textarea from '../ui/Textarea';
import MapInput from '../ui/MapInput';
import { Card, CardHeader, CardBody } from '../ui/Card';
import Badge from '../ui/Badge';

interface OriginatorConfirmationFormProps {
  data: OriginatorConfirmationData;
  onChange: (data: Partial<OriginatorConfirmationData>) => void;
  currentStep: number;
  config: ConfirmationConfig;
  purchaseOrder: PurchaseOrder;
}

const OriginatorConfirmationForm: React.FC<OriginatorConfirmationFormProps> = ({
  data,
  onChange,
  currentStep,
  config,
  purchaseOrder
}) => {
  const currentStepInfo = config.steps[currentStep];

  // Handle field changes
  const handleFieldChange = (field: string, value: any) => {
    onChange({ [field]: value });
  };

  // Handle nested field changes
  const handleNestedFieldChange = (parentField: string, field: string, value: any) => {
    const currentParentValue = data[parentField as keyof OriginatorConfirmationData] || {};
    onChange({
      [parentField]: {
        ...(typeof currentParentValue === 'object' ? currentParentValue : {}),
        [field]: value
      }
    });
  };

  // Handle certification changes
  const handleCertificationChange = (certifications: string[]) => {
    handleNestedFieldChange('origin_data', 'certifications', certifications);
  };

  // Render step content based on current step
  const renderStepContent = () => {
    switch (currentStepInfo?.id) {
      case 'basic_info':
        return (
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <Input
                label="Confirmed Quantity"
                type="number"
                value={data.confirmed_quantity?.toString() || ''}
                onChange={(e) => handleFieldChange('confirmed_quantity', parseFloat(e.target.value) || 0)}
                placeholder="Enter confirmed quantity"
                required
                step="0.001"
                min="0"
                helperText={`Original order: ${purchaseOrder.quantity} ${purchaseOrder.unit}`}
              />

              <Select
                label="Unit"
                value={data.unit || ''}
                onChange={(e) => handleFieldChange('unit', e.target.value)}
                required
                options={[
                  { label: 'Kilograms (KG)', value: 'KG' },
                  { label: 'Pounds (LB)', value: 'LB' },
                  { label: 'Tons (TON)', value: 'TON' },
                  { label: 'Liters (L)', value: 'L' },
                  { label: 'Gallons (GAL)', value: 'GAL' },
                  { label: 'Pieces (PCS)', value: 'PCS' }
                ]}
              />
            </div>

            <Input
              label="Confirmation Date"
              type="date"
              value={data.confirmation_date || ''}
              onChange={(e) => handleFieldChange('confirmation_date', e.target.value)}
              required
              max={new Date().toISOString().split('T')[0]}
            />

            <Textarea
              label="Notes"
              value={data.notes || ''}
              onChange={(e) => handleFieldChange('notes', e.target.value)}
              placeholder="Additional notes or comments about this confirmation"
              rows={3}
            />
          </div>
        );

      case 'origin_data':
        return (
          <div className="space-y-6">
            <Card>
              <CardHeader title="Farm and Cultivation Information" />
              <CardBody>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <Input
                    label="Farm Name"
                    value={data.origin_data?.farm_name || ''}
                    onChange={(e) => handleNestedFieldChange('origin_data', 'farm_name', e.target.value)}
                    placeholder="Name of the farm or production facility"
                  />

                  <Input
                    label="Farmer/Producer Name"
                    value={data.origin_data?.farmer_name || ''}
                    onChange={(e) => handleNestedFieldChange('origin_data', 'farmer_name', e.target.value)}
                    placeholder="Name of the farmer or producer"
                  />

                  <Input
                    label="Harvest Date"
                    type="date"
                    value={data.origin_data?.harvest_date || ''}
                    onChange={(e) => handleNestedFieldChange('origin_data', 'harvest_date', e.target.value)}
                    required
                    max={new Date().toISOString().split('T')[0]}
                  />

                  <Input
                    label="Planting Date"
                    type="date"
                    value={data.origin_data?.planting_date || ''}
                    onChange={(e) => handleNestedFieldChange('origin_data', 'planting_date', e.target.value)}
                    max={data.origin_data?.harvest_date || new Date().toISOString().split('T')[0]}
                  />

                  <Select
                    label="Cultivation Method"
                    value={data.origin_data?.cultivation_method || ''}
                    onChange={(e) => handleNestedFieldChange('origin_data', 'cultivation_method', e.target.value)}
                    required
                    options={[
                      { label: 'Organic', value: 'organic' },
                      { label: 'Conventional', value: 'conventional' },
                      { label: 'Transitional', value: 'transitional' }
                    ]}
                  />

                  <Select
                    label="Irrigation Method"
                    value={data.origin_data?.irrigation_method || ''}
                    onChange={(e) => handleNestedFieldChange('origin_data', 'irrigation_method', e.target.value)}
                    options={[
                      { label: 'Rain Fed', value: 'rain_fed' },
                      { label: 'Drip Irrigation', value: 'drip' },
                      { label: 'Sprinkler', value: 'sprinkler' },
                      { label: 'Flood Irrigation', value: 'flood' },
                      { label: 'Other', value: 'other' }
                    ]}
                  />

                  <Input
                    label="Field Size"
                    type="number"
                    value={data.origin_data?.field_size?.toString() || ''}
                    onChange={(e) => handleNestedFieldChange('origin_data', 'field_size', parseFloat(e.target.value) || 0)}
                    placeholder="Field size"
                    step="0.1"
                    min="0"
                  />

                  <Select
                    label="Field Size Unit"
                    value={data.origin_data?.field_size_unit || ''}
                    onChange={(e) => handleNestedFieldChange('origin_data', 'field_size_unit', e.target.value)}
                    options={[
                      { label: 'Hectares', value: 'hectares' },
                      { label: 'Acres', value: 'acres' },
                      { label: 'Square Meters', value: 'sqm' },
                      { label: 'Square Feet', value: 'sqft' }
                    ]}
                  />

                  <Input
                    label="Soil Type"
                    value={data.origin_data?.soil_type || ''}
                    onChange={(e) => handleNestedFieldChange('origin_data', 'soil_type', e.target.value)}
                    placeholder="e.g., Clay, Sandy, Loam"
                  />

                  <Input
                    label="Climate Zone"
                    value={data.origin_data?.climate_zone || ''}
                    onChange={(e) => handleNestedFieldChange('origin_data', 'climate_zone', e.target.value)}
                    placeholder="e.g., Tropical, Temperate, Arid"
                  />

                  <Input
                    label="Elevation (meters)"
                    type="number"
                    value={data.origin_data?.elevation?.toString() || ''}
                    onChange={(e) => handleNestedFieldChange('origin_data', 'elevation', parseFloat(e.target.value) || 0)}
                    placeholder="Elevation above sea level"
                    step="1"
                    min="0"
                  />
                </div>

                <div className="mt-6">
                  <label className="block text-sm font-medium text-neutral-700 mb-3">
                    Certifications
                  </label>
                  <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                    {[
                      'Organic',
                      'Fair Trade',
                      'Rainforest Alliance',
                      'UTZ Certified',
                      'Bird Friendly',
                      'Shade Grown',
                      'Direct Trade',
                      'C.A.F.E. Practices'
                    ].map((cert) => (
                      <label key={cert} className="flex items-center space-x-2">
                        <input
                          type="checkbox"
                          checked={data.origin_data?.certifications?.includes(cert) || false}
                          onChange={(e) => {
                            const current = data.origin_data?.certifications || [];
                            const updated = e.target.checked
                              ? [...current, cert]
                              : current.filter(c => c !== cert);
                            handleCertificationChange(updated);
                          }}
                          className="rounded border-neutral-300 text-primary-600 focus:ring-primary-500"
                        />
                        <span className="text-sm text-neutral-700">{cert}</span>
                      </label>
                    ))}
                  </div>
                </div>

                <Textarea
                  label="Processing Notes"
                  value={data.origin_data?.processing_notes || ''}
                  onChange={(e) => handleNestedFieldChange('origin_data', 'processing_notes', e.target.value)}
                  placeholder="Additional notes about cultivation, processing, or handling"
                  rows={3}
                />
              </CardBody>
            </Card>
          </div>
        );

      case 'location_data':
        return (
          <div className="space-y-6">
            <Card>
              <CardHeader title="Harvest Location" />
              <CardBody>
                <MapInput
                  label="Harvest Location"
                  value={data.harvest_location}
                  onChange={(location) => handleFieldChange('harvest_location', location)}
                  required
                  placeholder="Select the location where this product was harvested"
                />
              </CardBody>
            </Card>

            <Card>
              <CardHeader 
                title="Storage Location" 
                action={<Badge variant="secondary" size="sm">Optional</Badge>}
              />
              <CardBody>
                <MapInput
                  label="Storage Location"
                  value={data.storage_location}
                  onChange={(location) => handleFieldChange('storage_location', location)}
                  placeholder="Select the location where this product is stored (if different from harvest location)"
                />
              </CardBody>
            </Card>

            <Input
              label="Traceability Code"
              value={data.traceability_code || ''}
              onChange={(e) => handleFieldChange('traceability_code', e.target.value)}
              placeholder="Internal traceability or lot code"
              helperText="Optional internal code for tracking this specific batch"
            />
          </div>
        );

      case 'quality_metrics':
        return (
          <div className="space-y-6">
            <Card>
              <CardHeader title="Quality Metrics" />
              <CardBody>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  <Input
                    label="Moisture Content (%)"
                    type="number"
                    value={data.quality_metrics?.moisture_content?.toString() || ''}
                    onChange={(e) => handleNestedFieldChange('quality_metrics', 'moisture_content', parseFloat(e.target.value) || 0)}
                    placeholder="0-100"
                    step="0.1"
                    min="0"
                    max="100"
                  />

                  <Input
                    label="Purity Percentage (%)"
                    type="number"
                    value={data.quality_metrics?.purity_percentage?.toString() || ''}
                    onChange={(e) => handleNestedFieldChange('quality_metrics', 'purity_percentage', parseFloat(e.target.value) || 0)}
                    placeholder="0-100"
                    step="0.1"
                    min="0"
                    max="100"
                  />

                  <Input
                    label="Grade"
                    value={data.quality_metrics?.grade || ''}
                    onChange={(e) => handleNestedFieldChange('quality_metrics', 'grade', e.target.value)}
                    placeholder="e.g., A, B, Premium"
                  />

                  <Input
                    label="Color"
                    value={data.quality_metrics?.color || ''}
                    onChange={(e) => handleNestedFieldChange('quality_metrics', 'color', e.target.value)}
                    placeholder="Color description"
                  />

                  <Input
                    label="Defect Rate (%)"
                    type="number"
                    value={data.quality_metrics?.defect_rate?.toString() || ''}
                    onChange={(e) => handleNestedFieldChange('quality_metrics', 'defect_rate', parseFloat(e.target.value) || 0)}
                    placeholder="0-100"
                    step="0.1"
                    min="0"
                    max="100"
                  />
                </div>

                <Textarea
                  label="Quality Notes"
                  value={data.quality_metrics?.quality_notes || ''}
                  onChange={(e) => handleNestedFieldChange('quality_metrics', 'quality_notes', e.target.value)}
                  placeholder="Additional quality observations, test results, certifications, etc."
                  rows={3}
                />
              </CardBody>
            </Card>
          </div>
        );

      case 'attachments':
        return (
          <div className="space-y-6">
            <Card>
              <CardHeader title="Supporting Documentation" />
              <CardBody>
                <div className="border-2 border-dashed border-neutral-300 rounded-lg p-8 text-center">
                  <div className="space-y-4">
                    <div className="mx-auto w-12 h-12 bg-neutral-100 rounded-lg flex items-center justify-center">
                      <svg className="w-6 h-6 text-neutral-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                      </svg>
                    </div>
                    <div>
                      <p className="text-neutral-600">Upload supporting documents</p>
                      <p className="text-sm text-neutral-500 mt-1">
                        Certificates, test results, harvest records, etc.
                      </p>
                    </div>
                    <button
                      type="button"
                      className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-primary-700 bg-primary-100 hover:bg-primary-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
                    >
                      Choose Files
                    </button>
                  </div>
                </div>
                
                <p className="text-xs text-neutral-500 mt-2">
                  Supported formats: PDF, JPG, PNG, DOC, XLS. Maximum file size: 10MB per file.
                </p>
              </CardBody>
            </Card>
          </div>
        );

      default:
        return (
          <div className="text-center py-8">
            <p className="text-neutral-500">Step content not found</p>
          </div>
        );
    }
  };

  return (
    <div className="space-y-6">
      {renderStepContent()}
    </div>
  );
};

export default OriginatorConfirmationForm;
