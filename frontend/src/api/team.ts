/**
 * Team Management API Service
 */
import { apiClient } from '../lib/api';

export interface TeamMember {
  id: string;
  email: string;
  full_name: string;
  role: 'admin' | 'buyer' | 'seller' | 'viewer';
  is_active: boolean;
  created_at: string;
  last_login: string | null;
}

export interface TeamInvitation {
  id: string;
  email: string;
  full_name: string;
  role: 'admin' | 'buyer' | 'seller' | 'viewer';
  company_id: string;
  invited_by_user_id: string;
  status: 'pending' | 'accepted' | 'declined' | 'expired' | 'cancelled';
  invitation_token: string;
  message?: string;
  created_at: string;
  expires_at: string;
  accepted_at?: string | null;
  accepted_by_user_id?: string | null;
  is_expired: boolean;
  is_pending: boolean;
  invited_by_name?: string;
  invited_by_email?: string;
  company_name?: string;
}

export interface CreateInvitationRequest {
  email: string;
  full_name: string;
  role: 'admin' | 'buyer' | 'seller' | 'viewer';
  message?: string;
}

export interface AcceptInvitationRequest {
  invitation_token: string;
  password: string;
}

export interface TeamMembersResponse {
  members: TeamMember[];
  total: number;
  active_count: number;
  admin_count: number;
}

export interface TeamInvitationsResponse {
  invitations: TeamInvitation[];
  total: number;
  pending_count: number;
  accepted_count: number;
  expired_count: number;
}

export const teamApi = {
  // Get team members
  getMembers: async (): Promise<TeamMembersResponse> => {
    const response = await apiClient.get('/team/members');
    return response.data;
  },

  // Get team invitations
  getInvitations: async (): Promise<TeamInvitationsResponse> => {
    const response = await apiClient.get('/team/invitations');
    return response.data;
  },

  // Create team invitation
  createInvitation: async (data: CreateInvitationRequest): Promise<TeamInvitation> => {
    const response = await apiClient.post('/team/invitations', data);
    return response.data;
  },

  // Accept team invitation (public endpoint)
  acceptInvitation: async (data: AcceptInvitationRequest): Promise<{ message: string; user: any }> => {
    const response = await apiClient.post('/team/invitations/accept', data);
    return response.data;
  },

  // Cancel invitation
  cancelInvitation: async (invitationId: string): Promise<{ message: string }> => {
    const response = await apiClient.delete(`/team/invitations/${invitationId}`);
    return response.data;
  },

  // Resend invitation
  resendInvitation: async (invitationId: string): Promise<TeamInvitation> => {
    const response = await apiClient.post(`/team/invitations/${invitationId}/resend`);
    return response.data;
  },
};
