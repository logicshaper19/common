/**
 * Compliance Dashboard Component
 * Following the project plan: Dashboard for consultants to see all POs with compliance issues
 */
import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardBody } from '../ui/Card';
import Badge from '../ui/Badge';
import Button from '../ui/Button';
import Input from '../ui/Input';
import Select from '../ui/Select';
import AnalyticsCard from '../ui/AnalyticsCard';
import {
  ArrowPathIcon,
  MagnifyingGlassIcon,
  FunnelIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  XCircleIcon,
  ClockIcon
} from '@heroicons/react/24/outline';
import { complianceApi, ComplianceDashboardResponse, ComplianceDashboardItem } from '../../services/complianceApi';

interface ComplianceDashboardProps {
  className?: string;
}

const getStatusIcon = (status: string) => {
  switch (status) {
    case 'pass':
      return <CheckCircleIcon className="h-4 w-4 text-green-600" />;
    case 'fail':
      return <XCircleIcon className="h-4 w-4 text-red-600" />;
    case 'warning':
      return <ExclamationTriangleIcon className="h-4 w-4 text-yellow-600" />;
    case 'pending':
      return <ClockIcon className="h-4 w-4 text-gray-600" />;
    default:
      return <ClockIcon className="h-4 w-4 text-gray-600" />;
  }
};



export const ComplianceDashboard: React.FC<ComplianceDashboardProps> = ({ className }) => {
  const [dashboardData, setDashboardData] = useState<ComplianceDashboardResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [availableRegulations, setAvailableRegulations] = useState<string[]>([]);
  
  // Filters
  const [regulationFilter, setRegulationFilter] = useState<string>('');
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [currentPage, setCurrentPage] = useState(0);
  const [pageSize] = useState(50);

  useEffect(() => {
    loadAvailableRegulations();
    loadDashboardData();
  }, []);

  useEffect(() => {
    loadDashboardData();
  }, [regulationFilter, statusFilter, currentPage]);

  const loadAvailableRegulations = async () => {
    try {
      const response = await complianceApi.getAvailableRegulations();
      setAvailableRegulations(response.available_regulations);
    } catch (err) {
      console.error('Error loading regulations:', err);
    }
  };

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await complianceApi.getComplianceDashboard({
        regulation: regulationFilter || undefined,
        status: statusFilter || undefined,
        limit: pageSize,
        offset: currentPage * pageSize
      });
      
      setDashboardData(response);
    } catch (err) {
      console.error('Error loading dashboard data:', err);
      setError('Failed to load compliance dashboard data');
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = () => {
    setCurrentPage(0);
    loadDashboardData();
  };

  const handleClearFilters = () => {
    setRegulationFilter('');
    setStatusFilter('');
    setSearchTerm('');
    setCurrentPage(0);
  };

  const filteredData = dashboardData?.results.filter(item => {
    if (!searchTerm) return true;
    const searchLower = searchTerm.toLowerCase();
    return (
      item.po_number.toLowerCase().includes(searchLower) ||
      item.buyer_company.toLowerCase().includes(searchLower) ||
      item.seller_company.toLowerCase().includes(searchLower) ||
      item.product.toLowerCase().includes(searchLower) ||
      item.check_name.toLowerCase().includes(searchLower)
    );
  }) || [];

  const totalPages = dashboardData ? Math.ceil(dashboardData.total_count / pageSize) : 0;

  if (loading && !dashboardData) {
    return (
      <Card className={className}>
        <CardHeader title="Loading Compliance Dashboard" />
        <CardBody>
          <div className="flex items-center justify-center py-8">
            <ClockIcon className="h-6 w-6 text-neutral-400 mr-2 animate-spin" />
            <span className="text-neutral-500">Loading compliance data for all purchase orders...</span>
          </div>
        </CardBody>
      </Card>
    );
  }

  return (
    <div className={className}>
      <Card>
        <CardHeader
          title="Compliance Dashboard"
          action={
            <Button
              onClick={handleRefresh}
              disabled={loading}
              size="sm"
              variant="outline"
            >
              <ArrowPathIcon className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
              Refresh
            </Button>
          }
        />
        <CardBody>
          {error && (
            <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg">
              <div className="flex items-center">
                <ExclamationTriangleIcon className="h-4 w-4 text-red-600 mr-2" />
                <span className="text-red-800">{error}</span>
              </div>
            </div>
          )}

          {/* Filters */}
          <div className="flex flex-wrap gap-4 mb-6 p-4 bg-gray-50 rounded-lg">
            <div className="flex-1 min-w-[200px]">
              <label className="block text-sm font-medium mb-1">Search</label>
              <div className="relative">
                <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                <Input
                  placeholder="Search PO, company, product..."
                  value={searchTerm}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) => setSearchTerm(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>
            
            <div className="min-w-[150px]">
              <label className="block text-sm font-medium mb-1">Regulation</label>
              <Select
                value={regulationFilter}
                onChange={(e: React.ChangeEvent<HTMLSelectElement>) => setRegulationFilter(e.target.value)}
                options={[
                  { label: 'All regulations', value: '' },
                  ...availableRegulations.map(regulation => ({
                    label: regulation.toUpperCase(),
                    value: regulation
                  }))
                ]}
              />
            </div>
            
            <div className="min-w-[120px]">
              <label className="block text-sm font-medium mb-1">Status</label>
              <Select
                value={statusFilter}
                onChange={(e: React.ChangeEvent<HTMLSelectElement>) => setStatusFilter(e.target.value)}
                options={[
                  { label: 'All statuses', value: '' },
                  { label: 'Failed', value: 'fail' },
                  { label: 'Warning', value: 'warning' },
                  { label: 'Passed', value: 'pass' },
                  { label: 'Pending', value: 'pending' }
                ]}
              />
            </div>
            
            <div className="flex items-end">
              <Button onClick={handleClearFilters} variant="outline" size="sm">
                <FunnelIcon className="h-4 w-4 mr-2" />
                Clear Filters
              </Button>
            </div>
          </div>

          {/* Summary Stats */}
          {dashboardData && (
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
              <AnalyticsCard
                name="Total Checks"
                value={dashboardData.total_count.toString()}
                icon={CheckCircleIcon}
                size="sm"
              />
              <AnalyticsCard
                name="Failed"
                value={dashboardData.results.filter((r: ComplianceDashboardItem) => r.status === 'fail').length.toString()}
                changeType="decrease"
                icon={XCircleIcon}
                size="sm"
              />
              <AnalyticsCard
                name="Warnings"
                value={dashboardData.results.filter((r: ComplianceDashboardItem) => r.status === 'warning').length.toString()}
                changeType="neutral"
                icon={ExclamationTriangleIcon}
                size="sm"
              />
              <AnalyticsCard
                name="Passed"
                value={dashboardData.results.filter((r: ComplianceDashboardItem) => r.status === 'pass').length.toString()}
                changeType="increase"
                icon={CheckCircleIcon}
                size="sm"
              />
            </div>
          )}

          {/* Results Table */}
          <div className="border rounded-lg overflow-hidden">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">PO Number</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Regulation</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Check</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Buyer</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Seller</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Product</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Checked</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {filteredData.length === 0 ? (
                  <tr>
                    <td colSpan={8} className="px-6 py-8 text-center text-gray-500">
                      {loading ? 'Loading...' : 'No compliance data found'}
                    </td>
                  </tr>
                ) : (
                  filteredData.map((item: ComplianceDashboardItem, index: number) => (
                    <tr key={index} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{item.po_number}</td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <Badge variant="secondary">{item.regulation.toUpperCase()}</Badge>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {item.check_name.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center gap-2">
                          {getStatusIcon(item.status)}
                          <Badge variant={item.status === 'pass' ? 'success' : item.status === 'fail' ? 'error' : item.status === 'warning' ? 'warning' : 'neutral'}>
                            {item.status.toUpperCase()}
                          </Badge>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 max-w-[150px] truncate" title={item.buyer_company}>
                        {item.buyer_company}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 max-w-[150px] truncate" title={item.seller_company}>
                        {item.seller_company}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 max-w-[120px] truncate" title={item.product}>
                        {item.product}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                        {item.checked_at ? new Date(item.checked_at).toLocaleDateString() : 'Not checked'}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between mt-4">
              <div className="text-sm text-gray-600">
                Showing {currentPage * pageSize + 1} to {Math.min((currentPage + 1) * pageSize, dashboardData?.total_count || 0)} of {dashboardData?.total_count || 0} results
              </div>
              <div className="flex gap-2">
                <Button
                  onClick={() => setCurrentPage(Math.max(0, currentPage - 1))}
                  disabled={currentPage === 0 || loading}
                  variant="outline"
                  size="sm"
                >
                  Previous
                </Button>
                <Button
                  onClick={() => setCurrentPage(Math.min(totalPages - 1, currentPage + 1))}
                  disabled={currentPage >= totalPages - 1 || loading}
                  variant="outline"
                  size="sm"
                >
                  Next
                </Button>
              </div>
            </div>
          )}
        </CardBody>
      </Card>
    </div>
  );
};
