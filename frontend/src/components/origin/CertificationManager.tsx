/**
 * Certification Manager Component
 * Comprehensive certification management for sustainability standards
 */
import React, { useState, useEffect } from 'react';
import {
  ShieldCheckIcon,
  CalendarIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  ClockIcon,
  DocumentTextIcon,
  PlusIcon,
  PencilIcon,
  EyeIcon,
  ArrowPathIcon
} from '@heroicons/react/24/outline';
import { Card, CardHeader, CardBody } from '../ui/Card';
import Input from '../ui/Input';
import Select from '../ui/Select';
import TextArea from '../ui/Textarea';
import Button from '../ui/Button';
import Badge from '../ui/Badge';
import Modal from '../ui/Modal';
import LoadingSpinner from '../ui/LoadingSpinner';
import { useToast } from '../../contexts/ToastContext';
import { formatDate } from '../../lib/utils';

interface Certification {
  id: string;
  certification_type: string;
  certification_body: string;
  certificate_number: string;
  issue_date: string;
  expiry_date: string;
  status: 'active' | 'expiring' | 'expired' | 'pending' | 'suspended';
  coverage_scope: string;
  coverage_percentage: number;
  farm_ids: string[];
  document_url?: string;
  renewal_reminder_sent: boolean;
  notes?: string;
  last_audit_date?: string;
  next_audit_date?: string;
}

interface CertificationManagerProps {
  companyId?: string;
  className?: string;
}

const CertificationManager: React.FC<CertificationManagerProps> = ({
  companyId,
  className = ''
}) => {
  const { showToast } = useToast();
  
  // State
  const [certifications, setCertifications] = useState<Certification[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedCertification, setSelectedCertification] = useState<Certification | null>(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showViewModal, setShowViewModal] = useState(false);
  const [filterStatus, setFilterStatus] = useState('');

  // Form state
  const [formData, setFormData] = useState<Partial<Certification>>({
    certification_type: '',
    certification_body: '',
    certificate_number: '',
    issue_date: '',
    expiry_date: '',
    status: 'active',
    coverage_scope: '',
    coverage_percentage: 0,
    farm_ids: [],
    notes: ''
  });

  // Certification types and bodies
  const certificationTypes = [
    {
      type: 'RSPO',
      name: 'Roundtable on Sustainable Palm Oil',
      bodies: ['RSPO Secretariat', 'Control Union', 'SGS', 'Bureau Veritas'],
      description: 'Global standard for sustainable palm oil production'
    },
    {
      type: 'NDPE',
      name: 'No Deforestation, No Peat, No Exploitation',
      bodies: ['TFT', 'Proforest', 'Earthworm Foundation'],
      description: 'Commitment to responsible sourcing practices'
    },
    {
      type: 'ISPO',
      name: 'Indonesian Sustainable Palm Oil',
      bodies: ['ISPO Commission', 'Sucofindo', 'SGS Indonesia'],
      description: 'Indonesian national standard for palm oil'
    },
    {
      type: 'MSPO',
      name: 'Malaysian Sustainable Palm Oil',
      bodies: ['MPOCC', 'SIRIM QAS', 'SGS Malaysia'],
      description: 'Malaysian national certification scheme'
    },
    {
      type: 'Rainforest Alliance',
      name: 'Rainforest Alliance Certified',
      bodies: ['Rainforest Alliance', 'SCS Global Services'],
      description: 'Environmental and social sustainability standard'
    },
    {
      type: 'ISCC',
      name: 'International Sustainability & Carbon Certification',
      bodies: ['ISCC System', 'Control Union', 'SGS'],
      description: 'Sustainability certification for biomass and bioenergy'
    }
  ];

  // Load certifications
  useEffect(() => {
    loadCertifications();
  }, [companyId]);

  const loadCertifications = async () => {
    try {
      setIsLoading(true);
      setError(null);
      
      // TODO: Replace with actual API call
      // Simulated data for now
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      const mockCertifications: Certification[] = [
        {
          id: '1',
          certification_type: 'RSPO',
          certification_body: 'Control Union',
          certificate_number: 'RSPO-2024-001',
          issue_date: '2024-01-15',
          expiry_date: '2025-12-15',
          status: 'active',
          coverage_scope: 'All palm oil production facilities',
          coverage_percentage: 85,
          farm_ids: ['FARM-KAL-001', 'FARM-KAL-002'],
          renewal_reminder_sent: false,
          last_audit_date: '2024-01-10',
          next_audit_date: '2025-01-10',
          notes: 'Annual surveillance audit completed successfully'
        },
        {
          id: '2',
          certification_type: 'NDPE',
          certification_body: 'TFT',
          certificate_number: 'NDPE-2024-002',
          issue_date: '2024-03-20',
          expiry_date: '2025-03-20',
          status: 'expiring',
          coverage_scope: 'Kalimantan operations',
          coverage_percentage: 60,
          farm_ids: ['FARM-KAL-001'],
          renewal_reminder_sent: true,
          notes: 'Renewal process initiated'
        },
        {
          id: '3',
          certification_type: 'ISPO',
          certification_body: 'ISPO Commission',
          certificate_number: 'ISPO-2023-003',
          issue_date: '2023-06-30',
          expiry_date: '2026-06-30',
          status: 'active',
          coverage_scope: 'Sumatra smallholder cooperative',
          coverage_percentage: 40,
          farm_ids: ['FARM-SUM-001'],
          renewal_reminder_sent: false,
          last_audit_date: '2023-06-25',
          next_audit_date: '2024-06-25'
        },
        {
          id: '4',
          certification_type: 'Rainforest Alliance',
          certification_body: 'Rainforest Alliance',
          certificate_number: 'RA-2024-004',
          issue_date: '2024-08-15',
          expiry_date: '2027-08-15',
          status: 'pending',
          coverage_scope: 'New plantation areas',
          coverage_percentage: 25,
          farm_ids: ['FARM-SUM-001'],
          renewal_reminder_sent: false,
          notes: 'Initial certification in progress'
        }
      ];
      
      setCertifications(mockCertifications);
      
    } catch (err) {
      console.error('Error loading certifications:', err);
      setError('Failed to load certification data. Please try again.');
      showToast({
        type: 'error',
        title: 'Error loading certifications',
        message: 'Please try again or contact support if the problem persists.'
      });
    } finally {
      setIsLoading(false);
    }
  };

  // Calculate days until expiry
  const getDaysUntilExpiry = (expiryDate: string): number => {
    const today = new Date();
    const expiry = new Date(expiryDate);
    const diffTime = expiry.getTime() - today.getTime();
    return Math.ceil(diffTime / (1000 * 60 * 60 * 24));
  };

  // Get status badge variant
  const getStatusBadgeVariant = (status: string) => {
    switch (status) {
      case 'active':
        return 'success';
      case 'expiring':
        return 'warning';
      case 'expired':
        return 'error';
      case 'pending':
        return 'neutral';
      case 'suspended':
        return 'error';
      default:
        return 'neutral';
    }
  };

  // Get status icon
  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'active':
        return <CheckCircleIcon className="h-5 w-5 text-green-500" />;
      case 'expiring':
        return <ExclamationTriangleIcon className="h-5 w-5 text-yellow-500" />;
      case 'expired':
        return <ExclamationTriangleIcon className="h-5 w-5 text-red-500" />;
      case 'pending':
        return <ClockIcon className="h-5 w-5 text-gray-500" />;
      case 'suspended':
        return <ExclamationTriangleIcon className="h-5 w-5 text-red-500" />;
      default:
        return <ShieldCheckIcon className="h-5 w-5 text-gray-500" />;
    }
  };

  // Filter certifications
  const filteredCertifications = certifications.filter(cert => {
    return !filterStatus || cert.status === filterStatus;
  });

  // Get expiring certifications
  const expiringCertifications = certifications.filter(cert => {
    const daysUntilExpiry = getDaysUntilExpiry(cert.expiry_date);
    return daysUntilExpiry <= 90 && daysUntilExpiry > 0;
  });

  // Handle form submission
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    try {
      // TODO: Implement actual API call
      if (selectedCertification) {
        showToast({
          type: 'success',
          title: 'Certification Updated',
          message: `${formData.certification_type} certification has been updated successfully.`
        });
      } else {
        showToast({
          type: 'success',
          title: 'Certification Added',
          message: `${formData.certification_type} certification has been added successfully.`
        });
      }
      
      setShowCreateModal(false);
      setShowEditModal(false);
      loadCertifications();
      
    } catch (error) {
      showToast({
        type: 'error',
        title: 'Error',
        message: 'Failed to save certification. Please try again.'
      });
    }
  };

  // Open modals
  const openCreateModal = () => {
    setFormData({
      certification_type: '',
      certification_body: '',
      certificate_number: '',
      issue_date: '',
      expiry_date: '',
      status: 'active',
      coverage_scope: '',
      coverage_percentage: 0,
      farm_ids: [],
      notes: ''
    });
    setSelectedCertification(null);
    setShowCreateModal(true);
  };

  const openEditModal = (certification: Certification) => {
    setFormData(certification);
    setSelectedCertification(certification);
    setShowEditModal(true);
  };

  const openViewModal = (certification: Certification) => {
    setSelectedCertification(certification);
    setShowViewModal(true);
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
        <Button onClick={loadCertifications} variant="primary">
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
          <h2 className="text-xl font-bold text-gray-900">Certification Management</h2>
          <p className="text-gray-600 mt-1">
            Manage sustainability certifications and track renewal dates.
          </p>
        </div>
        <Button
          variant="primary"
          leftIcon={<PlusIcon className="h-4 w-4" />}
          onClick={openCreateModal}
        >
          Add Certification
        </Button>
      </div>

      {/* Alerts for expiring certifications */}
      {expiringCertifications.length > 0 && (
        <Card className="mb-6 border-yellow-200 bg-yellow-50">
          <CardBody>
            <div className="flex items-start space-x-3">
              <ExclamationTriangleIcon className="h-5 w-5 text-yellow-500 mt-0.5" />
              <div>
                <h3 className="font-medium text-yellow-800">Certifications Expiring Soon</h3>
                <div className="mt-2 space-y-1">
                  {expiringCertifications.map((cert) => (
                    <p key={cert.id} className="text-sm text-yellow-700">
                      <span className="font-medium">{cert.certification_type}</span> expires in{' '}
                      {getDaysUntilExpiry(cert.expiry_date)} days ({formatDate(cert.expiry_date)})
                    </p>
                  ))}
                </div>
              </div>
            </div>
          </CardBody>
        </Card>
      )}

      {/* Filters */}
      <Card className="mb-6">
        <CardBody>
          <div className="flex items-center space-x-4">
            <Select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
              options={[
                { label: 'All Status', value: '' },
                { label: 'Active', value: 'active' },
                { label: 'Expiring', value: 'expiring' },
                { label: 'Expired', value: 'expired' },
                { label: 'Pending', value: 'pending' },
                { label: 'Suspended', value: 'suspended' }
              ]}
            />
            <Button
              variant="outline"
              leftIcon={<ArrowPathIcon className="h-4 w-4" />}
              onClick={loadCertifications}
            >
              Refresh
            </Button>
          </div>
        </CardBody>
      </Card>

      {/* Certifications List */}
      <Card>
        <CardHeader title={`Certifications (${filteredCertifications.length})`} />
        <CardBody padding="none">
          {filteredCertifications.length === 0 ? (
            <div className="text-center py-12">
              <ShieldCheckIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-600 mb-4">No certifications found</p>
              <Button onClick={openCreateModal} variant="primary">
                Add Your First Certification
              </Button>
            </div>
          ) : (
            <div className="divide-y divide-gray-200">
              {filteredCertifications.map((cert) => {
                const daysUntilExpiry = getDaysUntilExpiry(cert.expiry_date);
                const certType = certificationTypes.find(t => t.type === cert.certification_type);
                
                return (
                  <div key={cert.id} className="p-6 hover:bg-gray-50">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center space-x-3 mb-2">
                          {getStatusIcon(cert.status)}
                          <h3 className="text-lg font-medium text-gray-900">
                            {cert.certification_type}
                          </h3>
                          <Badge variant={getStatusBadgeVariant(cert.status)}>
                            {cert.status.charAt(0).toUpperCase() + cert.status.slice(1)}
                          </Badge>
                        </div>
                        
                        <div className="text-sm text-gray-600 mb-3">
                          <span className="font-medium">Certificate:</span> {cert.certificate_number} • 
                          <span className="font-medium ml-2">Body:</span> {cert.certification_body}
                        </div>

                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm mb-3">
                          <div>
                            <span className="text-gray-500">Issue Date:</span>
                            <span className="ml-1 font-medium">{formatDate(cert.issue_date)}</span>
                          </div>
                          <div>
                            <span className="text-gray-500">Expiry Date:</span>
                            <span className={`ml-1 font-medium ${
                              daysUntilExpiry <= 30 ? 'text-red-600' :
                              daysUntilExpiry <= 90 ? 'text-yellow-600' : 'text-gray-900'
                            }`}>
                              {formatDate(cert.expiry_date)}
                            </span>
                          </div>
                          <div>
                            <span className="text-gray-500">Coverage:</span>
                            <span className="ml-1 font-medium">{cert.coverage_percentage}%</span>
                          </div>
                          <div>
                            <span className="text-gray-500">Farms:</span>
                            <span className="ml-1 font-medium">{cert.farm_ids.length}</span>
                          </div>
                        </div>

                        <div className="text-sm text-gray-600">
                          <span className="font-medium">Scope:</span> {cert.coverage_scope}
                        </div>

                        {cert.notes && (
                          <div className="mt-2 text-sm text-gray-600">
                            <span className="font-medium">Notes:</span> {cert.notes}
                          </div>
                        )}
                      </div>

                      <div className="flex items-center space-x-2 ml-4">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => openViewModal(cert)}
                        >
                          <EyeIcon className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => openEditModal(cert)}
                        >
                          <PencilIcon className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </CardBody>
      </Card>

      {/* Create/Edit Modal */}
      {(showCreateModal || showEditModal) && (
        <Modal
          isOpen={showCreateModal || showEditModal}
          onClose={() => {
            setShowCreateModal(false);
            setShowEditModal(false);
          }}
          title={selectedCertification ? `Edit ${selectedCertification.certification_type} Certification` : 'Add New Certification'}
        >
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Select
                label="Certification Type"
                value={formData.certification_type || ''}
                onChange={(e) => setFormData(prev => ({ ...prev, certification_type: e.target.value }))}
                options={[
                  { label: 'Select certification type', value: '' },
                  ...certificationTypes.map(type => ({ label: type.name, value: type.type }))
                ]}
                required
              />
              <Input
                label="Certificate Number"
                type="text"
                value={formData.certificate_number || ''}
                onChange={(e) => setFormData(prev => ({ ...prev, certificate_number: e.target.value }))}
                required
                placeholder="CERT-2024-001"
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Input
                label="Issue Date"
                type="date"
                value={formData.issue_date || ''}
                onChange={(e) => setFormData(prev => ({ ...prev, issue_date: e.target.value }))}
                required
              />
              <Input
                label="Expiry Date"
                type="date"
                value={formData.expiry_date || ''}
                onChange={(e) => setFormData(prev => ({ ...prev, expiry_date: e.target.value }))}
                required
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Select
                label="Certification Body"
                value={formData.certification_body || ''}
                onChange={(e) => setFormData(prev => ({ ...prev, certification_body: e.target.value }))}
                options={[
                  { label: 'Select certification body', value: '' },
                  ...(formData.certification_type ? 
                    certificationTypes.find(t => t.type === formData.certification_type)?.bodies.map(body => ({ label: body, value: body })) || []
                    : []
                  )
                ]}
                required
              />
              <Input
                label="Coverage Percentage"
                type="number"
                min="0"
                max="100"
                value={formData.coverage_percentage || ''}
                onChange={(e) => setFormData(prev => ({ ...prev, coverage_percentage: parseInt(e.target.value) }))}
                required
              />
            </div>

            <Input
              label="Coverage Scope"
              type="text"
              value={formData.coverage_scope || ''}
              onChange={(e) => setFormData(prev => ({ ...prev, coverage_scope: e.target.value }))}
              placeholder="Description of what this certification covers"
              required
            />

            <TextArea
              label="Notes"
              value={formData.notes || ''}
              onChange={(e) => setFormData(prev => ({ ...prev, notes: e.target.value }))}
              placeholder="Additional notes about this certification"
              rows={3}
            />

            <div className="flex justify-end space-x-3 pt-4">
              <Button
                type="button"
                variant="outline"
                onClick={() => {
                  setShowCreateModal(false);
                  setShowEditModal(false);
                }}
              >
                Cancel
              </Button>
              <Button
                type="submit"
                variant="primary"
                leftIcon={<CheckCircleIcon className="h-4 w-4" />}
              >
                {selectedCertification ? 'Update Certification' : 'Add Certification'}
              </Button>
            </div>
          </form>
        </Modal>
      )}

      {/* View Modal */}
      {showViewModal && selectedCertification && (
        <Modal
          isOpen={showViewModal}
          onClose={() => setShowViewModal(false)}
          title={`${selectedCertification.certification_type} Certification Details`}
        >
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <label className="block font-medium text-gray-700">Certificate Number</label>
                <p className="text-gray-900">{selectedCertification.certificate_number}</p>
              </div>
              <div>
                <label className="block font-medium text-gray-700">Certification Body</label>
                <p className="text-gray-900">{selectedCertification.certification_body}</p>
              </div>
              <div>
                <label className="block font-medium text-gray-700">Issue Date</label>
                <p className="text-gray-900">{formatDate(selectedCertification.issue_date)}</p>
              </div>
              <div>
                <label className="block font-medium text-gray-700">Expiry Date</label>
                <p className="text-gray-900">{formatDate(selectedCertification.expiry_date)}</p>
              </div>
              <div>
                <label className="block font-medium text-gray-700">Coverage</label>
                <p className="text-gray-900">{selectedCertification.coverage_percentage}%</p>
              </div>
              <div>
                <label className="block font-medium text-gray-700">Status</label>
                <Badge variant={getStatusBadgeVariant(selectedCertification.status)}>
                  {selectedCertification.status.charAt(0).toUpperCase() + selectedCertification.status.slice(1)}
                </Badge>
              </div>
            </div>

            <div>
              <label className="block font-medium text-gray-700 mb-2">Coverage Scope</label>
              <p className="text-gray-900">{selectedCertification.coverage_scope}</p>
            </div>

            {selectedCertification.notes && (
              <div>
                <label className="block font-medium text-gray-700 mb-2">Notes</label>
                <p className="text-gray-900">{selectedCertification.notes}</p>
              </div>
            )}

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

export default CertificationManager;
