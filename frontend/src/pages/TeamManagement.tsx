/**
 * Team Management Page - Main team management interface
 */
import React, { useState, useEffect, useCallback } from 'react';
import {
  UsersIcon,
  UserPlusIcon,
  EnvelopeIcon,
  ClockIcon,
  CheckCircleIcon,
  XCircleIcon
} from '@heroicons/react/24/outline';
import { teamApi, TeamMember, TeamInvitation, CreateInvitationRequest } from '../api/team';

import { useToast } from '../contexts/ToastContext';
import Button from '../components/ui/Button';
import Modal from '../components/ui/Modal';
import Input from '../components/ui/Input';
import Select from '../components/ui/Select';
import TextArea from '../components/ui/Textarea';

const TeamManagement: React.FC = () => {
  const { showSuccess, showError } = useToast();
  const [activeTab, setActiveTab] = useState<'members' | 'invitations'>('members');
  const [members, setMembers] = useState<TeamMember[]>([]);
  const [invitations, setInvitations] = useState<TeamInvitation[]>([]);
  const [loading, setLoading] = useState(true);
  const [showInviteModal, setShowInviteModal] = useState(false);
  const [inviteForm, setInviteForm] = useState<CreateInvitationRequest>({
    email: '',
    full_name: '',
    role: 'viewer',
    message: ''
  });
  const [submitting, setSubmitting] = useState(false);

  // Load team data
  const loadTeamData = useCallback(async () => {
    try {
      setLoading(true);
      const [membersResponse, invitationsResponse] = await Promise.all([
        teamApi.getMembers(),
        teamApi.getInvitations()
      ]);
      setMembers(membersResponse.members);
      setInvitations(invitationsResponse.invitations);
    } catch (error) {
      console.error('Failed to load team data:', error);
      showError('Failed to load team data');
    } finally {
      setLoading(false);
    }
  }, [showError]);

  useEffect(() => {
    loadTeamData();
  }, [loadTeamData]);

  // Handle invite form submission
  const handleInviteSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inviteForm.email || !inviteForm.full_name) {
      showError('Please fill in all required fields');
      return;
    }

    try {
      setSubmitting(true);
      await teamApi.createInvitation(inviteForm);
      showSuccess('Invitation sent successfully!');
      setShowInviteModal(false);
      setInviteForm({ email: '', full_name: '', role: 'viewer', message: '' });
      loadTeamData(); // Refresh data
    } catch (error: any) {
      console.error('Failed to send invitation:', error);
      const message = error.response?.data?.detail || 'Failed to send invitation';
      showError(message);
    } finally {
      setSubmitting(false);
    }
  };

  // Handle cancel invitation
  const handleCancelInvitation = async (invitationId: string) => {
    try {
      await teamApi.cancelInvitation(invitationId);
      showSuccess('Invitation cancelled');
      loadTeamData();
    } catch (error) {
      console.error('Failed to cancel invitation:', error);
      showError('Failed to cancel invitation');
    }
  };

  // Handle resend invitation
  const handleResendInvitation = async (invitationId: string) => {
    try {
      await teamApi.resendInvitation(invitationId);
      showSuccess('Invitation resent successfully!');
      loadTeamData();
    } catch (error) {
      console.error('Failed to resend invitation:', error);
      showError('Failed to resend invitation');
    }
  };

  const roleOptions = [
    { value: 'admin', label: 'Admin' },
    { value: 'buyer', label: 'Buyer' },
    { value: 'seller', label: 'Seller' },
    { value: 'viewer', label: 'Viewer' }
  ];

  const getStatusBadge = (status: string) => {
    const statusConfig = {
      pending: { color: 'bg-yellow-100 text-yellow-800', icon: ClockIcon },
      accepted: { color: 'bg-green-100 text-green-800', icon: CheckCircleIcon },
      declined: { color: 'bg-red-100 text-red-800', icon: XCircleIcon },
      expired: { color: 'bg-gray-100 text-gray-800', icon: XCircleIcon },
      cancelled: { color: 'bg-gray-100 text-gray-800', icon: XCircleIcon }
    };

    const config = statusConfig[status as keyof typeof statusConfig] || statusConfig.pending;
    const Icon = config.icon;

    return (
      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${config.color}`}>
        <Icon className="w-3 h-3 mr-1" />
        {status.charAt(0).toUpperCase() + status.slice(1)}
      </span>
    );
  };

  const getRoleBadge = (role: string) => {
    const roleColors = {
      admin: 'bg-purple-100 text-purple-800',
      buyer: 'bg-blue-100 text-blue-800',
      seller: 'bg-green-100 text-green-800',
      viewer: 'bg-gray-100 text-gray-800'
    };

    return (
      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${roleColors[role as keyof typeof roleColors] || roleColors.viewer}`}>
        {role.charAt(0).toUpperCase() + role.slice(1)}
      </span>
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Team Management</h1>
          <p className="text-gray-600">Manage your team members and invitations</p>
        </div>
        <Button
          onClick={() => setShowInviteModal(true)}
          className="flex items-center"
        >
          <UserPlusIcon className="w-4 h-4 mr-2" />
          Invite Member
        </Button>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          <button
            onClick={() => setActiveTab('members')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'members'
                ? 'border-primary-500 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            <UsersIcon className="w-4 h-4 inline mr-2" />
            Team Members ({members.length})
          </button>
          <button
            onClick={() => setActiveTab('invitations')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'invitations'
                ? 'border-primary-500 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            <EnvelopeIcon className="w-4 h-4 inline mr-2" />
            Invitations ({invitations.length})
          </button>
        </nav>
      </div>

      {/* Content */}
      {activeTab === 'members' && (
        <div className="bg-white shadow rounded-lg">
          <div className="px-4 py-5 sm:p-6">
            <div className="space-y-4">
              {members.map((member) => (
                <div key={member.id} className="flex items-center justify-between p-4 border border-gray-200 rounded-lg">
                  <div className="flex items-center space-x-4">
                    <div className="h-10 w-10 bg-primary-100 rounded-full flex items-center justify-center">
                      <span className="text-primary-700 font-medium">
                        {member.full_name.charAt(0)}
                      </span>
                    </div>
                    <div>
                      <h3 className="text-sm font-medium text-gray-900">{member.full_name}</h3>
                      <p className="text-sm text-gray-500">{member.email}</p>
                      <p className="text-xs text-gray-400">
                        Joined {new Date(member.created_at).toLocaleDateString()}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center space-x-3">
                    {getRoleBadge(member.role)}
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                      member.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                    }`}>
                      {member.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </div>
                </div>
              ))}
              {members.length === 0 && (
                <div className="text-center py-8">
                  <UsersIcon className="mx-auto h-12 w-12 text-gray-400" />
                  <h3 className="mt-2 text-sm font-medium text-gray-900">No team members</h3>
                  <p className="mt-1 text-sm text-gray-500">Get started by inviting your first team member.</p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {activeTab === 'invitations' && (
        <div className="bg-white shadow rounded-lg">
          <div className="px-4 py-5 sm:p-6">
            <div className="space-y-4">
              {invitations.map((invitation) => (
                <div key={invitation.id} className="flex items-center justify-between p-4 border border-gray-200 rounded-lg">
                  <div className="flex items-center space-x-4">
                    <div className="h-10 w-10 bg-gray-100 rounded-full flex items-center justify-center">
                      <EnvelopeIcon className="h-5 w-5 text-gray-400" />
                    </div>
                    <div>
                      <h3 className="text-sm font-medium text-gray-900">{invitation.full_name}</h3>
                      <p className="text-sm text-gray-500">{invitation.email}</p>
                      <p className="text-xs text-gray-400">
                        Invited {new Date(invitation.created_at).toLocaleDateString()} • 
                        Expires {new Date(invitation.expires_at).toLocaleDateString()}
                      </p>
                      {invitation.message && (
                        <p className="text-xs text-gray-600 mt-1">"{invitation.message}"</p>
                      )}
                    </div>
                  </div>
                  <div className="flex items-center space-x-3">
                    {getRoleBadge(invitation.role)}
                    {getStatusBadge(invitation.status)}
                    {invitation.status === 'pending' && (
                      <div className="flex space-x-2">
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => handleResendInvitation(invitation.id)}
                        >
                          Resend
                        </Button>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => handleCancelInvitation(invitation.id)}
                        >
                          Cancel
                        </Button>
                      </div>
                    )}
                  </div>
                </div>
              ))}
              {invitations.length === 0 && (
                <div className="text-center py-8">
                  <EnvelopeIcon className="mx-auto h-12 w-12 text-gray-400" />
                  <h3 className="mt-2 text-sm font-medium text-gray-900">No invitations</h3>
                  <p className="mt-1 text-sm text-gray-500">Invitations you send will appear here.</p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Invite Modal */}
      <Modal
        isOpen={showInviteModal}
        onClose={() => setShowInviteModal(false)}
        title="Invite Team Member"
      >
        <form onSubmit={handleInviteSubmit} className="space-y-4">
          <Input
            label="Email Address"
            type="email"
            value={inviteForm.email}
            onChange={(e) => setInviteForm({ ...inviteForm, email: e.target.value })}
            placeholder="Enter email address"
            required
          />
          <Input
            label="Full Name"
            value={inviteForm.full_name}
            onChange={(e) => setInviteForm({ ...inviteForm, full_name: e.target.value })}
            placeholder="Enter full name"
            required
          />
          <Select
            label="Role"
            value={inviteForm.role}
            onChange={(e) => setInviteForm({ ...inviteForm, role: e.target.value as any })}
            options={roleOptions}
          />
          <TextArea
            label="Message (Optional)"
            value={inviteForm.message}
            onChange={(e) => setInviteForm({ ...inviteForm, message: e.target.value })}
            placeholder="Add a personal message to the invitation"
            rows={3}
          />
          <div className="flex justify-end space-x-3">
            <Button
              type="button"
              variant="outline"
              onClick={() => setShowInviteModal(false)}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              isLoading={submitting}
            >
              Send Invitation
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
};

export default TeamManagement;
