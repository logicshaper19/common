import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardBody } from '../components/ui/Card';
import Button from '../components/ui/Button';
import Input from '../components/ui/Input';
import Select from '../components/ui/Select';
import LoadingSpinner from '../components/ui/LoadingSpinner';
import AnalyticsCard from '../components/ui/AnalyticsCard';
import PurchaseOrderTable from '../components/purchase-orders/PurchaseOrderTable';
import CreatePurchaseOrderModal from '../components/purchase-orders/CreatePurchaseOrderModal';
import {
  MagnifyingGlassIcon,
  FunnelIcon,
  PlusIcon,
  DocumentTextIcon,
  ClockIcon,
  CheckCircleIcon,
  TruckIcon,
  ExclamationTriangleIcon
} from '@heroicons/react/24/outline';
import {
  purchaseOrderApi,
  PurchaseOrderWithDetails,
  PurchaseOrderFilters,
  PurchaseOrderCreate,
  ProposeChangesRequest,
  ApproveChangesRequest
} from '../services/purchaseOrderApi';
import { useAmendments } from '../hooks/useAmendments';
import { useAuth } from '../contexts/AuthContext';
import { useToast } from '../contexts/ToastContext';

export const PurchaseOrdersPage: React.FC = () => {
  const { user } = useAuth();
  const { showToast } = useToast();
  const { proposeChanges: proposeChangesHook, approveChanges: approveChangesHook } = useAmendments();

  // Wrapper functions to handle the return values
  const handleProposeChanges = async (id: string, proposal: ProposeChangesRequest): Promise<void> => {
    await proposeChangesHook(id, proposal);
  };

  const handleApproveChanges = async (id: string, approval: ApproveChangesRequest): Promise<void> => {
    await approveChangesHook(id, approval);
  };
  
  const [purchaseOrders, setPurchaseOrders] = useState<PurchaseOrderWithDetails[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filters, setFilters] = useState<PurchaseOrderFilters>({
    page: 1,
    per_page: 20
  });
  const [showFilters, setShowFilters] = useState(false);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [isCreating, setIsCreating] = useState(false);

  // Calculate analytics from purchase orders
  const analytics = React.useMemo(() => {
    const total = purchaseOrders.length;
    const pending = purchaseOrders.filter(po => po.status === 'PENDING').length;
    const confirmed = purchaseOrders.filter(po => po.status === 'CONFIRMED').length;
    const delivered = purchaseOrders.filter(po => po.status === 'DELIVERED').length;
    const cancelled = purchaseOrders.filter(po => po.status === 'CANCELLED').length;

    // Calculate total value
    const totalValue = purchaseOrders.reduce((sum, po) => {
      return sum + (po.total_amount || 0);
    }, 0);

    // Calculate amendments
    const withAmendments = purchaseOrders.filter(po =>
      po.amendments && po.amendments.length > 0
    ).length;

    return [
      {
        name: 'Total Orders',
        value: total.toString(),
        change: '+8%',
        changeType: 'increase' as const,
        icon: DocumentTextIcon,
      },
      {
        name: 'Pending',
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
        name: 'Delivered',
        value: delivered.toString(),
        change: delivered > 0 ? `${Math.round((delivered / total) * 100)}%` : '0%',
        changeType: 'increase' as const,
        icon: TruckIcon,
      },
    ];
  }, [purchaseOrders]);

  // Calculate pending amendments for alerts
  const pendingAmendments = purchaseOrders.filter(po =>
    po.amendments?.some(amendment =>
      amendment.status === 'pending' &&
      amendment.proposed_by_user_id !== user?.id
    )
  );

  const myProposedAmendments = purchaseOrders.filter(po =>
    po.amendments?.some(amendment =>
      amendment.status === 'pending' &&
      amendment.proposed_by_user_id === user?.id
    )
  );

  // Load purchase orders
  const loadPurchaseOrders = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      const response = await purchaseOrderApi.getPurchaseOrders(filters);
      setPurchaseOrders(response.purchase_orders);
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || 'Failed to load purchase orders';
      setError(errorMessage);
      showToast({ type: 'error', title: errorMessage });
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadPurchaseOrders();
  }, [filters]);

  const handleFilterChange = (field: keyof PurchaseOrderFilters, value: string) => {
    setFilters(prev => ({
      ...prev,
      [field]: value || undefined,
      page: 1 // Reset to first page when filtering
    }));
  };

  const handleSearch = (searchTerm: string) => {
    setFilters(prev => ({
      ...prev,
      search: searchTerm || undefined,
      page: 1
    }));
  };

  const clearFilters = () => {
    setFilters({
      page: 1,
      per_page: 20
    });
  };

  // Handle purchase order creation
  const handleCreatePurchaseOrder = async (data: PurchaseOrderCreate) => {
    setIsCreating(true);
    try {
      await purchaseOrderApi.createPurchaseOrder(data);
      await loadPurchaseOrders(); // Refresh the list
      showToast({ type: 'success', title: 'Purchase order created successfully' });
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || 'Failed to create purchase order';
      showToast({ type: 'error', title: errorMessage });
      throw error; // Re-throw so the modal can handle it
    } finally {
      setIsCreating(false);
    }
  };



  if (isLoading && purchaseOrders.length === 0) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Purchase Orders</h1>
            <p className="mt-2 text-gray-600">
              Manage your purchase orders and amendments
            </p>
          </div>
          <Button
            variant="primary"
            onClick={() => setShowCreateModal(true)}
          >
            <PlusIcon className="h-5 w-5 mr-2" />
            Create Purchase Order
          </Button>
        </div>
      </div>

      {/* Analytics Cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4 mb-8">
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

      {/* Amendment Alerts */}
      {(pendingAmendments.length > 0 || myProposedAmendments.length > 0) && (
        <div className="mb-6 space-y-4">
          {pendingAmendments.length > 0 && (
            <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
              <h3 className="text-sm font-medium text-amber-800">
                {pendingAmendments.length} Amendment{pendingAmendments.length > 1 ? 's' : ''} Awaiting Your Review
              </h3>
              <p className="text-sm text-amber-700 mt-1">
                You have amendment proposals that need your approval or rejection.
              </p>
            </div>
          )}
          
          {myProposedAmendments.length > 0 && (
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <h3 className="text-sm font-medium text-blue-800">
                {myProposedAmendments.length} Amendment{myProposedAmendments.length > 1 ? 's' : ''} Pending Buyer Review
              </h3>
              <p className="text-sm text-blue-700 mt-1">
                Your amendment proposals are waiting for buyer approval.
              </p>
            </div>
          )}
        </div>
      )}

      {/* Search and Filters */}
      <Card className="mb-6">
        <CardBody>
          <div className="space-y-4">
            {/* Search Bar */}
            <div className="flex items-center space-x-4">
              <div className="flex-1">
                <div className="relative">
                  <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
                  <Input
                    type="text"
                    placeholder="Search by PO number, company, or product..."
                    className="pl-10"
                    onChange={(e) => handleSearch(e.target.value)}
                    value={filters.search || ''}
                  />
                </div>
              </div>
              <Button
                variant="secondary"
                onClick={() => setShowFilters(!showFilters)}
              >
                <FunnelIcon className="h-5 w-5 mr-2" />
                Filters
              </Button>
            </div>

            {/* Advanced Filters */}
            {showFilters && (
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4 pt-4 border-t">
                <Select
                  label="Status"
                  value={filters.status || ''}
                  onChange={(e) => handleFilterChange('status', e.target.value)}
                  options={[
                    { label: 'All Statuses', value: '' },
                    { label: 'Pending', value: 'PENDING' },
                    { label: 'Confirmed', value: 'CONFIRMED' },
                    { label: 'Delivered', value: 'DELIVERED' },
                    { label: 'Cancelled', value: 'CANCELLED' }
                  ]}
                />

                <Input
                  label="Delivery Date From"
                  type="date"
                  value={filters.delivery_date_from || ''}
                  onChange={(e) => handleFilterChange('delivery_date_from', e.target.value)}
                />

                <Input
                  label="Delivery Date To"
                  type="date"
                  value={filters.delivery_date_to || ''}
                  onChange={(e) => handleFilterChange('delivery_date_to', e.target.value)}
                />

                <div className="flex items-end">
                  <Button
                    variant="secondary"
                    onClick={clearFilters}
                    className="w-full"
                  >
                    Clear Filters
                  </Button>
                </div>
              </div>
            )}
          </div>
        </CardBody>
      </Card>

      {/* Purchase Orders List */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
          <p className="text-red-800">{error}</p>
          <Button
            variant="secondary"
            size="sm"
            onClick={loadPurchaseOrders}
            className="mt-2"
          >
            Retry
          </Button>
        </div>
      )}

      {purchaseOrders.length === 0 && !isLoading ? (
        <Card>
          <CardBody className="text-center py-12">
            <p className="text-gray-500 text-lg">No purchase orders found</p>
            <p className="text-gray-400 mt-2">
              {filters.search || filters.status 
                ? 'Try adjusting your search or filters'
                : 'Create your first purchase order to get started'
              }
            </p>
          </CardBody>
        </Card>
      ) : (
        <div className="space-y-6">
          {/* Priority Section: Pending Amendments */}
          {pendingAmendments.length > 0 && (
            <div>
              <h2 className="text-xl font-semibold text-gray-900 mb-4">
                🚨 Amendments Awaiting Your Review
              </h2>
              <PurchaseOrderTable
                purchaseOrders={pendingAmendments}
                onProposeChanges={handleProposeChanges}
                onApproveChanges={handleApproveChanges}
                onRefresh={loadPurchaseOrders}
                showAmendmentSection={true}
              />
            </div>
          )}

          {/* All Purchase Orders */}
          <div>
            <h2 className="text-xl font-semibold text-gray-900 mb-4">
              All Purchase Orders
            </h2>
            <PurchaseOrderTable
              purchaseOrders={purchaseOrders}
              onProposeChanges={handleProposeChanges}
              onApproveChanges={handleApproveChanges}
              onRefresh={loadPurchaseOrders}
              loading={isLoading}
            />
          </div>

          {/* Loading indicator for pagination */}
          {isLoading && (
            <div className="flex justify-center py-4">
              <LoadingSpinner />
            </div>
          )}
        </div>
      )}

      {/* Create Purchase Order Modal */}
      <CreatePurchaseOrderModal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        onCreate={handleCreatePurchaseOrder}
        isLoading={isCreating}
      />
    </div>
  );
};

export default PurchaseOrdersPage;
