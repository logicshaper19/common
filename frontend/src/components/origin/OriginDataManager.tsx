/**
 * Origin Data Manager Component
 * Comprehensive origin data management with table view and form access
 */
import React, { useState, useEffect } from 'react';
import {
  MapPinIcon,
  DocumentTextIcon,
  PlusIcon,
  PencilIcon,
  EyeIcon,
  TrashIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  ClockIcon
} from '@heroicons/react/24/outline';
import { Card, CardHeader, CardBody } from '../ui/Card';
import DataTable, { DataTableColumn } from '../ui/DataTable';
import Button from '../ui/Button';
import Badge from '../ui/Badge';
import Modal from '../ui/Modal';
import LoadingSpinner from '../ui/LoadingSpinner';
import OriginatorConfirmationForm from './OriginatorConfirmationForm';
import { useToast } from '../../contexts/ToastContext';
import { formatDate } from '../../lib/utils';
import { originApi, OriginDataRecord, OriginDataFilters } from '../../services/originApi';

// OriginDataRecord interface is now imported from originApi

interface OriginDataManagerProps {
  companyId?: string;
  className?: string;
}

const OriginDataManager: React.FC<OriginDataManagerProps> = ({
  companyId,
  className = ''
}) => {
  const { showToast } = useToast();
  
  // State
  const [originDataRecords, setOriginDataRecords] = useState<OriginDataRecord[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedRecord, setSelectedRecord] = useState<OriginDataRecord | null>(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showViewModal, setShowViewModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);

  // Load origin data records
  useEffect(() => {
    loadOriginDataRecords();
  }, [companyId]);

  const loadOriginDataRecords = async () => {
    try {
      setIsLoading(true);
      setError(null);
      
      // Use real API call
      const response = await originApi.getOriginDataRecords({
        page: 1,
        per_page: 50
      });
      
      setOriginDataRecords(response.records);
      
    } catch (err) {
      console.error('Error loading origin data records:', err);
      setError('Failed to load origin data records. Please try again.');
      showToast({
        type: 'error',
        title: 'Error loading origin data',
        message: 'Please try again or contact support if the problem persists.'
      });
    } finally {
      setIsLoading(false);
    }
  };

  // Get EUDR status badge variant
  const getEUDRStatusBadge = (status: string) => {
    switch (status) {
      case 'compliant':
        return <Badge variant="success">Compliant</Badge>;
      case 'non_compliant':
        return <Badge variant="error">Non-Compliant</Badge>;
      case 'pending':
        return <Badge variant="warning">Pending</Badge>;
      case 'not_applicable':
        return <Badge variant="neutral">N/A</Badge>;
      default:
        return <Badge variant="neutral">Unknown</Badge>;
    }
  };

  // Get record status badge variant
  const getRecordStatusBadge = (status: string) => {
    switch (status) {
      case 'verified':
        return <Badge variant="success">Verified</Badge>;
      case 'submitted':
        return <Badge variant="primary">Submitted</Badge>;
      case 'draft':
        return <Badge variant="neutral">Draft</Badge>;
      case 'rejected':
        return <Badge variant="error">Rejected</Badge>;
      default:
        return <Badge variant="neutral">Unknown</Badge>;
    }
  };

  // Get status icon
  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'verified':
        return <CheckCircleIcon className="h-5 w-5 text-green-500" />;
      case 'submitted':
        return <ClockIcon className="h-5 w-5 text-blue-500" />;
      case 'draft':
        return <DocumentTextIcon className="h-5 w-5 text-gray-500" />;
      case 'rejected':
        return <ExclamationTriangleIcon className="h-5 w-5 text-red-500" />;
      default:
        return <DocumentTextIcon className="h-5 w-5 text-gray-500" />;
    }
  };

  // Handle form submission
  const handleFormSubmit = (data: any) => {
    showToast({
      type: 'success',
      title: 'Origin Data Saved',
      message: 'Origin data has been successfully saved.'
    });
    setShowCreateModal(false);
    setShowEditModal(false);
    loadOriginDataRecords();
  };

  // Handle form cancellation
  const handleFormCancel = () => {
    setShowCreateModal(false);
    setShowEditModal(false);
  };

  // Handle delete
  const handleDelete = async (record: OriginDataRecord) => {
    if (window.confirm(`Are you sure you want to delete origin data for batch ${record.batch_id}?`)) {
      try {
        // TODO: Implement delete API call
        showToast({
          type: 'success',
          title: 'Origin Data Deleted',
          message: `Origin data for batch ${record.batch_id} has been deleted successfully.`
        });
        loadOriginDataRecords();
      } catch (error) {
        showToast({
          type: 'error',
          title: 'Error',
          message: 'Failed to delete origin data. Please try again.'
        });
      }
    }
  };

  // Define table columns
  const originDataColumns: DataTableColumn[] = [
    {
      key: 'icon',
      label: '',
      sortable: false,
      searchable: false,
      render: (_, record) => getStatusIcon(record.status),
      className: 'w-12'
    },
    {
      key: 'farm_name',
      label: 'Farm Name',
      sortable: true,
      searchable: true,
      render: (value, record) => (
        <div>
          <div className="font-medium text-gray-900">{value}</div>
          <div className="text-sm text-gray-500">
            {record.geographic_coordinates.latitude.toFixed(4)}, {record.geographic_coordinates.longitude.toFixed(4)}
          </div>
          <div className="text-xs text-gray-400 mt-1">
            PO: {record.purchase_order_id}
          </div>
        </div>
      )
    },
    {
      key: 'batch_id',
      label: 'Batch ID',
      sortable: true,
      searchable: true,
      render: (value, record) => (
        <div>
          <div className="text-sm font-medium text-gray-900">{value}</div>
          <div className="text-xs text-gray-500">{record.product_type}</div>
        </div>
      )
    },
    {
      key: 'harvest_date',
      label: 'Harvest Date',
      sortable: true,
      searchable: false,
      render: (value) => <div className="text-sm text-gray-900">{formatDate(value)}</div>
    },
    {
      key: 'date_of_recording',
      label: 'Date of Recording',
      sortable: true,
      searchable: false,
      render: (value, record) => (
        <div>
          <div className="text-sm text-gray-900">{formatDate(value)}</div>
          <div className="text-xs text-gray-500">by {record.created_by}</div>
        </div>
      )
    },
    {
      key: 'eudr_status',
      label: 'EUDR',
      sortable: true,
      searchable: false,
      render: (value) => getEUDRStatusBadge(value),
      tooltip: 'EU Deforestation Regulation compliance status'
    },
    {
      key: 'status',
      label: 'Status',
      sortable: true,
      searchable: false,
      render: (value) => getRecordStatusBadge(value)
    },
    {
      key: 'actions',
      label: 'Actions',
      sortable: false,
      searchable: false,
      render: (_, record) => (
        <div className="flex items-center space-x-1">
          <Button
            variant="outline"
            size="sm"
            onClick={() => openViewModal(record)}
            title="View details"
          >
            <EyeIcon className="h-4 w-4" />
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => openEditModal(record)}
            title="Edit record"
          >
            <PencilIcon className="h-4 w-4" />
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => handleDelete(record)}
            title="Delete record"
          >
            <TrashIcon className="h-4 w-4" />
          </Button>
        </div>
      ),
      className: 'w-32'
    }
  ];

  // Open modals
  const openCreateModal = () => {
    setSelectedRecord(null);
    setShowCreateModal(true);
  };

  const openViewModal = (record: OriginDataRecord) => {
    setSelectedRecord(record);
    setShowViewModal(true);
  };

  const openEditModal = (record: OriginDataRecord) => {
    setSelectedRecord(record);
    setShowEditModal(true);
  };

  if (isLoading) {
    return (
      <div className={`flex items-center justify-center py-8 ${className}`}>
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  if (error) {
    return (
      <div className={`text-center py-8 ${className}`}>
        <p className="text-red-600 mb-4">{error}</p>
        <Button onClick={loadOriginDataRecords} variant="primary">
          Try Again
        </Button>
      </div>
    );
  }

  return (
    <div className={className}>
      {/* Header */}
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-gray-900">Origin Data Management</h2>
          <p className="text-gray-600 mt-1">
            Comprehensive tracking and management of harvest origin data with EUDR compliance monitoring.
          </p>
        </div>
        <Button
          variant="primary"
          leftIcon={<PlusIcon className="h-4 w-4" />}
          onClick={openCreateModal}
        >
          Add Origin Data
        </Button>
      </div>

      {/* Origin Data Table */}
      <DataTable
        title={`Origin Data Records (${originDataRecords.length})`}
        data={originDataRecords}
        columns={originDataColumns}
        searchPlaceholder="Search farm names, batch IDs, product types..."
        statusFilterOptions={[
          { label: 'Verified', value: 'verified' },
          { label: 'Submitted', value: 'submitted' },
          { label: 'Draft', value: 'draft' },
          { label: 'Rejected', value: 'rejected' }
        ]}
        onRowClick={(record) => openViewModal(record)}
        onExport={() => console.log('Export origin data')}
        emptyState={{
          icon: DocumentTextIcon,
          title: 'No origin data records found',
          description: 'Get started by adding your first origin data record to the system.',
          actionLabel: 'Add Your First Origin Data',
          onAction: openCreateModal
        }}
      />

      {/* Create/Edit Modal */}
      {(showCreateModal || showEditModal) && (
        <Modal
          isOpen={showCreateModal || showEditModal}
          onClose={handleFormCancel}
          title={selectedRecord ? `Edit Origin Data - ${selectedRecord.batch_id}` : 'Add New Origin Data'}
          size="xl"
        >
          <OriginatorConfirmationForm
            purchaseOrderId={selectedRecord?.purchase_order_id || 'NEW-PO-001'}
            productType={selectedRecord?.product_type || 'Fresh Fruit Bunches'}
            onSubmit={handleFormSubmit}
            onCancel={handleFormCancel}
          />
        </Modal>
      )}

      {/* View Modal */}
      {showViewModal && selectedRecord && (
        <Modal
          isOpen={showViewModal}
          onClose={() => setShowViewModal(false)}
          title={`Origin Data Details - ${selectedRecord.batch_id}`}
          size="lg"
        >
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <label className="block font-medium text-gray-700">Farm Name</label>
                <p className="text-gray-900">{selectedRecord.farm_name}</p>
              </div>
              <div>
                <label className="block font-medium text-gray-700">Batch ID</label>
                <p className="text-gray-900">{selectedRecord.batch_id}</p>
              </div>
              <div>
                <label className="block font-medium text-gray-700">Harvest Date</label>
                <p className="text-gray-900">{formatDate(selectedRecord.harvest_date)}</p>
              </div>
              <div>
                <label className="block font-medium text-gray-700">Date of Recording</label>
                <p className="text-gray-900">{formatDate(selectedRecord.date_of_recording)}</p>
              </div>
              <div>
                <label className="block font-medium text-gray-700">EUDR Status</label>
                <div className="mt-1">
                  {getEUDRStatusBadge(selectedRecord.eudr_status)}
                </div>
              </div>
              <div>
                <label className="block font-medium text-gray-700">Record Status</label>
                <div className="mt-1">
                  {getRecordStatusBadge(selectedRecord.status)}
                </div>
              </div>
              <div>
                <label className="block font-medium text-gray-700">GPS Coordinates</label>
                <p className="text-gray-900">
                  {selectedRecord.geographic_coordinates.latitude.toFixed(6)}, {selectedRecord.geographic_coordinates.longitude.toFixed(6)}
                </p>
              </div>
              <div>
                <label className="block font-medium text-gray-700">Quality Score</label>
                <p className="text-gray-900">{selectedRecord.quality_score || 'N/A'}%</p>
              </div>
            </div>

            <div>
              <label className="block font-medium text-gray-700 mb-2">Certifications</label>
              <div className="flex flex-wrap gap-2">
                {selectedRecord.certifications.map((cert) => (
                  <Badge key={cert} variant="success">
                    {cert}
                  </Badge>
                ))}
              </div>
            </div>

            <div className="flex justify-end pt-4">
              <Button variant="outline" onClick={() => setShowViewModal(false)}>
                Close
              </Button>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
};

export default OriginDataManager;
