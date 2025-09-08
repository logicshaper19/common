import React, { useState } from 'react';
import { Card, CardHeader, CardBody } from '../ui/Card';
import Button from '../ui/Button';
import Badge from '../ui/Badge';
import AmendmentStatusBadge from './AmendmentStatusBadge';
import ProposeChangesModal from './ProposeChangesModal';
import ApproveChangesModal from './ApproveChangesModal';
import { 
  PencilSquareIcon, 
  CheckCircleIcon,
  CalendarIcon,
  MapPinIcon,
  BuildingOfficeIcon,
  CubeIcon
} from '@heroicons/react/24/outline';
import { PurchaseOrderWithDetails, ProposeChangesRequest, ApproveChangesRequest } from '../../services/purchaseOrderApi';
import { useAuth } from '../../contexts/AuthContext';
import { useToast } from '../../contexts/ToastContext';

interface PurchaseOrderCardProps {
  purchaseOrder: PurchaseOrderWithDetails;
  onProposeChanges?: (id: string, proposal: ProposeChangesRequest) => Promise<void>;
  onApproveChanges?: (id: string, approval: ApproveChangesRequest) => Promise<void>;
  onRefresh?: () => void;
}

export const PurchaseOrderCard: React.FC<PurchaseOrderCardProps> = ({
  purchaseOrder,
  onProposeChanges,
  onApproveChanges,
  onRefresh
}) => {
  const { user } = useAuth();
  const { showToast } = useToast();
  const [showProposeModal, setShowProposeModal] = useState(false);
  const [showApproveModal, setShowApproveModal] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  // Determine user's role in this PO
  const isBuyer = user?.company?.id === purchaseOrder.buyer_company_id;
  const isSeller = user?.company?.id === purchaseOrder.seller_company_id;

  // Determine what actions are available
  const canProposeChanges = isSeller && 
    purchaseOrder.status === 'PENDING' && 
    purchaseOrder.amendment_status !== 'proposed';

  const canApproveChanges = isBuyer && 
    purchaseOrder.amendment_status === 'proposed';

  const handleProposeChanges = async (proposal: ProposeChangesRequest) => {
    if (!onProposeChanges) return;
    
    setIsLoading(true);
    try {
      await onProposeChanges(purchaseOrder.id, proposal);
      showToast({ type: 'success', title: 'Amendment proposal submitted successfully' });
      onRefresh?.();
    } catch (error) {
      showToast({ type: 'error', title: 'Failed to submit amendment proposal' });
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  const handleApproveChanges = async (approval: ApproveChangesRequest) => {
    if (!onApproveChanges) return;
    
    setIsLoading(true);
    try {
      await onApproveChanges(purchaseOrder.id, approval);
      showToast({
        type: approval.approve ? 'success' : 'info',
        title: approval.approve ? 'Amendment approved successfully' : 'Amendment rejected'
      });
      onRefresh?.();
    } catch (error) {
      showToast({ type: 'error', title: 'Failed to process amendment decision' });
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  const getStatusBadgeVariant = (status: string) => {
    switch (status) {
      case 'PENDING': return 'warning';
      case 'CONFIRMED': return 'success';
      case 'CANCELLED': return 'error';
      case 'DELIVERED': return 'primary';
      default: return 'neutral';
    }
  };

  return (
    <>
      <Card className="hover:shadow-lg transition-shadow">
        <CardHeader className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <h3 className="text-lg font-semibold text-gray-900">
              PO #{purchaseOrder.po_number}
            </h3>
            <Badge variant={getStatusBadgeVariant(purchaseOrder.status)}>
              {purchaseOrder.status}
            </Badge>
            <AmendmentStatusBadge status={purchaseOrder.amendment_status || 'none'} />
          </div>
          
          <div className="flex items-center space-x-2">
            {canProposeChanges && (
              <Button
                variant="secondary"
                size="sm"
                onClick={() => setShowProposeModal(true)}
                disabled={isLoading}
              >
                <PencilSquareIcon className="h-4 w-4 mr-1" />
                Propose Changes
              </Button>
            )}
            
            {canApproveChanges && (
              <Button
                variant="primary"
                size="sm"
                onClick={() => setShowApproveModal(true)}
                disabled={isLoading}
              >
                <CheckCircleIcon className="h-4 w-4 mr-1" />
                Review Amendment
              </Button>
            )}
          </div>
        </CardHeader>

        <CardBody className="space-y-4">
          {/* Company Information */}
          <div className="grid grid-cols-2 gap-4">
            <div className="flex items-center space-x-2">
              <BuildingOfficeIcon className="h-4 w-4 text-gray-400" />
              <div>
                <p className="text-sm text-gray-600">Buyer</p>
                <p className="font-medium">{purchaseOrder.buyer_company.name}</p>
              </div>
            </div>
            <div className="flex items-center space-x-2">
              <BuildingOfficeIcon className="h-4 w-4 text-gray-400" />
              <div>
                <p className="text-sm text-gray-600">Seller</p>
                <p className="font-medium">{purchaseOrder.seller_company.name}</p>
              </div>
            </div>
          </div>

          {/* Product Information */}
          <div className="flex items-center space-x-2">
            <CubeIcon className="h-4 w-4 text-gray-400" />
            <div>
              <p className="text-sm text-gray-600">Product</p>
              <p className="font-medium">{purchaseOrder.product.name}</p>
            </div>
          </div>

          {/* Order Details */}
          <div className="grid grid-cols-3 gap-4">
            <div>
              <p className="text-sm text-gray-600">Quantity</p>
              <p className="font-medium">
                {purchaseOrder.quantity} {purchaseOrder.unit}
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Unit Price</p>
              <p className="font-medium">${typeof purchaseOrder.unit_price === 'string' ? parseFloat(purchaseOrder.unit_price).toFixed(2) : purchaseOrder.unit_price.toFixed(2)}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Total Amount</p>
              <p className="font-medium">${typeof purchaseOrder.total_amount === 'string' ? parseFloat(purchaseOrder.total_amount).toFixed(2) : purchaseOrder.total_amount.toFixed(2)}</p>
            </div>
          </div>

          {/* Amendment Information */}
          {purchaseOrder.amendment_status === 'proposed' && (
            <div className="bg-amber-50 border border-amber-200 rounded-lg p-3">
              <h4 className="text-sm font-medium text-amber-800 mb-2">Proposed Amendment</h4>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-amber-700">Proposed Quantity:</span>
                  <span className="ml-2 font-medium">
                    {purchaseOrder.proposed_quantity} {purchaseOrder.proposed_quantity_unit}
                  </span>
                </div>
                <div>
                  <span className="text-amber-700">Change:</span>
                  <span className="ml-2 font-medium">
                    {((purchaseOrder.proposed_quantity || 0) - purchaseOrder.quantity) > 0 ? '+' : ''}
                    {(purchaseOrder.proposed_quantity || 0) - purchaseOrder.quantity} {purchaseOrder.proposed_quantity_unit}
                  </span>
                </div>
              </div>
              {purchaseOrder.amendment_reason && (
                <div className="mt-2">
                  <span className="text-amber-700 text-sm">Reason:</span>
                  <p className="text-amber-800 text-sm mt-1">{purchaseOrder.amendment_reason}</p>
                </div>
              )}
            </div>
          )}

          {/* Delivery Information */}
          <div className="grid grid-cols-2 gap-4">
            <div className="flex items-center space-x-2">
              <CalendarIcon className="h-4 w-4 text-gray-400" />
              <div>
                <p className="text-sm text-gray-600">Delivery Date</p>
                <p className="font-medium">
                  {new Date(purchaseOrder.delivery_date).toLocaleDateString()}
                </p>
              </div>
            </div>
            <div className="flex items-center space-x-2">
              <MapPinIcon className="h-4 w-4 text-gray-400" />
              <div>
                <p className="text-sm text-gray-600">Delivery Location</p>
                <p className="font-medium">{purchaseOrder.delivery_location}</p>
              </div>
            </div>
          </div>

          {/* Amendment History */}
          {(purchaseOrder.amendment_count || 0) > 0 && (
            <div className="text-sm text-gray-600">
              <span>Amendment History: {purchaseOrder.amendment_count} amendment(s)</span>
              {purchaseOrder.last_amended_at && (
                <span className="ml-2">
                  Last amended: {new Date(purchaseOrder.last_amended_at).toLocaleDateString()}
                </span>
              )}
            </div>
          )}
        </CardBody>
      </Card>

      {/* Modals */}
      <ProposeChangesModal
        purchaseOrder={purchaseOrder}
        isOpen={showProposeModal}
        onClose={() => setShowProposeModal(false)}
        onPropose={handleProposeChanges}
        isLoading={isLoading}
      />

      <ApproveChangesModal
        purchaseOrder={purchaseOrder}
        isOpen={showApproveModal}
        onClose={() => setShowApproveModal(false)}
        onApprove={handleApproveChanges}
        isLoading={isLoading}
      />
    </>
  );
};

export default PurchaseOrderCard;
