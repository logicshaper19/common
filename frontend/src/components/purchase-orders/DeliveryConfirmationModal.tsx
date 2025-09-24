import React, { useState } from 'react';
import Modal from '../ui/Modal';
import { Button } from '../ui/Button';
import TextArea from '../ui/Textarea';
import { TruckIcon } from '@heroicons/react/24/outline';

interface PurchaseOrder {
  id: string;
  po_number: string;
  quantity: number;
  unit: string;
  buyer_company: {
    name: string;
  };
  seller_company: {
    name: string;
  };
}

interface DeliveryConfirmationModalProps {
  isOpen: boolean;
  onClose: () => void;
  purchaseOrder: PurchaseOrder;
  onConfirm: (notes: string) => Promise<void>;
}

export const DeliveryConfirmationModal: React.FC<DeliveryConfirmationModalProps> = ({
  isOpen,
  onClose,
  purchaseOrder,
  onConfirm
}) => {
  const [deliveryNotes, setDeliveryNotes] = useState('');
  const [isConfirming, setIsConfirming] = useState(false);

  const handleConfirm = async () => {
    setIsConfirming(true);
    try {
      await onConfirm(deliveryNotes);
      setDeliveryNotes(''); // Reset form
      onClose();
    } catch (error) {
      console.error('Error confirming delivery:', error);
      // Error handling is done in parent component
    } finally {
      setIsConfirming(false);
    }
  };

  const handleClose = () => {
    if (!isConfirming) {
      setDeliveryNotes(''); // Reset form
      onClose();
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={handleClose} title="Confirm Delivery" size="md">
      <div className="space-y-6">
        {/* Delivery Confirmation Header */}
        <div className="bg-green-50 p-4 rounded-lg border border-green-200">
          <div className="flex items-center space-x-3">
            <div className="flex-shrink-0">
              <TruckIcon className="h-6 w-6 text-green-600" />
            </div>
            <div>
              <h3 className="text-lg font-medium text-green-800">Delivery Confirmation</h3>
              <p className="text-green-600 text-sm mt-1">
                Confirm that you have received the goods for PO {purchaseOrder.po_number}
              </p>
            </div>
          </div>
        </div>

        {/* Order Details */}
        <div className="bg-gray-50 p-4 rounded-lg">
          <h4 className="text-sm font-medium text-gray-900 mb-3">Order Details</h4>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span className="text-gray-600">Quantity:</span>
              <span className="ml-2 font-medium">{purchaseOrder.quantity} {purchaseOrder.unit}</span>
            </div>
            <div>
              <span className="text-gray-600">From:</span>
              <span className="ml-2 font-medium">{purchaseOrder.seller_company.name}</span>
            </div>
            <div>
              <span className="text-gray-600">To:</span>
              <span className="ml-2 font-medium">{purchaseOrder.buyer_company.name}</span>
            </div>
            <div>
              <span className="text-gray-600">PO Number:</span>
              <span className="ml-2 font-medium">{purchaseOrder.po_number}</span>
            </div>
          </div>
        </div>

        {/* Delivery Notes */}
        <div>
          <TextArea
            label="Delivery Notes (Optional)"
            value={deliveryNotes}
            onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setDeliveryNotes(e.target.value)}
            placeholder="Any notes about the delivery condition, quantity verification, or issues..."
            rows={4}
            disabled={isConfirming}
          />
          <p className="mt-1 text-sm text-gray-500">
            Add any observations about the delivery condition, quantity received, or any issues encountered.
          </p>
        </div>

        {/* Action Buttons */}
        <div className="flex justify-end space-x-3 pt-4 border-t">
          <Button
            type="button"
            variant="secondary"
            onClick={handleClose}
            disabled={isConfirming}
          >
            Cancel
          </Button>
          <Button
            type="button"
            variant="primary"
            onClick={handleConfirm}
            disabled={isConfirming}
            isLoading={isConfirming}
          >
            {isConfirming ? 'Confirming...' : 'Confirm Delivery'}
          </Button>
        </div>
      </div>
    </Modal>
  );
};
