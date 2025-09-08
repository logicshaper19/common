import React, { useState } from 'react';
import { Card, CardHeader, CardBody } from '../ui/Card';
import Button from '../ui/Button';
import Input from '../ui/Input';
import TextArea from '../ui/Textarea';
import Select from '../ui/Select';
import { PencilSquareIcon, XMarkIcon } from '@heroicons/react/24/outline';
import { PurchaseOrderWithDetails, ProposeChangesRequest } from '../../services/purchaseOrderApi';

interface ProposeChangesModalProps {
  purchaseOrder: PurchaseOrderWithDetails;
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
    amendment_reason: ''
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

    if (!formData.proposed_quantity || formData.proposed_quantity <= 0) {
      newErrors.proposed_quantity = 'Proposed quantity must be greater than 0';
    }

    if (!formData.proposed_quantity_unit?.trim()) {
      newErrors.proposed_quantity_unit = 'Unit is required';
    }

    if (!formData.amendment_reason?.trim()) {
      newErrors.amendment_reason = 'Amendment reason is required';
    } else if (formData.amendment_reason.trim().length < 10) {
      newErrors.amendment_reason = 'Amendment reason must be at least 10 characters';
    }

    // Check if anything actually changed
    if (
      formData.proposed_quantity === purchaseOrder.quantity &&
      formData.proposed_quantity_unit === purchaseOrder.unit
    ) {
      newErrors.proposed_quantity = 'Please change the quantity or unit to propose an amendment';
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
      amendment_reason: ''
    });
    setErrors({});
    onClose();
  };

  if (!isOpen) return null;

  const quantityChange = formData.proposed_quantity - purchaseOrder.quantity;
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
                  <span className="ml-2 font-medium">{purchaseOrder.product.name}</span>
                </div>
                <div>
                  <span className="text-gray-600">Buyer:</span>
                  <span className="ml-2 font-medium">{purchaseOrder.buyer_company.name}</span>
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
              {/* Proposed Changes */}
              <div className="space-y-4">
                <h3 className="text-lg font-medium text-gray-900">Proposed Changes</h3>
                
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Input
                      label="Proposed Quantity"
                      type="number"
                      value={formData.proposed_quantity}
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
                      value={formData.proposed_quantity_unit}
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

                {/* Change Summary */}
                {quantityChange !== 0 && (
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

                <div>
                  <TextArea
                    label="Reason for Amendment"
                    value={formData.amendment_reason}
                    onChange={(e) => handleInputChange('amendment_reason', e.target.value)}
                    errorMessage={errors.amendment_reason}
                    placeholder="Please explain why you need to change the order quantity..."
                    rows={4}
                    required
                    disabled={isLoading}
                  />
                  <p className="mt-1 text-sm text-gray-500">
                    Minimum 10 characters. Be specific about the reason for the change.
                  </p>
                </div>
              </div>

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
