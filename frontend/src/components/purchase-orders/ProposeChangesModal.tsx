import React, { useState } from 'react';
import { Card, CardHeader, CardBody } from '../ui/Card';
import Button from '../ui/Button';
import Input from '../ui/Input';
import TextArea from '../ui/Textarea';
import Select from '../ui/Select';
import { PencilSquareIcon, XMarkIcon } from '@heroicons/react/24/outline';
import { PurchaseOrderWithDetails, PurchaseOrderWithRelations, ProposeChangesRequest } from '../../services/purchaseOrderApi';

interface ProposeChangesModalProps {
  purchaseOrder: PurchaseOrderWithDetails | PurchaseOrderWithRelations;
  isOpen: boolean;
  onClose: () => void;
  onPropose: (proposal: ProposeChangesRequest) => Promise<void>;
  isLoading?: boolean;
}

export const ProposeChangesModal: React.FC<ProposeChangesModalProps> = ({
  purchaseOrder,
  isOpen,
  onClose,
  onPropose,
  isLoading = false
}) => {
  const [formData, setFormData] = useState<ProposeChangesRequest>({
    proposed_quantity: purchaseOrder.quantity,
    proposed_quantity_unit: purchaseOrder.unit,
    proposed_delivery_date: purchaseOrder.delivery_date ? new Date(purchaseOrder.delivery_date).toISOString().split('T')[0] : '',
    proposed_delivery_location: purchaseOrder.delivery_location || '',
    amendment_reason: '',
    amendment_type: 'quantity_change'
  });

  const [errors, setErrors] = useState<Record<string, string>>({});

  const handleInputChange = (field: keyof ProposeChangesRequest, value: string | number) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
    
    // Clear error when user starts typing
    if (errors[field]) {
      setErrors(prev => ({
        ...prev,
        [field]: ''
      }));
    }
  };

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    // Validate amendment type
    if (!formData.amendment_type) {
      newErrors.amendment_type = 'Please select an amendment type';
    }

    // Validate based on amendment type
    if (formData.amendment_type === 'quantity_change') {
      if (!formData.proposed_quantity || formData.proposed_quantity <= 0) {
        newErrors.proposed_quantity = 'Proposed quantity must be greater than 0';
      }
      if (!formData.proposed_quantity_unit?.trim()) {
        newErrors.proposed_quantity_unit = 'Unit is required';
      }
    } else if (formData.amendment_type === 'delivery_date_change') {
      if (!formData.proposed_delivery_date?.trim()) {
        newErrors.proposed_delivery_date = 'Proposed delivery date is required';
      }
    } else if (formData.amendment_type === 'delivery_location_change') {
      if (!formData.proposed_delivery_location?.trim()) {
        newErrors.proposed_delivery_location = 'Proposed delivery location is required';
      }
    }

    // Validate reason
    if (!formData.amendment_reason?.trim()) {
      newErrors.amendment_reason = 'Amendment reason is required';
    } else if (formData.amendment_reason.trim().length < 10) {
      newErrors.amendment_reason = 'Amendment reason must be at least 10 characters';
    }

    // Check if anything actually changed
    let hasChanges = false;
    if (formData.amendment_type === 'quantity_change') {
      hasChanges = formData.proposed_quantity !== purchaseOrder.quantity || 
                   formData.proposed_quantity_unit !== purchaseOrder.unit;
    } else if (formData.amendment_type === 'delivery_date_change') {
      const currentDate = purchaseOrder.delivery_date ? new Date(purchaseOrder.delivery_date).toISOString().split('T')[0] : '';
      hasChanges = formData.proposed_delivery_date !== currentDate;
    } else if (formData.amendment_type === 'delivery_location_change') {
      hasChanges = formData.proposed_delivery_location !== (purchaseOrder.delivery_location || '');
    }

    if (!hasChanges) {
      newErrors.general = 'No changes detected. Please modify at least one field.';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    try {
      await onPropose(formData);
      onClose();
    } catch (error) {
      console.error('Error proposing changes:', error);
    }
  };

  const handleClose = () => {
    setFormData({
      proposed_quantity: purchaseOrder.quantity,
      proposed_quantity_unit: purchaseOrder.unit,
      proposed_delivery_date: purchaseOrder.delivery_date ? new Date(purchaseOrder.delivery_date).toISOString().split('T')[0] : '',
      proposed_delivery_location: purchaseOrder.delivery_location || '',
      amendment_reason: '',
      amendment_type: 'quantity_change'
    });
    setErrors({});
    onClose();
  };

  if (!isOpen) return null;

  const quantityChange = (formData.proposed_quantity || 0) - purchaseOrder.quantity;
  const percentageChange = ((quantityChange / purchaseOrder.quantity) * 100).toFixed(1);

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        <Card>
          <CardHeader className="flex items-center justify-between border-b">
            <div className="flex items-center space-x-2">
              <PencilSquareIcon className="h-6 w-6 text-blue-600" />
              <h2 className="text-xl font-semibold text-gray-900">
                Propose Changes to PO #{purchaseOrder.po_number}
              </h2>
            </div>
            <button
              onClick={handleClose}
              className="text-gray-400 hover:text-gray-600 transition-colors"
              disabled={isLoading}
            >
              <XMarkIcon className="h-6 w-6" />
            </button>
          </CardHeader>

          <CardBody className="space-y-6">
            {/* Current Order Summary */}
            <div className="bg-gray-50 rounded-lg p-4">
              <h3 className="text-sm font-medium text-gray-900 mb-3">Current Order Details</h3>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-gray-600">Product:</span>
                  <span className="ml-2 font-medium">{purchaseOrder.product?.name || 'Unknown'}</span>
                </div>
                <div>
                  <span className="text-gray-600">Buyer:</span>
                  <span className="ml-2 font-medium">{purchaseOrder.buyer_company?.name || 'Unknown'}</span>
                </div>
                <div>
                  <span className="text-gray-600">Current Quantity:</span>
                  <span className="ml-2 font-medium">{purchaseOrder.quantity} {purchaseOrder.unit}</span>
                </div>
                <div>
                  <span className="text-gray-600">Unit Price:</span>
                  <span className="ml-2 font-medium">${purchaseOrder.unit_price}</span>
                </div>
              </div>
            </div>

            <form onSubmit={handleSubmit} className="space-y-6">
              {/* Amendment Type Selection - Enhanced */}
              <div className="space-y-4">
                <h3 className="text-lg font-medium text-gray-900">Amendment Type</h3>
                
                <Select
                  label="What would you like to change?"
                  value={formData.amendment_type || ''}
                  onChange={(e) => handleInputChange('amendment_type', e.target.value)}
                  errorMessage={errors.amendment_type}
                  required
                  disabled={isLoading}
                  options={[
                    { label: 'Select amendment type', value: '' },
                    { label: 'Change Quantity', value: 'quantity_change' },
                    { label: 'Change Delivery Date', value: 'delivery_date_change' },
                    { label: 'Change Delivery Location', value: 'delivery_location_change' }
                  ]}
                />
              </div>

              {/* Conditional Fields Based on Amendment Type */}
              {formData.amendment_type === 'quantity_change' && (
                <div className="space-y-4">
                  <h3 className="text-lg font-medium text-gray-900">Quantity Changes</h3>
                  
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Input
                        label="Proposed Quantity"
                        type="number"
                        value={formData.proposed_quantity || ''}
                        onChange={(e) => handleInputChange('proposed_quantity', parseFloat(e.target.value) || 0)}
                        errorMessage={errors.proposed_quantity}
                        min="0"
                        step="0.01"
                        required
                        disabled={isLoading}
                      />
                    </div>
                    
                    <div>
                      <Select
                        label="Unit"
                        value={formData.proposed_quantity_unit || ''}
                        onChange={(e) => handleInputChange('proposed_quantity_unit', e.target.value)}
                        errorMessage={errors.proposed_quantity_unit}
                        required
                        disabled={isLoading}
                        options={[
                          { label: 'Select unit', value: '' },
                          { label: 'Kilograms (kg)', value: 'kg' },
                          { label: 'Pounds (lbs)', value: 'lbs' },
                          { label: 'Tons', value: 'tons' },
                          { label: 'Units', value: 'units' },
                          { label: 'Boxes', value: 'boxes' },
                          { label: 'Pallets', value: 'pallets' }
                        ]}
                      />
                    </div>
                  </div>

                  {/* Quantity Change Summary */}
                  {formData.proposed_quantity && quantityChange !== 0 && (
                    <div className={`p-3 rounded-lg ${
                      quantityChange > 0 ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'
                    }`}>
                      <div className="flex items-center space-x-2">
                        <span className="text-sm font-medium">
                          {quantityChange > 0 ? 'Increase' : 'Decrease'} of {Math.abs(quantityChange)} {formData.proposed_quantity_unit}
                        </span>
                        <span className={`text-sm ${
                          quantityChange > 0 ? 'text-green-600' : 'text-red-600'
                        }`}>
                          ({quantityChange > 0 ? '+' : ''}{percentageChange}%)
                        </span>
                      </div>
                    </div>
                  )}
                </div>
              )}

              {formData.amendment_type === 'delivery_date_change' && (
                <div className="space-y-4">
                  <h3 className="text-lg font-medium text-gray-900">Delivery Date Changes</h3>
                  
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Input
                        label="Current Delivery Date"
                        type="text"
                        value={purchaseOrder.delivery_date ? new Date(purchaseOrder.delivery_date).toLocaleDateString() : 'Not set'}
                        disabled
                        className="bg-gray-50"
                      />
                    </div>
                    
                    <div>
                      <Input
                        label="Proposed Delivery Date"
                        type="date"
                        value={formData.proposed_delivery_date || ''}
                        onChange={(e) => handleInputChange('proposed_delivery_date', e.target.value)}
                        errorMessage={errors.proposed_delivery_date}
                        required
                        disabled={isLoading}
                      />
                    </div>
                  </div>
                </div>
              )}

              {formData.amendment_type === 'delivery_location_change' && (
                <div className="space-y-4">
                  <h3 className="text-lg font-medium text-gray-900">Delivery Location Changes</h3>
                  
                  <div className="space-y-4">
                    <div>
                      <Input
                        label="Current Delivery Location"
                        type="text"
                        value={purchaseOrder.delivery_location || 'Not set'}
                        disabled
                        className="bg-gray-50"
                      />
                    </div>
                    
                    <div>
                      <Input
                        label="Proposed Delivery Location"
                        type="text"
                        value={formData.proposed_delivery_location || ''}
                        onChange={(e) => handleInputChange('proposed_delivery_location', e.target.value)}
                        errorMessage={errors.proposed_delivery_location}
                        placeholder="Enter new delivery location..."
                        required
                        disabled={isLoading}
                      />
                    </div>
                  </div>
                </div>
              )}

              {/* Amendment Reason */}
              <div>
                <TextArea
                  label="Reason for Amendment"
                  value={formData.amendment_reason}
                  onChange={(e) => handleInputChange('amendment_reason', e.target.value)}
                  errorMessage={errors.amendment_reason}
                  placeholder={`Please explain why you need to change the ${formData.amendment_type?.replace('_', ' ') || 'order'}...`}
                  rows={4}
                  required
                  disabled={isLoading}
                />
                <p className="mt-1 text-sm text-gray-500">
                  Minimum 10 characters. Be specific about the reason for the change.
                </p>
              </div>

              {/* General Error */}
              {errors.general && (
                <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
                  <p className="text-sm text-red-600">{errors.general}</p>
                </div>
              )}

              {/* Action Buttons */}
              <div className="flex justify-end space-x-3 pt-4 border-t">
                <Button
                  type="button"
                  variant="secondary"
                  onClick={handleClose}
                  disabled={isLoading}
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  variant="primary"
                  disabled={isLoading}
                  isLoading={isLoading}
                >
                  {isLoading ? 'Proposing Changes...' : 'Propose Changes'}
                </Button>
              </div>
            </form>
          </CardBody>
        </Card>
      </div>
    </div>
  );
};

export default ProposeChangesModal;
