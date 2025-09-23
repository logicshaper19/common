/**
 * Inventory Management Card - Pillar 3 of Four-Pillar Dashboard
 * Shows current inventory and stock management
 */
import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { 
  ExclamationTriangleIcon,
  CheckCircleIcon,
  ClockIcon,
  PlusIcon,
  EyeIcon,
  ArchiveBoxIcon
} from '@heroicons/react/24/outline';
import { Card, CardHeader, CardBody } from '../../ui/Card';
import { Button } from '../../ui/Button';
import { Badge } from '../../ui/Badge';
import LoadingSpinner from '../../ui/LoadingSpinner';
import { useAuth } from '../../../contexts/AuthContext';
import { useToast } from '../../../contexts/ToastContext';
import { formatDate, formatCurrency } from '../../../lib/utils';
import { INVENTORY_CONSTANTS, STATUS_CONFIGS } from './constants';

interface Batch {
  id: string;
  batch_id: string;
  quantity: number;
  unit: string;
  production_date: string;
  expiry_date?: string;
  status: string;
  product: {
    name: string;
  };
  location?: string;
  value?: number;
}

interface InventoryManagementCardProps {
  className?: string;
  maxItems?: number;
}

const InventoryManagementCard: React.FC<InventoryManagementCardProps> = ({ 
  className = '',
  maxItems = 5 
}) => {
  const { user } = useAuth();
  const { showToast } = useToast();
  const [inventory, setInventory] = useState<Batch[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadInventory = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      // Using the existing inventory API endpoint
      const response = await fetch(`/api/v1/batches/companies/${user?.company?.id}/inventory`);
      if (!response.ok) throw new Error('Failed to load inventory');
      const data = await response.json();
      setInventory(data.slice(0, maxItems));
    } catch (err: any) {
      const errorMessage = err.message || 'Failed to load inventory';
      setError(errorMessage);
      showToast({ type: 'error', title: errorMessage });
    } finally {
      setLoading(false);
    }
  }, [user?.company?.id, maxItems, showToast]);

  useEffect(() => {
    loadInventory();
  }, [loadInventory]);

  const getStatusBadge = (status: string) => {
    const config = STATUS_CONFIGS.BATCH_STATUS[status as keyof typeof STATUS_CONFIGS.BATCH_STATUS] || { variant: 'neutral' as const, label: status };
    return <Badge variant={config.variant}>{config.label}</Badge>;
  };

  const getStatusIcon = (batch: Batch) => {
    const now = new Date();
    const expiryDate = batch.expiry_date ? new Date(batch.expiry_date) : null;
    const daysUntilExpiry = expiryDate ? Math.ceil((expiryDate.getTime() - now.getTime()) / (1000 * 60 * 60 * 24)) : null;

    if (batch.status === 'expired' || (expiryDate && now > expiryDate)) {
      return <ExclamationTriangleIcon className="h-4 w-4 text-error-600" />;
    }
    if (daysUntilExpiry && daysUntilExpiry <= INVENTORY_CONSTANTS.EXPIRY_WARNING_DAYS) {
      return <ClockIcon className="h-4 w-4 text-warning-600" />;
    }
    if (batch.quantity < INVENTORY_CONSTANTS.LOW_STOCK_THRESHOLD) {
      return <ExclamationTriangleIcon className="h-4 w-4 text-warning-600" />;
    }
    return <CheckCircleIcon className="h-4 w-4 text-success-600" />;
  };

  const getDaysUntilExpiry = (expiryDate?: string) => {
    if (!expiryDate) return null;
    const now = new Date();
    const expiry = new Date(expiryDate);
    return Math.ceil((expiry.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));
  };

  const totalQuantity = useMemo(() => 
    inventory.reduce((sum, batch) => sum + batch.quantity, 0),
    [inventory]
  );
  
  const totalValue = useMemo(() => 
    inventory.reduce((sum, batch) => sum + (batch.value || 0), 0),
    [inventory]
  );
  
  const lowStockCount = useMemo(() => 
    inventory.filter(batch => batch.quantity < INVENTORY_CONSTANTS.LOW_STOCK_THRESHOLD).length,
    [inventory]
  );
  
  const expiringSoonCount = useMemo(() => 
    inventory.filter(batch => {
      const days = getDaysUntilExpiry(batch.expiry_date);
      return days !== null && days <= INVENTORY_CONSTANTS.EXPIRY_WARNING_DAYS && days > 0;
    }).length,
    [inventory]
  );

  if (loading) {
    return (
      <Card className={className}>
        <CardHeader title="Inventory Management" />
        <CardBody>
          <div className="flex items-center justify-center h-32">
            <LoadingSpinner size="md" />
            <span className="ml-2 text-neutral-600">Loading inventory...</span>
          </div>
        </CardBody>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className={className}>
        <CardHeader title="Inventory Management" />
        <CardBody>
          <div className="text-center py-8">
            <ExclamationTriangleIcon className="h-12 w-12 text-error-600 mx-auto mb-4" />
            <p className="text-error-600 mb-4">{error}</p>
            <Button onClick={loadInventory} variant="outline">
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
        title="Inventory Management"
        subtitle={`Current stock: ${totalQuantity.toLocaleString()} units • Value: ${formatCurrency(totalValue)}`}
        action={
          <div className="flex items-center space-x-2">
            <Badge variant="primary">{inventory.length}</Badge>
            {lowStockCount > 0 && (
              <Badge variant="warning">{lowStockCount} low stock</Badge>
            )}
            {expiringSoonCount > 0 && (
              <Badge variant="error">{expiringSoonCount} expiring</Badge>
            )}
          </div>
        }
      />
      <CardBody>
        {inventory.length === 0 ? (
          <div className="text-center py-8">
            <ArchiveBoxIcon className="h-12 w-12 text-neutral-400 mx-auto mb-4" />
            <p className="text-neutral-500 mb-4">No inventory found</p>
            <p className="text-sm text-neutral-400 mb-4">
              Inventory will appear here when you receive products from purchase orders.
            </p>
            <Button leftIcon={<PlusIcon className="h-4 w-4" />}>
              Create Batch
            </Button>
          </div>
        ) : (
          <div className="space-y-4">
            {inventory.map((batch) => {
              const daysUntilExpiry = getDaysUntilExpiry(batch.expiry_date);
              return (
                <div key={batch.id} className="border rounded-lg p-4 hover:bg-neutral-50 transition-colors">
                  <div className="flex items-start justify-between">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center space-x-2 mb-2">
                        {getStatusIcon(batch)}
                        <span className="font-medium text-neutral-900">{batch.batch_id}</span>
                        {getStatusBadge(batch.status)}
                      </div>
                      <p className="text-sm text-neutral-600 mb-1">
                        <span className="font-medium">{batch.product.name}</span>
                      </p>
                      <p className="text-sm text-neutral-500 mb-2">
                        {(batch.quantity || 0).toLocaleString()} {batch.unit || 'N/A'}
                        {batch.location && ` • ${batch.location}`}
                      </p>
                      <div className="flex items-center justify-between text-xs text-neutral-500">
                        <span>Produced: {formatDate(batch.production_date)}</span>
                        {batch.expiry_date && (
                          <span className={daysUntilExpiry && daysUntilExpiry <= INVENTORY_CONSTANTS.EXPIRY_WARNING_DAYS ? 'text-warning-600 font-medium' : ''}>
                            {daysUntilExpiry && daysUntilExpiry > 0 
                              ? `Expires in ${daysUntilExpiry} days`
                              : daysUntilExpiry === 0 
                                ? 'Expires today'
                                : 'Expired'
                            }
                          </span>
                        )}
                        {batch.value && (
                          <span className="font-medium">{formatCurrency(batch.value)}</span>
                        )}
                      </div>
                    </div>
                    <div className="flex items-center space-x-1 ml-4">
                      <Button size="sm" variant="outline">
                        <EyeIcon className="h-4 w-4" />
                      </Button>
                      <Button size="sm" variant="outline">
                        Allocate
                      </Button>
                    </div>
                  </div>
                </div>
              );
            })}
            
            <div className="flex space-x-2 pt-4">
              <Button variant="outline" className="flex-1">
                View All Inventory
              </Button>
              <Button leftIcon={<PlusIcon className="h-4 w-4" />}>
                New Batch
              </Button>
            </div>
          </div>
        )}
      </CardBody>
    </Card>
  );
};

export default InventoryManagementCard;
