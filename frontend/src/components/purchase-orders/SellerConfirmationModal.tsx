import React, { useState } from 'react';
import { Card, CardHeader, CardBody } from '../ui/Card';
import Button from '../ui/Button';
import Input from '../ui/Input';
import TextArea from '../ui/Textarea';
import BatchInventorySelector from '../inventory/BatchInventorySelector';
import useBatchValidation from '../../hooks/useBatchValidation';
import { CheckCircleIcon, XMarkIcon } from '@heroicons/react/24/outline';

interface PurchaseOrder {
  id: string;
  po_number: string;
  quantity: number;
  unit_price: number;
  delivery_date: string;
  delivery_location: string;
  product: {
    id: string;
    name: string;
    default_unit: string;
  };
  buyer_company: {
    id: string;
    name: string;
  };
  seller_company: {
    id: string;
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

interface BatchSelection {
  batchId: string;
  quantityToUse: number;
  batch: {
    id: string;
    batch_id: string;
    quantity: number;
    unit: string;
  };
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
  const [selectedBatches, setSelectedBatches] = useState<BatchSelection[]>([]);
  const [useInventorySelector, setUseInventorySelector] = useState(true);

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

  const handleBatchesSelected = (selections: BatchSelection[], totalQuantity: number) => {
    setSelectedBatches(selections);
    setFormData(prev => ({
      ...prev,
      confirmed_quantity: totalQuantity
    }));

    // Clear quantity error when batches are selected
    if (errors.confirmed_quantity) {
      setErrors(prev => ({
        ...prev,
        confirmed_quantity: ''
      }));
    }
  };

  // Validate batch selections when using inventory selector
  const batchValidation = useBatchValidation(selectedBatches, useInventorySelector ? purchaseOrder.quantity : undefined);

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!formData.confirmed_quantity || formData.confirmed_quantity <= 0) {
      newErrors.confirmed_quantity = 'Confirmed quantity must be greater than 0';
    }

    if (formData.confirmed_unit_price && formData.confirmed_unit_price <= 0) {
      newErrors.confirmed_unit_price = 'Confirmed price must be greater than 0';
    }

    // Validate batch selections when using inventory selector
    if (useInventorySelector && !batchValidation.isValid) {
      newErrors.batch_selection = 'Please fix batch selection errors before confirming';
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

            <form onSubmit={handleSubmit} className="space-y-6">
              {/* Inventory Selection Toggle */}
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-medium text-gray-900">Quantity Confirmation</h3>
                <div className="flex items-center space-x-2">
                  <label className="text-sm text-gray-600">Use Inventory:</label>
                  <button
                    type="button"
                    onClick={() => setUseInventorySelector(!useInventorySelector)}
                    className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                      useInventorySelector ? 'bg-blue-600' : 'bg-gray-200'
                    }`}
                  >
                    <span
                      className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                        useInventorySelector ? 'translate-x-6' : 'translate-x-1'
                      }`}
                    />
                  </button>
                </div>
              </div>

              {useInventorySelector ? (
                /* Inventory Selector */
                <div className="space-y-4">
                  <BatchInventorySelector
                    companyId={purchaseOrder.seller_company.id}
                    productId={purchaseOrder.product.id}
                    targetQuantity={purchaseOrder.quantity}
                    onBatchesSelected={handleBatchesSelected}
                    disabled={isLoading}
                  />

                  {/* Confirmed Quantity Display (Read-only) */}
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium text-blue-900">Total Confirmed Quantity:</span>
                      <span className="text-lg font-bold text-blue-900">
                        {formData.confirmed_quantity.toFixed(3)} {purchaseOrder.product.default_unit}
                      </span>
                    </div>
                    {quantityDifference !== 0 && (
                      <p className={`text-sm mt-2 ${quantityDifference > 0 ? 'text-green-700' : 'text-orange-700'}`}>
                        {quantityDifference > 0 ? '+' : ''}{quantityDifference.toFixed(3)} {purchaseOrder.product.default_unit} vs. requested
                      </p>
                    )}
                  </div>

                  {/* Batch Selection Error */}
                  {errors.batch_selection && (
                    <div className="mt-2 text-sm text-red-600">
                      {errors.batch_selection}
                    </div>
                  )}
                </div>
              ) : (
                /* Manual Quantity Input */
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
              )}

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
