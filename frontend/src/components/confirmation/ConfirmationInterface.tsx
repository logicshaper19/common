/**
 * Main Confirmation Interface Component
 * Dynamically selects between processor and originator confirmation interfaces
 */
import React, { useState, useEffect } from 'react';
import { 
  CheckCircleIcon, 
  ExclamationTriangleIcon,
  ArrowLeftIcon,
  ArrowRightIcon
} from '@heroicons/react/24/outline';
import {
  PurchaseOrder,
  ProcessorConfirmationData,
  OriginatorConfirmationData,
  ConfirmationFormState
} from '../../types/confirmation';
import { PurchaseOrder as APIPurchaseOrder } from '../../lib/api';
import { 
  getConfirmationConfig,
  validateConfirmationData,
  isStepComplete,
  getFormProgress
} from '../../lib/confirmationConfig';
import { useAuth } from '../../contexts/AuthContext';
import { cn } from '../../lib/utils';
import Button from '../ui/Button';
import { Card, CardHeader, CardBody } from '../ui/Card';
import Badge from '../ui/Badge';
import ProcessorConfirmationForm from './ProcessorConfirmationForm';
import OriginatorConfirmationForm from './OriginatorConfirmationForm';

interface ConfirmationInterfaceProps {
  purchaseOrder: APIPurchaseOrder;
  onSubmit: (data: ProcessorConfirmationData | OriginatorConfirmationData) => Promise<void>;
  onCancel: () => void;
  className?: string;
}

const ConfirmationInterface: React.FC<ConfirmationInterfaceProps> = ({
  purchaseOrder,
  onSubmit,
  onCancel,
  className
}) => {
  const { user } = useAuth();
  const [currentStep, setCurrentStep] = useState(0);
  const [formData, setFormData] = useState<any>({});
  const [formState, setFormState] = useState<ConfirmationFormState>({
    step: 0,
    isValid: false,
    errors: {},
    isSubmitting: false,
    isDirty: false
  });

  // Determine company type and get configuration
  const companyType = user?.company?.company_type === 'processor' ? 'processor' : 'originator';
  const productCategory = purchaseOrder.product?.category || 'raw_material';
  const config = getConfirmationConfig(companyType, productCategory);

  // Initialize form data based on company type
  useEffect(() => {
    const initialData = {
      purchase_order_id: purchaseOrder.id,
      confirmed_quantity: purchaseOrder.quantity,
      unit: purchaseOrder.unit,
      confirmation_date: new Date().toISOString().split('T')[0],
      notes: '',
      quality_metrics: {},
      attachments: []
    };

    if (companyType === 'processor') {
      setFormData({
        ...initialData,
        input_materials: [],
        processing_info: {},
        composition_validated: false,
        total_input_percentage: 0
      });
    } else {
      setFormData({
        ...initialData,
        origin_data: {
          cultivation_method: 'conventional',
          certifications: []
        },
        harvest_location: {
          coordinates: { latitude: 0, longitude: 0 },
          country: ''
        }
      });
    }
  }, [purchaseOrder, companyType]);

  // Validate current step
  useEffect(() => {
    if (config.steps[currentStep]) {
      const stepValidation = isStepComplete(config.steps[currentStep], formData);

      setFormState(prev => {
        const newErrors = stepValidation.errors.reduce((acc, error, index) => {
          acc[`step_${currentStep}_${index}`] = error;
          return acc;
        }, {} as Record<string, string>);

        // Only update if there's actually a change
        if (
          prev.step !== currentStep ||
          prev.isValid !== stepValidation.isComplete ||
          JSON.stringify(prev.errors) !== JSON.stringify(newErrors)
        ) {
          return {
            ...prev,
            step: currentStep,
            isValid: stepValidation.isComplete,
            errors: newErrors
          };
        }
        return prev;
      });
    }
  }, [currentStep, config.steps, formData]);

  // Handle form data changes
  const handleDataChange = (newData: Partial<any>) => {
    setFormData((prev: any) => {
      const updated = { ...prev, ...newData };
      // Only update if data actually changed
      if (JSON.stringify(prev) !== JSON.stringify(updated)) {
        return updated;
      }
      return prev;
    });
    setFormState(prev => ({ ...prev, isDirty: true }));
  };

  // Navigate to next step
  const handleNextStep = () => {
    if (currentStep < config.steps.length - 1) {
      setCurrentStep(currentStep + 1);
    }
  };

  // Navigate to previous step
  const handlePreviousStep = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  // Handle form submission
  const handleSubmit = async () => {
    const validation = validateConfirmationData(formData, config);
    
    if (!validation.isValid) {
      setFormState(prev => ({
        ...prev,
        errors: validation.errors
      }));
      return;
    }

    setFormState(prev => ({ ...prev, isSubmitting: true }));

    try {
      await onSubmit(formData);
    } catch (error) {
      console.error('Confirmation submission error:', error);
      setFormState(prev => ({
        ...prev,
        isSubmitting: false,
        errors: { submit: 'Failed to submit confirmation. Please try again.' }
      }));
    }
  };

  // Get current step info
  const currentStepInfo = config.steps[currentStep];
  const progress = getFormProgress(config.steps, currentStep + 1, formData);
  const isLastStep = currentStep === config.steps.length - 1;
  const canProceed = formState.isValid || currentStepInfo?.isOptional;

  return (
    <div className={cn('max-w-4xl mx-auto', className)}>
      {/* Header */}
      <Card className="mb-6">
        <CardHeader
          title={`Confirm ${companyType === 'processor' ? 'Processing' : 'Origin'} Order`}
          subtitle={`Purchase Order: ${purchaseOrder.id}`}
          action={
            <Badge variant="primary">
              {companyType === 'processor' ? 'Processor' : 'Originator'} Interface
            </Badge>
          }
        />
        <CardBody>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <p className="text-sm text-neutral-500">Product</p>
              <p className="font-medium">{purchaseOrder.product?.name}</p>
            </div>
            <div>
              <p className="text-sm text-neutral-500">Quantity</p>
              <p className="font-medium">{purchaseOrder.quantity} {purchaseOrder.unit}</p>
            </div>
            <div>
              <p className="text-sm text-neutral-500">Buyer</p>
              <p className="font-medium">{purchaseOrder.buyer_company?.name}</p>
            </div>
          </div>
        </CardBody>
      </Card>

      {/* Progress indicator */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-medium text-neutral-700">
            Step {currentStep + 1} of {config.steps.length}: {currentStepInfo?.title}
          </span>
          <span className="text-sm text-neutral-500">{progress}% complete</span>
        </div>
        
        <div className="w-full bg-neutral-200 rounded-full h-2">
          <div 
            className="bg-primary-600 h-2 rounded-full transition-all duration-300"
            style={{ width: `${progress}%` }}
          />
        </div>

        {/* Step indicators */}
        <div className="flex justify-between mt-4">
          {config.steps.map((step, index) => {
            const stepComplete = isStepComplete(step, formData).isComplete;
            const isCurrent = index === currentStep;
            const isPast = index < currentStep;
            
            return (
              <div key={step.id} className="flex flex-col items-center">
                <div className={cn(
                  "w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium",
                  isCurrent ? "bg-primary-600 text-white" :
                  isPast || stepComplete ? "bg-success-600 text-white" :
                  "bg-neutral-200 text-neutral-500"
                )}>
                  {isPast || stepComplete ? (
                    <CheckCircleIcon className="h-5 w-5" />
                  ) : (
                    index + 1
                  )}
                </div>
                <span className={cn(
                  "text-xs mt-1 text-center max-w-20",
                  isCurrent ? "text-primary-600 font-medium" : "text-neutral-500"
                )}>
                  {step.title}
                </span>
              </div>
            );
          })}
        </div>
      </div>

      {/* Current step description */}
      {currentStepInfo && (
        <div className="mb-6 p-4 bg-primary-50 rounded-lg">
          <h3 className="font-medium text-primary-900 mb-1">
            {currentStepInfo.title}
          </h3>
          <p className="text-sm text-primary-700">
            {currentStepInfo.description}
          </p>
          {currentStepInfo.isOptional && (
            <Badge variant="secondary" size="sm" className="mt-2">
              Optional
            </Badge>
          )}
        </div>
      )}

      {/* Form content */}
      <Card className="mb-6">
        <CardBody>
          {companyType === 'processor' ? (
            <ProcessorConfirmationForm
              data={formData}
              onChange={handleDataChange}
              currentStep={currentStep}
              config={config}
              purchaseOrder={purchaseOrder}
            />
          ) : (
            <OriginatorConfirmationForm
              data={formData}
              onChange={handleDataChange}
              currentStep={currentStep}
              config={config}
              purchaseOrder={purchaseOrder}
              onConfirmationEligibilityChange={(canConfirm) => {
                // Update form state to reflect confirmation eligibility
                setFormState(prev => ({
                  ...prev,
                  canSubmit: canConfirm
                }));
              }}
            />
          )}
        </CardBody>
      </Card>

      {/* Validation errors */}
      {Object.keys(formState.errors).length > 0 && (
        <div className="mb-6 p-4 bg-error-50 rounded-lg">
          <div className="flex items-center space-x-2 mb-2">
            <ExclamationTriangleIcon className="h-5 w-5 text-error-600" />
            <h4 className="font-medium text-error-900">Please fix the following issues:</h4>
          </div>
          <ul className="text-sm text-error-700 space-y-1">
            {Object.values(formState.errors).map((error, index) => (
              <li key={index}>• {error}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Navigation */}
      <div className="flex items-center justify-between">
        <Button
          variant="secondary"
          onClick={currentStep === 0 ? onCancel : handlePreviousStep}
          leftIcon={<ArrowLeftIcon className="h-4 w-4" />}
          disabled={formState.isSubmitting}
        >
          {currentStep === 0 ? 'Cancel' : 'Previous'}
        </Button>

        <div className="flex space-x-3">
          {!isLastStep ? (
            <Button
              variant="primary"
              onClick={handleNextStep}
              disabled={!canProceed || formState.isSubmitting}
              rightIcon={<ArrowRightIcon className="h-4 w-4" />}
            >
              Next Step
            </Button>
          ) : (
            <Button
              variant="success"
              onClick={handleSubmit}
              disabled={!canProceed || formState.isSubmitting}
              isLoading={formState.isSubmitting}
              rightIcon={<CheckCircleIcon className="h-4 w-4" />}
            >
              {formState.isSubmitting ? 'Submitting...' : 'Submit Confirmation'}
            </Button>
          )}
        </div>
      </div>
    </div>
  );
};

export default ConfirmationInterface;
