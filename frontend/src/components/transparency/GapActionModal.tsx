/**
 * Gap Action Modal Component
 * Modal for creating gap resolution actions
 */
import React, { useState, useEffect } from 'react';
import { XMarkIcon } from '@heroicons/react/24/outline';
import { TransparencyGap } from '../../hooks/useDeterministicTransparency';
import { GapActionRequest } from './GapActionsPanel';
import Button from '../ui/Button';
import { Card, CardBody } from '../ui/Card';

interface GapActionModalProps {
  isOpen: boolean;
  onClose: () => void;
  actionType: GapActionRequest['action_type'];
  gap: TransparencyGap;
  onSubmit: (action: GapActionRequest) => Promise<void>;
  loading: boolean;
}

export const GapActionModal: React.FC<GapActionModalProps> = ({
  isOpen,
  onClose,
  actionType,
  gap,
  onSubmit,
  loading
}) => {
  const [message, setMessage] = useState('');
  const [targetCompanyId, setTargetCompanyId] = useState('');

  useEffect(() => {
    if (isOpen) {
      // Reset form when modal opens
      setMessage('');
      setTargetCompanyId('');
      
      // Set default message based on action type
      switch (actionType) {
        case 'request_data':
          setMessage(`Hi, we need additional traceability data for PO ${gap.po_number}. Could you please provide mill/plantation information for this order?`);
          break;
        case 'contact_supplier':
          setMessage(`Regarding PO ${gap.po_number}, we need to discuss traceability requirements. Please contact us to resolve transparency gaps.`);
          break;
        case 'mark_resolved':
          setMessage('Gap has been resolved through offline communication or data collection.');
          break;
      }
    }
  }, [isOpen, actionType, gap.po_number]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!message.trim()) {
      return;
    }

    const actionData: GapActionRequest = {
      action_type: actionType,
      message: message.trim(),
      target_company_id: targetCompanyId || undefined
    };

    await onSubmit(actionData);
  };

  const getActionTitle = () => {
    switch (actionType) {
      case 'request_data':
        return 'Request Traceability Data';
      case 'contact_supplier':
        return 'Contact Supplier';
      case 'mark_resolved':
        return 'Mark Gap as Resolved';
      default:
        return 'Gap Action';
    }
  };

  const getActionDescription = () => {
    switch (actionType) {
      case 'request_data':
        return 'Send a formal request for additional traceability data to resolve this transparency gap.';
      case 'contact_supplier':
        return 'Initiate direct communication with the supplier to discuss traceability requirements.';
      case 'mark_resolved':
        return 'Mark this gap as resolved if it has been addressed through other means.';
      default:
        return 'Take action to resolve this transparency gap.';
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
                {getActionTitle()}
              </h3>
              <button
                onClick={onClose}
                className="text-neutral-400 hover:text-neutral-600"
                disabled={loading}
              >
                <XMarkIcon className="h-6 w-6" />
              </button>
            </div>

            <div className="mb-6">
              <p className="text-sm text-neutral-600 mb-4">
                {getActionDescription()}
              </p>
              
              <Card>
                <CardBody>
                  <h4 className="font-medium text-neutral-900 mb-2">Gap Details</h4>
                  <div className="space-y-2 text-sm">
                    <div><strong>PO Number:</strong> {gap.po_number}</div>
                    <div><strong>Supplier:</strong> {gap.seller_company_name}</div>
                    <div><strong>Product:</strong> {gap.product_name}</div>
                    <div><strong>Gap Type:</strong> {gap.gap_type === 'not_traced_to_mill' ? 'Mill Traceability' : 'Plantation Traceability'}</div>
                    <div><strong>Quantity:</strong> {gap.quantity.toLocaleString()} {gap.unit}</div>
                  </div>
                </CardBody>
              </Card>
            </div>

            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-neutral-700 mb-2">
                  Message
                </label>
                <textarea
                  value={message}
                  onChange={(e) => setMessage(e.target.value)}
                  rows={4}
                  className="w-full border border-neutral-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  placeholder="Enter your message..."
                  required
                  disabled={loading}
                />
              </div>

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
                  disabled={!message.trim() || loading}
                >
                  {actionType === 'mark_resolved' ? 'Mark Resolved' : 'Send Action'}
                </Button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
};

export default GapActionModal;
