/**
 * Business Relationship Management Interface
 * Manage supplier/customer relationships and data sharing
 */
import React, { useState, useEffect } from 'react';
import { 
  UsersIcon,
  BuildingOfficeIcon,
  Cog6ToothIcon,
  EyeIcon,
  PencilIcon,
  TrashIcon,
  PlusIcon,
  FunnelIcon,
  MagnifyingGlassIcon,
  ChartBarIcon,
} from '@heroicons/react/24/outline';
import { BusinessRelationship, DataSharingPermissions } from '../../types/onboarding';
import { onboardingApi } from '../../lib/onboardingApi';
import { Card, CardHeader, CardBody } from '../ui/Card';
import Button from '../ui/Button';
import Input from '../ui/Input';
import Select from '../ui/Select';
import Badge from '../ui/Badge';
import SupplierAddForm from './SupplierInvitationForm';
import DataSharingPermissionsModal from './DataSharingPermissionsModal';
import { cn, formatCurrency, formatDate } from '../../lib/utils';

interface RelationshipManagementProps {
  companyId: string;
  onInviteSupplier?: () => void;
  className?: string;
}

const RelationshipManagement: React.FC<RelationshipManagementProps> = ({
  companyId,
  onInviteSupplier,
  className,
}) => {
  const [relationships, setRelationships] = useState<BusinessRelationship[]>([]);
  const [filteredRelationships, setFilteredRelationships] = useState<BusinessRelationship[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [showInviteForm, setShowInviteForm] = useState(false);
  const [showPermissionsModal, setShowPermissionsModal] = useState(false);
  const [selectedRelationship, setSelectedRelationship] = useState<BusinessRelationship | null>(null);
  
  // Filters
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [typeFilter, setTypeFilter] = useState<string>('all');
  const [sortBy, setSortBy] = useState<'name' | 'date' | 'value' | 'transparency'>('name');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('asc');

  // Load relationships
  useEffect(() => {
    loadRelationships();
  }, [companyId]);

  // Apply filters
  useEffect(() => {
    let filtered = [...relationships];

    // Search filter
    if (searchTerm) {
      filtered = filtered.filter(rel => 
        rel.buyer_company_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        rel.seller_company_name.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    // Status filter
    if (statusFilter !== 'all') {
      filtered = filtered.filter(rel => rel.status === statusFilter);
    }

    // Type filter
    if (typeFilter !== 'all') {
      filtered = filtered.filter(rel => rel.relationship_type === typeFilter);
    }

    // Sort
    filtered.sort((a, b) => {
      let aValue: any, bValue: any;
      
      switch (sortBy) {
        case 'name':
          aValue = a.seller_company_name;
          bValue = b.seller_company_name;
          break;
        case 'date':
          aValue = new Date(a.established_at);
          bValue = new Date(b.established_at);
          break;
        case 'value':
          aValue = a.total_value;
          bValue = b.total_value;
          break;
        case 'transparency':
          aValue = a.transparency_score || 0;
          bValue = b.transparency_score || 0;
          break;
        default:
          aValue = a.seller_company_name;
          bValue = b.seller_company_name;
      }

      if (typeof aValue === 'string') {
        return sortOrder === 'asc' 
          ? aValue.localeCompare(bValue)
          : bValue.localeCompare(aValue);
      }

      return sortOrder === 'asc' ? aValue - bValue : bValue - aValue;
    });

    setFilteredRelationships(filtered);
  }, [relationships, searchTerm, statusFilter, typeFilter, sortBy, sortOrder]);

  const loadRelationships = async () => {
    setIsLoading(true);
    try {
      const data = await onboardingApi.getBusinessRelationships(companyId);
      setRelationships(data);
    } catch (error) {
      console.error('Failed to load relationships:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleInvitationSent = () => {
    setShowInviteForm(false);
    loadRelationships();
    if (onInviteSupplier) {
      onInviteSupplier();
    }
  };

  const handlePermissionsUpdate = async (permissions: DataSharingPermissions) => {
    if (!selectedRelationship) return;

    try {
      await onboardingApi.updateDataSharingPermissions(selectedRelationship.id, permissions);
      setShowPermissionsModal(false);
      setSelectedRelationship(null);
      loadRelationships();
    } catch (error) {
      console.error('Failed to update permissions:', error);
    }
  };

  const getStatusBadgeVariant = (status: string) => {
    switch (status) {
      case 'active': return 'success';
      case 'pending': return 'warning';
      case 'suspended': return 'error';
      case 'terminated': return 'neutral';
      default: return 'neutral';
    }
  };

  const getRelationshipTypeIcon = (type: string) => {
    switch (type) {
      case 'supplier': return '🏭';
      case 'customer': return '🏪';
      case 'partner': return '🤝';
      default: return '🔗';
    }
  };

  const getTransparencyColor = (score?: number) => {
    if (!score) return 'text-neutral-400';
    if (score >= 80) return 'text-success-600';
    if (score >= 60) return 'text-warning-600';
    return 'text-error-600';
  };

  if (showInviteForm) {
    return (
      <SupplierAddForm
        onInvitationSent={handleInvitationSent}
        onCancel={() => setShowInviteForm(false)}
        className={className}
      />
    );
  }

  return (
    <div className={className}>
      <Card>
        <CardHeader
          title="Business Relationships"
          subtitle={`${relationships.length} active relationships`}
          action={
            <div className="flex items-center space-x-2">
              <UsersIcon className="h-5 w-5 text-neutral-400" />
              <Button
                variant="primary"
                onClick={() => setShowInviteForm(true)}
                leftIcon={<PlusIcon className="h-4 w-4" />}
              >
                Add Supplier
              </Button>
            </div>
          }
        />
        
        <CardBody>
          {/* Filters and Search */}
          <div className="mb-6 space-y-4">
            <div className="flex flex-col sm:flex-row gap-4">
              <div className="flex-1">
                <Input
                  placeholder="Search companies..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  leftIcon={<MagnifyingGlassIcon className="h-4 w-4" />}
                />
              </div>
              
              <div className="flex gap-2">
                <Select
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value)}
                  options={[
                    { label: 'All Status', value: 'all' },
                    { label: 'Active', value: 'active' },
                    { label: 'Pending', value: 'pending' },
                    { label: 'Suspended', value: 'suspended' },
                    { label: 'Terminated', value: 'terminated' }
                  ]}
                />

                <Select
                  value={typeFilter}
                  onChange={(e) => setTypeFilter(e.target.value)}
                  options={[
                    { label: 'All Types', value: 'all' },
                    { label: 'Suppliers', value: 'supplier' },
                    { label: 'Customers', value: 'customer' },
                    { label: 'Partners', value: 'partner' }
                  ]}
                />

                <Select
                  value={`${sortBy}-${sortOrder}`}
                  onChange={(e) => {
                    const [field, order] = e.target.value.split('-');
                    setSortBy(field as any);
                    setSortOrder(order as any);
                  }}
                  options={[
                    { label: 'Name A-Z', value: 'name-asc' },
                    { label: 'Name Z-A', value: 'name-desc' },
                    { label: 'Newest First', value: 'date-desc' },
                    { label: 'Oldest First', value: 'date-asc' },
                    { label: 'Highest Value', value: 'value-desc' },
                    { label: 'Best Transparency', value: 'transparency-desc' }
                  ]}
                />
              </div>
            </div>
          </div>

          {/* Relationships List */}
          {isLoading ? (
            <div className="text-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600 mx-auto"></div>
              <p className="mt-2 text-neutral-600">Loading relationships...</p>
            </div>
          ) : filteredRelationships.length === 0 ? (
            <div className="text-center py-8">
              <UsersIcon className="h-12 w-12 text-neutral-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-neutral-900 mb-2">
                {relationships.length === 0 ? 'No relationships yet' : 'No matching relationships'}
              </h3>
              <p className="text-neutral-600 mb-4">
                {relationships.length === 0
                  ? 'Start building your supply chain network by adding suppliers.'
                  : 'Try adjusting your search or filter criteria.'
                }
              </p>
              {relationships.length === 0 && (
                <Button
                  variant="primary"
                  onClick={() => setShowInviteForm(true)}
                  leftIcon={<PlusIcon className="h-4 w-4" />}
                >
                  Add Your First Supplier
                </Button>
              )}
            </div>
          ) : (
            <div className="space-y-4">
              {filteredRelationships.map((relationship) => (
                <div
                  key={relationship.id}
                  className="border border-neutral-200 rounded-lg p-4 hover:shadow-md transition-shadow"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex items-start space-x-3 flex-1">
                      <div className="text-2xl">
                        {getRelationshipTypeIcon(relationship.relationship_type)}
                      </div>
                      
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center space-x-2 mb-1">
                          <h3 className="font-medium text-neutral-900 truncate">
                            {relationship.seller_company_name}
                          </h3>
                          <Badge 
                            variant={getStatusBadgeVariant(relationship.status)}
                            size="sm"
                          >
                            {relationship.status}
                          </Badge>
                          <Badge variant="neutral" size="sm">
                            {relationship.relationship_type}
                          </Badge>
                        </div>
                        
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-2 text-sm">
                          <div>
                            <span className="text-neutral-600">Orders:</span>
                            <span className="ml-1 font-medium">{relationship.total_orders}</span>
                          </div>
                          <div>
                            <span className="text-neutral-600">Value:</span>
                            <span className="ml-1 font-medium">
                              {formatCurrency(relationship.total_value)}
                            </span>
                          </div>
                          <div>
                            <span className="text-neutral-600">Since:</span>
                            <span className="ml-1 font-medium">
                              {formatDate(relationship.established_at)}
                            </span>
                          </div>
                          <div>
                            <span className="text-neutral-600">Transparency:</span>
                            <span className={cn(
                              'ml-1 font-medium',
                              getTransparencyColor(relationship.transparency_score)
                            )}>
                              {relationship.transparency_score 
                                ? `${relationship.transparency_score.toFixed(1)}%`
                                : 'N/A'
                              }
                            </span>
                          </div>
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center space-x-2 ml-4">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => {
                          setSelectedRelationship(relationship);
                          setShowPermissionsModal(true);
                        }}
                        leftIcon={<Cog6ToothIcon className="h-4 w-4" />}
                      >
                        Permissions
                      </Button>
                      
                      <Button
                        variant="outline"
                        size="sm"
                        leftIcon={<ChartBarIcon className="h-4 w-4" />}
                      >
                        Analytics
                      </Button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardBody>
      </Card>

      {/* Data Sharing Permissions Modal */}
      {showPermissionsModal && selectedRelationship && (
        <DataSharingPermissionsModal
          relationship={selectedRelationship}
          onSave={handlePermissionsUpdate}
          onCancel={() => {
            setShowPermissionsModal(false);
            setSelectedRelationship(null);
          }}
        />
      )}
    </div>
  );
};

export default RelationshipManagement;
