/**
 * Processor Confirmation Form Component
 * Handles processor-specific confirmation workflow with input material composition
 */
import React from 'react';
import { ConfirmationConfig, ProcessorConfirmationData } from '../../types/confirmation';
import { PurchaseOrder } from '../../lib/api';
import Input from '../ui/Input';
import Select from '../ui/Select';
import Textarea from '../ui/Textarea';
import CompositionInput from '../ui/CompositionInput';
import { Card, CardHeader, CardBody } from '../ui/Card';

interface ProcessorConfirmationFormProps {
  data: ProcessorConfirmationData;
  onChange: (data: Partial<ProcessorConfirmationData>) => void;
  currentStep: number;
  config: ConfirmationConfig;
  purchaseOrder: PurchaseOrder;
}

const ProcessorConfirmationForm: React.FC<ProcessorConfirmationFormProps> = ({
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
    const currentParentValue = data[parentField as keyof ProcessorConfirmationData] || {};
    onChange({
      [parentField]: {
        ...(typeof currentParentValue === 'object' ? currentParentValue : {}),
        [field]: value
      }
    });
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

      case 'input_materials':
        return (
          <div className="space-y-6">
            <CompositionInput
              label="Input Materials Composition"
              value={data.input_materials || []}
              onChange={(materials) => {
                const totalPercentage = materials.reduce(
                  (sum, material) => sum + (material.percentage_contribution || 0),
                  0
                );
                onChange({
                  input_materials: materials,
                  total_input_percentage: totalPercentage,
                  composition_validated: Math.abs(totalPercentage - 100) <= 0.01
                });
              }}
              targetQuantity={data.confirmed_quantity || 0}
              targetUnit={data.unit || 'KG'}
              required
            />

            {data.composition_validated && (
              <div className="p-4 bg-success-50 rounded-lg">
                <p className="text-success-800 font-medium">
                  ✓ Composition validated successfully
                </p>
                <p className="text-success-700 text-sm mt-1">
                  Total percentage: {data.total_input_percentage?.toFixed(2)}%
                </p>
              </div>
            )}
          </div>
        );

      case 'processing_info':
        return (
          <div className="space-y-6">
            <Card>
              <CardHeader title="Processing Information" />
              <CardBody>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <Input
                    label="Processing Method"
                    value={data.processing_info?.processing_method || ''}
                    onChange={(e) => handleNestedFieldChange('processing_info', 'processing_method', e.target.value)}
                    placeholder="e.g., Mechanical pressing, Chemical extraction"
                  />

                  <Input
                    label="Processing Date"
                    type="date"
                    value={data.processing_info?.processing_date || ''}
                    onChange={(e) => handleNestedFieldChange('processing_info', 'processing_date', e.target.value)}
                    max={new Date().toISOString().split('T')[0]}
                  />

                  <Input
                    label="Duration (hours)"
                    type="number"
                    value={data.processing_info?.duration_hours?.toString() || ''}
                    onChange={(e) => handleNestedFieldChange('processing_info', 'duration_hours', parseFloat(e.target.value) || 0)}
                    placeholder="Processing duration"
                    step="0.1"
                    min="0"
                  />

                  <Input
                    label="Yield Percentage"
                    type="number"
                    value={data.processing_info?.yield_percentage?.toString() || ''}
                    onChange={(e) => handleNestedFieldChange('processing_info', 'yield_percentage', parseFloat(e.target.value) || 0)}
                    placeholder="Output yield %"
                    step="0.1"
                    min="0"
                    max="100"
                  />
                </div>

                <Textarea
                  label="Processing Notes"
                  value={data.processing_info?.processing_notes || ''}
                  onChange={(e) => handleNestedFieldChange('processing_info', 'processing_notes', e.target.value)}
                  placeholder="Additional processing details, equipment used, conditions, etc."
                  rows={3}
                />
              </CardBody>
            </Card>
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
                        Certificates, test results, processing records, etc.
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

export default ProcessorConfirmationForm;
