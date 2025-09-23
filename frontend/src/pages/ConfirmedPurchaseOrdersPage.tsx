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
  CheckCircleIcon, 
  CalendarIcon, 
  TruckIcon
} from '@heroicons/react/24/outline';

const ConfirmedPurchaseOrdersPage: React.FC = () => {
  const { showToast } = useToast();
  const [purchaseOrders, setPurchaseOrders] = useState<PurchaseOrderWithRelations[]>([]);
  const [loading, setLoading] = useState(true);

  // Calculate analytics from confirmed purchase orders
  const analytics = React.useMemo(() => {
    const total = purchaseOrders.length;
    const thisMonth = purchaseOrders.filter(po => {
      const confirmedDate = new Date(po.updated_at || po.created_at);
      const now = new Date();
      return confirmedDate.getMonth() === now.getMonth() && 
             confirmedDate.getFullYear() === now.getFullYear();
    }).length;
    
    const totalValue = purchaseOrders.reduce((sum, po) => {
      return sum + (po.quantity * po.unit_price || 0);
    }, 0);

    const avgDeliveryTime = purchaseOrders.reduce((sum, po) => {
      if (!po.delivery_date || !po.updated_at) return sum;
      const deliveryDate = new Date(po.delivery_date);
      const confirmedDate = new Date(po.updated_at);
      const daysToDelivery = Math.ceil((deliveryDate.getTime() - confirmedDate.getTime()) / (1000 * 60 * 60 * 24));
      return sum + Math.max(0, daysToDelivery);
    }, 0) / Math.max(1, purchaseOrders.length);

    return [
      {
        name: 'Total Confirmed',
        value: total.toString(),
        change: '+8%',
        changeType: 'increase' as const,
        icon: CheckCircleIcon,
      },
      {
        name: 'This Month',
        value: thisMonth.toString(),
        change: thisMonth > 0 ? `${Math.round((thisMonth / total) * 100)}%` : '0%',
        changeType: thisMonth > total * 0.2 ? 'increase' as const : 'neutral' as const,
        icon: CalendarIcon,
      },
      {
        name: 'Total Value',
        value: `$${totalValue.toLocaleString(undefined, { maximumFractionDigits: 0 })}`,
        change: '+15%',
        changeType: 'increase' as const,
        icon: DocumentTextIcon,
      },
      {
        name: 'Avg Delivery Time',
        value: `${Math.round(avgDeliveryTime)} days`,
        change: avgDeliveryTime < 14 ? 'Good' : 'Monitor',
        changeType: avgDeliveryTime < 14 ? 'decrease' as const : 'increase' as const,
        icon: TruckIcon,
      },
    ];
  }, [purchaseOrders]);

  // Load confirmed purchase orders
  const loadPurchaseOrders = useCallback(async () => {
    try {
      setLoading(true);
      const response = await purchaseOrderApi.getPurchaseOrders({
        status: 'confirmed',
        per_page: 100
      });
      
      setPurchaseOrders(response.purchase_orders || []);
    } catch (error) {
      console.error('Error loading confirmed purchase orders:', error);
      showToast({
        type: 'error',
        title: 'Error',
        message: 'Failed to load confirmed purchase orders'
      });
    } finally {
      setLoading(false);
    }
  }, [showToast]);

  // Load data on component mount
  useEffect(() => {
    loadPurchaseOrders();
  }, [loadPurchaseOrders]);

  // Handle refresh
  const handleRefresh = () => {
    loadPurchaseOrders();
  };


  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Confirmed Purchase Orders</h1>
          <p className="text-gray-600">View all confirmed purchase orders and their details</p>
        </div>
        <Button
          onClick={handleRefresh}
          variant="outline"
          disabled={loading}
        >
          <ArrowPathIcon className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </Button>
      </div>

      {/* Analytics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {analytics.map((metric, index) => (
          <AnalyticsCard
            key={index}
            title={metric.name}
            value={metric.value}
            change={metric.change}
            changeType={metric.changeType}
            icon={metric.icon}
          />
        ))}
      </div>

      {/* Purchase Orders Table */}
      <Card>
        <CardHeader 
          title="Confirmed Purchase Orders" 
          subtitle={`${purchaseOrders.length} confirmed orders`}
        />
        <CardBody>
          <PurchaseOrderTable
            purchaseOrders={purchaseOrders}
            loading={loading}
            onRefresh={handleRefresh}
          />
        </CardBody>
      </Card>
    </div>
  );
};

export default ConfirmedPurchaseOrdersPage;
