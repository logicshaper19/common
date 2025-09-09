/**
 * Supplier Onboarding Dashboard Page
 * Main interface for supplier onboarding and relationship management
 */
import React, { useState, useEffect } from 'react';
import {
  UserPlusIcon,
  UsersIcon,
  ChartBarIcon,
  PlusIcon,
  EyeIcon,
} from '@heroicons/react/24/outline';
import { useAuth } from '../contexts/AuthContext';
import { SupplierInvitation, BusinessRelationship } from '../types/onboarding';
import { onboardingApi } from '../lib/onboardingApi';
import { Card, CardHeader, CardBody } from '../components/ui/Card';
import Button from '../components/ui/Button';
import Badge from '../components/ui/Badge';
import AnalyticsCard from '../components/ui/AnalyticsCard';
import SupplierAddForm from '../components/onboarding/SupplierInvitationForm';
import RelationshipManagement from '../components/onboarding/RelationshipManagement';
import ViralCascadeAnalytics from '../components/onboarding/ViralCascadeAnalytics';
import { cn, formatDate } from '../lib/utils';

const SupplierOnboardingDashboard: React.FC = () => {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState<'overview' | 'add' | 'relationships' | 'analytics'>('overview');
  const [invitations, setInvitations] = useState<SupplierInvitation[]>([]);
  const [relationships, setRelationships] = useState<BusinessRelationship[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  // Load dashboard data
  useEffect(() => {
    if (user?.company?.id) {
      loadDashboardData();
    }
  }, [user?.company?.id]);

  const loadDashboardData = async () => {
    if (!user?.company?.id) return;

    setIsLoading(true);
    try {
      const [invitationsData, relationshipsData] = await Promise.all([
        onboardingApi.getSupplierInvitations(user.company.id),
        onboardingApi.getBusinessRelationships(user.company.id),
      ]);
      
      setInvitations(invitationsData);
      setRelationships(relationshipsData);
    } catch (error) {
      console.error('Failed to load dashboard data:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleInvitationSent = (invitation: SupplierInvitation) => {
    setInvitations(prev => [invitation, ...prev]);
    setActiveTab('overview');
  };

  // Get status badge variant
  const getStatusBadgeVariant = (status: string) => {
    switch (status) {
      case 'accepted':
      case 'active': return 'success';
      case 'pending': return 'warning';
      case 'declined':
      case 'expired':
      case 'terminated': return 'error';
      default: return 'neutral';
    }
  };

  // Calculate dashboard stats
  const stats = {
    totalSuppliers: invitations.length,
    pendingSuppliers: invitations.filter(inv => inv.status === 'pending').length,
    onboardedSuppliers: invitations.filter(inv => inv.status === 'accepted').length,
    activeRelationships: relationships.filter(rel => rel.status === 'active').length,
    totalRelationships: relationships.length,
    onboardingRate: invitations.length > 0
      ? (invitations.filter(inv => inv.status === 'accepted').length / invitations.length) * 100
      : 0,
  };

  // Render overview tab
  const renderOverview = () => (
    <div className="space-y-6">
      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <AnalyticsCard
          name="Total Suppliers"
          value={stats.totalSuppliers}
          icon={UsersIcon}
        />

        <AnalyticsCard
          name="Pending Onboarding"
          value={stats.pendingSuppliers}
          icon={UserPlusIcon}
        />

        <AnalyticsCard
          name="Active Relationships"
          value={stats.activeRelationships}
          icon={UsersIcon}
        />

        <AnalyticsCard
          name="Onboarding Rate"
          value={`${stats.onboardingRate.toFixed(1)}%`}
          icon={ChartBarIcon}
        />
      </div>



      {/* Recent Suppliers */}
      <Card>
        <CardHeader
          title="Recent Suppliers"
          subtitle={`${invitations.length} total suppliers added`}
          action={
            <Button
              variant="outline"
              size="sm"
              onClick={() => setActiveTab('add')}
              leftIcon={<PlusIcon className="h-4 w-4" />}
            >
              Add Supplier
            </Button>
          }
        />
        <CardBody>
          {isLoading ? (
            <div className="text-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600 mx-auto"></div>
              <p className="mt-2 text-neutral-600">Loading suppliers...</p>
            </div>
          ) : invitations.length === 0 ? (
            <div className="text-center py-8">
              <UserPlusIcon className="h-12 w-12 text-neutral-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-neutral-900 mb-2">No suppliers added yet</h3>
              <p className="text-neutral-600 mb-4">
                Start building your supply chain network by adding suppliers.
              </p>
              <Button
                variant="primary"
                onClick={() => setActiveTab('add')}
                leftIcon={<PlusIcon className="h-4 w-4" />}
              >
                Add Your First Supplier
              </Button>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-neutral-200">
                <thead className="bg-neutral-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-neutral-500 uppercase tracking-wider">
                      Supplier
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-neutral-500 uppercase tracking-wider">
                      Type
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-neutral-500 uppercase tracking-wider">
                      Status
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-neutral-500 uppercase tracking-wider">
                      Date Added
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-neutral-200">
                  {invitations.slice(0, 5).map((invitation) => (
                    <tr key={invitation.id} className="hover:bg-neutral-50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center">
                          <div className="w-10 h-10 bg-primary-100 rounded-full flex items-center justify-center">
                            <UserPlusIcon className="h-5 w-5 text-primary-600" />
                          </div>
                          <div className="ml-4">
                            <div className="text-sm font-medium text-neutral-900">
                              {invitation.supplier_name || 'Unnamed Supplier'}
                            </div>
                            <div className="text-sm text-neutral-500">
                              {invitation.supplier_email}
                            </div>
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-neutral-900">
                          {invitation.relationship_type}
                        </div>
                        <div className="text-sm text-neutral-500">
                          {invitation.company_type}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <Badge variant={getStatusBadgeVariant(invitation.status)}>
                          {invitation.status}
                        </Badge>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-neutral-500">
                        {formatDate(invitation.sent_at)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>

              {invitations.length > 5 && (
                <div className="text-center pt-4 border-t border-neutral-200 mt-4">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setActiveTab('relationships')}
                  >
                    View All {invitations.length} Suppliers
                  </Button>
                </div>
              )}
            </div>
          )}
        </CardBody>
      </Card>

      {/* Active Relationships Summary */}
      <Card>
        <CardHeader 
          title="Active Relationships"
          subtitle={`${stats.activeRelationships} active supplier relationships`}
          action={
            <Button
              variant="outline"
              size="sm"
              onClick={() => setActiveTab('relationships')}
              leftIcon={<EyeIcon className="h-4 w-4" />}
            >
              View All
            </Button>
          }
        />
        <CardBody>
          {relationships.filter(rel => rel.status === 'active').length === 0 ? (
            <div className="text-center py-8">
              <UsersIcon className="h-12 w-12 text-neutral-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-neutral-900 mb-2">No active relationships</h3>
              <p className="text-neutral-600">
                Relationships will appear here once suppliers are onboarded to the platform.
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {relationships
                .filter(rel => rel.status === 'active')
                .slice(0, 3)
                .map((relationship) => (
                  <div
                    key={relationship.id}
                    className="flex items-center justify-between p-3 bg-neutral-50 rounded-lg"
                  >
                    <div className="flex items-center space-x-3">
                      <div className="w-10 h-10 bg-success-100 rounded-full flex items-center justify-center">
                        <UsersIcon className="h-5 w-5 text-success-600" />
                      </div>
                      <div>
                        <h4 className="font-medium text-neutral-900">{relationship.seller_company_name}</h4>
                        <p className="text-sm text-neutral-600">
                          {relationship.total_orders} orders • {relationship.relationship_type}
                        </p>
                      </div>
                    </div>
                    
                    <div className="text-right">
                      <div className="text-sm font-medium text-neutral-900">
                        {relationship.transparency_score 
                          ? `${relationship.transparency_score.toFixed(1)}% transparency`
                          : 'No score yet'
                        }
                      </div>
                      <div className="text-xs text-neutral-600">
                        Since {formatDate(relationship.established_at)}
                      </div>
                    </div>
                  </div>
                ))}
            </div>
          )}
        </CardBody>
      </Card>
    </div>
  );

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-neutral-900">Supplier Management</h1>
          <p className="text-neutral-600">
            Add and manage suppliers, relationships, and supply chain analytics
          </p>
        </div>
        
        <Button
          variant="primary"
          onClick={() => setActiveTab('add')}
          leftIcon={<PlusIcon className="h-4 w-4" />}
        >
          Add Supplier
        </Button>
      </div>

      {/* Tab Navigation */}
      <div className="border-b border-neutral-200">
        <nav className="-mb-px flex space-x-8">
          {[
            { id: 'overview', label: 'Overview', icon: ChartBarIcon },
            { id: 'add', label: 'Add Supplier', icon: UserPlusIcon },
            { id: 'relationships', label: 'Relationships', icon: UsersIcon },
            { id: 'analytics', label: 'Analytics', icon: ChartBarIcon },
          ].map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={cn(
                  'flex items-center space-x-2 py-2 px-1 border-b-2 font-medium text-sm transition-colors',
                  isActive
                    ? 'border-primary-500 text-primary-600'
                    : 'border-transparent text-neutral-500 hover:text-neutral-700 hover:border-neutral-300'
                )}
              >
                <Icon className="h-5 w-5" />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </nav>
      </div>

      {/* Tab Content */}
      <div>
        {activeTab === 'overview' && renderOverview()}
        {activeTab === 'add' && (
          <SupplierAddForm
            onInvitationSent={handleInvitationSent}
            onCancel={() => setActiveTab('overview')}
          />
        )}
        {activeTab === 'relationships' && user?.company?.id && (
          <RelationshipManagement
            companyId={user.company.id}
            onInviteSupplier={() => setActiveTab('add')}
          />
        )}
        {activeTab === 'analytics' && user?.company?.id && (
          <ViralCascadeAnalytics companyId={user.company.id} />
        )}
      </div>
    </div>
  );
};

export default SupplierOnboardingDashboard;
