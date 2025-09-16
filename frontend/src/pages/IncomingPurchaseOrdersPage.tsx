import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardHeader, CardBody } from '../components/ui/Card';
import Button from '../components/ui/Button';
import AnalyticsCard from '../components/ui/AnalyticsCard';
import PurchaseOrderTable from '../components/purchase-orders/PurchaseOrderTable';
import { PurchaseOrderWithRelations, purchaseOrderApi } from '../services/purchaseOrderApi';
import { useToast } from '../contexts/ToastContext';
import { 
  ArrowPathIcon, 
  DocumentTextIcon, 
  ClockIcon, 
  CheckCircleIcon, 
  XCircleIcon,
  ExclamationTriangleIcon
} from '@heroicons/react/24/outline';

const IncomingPurchaseOrdersPage: React.FC = () => {
  const { showToast } = useToast();
  const [purchaseOrders, setPurchaseOrders] = useState<PurchaseOrderWithRelations[]>([]);
  const [loading, setLoading] = useState(true);
  // const [actionLoading, setActionLoading] = useState<string | null>(null); // Not currently used

  // Calculate analytics from purchase orders
  const analytics = React.useMemo(() => {
    const total = purchaseOrders.length;
    const pending = purchaseOrders.filter(po => po.status === 'PENDING' || po.status === 'pending').length;
    const confirmed = purchaseOrders.filter(po => po.status === 'CONFIRMED' || po.status === 'confirmed').length;
    const rejected = purchaseOrders.filter(po => po.status === 'REJECTED' || po.status === 'rejected').length;
    const urgent = purchaseOrders.filter(po => {
      if (!po.delivery_date) return false;
      const deliveryDate = new Date(po.delivery_date);
      const today = new Date();
      const daysUntilDelivery = Math.ceil((deliveryDate.getTime() - today.getTime()) / (1000 * 60 * 60 * 24));
      return daysUntilDelivery <= 7 && daysUntilDelivery >= 0; // Within 7 days
    }).length;

    return [
      {
        name: 'Total Orders',
        value: total.toString(),
        change: '+12%',
        changeType: 'increase' as const,
        icon: DocumentTextIcon,
      },
      {
        name: 'Pending Review',
        value: pending.toString(),
        change: pending > 0 ? `${Math.round((pending / total) * 100)}%` : '0%',
        changeType: pending > total * 0.3 ? 'increase' as const : 'neutral' as const,
        icon: ClockIcon,
      },
      {
        name: 'Confirmed',
        value: confirmed.toString(),
        change: confirmed > 0 ? `${Math.round((confirmed / total) * 100)}%` : '0%',
        changeType: 'increase' as const,
        icon: CheckCircleIcon,
      },
      {
        name: 'Urgent (≤7 days)',
        value: urgent.toString(),
        change: urgent > 0 ? `${Math.round((urgent / total) * 100)}%` : '0%',
        changeType: urgent > 0 ? 'increase' as const : 'neutral' as const,
        icon: ExclamationTriangleIcon,
      },
    ];
  }, [purchaseOrders]);

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

      {/* Analytics Cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {analytics.map((stat) => (
          <AnalyticsCard
            key={stat.name}
            name={stat.name}
            value={stat.value}
            change={stat.change}
            changeType={stat.changeType}
            icon={stat.icon}
          />
        ))}
      </div>

      {/* Urgent Orders Alert */}
      {analytics.find(stat => stat.name === 'Urgent (≤7 days)')?.value !== '0' && (
        <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
          <div className="flex items-center">
            <ExclamationTriangleIcon className="h-5 w-5 text-amber-600 mr-2" />
            <div>
              <h3 className="text-sm font-medium text-amber-800">
                {analytics.find(stat => stat.name === 'Urgent (≤7 days)')?.value} Urgent Order{analytics.find(stat => stat.name === 'Urgent (≤7 days)')?.value !== '1' ? 's' : ''} Require{analytics.find(stat => stat.name === 'Urgent (≤7 days)')?.value === '1' ? 's' : ''} Immediate Attention
              </h3>
              <p className="text-sm text-amber-700 mt-1">
                These orders have delivery dates within 7 days and need your review.
              </p>
            </div>
          </div>
        </div>
      )}

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