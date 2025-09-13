/**
 * Team Management Widget - Shared component for all dashboards
 * Reuses existing team management functionality in widget form
 */
import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Card, CardHeader, CardBody } from '../../ui/Card';
import { Button } from '../../ui/Button';
import { Badge } from '../../ui/Badge';
import LoadingSpinner from '../../ui/LoadingSpinner';
import { UsersIcon, PlusIcon, UserGroupIcon } from '@heroicons/react/24/outline';

interface TeamMember {
  id: string;
  full_name: string;
  email: string;
  role: string;
  status: 'active' | 'pending' | 'inactive';
  last_login?: string;
}

interface TeamManagementWidgetProps {
  companyId: string;
  userRole: string;
  canManageTeam: boolean;
  className?: string;
}

export const TeamManagementWidget: React.FC<TeamManagementWidgetProps> = ({
  companyId,
  userRole,
  canManageTeam,
  className = ''
}) => {
  const [teamMembers, setTeamMembers] = useState<TeamMember[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadTeamMembers();
  }, [companyId]);

  const loadTeamMembers = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch(`/api/v1/companies/${companyId}/team`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('auth_token')}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to load team members');
      }

      const data = await response.json();
      setTeamMembers(data.slice(0, 5)); // Show only first 5 members in widget
    } catch (err) {
      console.error('Error loading team members:', err);
      setError(err instanceof Error ? err.message : 'Failed to load team members');
    } finally {
      setLoading(false);
    }
  };

  const getStatusBadgeColor = (status: string) => {
    switch (status) {
      case 'active': return 'green';
      case 'pending': return 'yellow';
      case 'inactive': return 'gray';
      default: return 'gray';
    }
  };

  const getRoleBadgeColor = (role: string) => {
    switch (role) {
      case 'admin': return 'blue';
      case 'supply_chain_manager': return 'purple';
      case 'production_manager': return 'indigo';
      case 'viewer': return 'gray';
      default: return 'gray';
    }
  };

  if (loading) {
    return (
      <Card className={className}>
        <CardHeader>
          <div className="flex items-center">
            <UserGroupIcon className="h-5 w-5 text-gray-400 mr-2" />
            <h3 className="text-lg font-medium">Team Management</h3>
          </div>
        </CardHeader>
        <CardBody>
          <div className="flex items-center justify-center py-8">
            <LoadingSpinner size="md" />
          </div>
        </CardBody>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className={className}>
        <CardHeader>
          <div className="flex items-center">
            <UserGroupIcon className="h-5 w-5 text-gray-400 mr-2" />
            <h3 className="text-lg font-medium">Team Management</h3>
          </div>
        </CardHeader>
        <CardBody>
          <div className="text-center py-8">
            <p className="text-red-600 mb-2">Failed to load team members</p>
            <Button onClick={loadTeamMembers} variant="outline" size="sm">
              Retry
            </Button>
          </div>
        </CardBody>
      </Card>
    );
  }

  return (
    <Card className={className}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center">
            <UserGroupIcon className="h-5 w-5 text-gray-400 mr-2" />
            <h3 className="text-lg font-medium">Team Management</h3>
          </div>
          {canManageTeam && (
            <Link to="/team/invite">
              <Button size="sm" variant="outline">
                <PlusIcon className="h-4 w-4 mr-1" />
                Invite
              </Button>
            </Link>
          )}
        </div>
      </CardHeader>
      <CardBody>
        {teamMembers.length === 0 ? (
          <div className="text-center py-8">
            <UsersIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h4 className="text-lg font-medium text-gray-900 mb-2">No Team Members</h4>
            <p className="text-gray-600 mb-4">
              {canManageTeam 
                ? "Start building your team by inviting members."
                : "No team members to display."
              }
            </p>
            {canManageTeam && (
              <Link to="/team/invite">
                <Button>
                  <PlusIcon className="h-4 w-4 mr-2" />
                  Invite Team Member
                </Button>
              </Link>
            )}
          </div>
        ) : (
          <div className="space-y-3">
            {teamMembers.map((member) => (
              <div key={member.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex-1">
                  <div className="flex items-center space-x-2">
                    <span className="font-medium text-gray-900">{member.full_name}</span>
                    <Badge color={getStatusBadgeColor(member.status)} size="sm">
                      {member.status}
                    </Badge>
                  </div>
                  <div className="flex items-center space-x-2 mt-1">
                    <span className="text-sm text-gray-600">{member.email}</span>
                    <Badge color={getRoleBadgeColor(member.role)} size="sm" variant="outline">
                      {member.role.replace('_', ' ')}
                    </Badge>
                  </div>
                  {member.last_login && (
                    <p className="text-xs text-gray-500 mt-1">
                      Last login: {new Date(member.last_login).toLocaleDateString()}
                    </p>
                  )}
                </div>
              </div>
            ))}
            
            {teamMembers.length >= 5 && (
              <div className="pt-3 border-t border-gray-200">
                <Link to="/team" className="text-sm text-blue-600 hover:text-blue-800">
                  View all team members →
                </Link>
              </div>
            )}
          </div>
        )}
      </CardBody>
    </Card>
  );
};

export default TeamManagementWidget;
