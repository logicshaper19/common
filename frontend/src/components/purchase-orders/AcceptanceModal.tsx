import React, { useState } from 'react';
import { Card, CardHeader, CardBody } from '../ui/Card';
import Button from '../ui/Button';
import Input from '../ui/Input';
import TextArea from '../ui/Textarea';
import { XMarkIcon, CheckCircleIcon, XCircleIcon } from '@heroicons/react/24/outline';
import { PurchaseOrderWithRelations } from '../../services/purchaseOrderApi';
import { useToast } from '../../contexts/ToastContext';

interface AcceptanceModalProps {
  isOpen: boolean;
  onClose: () => void;
  po: PurchaseOrderWithRelations | null;
  onAccept: (acceptanceData: any) => Promise<void>;
  onReject: (rejectionData: any) => Promise<void>;
  isLoading?: boolean;
}

export const AcceptanceModal: React.FC<AcceptanceModalProps> = ({
  isOpen,
  onClose,
  po,
  onAccept,
  onReject,
  isLoading = false
}) => {
  const { showToast } = useToast();
  const [action, setAction] = useState<'accept' | 'reject' | null>(null);
  const [formData, setFormData] = useState({
    acceptance_notes: '',
    acceptance_terms: '',
    expected_delivery_date: '',
    special_instructions: '',
    rejection_reason: '',
    alternative_suggestions: '',
    can_negotiate: false
  });
  const [errors, setErrors] = useState<Record<string, string>>({});

  if (!isOpen || !po) return null;

  const handleInputChange = (field: string, value: string | boolean) => {
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

    if (action === 'accept') {
      // Acceptance validation
      if (!formData.acceptance_notes.trim()) {
        newErrors.acceptance_notes = 'Please provide acceptance notes';
      }
    } else if (action === 'reject') {
      // Rejection validation
      if (!formData.rejection_reason.trim()) {
        newErrors.rejection_reason = 'Please provide a reason for rejection';
      }
      if (formData.rejection_reason.trim().length < 10) {
        newErrors.rejection_reason = 'Rejection reason must be at least 10 characters';
      }
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async () => {
    if (!validateForm()) {
      return;
    }

    try {
      if (action === 'accept') {
        await onAccept({
          accept: true,
          acceptance_notes: formData.acceptance_notes,
          acceptance_terms: formData.acceptance_terms,
          expected_delivery_date: formData.expected_delivery_date || undefined,
          special_instructions: formData.special_instructions
        });
        showToast({ type: 'success', title: 'Purchase order accepted successfully' });
      } else if (action === 'reject') {
        await onReject({
          rejection_reason: formData.rejection_reason,
          alternative_suggestions: formData.alternative_suggestions,
          can_negotiate: formData.can_negotiate
        });
        showToast({ type: 'success', title: 'Purchase order rejected' });
      }
      
      handleClose();
    } catch (error) {
      console.error('Error processing acceptance/rejection:', error);
      showToast({ type: 'error', title: 'Failed to process request' });
    }
  };

  const handleClose = () => {
    setAction(null);
    setFormData({
      acceptance_notes: '',
      acceptance_terms: '',
      expected_delivery_date: '',
      special_instructions: '',
      rejection_reason: '',
      alternative_suggestions: '',
      can_negotiate: false
    });
    setErrors({});
    onClose();
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <Card>
          <CardHeader
            title={`${action === 'accept' ? 'Accept' : action === 'reject' ? 'Reject' : 'Purchase Order Action'} - ${po.po_number}`}
            action={
              <Button
                variant="ghost"
                size="sm"
                onClick={handleClose}
                disabled={isLoading}
              >
                <XMarkIcon className="h-5 w-5" />
              </Button>
            }
          />
          <CardBody>
            {!action ? (
              // Action selection
              <div className="space-y-6">
                <div className="text-center">
                  <h3 className="text-lg font-medium text-gray-900 mb-2">
                    What would you like to do with this purchase order?
                  </h3>
                  <p className="text-sm text-gray-600">
                    Choose to accept or reject this purchase order from {po.buyer_company?.name || 'Unknown Buyer'}
                  </p>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <Button
                    variant="primary"
                    onClick={() => setAction('accept')}
                    className="flex items-center justify-center space-x-2 py-4"
                  >
                    <CheckCircleIcon className="h-6 w-6" />
                    <span>Accept Order</span>
                  </Button>
                  
                  <Button
                    variant="outline"
                    onClick={() => setAction('reject')}
                    className="flex items-center justify-center space-x-2 py-4 border-red-300 text-red-700 hover:bg-red-50"
                  >
                    <XCircleIcon className="h-6 w-6" />
                    <span>Reject Order</span>
                  </Button>
                </div>

                {/* PO Details Summary */}
                <div className="bg-gray-50 rounded-lg p-4">
                  <h4 className="font-medium text-gray-900 mb-2">Order Details</h4>
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="text-gray-600">Product:</span>
                      <span className="ml-2 font-medium">{po.product?.name || 'Unknown'}</span>
                    </div>
                    <div>
                      <span className="text-gray-600">Quantity:</span>
                      <span className="ml-2 font-medium">{po.quantity} {po.unit}</span>
                    </div>
                    <div>
                      <span className="text-gray-600">Total Amount:</span>
                      <span className="ml-2 font-medium">${po.total_amount?.toFixed(2) || '0.00'}</span>
                    </div>
                    <div>
                      <span className="text-gray-600">Delivery Date:</span>
                      <span className="ml-2 font-medium">
                        {po.delivery_date ? new Date(po.delivery_date).toLocaleDateString() : 'Not set'}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            ) : (
              // Form for selected action
              <div className="space-y-6">
                <div className="text-center">
                  <h3 className="text-lg font-medium text-gray-900 mb-2">
                    {action === 'accept' ? 'Accept Purchase Order' : 'Reject Purchase Order'}
                  </h3>
                  <p className="text-sm text-gray-600">
                    {action === 'accept' 
                      ? 'Please provide details about accepting this order'
                      : 'Please provide a reason for rejecting this order'
                    }
                  </p>
                </div>

                {action === 'accept' ? (
                  // Acceptance form
                  <div className="space-y-4">
                    <TextArea
                      label="Acceptance Notes *"
                      value={formData.acceptance_notes}
                      onChange={(e) => handleInputChange('acceptance_notes', e.target.value)}
                      placeholder="Please provide notes about accepting this order..."
                      rows={3}
                      errorMessage={errors.acceptance_notes}
                      required
                    />

                    <TextArea
                      label="Terms and Conditions"
                      value={formData.acceptance_terms}
                      onChange={(e) => handleInputChange('acceptance_terms', e.target.value)}
                      placeholder="Any specific terms or conditions for this order..."
                      rows={3}
                    />

                    <Input
                      label="Expected Delivery Date"
                      type="date"
                      value={formData.expected_delivery_date}
                      onChange={(e) => handleInputChange('expected_delivery_date', e.target.value)}
                    />

                    <TextArea
                      label="Special Instructions"
                      value={formData.special_instructions}
                      onChange={(e) => handleInputChange('special_instructions', e.target.value)}
                      placeholder="Any special delivery or handling instructions..."
                      rows={2}
                    />
                  </div>
                ) : (
                  // Rejection form
                  <div className="space-y-4">
                    <TextArea
                      label="Rejection Reason *"
                      value={formData.rejection_reason}
                      onChange={(e) => handleInputChange('rejection_reason', e.target.value)}
                      placeholder="Please provide a detailed reason for rejecting this order..."
                      rows={4}
                      errorMessage={errors.rejection_reason}
                      required
                    />

                    <TextArea
                      label="Alternative Suggestions"
                      value={formData.alternative_suggestions}
                      onChange={(e) => handleInputChange('alternative_suggestions', e.target.value)}
                      placeholder="Any alternative suggestions or counter-proposals..."
                      rows={3}
                    />

                    <div className="flex items-center">
                      <input
                        type="checkbox"
                        id="can_negotiate"
                        checked={formData.can_negotiate}
                        onChange={(e) => handleInputChange('can_negotiate', e.target.checked)}
                        className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                      />
                      <label htmlFor="can_negotiate" className="ml-2 block text-sm text-gray-700">
                        Open to negotiation
                      </label>
                    </div>
                  </div>
                )}

                {/* Action Buttons */}
                <div className="flex justify-end space-x-3 pt-4 border-t">
                  <Button
                    type="button"
                    variant="secondary"
                    onClick={() => setAction(null)}
                    disabled={isLoading}
                  >
                    Back
                  </Button>
                  <Button
                    type="button"
                    variant={action === 'accept' ? 'primary' : 'outline'}
                    onClick={handleSubmit}
                    disabled={isLoading}
                    className={action === 'reject' ? 'border-red-300 text-red-700 hover:bg-red-50' : ''}
                  >
                    {isLoading ? (
                      <>
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                        Processing...
                      </>
                    ) : (
                      <>
                        {action === 'accept' ? (
                          <>
                            <CheckCircleIcon className="h-4 w-4 mr-2" />
                            Accept Order
                          </>
                        ) : (
                          <>
                            <XCircleIcon className="h-4 w-4 mr-2" />
                            Reject Order
                          </>
                        )}
                      </>
                    )}
                  </Button>
                </div>
              </div>
            )}
          </CardBody>
        </Card>
      </div>
    </div>
  );
};

export default AcceptanceModal;
