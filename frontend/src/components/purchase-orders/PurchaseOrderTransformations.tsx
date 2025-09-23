import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardBody } from '../ui/Card';
import { Button } from '../ui/Button';
import { Badge } from '../ui/Badge';
import { useToast } from '../../contexts/ToastContext';
import { 
  CogIcon, 
  PlusIcon, 
  ClockIcon, 
  CheckCircleIcon,
  ExclamationTriangleIcon,
  ChartBarIcon,
  BeakerIcon,
  ArrowRightIcon
} from '@heroicons/react/24/outline';

interface PurchaseOrderTransformationsProps {
  purchaseOrderId: string;
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
    batch_id?: string;
  };
  onOpenTransformationWizard: () => void;
}

interface TransformationEvent {
  id: string;
  event_id: string;
  transformation_type: string;
  status: 'planned' | 'in_progress' | 'completed' | 'failed';
  input_batches: Array<{
    batch_id: string;
    quantity: number;
    unit: string;
  }>;
  output_batches: Array<{
    batch_id: string;
    quantity: number;
    unit: string;
    product_name: string;
  }>;
  yield_percentage: number;
  start_time: string;
  end_time?: string;
  process_description: string;
  quality_metrics: any;
  efficiency_metrics: any;
}

interface InputBatch {
  id: string;
  batch_id: string;
  quantity: number;
  unit: string;
  status: string;
  product_name: string;
}

export const PurchaseOrderTransformations: React.FC<PurchaseOrderTransformationsProps> = ({
  purchaseOrderId,
  purchaseOrder,
  onOpenTransformationWizard
}) => {
  const { showToast } = useToast();
  const [loading, setLoading] = useState(true);
  const [transformations, setTransformations] = useState<TransformationEvent[]>([]);
  const [inputBatches, setInputBatches] = useState<InputBatch[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadTransformationData();
  }, [purchaseOrderId]);

  const loadTransformationData = async () => {
    setLoading(true);
    setError(null);
    
    try {
      // Load input batches for this PO
      const batchesResponse = await fetch(`/api/v1/batches?purchase_order_id=${purchaseOrderId}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
        }
      });
      
      if (batchesResponse.ok) {
        const batchesData = await batchesResponse.json();
        setInputBatches(batchesData.batches || []);
      }

      // Load transformation events linked to this PO
      const transformationsResponse = await fetch(`/api/v1/transformation-events?purchase_order_id=${purchaseOrderId}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
        }
      });
      
      if (transformationsResponse.ok) {
        const transformationsData = await transformationsResponse.json();
        setTransformations(transformationsData.transformation_events || []);
      }
    } catch (err) {
      setError('Failed to load transformation data');
      console.error('Error loading transformation data:', err);
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'success';
      case 'in_progress': return 'warning';
      case 'planned': return 'secondary';
      case 'failed': return 'error';
      default: return 'secondary';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed': return <CheckCircleIcon className="h-4 w-4" />;
      case 'in_progress': return <ClockIcon className="h-4 w-4" />;
      case 'planned': return <ClockIcon className="h-4 w-4" />;
      case 'failed': return <ExclamationTriangleIcon className="h-4 w-4" />;
      default: return <ClockIcon className="h-4 w-4" />;
    }
  };

  const calculateYieldEstimation = () => {
    if (purchaseOrder.product.name.toLowerCase().includes('fresh fruit bunches') || 
        purchaseOrder.product.name.toLowerCase().includes('ffb')) {
      return {
        cpo: Math.round(purchaseOrder.quantity * 0.20),
        kernel: Math.round(purchaseOrder.quantity * 0.15),
        total_yield: 35
      };
    }
    return {
      processed: Math.round(purchaseOrder.quantity * 0.85),
      total_yield: 85
    };
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-1/4 mb-4"></div>
          <div className="space-y-3">
            <div className="h-20 bg-gray-200 rounded"></div>
            <div className="h-20 bg-gray-200 rounded"></div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <Card>
        <CardBody>
          <div className="text-center py-8">
            <ExclamationTriangleIcon className="h-12 w-12 text-red-500 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">Error Loading Data</h3>
            <p className="text-gray-600 mb-4">{error}</p>
            <Button onClick={loadTransformationData} variant="outline">
              Try Again
            </Button>
          </div>
        </CardBody>
      </Card>
    );
  }

  const yieldEstimation = calculateYieldEstimation();
  const hasInputBatches = inputBatches.length > 0;
  const hasTransformations = transformations.length > 0;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-medium text-gray-900">Transformation Management</h3>
          <p className="text-sm text-gray-600">
            Manage processing of {purchaseOrder.quantity.toLocaleString()} {purchaseOrder.unit} {purchaseOrder.product.name}
          </p>
        </div>
        {hasInputBatches && !hasTransformations && (
          <Button onClick={onOpenTransformationWizard} className="flex items-center">
            <PlusIcon className="h-4 w-4 mr-2" />
            Create Transformation
          </Button>
        )}
      </div>

      {/* Input Batches Status */}
      {hasInputBatches && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center text-sm">
              <div className="w-2 h-2 bg-orange-500 rounded-full mr-2"></div>
              Available Input Materials
            </CardTitle>
          </CardHeader>
          <CardBody>
            <div className="space-y-3">
              {inputBatches.map((batch) => (
                <div key={batch.id} className="flex items-center justify-between p-3 bg-orange-50 rounded-lg">
                  <div className="flex items-center">
                    <div className="w-3 h-3 bg-orange-500 rounded-full mr-3"></div>
                    <div>
                      <div className="font-medium">{batch.batch_id}</div>
                      <div className="text-sm text-gray-600">{batch.product_name}</div>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="font-semibold">
                      {batch.quantity.toLocaleString()} {batch.unit}
                    </div>
                    <Badge variant="secondary" size="sm">
                      {batch.status}
                    </Badge>
                  </div>
                </div>
              ))}
            </div>
          </CardBody>
        </Card>
      )}

      {/* Yield Estimation */}
      {hasInputBatches && !hasTransformations && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center text-sm">
              <ChartBarIcon className="h-4 w-4 mr-2" />
              Expected Processing Yields
            </CardTitle>
          </CardHeader>
          <CardBody>
            <div className="space-y-4">
              {/* Input */}
              <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center">
                  <div className="w-3 h-3 bg-orange-500 rounded-full mr-3"></div>
                  <span className="font-medium">Input Material</span>
                </div>
                <div className="text-right">
                  <div className="font-semibold">
                    {purchaseOrder.quantity.toLocaleString()} {purchaseOrder.unit}
                  </div>
                  <div className="text-sm text-gray-500">{purchaseOrder.product.name}</div>
                </div>
              </div>

              {/* Arrow */}
              <div className="flex justify-center">
                <ArrowRightIcon className="h-5 w-5 text-gray-400" />
              </div>

              {/* Outputs */}
              {purchaseOrder.product.name.toLowerCase().includes('fresh fruit bunches') ? (
                <div className="space-y-2">
                  <div className="flex items-center justify-between p-3 bg-green-50 rounded-lg">
                    <div className="flex items-center">
                      <div className="w-3 h-3 bg-green-500 rounded-full mr-3"></div>
                      <span className="font-medium">Crude Palm Oil (CPO)</span>
                    </div>
                    <div className="text-right">
                      <div className="font-semibold">
                        {yieldEstimation.cpo?.toLocaleString() || '0'} KGM
                      </div>
                      <Badge variant="success" size="sm">20% yield</Badge>
                    </div>
                  </div>
                  <div className="flex items-center justify-between p-3 bg-green-50 rounded-lg">
                    <div className="flex items-center">
                      <div className="w-3 h-3 bg-green-500 rounded-full mr-3"></div>
                      <span className="font-medium">Palm Kernel</span>
                    </div>
                    <div className="text-right">
                      <div className="font-semibold">
                        {yieldEstimation.kernel?.toLocaleString() || '0'} KGM
                      </div>
                      <Badge variant="success" size="sm">15% yield</Badge>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="flex items-center justify-between p-3 bg-green-50 rounded-lg">
                  <div className="flex items-center">
                    <div className="w-3 h-3 bg-green-500 rounded-full mr-3"></div>
                    <span className="font-medium">Processed Product</span>
                  </div>
                  <div className="text-right">
                    <div className="font-semibold">
                      {yieldEstimation.processed?.toLocaleString() || '0'} {purchaseOrder.unit}
                    </div>
                    <Badge variant="success" size="sm">{yieldEstimation.total_yield}% yield</Badge>
                  </div>
                </div>
              )}
            </div>
          </CardBody>
        </Card>
      )}

      {/* Transformation Events */}
      {hasTransformations ? (
        <div className="space-y-4">
          <h4 className="font-medium text-gray-900">Transformation Events</h4>
          {transformations.map((transformation) => (
            <Card key={transformation.id}>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="flex items-center text-sm">
                    <CogIcon className="h-4 w-4 mr-2" />
                    {transformation.event_id}
                  </CardTitle>
                  <Badge variant={getStatusColor(transformation.status)} size="sm">
                    {getStatusIcon(transformation.status)}
                    <span className="ml-1 capitalize">{transformation.status.replace('_', ' ')}</span>
                  </Badge>
                </div>
              </CardHeader>
              <CardBody>
                <div className="space-y-4">
                  {/* Process Description */}
                  <div>
                    <h5 className="font-medium text-gray-900 mb-2">Process</h5>
                    <p className="text-sm text-gray-600">{transformation.process_description}</p>
                  </div>

                  {/* Input/Output Batches */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {/* Input */}
                    <div>
                      <h5 className="font-medium text-gray-900 mb-2">Input Batches</h5>
                      <div className="space-y-2">
                        {transformation.input_batches.map((batch, index) => (
                          <div key={index} className="flex items-center justify-between p-2 bg-orange-50 rounded">
                            <span className="text-sm font-medium">{batch.batch_id}</span>
                            <span className="text-sm text-gray-600">
                              {batch.quantity.toLocaleString()} {batch.unit}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Output */}
                    <div>
                      <h5 className="font-medium text-gray-900 mb-2">Output Batches</h5>
                      <div className="space-y-2">
                        {transformation.output_batches.map((batch, index) => (
                          <div key={index} className="flex items-center justify-between p-2 bg-green-50 rounded">
                            <span className="text-sm font-medium">{batch.product_name}</span>
                            <span className="text-sm text-gray-600">
                              {batch.quantity.toLocaleString()} {batch.unit}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>

                  {/* Metrics */}
                  <div className="grid grid-cols-3 gap-4 pt-4 border-t">
                    <div className="text-center">
                      <div className="text-lg font-semibold text-blue-600">
                        {transformation.yield_percentage}%
                      </div>
                      <div className="text-xs text-gray-500">Yield Efficiency</div>
                    </div>
                    <div className="text-center">
                      <div className="text-lg font-semibold text-green-600">
                        {new Date(transformation.start_time).toLocaleDateString()}
                      </div>
                      <div className="text-xs text-gray-500">Start Date</div>
                    </div>
                    <div className="text-center">
                      <div className="text-lg font-semibold text-purple-600">
                        {transformation.end_time ? 
                          new Date(transformation.end_time).toLocaleDateString() : 
                          'In Progress'
                        }
                      </div>
                      <div className="text-xs text-gray-500">End Date</div>
                    </div>
                  </div>
                </div>
              </CardBody>
            </Card>
          ))}
        </div>
      ) : hasInputBatches ? (
        <Card>
          <CardBody>
            <div className="text-center py-8">
              <CogIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">No Transformations Yet</h3>
              <p className="text-gray-600 mb-4">
                Create a transformation to process your input materials into finished products.
              </p>
              <Button onClick={onOpenTransformationWizard} className="flex items-center mx-auto">
                <PlusIcon className="h-4 w-4 mr-2" />
                Create First Transformation
              </Button>
            </div>
          </CardBody>
        </Card>
      ) : (
        <Card>
          <CardBody>
            <div className="text-center py-8">
              <ExclamationTriangleIcon className="h-12 w-12 text-yellow-500 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">No Input Materials</h3>
              <p className="text-gray-600">
                No batches have been created for this purchase order yet. 
                Confirm the purchase order to create input materials for processing.
              </p>
            </div>
          </CardBody>
        </Card>
      )}
    </div>
  );
};
