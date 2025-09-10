/**
 * Simple Confirmation Modal Component
 * Simplified modal for basic purchase order confirmation
 */
import React, { useState } from 'react';
import { XMarkIcon, CheckCircleIcon } from '@heroicons/react/24/outline';
import { PurchaseOrderWithDetails } from '../../services/purchaseOrderApi';
import { useToast } from '../../contexts/ToastContext';
import { formatCurrency, formatDate } from '../../lib/utils';
import Button from '../ui/Button';
import { Card, CardBody } from '../ui/Card';

interface SimpleConfirmationModalProps {
  isOpen: boolean;
  onClose: () => void;
  purchaseOrder: PurchaseOrderWithDetails;
  onSubmit: (confirmation: SimpleConfirmationRequest) => Promise<void>;
}

interface SimpleConfirmationRequest {
  delivery_date?: string;
  notes?: string;
  confirmed_quantity?: number;
  confirmed_unit?: string;
}

const SimpleConfirmationModal: React.FC<SimpleConfirmationModalProps> = ({
  isOpen,
  onClose,
  purchaseOrder,
  onSubmit,
}) => {
  const { showToast } = useToast();
  const [loading, setLoading] = useState(false);
  
  // Simple confirmation fields - optional modifications
  const [deliveryDate, setDeliveryDate] = useState(purchaseOrder.delivery_date);
  const [notes, setNotes] = useState('');
  const [confirmedQuantity, setConfirmedQuantity] = useState<number | undefined>(undefined);
  const [confirmedUnit, setConfirmedUnit] = useState<string | undefined>(undefined);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    setLoading(true);
    
    try {
      const confirmation: SimpleConfirmationRequest = {
        delivery_date: deliveryDate !== purchaseOrder.delivery_date ? deliveryDate : undefined,
        notes: notes.trim() || undefined,
        confirmed_quantity: confirmedQuantity,
        confirmed_unit: confirmedUnit
      };

      await onSubmit(confirmation);
      onClose();
      
      showToast({
        type: 'success',
        title: 'Order Confirmed',
        message: 'Purchase order has been confirmed successfully.'
      });
    } catch (error) {
      showToast({
        type: 'error',
        title: 'Error',
        message: 'Failed to confirm order. Please try again.'
      });
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex items-center justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
        <div className="fixed inset-0 bg-neutral-500 bg-opacity-75 transition-opacity" onClick={onClose} />
        
        <div className="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full">
          <div className="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-medium text-neutral-900">
                Confirm Purchase Order
              </h3>
              <button
                onClick={onClose}
                className="text-neutral-400 hover:text-neutral-600"
              >
                <XMarkIcon className="h-6 w-6" />
              </button>
            </div>

            <div className="mb-6">
              <p className="text-sm text-neutral-600">
                Confirm purchase order <strong>{purchaseOrder.po_number}</strong> for {purchaseOrder.product.name}
              </p>
            </div>

            <form onSubmit={handleSubmit} className="space-y-6">
              {/* Order Summary */}
              <Card>
                <CardBody>
                  <h4 className="font-medium text-neutral-900 mb-4">Order Summary</h4>
                  
                  <div className="space-y-3 text-sm">
                    <div className="flex justify-between">
                      <span className="text-neutral-600">Product:</span>
                      <span className="font-medium">{purchaseOrder.product.name}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-neutral-600">Quantity:</span>
                      <span className="font-medium">{purchaseOrder.quantity} {purchaseOrder.unit}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-neutral-600">Unit Price:</span>
                      <span className="font-medium">{formatCurrency(Number(purchaseOrder.unit_price))}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-neutral-600">Total Amount:</span>
                      <span className="font-medium">{formatCurrency(Number(purchaseOrder.total_amount))}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-neutral-600">Delivery Date:</span>
                      <span className="font-medium">{formatDate(purchaseOrder.delivery_date)}</span>
                    </div>
                  </div>
                </CardBody>
              </Card>

              {/* Optional Modifications */}
              <div className="space-y-4">
                <h4 className="font-medium text-neutral-900">Optional Modifications</h4>
                
                {/* Delivery Date */}
                <div>
                  <label className="block text-sm font-medium text-neutral-700 mb-1">
                    Delivery Date
                  </label>
                  <input
                    type="date"
                    value={deliveryDate}
                    onChange={(e) => setDeliveryDate(e.target.value)}
                    className="w-full border border-neutral-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500"
                  />
                </div>

                {/* Confirmed Quantity (optional override) */}
                <div>
                  <label className="block text-sm font-medium text-neutral-700 mb-1">
                    Confirmed Quantity (optional)
                  </label>
                  <input
                    type="number"
                    step="0.001"
                    value={confirmedQuantity || ''}
                    onChange={(e) => setConfirmedQuantity(e.target.value ? Number(e.target.value) : undefined)}
                    placeholder={`Default: ${purchaseOrder.quantity}`}
                    className="w-full border border-neutral-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500"
                  />
                </div>

                {/* Notes */}
                <div>
                  <label className="block text-sm font-medium text-neutral-700 mb-2">
                    Confirmation Notes (Optional)
                  </label>
                  <textarea
                    value={notes}
                    onChange={(e) => setNotes(e.target.value)}
                    rows={3}
                    placeholder="Add any notes about the confirmation..."
                    className="w-full border border-neutral-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500"
                  />
                </div>
              </div>

              {/* Actions */}
              <div className="flex justify-end space-x-3 pt-4">
                <Button
                  type="button"
                  variant="outline"
                  onClick={onClose}
                  disabled={loading}
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  variant="primary"
                  isLoading={loading}
                  leftIcon={<CheckCircleIcon className="h-4 w-4" />}
                >
                  Confirm Order
                </Button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SimpleConfirmationModal;
