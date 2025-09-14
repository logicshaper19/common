/**
 * Outgoing Orders Card - Pillar 2 of Four-Pillar Dashboard
 * Shows purchase orders where the current company is the buyer
 */
import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { 
  ArrowUpTrayIcon,
  ClockIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  EyeIcon,
  PlusIcon,
  ShoppingCartIcon
} from '@heroicons/react/24/outline';
import { Card, CardHeader, CardBody } from '../../ui/Card';
import { Button } from '../../ui/Button';
import { Badge } from '../../ui/Badge';
import LoadingSpinner from '../../ui/LoadingSpinner';
import { purchaseOrderApi, PurchaseOrderWithRelations } from '../../../services/purchaseOrderApi';
import { useAuth } from '../../../contexts/AuthContext';
import { useToast } from '../../../contexts/ToastContext';
import { formatDate, formatCurrency } from '../../../lib/utils';
import { STATUS_CONFIGS } from './constants';

interface OutgoingOrdersCardProps {
  className?: string;
  maxItems?: number;
}

const OutgoingOrdersCard: React.FC<OutgoingOrdersCardProps> = ({ 
  className = '',
  maxItems = 5 
}) => {
  const { user } = useAuth();
  const { showToast } = useToast();
  const [outgoingOrders, setOutgoingOrders] = useState<PurchaseOrderWithRelations[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadOutgoingOrders = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await purchaseOrderApi.getPurchaseOrders({
        buyer_company_id: user?.company?.id
      });
      setOutgoingOrders(response.purchase_orders.slice(0, maxItems));
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || 'Failed to load outgoing orders';
      setError(errorMessage);
      showToast({ type: 'error', title: errorMessage });
    } finally {
      setLoading(false);
    }
  }, [user?.company?.id, maxItems, showToast]);

  useEffect(() => {
    loadOutgoingOrders();
  }, [loadOutgoingOrders]);

  const getStatusBadge = (status: string) => {
    const config = STATUS_CONFIGS.PO_STATUS[status as keyof typeof STATUS_CONFIGS.PO_STATUS] || { variant: 'neutral' as const, label: status };
    return <Badge variant={config.variant}>{config.label}</Badge>;
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'draft':
        return <ClockIcon className="h-4 w-4 text-neutral-600" />;
      case 'pending':
        return <ClockIcon className="h-4 w-4 text-warning-600" />;
      case 'confirmed':
        return <CheckCircleIcon className="h-4 w-4 text-success-600" />;
      case 'in_transit':
        return <ArrowUpTrayIcon className="h-4 w-4 text-primary-600" />;
      case 'delivered':
        return <CheckCircleIcon className="h-4 w-4 text-success-600" />;
      case 'cancelled':
        return <ExclamationTriangleIcon className="h-4 w-4 text-error-600" />;
      default:
        return <ClockIcon className="h-4 w-4 text-neutral-600" />;
    }
  };

  const pendingCount = useMemo(() => 
    outgoingOrders.filter(order => order.status === 'pending').length,
    [outgoingOrders]
  );
  
  const draftCount = useMemo(() => 
    outgoingOrders.filter(order => order.status === 'draft').length,
    [outgoingOrders]
  );
  
  const totalValue = useMemo(() => 
    outgoingOrders.reduce((sum, order) => sum + order.total_amount, 0),
    [outgoingOrders]
  );

  const handleCreatePO = () => {
    // This would open the create PO modal/page
    showToast({ type: 'info', title: 'Opening create purchase order form...' });
  };

  if (loading) {
    return (
      <Card className={className}>
        <CardHeader title="Outgoing Orders" />
        <CardBody>
          <div className="flex items-center justify-center h-32">
            <LoadingSpinner size="md" />
            <span className="ml-2 text-neutral-600">Loading orders...</span>
          </div>
        </CardBody>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className={className}>
        <CardHeader title="Outgoing Orders" />
        <CardBody>
          <div className="text-center py-8">
            <ExclamationTriangleIcon className="h-12 w-12 text-error-600 mx-auto mb-4" />
            <p className="text-error-600 mb-4">{error}</p>
            <Button onClick={loadOutgoingOrders} variant="outline">
              Try Again
            </Button>
          </div>
        </CardBody>
      </Card>
    );
  }

  return (
    <Card className={className}>
      <CardHeader 
        title="Outgoing Orders"
        subtitle={`Orders where you are the buyer • Total value: ${formatCurrency(totalValue)}`}
        action={
          <div className="flex items-center space-x-2">
            <Badge variant="primary">{outgoingOrders.length}</Badge>
            {pendingCount > 0 && (
              <Badge variant="warning">{pendingCount} pending</Badge>
            )}
            {draftCount > 0 && (
              <Badge variant="neutral">{draftCount} draft</Badge>
            )}
          </div>
        }
      />
      <CardBody>
        {outgoingOrders.length === 0 ? (
          <div className="text-center py-8">
            <ShoppingCartIcon className="h-12 w-12 text-neutral-400 mx-auto mb-4" />
            <p className="text-neutral-500 mb-4">No outgoing orders found</p>
            <p className="text-sm text-neutral-400 mb-4">
              Create purchase orders to buy products from suppliers.
            </p>
            <Button onClick={handleCreatePO} leftIcon={<PlusIcon className="h-4 w-4" />}>
              Create Purchase Order
            </Button>
          </div>
        ) : (
          <div className="space-y-4">
            {outgoingOrders.map((order) => (
              <div key={order.id} className="border rounded-lg p-4 hover:bg-neutral-50 transition-colors">
                <div className="flex items-start justify-between">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center space-x-2 mb-2">
                      {getStatusIcon(order.status)}
                      <span className="font-medium text-neutral-900">{order.po_number}</span>
                      {getStatusBadge(order.status)}
                    </div>
                    <p className="text-sm text-neutral-600 mb-1">
                      <span className="font-medium">{order.seller_company?.name || 'Unknown Company'}</span>
                    </p>
                    <p className="text-sm text-neutral-500 mb-2">
                      {order.product?.name || 'Unknown Product'} • {order.quantity} {order.unit}
                    </p>
                    <div className="flex items-center justify-between text-xs text-neutral-500">
                      <span>Delivery: {formatDate(order.delivery_date)}</span>
                      <span className="font-medium">{formatCurrency(order.total_amount)}</span>
                    </div>
                  </div>
                  <div className="flex items-center space-x-1 ml-4">
                    <Button size="sm" variant="outline">
                      <EyeIcon className="h-4 w-4" />
                    </Button>
                    {order.status === 'draft' && (
                      <Button size="sm" variant="outline">
                        Edit
                      </Button>
                    )}
                  </div>
                </div>
              </div>
            ))}
            
            <div className="flex space-x-2 pt-4">
              <Button variant="outline" className="flex-1">
                View All Outgoing Orders
              </Button>
              <Button onClick={handleCreatePO} leftIcon={<PlusIcon className="h-4 w-4" />}>
                New Order
              </Button>
            </div>
          </div>
        )}
      </CardBody>
    </Card>
  );
};

export default OutgoingOrdersCard;