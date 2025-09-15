import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Button from '../ui/Button';
import Badge from '../ui/Badge';
import AmendmentStatusBadge from './AmendmentStatusBadge';
import ProposeChangesModal from './ProposeChangesModal';
import ApproveChangesModal from './ApproveChangesModal';
import AcceptanceModal from './AcceptanceModal';
import EditPurchaseOrderModal from './EditPurchaseOrderModal';
import { 
  PencilSquareIcon, 
  CheckCircleIcon,
  CalendarIcon,
  MapPinIcon,
  BuildingOfficeIcon,
  CubeIcon,
  EyeIcon,
  XCircleIcon,
  PencilIcon
} from '@heroicons/react/24/outline';
import { PurchaseOrderWithDetails, PurchaseOrderWithRelations, ProposeChangesRequest, ApproveChangesRequest } from '../../services/purchaseOrderApi';
import { useAuth } from '../../contexts/AuthContext';
import { useToast } from '../../contexts/ToastContext';

interface PurchaseOrderTableProps {
  purchaseOrders: (PurchaseOrderWithDetails | PurchaseOrderWithRelations)[];
  onProposeChanges?: (id: string, proposal: ProposeChangesRequest) => Promise<void>;
  onApproveChanges?: (id: string, approval: ApproveChangesRequest) => Promise<void>;
  onAccept?: (id: string, acceptanceData: any) => Promise<void>;
  onReject?: (id: string, rejectionData: any) => Promise<void>;
  onEdit?: (id: string, editData: any) => Promise<void>;
  onRefresh?: () => void;
  loading?: boolean;
  showAmendmentSection?: boolean;
}

export const PurchaseOrderTable: React.FC<PurchaseOrderTableProps> = ({
  purchaseOrders,
  onProposeChanges,
  onApproveChanges,
  onAccept,
  onReject,
  onEdit,
  onRefresh,
  loading = false,
  showAmendmentSection = false
}) => {
  const { user } = useAuth();
  const { showToast } = useToast();
  const navigate = useNavigate();
  const [selectedPO, setSelectedPO] = useState<(PurchaseOrderWithDetails | PurchaseOrderWithRelations) | null>(null);
  const [showProposeModal, setShowProposeModal] = useState(false);
  const [showApproveModal, setShowApproveModal] = useState(false);
  const [showAcceptanceModal, setShowAcceptanceModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  // Helper function to determine user's role in a PO
  const getUserRole = (po: PurchaseOrderWithDetails | PurchaseOrderWithRelations) => {
    const isBuyer = user?.company?.id === po.buyer_company_id;
    const isSeller = user?.company?.id === po.seller_company_id;
    return { isBuyer, isSeller };
  };

  // Helper function to determine available actions
  const getAvailableActions = (po: PurchaseOrderWithDetails | PurchaseOrderWithRelations) => {
    const { isBuyer, isSeller } = getUserRole(po);
    
    const canProposeChanges = isSeller && 
      po.status === 'PENDING' && 
      po.amendment_status !== 'proposed';
    
    const canApproveChanges = isBuyer && 
      po.amendment_status === 'proposed';
    
    // New acceptance and editing actions
    const canAccept = isSeller && 
      (po.status === 'PENDING' || po.status === 'AWAITING_ACCEPTANCE');
    
    const canReject = isSeller && 
      (po.status === 'PENDING' || po.status === 'AWAITING_ACCEPTANCE');
    
    const canEdit = (isBuyer || isSeller) && 
      (po.status === 'PENDING' || po.status === 'AWAITING_ACCEPTANCE' || po.status === 'ACCEPTED');
    
    return { 
      canProposeChanges, 
      canApproveChanges, 
      canAccept, 
      canReject, 
      canEdit 
    };
  };

  // Status badge variant mapping
  const getStatusBadgeVariant = (status: string) => {
    switch (status.toLowerCase()) {
      case 'draft': return 'neutral';
      case 'pending': return 'warning';
      case 'awaiting_acceptance': return 'warning';
      case 'accepted': return 'success';
      case 'confirmed': return 'success';
      case 'shipped': return 'primary';
      case 'delivered': return 'success';
      case 'cancelled': return 'error';
      case 'rejected': return 'error';
      case 'declined': return 'error';
      default: return 'neutral';
    }
  };

  // Handle propose changes
  const handleProposeChanges = async (proposal: ProposeChangesRequest) => {
    if (!selectedPO || !onProposeChanges) return;
    
    try {
      setActionLoading(selectedPO.id);
      await onProposeChanges(selectedPO.id, proposal);
      setShowProposeModal(false);
      setSelectedPO(null);
      onRefresh?.();
      showToast({
        type: 'success',
        title: 'Amendment Proposed',
        message: 'Your proposed changes have been submitted for review.'
      });
    } catch (error) {
      showToast({
        type: 'error',
        title: 'Failed to Propose Changes',
        message: 'There was an error submitting your proposed changes.'
      });
    } finally {
      setActionLoading(null);
    }
  };

  // Handle approve changes
  const handleApproveChanges = async (approval: ApproveChangesRequest) => {
    if (!selectedPO || !onApproveChanges) return;
    
    try {
      setActionLoading(selectedPO.id);
      await onApproveChanges(selectedPO.id, approval);
      setShowApproveModal(false);
      setSelectedPO(null);
      onRefresh?.();
      showToast({
        type: 'success',
        title: 'Amendment Processed',
        message: approval.approve ? 'Amendment approved successfully.' : 'Amendment rejected.'
      });
    } catch (error) {
      showToast({
        type: 'error',
        title: 'Failed to Process Amendment',
        message: 'There was an error processing the amendment.'
      });
    } finally {
      setActionLoading(null);
    }
  };

  // Handle acceptance
  const handleAccept = async (acceptanceData: any) => {
    if (!selectedPO || !onAccept) return;
    
    try {
      setActionLoading(selectedPO.id);
      await onAccept(selectedPO.id, acceptanceData);
      setShowAcceptanceModal(false);
      setSelectedPO(null);
      onRefresh?.();
    } catch (error) {
      showToast({
        type: 'error',
        title: 'Failed to Accept Order',
        message: 'There was an error accepting the purchase order.'
      });
    } finally {
      setActionLoading(null);
    }
  };

  // Handle rejection
  const handleReject = async (rejectionData: any) => {
    if (!selectedPO || !onReject) return;
    
    try {
      setActionLoading(selectedPO.id);
      await onReject(selectedPO.id, rejectionData);
      setShowAcceptanceModal(false);
      setSelectedPO(null);
      onRefresh?.();
    } catch (error) {
      showToast({
        type: 'error',
        title: 'Failed to Reject Order',
        message: 'There was an error rejecting the purchase order.'
      });
    } finally {
      setActionLoading(null);
    }
  };

  // Handle edit
  const handleEdit = async (editData: any) => {
    if (!selectedPO || !onEdit) return;
    
    try {
      setActionLoading(selectedPO.id);
      await onEdit(selectedPO.id, editData);
      setShowEditModal(false);
      setSelectedPO(null);
      onRefresh?.();
    } catch (error) {
      showToast({
        type: 'error',
        title: 'Failed to Edit Order',
        message: 'There was an error editing the purchase order.'
      });
    } finally {
      setActionLoading(null);
    }
  };

  if (loading) {
    return (
      <div className="bg-white shadow rounded-lg p-6">
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-1/4 mb-4"></div>
          <div className="space-y-3">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="h-4 bg-gray-200 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (purchaseOrders.length === 0) {
    return (
      <div className="bg-white shadow rounded-lg p-6">
        <div className="text-center py-8">
          <CubeIcon className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">No purchase orders</h3>
          <p className="mt-1 text-sm text-gray-500">
            {showAmendmentSection ? 'No amendments awaiting review.' : 'Get started by creating a new purchase order.'}
          </p>
        </div>
      </div>
    );
  }

  return (
    <>
      <div className="bg-white shadow rounded-lg overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Purchase Order
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Companies
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Product & Quantity
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Pricing
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Delivery
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {purchaseOrders.map((po) => {
                const { canProposeChanges, canApproveChanges, canAccept, canReject, canEdit } = getAvailableActions(po);
                const isActionLoading = actionLoading === po.id;
                
                return (
                  <tr key={po.id} className="hover:bg-gray-50">
                    {/* Purchase Order Column */}
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <div>
                          <div className="text-sm font-medium text-gray-900">
                            PO #{po.po_number}
                          </div>
                          <div className="text-sm text-gray-500">
                            {new Date(po.created_at).toLocaleDateString()}
                          </div>
                        </div>
                      </div>
                    </td>

                    {/* Companies Column */}
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-900">
                        <div className="flex items-center mb-1">
                          <BuildingOfficeIcon className="h-4 w-4 text-gray-400 mr-1" />
                          <span className="font-medium">{po.buyer_company?.name || 'Unknown'}</span>
                        </div>
                        <div className="flex items-center text-gray-500">
                          <span className="mr-1">→</span>
                          <span>{po.seller_company?.name || 'Unknown'}</span>
                        </div>
                      </div>
                    </td>

                    {/* Product & Quantity Column */}
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-900">
                        <div className="font-medium">{po.product?.name || 'Unknown'}</div>
                        <div className="text-gray-500 flex items-center">
                          <CubeIcon className="h-4 w-4 mr-1" />
                          {po.quantity} {po.unit}
                        </div>
                      </div>
                    </td>

                    {/* Pricing Column */}
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-900">
                        <div className="font-medium">
                          ${typeof po.total_amount === 'string' ? parseFloat(po.total_amount).toFixed(2) : po.total_amount.toFixed(2)}
                        </div>
                        <div className="text-gray-500">
                          ${typeof po.unit_price === 'string' ? parseFloat(po.unit_price).toFixed(2) : po.unit_price.toFixed(2)}/{po.unit}
                        </div>
                      </div>
                    </td>

                    {/* Status Column */}
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex flex-col space-y-1">
                        <Badge variant={getStatusBadgeVariant(po.status)}>
                          {po.status}
                        </Badge>
                        <AmendmentStatusBadge status={po.amendment_status || 'none'} />
                      </div>
                    </td>

                    {/* Delivery Column */}
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-900">
                        <div className="flex items-center mb-1">
                          <CalendarIcon className="h-4 w-4 text-gray-400 mr-1" />
                          {new Date(po.delivery_date).toLocaleDateString()}
                        </div>
                        <div className="flex items-center text-gray-500">
                          <MapPinIcon className="h-4 w-4 mr-1" />
                          <span className="truncate max-w-24" title={po.delivery_location}>
                            {po.delivery_location}
                          </span>
                        </div>
                      </div>
                    </td>

                    {/* Actions Column */}
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                      <div className="flex justify-end space-x-2">
                        {canProposeChanges && (
                          <Button
                            variant="secondary"
                            size="sm"
                            onClick={() => {
                              setSelectedPO(po);
                              setShowProposeModal(true);
                            }}
                            disabled={isActionLoading}
                          >
                            <PencilSquareIcon className="h-4 w-4 mr-1" />
                            Propose Changes
                          </Button>
                        )}
                        
                        {canApproveChanges && (
                          <Button
                            variant="primary"
                            size="sm"
                            onClick={() => {
                              setSelectedPO(po);
                              setShowApproveModal(true);
                            }}
                            disabled={isActionLoading}
                          >
                            <CheckCircleIcon className="h-4 w-4 mr-1" />
                            Review Amendment
                          </Button>
                        )}

                        {/* New Acceptance and Editing Actions */}
                        {canAccept && (
                          <Button
                            variant="success"
                            size="sm"
                            onClick={() => {
                              setSelectedPO(po);
                              setShowAcceptanceModal(true);
                            }}
                            disabled={isActionLoading}
                            title="Accept Purchase Order"
                          >
                            <CheckCircleIcon className="h-4 w-4 mr-1" />
                            Accept
                          </Button>
                        )}

                        {canReject && (
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => {
                              setSelectedPO(po);
                              setShowAcceptanceModal(true);
                            }}
                            disabled={isActionLoading}
                            className="border-red-300 text-red-700 hover:bg-red-50"
                            title="Reject Purchase Order"
                          >
                            <XCircleIcon className="h-4 w-4 mr-1" />
                            Reject
                          </Button>
                        )}

                        {canEdit && (
                          <Button
                            variant="secondary"
                            size="sm"
                            onClick={() => {
                              setSelectedPO(po);
                              setShowEditModal(true);
                            }}
                            disabled={isActionLoading}
                            title="Edit Purchase Order"
                          >
                            <PencilIcon className="h-4 w-4 mr-1" />
                            Edit
                          </Button>
                        )}

                        {/* View Details Button - always available */}
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => navigate(`/purchase-orders/${po.id}`)}
                          title="View Details"
                        >
                          <EyeIcon className="h-4 w-4" />
                        </Button>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>

        {/* Amendment Information Row - shown when there are proposed amendments */}
        {purchaseOrders.some(po => po.amendment_status === 'proposed') && (
          <div className="bg-amber-50 border-t border-amber-200 px-6 py-4">
            <div className="text-sm text-amber-800">
              <strong>Amendment Details:</strong> Some purchase orders have proposed amendments that require review.
              Click "Review Amendment" to see the proposed changes.
            </div>
          </div>
        )}
      </div>

      {/* Modals */}
      {selectedPO && (
        <>
          <ProposeChangesModal
            purchaseOrder={selectedPO}
            isOpen={showProposeModal}
            onClose={() => {
              setShowProposeModal(false);
              setSelectedPO(null);
            }}
            onPropose={handleProposeChanges}
            isLoading={actionLoading === selectedPO.id}
          />

          <ApproveChangesModal
            purchaseOrder={selectedPO}
            isOpen={showApproveModal}
            onClose={() => {
              setShowApproveModal(false);
              setSelectedPO(null);
            }}
            onApprove={handleApproveChanges}
            isLoading={actionLoading === selectedPO.id}
          />

          <AcceptanceModal
            po={selectedPO}
            isOpen={showAcceptanceModal}
            onClose={() => {
              setShowAcceptanceModal(false);
              setSelectedPO(null);
            }}
            onAccept={handleAccept}
            onReject={handleReject}
            isLoading={actionLoading === selectedPO.id}
          />

          <EditPurchaseOrderModal
            po={selectedPO}
            isOpen={showEditModal}
            onClose={() => {
              setShowEditModal(false);
              setSelectedPO(null);
            }}
            onEdit={handleEdit}
            isLoading={actionLoading === selectedPO.id}
          />
        </>
      )}
    </>
  );
};

export default PurchaseOrderTable;
