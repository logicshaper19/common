import React, { useState } from 'react';
import { Card, CardHeader, CardBody } from '../ui/Card';
import Button from '../ui/Button';
import TextArea from '../ui/Textarea';
import { CheckCircleIcon, XCircleIcon, XMarkIcon, ExclamationTriangleIcon } from '@heroicons/react/24/outline';
import { PurchaseOrderWithDetails, ApproveChangesRequest } from '../../services/purchaseOrderApi';

interface ApproveChangesModalProps {
  purchaseOrder: PurchaseOrderWithDetails;
  isOpen: boolean;
  onClose: () => void;
  onApprove: (approval: ApproveChangesRequest) => Promise<void>;
  isLoading?: boolean;
}

export const ApproveChangesModal: React.FC<ApproveChangesModalProps> = ({
  purchaseOrder,
  isOpen,
  onClose,
  onApprove,
  isLoading = false
}) => {
  const [decision, setDecision] = useState<'approve' | 'reject' | null>(null);
  const [buyerNotes, setBuyerNotes] = useState('');
  const [errors, setErrors] = useState<Record<string, string>>({});

  const handleDecisionChange = (newDecision: 'approve' | 'reject') => {
    setDecision(newDecision);
    setErrors({});
  };

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!decision) {
      newErrors.decision = 'Please select approve or reject';
    }

    if (decision === 'reject' && !buyerNotes.trim()) {
      newErrors.buyerNotes = 'Please provide a reason for rejecting the amendment';
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
      await onApprove({
        approve: decision === 'approve',
        buyer_notes: buyerNotes.trim() || undefined
      });
      onClose();
    } catch (error) {
      console.error('Error processing amendment decision:', error);
    }
  };

  const handleClose = () => {
    setDecision(null);
    setBuyerNotes('');
    setErrors({});
    onClose();
  };

  if (!isOpen) return null;

  const quantityChange = (purchaseOrder.proposed_quantity || 0) - purchaseOrder.quantity;
  const percentageChange = ((quantityChange / purchaseOrder.quantity) * 100).toFixed(1);
  const newTotalAmount = (purchaseOrder.proposed_quantity || 0) * purchaseOrder.unit_price;
  const totalAmountChange = newTotalAmount - purchaseOrder.total_amount;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        <Card>
          <CardHeader className="flex items-center justify-between border-b">
            <div className="flex items-center space-x-2">
              <ExclamationTriangleIcon className="h-6 w-6 text-amber-600" />
              <h2 className="text-xl font-semibold text-gray-900">
                Review Amendment Request
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
            {/* Amendment Summary */}
            <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
              <h3 className="text-sm font-medium text-amber-800 mb-3">
                Amendment Request for PO #{purchaseOrder.po_number}
              </h3>
              <div className="text-sm text-amber-700">
                <p><strong>From:</strong> {purchaseOrder.seller_company.name}</p>
                <p><strong>Product:</strong> {purchaseOrder.product.name}</p>
              </div>
            </div>

            {/* Current vs Proposed Comparison */}
            <div className="grid grid-cols-2 gap-6">
              {/* Current Order */}
              <div className="space-y-3">
                <h4 className="font-medium text-gray-900">Current Order</h4>
                <div className="bg-gray-50 rounded-lg p-4 space-y-2">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Quantity:</span>
                    <span className="font-medium">{purchaseOrder.quantity} {purchaseOrder.unit}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Unit Price:</span>
                    <span className="font-medium">${purchaseOrder.unit_price}</span>
                  </div>
                  <div className="flex justify-between border-t pt-2">
                    <span className="text-gray-600">Total Amount:</span>
                    <span className="font-medium">${purchaseOrder.total_amount.toFixed(2)}</span>
                  </div>
                </div>
              </div>

              {/* Proposed Changes */}
              <div className="space-y-3">
                <h4 className="font-medium text-gray-900">Proposed Changes</h4>
                <div className="bg-blue-50 rounded-lg p-4 space-y-2">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Quantity:</span>
                    <span className="font-medium">
                      {purchaseOrder.proposed_quantity} {purchaseOrder.proposed_quantity_unit}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Unit Price:</span>
                    <span className="font-medium">${purchaseOrder.unit_price}</span>
                  </div>
                  <div className="flex justify-between border-t pt-2">
                    <span className="text-gray-600">New Total:</span>
                    <span className="font-medium">${newTotalAmount.toFixed(2)}</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Change Impact */}
            <div className={`p-4 rounded-lg ${
              quantityChange > 0 ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'
            }`}>
              <h4 className="font-medium text-gray-900 mb-2">Impact Summary</h4>
              <div className="space-y-1 text-sm">
                <div className="flex justify-between">
                  <span>Quantity Change:</span>
                  <span className={`font-medium ${
                    quantityChange > 0 ? 'text-green-600' : 'text-red-600'
                  }`}>
                    {quantityChange > 0 ? '+' : ''}{quantityChange} {purchaseOrder.proposed_quantity_unit} ({quantityChange > 0 ? '+' : ''}{percentageChange}%)
                  </span>
                </div>
                <div className="flex justify-between">
                  <span>Total Amount Change:</span>
                  <span className={`font-medium ${
                    totalAmountChange > 0 ? 'text-green-600' : 'text-red-600'
                  }`}>
                    {totalAmountChange > 0 ? '+' : ''}${totalAmountChange.toFixed(2)}
                  </span>
                </div>
              </div>
            </div>

            {/* Amendment Reason */}
            <div className="space-y-2">
              <h4 className="font-medium text-gray-900">Reason for Amendment</h4>
              <div className="bg-gray-50 rounded-lg p-3">
                <p className="text-sm text-gray-700">{purchaseOrder.amendment_reason}</p>
              </div>
            </div>

            <form onSubmit={handleSubmit} className="space-y-6">
              {/* Decision Buttons */}
              <div className="space-y-4">
                <h4 className="font-medium text-gray-900">Your Decision</h4>
                <div className="grid grid-cols-2 gap-4">
                  <button
                    type="button"
                    onClick={() => handleDecisionChange('approve')}
                    className={`p-4 rounded-lg border-2 transition-all ${
                      decision === 'approve'
                        ? 'border-green-500 bg-green-50 text-green-700'
                        : 'border-gray-200 hover:border-green-300 text-gray-700'
                    }`}
                    disabled={isLoading}
                  >
                    <div className="flex items-center justify-center space-x-2">
                      <CheckCircleIcon className="h-6 w-6" />
                      <span className="font-medium">Approve Changes</span>
                    </div>
                    <p className="text-sm mt-1">Accept the proposed amendment</p>
                  </button>

                  <button
                    type="button"
                    onClick={() => handleDecisionChange('reject')}
                    className={`p-4 rounded-lg border-2 transition-all ${
                      decision === 'reject'
                        ? 'border-red-500 bg-red-50 text-red-700'
                        : 'border-gray-200 hover:border-red-300 text-gray-700'
                    }`}
                    disabled={isLoading}
                  >
                    <div className="flex items-center justify-center space-x-2">
                      <XCircleIcon className="h-6 w-6" />
                      <span className="font-medium">Reject Changes</span>
                    </div>
                    <p className="text-sm mt-1">Decline the proposed amendment</p>
                  </button>
                </div>
                {errors.decision && (
                  <p className="text-red-600 text-sm">{errors.decision}</p>
                )}
              </div>

              {/* Buyer Notes */}
              <div>
                <TextArea
                  label={decision === 'reject' ? 'Reason for Rejection (Required)' : 'Additional Notes (Optional)'}
                  value={buyerNotes}
                  onChange={(e) => setBuyerNotes(e.target.value)}
                  error={errors.buyerNotes}
                  placeholder={
                    decision === 'reject'
                      ? 'Please explain why you are rejecting this amendment...'
                      : 'Any additional comments or instructions...'
                  }
                  rows={3}
                  required={decision === 'reject'}
                  disabled={isLoading}
                />
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
                  variant={decision === 'approve' ? 'primary' : 'danger'}
                  disabled={isLoading || !decision}
                  loading={isLoading}
                >
                  {isLoading 
                    ? 'Processing...' 
                    : decision === 'approve' 
                      ? 'Approve Amendment' 
                      : 'Reject Amendment'
                  }
                </Button>
              </div>
            </form>
          </CardBody>
        </Card>
      </div>
    </div>
  );
};

export default ApproveChangesModal;
