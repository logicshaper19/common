import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardBody } from '../components/ui/Card';
import Button from '../components/ui/Button';
import { 
  PlusIcon, 
  LinkIcon, 
  CheckCircleIcon, 
  ClockIcon,
  ArrowRightIcon,
  ArrowLeftIcon
} from '@heroicons/react/24/outline';
import { PurchaseOrderWithRelations, purchaseOrderApi } from '../services/purchaseOrderApi';
import { useAuth } from '../contexts/AuthContext';
import { useToast } from '../contexts/ToastContext';
import { CreatePurchaseOrderModal } from '../components/purchase-orders/CreatePurchaseOrderModal';
import { FulfillmentModal } from '../components/purchase-orders/FulfillmentModal';

interface FulfillmentHubPageProps {}

export const FulfillmentHubPage: React.FC<FulfillmentHubPageProps> = () => {
  const { user } = useAuth();
  const { showToast } = useToast();
  
  // State
  const [incomingPOs, setIncomingPOs] = useState<PurchaseOrderWithRelations[]>([]);
  const [outgoingPOs, setOutgoingPOs] = useState<PurchaseOrderWithRelations[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showFulfillmentModal, setShowFulfillmentModal] = useState(false);
  const [selectedPO, setSelectedPO] = useState<PurchaseOrderWithRelations | null>(null);

  // Load data on component mount
  useEffect(() => {
    loadFulfillmentData();
  }, []);

  const loadFulfillmentData = async () => {
    setLoading(true);
    try {
      console.log('🔄 Loading fulfillment data...');
      
      // Load incoming POs (where current user's company is the seller)
      const incomingResponse = await purchaseOrderApi.getIncomingPurchaseOrders();
      
      // Load outgoing POs (where current user's company is the buyer)
      const outgoingResponse = await purchaseOrderApi.getPurchaseOrders({
        buyer_company_id: user?.company?.id,
        status: 'confirmed'
      });
      
      console.log('📥 Incoming POs:', incomingResponse);
      console.log('📤 Outgoing POs:', outgoingResponse.purchase_orders);
      
      setIncomingPOs(incomingResponse);
      setOutgoingPOs(outgoingResponse.purchase_orders || []);
      
    } catch (error: any) {
      console.error('❌ Error loading fulfillment data:', error);
      showToast({ 
        type: 'error', 
        title: 'Failed to load fulfillment data',
        message: error.response?.data?.detail || error.message
      });
    } finally {
      setLoading(false);
    }
  };

  const handleCreatePO = async (poData: any) => {
    try {
      await purchaseOrderApi.createPurchaseOrder(poData);
      showToast({ type: 'success', title: 'Purchase order created successfully' });
      setShowCreateModal(false);
      loadFulfillmentData(); // Refresh data
    } catch (error: any) {
      console.error('Error creating purchase order:', error);
      showToast({ type: 'error', title: 'Failed to create purchase order' });
    }
  };

  const handleFulfillPO = (po: PurchaseOrderWithRelations) => {
    setSelectedPO(po);
    setShowFulfillmentModal(true);
  };

  const handleLinkToParent = (po: PurchaseOrderWithRelations) => {
    // Open create modal with this PO pre-selected as parent
    setShowCreateModal(true);
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'confirmed':
        return <CheckCircleIcon className="h-5 w-5 text-green-500" />;
      case 'pending':
        return <ClockIcon className="h-5 w-5 text-yellow-500" />;
      default:
        return <ClockIcon className="h-5 w-5 text-gray-500" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'confirmed':
        return 'bg-green-100 text-green-800';
      case 'pending':
        return 'bg-yellow-100 text-yellow-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 py-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
            <span className="ml-3 text-lg text-gray-600">Loading fulfillment data...</span>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Fulfillment Hub</h1>
          <p className="mt-2 text-gray-600">
            Manage your incoming and outgoing purchase orders, and create commercial chain links
          </p>
        </div>

        {/* Action Buttons */}
        <div className="mb-6 flex space-x-4">
          <Button
            onClick={() => setShowCreateModal(true)}
            className="flex items-center space-x-2"
          >
            <PlusIcon className="h-5 w-5" />
            <span>Create New PO</span>
          </Button>
          <Button
            onClick={loadFulfillmentData}
            variant="outline"
            className="flex items-center space-x-2"
          >
            <ArrowRightIcon className="h-5 w-5" />
            <span>Refresh Data</span>
          </Button>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Incoming POs (Where you are the seller) */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <h2 className="text-xl font-semibold text-gray-900 flex items-center">
                  <ArrowLeftIcon className="h-6 w-6 text-blue-600 mr-2" />
                  Incoming Purchase Orders
                </h2>
                <span className="bg-blue-100 text-blue-800 text-sm font-medium px-2.5 py-0.5 rounded-full">
                  {incomingPOs.length}
                </span>
              </div>
              <p className="text-sm text-gray-600">
                POs where your company is the seller (fulfill these)
              </p>
            </CardHeader>
            <CardBody>
              {incomingPOs.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  <ClockIcon className="h-12 w-12 mx-auto mb-4 text-gray-300" />
                  <p>No incoming purchase orders</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {incomingPOs.map((po) => (
                    <div key={po.id} className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center space-x-2 mb-2">
                            <h3 className="font-medium text-gray-900">{po.po_number}</h3>
                            <span className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(po.status)}`}>
                              {po.status}
                            </span>
                            {getStatusIcon(po.status)}
                          </div>
                          <p className="text-sm text-gray-600 mb-1">
                            From: <span className="font-medium">{po.buyer_company?.name || 'Unknown'}</span>
                          </p>
                          <p className="text-sm text-gray-600 mb-1">
                            Product: <span className="font-medium">{po.product?.name || 'Unknown'}</span>
                          </p>
                          <p className="text-sm text-gray-600">
                            Quantity: <span className="font-medium">{po.quantity} {po.unit}</span>
                          </p>
                          {po.parent_po_id && (
                            <p className="text-xs text-blue-600 mt-1">
                              🔗 Linked to parent PO
                            </p>
                          )}
                        </div>
                        <div className="flex space-x-2 ml-4">
                          <Button
                            size="sm"
                            onClick={() => handleFulfillPO(po)}
                            className="flex items-center space-x-1"
                          >
                            <CheckCircleIcon className="h-4 w-4" />
                            <span>Fulfill</span>
                          </Button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardBody>
          </Card>

          {/* Outgoing POs (Where you are the buyer) */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <h2 className="text-xl font-semibold text-gray-900 flex items-center">
                  <ArrowRightIcon className="h-6 w-6 text-green-600 mr-2" />
                  Outgoing Purchase Orders
                </h2>
                <span className="bg-green-100 text-green-800 text-sm font-medium px-2.5 py-0.5 rounded-full">
                  {outgoingPOs.length}
                </span>
              </div>
              <p className="text-sm text-gray-600">
                POs where your company is the buyer (create child POs from these)
              </p>
            </CardHeader>
            <CardBody>
              {outgoingPOs.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  <ClockIcon className="h-12 w-12 mx-auto mb-4 text-gray-300" />
                  <p>No outgoing purchase orders</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {outgoingPOs.map((po) => (
                    <div key={po.id} className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center space-x-2 mb-2">
                            <h3 className="font-medium text-gray-900">{po.po_number}</h3>
                            <span className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(po.status)}`}>
                              {po.status}
                            </span>
                            {getStatusIcon(po.status)}
                          </div>
                          <p className="text-sm text-gray-600 mb-1">
                            To: <span className="font-medium">{po.seller_company?.name || 'Unknown'}</span>
                          </p>
                          <p className="text-sm text-gray-600 mb-1">
                            Product: <span className="font-medium">{po.product?.name || 'Unknown'}</span>
                          </p>
                          <p className="text-sm text-gray-600">
                            Quantity: <span className="font-medium">{po.quantity} {po.unit}</span>
                          </p>
                          {po.parent_po_id && (
                            <p className="text-xs text-blue-600 mt-1">
                              🔗 Child of parent PO
                            </p>
                          )}
                        </div>
                        <div className="flex space-x-2 ml-4">
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => handleLinkToParent(po)}
                            className="flex items-center space-x-1"
                          >
                            <LinkIcon className="h-4 w-4" />
                            <span>Create Child</span>
                          </Button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardBody>
          </Card>
        </div>

        {/* Modals */}
        <CreatePurchaseOrderModal
          isOpen={showCreateModal}
          onClose={() => setShowCreateModal(false)}
          onCreate={handleCreatePO}
        />

        <FulfillmentModal
          isOpen={showFulfillmentModal}
          onClose={() => setShowFulfillmentModal(false)}
          po={selectedPO}
          onFulfilled={() => {
            setShowFulfillmentModal(false);
            loadFulfillmentData();
          }}
        />
      </div>
    </div>
  );
};

export default FulfillmentHubPage;
