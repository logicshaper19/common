/**
 * API client for supplier onboarding and relationship management
 */
import { apiClient } from './api';
import {
  SupplierInvitation,
  SupplierInvitationRequest,
  BusinessRelationship,
  ViralCascadeMetrics,
  OnboardingProgress,
  CompanyOnboardingData,
  UserOnboardingData,
  DataSharingPermissions,
  RelationshipAnalytics,
  CompanySetupStatus,
  InvitationTemplate,
  EmailSendRequest,
} from '../types/onboarding';

export class OnboardingApi {
  /**
   * Send supplier invitation (add supplier)
   */
  async sendSupplierInvitation(invitation: SupplierInvitationRequest): Promise<SupplierInvitation> {
    const response = await apiClient.post('/business-relationships/invite-supplier', invitation);
    return response.data;
  }

  /**
   * Get supplier invitations (added suppliers)
   */
  async getSupplierInvitations(companyId: string): Promise<SupplierInvitation[]> {
    // For now, we'll get this from business relationships since invitations are tracked there
    const relationships = await this.getBusinessRelationships(companyId);
    // Convert relationships to invitation format for backward compatibility
    return relationships.map(rel => ({
      id: rel.id,
      supplier_email: '', // Email not available in relationship data
      supplier_name: rel.seller_company_name || '',
      company_type: 'originator' as const, // Default to originator
      sector_id: 'palm_oil' as const, // Default to palm_oil
      relationship_type: rel.relationship_type,
      status: rel.status === 'active' ? 'accepted' : 'pending',
      sent_at: rel.established_at,
      expires_at: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString(), // 30 days from now
      data_sharing_permissions: rel.data_sharing_permissions,
      invited_by_company_id: rel.invited_by_company_id || '',
      invited_by_company_name: rel.invited_by_company_name || '',
      invited_by_user_id: '',
      invited_by_user_name: ''
    }));
  }

  /**
   * Get business relationships
   */
  async getBusinessRelationships(companyId: string): Promise<BusinessRelationship[]> {
    const response = await apiClient.get(`/business-relationships/`);
    const relationships = response.data.relationships || response.data;

    // Transform the response to match frontend expectations
    return relationships.map((rel: any) => ({
      id: rel.id,
      buyer_company_id: rel.buyer_company_id,
      buyer_company_name: rel.buyer_company_name || '',
      seller_company_id: rel.seller_company_id,
      seller_company_name: rel.seller_company_name || '',
      relationship_type: rel.relationship_type,
      status: rel.status,
      data_sharing_permissions: rel.data_sharing_permissions,
      invited_by_company_id: rel.invited_by_company_id,
      invited_by_company_name: rel.invited_by_company_name,
      established_at: rel.established_at,
      terminated_at: rel.terminated_at,
      total_orders: 0, // These would come from separate API calls
      total_value: 0,
      transparency_score: undefined
    }));
  }

  /**
   * Get viral cascade metrics
   */
  async getViralCascadeMetrics(companyId: string): Promise<ViralCascadeMetrics> {
    const response = await apiClient.get(`/onboarding/viral-metrics/${companyId}`);
    return response.data;
  }

  /**
   * Get onboarding progress
   */
  async getOnboardingProgress(companyId: string): Promise<OnboardingProgress> {
    const response = await apiClient.get(`/onboarding/progress/${companyId}`);
    return response.data;
  }

  /**
   * Update company onboarding data
   */
  async updateCompanyOnboarding(companyId: string, data: Partial<CompanyOnboardingData>): Promise<CompanyOnboardingData> {
    const response = await apiClient.put(`/onboarding/company/${companyId}`, data);
    return response.data;
  }

  /**
   * Update user onboarding data
   */
  async updateUserOnboarding(userId: string, data: Partial<UserOnboardingData>): Promise<UserOnboardingData> {
    const response = await apiClient.put(`/onboarding/user/${userId}`, data);
    return response.data;
  }

  /**
   * Update data sharing permissions
   */
  async updateDataSharingPermissions(
    relationshipId: string, 
    permissions: DataSharingPermissions
  ): Promise<BusinessRelationship> {
    const response = await apiClient.put(`/onboarding/relationships/${relationshipId}/permissions`, permissions);
    return response.data;
  }

  /**
   * Get relationship analytics
   */
  async getRelationshipAnalytics(companyId: string): Promise<RelationshipAnalytics> {
    const response = await apiClient.get(`/onboarding/analytics/${companyId}`);
    return response.data;
  }

  /**
   * Get company setup status
   */
  async getCompanySetupStatus(companyId: string): Promise<CompanySetupStatus> {
    const response = await apiClient.get(`/onboarding/setup-status/${companyId}`);
    return response.data;
  }

  /**
   * Complete onboarding step
   */
  async completeOnboardingStep(companyId: string, step: string): Promise<OnboardingProgress> {
    const response = await apiClient.post(`/onboarding/complete-step`, { company_id: companyId, step });
    return response.data;
  }

  /**
   * Get invitation templates
   */
  async getInvitationTemplates(): Promise<InvitationTemplate[]> {
    const response = await apiClient.get('/onboarding/templates');
    return response.data;
  }

  /**
   * Send custom email
   */
  async sendCustomEmail(emailRequest: EmailSendRequest): Promise<{ success: boolean; message: string }> {
    const response = await apiClient.post('/onboarding/send-email', emailRequest);
    return response.data;
  }

  /**
   * Accept supplier invitation
   */
  async acceptInvitation(invitationId: string, companyData: CompanyOnboardingData): Promise<BusinessRelationship> {
    const response = await apiClient.post(`/onboarding/invitations/${invitationId}/accept`, companyData);
    return response.data;
  }

  /**
   * Decline supplier invitation
   */
  async declineInvitation(invitationId: string, reason?: string): Promise<void> {
    await apiClient.post(`/onboarding/invitations/${invitationId}/decline`, { reason });
  }

  /**
   * Resend invitation
   */
  async resendInvitation(invitationId: string): Promise<SupplierInvitation> {
    const response = await apiClient.post(`/onboarding/invitations/${invitationId}/resend`);
    return response.data;
  }

  /**
   * Cancel invitation
   */
  async cancelInvitation(invitationId: string): Promise<void> {
    await apiClient.delete(`/onboarding/invitations/${invitationId}`);
  }

  /**
   * Update relationship status
   */
  async updateRelationshipStatus(
    relationshipId: string, 
    status: 'active' | 'suspended' | 'terminated'
  ): Promise<BusinessRelationship> {
    const response = await apiClient.put(`/onboarding/relationships/${relationshipId}/status`, { status });
    return response.data;
  }

  /**
   * Get onboarding checklist
   */
  async getOnboardingChecklist(companyId: string): Promise<Array<{
    id: string;
    title: string;
    description: string;
    completed: boolean;
    required: boolean;
    order: number;
  }>> {
    const response = await apiClient.get(`/onboarding/checklist/${companyId}`);
    return response.data;
  }
}

// Export singleton instance
export const onboardingApi = new OnboardingApi();

// Legacy exports for backward compatibility
export const sendSupplierInvitation = (invitation: SupplierInvitationRequest) =>
  onboardingApi.sendSupplierInvitation(invitation);
export const getSupplierInvitations = (companyId: string) => onboardingApi.getSupplierInvitations(companyId);
export const getBusinessRelationships = (companyId: string) => onboardingApi.getBusinessRelationships(companyId);
export const getViralCascadeMetrics = (companyId: string) => onboardingApi.getViralCascadeMetrics(companyId);
export const getOnboardingProgress = (companyId: string) => onboardingApi.getOnboardingProgress(companyId);
export const updateCompanyOnboarding = (companyId: string, data: Partial<CompanyOnboardingData>) => 
  onboardingApi.updateCompanyOnboarding(companyId, data);
export const updateUserOnboarding = (userId: string, data: Partial<UserOnboardingData>) => 
  onboardingApi.updateUserOnboarding(userId, data);
export const updateDataSharingPermissions = (relationshipId: string, permissions: DataSharingPermissions) => 
  onboardingApi.updateDataSharingPermissions(relationshipId, permissions);
export const getRelationshipAnalytics = (companyId: string) => onboardingApi.getRelationshipAnalytics(companyId);
export const getCompanySetupStatus = (companyId: string) => onboardingApi.getCompanySetupStatus(companyId);
export const completeOnboardingStep = (companyId: string, step: string) => 
  onboardingApi.completeOnboardingStep(companyId, step);
export const getInvitationTemplates = () => onboardingApi.getInvitationTemplates();
export const sendCustomEmail = (emailRequest: EmailSendRequest) => onboardingApi.sendCustomEmail(emailRequest);
export const acceptInvitation = (invitationId: string, companyData: CompanyOnboardingData) => 
  onboardingApi.acceptInvitation(invitationId, companyData);
export const declineInvitation = (invitationId: string, reason?: string) => 
  onboardingApi.declineInvitation(invitationId, reason);
export const resendInvitation = (invitationId: string) => onboardingApi.resendInvitation(invitationId);
export const cancelInvitation = (invitationId: string) => onboardingApi.cancelInvitation(invitationId);
export const updateRelationshipStatus = (relationshipId: string, status: 'active' | 'suspended' | 'terminated') => 
  onboardingApi.updateRelationshipStatus(relationshipId, status);
export const getOnboardingChecklist = (companyId: string) => onboardingApi.getOnboardingChecklist(companyId);
