/**
 * Confirmation Modal Component
 * Modal for sellers to confirm purchase orders with originator detection
 */
import React, { useState, useEffect } from 'react';
import { XMarkIcon, CheckCircleIcon } from '@heroicons/react/24/outline';
import { PurchaseOrderWithDetails } from '../../services/purchaseOrderApi';
import { useAuth } from '../../contexts/AuthContext';
import { useToast } from '../../contexts/ToastContext';
import { formatCurrency, formatDate } from '../../lib/utils';
import Button from '../ui/Button';
import { Card, CardBody } from '../ui/Card';
import OriginatorConfirmationForm from '../origin/OriginatorConfirmationForm';

interface ConfirmationModalProps {
  isOpen: boolean;
  onClose: () => void;
  purchaseOrder: PurchaseOrderWithDetails;
  onSubmit: (confirmation: ConfirmationRequest) => Promise<void>;
}

interface ConfirmationRequest {
  confirmed_quantity: number;
  confirmed_unit_price: number;
  confirmed_delivery_date: string;
  confirmed_delivery_location: string;
  seller_notes?: string;
  origin_data?: any; // Origin data for originators
}

const ConfirmationModal: React.FC<ConfirmationModalProps> = ({
  isOpen,
  onClose,
  purchaseOrder,
  onSubmit,
}) => {
  const { user } = useAuth();
  const { showToast } = useToast();
  const [loading, setLoading] = useState(false);
  const [isOriginator, setIsOriginator] = useState(false);
  const [showOriginForm, setShowOriginForm] = useState(false);
  const [originData, setOriginData] = useState(null);

  // Confirmation fields - start with original values
  const [confirmedQuantity, setConfirmedQuantity] = useState(Number(purchaseOrder.quantity));
  const [confirmedPrice, setConfirmedPrice] = useState(Number(purchaseOrder.unit_price));
  const [confirmedDeliveryDate, setConfirmedDeliveryDate] = useState(purchaseOrder.delivery_date);
  const [confirmedLocation, setConfirmedLocation] = useState(purchaseOrder.delivery_location);
  const [sellerNotes, setSellerNotes] = useState('');

  // Detect if user is an originator
  useEffect(() => {
    const checkOriginatorStatus = () => {
      // Check if user's company is an originator based on multiple criteria
      const companyType = user?.company?.company_type;
      const sectorId = user?.sector_id;
      const tierLevel = user?.tier_level;

      // Check if company type indicates originator (legacy and new types)
      const isOriginatorType = companyType === 'originator' || 
                              companyType === 'plantation_grower' || 
                              companyType === 'smallholder_cooperative';

      // Check if sector/tier indicates originator (T6/T7 in palm oil)
      const isOriginatorTier = (sectorId === 'palm_oil' && (tierLevel === 6 || tierLevel === 7)) ||
                              (sectorId === 'apparel' && tierLevel === 6);

      // Check if user has originator permissions
      const hasOriginatorPermissions = user?.permissions?.includes('add_origin_data') ||
                                      user?.permissions?.includes('provide_farmer_data');

      const originatorStatus = Boolean(isOriginatorType || isOriginatorTier || hasOriginatorPermissions);
      setIsOriginator(originatorStatus);

      // For raw materials from originators, show origin form by default
      if (originatorStatus && purchaseOrder.product.category === 'raw_material') {
        setShowOriginForm(true);
      }
    };

    if (user && isOpen) {
      checkOriginatorStatus();
    }
  }, [user, isOpen, purchaseOrder.product.category]);

  // Handle origin data submission
  const handleOriginDataSubmit = async (submittedOriginData: any) => {
    setOriginData(submittedOriginData);

    // Proceed with standard confirmation including origin data
    const confirmation: ConfirmationRequest = {
      confirmed_quantity: confirmedQuantity,
      confirmed_unit_price: confirmedPrice,
      confirmed_delivery_date: confirmedDeliveryDate,
      confirmed_delivery_location: confirmedLocation,
      seller_notes: sellerNotes.trim() || undefined,
      origin_data: submittedOriginData
    };

    setLoading(true);

    try {
      await onSubmit(confirmation);
      onClose();

      showToast({
        type: 'success',
        title: 'Order Confirmed with Origin Data',
        message: 'Purchase order has been confirmed with complete origin information.'
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

  const handleStandardSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (confirmedQuantity <= 0) {
      showToast({
        type: 'error',
        title: 'Validation Error',
        message: 'Confirmed quantity must be greater than zero.'
      });
      return;
    }

    if (confirmedPrice <= 0) {
      showToast({
        type: 'error',
        title: 'Validation Error',
        message: 'Confirmed price must be greater than zero.'
      });
      return;
    }

    // Check if originator should provide origin data
    if (isOriginator && purchaseOrder.product.category === 'raw_material' && !originData) {
      showToast({
        type: 'warning',
        title: 'Origin Data Required',
        message: 'As an originator, please provide origin data for this raw material.'
      });
      setShowOriginForm(true);
      return;
    }

    setLoading(true);

    try {
      const confirmation: ConfirmationRequest = {
        confirmed_quantity: confirmedQuantity,
        confirmed_unit_price: confirmedPrice,
        confirmed_delivery_date: confirmedDeliveryDate,
        confirmed_delivery_location: confirmedLocation,
        seller_notes: sellerNotes.trim() || undefined,
        origin_data: originData
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

  // Calculate totals
  const originalTotal = Number(purchaseOrder.quantity) * Number(purchaseOrder.unit_price);
  const confirmedTotal = confirmedQuantity * confirmedPrice;
  const totalDifference = confirmedTotal - originalTotal;

  if (!isOpen) return null;

  // Show originator form if required
  if (showOriginForm && isOriginator) {
    return (
      <div className="fixed inset-0 z-50 overflow-y-auto">
        <div className="flex items-center justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
          <div className="fixed inset-0 bg-neutral-500 bg-opacity-75 transition-opacity" onClick={onClose} />

          <div className="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-4xl sm:w-full">
            <div className="bg-white px-4 pt-5 pb-4 sm:p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-medium text-neutral-900">
                  Originator Confirmation - {purchaseOrder.po_number}
                </h3>
                <button
                  onClick={onClose}
                  className="text-neutral-400 hover:text-neutral-600"
                >
                  <XMarkIcon className="h-6 w-6" />
                </button>
              </div>

              <OriginatorConfirmationForm
                purchaseOrderId={purchaseOrder.po_number}
                productType={purchaseOrder.product.name}
                onSubmit={handleOriginDataSubmit}
                onCancel={() => setShowOriginForm(false)}
                isLoading={loading}
              />
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex items-center justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
        <div className="fixed inset-0 bg-neutral-500 bg-opacity-75 transition-opacity" onClick={onClose} />

        <div className="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-2xl sm:w-full">
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
                Review and confirm the details for purchase order <strong>{purchaseOrder.po_number}</strong>
              </p>
            </div>

            <form onSubmit={handleStandardSubmit} className="space-y-6">

              {/* Originator Status Indicator */}
              {isOriginator && (
                <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                  <div className="flex items-center space-x-2">
                    <CheckCircleIcon className="h-5 w-5 text-green-500" />
                    <div>
                      <p className="text-sm font-medium text-green-800">
                        Originator Status Detected
                      </p>
                      <p className="text-sm text-green-700">
                        {purchaseOrder.product.category === 'raw_material'
                          ? 'Origin data capture is required for this raw material.'
                          : 'You can optionally provide origin data for enhanced traceability.'
                        }
                      </p>
                      {!showOriginForm && purchaseOrder.product.category === 'raw_material' && (
                        <Button
                          type="button"
                          variant="outline"
                          size="sm"
                          className="mt-2"
                          onClick={() => setShowOriginForm(true)}
                        >
                          Add Origin Data
                        </Button>
                      )}
                    </div>
                  </div>
                </div>
              )}
              {/* Original vs Confirmed Comparison */}
              <Card>
                <CardBody>
                  <h4 className="font-medium text-neutral-900 mb-4">Order Details</h4>
                  
                  <div className="space-y-4">
                    {/* Product */}
                    <div>
                      <label className="block text-sm font-medium text-neutral-700 mb-1">
                        Product
                      </label>
                      <p className="text-neutral-900">{purchaseOrder.product.name}</p>
                    </div>

                    {/* Quantity */}
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-neutral-700 mb-1">
                          Requested Quantity
                        </label>
                        <p className="text-neutral-900">{purchaseOrder.quantity} {purchaseOrder.unit}</p>
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-neutral-700 mb-1">
                          Confirmed Quantity *
                        </label>
                        <input
                          type="number"
                          step="0.001"
                          value={confirmedQuantity}
                          onChange={(e) => setConfirmedQuantity(Number(e.target.value))}
                          className="w-full border border-neutral-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500"
                          required
                        />
                      </div>
                    </div>

                    {/* Price */}
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-neutral-700 mb-1">
                          Requested Unit Price
                        </label>
                        <p className="text-neutral-900">{formatCurrency(Number(purchaseOrder.unit_price))}</p>
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-neutral-700 mb-1">
                          Confirmed Unit Price *
                        </label>
                        <input
                          type="number"
                          step="0.01"
                          value={confirmedPrice}
                          onChange={(e) => setConfirmedPrice(Number(e.target.value))}
                          className="w-full border border-neutral-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500"
                          required
                        />
                      </div>
                    </div>

                    {/* Delivery Date */}
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-neutral-700 mb-1">
                          Requested Delivery Date
                        </label>
                        <p className="text-neutral-900">{formatDate(purchaseOrder.delivery_date)}</p>
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-neutral-700 mb-1">
                          Confirmed Delivery Date *
                        </label>
                        <input
                          type="date"
                          value={confirmedDeliveryDate}
                          onChange={(e) => setConfirmedDeliveryDate(e.target.value)}
                          className="w-full border border-neutral-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500"
                          required
                        />
                      </div>
                    </div>

                    {/* Delivery Location */}
                    <div className="space-y-4">
                      <div>
                        <label className="block text-sm font-medium text-neutral-700 mb-1">
                          Requested Delivery Location
                        </label>
                        <p className="text-neutral-900">{purchaseOrder.delivery_location}</p>
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-neutral-700 mb-1">
                          Confirmed Delivery Location *
                        </label>
                        <textarea
                          value={confirmedLocation}
                          onChange={(e) => setConfirmedLocation(e.target.value)}
                          rows={3}
                          className="w-full border border-neutral-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500"
                          required
                        />
                      </div>
                    </div>
                  </div>
                </CardBody>
              </Card>

              {/* Total Comparison */}
              <Card>
                <CardBody>
                  <h4 className="font-medium text-neutral-900 mb-4">Total Amount</h4>
                  
                  <div className="grid grid-cols-3 gap-4 text-center">
                    <div>
                      <label className="block text-sm font-medium text-neutral-700 mb-1">
                        Original Total
                      </label>
                      <p className="text-lg font-semibold text-neutral-900">
                        {formatCurrency(originalTotal)}
                      </p>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-neutral-700 mb-1">
                        Confirmed Total
                      </label>
                      <p className="text-lg font-semibold text-neutral-900">
                        {formatCurrency(confirmedTotal)}
                      </p>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-neutral-700 mb-1">
                        Difference
                      </label>
                      <p className={`text-lg font-semibold ${
                        totalDifference > 0 ? 'text-red-600' : 
                        totalDifference < 0 ? 'text-green-600' : 'text-neutral-900'
                      }`}>
                        {totalDifference > 0 ? '+' : ''}{formatCurrency(totalDifference)}
                      </p>
                    </div>
                  </div>
                </CardBody>
              </Card>

              {/* Seller Notes */}
              <div>
                <label className="block text-sm font-medium text-neutral-700 mb-2">
                  Seller Notes (Optional)
                </label>
                <textarea
                  value={sellerNotes}
                  onChange={(e) => setSellerNotes(e.target.value)}
                  rows={3}
                  placeholder="Add any notes about the confirmation, changes, or special instructions..."
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

export default ConfirmationModal;
