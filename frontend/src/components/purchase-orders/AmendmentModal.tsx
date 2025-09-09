/**
 * Amendment Modal Component
 * Modal for proposing amendments to purchase orders
 */
import React, { useState } from 'react';
import { XMarkIcon, ExclamationTriangleIcon } from '@heroicons/react/24/outline';
import { PurchaseOrderWithDetails } from '../../services/purchaseOrderApi';
import { useToast } from '../../contexts/ToastContext';
import { formatCurrency } from '../../lib/utils';
import Button from '../ui/Button';
import { Card, CardBody } from '../ui/Card';

interface AmendmentModalProps {
  isOpen: boolean;
  onClose: () => void;
  purchaseOrder: PurchaseOrderWithDetails;
  onSubmit: (amendment: AmendmentRequest) => Promise<void>;
}

interface AmendmentRequest {
  amendment_type: 'quantity_change' | 'delivery_date_change' | 'price_change' | 'location_change';
  reason: string;
  priority: 'low' | 'medium' | 'high' | 'critical';
  changes: {
    field: string;
    current_value: any;
    proposed_value: any;
  }[];
  notes?: string;
}

const AmendmentModal: React.FC<AmendmentModalProps> = ({
  isOpen,
  onClose,
  purchaseOrder,
  onSubmit,
}) => {
  const { showToast } = useToast();
  const [loading, setLoading] = useState(false);
  const [amendmentType, setAmendmentType] = useState<AmendmentRequest['amendment_type']>('quantity_change');
  const [reason, setReason] = useState('');
  const [priority, setPriority] = useState<AmendmentRequest['priority']>('medium');
  const [notes, setNotes] = useState('');
  
  // Form fields for different amendment types
  const [proposedQuantity, setProposedQuantity] = useState(Number(purchaseOrder.quantity));
  const [proposedPrice, setProposedPrice] = useState(Number(purchaseOrder.unit_price));
  const [proposedDeliveryDate, setProposedDeliveryDate] = useState(purchaseOrder.delivery_date);
  const [proposedLocation, setProposedLocation] = useState(purchaseOrder.delivery_location);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!reason.trim()) {
      showToast({
        type: 'error',
        title: 'Validation Error',
        message: 'Please provide a reason for the amendment.'
      });
      return;
    }

    setLoading(true);
    
    try {
      const changes = [];
      
      switch (amendmentType) {
        case 'quantity_change':
          if (proposedQuantity !== Number(purchaseOrder.quantity)) {
            changes.push({
              field: 'quantity',
              current_value: Number(purchaseOrder.quantity),
              proposed_value: proposedQuantity
            });
          }
          break;
        case 'price_change':
          if (proposedPrice !== Number(purchaseOrder.unit_price)) {
            changes.push({
              field: 'unit_price',
              current_value: Number(purchaseOrder.unit_price),
              proposed_value: proposedPrice
            });
          }
          break;
        case 'delivery_date_change':
          if (proposedDeliveryDate !== purchaseOrder.delivery_date) {
            changes.push({
              field: 'delivery_date',
              current_value: purchaseOrder.delivery_date,
              proposed_value: proposedDeliveryDate
            });
          }
          break;
        case 'location_change':
          if (proposedLocation !== purchaseOrder.delivery_location) {
            changes.push({
              field: 'delivery_location',
              current_value: purchaseOrder.delivery_location,
              proposed_value: proposedLocation
            });
          }
          break;
      }

      if (changes.length === 0) {
        showToast({
          type: 'error',
          title: 'No Changes',
          message: 'Please make at least one change to propose an amendment.'
        });
        return;
      }

      const amendment: AmendmentRequest = {
        amendment_type: amendmentType,
        reason,
        priority,
        changes,
        notes: notes.trim() || undefined
      };

      await onSubmit(amendment);
      onClose();
      
      showToast({
        type: 'success',
        title: 'Amendment Proposed',
        message: 'Your amendment has been submitted for review.'
      });
    } catch (error) {
      showToast({
        type: 'error',
        title: 'Error',
        message: 'Failed to propose amendment. Please try again.'
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
        
        <div className="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-2xl sm:w-full">
          <div className="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-medium text-neutral-900">
                Propose Amendment
              </h3>
              <button
                onClick={onClose}
                className="text-neutral-400 hover:text-neutral-600"
              >
                <XMarkIcon className="h-6 w-6" />
              </button>
            </div>

            <form onSubmit={handleSubmit} className="space-y-6">
              {/* Amendment Type */}
              <div>
                <label className="block text-sm font-medium text-neutral-700 mb-2">
                  Amendment Type
                </label>
                <select
                  value={amendmentType}
                  onChange={(e) => setAmendmentType(e.target.value as AmendmentRequest['amendment_type'])}
                  className="w-full border border-neutral-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500"
                >
                  <option value="quantity_change">Quantity Change</option>
                  <option value="price_change">Price Change</option>
                  <option value="delivery_date_change">Delivery Date Change</option>
                  <option value="location_change">Delivery Location Change</option>
                </select>
              </div>

              {/* Amendment Fields */}
              <Card>
                <CardBody>
                  <h4 className="font-medium text-neutral-900 mb-4">Proposed Changes</h4>
                  
                  {amendmentType === 'quantity_change' && (
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-neutral-700 mb-1">
                          Current Quantity
                        </label>
                        <p className="text-neutral-900">{purchaseOrder.quantity} {purchaseOrder.unit}</p>
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-neutral-700 mb-1">
                          Proposed Quantity
                        </label>
                        <input
                          type="number"
                          step="0.001"
                          value={proposedQuantity}
                          onChange={(e) => setProposedQuantity(Number(e.target.value))}
                          className="w-full border border-neutral-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500"
                        />
                      </div>
                    </div>
                  )}

                  {amendmentType === 'price_change' && (
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-neutral-700 mb-1">
                          Current Unit Price
                        </label>
                        <p className="text-neutral-900">{formatCurrency(Number(purchaseOrder.unit_price))}</p>
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-neutral-700 mb-1">
                          Proposed Unit Price
                        </label>
                        <input
                          type="number"
                          step="0.01"
                          value={proposedPrice}
                          onChange={(e) => setProposedPrice(Number(e.target.value))}
                          className="w-full border border-neutral-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500"
                        />
                      </div>
                    </div>
                  )}

                  {amendmentType === 'delivery_date_change' && (
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-neutral-700 mb-1">
                          Current Delivery Date
                        </label>
                        <p className="text-neutral-900">{purchaseOrder.delivery_date}</p>
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-neutral-700 mb-1">
                          Proposed Delivery Date
                        </label>
                        <input
                          type="date"
                          value={proposedDeliveryDate}
                          onChange={(e) => setProposedDeliveryDate(e.target.value)}
                          className="w-full border border-neutral-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500"
                        />
                      </div>
                    </div>
                  )}

                  {amendmentType === 'location_change' && (
                    <div className="space-y-4">
                      <div>
                        <label className="block text-sm font-medium text-neutral-700 mb-1">
                          Current Delivery Location
                        </label>
                        <p className="text-neutral-900">{purchaseOrder.delivery_location}</p>
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-neutral-700 mb-1">
                          Proposed Delivery Location
                        </label>
                        <textarea
                          value={proposedLocation}
                          onChange={(e) => setProposedLocation(e.target.value)}
                          rows={3}
                          className="w-full border border-neutral-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500"
                        />
                      </div>
                    </div>
                  )}
                </CardBody>
              </Card>

              {/* Reason */}
              <div>
                <label className="block text-sm font-medium text-neutral-700 mb-2">
                  Reason for Amendment *
                </label>
                <select
                  value={reason}
                  onChange={(e) => setReason(e.target.value)}
                  className="w-full border border-neutral-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500"
                  required
                >
                  <option value="">Select a reason</option>
                  <option value="supply_shortage">Supply Shortage</option>
                  <option value="demand_change">Demand Change</option>
                  <option value="logistics_issue">Logistics Issue</option>
                  <option value="quality_concern">Quality Concern</option>
                  <option value="market_conditions">Market Conditions</option>
                  <option value="other">Other</option>
                </select>
              </div>

              {/* Priority */}
              <div>
                <label className="block text-sm font-medium text-neutral-700 mb-2">
                  Priority
                </label>
                <select
                  value={priority}
                  onChange={(e) => setPriority(e.target.value as AmendmentRequest['priority'])}
                  className="w-full border border-neutral-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500"
                >
                  <option value="low">Low</option>
                  <option value="medium">Medium</option>
                  <option value="high">High</option>
                  <option value="critical">Critical</option>
                </select>
              </div>

              {/* Notes */}
              <div>
                <label className="block text-sm font-medium text-neutral-700 mb-2">
                  Additional Notes
                </label>
                <textarea
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  rows={3}
                  placeholder="Provide any additional context or details..."
                  className="w-full border border-neutral-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500"
                />
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
                  leftIcon={<ExclamationTriangleIcon className="h-4 w-4" />}
                >
                  Propose Amendment
                </Button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AmendmentModal;
