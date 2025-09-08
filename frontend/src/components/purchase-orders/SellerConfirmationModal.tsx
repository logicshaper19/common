import React, { useState } from 'react';
import { Card, CardHeader, CardBody } from '../ui/Card';
import Button from '../ui/Button';
import Input from '../ui/Input';
import TextArea from '../ui/Textarea';
import { CheckCircleIcon, XMarkIcon } from '@heroicons/react/24/outline';

interface PurchaseOrder {
  id: string;
  po_number: string;
  quantity: number;
  unit_price: number;
  delivery_date: string;
  delivery_location: string;
  product: {
    name: string;
    default_unit: string;
  };
  buyer_company: {
    name: string;
  };
}

interface SellerConfirmationData {
  confirmed_quantity: number;
  confirmed_unit_price?: number;
  confirmed_delivery_date?: string;
  confirmed_delivery_location?: string;
  seller_notes?: string;
}

interface SellerConfirmationModalProps {
  purchaseOrder: PurchaseOrder;
  isOpen: boolean;
  onClose: () => void;
  onConfirm: (confirmation: SellerConfirmationData) => Promise<void>;
  isLoading?: boolean;
}

export const SellerConfirmationModal: React.FC<SellerConfirmationModalProps> = ({
  purchaseOrder,
  isOpen,
  onClose,
  onConfirm,
  isLoading = false
}) => {
  const [formData, setFormData] = useState<SellerConfirmationData>({
    confirmed_quantity: purchaseOrder.quantity,
    confirmed_unit_price: purchaseOrder.unit_price,
    confirmed_delivery_date: purchaseOrder.delivery_date,
    confirmed_delivery_location: purchaseOrder.delivery_location,
    seller_notes: ''
  });

  const [errors, setErrors] = useState<Record<string, string>>({});

  const handleInputChange = (field: keyof SellerConfirmationData, value: any) => {
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

    if (!formData.confirmed_quantity || formData.confirmed_quantity <= 0) {
      newErrors.confirmed_quantity = 'Confirmed quantity must be greater than 0';
    }

    if (formData.confirmed_unit_price && formData.confirmed_unit_price <= 0) {
      newErrors.confirmed_unit_price = 'Confirmed price must be greater than 0';
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
      await onConfirm(formData);
      onClose();
    } catch (error) {
      console.error('Failed to confirm purchase order:', error);
    }
  };

  const quantityDifference = formData.confirmed_quantity - purchaseOrder.quantity;
  const priceDifference = (formData.confirmed_unit_price || 0) - purchaseOrder.unit_price;

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        <Card>
          <CardHeader className="flex justify-between items-center border-b">
            <div>
              <h2 className="text-xl font-semibold">Confirm Purchase Order</h2>
              <p className="text-gray-600">PO #{purchaseOrder.po_number} from {purchaseOrder.buyer_company.name}</p>
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600"
            >
              <XMarkIcon className="h-5 w-5" />
            </Button>
          </CardHeader>

          <CardBody className="space-y-6">
            {/* Original Request Summary */}
            <div className="bg-gray-50 p-4 rounded-lg">
              <h3 className="font-medium text-gray-900 mb-2">Original Request</h3>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-gray-600">Product:</span>
                  <span className="ml-2 font-medium">{purchaseOrder.product.name}</span>
                </div>
                <div>
                  <span className="text-gray-600">Quantity:</span>
                  <span className="ml-2 font-medium">{purchaseOrder.quantity} {purchaseOrder.product.default_unit}</span>
                </div>
                <div>
                  <span className="text-gray-600">Unit Price:</span>
                  <span className="ml-2 font-medium">${purchaseOrder.unit_price}</span>
                </div>
                <div>
                  <span className="text-gray-600">Delivery Date:</span>
                  <span className="ml-2 font-medium">{new Date(purchaseOrder.delivery_date).toLocaleDateString()}</span>
                </div>
              </div>
            </div>

            <form onSubmit={handleSubmit} className="space-y-4">
              {/* Confirmed Quantity */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Confirmed Quantity *
                </label>
                <Input
                  type="number"
                  step="0.001"
                  value={formData.confirmed_quantity}
                  onChange={(e) => handleInputChange('confirmed_quantity', parseFloat(e.target.value) || 0)}
                  errorMessage={errors.confirmed_quantity}
                  placeholder="Enter confirmed quantity"
                />
                {quantityDifference !== 0 && (
                  <p className={`text-sm mt-1 ${quantityDifference > 0 ? 'text-green-600' : 'text-orange-600'}`}>
                    {quantityDifference > 0 ? '+' : ''}{quantityDifference.toFixed(3)} {purchaseOrder.product.default_unit} vs. requested
                  </p>
                )}
              </div>

              {/* Confirmed Unit Price */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Confirmed Unit Price
                </label>
                <Input
                  type="number"
                  step="0.01"
                  value={formData.confirmed_unit_price || ''}
                  onChange={(e) => handleInputChange('confirmed_unit_price', parseFloat(e.target.value) || undefined)}
                  errorMessage={errors.confirmed_unit_price}
                  placeholder="Enter confirmed price (optional)"
                />
                {priceDifference !== 0 && formData.confirmed_unit_price && (
                  <p className={`text-sm mt-1 ${priceDifference > 0 ? 'text-green-600' : 'text-red-600'}`}>
                    {priceDifference > 0 ? '+' : ''}${priceDifference.toFixed(2)} vs. requested
                  </p>
                )}
              </div>

              {/* Confirmed Delivery Date */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Confirmed Delivery Date
                </label>
                <Input
                  type="date"
                  value={formData.confirmed_delivery_date || ''}
                  onChange={(e) => handleInputChange('confirmed_delivery_date', e.target.value || undefined)}
                  placeholder="Select confirmed delivery date"
                />
              </div>

              {/* Confirmed Delivery Location */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Confirmed Delivery Location
                </label>
                <Input
                  value={formData.confirmed_delivery_location || ''}
                  onChange={(e) => handleInputChange('confirmed_delivery_location', e.target.value || undefined)}
                  placeholder="Enter confirmed delivery location"
                />
              </div>

              {/* Seller Notes */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Notes & Conditions
                </label>
                <TextArea
                  value={formData.seller_notes || ''}
                  onChange={(e) => handleInputChange('seller_notes', e.target.value || undefined)}
                  placeholder="Add any notes, conditions, or explanations for the buyer..."
                  rows={3}
                />
              </div>

              {/* Action Buttons */}
              <div className="flex justify-end space-x-3 pt-4 border-t">
                <Button
                  type="button"
                  variant="outline"
                  onClick={onClose}
                  disabled={isLoading}
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  disabled={isLoading}
                  className="bg-green-600 hover:bg-green-700 text-white"
                >
                  {isLoading ? (
                    'Confirming...'
                  ) : (
                    <>
                      <CheckCircleIcon className="h-4 w-4 mr-2" />
                      Confirm Order
                    </>
                  )}
                </Button>
              </div>
            </form>
          </CardBody>
        </Card>
      </div>
    </div>
  );
};

export default SellerConfirmationModal;
