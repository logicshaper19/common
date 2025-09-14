/**
 * Incoming Orders Card - Pillar 1 of Four-Pillar Dashboard
 * Shows purchase orders where the current company is the seller
 */
import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { 
  ArrowDownTrayIcon,
  ClockIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  EyeIcon
} from '@heroicons/react/24/outline';
import { Card, CardHeader, CardBody } from '../../ui/Card';
import { Button } from '../../ui/Button';
import { Badge } from '../../ui/Badge';
import LoadingSpinner from '../../ui/LoadingSpinner';
import { purchaseOrderApi, PurchaseOrderWithRelations } from '../../../services/purchaseOrderApi';
// Removed unused useAuth import
import { useToast } from '../../../contexts/ToastContext';
import { formatDate, formatCurrency } from '../../../lib/utils';
import { STATUS_CONFIGS } from './constants';

interface IncomingOrdersCardProps {
  className?: string;
  maxItems?: number;
}

const IncomingOrdersCard: React.FC<IncomingOrdersCardProps> = ({ 
  className = '',
  maxItems = 5 
}) => {
  // Removed unused user variable
  const { showToast } = useToast();
  const [incomingOrders, setIncomingOrders] = useState<PurchaseOrderWithRelations[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadIncomingOrders = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const orders = await purchaseOrderApi.getIncomingPurchaseOrders();
      setIncomingOrders(orders.slice(0, maxItems));
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || 'Failed to load incoming orders';
      setError(errorMessage);
      showToast({ type: 'error', title: errorMessage });
    } finally {
      setLoading(false);
    }
  }, [maxItems, showToast]);

  useEffect(() => {
    loadIncomingOrders();
  }, [loadIncomingOrders]);

  const getStatusBadge = (status: string) => {
    const config = STATUS_CONFIGS.PO_STATUS[status as keyof typeof STATUS_CONFIGS.PO_STATUS] || { variant: 'neutral' as const, label: status };
    return <Badge variant={config.variant}>{config.label}</Badge>;
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'pending':
        return <ClockIcon className="h-4 w-4 text-warning-600" />;
      case 'confirmed':
        return <CheckCircleIcon className="h-4 w-4 text-success-600" />;
      case 'in_transit':
        return <ArrowDownTrayIcon className="h-4 w-4 text-primary-600" />;
      case 'delivered':
        return <CheckCircleIcon className="h-4 w-4 text-success-600" />;
      case 'cancelled':
        return <ExclamationTriangleIcon className="h-4 w-4 text-error-600" />;
      default:
        return <ClockIcon className="h-4 w-4 text-neutral-600" />;
    }
  };

  const pendingCount = useMemo(() => 
    incomingOrders.filter(order => order.status === 'pending').length,
    [incomingOrders]
  );
  
  const totalValue = useMemo(() => 
    incomingOrders.reduce((sum, order) => sum + order.total_amount, 0),
    [incomingOrders]
  );

  if (loading) {
    return (
      <Card className={className}>
        <CardHeader title="Incoming Orders" />
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
        <CardHeader title="Incoming Orders" />
        <CardBody>
          <div className="text-center py-8">
            <ExclamationTriangleIcon className="h-12 w-12 text-error-600 mx-auto mb-4" />
            <p className="text-error-600 mb-4">{error}</p>
            <Button onClick={loadIncomingOrders} variant="outline">
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
        title="Incoming Orders"
        subtitle={`Orders where you are the seller • Total value: ${formatCurrency(totalValue)}`}
        action={
          <div className="flex items-center space-x-2">
            <Badge variant="primary">{incomingOrders.length}</Badge>
            {pendingCount > 0 && (
              <Badge variant="warning">{pendingCount} pending</Badge>
            )}
          </div>
        }
      />
      <CardBody>
        {incomingOrders.length === 0 ? (
          <div className="text-center py-8">
            <ArrowDownTrayIcon className="h-12 w-12 text-neutral-400 mx-auto mb-4" />
            <p className="text-neutral-500 mb-4">No incoming orders found</p>
            <p className="text-sm text-neutral-400">
              Orders from buyers will appear here when they create purchase orders with your company as the seller.
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            {incomingOrders.map((order) => (
              <div key={order.id} className="border rounded-lg p-4 hover:bg-neutral-50 transition-colors">
                <div className="flex items-start justify-between">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center space-x-2 mb-2">
                      {getStatusIcon(order.status)}
                      <span className="font-medium text-neutral-900">{order.po_number}</span>
                      {getStatusBadge(order.status)}
                    </div>
                    <p className="text-sm text-neutral-600 mb-1">
                      <span className="font-medium">{order.buyer_company?.name || 'Unknown Company'}</span>
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
                    {order.status === 'pending' && (
                      <Button size="sm" variant="success">
                        <CheckCircleIcon className="h-4 w-4" />
                      </Button>
                    )}
                  </div>
                </div>
              </div>
            ))}
            
            {incomingOrders.length >= maxItems && (
              <div className="text-center pt-4">
                <Button variant="outline" fullWidth>
                  View All Incoming Orders
                </Button>
              </div>
            )}
          </div>
        )}
      </CardBody>
    </Card>
  );
};

export default IncomingOrdersCard;