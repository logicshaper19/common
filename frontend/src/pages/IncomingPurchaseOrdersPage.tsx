import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardHeader, CardBody } from '../components/ui/Card';
import Button from '../components/ui/Button';
import PurchaseOrderTable from '../components/purchase-orders/PurchaseOrderTable';
import { PurchaseOrderWithRelations, purchaseOrderApi } from '../services/purchaseOrderApi';
import { useToast } from '../contexts/ToastContext';
import { ArrowPathIcon } from '@heroicons/react/24/outline';

const IncomingPurchaseOrdersPage: React.FC = () => {
  const { showToast } = useToast();
  const [purchaseOrders, setPurchaseOrders] = useState<PurchaseOrderWithRelations[]>([]);
  const [loading, setLoading] = useState(true);
  // const [actionLoading, setActionLoading] = useState<string | null>(null); // Not currently used

  const loadIncomingPOs = useCallback(async () => {
    try {
      setLoading(true);
      const response = await purchaseOrderApi.getIncomingPurchaseOrders();
      setPurchaseOrders(response);
    } catch (error) {
      console.error('Error loading incoming purchase orders:', error);
      showToast({
        type: 'error',
        title: 'Failed to load purchase orders',
        message: 'There was an error loading incoming purchase orders.'
      });
    } finally {
      setLoading(false);
    }
  }, [showToast]);

  useEffect(() => {
    loadIncomingPOs();
  }, [loadIncomingPOs]);

  const handleAccept = async (id: string, acceptanceData: any) => {
    try {
      await purchaseOrderApi.acceptPurchaseOrder(id, acceptanceData);
      showToast({
        type: 'success',
        title: 'Purchase order accepted',
        message: 'The purchase order has been accepted successfully.'
      });
      await loadIncomingPOs(); // Refresh the list
    } catch (error) {
      console.error('Error accepting purchase order:', error);
      showToast({
        type: 'error',
        title: 'Failed to accept purchase order',
        message: 'There was an error accepting the purchase order.'
      });
    }
  };

  const handleReject = async (id: string, rejectionData: any) => {
    try {
      await purchaseOrderApi.rejectPurchaseOrder(id, rejectionData);
      showToast({
        type: 'success',
        title: 'Purchase order rejected',
        message: 'The purchase order has been rejected.'
      });
      await loadIncomingPOs(); // Refresh the list
    } catch (error) {
      console.error('Error rejecting purchase order:', error);
      showToast({
        type: 'error',
        title: 'Failed to reject purchase order',
        message: 'There was an error rejecting the purchase order.'
      });
    }
  };

  const handleEdit = async (id: string, editData: any) => {
    try {
      await purchaseOrderApi.editPurchaseOrder(id, editData);
      showToast({
        type: 'success',
        title: 'Purchase order edited',
        message: 'The purchase order has been edited successfully.'
      });
      await loadIncomingPOs(); // Refresh the list
    } catch (error) {
      console.error('Error editing purchase order:', error);
      showToast({
        type: 'error',
        title: 'Failed to edit purchase order',
        message: 'There was an error editing the purchase order.'
      });
    }
  };

  const handleRefresh = () => {
    loadIncomingPOs();
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
          <div>
          <h1 className="text-2xl font-bold text-gray-900">Incoming Purchase Orders</h1>
          <p className="text-gray-600">
            Manage purchase orders where your company is the seller
          </p>
              </div>
              <Button
                variant="secondary"
          onClick={handleRefresh}
          disabled={loading}
              >
          <ArrowPathIcon className="h-4 w-4 mr-2" />
          Refresh
              </Button>
            </div>

      <Card>
        <CardHeader
          title="Purchase Orders Awaiting Your Action"
          subtitle={`${purchaseOrders.length} purchase order(s) found`}
        />
        <CardBody>
          <PurchaseOrderTable
            purchaseOrders={purchaseOrders}
            onAccept={handleAccept}
            onReject={handleReject}
            onEdit={handleEdit}
            onRefresh={handleRefresh}
            loading={loading}
            showAmendmentSection={true}
          />
        </CardBody>
      </Card>

      {purchaseOrders.length === 0 && !loading && (
        <Card>
          <CardBody>
            <div className="text-center py-8">
              <div className="text-gray-400 mb-4">
                <svg className="mx-auto h-12 w-12" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">No Incoming Purchase Orders</h3>
              <p className="text-gray-600">
                There are currently no purchase orders awaiting your action.
              </p>
            </div>
          </CardBody>
        </Card>
      )}
    </div>
  );
};

export default IncomingPurchaseOrdersPage;