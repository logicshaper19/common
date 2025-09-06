/**
 * Supplier Onboarding Dashboard Page
 * Main interface for supplier onboarding and relationship management
 */
import React, { useState, useEffect } from 'react';
import { 
  UserPlusIcon,
  UsersIcon,
  ChartBarIcon,
  Cog6ToothIcon,
  PlusIcon,
  EyeIcon,
} from '@heroicons/react/24/outline';
import { useAuth } from '../contexts/AuthContext';
import { SupplierInvitation, BusinessRelationship } from '../types/onboarding';
import { onboardingApi } from '../lib/onboardingApi';
import { Card, CardHeader, CardBody } from '../components/ui/Card';
import Button from '../components/ui/Button';
import Badge from '../components/ui/Badge';
import SupplierInvitationForm from '../components/onboarding/SupplierInvitationForm';
import RelationshipManagement from '../components/onboarding/RelationshipManagement';
import ViralCascadeAnalytics from '../components/onboarding/ViralCascadeAnalytics';
import { cn, formatDate } from '../lib/utils';

const SupplierOnboardingDashboard: React.FC = () => {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState<'overview' | 'invite' | 'relationships' | 'analytics'>('overview');
  const [invitations, setInvitations] = useState<SupplierInvitation[]>([]);
  const [relationships, setRelationships] = useState<BusinessRelationship[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  // Load dashboard data
  useEffect(() => {
    if (user?.company_id) {
      loadDashboardData();
    }
  }, [user?.company_id]);

  const loadDashboardData = async () => {
    if (!user?.company_id) return;

    setIsLoading(true);
    try {
      const [invitationsData, relationshipsData] = await Promise.all([
        onboardingApi.getSupplierInvitations(user.company_id),
        onboardingApi.getBusinessRelationships(user.company_id),
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
    totalInvitations: invitations.length,
    pendingInvitations: invitations.filter(inv => inv.status === 'pending').length,
    acceptedInvitations: invitations.filter(inv => inv.status === 'accepted').length,
    activeRelationships: relationships.filter(rel => rel.status === 'active').length,
    totalRelationships: relationships.length,
    conversionRate: invitations.length > 0 
      ? (invitations.filter(inv => inv.status === 'accepted').length / invitations.length) * 100 
      : 0,
  };

  // Render overview tab
  const renderOverview = () => (
    <div className="space-y-6">
      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardBody className="text-center">
            <div className="text-3xl font-bold text-primary-600 mb-1">
              {stats.totalInvitations}
            </div>
            <div className="text-sm text-neutral-600">Total Invitations</div>
          </CardBody>
        </Card>

        <Card>
          <CardBody className="text-center">
            <div className="text-3xl font-bold text-warning-600 mb-1">
              {stats.pendingInvitations}
            </div>
            <div className="text-sm text-neutral-600">Pending Invitations</div>
          </CardBody>
        </Card>

        <Card>
          <CardBody className="text-center">
            <div className="text-3xl font-bold text-success-600 mb-1">
              {stats.activeRelationships}
            </div>
            <div className="text-sm text-neutral-600">Active Relationships</div>
          </CardBody>
        </Card>

        <Card>
          <CardBody className="text-center">
            <div className="text-3xl font-bold text-neutral-600 mb-1">
              {stats.conversionRate.toFixed(1)}%
            </div>
            <div className="text-sm text-neutral-600">Conversion Rate</div>
          </CardBody>
        </Card>
      </div>

      {/* Quick Actions */}
      <Card>
        <CardHeader title="Quick Actions" />
        <CardBody>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Button
              variant="primary"
              onClick={() => setActiveTab('invite')}
              leftIcon={<PlusIcon className="h-4 w-4" />}
              className="h-20 flex-col"
            >
              <span className="text-lg font-medium">Invite Supplier</span>
              <span className="text-sm opacity-80">Send new invitation</span>
            </Button>

            <Button
              variant="outline"
              onClick={() => setActiveTab('relationships')}
              leftIcon={<UsersIcon className="h-4 w-4" />}
              className="h-20 flex-col"
            >
              <span className="text-lg font-medium">Manage Relationships</span>
              <span className="text-sm opacity-80">View and configure</span>
            </Button>

            <Button
              variant="outline"
              onClick={() => setActiveTab('analytics')}
              leftIcon={<ChartBarIcon className="h-4 w-4" />}
              className="h-20 flex-col"
            >
              <span className="text-lg font-medium">View Analytics</span>
              <span className="text-sm opacity-80">Viral cascade metrics</span>
            </Button>
          </div>
        </CardBody>
      </Card>

      {/* Recent Invitations */}
      <Card>
        <CardHeader 
          title="Recent Invitations"
          subtitle={`${invitations.length} total invitations sent`}
          action={
            <Button
              variant="outline"
              size="sm"
              onClick={() => setActiveTab('invite')}
              leftIcon={<PlusIcon className="h-4 w-4" />}
            >
              Send Invitation
            </Button>
          }
        />
        <CardBody>
          {isLoading ? (
            <div className="text-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600 mx-auto"></div>
              <p className="mt-2 text-neutral-600">Loading invitations...</p>
            </div>
          ) : invitations.length === 0 ? (
            <div className="text-center py-8">
              <UserPlusIcon className="h-12 w-12 text-neutral-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-neutral-900 mb-2">No invitations sent yet</h3>
              <p className="text-neutral-600 mb-4">
                Start building your supply chain network by inviting suppliers.
              </p>
              <Button
                variant="primary"
                onClick={() => setActiveTab('invite')}
                leftIcon={<PlusIcon className="h-4 w-4" />}
              >
                Send Your First Invitation
              </Button>
            </div>
          ) : (
            <div className="space-y-3">
              {invitations.slice(0, 5).map((invitation) => (
                <div
                  key={invitation.id}
                  className="flex items-center justify-between p-3 border border-neutral-200 rounded-lg hover:shadow-sm transition-shadow"
                >
                  <div className="flex items-center space-x-3">
                    <div className="w-10 h-10 bg-primary-100 rounded-full flex items-center justify-center">
                      <UserPlusIcon className="h-5 w-5 text-primary-600" />
                    </div>
                    <div>
                      <h4 className="font-medium text-neutral-900">{invitation.supplier_name}</h4>
                      <p className="text-sm text-neutral-600">{invitation.supplier_email}</p>
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-3">
                    <Badge variant={getStatusBadgeVariant(invitation.status)}>
                      {invitation.status}
                    </Badge>
                    <div className="text-right text-sm text-neutral-600">
                      {formatDate(invitation.sent_at)}
                    </div>
                  </div>
                </div>
              ))}
              
              {invitations.length > 5 && (
                <div className="text-center pt-3">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setActiveTab('relationships')}
                  >
                    View All {invitations.length} Invitations
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
                Relationships will appear here once suppliers accept your invitations.
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
          <h1 className="text-2xl font-bold text-neutral-900">Supplier Onboarding</h1>
          <p className="text-neutral-600">
            Manage supplier invitations, relationships, and viral growth analytics
          </p>
        </div>
        
        <Button
          variant="primary"
          onClick={() => setActiveTab('invite')}
          leftIcon={<PlusIcon className="h-4 w-4" />}
        >
          Invite Supplier
        </Button>
      </div>

      {/* Tab Navigation */}
      <div className="border-b border-neutral-200">
        <nav className="-mb-px flex space-x-8">
          {[
            { id: 'overview', label: 'Overview', icon: ChartBarIcon },
            { id: 'invite', label: 'Invite Supplier', icon: UserPlusIcon },
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
        {activeTab === 'invite' && (
          <SupplierInvitationForm
            onInvitationSent={handleInvitationSent}
            onCancel={() => setActiveTab('overview')}
          />
        )}
        {activeTab === 'relationships' && user?.company_id && (
          <RelationshipManagement
            companyId={user.company_id}
            onInviteSupplier={() => setActiveTab('invite')}
          />
        )}
        {activeTab === 'analytics' && user?.company_id && (
          <ViralCascadeAnalytics companyId={user.company_id} />
        )}
      </div>
    </div>
  );
};

export default SupplierOnboardingDashboard;
