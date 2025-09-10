/**
 * Batch Management Page
 * Comprehensive batch CRUD operations, search, filtering, and status management
 */
import React, { useState, useEffect, useCallback } from 'react';
import {
  PlusIcon,
  MagnifyingGlassIcon,
  FunnelIcon,
  PencilIcon,
  EyeIcon,
  TrashIcon,
  ArrowPathIcon,
  ChevronLeftIcon,
  ChevronRightIcon
} from '@heroicons/react/24/outline';
import { useAuth } from '../contexts/AuthContext';
import { useToast } from '../contexts/ToastContext';
import { Card, CardHeader, CardBody } from '../components/ui/Card';
import Button from '../components/ui/Button';
import Input from '../components/ui/Input';
import Select from '../components/ui/Select';
import Badge from '../components/ui/Badge';
import LoadingSpinner from '../components/ui/LoadingSpinner';
import Modal from '../components/ui/Modal';
import { formatDate } from '../lib/utils';

interface Batch {
  id: string;
  batch_id: string;
  batch_type: 'harvest' | 'processing' | 'transformation';
  product_name: string;
  quantity: number;
  unit: string;
  status: 'active' | 'consumed' | 'expired' | 'recalled';
  production_date: string;
  expiry_date?: string;
  location_name?: string;
  facility_code?: string;
  created_at: string;
}

interface BatchFilter {
  search?: string;
  batch_type?: string;
  status?: string;
  product_id?: string;
  page: number;
  per_page: number;
}

const BatchManagement: React.FC = () => {
  const { user } = useAuth();
  const { showToast } = useToast();
  
  // State
  const [batches, setBatches] = useState<Batch[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [typeFilter, setTypeFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalBatches, setTotalBatches] = useState(0);
  const [selectedBatch, setSelectedBatch] = useState<Batch | null>(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showViewModal, setShowViewModal] = useState(false);
  
  const perPage = 20;

  // Load batches
  const loadBatches = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      
      // TODO: Replace with actual API call
      // Simulated data for now
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      const mockBatches: Batch[] = [
        {
          id: '1',
          batch_id: 'HARVEST-2025-001',
          batch_type: 'harvest',
          product_name: 'Fresh Fruit Bunches',
          quantity: 1000,
          unit: 'KGM',
          status: 'active',
          production_date: '2025-01-10',
          expiry_date: '2025-02-10',
          location_name: 'Plantation A',
          facility_code: 'FARM-001',
          created_at: '2025-01-10T10:30:00Z'
        },
        {
          id: '2',
          batch_id: 'PROCESS-2025-001',
          batch_type: 'processing',
          product_name: 'Crude Palm Oil',
          quantity: 750,
          unit: 'KGM',
          status: 'active',
          production_date: '2025-01-09',
          expiry_date: '2025-07-09',
          location_name: 'Mill A',
          facility_code: 'MILL-001',
          created_at: '2025-01-09T14:20:00Z'
        },
        {
          id: '3',
          batch_id: 'REFINE-2025-001',
          batch_type: 'transformation',
          product_name: 'Refined Palm Oil',
          quantity: 600,
          unit: 'KGM',
          status: 'consumed',
          production_date: '2025-01-08',
          expiry_date: '2026-01-08',
          location_name: 'Refinery A',
          facility_code: 'REF-001',
          created_at: '2025-01-08T09:15:00Z'
        }
      ];
      
      setBatches(mockBatches);
      setTotalPages(1);
      setTotalBatches(mockBatches.length);
      
    } catch (err) {
      console.error('Error loading batches:', err);
      setError('Failed to load batches. Please try again.');
      showToast({
        type: 'error',
        title: 'Error loading batches',
        message: 'Please try again or contact support if the problem persists.'
      });
    } finally {
      setIsLoading(false);
    }
  }, [currentPage, searchTerm, typeFilter, statusFilter, showToast]);

  // Load batches when filters change
  useEffect(() => {
    loadBatches();
  }, [loadBatches]);

  // Handle search
  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setCurrentPage(1);
    loadBatches();
  };

  // Handle filter changes
  const handleTypeChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
    setTypeFilter(event.target.value);
    setCurrentPage(1);
  };

  const handleStatusChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
    setStatusFilter(event.target.value);
    setCurrentPage(1);
  };

  // Handle pagination
  const handlePageChange = (page: number) => {
    setCurrentPage(page);
  };

  // Clear filters
  const clearFilters = () => {
    setSearchTerm('');
    setTypeFilter('');
    setStatusFilter('');
    setCurrentPage(1);
  };

  // Handle batch actions
  const handleViewBatch = (batch: Batch) => {
    setSelectedBatch(batch);
    setShowViewModal(true);
  };

  const handleEditBatch = (batch: Batch) => {
    setSelectedBatch(batch);
    setShowEditModal(true);
  };

  const handleDeleteBatch = async (batch: Batch) => {
    if (window.confirm(`Are you sure you want to delete batch ${batch.batch_id}?`)) {
      try {
        // TODO: Implement delete API call
        showToast({
          type: 'success',
          title: 'Batch deleted',
          message: `Batch ${batch.batch_id} has been deleted successfully.`
        });
        loadBatches();
      } catch (error) {
        showToast({
          type: 'error',
          title: 'Error',
          message: 'Failed to delete batch. Please try again.'
        });
      }
    }
  };

  // Format batch type for display
  const formatBatchType = (type: string) => {
    return type.charAt(0).toUpperCase() + type.slice(1);
  };

  // Get status badge variant
  const getStatusVariant = (status: string) => {
    switch (status) {
      case 'active':
        return 'success';
      case 'consumed':
        return 'neutral';
      case 'expired':
        return 'warning';
      case 'recalled':
        return 'error';
      default:
        return 'neutral';
    }
  };

  return (
    <>
      {/* Page Header */}
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Batch Management</h1>
          <p className="text-gray-600 mt-1">
            Manage your inventory batches, track status, and monitor lifecycle.
          </p>
        </div>
        <Button 
          variant="primary" 
          leftIcon={<PlusIcon className="h-4 w-4" />}
          onClick={() => setShowCreateModal(true)}
        >
          Create Batch
        </Button>
      </div>

      {/* Filters */}
      <Card className="mb-6">
        <CardHeader title="Search & Filter" />
        <CardBody>
          <form onSubmit={handleSearch} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              {/* Search */}
              <div className="md:col-span-2">
                <Input
                  type="text"
                  placeholder="Search batches..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  leftIcon={<MagnifyingGlassIcon className="h-4 w-4" />}
                />
              </div>
              
              {/* Type Filter */}
              <div>
                <Select
                  value={typeFilter}
                  onChange={handleTypeChange}
                  options={[
                    { label: 'All Types', value: '' },
                    { label: 'Harvest', value: 'harvest' },
                    { label: 'Processing', value: 'processing' },
                    { label: 'Transformation', value: 'transformation' }
                  ]}
                />
              </div>
              
              {/* Status Filter */}
              <div>
                <Select
                  value={statusFilter}
                  onChange={handleStatusChange}
                  options={[
                    { label: 'All Status', value: '' },
                    { label: 'Active', value: 'active' },
                    { label: 'Consumed', value: 'consumed' },
                    { label: 'Expired', value: 'expired' },
                    { label: 'Recalled', value: 'recalled' }
                  ]}
                />
              </div>
            </div>
            
            <div className="flex items-center space-x-4">
              <Button type="submit" variant="primary" size="sm">
                <MagnifyingGlassIcon className="h-4 w-4 mr-2" />
                Search
              </Button>
              <Button type="button" variant="secondary" size="sm" onClick={clearFilters}>
                <FunnelIcon className="h-4 w-4 mr-2" />
                Clear Filters
              </Button>
              <Button type="button" variant="outline" size="sm" onClick={loadBatches}>
                <ArrowPathIcon className="h-4 w-4 mr-2" />
                Refresh
              </Button>
            </div>
          </form>
        </CardBody>
      </Card>

      {/* Results */}
      <Card>
        <CardHeader 
          title={`Batches (${totalBatches})`}
          subtitle={`Page ${currentPage} of ${totalPages}`}
        />
        <CardBody padding="none">
          {isLoading ? (
            <div className="flex items-center justify-center py-12">
              <LoadingSpinner size="lg" />
            </div>
          ) : error ? (
            <div className="text-center py-12">
              <p className="text-red-600 mb-4">{error}</p>
              <Button onClick={loadBatches} variant="primary">
                Try Again
              </Button>
            </div>
          ) : batches.length === 0 ? (
            <div className="text-center py-12">
              <p className="text-gray-600 mb-4">No batches found</p>
              <Button onClick={clearFilters} variant="secondary">
                Clear Filters
              </Button>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Batch ID
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Product
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Type
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Quantity
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Status
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Location
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Created
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {batches.map((batch) => (
                    <tr key={batch.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm font-medium text-gray-900">
                          {batch.batch_id}
                        </div>
                        {batch.facility_code && (
                          <div className="text-sm text-gray-500">
                            {batch.facility_code}
                          </div>
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-900">{batch.product_name}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <Badge variant="secondary">
                          {formatBatchType(batch.batch_type)}
                        </Badge>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {batch.quantity} {batch.unit}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <Badge variant={getStatusVariant(batch.status)}>
                          {batch.status.charAt(0).toUpperCase() + batch.status.slice(1)}
                        </Badge>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {batch.location_name || '-'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {formatDate(batch.created_at)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                        <div className="flex items-center justify-end space-x-2">
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handleViewBatch(batch)}
                          >
                            <EyeIcon className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handleEditBatch(batch)}
                          >
                            <PencilIcon className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handleDeleteBatch(batch)}
                          >
                            <TrashIcon className="h-4 w-4" />
                          </Button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardBody>
      </Card>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="mt-6 flex items-center justify-between">
          <div className="text-sm text-gray-700">
            Showing {((currentPage - 1) * perPage) + 1} to {Math.min(currentPage * perPage, totalBatches)} of {totalBatches} batches
          </div>
          <div className="flex items-center space-x-2">
            <Button
              variant="outline"
              size="sm"
              disabled={currentPage <= 1}
              onClick={() => handlePageChange(currentPage - 1)}
            >
              <ChevronLeftIcon className="h-4 w-4 mr-1" />
              Previous
            </Button>
            
            <span className="text-sm text-gray-700">
              Page {currentPage} of {totalPages}
            </span>
            
            <Button
              variant="outline"
              size="sm"
              disabled={currentPage >= totalPages}
              onClick={() => handlePageChange(currentPage + 1)}
            >
              Next
              <ChevronRightIcon className="h-4 w-4 ml-1" />
            </Button>
          </div>
        </div>
      )}

      {/* Modals */}
      {showCreateModal && (
        <Modal
          isOpen={showCreateModal}
          onClose={() => setShowCreateModal(false)}
          title="Create New Batch"
        >
          <div className="p-6">
            <p className="text-gray-600 mb-4">
              Create batch form will be implemented here.
            </p>
            <div className="flex justify-end space-x-3">
              <Button variant="outline" onClick={() => setShowCreateModal(false)}>
                Cancel
              </Button>
              <Button variant="primary">
                Create Batch
              </Button>
            </div>
          </div>
        </Modal>
      )}

      {showEditModal && selectedBatch && (
        <Modal
          isOpen={showEditModal}
          onClose={() => setShowEditModal(false)}
          title={`Edit Batch ${selectedBatch.batch_id}`}
        >
          <div className="p-6">
            <p className="text-gray-600 mb-4">
              Edit batch form will be implemented here.
            </p>
            <div className="flex justify-end space-x-3">
              <Button variant="outline" onClick={() => setShowEditModal(false)}>
                Cancel
              </Button>
              <Button variant="primary">
                Save Changes
              </Button>
            </div>
          </div>
        </Modal>
      )}

      {showViewModal && selectedBatch && (
        <Modal
          isOpen={showViewModal}
          onClose={() => setShowViewModal(false)}
          title={`Batch Details - ${selectedBatch.batch_id}`}
        >
          <div className="p-6">
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">Product</label>
                <p className="text-sm text-gray-900">{selectedBatch.product_name}</p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Quantity</label>
                <p className="text-sm text-gray-900">{selectedBatch.quantity} {selectedBatch.unit}</p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Status</label>
                <Badge variant={getStatusVariant(selectedBatch.status)}>
                  {selectedBatch.status.charAt(0).toUpperCase() + selectedBatch.status.slice(1)}
                </Badge>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Production Date</label>
                <p className="text-sm text-gray-900">{formatDate(selectedBatch.production_date)}</p>
              </div>
              {selectedBatch.expiry_date && (
                <div>
                  <label className="block text-sm font-medium text-gray-700">Expiry Date</label>
                  <p className="text-sm text-gray-900">{formatDate(selectedBatch.expiry_date)}</p>
                </div>
              )}
              <div>
                <label className="block text-sm font-medium text-gray-700">Location</label>
                <p className="text-sm text-gray-900">{selectedBatch.location_name || 'Not specified'}</p>
              </div>
            </div>
            <div className="flex justify-end mt-6">
              <Button variant="outline" onClick={() => setShowViewModal(false)}>
                Close
              </Button>
            </div>
          </div>
        </Modal>
      )}
    </>
  );
};

export default BatchManagement;
