/**
 * Inventory Management Page
 * Single page with comprehensive filtering and grouping
 */
import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useToast } from '../contexts/ToastContext';
import { inventoryApi, InventoryFilters, InventoryResponse, InventorySummary } from '../services/inventoryApi';
import { Card, CardHeader, CardTitle, CardBody } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import Select from '../components/ui/Select';
import Input from '../components/ui/Input';
import Label from '../components/ui/Label';
import { 
  FunnelIcon, 
  AdjustmentsHorizontalIcon,
  ArchiveBoxIcon,
  ChartBarIcon,
  ClockIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon
} from '@heroicons/react/24/outline';

interface FilterState {
  status: string[];
  batch_types: string[];
  product_ids: string[];
  facility_ids: string[];
  production_date_from: string;
  production_date_to: string;
  expiry_warning_days: number | null;
  group_by: string;
  sort_by: string;
  sort_order: string;
}

const InventoryPage: React.FC = () => {
  const { user } = useAuth();
  const { showToast } = useToast();
  
  // State
  const [inventoryData, setInventoryData] = useState<InventoryResponse | null>(null);
  const [summary, setSummary] = useState<InventorySummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showFilters, setShowFilters] = useState(false);
  
  // Filter state
  const [filters, setFilters] = useState<FilterState>({
    status: ['available'],
    batch_types: [],
    product_ids: [],
    facility_ids: [],
    production_date_from: '',
    production_date_to: '',
    expiry_warning_days: null,
    group_by: 'product',
    sort_by: 'production_date',
    sort_order: 'desc'
  });

  // Quick filter presets
  const quickFilters = inventoryApi.getQuickFilters();

  // Load inventory data
  const loadInventoryData = useCallback(async (filterState: FilterState = filters) => {
    setLoading(true);
    setError(null);
    
    try {
      const inventoryFilters: InventoryFilters = {
        ...filterState,
        limit: 100,
        offset: 0
      };
      
      const [inventoryResponse, summaryResponse] = await Promise.all([
        inventoryApi.getInventory(inventoryFilters),
        inventoryApi.getInventorySummary()
      ]);
      
      setInventoryData(inventoryResponse);
      setSummary(summaryResponse.summary);
      
    } catch (err) {
      console.error('Error loading inventory:', err);
      setError(err instanceof Error ? err.message : 'Failed to load inventory data');
      showToast({
        type: 'error',
        title: 'Error Loading Inventory',
        message: 'Failed to load inventory data. Please try again.'
      });
    } finally {
      setLoading(false);
    }
  }, [filters, showToast]);

  // Load data on mount
  useEffect(() => {
    if (user) {
      loadInventoryData();
    }
  }, [user, loadInventoryData]);

  // Handle filter changes
  const handleFilterChange = (key: keyof FilterState, value: any) => {
    setFilters(prev => ({
      ...prev,
      [key]: value
    }));
  };

  // Apply filters
  const applyFilters = () => {
    loadInventoryData(filters);
    setShowFilters(false);
  };

  // Reset filters
  const resetFilters = () => {
    setFilters({
      status: ['available'],
      batch_types: [],
      product_ids: [],
      facility_ids: [],
      production_date_from: '',
      production_date_to: '',
      expiry_warning_days: null,
      group_by: 'product',
      sort_by: 'production_date',
      sort_order: 'desc'
    });
  };

  // Quick filter buttons
  const handleQuickFilter = (status: string) => {
    setFilters(prev => ({
      ...prev,
      status: [status]
    }));
    loadInventoryData({ ...filters, status: [status] });
  };

  // Render status badge
  const renderStatusBadge = (status: string) => {
    const statusConfig = quickFilters.status.find(s => s.value === status);
    const color = statusConfig?.color || 'gray';
    
    const colorClasses = {
      green: 'bg-green-100 text-green-800',
      yellow: 'bg-yellow-100 text-yellow-800',
      blue: 'bg-blue-100 text-blue-800',
      purple: 'bg-purple-100 text-purple-800',
      red: 'bg-red-100 text-red-800',
      gray: 'bg-gray-100 text-gray-800'
    };
    
    return (
      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${colorClasses[color as keyof typeof colorClasses]}`}>
        {statusConfig?.label || status}
      </span>
    );
  };

  // Render inventory group
  const renderInventoryGroup = (group: any) => {
    const isProductGroup = filters.group_by === 'product';
    const isStatusGroup = filters.group_by === 'status';
    const isFacilityGroup = filters.group_by === 'facility';
    const isDateGroup = filters.group_by === 'date';

    return (
      <Card key={group.product_id || group.status || group.facility_name || group.production_date} className="mb-4">
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <ArchiveBoxIcon className="h-5 w-5 text-gray-500" />
              <span>
                {isProductGroup && `${group.product_name} (${group.product_code})`}
                {isStatusGroup && renderStatusBadge(group.status)}
                {isFacilityGroup && group.facility_name}
                {isDateGroup && new Date(group.production_date).toLocaleDateString()}
              </span>
            </div>
            <div className="text-sm text-gray-500">
              {group.batch_count && `${group.batch_count} batches`}
              <span className="ml-2 font-medium">
                {group.total_quantity?.toLocaleString()} {group.batches?.[0]?.unit || 'units'}
              </span>
            </div>
          </CardTitle>
        </CardHeader>
        <CardBody>
          <div className="space-y-3">
            {group.batches?.map((batch: any) => (
              <div key={batch.batch_id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex-1">
                  <div className="flex items-center space-x-3">
                    <span className="font-medium text-gray-900">{batch.batch_id}</span>
                    {renderStatusBadge(batch.status)}
                    <span className="text-sm text-gray-500">{batch.batch_type}</span>
                  </div>
                  <div className="mt-1 text-sm text-gray-600">
                    <span>Quantity: {batch.quantity.toLocaleString()} {batch.unit}</span>
                    {batch.location_name && <span className="ml-4">Location: {batch.location_name}</span>}
                    {batch.production_date && (
                      <span className="ml-4">
                        Produced: {new Date(batch.production_date).toLocaleDateString()}
                      </span>
                    )}
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-sm font-medium text-gray-900">
                    {batch.available_quantity?.toLocaleString()} {batch.unit}
                  </div>
                  <div className="text-xs text-gray-500">Available</div>
                </div>
              </div>
            ))}
          </div>
        </CardBody>
      </Card>
    );
  };

  if (loading && !inventoryData) {
    return (
      <div className="p-6">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded w-1/4 mb-6"></div>
          <div className="space-y-4">
            <div className="h-32 bg-gray-200 rounded"></div>
            <div className="h-32 bg-gray-200 rounded"></div>
            <div className="h-32 bg-gray-200 rounded"></div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6">
        <div className="text-center">
          <ExclamationTriangleIcon className="h-12 w-12 text-red-500 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">Error Loading Inventory</h3>
          <p className="text-gray-600 mb-4">{error}</p>
          <Button onClick={() => loadInventoryData()}>Try Again</Button>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center">
            <ArchiveBoxIcon className="h-8 w-8 text-blue-600 mr-3" />
            📦 Inventory Management
          </h1>
          <p className="text-gray-600 mt-1">
            Manage and track all your company's inventory batches
          </p>
        </div>
        <div className="flex space-x-2">
          <Button
            variant="outline"
            onClick={() => setShowFilters(!showFilters)}
            className="flex items-center"
          >
            <FunnelIcon className="h-4 w-4 mr-2" />
            {showFilters ? 'Hide Filters' : 'Show Filters'}
          </Button>
        </div>
      </div>

      {/* Summary Cards */}
      {summary && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <Card>
            <CardBody className="p-4">
              <div className="flex items-center">
                <ArchiveBoxIcon className="h-8 w-8 text-blue-600" />
                <div className="ml-3">
                  <p className="text-sm font-medium text-gray-500">Total Batches</p>
                  <p className="text-2xl font-bold text-gray-900">{summary.total_batches}</p>
                </div>
              </div>
            </CardBody>
          </Card>
          
          <Card>
            <CardBody className="p-4">
              <div className="flex items-center">
                <CheckCircleIcon className="h-8 w-8 text-green-600" />
                <div className="ml-3">
                  <p className="text-sm font-medium text-gray-500">Available Quantity</p>
                  <p className="text-2xl font-bold text-gray-900">{summary.available_quantity.toLocaleString()}</p>
                </div>
              </div>
            </CardBody>
          </Card>
          
          <Card>
            <CardBody className="p-4">
              <div className="flex items-center">
                <ChartBarIcon className="h-8 w-8 text-purple-600" />
                <div className="ml-3">
                  <p className="text-sm font-medium text-gray-500">Total Quantity</p>
                  <p className="text-2xl font-bold text-gray-900">{summary.total_quantity.toLocaleString()}</p>
                </div>
              </div>
            </CardBody>
          </Card>
          
          <Card>
            <CardBody className="p-4">
              <div className="flex items-center">
                <ClockIcon className="h-8 w-8 text-yellow-600" />
                <div className="ml-3">
                  <p className="text-sm font-medium text-gray-500">Expiring Soon</p>
                  <p className="text-2xl font-bold text-gray-900">{summary.expiring_soon}</p>
                </div>
              </div>
            </CardBody>
          </Card>
        </div>
      )}

      {/* Quick Filter Buttons */}
      <div className="mb-6">
        <div className="flex flex-wrap gap-2">
          <span className="text-sm font-medium text-gray-700 mr-2">Quick Filters:</span>
          {quickFilters.status.map((status) => (
            <Button
              key={status.value}
              variant={filters.status.includes(status.value) ? "default" : "outline"}
              size="sm"
              onClick={() => handleQuickFilter(status.value)}
            >
              {status.label}
            </Button>
          ))}
        </div>
      </div>

      {/* Advanced Filters */}
      {showFilters && (
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="flex items-center">
              <AdjustmentsHorizontalIcon className="h-5 w-5 mr-2" />
              Advanced Filters
            </CardTitle>
          </CardHeader>
          <CardBody>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <Label htmlFor="group_by">Group By</Label>
                <Select
                  id="group_by"
                  value={filters.group_by}
                  onChange={(e) => handleFilterChange('group_by', e.target.value)}
                  options={quickFilters.groupBy}
                />
              </div>
              
              <div>
                <Label htmlFor="sort_by">Sort By</Label>
                <Select
                  id="sort_by"
                  value={filters.sort_by}
                  onChange={(e) => handleFilterChange('sort_by', e.target.value)}
                  options={quickFilters.sortBy}
                />
              </div>
              
              <div>
                <Label htmlFor="sort_order">Sort Order</Label>
                <Select
                  id="sort_order"
                  value={filters.sort_order}
                  onChange={(e) => handleFilterChange('sort_order', e.target.value)}
                  options={[
                    { value: 'asc', label: 'Ascending' },
                    { value: 'desc', label: 'Descending' }
                  ]}
                />
              </div>
              
              <div>
                <Label htmlFor="production_date_from">Production Date From</Label>
                <Input
                  id="production_date_from"
                  type="date"
                  value={filters.production_date_from}
                  onChange={(e) => handleFilterChange('production_date_from', e.target.value)}
                />
              </div>
              
              <div>
                <Label htmlFor="production_date_to">Production Date To</Label>
                <Input
                  id="production_date_to"
                  type="date"
                  value={filters.production_date_to}
                  onChange={(e) => handleFilterChange('production_date_to', e.target.value)}
                />
              </div>
              
              <div>
                <Label htmlFor="expiry_warning_days">Expiry Warning (Days)</Label>
                <Input
                  id="expiry_warning_days"
                  type="number"
                  value={filters.expiry_warning_days || ''}
                  onChange={(e) => handleFilterChange('expiry_warning_days', e.target.value ? parseInt(e.target.value) : null)}
                  placeholder="30"
                />
              </div>
            </div>
            
            <div className="flex justify-end space-x-2 mt-4">
              <Button variant="outline" onClick={resetFilters}>
                Reset Filters
              </Button>
              <Button onClick={applyFilters}>
                Apply Filters
              </Button>
            </div>
          </CardBody>
        </Card>
      )}

      {/* Inventory Results */}
      <div className="space-y-4">
        {inventoryData?.results?.length === 0 ? (
          <Card>
            <CardBody className="text-center py-12">
              <ArchiveBoxIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">No Inventory Found</h3>
              <p className="text-gray-600">
                No batches match your current filters. Try adjusting your search criteria.
              </p>
            </CardBody>
          </Card>
        ) : (
          inventoryData?.results?.map(renderInventoryGroup)
        )}
      </div>

      {/* Loading overlay */}
      {loading && (
        <div className="fixed inset-0 bg-black bg-opacity-25 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 flex items-center space-x-3">
            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
            <span className="text-gray-700">Loading inventory...</span>
          </div>
        </div>
      )}
    </div>
  );
};

export default InventoryPage;
