/**
 * Originator V2 Dashboard Content - Role-specific dashboard content for originator companies
 * Works with main layout system, no duplicate navigation
 */
import React from 'react';
import { useDashboardConfig, useDashboardMetrics } from '../../../hooks/useDashboardConfig';
import LoadingSpinner from '../../ui/LoadingSpinner';
import { Card, CardHeader, CardBody } from '../../ui/Card';
import { Button } from '../../ui/Button';
import { Badge } from '../../ui/Badge';
import AnalyticsCard from '../../ui/AnalyticsCard';
import Input from '../../ui/Input';
import Select from '../../ui/Select';
import { 
  MapIcon,
  ShieldCheckIcon,
  ChartBarIcon,
  DocumentCheckIcon,
  PlusIcon,
  BuildingOfficeIcon,
  ExclamationTriangleIcon,
  EyeIcon,
  CalendarIcon,
  DocumentTextIcon,
  ArrowRightIcon,
  MagnifyingGlassIcon,
  FunnelIcon,
  ChevronUpIcon,
  ChevronDownIcon,
  BellIcon,
  InformationCircleIcon,
  ArrowDownTrayIcon,
  HomeIcon
} from '@heroicons/react/24/outline';

interface ProductionTracker {
  recent_harvests: number;
  pending_po_links: number;
}

interface FarmManagement {
  total_farms: number;
  eudr_compliant: number;
  certifications_expiring: number;
}

interface RecentActivity {
  harvests_this_week: number;
  pos_confirmed: number;
}

interface OriginatorMetrics {
  production_tracker: ProductionTracker;
  farm_management: FarmManagement;
  recent_activity: RecentActivity;
}

const OriginatorLayout: React.FC = () => {
  const { config, loading: configLoading } = useDashboardConfig();
  const { metrics, loading: metricsLoading } = useDashboardMetrics('originator');
  const [searchTerm, setSearchTerm] = React.useState('');
  const [sortField, setSortField] = React.useState<string>('');
  const [sortDirection, setSortDirection] = React.useState<'asc' | 'desc'>('asc');
  const [statusFilter, setStatusFilter] = React.useState<string>('');

  if (configLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner size="lg" />
        <span className="ml-3 text-gray-600">Loading dashboard...</span>
      </div>
    );
  }

  if (!config) {
    return (
      <div className="text-center py-12">
        <p className="text-red-600">Failed to load dashboard configuration</p>
      </div>
    );
  }

  const originatorMetrics = metrics as OriginatorMetrics;

  // Mock data for the tabs
  const latestPurchaseOrders = [
    {
      id: '1',
      po_number: 'PO-2025-001',
      supplier: 'PT Kalimantan Plantation',
      product: 'Fresh Fruit Bunches',
      quantity: 5000,
      status: 'confirmed',
      date: '2025-01-10',
      value: 125000
    },
    {
      id: '2',
      po_number: 'PO-2025-002',
      supplier: 'Sumatra Smallholder Cooperative',
      product: 'Fresh Fruit Bunches',
      quantity: 3200,
      status: 'pending',
      date: '2025-01-09',
      value: 80000
    },
    {
      id: '3',
      po_number: 'PO-2025-003',
      supplier: 'PT Kalimantan Plantation',
      product: 'Fresh Fruit Bunches',
      quantity: 7500,
      status: 'confirmed',
      date: '2025-01-08',
      value: 187500
    },
    {
      id: '4',
      po_number: 'PO-2025-004',
      supplier: 'Borneo Sustainable Farms',
      product: 'Fresh Fruit Bunches',
      quantity: 2800,
      status: 'draft',
      date: '2025-01-07',
      value: 70000
    },
    {
      id: '5',
      po_number: 'PO-2025-005',
      supplier: 'Sumatra Smallholder Cooperative',
      product: 'Fresh Fruit Bunches',
      quantity: 4100,
      status: 'confirmed',
      date: '2025-01-06',
      value: 102500
    }
  ];


  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'confirmed':
        return <Badge variant="success">Confirmed</Badge>;
      case 'pending':
        return <Badge variant="warning">Pending</Badge>;
      case 'draft':
        return <Badge variant="neutral">Draft</Badge>;
      case 'verified':
        return <Badge variant="success">Verified</Badge>;
      case 'submitted':
        return <Badge variant="primary">Submitted</Badge>;
      default:
        return <Badge variant="neutral">{status}</Badge>;
    }
  };


  // Filter and sort data
  const getFilteredAndSortedData = (data: any[], type: 'purchase-orders') => {
    let filtered = data;

    // Apply search filter
    if (searchTerm) {
      if (type === 'purchase-orders') {
        filtered = filtered.filter(item => 
          item.po_number.toLowerCase().includes(searchTerm.toLowerCase()) ||
          item.supplier.toLowerCase().includes(searchTerm.toLowerCase()) ||
          item.product.toLowerCase().includes(searchTerm.toLowerCase())
        );
      } else {
        filtered = filtered.filter(item => 
          item.batch_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
          item.farm_name.toLowerCase().includes(searchTerm.toLowerCase())
        );
      }
    }

    // Apply status filter
    if (statusFilter) {
      filtered = filtered.filter(item => item.status === statusFilter);
    }

    // Apply sorting
    if (sortField) {
      filtered = [...filtered].sort((a, b) => {
        const aValue = a[sortField];
        const bValue = b[sortField];
        
        if (typeof aValue === 'string' && typeof bValue === 'string') {
          return sortDirection === 'asc' 
            ? aValue.localeCompare(bValue)
            : bValue.localeCompare(aValue);
        }
        
        if (typeof aValue === 'number' && typeof bValue === 'number') {
          return sortDirection === 'asc' ? aValue - bValue : bValue - aValue;
        }
        
        return 0;
      });
    }

    return filtered;
  };

  const handleSort = (field: string) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('asc');
    }
  };

  const getSortIcon = (field: string) => {
    if (sortField !== field) return null;
    return sortDirection === 'asc' 
      ? <ChevronUpIcon className="h-4 w-4" />
      : <ChevronDownIcon className="h-4 w-4" />;
  };

  // Get filtered data
  const filteredPurchaseOrders = getFilteredAndSortedData(latestPurchaseOrders, 'purchase-orders');

  // Status counts for metrics
  const statusCounts = {
    confirmedPOs: latestPurchaseOrders.filter(po => po.status === 'confirmed').length,
    pendingPOs: latestPurchaseOrders.filter(po => po.status === 'pending').length,
    expiringCertifications: originatorMetrics?.farm_management?.certifications_expiring || 0
  };

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div className="md:flex md:items-center md:justify-between">
        <div className="min-w-0 flex-1">
          <h2 className="text-2xl font-bold leading-7 text-gray-900 sm:truncate sm:text-3xl sm:tracking-tight">
            Originator Dashboard
          </h2>
          <p className="mt-1 text-sm text-gray-500">
            Farm management and certification tracking
          </p>
        </div>
        <div className="mt-4 flex space-x-3 md:ml-4 md:mt-0">
          <Button variant="outline" size="sm">
            <ArrowDownTrayIcon className="h-4 w-4 mr-2" />
            Export Data
          </Button>
          <Button>
            <PlusIcon className="h-4 w-4 mr-2" />
            Add New Farm
          </Button>
        </div>
      </div>

      {/* Notifications/Alerts */}
      {statusCounts.expiringCertifications > 0 && (
        <Card className="border-yellow-200 bg-yellow-50">
          <CardBody>
            <div className="flex items-start space-x-3">
              <ExclamationTriangleIcon className="h-5 w-5 text-yellow-500 mt-0.5" />
              <div>
                <h3 className="font-medium text-yellow-800">Certifications Expiring Soon</h3>
                <p className="text-sm text-yellow-700 mt-1">
                  You have {statusCounts.expiringCertifications} certification(s) expiring within 90 days. 
                  <Button variant="link" className="text-yellow-700 underline p-0 ml-1">
                    Review now
                  </Button>
                </p>
              </div>
            </div>
          </CardBody>
        </Card>
      )}


      {/* Dashboard content */}
      {metricsLoading ? (
        <div className="flex items-center justify-center h-64">
          <LoadingSpinner size="lg" />
          <span className="ml-3 text-gray-600">Loading metrics...</span>
        </div>
      ) : (
        <div className="space-y-6">
          {/* Key Metrics */}
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <AnalyticsCard
              title="Total Farms"
              value={originatorMetrics?.farm_management?.total_farms || 0}
              subtitle="Active farms"
              icon={MapIcon}
              trend={{ value: 2, isPositive: true }}
            />
            <AnalyticsCard
              title="EUDR Compliant"
              value={originatorMetrics?.farm_management?.eudr_compliant || 0}
              subtitle="Compliant farms"
              icon={ShieldCheckIcon}
              trend={{ value: 5, isPositive: true }}
            />
            <AnalyticsCard
              title="Certifications Expiring"
              value={originatorMetrics?.farm_management?.certifications_expiring || 0}
              subtitle="Within 90 days"
              icon={BuildingOfficeIcon}
              trend={{ value: 1, isPositive: false }}
            />
            <AnalyticsCard
              title="POs Confirmed"
              value={originatorMetrics?.recent_activity?.pos_confirmed || 0}
              subtitle="This month"
              icon={ChartBarIcon}
              trend={{ value: 12, isPositive: true }}
            />
            </div>


              {/* Latest Activity Tabs */}
              <Card>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <h3 className="text-lg font-medium text-gray-900">Latest Purchase Orders</h3>
                  </div>
                </CardHeader>
                
                {/* Search and Filter Bar */}
                <div className="px-6 py-4 border-b border-gray-200 bg-gray-50">
                  <div className="flex flex-col sm:flex-row gap-4">
                    <div className="flex-1">
                      <div className="relative">
                        <MagnifyingGlassIcon className="h-5 w-5 absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
                        <Input
                          type="text"
                          placeholder="Search PO numbers, suppliers, products..."
                          value={searchTerm}
                          onChange={(e) => setSearchTerm(e.target.value)}
                          className="pl-10"
                        />
                      </div>
                    </div>
                    <div className="flex gap-2">
                      <Select
                        value={statusFilter}
                        onChange={(e) => setStatusFilter(e.target.value)}
                        options={[
                          { label: 'All Status', value: '' },
                          { label: 'Confirmed', value: 'confirmed' },
                          { label: 'Pending', value: 'pending' },
                          { label: 'Draft', value: 'draft' }
                        ]}
                        className="min-w-[120px]"
                      />
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => {
                          setSearchTerm('');
                          setStatusFilter('');
                          setSortField('');
                        }}
                      >
                        <FunnelIcon className="h-4 w-4 mr-2" />
                        Clear
                      </Button>
                    </div>
                  </div>
            </div>

                <CardBody padding="none">
                  <div className="overflow-x-auto">
                      <table className="min-w-full divide-y divide-gray-200">
                        <thead className="bg-gray-50">
                          <tr>
                            <th 
                              className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                              onClick={() => handleSort('po_number')}
                            >
                              <div className="flex items-center space-x-1">
                                <span>PO Number</span>
                                {getSortIcon('po_number')}
                              </div>
                            </th>
                            <th 
                              className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                              onClick={() => handleSort('supplier')}
                            >
                              <div className="flex items-center space-x-1">
                                <span>Supplier</span>
                                {getSortIcon('supplier')}
                              </div>
                            </th>
                            <th 
                              className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                              onClick={() => handleSort('product')}
                            >
                              <div className="flex items-center space-x-1">
                                <span>Product</span>
                                {getSortIcon('product')}
                              </div>
                            </th>
                            <th 
                              className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                              onClick={() => handleSort('quantity')}
                            >
                              <div className="flex items-center space-x-1">
                                <span>Quantity</span>
                                {getSortIcon('quantity')}
                              </div>
                            </th>
                            <th 
                              className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                              onClick={() => handleSort('status')}
                            >
                              <div className="flex items-center space-x-1">
                                <span>Status</span>
                                {getSortIcon('status')}
                              </div>
                            </th>
                            <th 
                              className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                              onClick={() => handleSort('date')}
                            >
                              <div className="flex items-center space-x-1">
                                <span>Date</span>
                                {getSortIcon('date')}
                  </div>
                            </th>
                            <th 
                              className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                              onClick={() => handleSort('value')}
                            >
                              <div className="flex items-center space-x-1">
                                <span>Value</span>
                                {getSortIcon('value')}
                      </div>
                            </th>
                          </tr>
                        </thead>
                        <tbody className="bg-white divide-y divide-gray-200">
                          {filteredPurchaseOrders.map((po, index) => (
                            <tr 
                              key={po.id} 
                              className={`hover:bg-gray-50 cursor-pointer ${index % 2 === 0 ? 'bg-white' : 'bg-gray-50'}`}
                              onClick={() => {
                                // Navigate to PO details
                                console.log('Navigate to PO:', po.id);
                              }}
                            >
                              <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                                {po.po_number}
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                {po.supplier}
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                {po.product}
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                {(po.quantity || 0).toLocaleString()} KG
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap">
                                {getStatusBadge(po.status)}
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                {po.date}
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                ${po.value.toLocaleString()}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  
                  {/* See More Button */}
                  <div className="px-6 py-4 bg-gray-50 border-t border-gray-200">
                    <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
                      <div className="text-sm text-gray-600">
                        <p>
                          Showing {filteredPurchaseOrders.length} of {latestPurchaseOrders.length} items
                          {(searchTerm || statusFilter) && (
                            <span className="text-blue-600 ml-1">
                              (filtered)
                    </span>
                          )}
                        </p>
                      </div>
                      <div className="flex gap-2">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => {
                            // Export functionality
                            console.log('Export data');
                          }}
                        >
                          <ArrowDownTrayIcon className="h-4 w-4 mr-2" />
                          Export
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => {
                            window.location.href = '/purchase-orders';
                          }}
                        >
                          See More
                          <ArrowRightIcon className="h-4 w-4 ml-2" />
                        </Button>
                        </div>
                    </div>
                  </div>
                </CardBody>
              </Card>
            </div>
      )}
    </div>
  );
};

export default OriginatorLayout;