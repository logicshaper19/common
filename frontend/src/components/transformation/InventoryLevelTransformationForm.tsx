import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardBody } from '../ui/Card';
import { Button } from '../ui/Button';
import Input from '../ui/Input';
import Label from '../ui/Label';
import Textarea from '../ui/Textarea';
import Select from '../ui/Select';
import { useAuth } from '../../contexts/AuthContext';
import { useToast } from '../../contexts/ToastContext';
import { Badge } from '../ui/Badge';
import { Loader2, Package, TrendingUp, AlertCircle, CheckCircle } from 'lucide-react';

interface InventoryLevelTransformationFormProps {
  onSave: (formData: any) => Promise<void>;
  onCancel: () => void;
  className?: string;
}

interface InventoryAvailability {
  total_quantity: number;
  unit: string;
  batch_count: number;
  batches: Array<{
    id: string;
    batch_number: string;
    quantity: number;
    unit: string;
    production_date: string;
    quality_metrics: any;
    origin_data: any;
    certifications: string[];
  }>;
  pool_composition: Array<{
    batch_id: string;
    quantity: number;
    percentage: number;
  }>;
}

interface AllocationPreview {
  requested_quantity: number;
  allocation_method: string;
  allocation_details: Array<{
    batch_id: string;
    batch_number: string;
    quantity_used: number;
    contribution_ratio: number;
    contribution_percentage: number;
  }>;
  total_batches_used: number;
  can_fulfill: boolean;
}

export const InventoryLevelTransformationForm: React.FC<InventoryLevelTransformationFormProps> = ({
  onSave,
  onCancel,
  className = ''
}) => {
  const { user } = useAuth();
  const { showToast } = useToast();
  
  const [loading, setLoading] = useState(false);
  const [loadingInventory, setLoadingInventory] = useState(false);
  const [loadingPreview, setLoadingPreview] = useState(false);
  
  const [formData, setFormData] = useState<any>({
    event_id: '',
    transformation_type: 'MILLING',
    company_id: user?.company?.id || '',
    facility_id: '',
    input_product_id: '',
    input_quantity_requested: 0,
    inventory_drawdown_method: 'PROPORTIONAL',
    process_description: '',
    start_time: new Date().toISOString().slice(0, 16),
    expected_outputs: []
  });

  const [inventory, setInventory] = useState<InventoryAvailability | null>(null);
  const [allocationPreview, setAllocationPreview] = useState<AllocationPreview | null>(null);
  const [selectedProduct, setSelectedProduct] = useState<any>(null);

  useEffect(() => {
    // Auto-generate event ID
    const newEventId = `TRANS-${new Date().getFullYear()}-${String(Math.floor(Math.random() * 100000)).padStart(5, '0')}`;
    setFormData((prev: any) => ({
      ...prev,
      company_id: user?.company?.id || '',
      event_id: newEventId,
      start_time: new Date().toISOString().slice(0, 16),
    }));
  }, [user]);

  const handleInputChange = (field: string, value: any) => {
    setFormData((prev: any) => ({
      ...prev,
      [field]: value
    }));
  };

  const loadInventoryAvailability = async (productId: string) => {
    if (!productId) return;
    
    setLoadingInventory(true);
    try {
      const token = localStorage.getItem('auth_token');
      const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
      
      const response = await fetch(`${API_BASE_URL}/api/v1/inventory-transformations/inventory-availability/${productId}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setInventory(data);
        showToast({
          type: 'success',
          title: 'Inventory Loaded',
          message: `Found ${data.total_quantity} ${data.unit} across ${data.batch_count} batches`
        });
      } else {
        throw new Error('Failed to load inventory');
      }
    } catch (error) {
      console.error('Error loading inventory:', error);
      showToast({
        type: 'error',
        title: 'Error',
        message: 'Failed to load inventory availability'
      });
    } finally {
      setLoadingInventory(false);
    }
  };

  const previewAllocation = async () => {
    if (!formData.input_product_id || !formData.input_quantity_requested) {
      showToast({
        type: 'warning',
        title: 'Missing Information',
        message: 'Please select a product and enter quantity to preview allocation'
      });
      return;
    }

    setLoadingPreview(true);
    try {
      const token = localStorage.getItem('auth_token');
      const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
      
      const params = new URLSearchParams({
        product_id: formData.input_product_id,
        requested_quantity: formData.input_quantity_requested.toString(),
        allocation_method: formData.inventory_drawdown_method
      });

      const response = await fetch(`${API_BASE_URL}/api/v1/inventory-transformations/allocation-preview?${params}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setAllocationPreview(data);
        showToast({
          type: 'success',
          title: 'Allocation Preview',
          message: data.can_fulfill ? 'Allocation preview generated' : 'Cannot fulfill request with current inventory'
        });
      } else {
        throw new Error('Failed to preview allocation');
      }
    } catch (error) {
      console.error('Error previewing allocation:', error);
      showToast({
        type: 'error',
        title: 'Error',
        message: 'Failed to preview allocation'
      });
    } finally {
      setLoadingPreview(false);
    }
  };

  const handleSave = async () => {
    if (!allocationPreview?.can_fulfill) {
      showToast({
        type: 'error',
        title: 'Cannot Create Transformation',
        message: 'Please ensure the allocation can be fulfilled before creating the transformation'
      });
      return;
    }

    setLoading(true);
    try {
      await onSave(formData);
      showToast({
        type: 'success',
        title: 'Transformation Created',
        message: 'Your inventory-level transformation has been created successfully'
      });
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

  const renderInventoryInfo = () => {
    if (!inventory) return null;

    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Package className="h-5 w-5" />
            Available Inventory
          </CardTitle>
        </CardHeader>
        <CardBody>
          <div className="grid grid-cols-3 gap-4 mb-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">{inventory.total_quantity}</div>
              <div className="text-sm text-gray-500">{inventory.unit}</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">{inventory.batch_count}</div>
              <div className="text-sm text-gray-500">Batches</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-purple-600">
                {inventory.pool_composition.length}
              </div>
              <div className="text-sm text-gray-500">Active</div>
            </div>
          </div>

          <div className="space-y-2">
            <h4 className="font-medium">Batch Details:</h4>
            {inventory.batches.map((batch, index) => (
              <div key={batch.id} className="flex justify-between items-center p-2 bg-gray-50 rounded">
                <div>
                  <span className="font-medium">{batch.batch_number}</span>
                  <span className="text-sm text-gray-500 ml-2">
                    {batch.production_date}
                  </span>
                </div>
                <div className="text-right">
                  <div className="font-medium">{batch.quantity} {batch.unit}</div>
                  <div className="text-sm text-gray-500">
                    {inventory.pool_composition[index]?.percentage.toFixed(1)}%
                  </div>
                </div>
              </div>
            ))}
          </div>
        </CardBody>
      </Card>
    );
  };

  const renderAllocationPreview = () => {
    if (!allocationPreview) return null;

    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <TrendingUp className="h-5 w-5" />
            Allocation Preview
            {allocationPreview.can_fulfill ? (
              <CheckCircle className="h-5 w-5 text-green-500" />
            ) : (
              <AlertCircle className="h-5 w-5 text-red-500" />
            )}
          </CardTitle>
        </CardHeader>
        <CardBody>
          <div className="mb-4">
            <div className="flex items-center gap-2 mb-2">
              <span className="font-medium">Requested:</span>
              <span>{allocationPreview.requested_quantity} KGM</span>
              <Badge variant={allocationPreview.can_fulfill ? "success" : "error"}>
                {allocationPreview.can_fulfill ? "Can Fulfill" : "Cannot Fulfill"}
              </Badge>
            </div>
            <div className="flex items-center gap-2">
              <span className="font-medium">Method:</span>
              <Badge variant="outline">{allocationPreview.allocation_method}</Badge>
              <span className="font-medium">Batches:</span>
              <Badge variant="outline">{allocationPreview.total_batches_used}</Badge>
            </div>
          </div>

          {allocationPreview.allocation_details.length > 0 && (
            <div className="space-y-2">
              <h4 className="font-medium">Allocation Details:</h4>
              {allocationPreview.allocation_details.map((detail, index) => (
                <div key={detail.batch_id} className="flex justify-between items-center p-2 bg-gray-50 rounded">
                  <div>
                    <span className="font-medium">{detail.batch_number}</span>
                  </div>
                  <div className="text-right">
                    <div className="font-medium">{detail.quantity_used.toFixed(1)} KGM</div>
                    <div className="text-sm text-gray-500">
                      {detail.contribution_percentage.toFixed(1)}%
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardBody>
      </Card>
    );
  };

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Basic Information */}
      <Card>
        <CardHeader>
          <CardTitle>Inventory-Level Transformation</CardTitle>
        </CardHeader>
        <CardBody className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label htmlFor="event_id">Event ID</Label>
              <Input
                id="event_id"
                value={formData.event_id}
                readOnly
                className="bg-gray-50"
                placeholder="Auto-generated"
              />
            </div>
            <div>
              <Label htmlFor="transformation_type">Transformation Type</Label>
              <Select
                value={formData.transformation_type}
                onChange={(e) => handleInputChange('transformation_type', e.target.value)}
                options={[
                  { label: 'MILLING', value: 'MILLING' },
                  { label: 'REFINING', value: 'REFINING' },
                  { label: 'FRACTIONATION', value: 'FRACTIONATION' },
                  { label: 'MANUFACTURING', value: 'MANUFACTURING' }
                ]}
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label htmlFor="facility_id">Facility ID</Label>
              <Input
                id="facility_id"
                value={formData.facility_id}
                onChange={(e) => handleInputChange('facility_id', e.target.value)}
                placeholder="MILL-001, REFINERY-A, etc."
              />
            </div>
            <div>
              <Label htmlFor="start_time">Start Time</Label>
              <Input
                id="start_time"
                type="datetime-local"
                value={formData.start_time}
                onChange={(e) => handleInputChange('start_time', e.target.value)}
              />
            </div>
          </div>

          <div>
            <Label htmlFor="process_description">Process Description</Label>
            <Textarea
              id="process_description"
              value={formData.process_description}
              onChange={(e) => handleInputChange('process_description', e.target.value)}
              placeholder="Brief description of the transformation process"
            />
          </div>
        </CardBody>
      </Card>

      {/* Input Configuration */}
      <Card>
        <CardHeader>
          <CardTitle>Input Configuration</CardTitle>
        </CardHeader>
        <CardBody className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label htmlFor="input_product_id">Input Product</Label>
              <Select
                value={formData.input_product_id}
                onChange={(e) => {
                  handleInputChange('input_product_id', e.target.value);
                  loadInventoryAvailability(e.target.value);
                }}
                options={[
                  { label: 'Select Product', value: '' },
                  { label: 'Fresh Fruit Bunches (FFB)', value: 'ffb-uuid' },
                  { label: 'Crude Palm Oil (CPO)', value: 'cpo-uuid' },
                  { label: 'Refined Palm Oil (RPO)', value: 'rpo-uuid' }
                ]}
              />
            </div>
            <div>
              <Label htmlFor="input_quantity_requested">Quantity Requested</Label>
              <Input
                id="input_quantity_requested"
                type="number"
                value={formData.input_quantity_requested}
                onChange={(e) => handleInputChange('input_quantity_requested', parseFloat(e.target.value))}
                placeholder="800"
              />
            </div>
          </div>

          <div>
            <Label htmlFor="inventory_drawdown_method">Allocation Method</Label>
            <Select
              value={formData.inventory_drawdown_method}
              onChange={(e) => handleInputChange('inventory_drawdown_method', e.target.value)}
              options={[
                { label: 'Proportional (Default)', value: 'PROPORTIONAL' },
                { label: 'First-In-First-Out', value: 'FIFO' },
                { label: 'Last-In-First-Out', value: 'LIFO' },
                { label: 'Entire Batches First', value: 'ENTIRE_BATCHES_FIRST' }
              ]}
            />
          </div>

          <div className="flex gap-2">
            <Button
              onClick={previewAllocation}
              disabled={loadingPreview || !formData.input_product_id || !formData.input_quantity_requested}
              variant="outline"
            >
              {loadingPreview ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin mr-2" />
                  Previewing...
                </>
              ) : (
                'Preview Allocation'
              )}
            </Button>
          </div>
        </CardBody>
      </Card>

      {/* Inventory Information */}
      {renderInventoryInfo()}

      {/* Allocation Preview */}
      {renderAllocationPreview()}

      {/* Action Buttons */}
      <div className="flex justify-end space-x-4">
        <Button variant="outline" onClick={onCancel} disabled={loading}>
          Cancel
        </Button>
        <Button 
          onClick={handleSave} 
          disabled={loading || !allocationPreview?.can_fulfill}
        >
          {loading ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin mr-2" />
              Creating...
            </>
          ) : (
            'Create Transformation'
          )}
        </Button>
      </div>
    </div>
  );
};
