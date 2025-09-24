/**
 * Purchase Order Detail Page
 * Comprehensive view for managing purchase orders, amendments, and confirmations
 */
import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  DocumentTextIcon,
  PencilIcon,
  CheckCircleIcon,
  XCircleIcon,
  ClockIcon,
  ArrowLeftIcon,
  PrinterIcon,
  MapIcon,
  CogIcon,
} from '@heroicons/react/24/outline';
import { useAuth } from '../contexts/AuthContext';
import { purchaseOrderApi, PurchaseOrderWithDetails, ProposeChangesRequest, PurchaseOrderConfirmation, ConfirmationResponse } from '../services/purchaseOrderApi';
import { useToast } from '../contexts/ToastContext';
import { useAmendments } from '../hooks/useAmendments';
import { Card, CardHeader, CardBody } from '../components/ui/Card';
import Button from '../components/ui/Button';
import Badge from '../components/ui/Badge';
import { ProposeChangesModal } from '../components/purchase-orders/ProposeChangesModal';
import ConfirmationModal from '../components/purchase-orders/ConfirmationModal';
import EditPurchaseOrderModal from '../components/purchase-orders/EditPurchaseOrderModal';
import PurchaseOrderTraceability from '../components/purchase-orders/PurchaseOrderTraceability';
import { DeliveryConfirmationModal } from '../components/purchase-orders/DeliveryConfirmationModal';
import { PurchaseOrderTransformations } from '../components/purchase-orders/PurchaseOrderTransformations';
import { TransformationPrompt } from '../components/transformation/TransformationPrompt';
import { TransformationWizard } from '../components/transformation/TransformationWizard';
import { cn, formatCurrency, formatDate } from '../lib/utils';

const PurchaseOrderDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { user } = useAuth();
  const { showToast } = useToast();
  const { proposeChanges } = useAmendments();

  const [purchaseOrder, setPurchaseOrder] = useState<PurchaseOrderWithDetails | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'details' | 'amendments' | 'history' | 'traceability' | 'transformations'>('details');
  const [showAmendmentModal, setShowAmendmentModal] = useState(false);
  const [showConfirmationModal, setShowConfirmationModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showDeliveryConfirmationModal, setShowDeliveryConfirmationModal] = useState(false);
  const [showTransformationPrompt, setShowTransformationPrompt] = useState(false);
  const [showTransformationWizard, setShowTransformationWizard] = useState(false);

  const loadPurchaseOrder = useCallback(async () => {
    if (!id) return;
    
    try {
      setLoading(true);
      const data = await purchaseOrderApi.getPurchaseOrder(id);
      setPurchaseOrder(data);
    } catch (error) {
      showToast({
        type: 'error',
        title: 'Error loading purchase order',
        message: 'Please try again or contact support if the problem persists.'
      });
      navigate('/purchase-orders');
    } finally {
      setLoading(false);
    }
  }, [id, showToast, navigate]);

  useEffect(() => {
    if (id) {
      loadPurchaseOrder();
    }
  }, [id, loadPurchaseOrder]);

  // Check if we should show transformation prompt
  const shouldShowTransformationPrompt = () => {
    if (!purchaseOrder) return false;
    
    // Show for processor companies with raw materials
    const isProcessor = ['processor', 'mill', 'refinery', 'manufacturer'].includes(
      purchaseOrder.buyer_company?.company_type?.toLowerCase() || ''
    );
    
    const isRawMaterial = purchaseOrder.product.category === 'raw_material' || 
                         purchaseOrder.product.name.toLowerCase().includes('fresh fruit bunches') ||
                         purchaseOrder.product.name.toLowerCase().includes('ffb');
    
    return isProcessor && isRawMaterial;
  };

  // Transformation prompt handlers
  const handleCreateTransformationNow = () => {
    setShowTransformationWizard(true);
  };

  const handleScheduleTransformationLater = async () => {
    // Create a pending transformation reminder
    try {
      // This would create a pending transformation event
      showToast({
        type: 'info',
        title: 'Transformation Scheduled',
        message: 'Transformation has been marked for later processing.'
      });
    } catch (error) {
      showToast({
        type: 'error',
        title: 'Error',
        message: 'Failed to schedule transformation.'
      });
    }
  };

  const handleSkipTransformation = () => {
    // Just close the prompt
  };

  const handleTransformationCreated = (transformationId: string) => {
    showToast({
      type: 'success',
      title: 'Transformation Created',
      message: 'Transformation event has been created successfully.'
    });
    // Refresh the purchase order to show the new transformation
    loadPurchaseOrder();
  };

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'confirmed':
        return 'success';
      case 'pending':
        return 'warning';
      case 'draft':
        return 'neutral';
      case 'cancelled':
        return 'error';
      case 'delivered':
        return 'success';
      default:
        return 'neutral';
    }
  };

  const getDeliveryStatusColor = (status: string | undefined) => {
    switch (status?.toLowerCase()) {
      case 'delivered':
        return 'success';
      case 'in_transit':
        return 'warning'; // Changed from 'info' to 'warning' since 'info' is not a valid BadgeVariant
      case 'failed':
        return 'error';
      case 'pending':
      default:
        return 'warning';
    }
  };

  const getAmendmentStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'approved':
        return 'success';
      case 'pending':
        return 'warning';
      case 'rejected':
        return 'error';
      case 'applied':
        return 'success';
      case 'expired':
        return 'neutral';
      default:
        return 'neutral';
    }
  };

  const canProposeAmendment = () => {
    if (!purchaseOrder || !user) return false;
    return (
      purchaseOrder.status === 'confirmed' &&
      (purchaseOrder.buyer_company.id === user.company?.id || 
       purchaseOrder.seller_company.id === user.company?.id)
    );
  };

  const canConfirmOrder = () => {
    if (!purchaseOrder || !user) return false;
    return (
      purchaseOrder.status === 'pending' &&
      purchaseOrder.seller_company.id === user.company?.id
    );
  };

  const canEditOrder = () => {
    if (!purchaseOrder || !user) return false;
    return (
      (purchaseOrder.status === 'pending' || purchaseOrder.status === 'confirmed') &&
      (purchaseOrder.buyer_company.id === user.company?.id || 
       purchaseOrder.seller_company.id === user.company?.id)
    );
  };

  const canConfirmDelivery = () => {
    if (!purchaseOrder || !user) return false;
    return (
      purchaseOrder.status === 'confirmed' &&
      purchaseOrder.delivery_status === 'pending' &&
      purchaseOrder.buyer_company.id === user.company?.id
    );
  };

  const handleProposeAmendment = () => {
    setShowAmendmentModal(true);
  };

  const handleDeliveryConfirmation = () => {
    setShowDeliveryConfirmationModal(true);
  };

  const handleConfirmDelivery = async (deliveryNotes: string) => {
    if (!id || !purchaseOrder) return;

    try {
      const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
      const authToken = localStorage.getItem('auth_token');
      
      const response = await fetch(`${API_BASE_URL}/api/v1/purchase-orders/${id}/confirm-delivery`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${authToken}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ delivery_notes: deliveryNotes })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to confirm delivery');
      }

      const updatedPO = await response.json();
      
      // Update the local state
      setPurchaseOrder(updatedPO);
      
      // Also reload the purchase order to ensure we have the latest data
      await loadPurchaseOrder();
      
      showToast({
        type: 'success',
        title: 'Delivery Confirmed',
        message: 'The delivery has been confirmed and batch ownership has been transferred.'
      });
      
      setShowDeliveryConfirmationModal(false);
    } catch (error) {
      console.error('Error confirming delivery:', error);
      showToast({
        type: 'error',
        title: 'Delivery Confirmation Failed',
        message: error instanceof Error ? error.message : 'Failed to confirm delivery'
      });
    }
  };

  const handleConfirmOrder = () => {
    setShowConfirmationModal(true);
  };

  const handleEditOrder = () => {
    setShowEditModal(true);
  };

  const handleAmendmentSubmit = async (proposal: ProposeChangesRequest) => {
    if (!id || !purchaseOrder) return;

    try {
      await proposeChanges(id, proposal);

      showToast({
        type: 'success',
        title: 'Amendment Proposed',
        message: 'Your amendment has been submitted for approval.'
      });

      setShowAmendmentModal(false);
      await loadPurchaseOrder(); // Refresh data
    } catch (error: any) {
      showToast({
        type: 'error',
        title: 'Amendment Failed',
        message: error.message || 'Failed to submit amendment. Please try again.'
      });
    }
  };

  const handleConfirmationSubmit = async (confirmation: any) => {
    if (!id || !purchaseOrder) return;

    try {
      // Use enhanced confirmation format with batch selection support
      const enhancedConfirmation: PurchaseOrderConfirmation = {
        delivery_date: confirmation.confirmed_delivery_date || undefined,
        notes: confirmation.seller_notes || undefined,
        confirmed_quantity: confirmation.confirmed_quantity || undefined,
        confirmed_unit: confirmation.confirmed_unit || undefined,
        confirmed_unit_price: confirmation.confirmed_unit_price || undefined,
        delivery_location: confirmation.confirmed_delivery_location || undefined,
        // Add batch selection support
        stock_batches: confirmation.batch_id ? [{
          batch_id: confirmation.batch_id,
          quantity_to_use: confirmation.confirmed_quantity || purchaseOrder.quantity
        }] : undefined
      };

      const response: ConfirmationResponse = await purchaseOrderApi.confirmPurchaseOrder(id, enhancedConfirmation);

      // Update batch allocation if a batch was used
      if (confirmation.batch_id && confirmation.confirmed_quantity) {
        try {
          const { harvestApi } = await import('../services/harvestApi');
          await harvestApi.updateBatchAllocation(confirmation.batch_id, {
            allocated_quantity: confirmation.confirmed_quantity,
            purchase_order_id: id,
            purchase_order_number: purchaseOrder.po_number || `PO-${id.slice(-8)}`,
            buyer_company: purchaseOrder.buyer_company?.name || 'Unknown Buyer'
          });
        } catch (allocationError) {
          console.warn('Failed to update batch allocation:', allocationError);
          // Don't fail the entire confirmation if allocation update fails
        }
      }

      showToast({
        type: 'success',
        title: 'Order Confirmed',
        message: response.message || 'Purchase order has been successfully confirmed.'
      });

      setShowConfirmationModal(false);
      await loadPurchaseOrder();

      // Check if we should show transformation prompt for processor companies
      if (shouldShowTransformationPrompt()) {
        setShowTransformationPrompt(true);
      } // Refresh data
    } catch (error: any) {
      showToast({
        type: 'error',
        title: 'Confirmation Failed',
        message: error.response?.data?.detail || 'Failed to confirm purchase order. Please try again.'
      });
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  if (!purchaseOrder) {
    return (
      <div className="text-center py-12">
        <h2 className="text-xl font-semibold text-neutral-900 mb-2">Purchase Order Not Found</h2>
        <p className="text-neutral-600 mb-4">The purchase order you're looking for doesn't exist.</p>
        <Button onClick={() => navigate('/purchase-orders')}>
          Back to Purchase Orders
        </Button>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <Button
            variant="outline"
            size="sm"
            onClick={() => navigate('/purchase-orders')}
            leftIcon={<ArrowLeftIcon className="h-4 w-4" />}
          >
            Back
          </Button>
          <div>
            <h1 className="text-2xl font-bold text-neutral-900">
              {purchaseOrder.po_number}
            </h1>
            <p className="text-neutral-600">
              {purchaseOrder.buyer_company.name} → {purchaseOrder.seller_company.name}
            </p>
          </div>
        </div>
        
        <div className="flex items-center space-x-3">
          <Badge variant={getStatusColor(purchaseOrder.status)} size="lg">
            {purchaseOrder.status}
          </Badge>
          
          <div className="flex items-center space-x-3">
            <Button variant="outline" size="sm" leftIcon={<PrinterIcon className="h-4 w-4" />}>
              Print
            </Button>
            
            <div className="h-6 w-px bg-gray-300"></div>
            
            <div className="flex space-x-2">
              {canEditOrder() && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleEditOrder}
                  leftIcon={<PencilIcon className="h-4 w-4" />}
                >
                  Edit Order
                </Button>
              )}
              
              {canConfirmOrder() && (
                <Button
                  variant="primary"
                  size="sm"
                  onClick={handleConfirmOrder}
                  leftIcon={<CheckCircleIcon className="h-4 w-4" />}
                >
                  Confirm Order
                </Button>
              )}
              
              {canProposeAmendment() && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleProposeAmendment}
                  leftIcon={<PencilIcon className="h-4 w-4" />}
                >
                  Propose Amendment
                </Button>
              )}
              
              {canConfirmDelivery() && (
                <Button
                  variant="primary"
                  size="sm"
                  onClick={handleDeliveryConfirmation}
                  leftIcon={<CheckCircleIcon className="h-4 w-4" />}
                >
                  Confirm Delivery
                </Button>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-neutral-200">
        <nav className="-mb-px flex space-x-8">
          {[
            { id: 'details', label: 'Order Details', icon: DocumentTextIcon },
            { id: 'amendments', label: 'Amendments', icon: PencilIcon, count: purchaseOrder.amendments?.length || 0 },
            { id: 'history', label: 'History', icon: ClockIcon },
            { id: 'traceability', label: 'Traceability', icon: MapIcon },
            ...(shouldShowTransformationPrompt() ? [{ id: 'transformations', label: 'Transformations', icon: CogIcon }] : []),
          ].map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={cn(
                  'flex items-center space-x-2 py-2 px-1 border-b-2 font-medium text-sm',
                  isActive
                    ? 'border-primary-500 text-primary-600'
                    : 'border-transparent text-neutral-500 hover:text-neutral-700 hover:border-neutral-300'
                )}
              >
                <Icon className="h-4 w-4" />
                <span>{tab.label}</span>
                {tab.count !== undefined && tab.count > 0 && (
                  <Badge variant="neutral" size="sm">{tab.count}</Badge>
                )}
              </button>
            );
          })}
        </nav>
      </div>

      {/* Tab Content */}
      {activeTab === 'details' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Order Information */}
          <Card>
            <CardHeader title="Order Information" />
            <CardBody className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium text-neutral-700">Product</label>
                  <p className="text-neutral-900">{purchaseOrder.product.name}</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-neutral-700">Quantity</label>
                  <p className="text-neutral-900">{purchaseOrder.quantity} {purchaseOrder.unit}</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-neutral-700">Unit Price</label>
                  <p className="text-neutral-900">{formatCurrency(Number(purchaseOrder.unit_price))}</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-neutral-700">Total Amount</label>
                  <p className="text-lg font-semibold text-neutral-900">
                    {formatCurrency(Number(purchaseOrder.total_amount))}
                  </p>
                </div>
                <div>
                  <label className="text-sm font-medium text-neutral-700">Delivery Date</label>
                  <p className="text-neutral-900">{formatDate(purchaseOrder.delivery_date)}</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-neutral-700">Delivery Status</label>
                  <div className="flex items-center space-x-2">
                    <Badge variant={getDeliveryStatusColor(purchaseOrder.delivery_status)} size="sm">
                      {purchaseOrder.delivery_status?.replace('_', ' ').toUpperCase() || 'PENDING'}
                    </Badge>
                    {purchaseOrder.delivered_at && (
                      <span className="text-xs text-neutral-500">
                        {formatDate(purchaseOrder.delivered_at)}
                      </span>
                    )}
                  </div>
                </div>
                <div>
                  <label className="text-sm font-medium text-neutral-700">Created</label>
                  <p className="text-neutral-900">{formatDate(purchaseOrder.created_at)}</p>
                </div>
              </div>
              
              <div>
                <label className="text-sm font-medium text-neutral-700">Delivery Location</label>
                <p className="text-neutral-900">{purchaseOrder.delivery_location}</p>
              </div>
              
              {purchaseOrder.notes && (
                <div>
                  <label className="text-sm font-medium text-neutral-700">Notes</label>
                  <p className="text-neutral-900">{purchaseOrder.notes}</p>
                </div>
              )}
            </CardBody>
          </Card>

          {/* Company Information */}
          <Card>
            <CardHeader title="Companies" />
            <CardBody className="space-y-4">
              <div>
                <label className="text-sm font-medium text-neutral-700">Buyer</label>
                <div className="flex items-center space-x-2 mt-1">
                  <p className="text-neutral-900 font-medium">{purchaseOrder.buyer_company.name}</p>
                  <Badge variant="neutral" size="sm">{purchaseOrder.buyer_company.company_type}</Badge>
                </div>
              </div>
              
              <div>
                <label className="text-sm font-medium text-neutral-700">Seller</label>
                <div className="flex items-center space-x-2 mt-1">
                  <p className="text-neutral-900 font-medium">{purchaseOrder.seller_company.name}</p>
                  <Badge variant="neutral" size="sm">{purchaseOrder.seller_company.company_type}</Badge>
                </div>
              </div>
            </CardBody>
          </Card>
        </div>
      )}

      {activeTab === 'amendments' && (
        <div className="space-y-4">
          {purchaseOrder.amendments && purchaseOrder.amendments.length > 0 ? (
            purchaseOrder.amendments.map((amendment) => (
              <Card key={amendment.id}>
                <CardBody>
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-2 mb-2">
                        <h3 className="font-medium text-neutral-900">{amendment.amendment_number}</h3>
                        <Badge variant={getAmendmentStatusColor(amendment.status)} size="sm">
                          {amendment.status}
                        </Badge>
                        <Badge variant="neutral" size="sm">{amendment.priority}</Badge>
                      </div>
                      <p className="text-sm text-neutral-600 mb-2">{amendment.reason}</p>
                      <p className="text-xs text-neutral-500">
                        Proposed {formatDate(amendment.proposed_at)}
                      </p>
                    </div>
                    
                    {amendment.status === 'pending' && user?.company?.id === amendment.requires_approval_from_company_id && (
                      <div className="flex space-x-2 ml-4">
                        <Button variant="outline" size="sm" leftIcon={<XCircleIcon className="h-4 w-4" />}>
                          Reject
                        </Button>
                        <Button variant="primary" size="sm" leftIcon={<CheckCircleIcon className="h-4 w-4" />}>
                          Approve
                        </Button>
                      </div>
                    )}
                  </div>
                </CardBody>
              </Card>
            ))
          ) : (
            <div className="text-center py-12">
              <PencilIcon className="h-12 w-12 mx-auto text-neutral-400 mb-4" />
              <h3 className="text-lg font-medium text-neutral-900 mb-2">No Amendments</h3>
              <p className="text-neutral-600 mb-4">This purchase order has no amendments yet.</p>
              {canProposeAmendment() && (
                <Button onClick={handleProposeAmendment} leftIcon={<PencilIcon className="h-4 w-4" />}>
                  Propose Amendment
                </Button>
              )}
            </div>
          )}
        </div>
      )}

      {activeTab === 'history' && (
        <Card>
          <CardHeader title="Order History" />
          <CardBody>
            <div className="space-y-4">
              <div className="flex items-start space-x-3">
                <div className="flex-shrink-0 w-2 h-2 bg-primary-600 rounded-full mt-2"></div>
                <div>
                  <p className="font-medium text-neutral-900">Order Created</p>
                  <p className="text-sm text-neutral-600">{formatDate(purchaseOrder.created_at)}</p>
                </div>
              </div>
              
              {purchaseOrder.status === 'confirmed' && (
                <div className="flex items-start space-x-3">
                  <div className="flex-shrink-0 w-2 h-2 bg-success-600 rounded-full mt-2"></div>
                  <div>
                    <p className="font-medium text-neutral-900">Order Confirmed</p>
                    <p className="text-sm text-neutral-600">Confirmed by seller</p>
                  </div>
                </div>
              )}
            </div>
          </CardBody>
        </Card>
      )}

      {activeTab === 'traceability' && (
        <PurchaseOrderTraceability
          poId={id!}
          poNumber={purchaseOrder.po_number}
        />
      )}

      {activeTab === 'transformations' && (
        <PurchaseOrderTransformations
          purchaseOrderId={id!}
          purchaseOrder={purchaseOrder}
          onOpenTransformationWizard={() => setShowTransformationWizard(true)}
        />
      )}

      {/* Modals */}
      {showAmendmentModal && (
        <ProposeChangesModal
          isOpen={showAmendmentModal}
          onClose={() => setShowAmendmentModal(false)}
          purchaseOrder={purchaseOrder}
          onPropose={handleAmendmentSubmit}
        />
      )}

      {showConfirmationModal && (
        <ConfirmationModal
          isOpen={showConfirmationModal}
          onClose={() => setShowConfirmationModal(false)}
          purchaseOrder={purchaseOrder}
          onSubmit={handleConfirmationSubmit}
        />
      )}

      {showEditModal && (
        <EditPurchaseOrderModal
          isOpen={showEditModal}
          onClose={() => setShowEditModal(false)}
          po={purchaseOrder}
          onEdit={async (editData) => {
            try {
              // Use the direct update API for immediate changes
              const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
              const authToken = localStorage.getItem('auth_token');
              
              const response = await fetch(`${API_BASE_URL}/api/v1/purchase-orders/${id}`, {
                method: 'PUT',
                headers: {
                  'Authorization': `Bearer ${authToken}`,
                  'Content-Type': 'application/json'
                },
                body: JSON.stringify(editData)
              });

              if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to update purchase order');
              }

              const updatedPO = await response.json();
              
              // Update the local state
              setPurchaseOrder(updatedPO);
              
              // Also reload the purchase order to ensure we have the latest data
              await loadPurchaseOrder();
              
              showToast({
                type: 'success',
                title: 'Purchase Order Updated',
                message: 'The purchase order has been updated successfully.'
              });
              
              setShowEditModal(false);
            } catch (error) {
              console.error('Error updating purchase order:', error);
              showToast({
                type: 'error',
                title: 'Update Failed',
                message: error instanceof Error ? error.message : 'Failed to update purchase order'
              });
            }
          }}
        />
      )}

      {showDeliveryConfirmationModal && (
        <DeliveryConfirmationModal
          isOpen={showDeliveryConfirmationModal}
          onClose={() => setShowDeliveryConfirmationModal(false)}
          purchaseOrder={purchaseOrder}
          onConfirm={handleConfirmDelivery}
        />
      )}

      {/* Transformation Prompt */}
      {showTransformationPrompt && purchaseOrder && (
        <TransformationPrompt
          isOpen={showTransformationPrompt}
          onClose={() => setShowTransformationPrompt(false)}
          purchaseOrder={purchaseOrder}
          inputBatch={{
            id: 'temp-batch-id',
            batch_id: `BATCH-${purchaseOrder.id.slice(-8)}`,
            quantity: purchaseOrder.quantity,
            unit: purchaseOrder.unit
          }}
          onCreateNow={handleCreateTransformationNow}
          onScheduleLater={handleScheduleTransformationLater}
          onSkip={handleSkipTransformation}
        />
      )}

      {/* Transformation Wizard */}
      {showTransformationWizard && purchaseOrder && (
        <TransformationWizard
          isOpen={showTransformationWizard}
          onClose={() => setShowTransformationWizard(false)}
          purchaseOrder={purchaseOrder}
          inputBatch={{
            id: 'temp-batch-id',
            batch_id: `BATCH-${purchaseOrder.id.slice(-8)}`,
            quantity: purchaseOrder.quantity,
            unit: purchaseOrder.unit
          }}
          onTransformationCreated={handleTransformationCreated}
        />
      )}
    </div>
  );
};

export default PurchaseOrderDetailPage;
