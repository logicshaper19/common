import React, { useState, useEffect } from 'react';
import Modal from '../ui/Modal';
import { Button } from '../ui/Button';
import { Card, CardHeader, CardTitle, CardBody } from '../ui/Card';
import { Badge } from '../ui/Badge';
import { useToast } from '../../contexts/ToastContext';
import { 
  CogIcon, 
  ChartBarIcon, 
  ClockIcon, 
  CheckCircleIcon,
  ArrowRightIcon,
  BeakerIcon
} from '@heroicons/react/24/outline';

interface TransformationPromptProps {
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
  onCreateNow: () => void;
  onScheduleLater: () => void;
  onSkip: () => void;
}

interface YieldEstimation {
  input_quantity: number;
  input_unit: string;
  output_products: Array<{
    name: string;
    quantity: number;
    unit: string;
    yield_percentage: number;
  }>;
  processing_time_hours: number;
  energy_consumption_kwh: number;
  water_consumption_m3: number;
}

export const TransformationPrompt: React.FC<TransformationPromptProps> = ({
  isOpen,
  onClose,
  purchaseOrder,
  inputBatch,
  onCreateNow,
  onScheduleLater,
  onSkip
}) => {
  const { showToast } = useToast();
  const [loading, setLoading] = useState(false);
  const [yieldEstimation, setYieldEstimation] = useState<YieldEstimation | null>(null);

  useEffect(() => {
    if (isOpen) {
      calculateYieldEstimation();
    }
  }, [isOpen, purchaseOrder, inputBatch]);

  const calculateYieldEstimation = async () => {
    try {
      // Calculate yield based on material type and industry standards
      const estimation = calculateYieldForMaterial(
        purchaseOrder.product.name,
        purchaseOrder.product.category,
        inputBatch.quantity
      );
      setYieldEstimation(estimation);
    } catch (error) {
      console.error('Failed to calculate yield estimation:', error);
    }
  };

  const calculateYieldForMaterial = (
    productName: string,
    category: string,
    quantity: number
  ): YieldEstimation => {
    // Industry-standard yield calculations for palm oil processing
    if (productName.toLowerCase().includes('fresh fruit bunches') || 
        productName.toLowerCase().includes('ffb')) {
      return {
        input_quantity: quantity,
        input_unit: 'KGM',
        output_products: [
          {
            name: 'Crude Palm Oil (CPO)',
            quantity: Math.round(quantity * 0.20), // 20% oil yield
            unit: 'KGM',
            yield_percentage: 20
          },
          {
            name: 'Palm Kernel',
            quantity: Math.round(quantity * 0.15), // 15% kernel yield
            unit: 'KGM',
            yield_percentage: 15
          }
        ],
        processing_time_hours: Math.round(quantity / 1000 * 2), // 2 hours per 1000kg
        energy_consumption_kwh: Math.round(quantity * 0.15), // 0.15 kWh per kg
        water_consumption_m3: Math.round(quantity * 0.0008) // 0.8L per kg
      };
    }

    // Default estimation for other materials
    return {
      input_quantity: quantity,
      input_unit: 'KGM',
      output_products: [
        {
          name: 'Processed Product',
          quantity: Math.round(quantity * 0.85), // 85% yield assumption
          unit: 'KGM',
          yield_percentage: 85
        }
      ],
      processing_time_hours: Math.round(quantity / 1000 * 1),
      energy_consumption_kwh: Math.round(quantity * 0.10),
      water_consumption_m3: Math.round(quantity * 0.0005)
    };
  };

  const handleCreateNow = async () => {
    setLoading(true);
    try {
      await onCreateNow();
      onClose();
      showToast({
        type: 'success',
        title: 'Transformation Started',
        message: 'Transformation wizard opened. Complete the setup to begin processing.'
      });
    } catch (error) {
      showToast({
        type: 'error',
        title: 'Error',
        message: 'Failed to open transformation wizard. Please try again.'
      });
    } finally {
      setLoading(false);
    }
  };

  const handleScheduleLater = async () => {
    setLoading(true);
    try {
      await onScheduleLater();
      onClose();
      showToast({
        type: 'info',
        title: 'Transformation Scheduled',
        message: 'Transformation has been marked for later processing. You can access it from the Transformations tab.'
      });
    } catch (error) {
      showToast({
        type: 'error',
        title: 'Error',
        message: 'Failed to schedule transformation. Please try again.'
      });
    } finally {
      setLoading(false);
    }
  };

  const handleSkip = () => {
    onSkip();
    onClose();
    showToast({
      type: 'info',
      title: 'Transformation Skipped',
      message: 'You can create transformations later from the Transformations tab.'
    });
  };

  if (!isOpen) return null;

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Processing Opportunity Detected"
      size="lg"
    >
      <div className="space-y-6">
        {/* Header */}
        <div className="text-center">
          <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-blue-100 mb-4">
            <CogIcon className="h-6 w-6 text-blue-600" />
          </div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            Ready to Process Raw Materials
          </h3>
          <p className="text-sm text-gray-600">
            You've received {purchaseOrder.quantity.toLocaleString()} {purchaseOrder.unit} of {purchaseOrder.product.name}
          </p>
        </div>

        {/* Yield Estimation */}
        {yieldEstimation && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center text-sm">
                <ChartBarIcon className="h-4 w-4 mr-2" />
                Processing Yield Estimation
              </CardTitle>
            </CardHeader>
            <CardBody className="space-y-4">
              {/* Input */}
              <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center">
                  <div className="w-3 h-3 bg-orange-500 rounded-full mr-3"></div>
                  <span className="font-medium">Input Material</span>
                </div>
                <div className="text-right">
                  <div className="font-semibold">
                    {yieldEstimation.input_quantity.toLocaleString()} {yieldEstimation.input_unit}
                  </div>
                  <div className="text-sm text-gray-500">{purchaseOrder.product.name}</div>
                </div>
              </div>

              {/* Arrow */}
              <div className="flex justify-center">
                <ArrowRightIcon className="h-5 w-5 text-gray-400" />
              </div>

              {/* Outputs */}
              <div className="space-y-2">
                {yieldEstimation.output_products.map((product, index) => (
                  <div key={index} className="flex items-center justify-between p-3 bg-green-50 rounded-lg">
                    <div className="flex items-center">
                      <div className="w-3 h-3 bg-green-500 rounded-full mr-3"></div>
                      <span className="font-medium">{product.name}</span>
                    </div>
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

              {/* Processing Details */}
              <div className="grid grid-cols-3 gap-4 pt-4 border-t">
                <div className="text-center">
                  <ClockIcon className="h-5 w-5 text-blue-500 mx-auto mb-1" />
                  <div className="text-sm font-medium">{yieldEstimation.processing_time_hours}h</div>
                  <div className="text-xs text-gray-500">Processing Time</div>
                </div>
                <div className="text-center">
                  <BeakerIcon className="h-5 w-5 text-yellow-500 mx-auto mb-1" />
                  <div className="text-sm font-medium">{yieldEstimation.energy_consumption_kwh} kWh</div>
                  <div className="text-xs text-gray-500">Energy Required</div>
                </div>
                <div className="text-center">
                  <div className="h-5 w-5 text-cyan-500 mx-auto mb-1">💧</div>
                  <div className="text-sm font-medium">{yieldEstimation.water_consumption_m3} m³</div>
                  <div className="text-xs text-gray-500">Water Required</div>
                </div>
              </div>
            </CardBody>
          </Card>
        )}

        {/* Action Buttons */}
        <div className="space-y-3">
          <Button
            onClick={handleCreateNow}
            disabled={loading}
            className="w-full"
            size="lg"
          >
            <CogIcon className="h-5 w-5 mr-2" />
            Create Transformation Now
          </Button>
          
          <div className="grid grid-cols-2 gap-3">
            <Button
              onClick={handleScheduleLater}
              disabled={loading}
              variant="secondary"
              className="w-full"
            >
              <ClockIcon className="h-4 w-4 mr-2" />
              Schedule Later
            </Button>
            
            <Button
              onClick={handleSkip}
              disabled={loading}
              variant="outline"
              className="w-full"
            >
              Skip for Now
            </Button>
          </div>
        </div>

        {/* Help Text */}
        <div className="text-center text-sm text-gray-500">
          <p>
            You can always access transformation management from the <strong>Transformations</strong> tab 
            in this purchase order.
          </p>
        </div>
      </div>
    </Modal>
  );
};
