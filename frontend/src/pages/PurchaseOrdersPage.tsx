import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardBody } from '../components/ui/Card';
import Button from '../components/ui/Button';
import Input from '../components/ui/Input';
import Select from '../components/ui/Select';
import LoadingSpinner from '../components/ui/LoadingSpinner';
import PurchaseOrderCard from '../components/purchase-orders/PurchaseOrderCard';
import { 
  MagnifyingGlassIcon, 
  FunnelIcon,
  PlusIcon 
} from '@heroicons/react/24/outline';
import {
  purchaseOrderApi,
  PurchaseOrderWithDetails,
  PurchaseOrderFilters,
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

  // Get purchase orders that need attention
  const pendingAmendments = purchaseOrders.filter(po =>
    po.amendment_status === 'proposed' &&
    user?.company?.id === po.buyer_company_id
  );

  const myProposedAmendments = purchaseOrders.filter(po =>
    po.amendment_status === 'proposed' &&
    user?.company?.id === po.seller_company_id
  );

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
          <Button variant="primary">
            <PlusIcon className="h-5 w-5 mr-2" />
            Create Purchase Order
          </Button>
        </div>
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
              <div className="space-y-4">
                {pendingAmendments.map((po) => (
                  <PurchaseOrderCard
                    key={po.id}
                    purchaseOrder={po}
                    onProposeChanges={handleProposeChanges}
                    onApproveChanges={handleApproveChanges}
                    onRefresh={loadPurchaseOrders}
                  />
                ))}
              </div>
            </div>
          )}

          {/* All Purchase Orders */}
          <div>
            <h2 className="text-xl font-semibold text-gray-900 mb-4">
              All Purchase Orders
            </h2>
            <div className="space-y-4">
              {purchaseOrders.map((po) => (
                <PurchaseOrderCard
                  key={po.id}
                  purchaseOrder={po}
                  onProposeChanges={handleProposeChanges}
                  onApproveChanges={handleApproveChanges}
                  onRefresh={loadPurchaseOrders}
                />
              ))}
            </div>
          </div>

          {/* Loading indicator for pagination */}
          {isLoading && (
            <div className="flex justify-center py-4">
              <LoadingSpinner />
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default PurchaseOrdersPage;
