import React, { useState, useEffect } from 'react';
import Modal from '../ui/Modal';
import { Button } from '../ui/Button';
import { Card, CardHeader, CardTitle, CardBody } from '../ui/Card';
import { Badge } from '../ui/Badge';
import Input from '../ui/Input';
import Label from '../ui/Label';
import Textarea from '../ui/Textarea';
import Select from '../ui/Select';
import { useToast } from '../../contexts/ToastContext';
import { 
  CogIcon, 
  CheckCircleIcon,
  ArrowRightIcon,
  PlusIcon,
  XMarkIcon
} from '@heroicons/react/24/outline';

interface TransformationWizardProps {
  isOpen: boolean;
  onClose: () => void;
  purchaseOrder: {
    id: string;
    po_number: string;
    quantity: number;
    unit: string;
    product: {
      name: string;
      category: string;
    };
    buyer_company: {
      name: string;
      company_type: string;
    };
  };
  inputBatch: {
    id: string;
    batch_id: string;
    quantity: number;
    unit: string;
  };
  onTransformationCreated: (transformationId: string) => void;
}

interface OutputProduct {
  id: string;
  name: string;
  quantity: number;
  unit: string;
  yield_percentage: number;
}

export const TransformationWizard: React.FC<TransformationWizardProps> = ({
  isOpen,
  onClose,
  purchaseOrder,
  inputBatch,
  onTransformationCreated
}) => {
  const { showToast } = useToast();
  const [currentStep, setCurrentStep] = useState(1);
  const [loading, setLoading] = useState(false);
  
  // Form data
  const [transformationData, setTransformationData] = useState({
    transformation_type: 'MILLING',
    facility_id: '',
    process_description: '',
    start_time: new Date().toISOString().slice(0, 16), // YYYY-MM-DDTHH:MM
    estimated_duration_hours: 2,
    location_name: '',
    notes: ''
  });

  const [outputProducts, setOutputProducts] = useState<OutputProduct[]>([]);

  useEffect(() => {
    if (isOpen) {
      initializeOutputProducts();
    }
  }, [isOpen, purchaseOrder]);

  const initializeOutputProducts = () => {
    if (purchaseOrder.product.name.toLowerCase().includes('fresh fruit bunches') || 
        purchaseOrder.product.name.toLowerCase().includes('ffb')) {
      setOutputProducts([
        {
          id: '1',
          name: 'Crude Palm Oil (CPO)',
          quantity: Math.round(inputBatch.quantity * 0.20),
          unit: 'KGM',
          yield_percentage: 20
        },
        {
          id: '2',
          name: 'Palm Kernel',
          quantity: Math.round(inputBatch.quantity * 0.15),
          unit: 'KGM',
          yield_percentage: 15
        }
      ]);
    } else {
      setOutputProducts([
        {
          id: '1',
          name: 'Processed Product',
          quantity: Math.round(inputBatch.quantity * 0.85),
          unit: purchaseOrder.unit,
          yield_percentage: 85
        }
      ]);
    }
  };

  const handleInputChange = (field: string, value: any) => {
    setTransformationData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleOutputProductChange = (id: string, field: string, value: any) => {
    setOutputProducts(prev => prev.map(product => 
      product.id === id ? { ...product, [field]: value } : product
    ));
  };

  const addOutputProduct = () => {
    const newId = (outputProducts.length + 1).toString();
    setOutputProducts(prev => [...prev, {
      id: newId,
      name: '',
      quantity: 0,
      unit: 'KGM',
      yield_percentage: 0
    }]);
  };

  const removeOutputProduct = (id: string) => {
    setOutputProducts(prev => prev.filter(product => product.id !== id));
  };

  const validateStep = (step: number): boolean => {
    switch (step) {
      case 1:
        return !!(transformationData.transformation_type && 
               transformationData.facility_id && 
               transformationData.process_description);
      case 2:
        return outputProducts.length > 0 && 
               outputProducts.every(p => p.name && p.quantity > 0);
      default:
        return true;
    }
  };

  const handleNext = () => {
    if (validateStep(currentStep)) {
      setCurrentStep(prev => prev + 1);
    } else {
      showToast({
        type: 'error',
        title: 'Validation Error',
        message: 'Please fill in all required fields before proceeding.'
      });
    }
  };

  const handlePrevious = () => {
    setCurrentStep(prev => prev - 1);
  };

  const handleSubmit = async () => {
    if (!validateStep(2)) {
      showToast({
        type: 'error',
        title: 'Validation Error',
        message: 'Please complete all required fields.'
      });
      return;
    }

    setLoading(true);
    try {
      const transformationPayload = {
        transformation_type: transformationData.transformation_type,
        company_id: purchaseOrder.buyer_company.company_type, // This should be the actual company ID
        facility_id: transformationData.facility_id,
        input_batches: [{
          batch_id: inputBatch.id,
          quantity: inputBatch.quantity,
          unit: inputBatch.unit
        }],
        output_batches: outputProducts.map(product => ({
          product_name: product.name,
          quantity: product.quantity,
          unit: product.unit,
          yield_percentage: product.yield_percentage
        })),
        process_description: transformationData.process_description,
        start_time: transformationData.start_time,
        estimated_duration_hours: transformationData.estimated_duration_hours,
        location_name: transformationData.location_name,
        notes: transformationData.notes,
        purchase_order_id: purchaseOrder.id
      };

      const response = await fetch('/api/v1/transformation-enhanced/transformation/create-complete', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
        },
        body: JSON.stringify(transformationPayload)
      });

      if (response.ok) {
        const result = await response.json();
        onTransformationCreated(result.transformation_event_id);
        onClose();
        showToast({
          type: 'success',
          title: 'Transformation Created',
          message: 'Transformation event has been created successfully.'
        });
      } else {
        throw new Error('Failed to create transformation');
      }
    } catch (error) {
      showToast({
        type: 'error',
        title: 'Error',
        message: 'Failed to create transformation. Please try again.'
      });
    } finally {
      setLoading(false);
    }
  };

  const renderStep1 = () => (
    <div className="space-y-6">
      <div className="text-center">
        <h3 className="text-lg font-medium text-gray-900 mb-2">Transformation Setup</h3>
        <p className="text-sm text-gray-600">
          Configure the processing parameters for your transformation
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <Label htmlFor="transformation_type">Transformation Type *</Label>
          <Select
            id="transformation_type"
            value={transformationData.transformation_type}
            onChange={(e) => handleInputChange('transformation_type', e.target.value)}
            options={[
              { value: "MILLING", label: "Milling" },
              { value: "CRUSHING", label: "Crushing" },
              { value: "REFINING", label: "Refining" },
              { value: "FRACTIONATION", label: "Fractionation" },
              { value: "BLENDING", label: "Blending" },
              { value: "MANUFACTURING", label: "Manufacturing" }
            ]}
          />
        </div>

        <div>
          <Label htmlFor="facility_id">Facility ID *</Label>
          <Input
            id="facility_id"
            value={transformationData.facility_id}
            onChange={(e) => handleInputChange('facility_id', e.target.value)}
            placeholder="e.g., MILL-001, REFINERY-A"
          />
        </div>
      </div>

      <div>
        <Label htmlFor="process_description">Process Description *</Label>
        <Textarea
          id="process_description"
          value={transformationData.process_description}
          onChange={(e) => handleInputChange('process_description', e.target.value)}
          placeholder="Describe the transformation process..."
          rows={3}
        />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <Label htmlFor="start_time">Start Time</Label>
          <Input
            id="start_time"
            type="datetime-local"
            value={transformationData.start_time}
            onChange={(e) => handleInputChange('start_time', e.target.value)}
          />
        </div>

        <div>
          <Label htmlFor="estimated_duration_hours">Estimated Duration (hours)</Label>
          <Input
            id="estimated_duration_hours"
            type="number"
            value={transformationData.estimated_duration_hours}
            onChange={(e) => handleInputChange('estimated_duration_hours', parseInt(e.target.value))}
            min="1"
          />
        </div>
      </div>

      <div>
        <Label htmlFor="location_name">Location</Label>
        <Input
          id="location_name"
          value={transformationData.location_name}
          onChange={(e) => handleInputChange('location_name', e.target.value)}
          placeholder="Processing facility location"
        />
      </div>

      <div>
        <Label htmlFor="notes">Notes</Label>
        <Textarea
          id="notes"
          value={transformationData.notes}
          onChange={(e) => handleInputChange('notes', e.target.value)}
          placeholder="Additional notes or special instructions..."
          rows={2}
        />
      </div>
    </div>
  );

  const renderStep2 = () => (
    <div className="space-y-6">
      <div className="text-center">
        <h3 className="text-lg font-medium text-gray-900 mb-2">Output Products</h3>
        <p className="text-sm text-gray-600">
          Define the expected output products from this transformation
        </p>
      </div>

      {/* Input Summary */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm">Input Material</CardTitle>
        </CardHeader>
        <CardBody>
          <div className="flex items-center justify-between p-3 bg-orange-50 rounded-lg">
            <div className="flex items-center">
              <div className="w-3 h-3 bg-orange-500 rounded-full mr-3"></div>
              <span className="font-medium">{inputBatch.batch_id}</span>
            </div>
            <div className="text-right">
              <div className="font-semibold">
                {inputBatch.quantity.toLocaleString()} {inputBatch.unit}
              </div>
              <div className="text-sm text-gray-500">{purchaseOrder.product.name}</div>
            </div>
          </div>
        </CardBody>
      </Card>

      {/* Output Products */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h4 className="font-medium text-gray-900">Output Products</h4>
          <Button onClick={addOutputProduct} variant="outline" size="sm">
            <PlusIcon className="h-4 w-4 mr-1" />
            Add Product
          </Button>
        </div>

        {outputProducts.map((product, index) => (
          <Card key={product.id}>
            <CardBody>
              <div className="flex items-center justify-between mb-4">
                <h5 className="font-medium text-gray-900">Product {index + 1}</h5>
                {outputProducts.length > 1 && (
                  <Button
                    onClick={() => removeOutputProduct(product.id)}
                    variant="outline"
                    size="sm"
                  >
                    <XMarkIcon className="h-4 w-4" />
                  </Button>
                )}
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <Label htmlFor={`product_name_${product.id}`}>Product Name *</Label>
                  <Input
                    id={`product_name_${product.id}`}
                    value={product.name}
                    onChange={(e) => handleOutputProductChange(product.id, 'name', e.target.value)}
                    placeholder="e.g., Crude Palm Oil"
                  />
                </div>

                <div>
                  <Label htmlFor={`quantity_${product.id}`}>Quantity *</Label>
                  <Input
                    id={`quantity_${product.id}`}
                    type="number"
                    value={product.quantity}
                    onChange={(e) => handleOutputProductChange(product.id, 'quantity', parseFloat(e.target.value))}
                    min="0"
                    step="0.01"
                  />
                </div>

                <div>
                  <Label htmlFor={`unit_${product.id}`}>Unit</Label>
                  <Input
                    id={`unit_${product.id}`}
                    value={product.unit}
                    onChange={(e) => handleOutputProductChange(product.id, 'unit', e.target.value)}
                    placeholder="KGM"
                  />
                </div>
              </div>

              <div className="mt-4">
                <Label htmlFor={`yield_${product.id}`}>Yield Percentage</Label>
                <Input
                  id={`yield_${product.id}`}
                  type="number"
                  value={product.yield_percentage}
                  onChange={(e) => handleOutputProductChange(product.id, 'yield_percentage', parseFloat(e.target.value))}
                  min="0"
                  max="100"
                  step="0.1"
                />
              </div>
            </CardBody>
          </Card>
        ))}
      </div>
    </div>
  );

  const renderStep3 = () => (
    <div className="space-y-6">
      <div className="text-center">
        <CheckCircleIcon className="h-12 w-12 text-green-500 mx-auto mb-4" />
        <h3 className="text-lg font-medium text-gray-900 mb-2">Review & Create</h3>
        <p className="text-sm text-gray-600">
          Review your transformation setup before creating the event
        </p>
      </div>

      {/* Summary */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm">Transformation Summary</CardTitle>
        </CardHeader>
        <CardBody className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <div className="text-sm font-medium text-gray-600">Type</div>
              <div className="font-semibold">{transformationData.transformation_type}</div>
            </div>
            <div>
              <div className="text-sm font-medium text-gray-600">Facility</div>
              <div className="font-semibold">{transformationData.facility_id}</div>
            </div>
            <div>
              <div className="text-sm font-medium text-gray-600">Start Time</div>
              <div className="font-semibold">
                {new Date(transformationData.start_time).toLocaleString()}
              </div>
            </div>
            <div>
              <div className="text-sm font-medium text-gray-600">Duration</div>
              <div className="font-semibold">{transformationData.estimated_duration_hours} hours</div>
            </div>
          </div>

          <div>
            <div className="text-sm font-medium text-gray-600 mb-2">Process Description</div>
            <p className="text-sm text-gray-800">{transformationData.process_description}</p>
          </div>

          <div>
            <div className="text-sm font-medium text-gray-600 mb-2">Expected Outputs</div>
            <div className="space-y-2">
              {outputProducts.map((product, index) => (
                <div key={index} className="flex items-center justify-between p-2 bg-green-50 rounded">
                  <span className="font-medium">{product.name}</span>
                  <div className="text-right">
                    <div className="font-semibold">
                      {product.quantity.toLocaleString()} {product.unit}
                    </div>
                    <Badge variant="success" size="sm">
                      {product.yield_percentage}% yield
                    </Badge>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </CardBody>
      </Card>
    </div>
  );

  if (!isOpen) return null;

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Create Transformation"
      size="xl"
    >
      <div className="space-y-6">
        {/* Progress Steps */}
        <div className="flex items-center justify-center space-x-4">
          {[1, 2, 3].map((step) => (
            <div key={step} className="flex items-center">
              <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
                step <= currentStep 
                  ? 'bg-blue-600 text-white' 
                  : 'bg-gray-200 text-gray-600'
              }`}>
                {step < currentStep ? <CheckCircleIcon className="h-5 w-5" /> : step}
              </div>
              {step < 3 && (
                <div className={`w-12 h-0.5 mx-2 ${
                  step < currentStep ? 'bg-blue-600' : 'bg-gray-200'
                }`} />
              )}
            </div>
          ))}
        </div>

        {/* Step Content */}
        <div className="min-h-[400px]">
          {currentStep === 1 && renderStep1()}
          {currentStep === 2 && renderStep2()}
          {currentStep === 3 && renderStep3()}
        </div>

        {/* Navigation Buttons */}
        <div className="flex justify-between pt-6 border-t">
          <div>
            {currentStep > 1 && (
              <Button onClick={handlePrevious} variant="outline">
                Previous
              </Button>
            )}
          </div>
          
          <div className="flex space-x-3">
            <Button onClick={onClose} variant="outline">
              Cancel
            </Button>
            
            {currentStep < 3 ? (
              <Button onClick={handleNext}>
                Next
              </Button>
            ) : (
              <Button onClick={handleSubmit} disabled={loading}>
                {loading ? 'Creating...' : 'Create Transformation'}
              </Button>
            )}
          </div>
        </div>
      </div>
    </Modal>
  );
};
