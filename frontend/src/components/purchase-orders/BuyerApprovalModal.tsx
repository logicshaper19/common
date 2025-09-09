import React, { useState } from 'react';
import { X, CheckCircle, XCircle, MessageSquare } from 'lucide-react';

interface BuyerApprovalModalProps {
  isOpen: boolean;
  onClose: () => void;
  onApprove: (notes?: string) => void;
  onReject: (notes?: string) => void;
  isLoading?: boolean;
  action: 'approve' | 'reject';
  sellerCompanyName: string;
  poNumber: string;
}

const BuyerApprovalModal: React.FC<BuyerApprovalModalProps> = ({
  isOpen,
  onClose,
  onApprove,
  onReject,
  isLoading = false,
  action,
  sellerCompanyName,
  poNumber
}) => {
  const [notes, setNotes] = useState('');

  if (!isOpen) return null;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (action === 'approve') {
      onApprove(notes.trim() || undefined);
    } else {
      onReject(notes.trim() || undefined);
    }
  };

  const isApprove = action === 'approve';
  const title = isApprove ? 'Approve Changes' : 'Request Revision';
  const buttonText = isApprove ? 'Approve Changes' : 'Request Revision';
  const buttonColor = isApprove ? 'bg-green-600 hover:bg-green-700' : 'bg-gray-600 hover:bg-gray-700';
  const icon = isApprove ? <CheckCircle className="h-5 w-5" /> : <XCircle className="h-5 w-5" />;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4">
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <h2 className="text-xl font-semibold text-gray-900">{title}</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <X className="h-6 w-6" />
          </button>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="p-6">
            <div className="mb-4">
              <p className="text-gray-700">
                {isApprove ? (
                  <>
                    You are about to approve the changes proposed by{' '}
                    <span className="font-medium">{sellerCompanyName}</span> for purchase order{' '}
                    <span className="font-medium">{poNumber}</span>.
                  </>
                ) : (
                  <>
                    You are about to request a revision from{' '}
                    <span className="font-medium">{sellerCompanyName}</span> for purchase order{' '}
                    <span className="font-medium">{poNumber}</span>.
                  </>
                )}
              </p>
            </div>

            <div className="mb-6">
              <label htmlFor="notes" className="flex items-center space-x-2 text-sm font-medium text-gray-700 mb-2">
                <MessageSquare className="h-4 w-4" />
                <span>
                  {isApprove ? 'Approval Notes (Optional)' : 'Revision Request (Optional)'}
                </span>
              </label>
              <textarea
                id="notes"
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                placeholder={
                  isApprove 
                    ? "Add any notes about this approval..."
                    : "Explain what needs to be revised..."
                }
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-none"
                rows={4}
                maxLength={1000}
              />
              <p className="text-xs text-gray-500 mt-1">
                {notes.length}/1000 characters
              </p>
            </div>

            {isApprove && (
              <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-lg">
                <p className="text-sm text-green-700">
                  <strong>Confirming approval will:</strong>
                </p>
                <ul className="text-sm text-green-700 mt-2 space-y-1">
                  <li>• Update the purchase order with the seller's proposed values</li>
                  <li>• Mark the order as confirmed and ready for fulfillment</li>
                  <li>• Automatically create a batch for tracking</li>
                  <li>• Send a confirmation notification to the seller</li>
                </ul>
              </div>
            )}

            {!isApprove && (
              <div className="mb-6 p-4 bg-amber-50 border border-amber-200 rounded-lg">
                <p className="text-sm text-amber-700">
                  <strong>Requesting revision will:</strong>
                </p>
                <ul className="text-sm text-amber-700 mt-2 space-y-1">
                  <li>• Return the order to pending status</li>
                  <li>• Clear the seller's proposed changes</li>
                  <li>• Send a revision request notification to the seller</li>
                  <li>• Allow the seller to submit new confirmation details</li>
                </ul>
              </div>
            )}
          </div>

          <div className="flex justify-end space-x-3 p-6 border-t border-gray-200">
            <button
              type="button"
              onClick={onClose}
              disabled={isLoading}
              className="px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isLoading}
              className={`flex items-center space-x-2 px-4 py-2 text-white rounded-lg disabled:opacity-50 disabled:cursor-not-allowed transition-colors ${buttonColor}`}
            >
              {icon}
              <span>{isLoading ? 'Processing...' : buttonText}</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default BuyerApprovalModal;
