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
   * Note: Simple relationships don't support invitations - relationships are created automatically
   * when purchase orders are created between companies.
   */
  async sendSupplierInvitation(invitation: SupplierInvitationRequest): Promise<SupplierInvitation> {
    // For simple relationships, we don't actually send invitations
    // Relationships are created automatically when POs are created
    // This is a mock response to maintain compatibility
    return {
      id: 'mock-invitation-id',
      supplier_email: invitation.supplier_email,
      supplier_name: invitation.supplier_name,
      company_type: invitation.company_type,
      sector_id: invitation.sector_id,
      relationship_type: invitation.relationship_type,
      invitation_message: invitation.invitation_message,
      data_sharing_permissions: {
        operational_data: true,
        commercial_data: false,
        traceability_data: true,
        quality_data: true,
        location_data: true
      },
      invited_by_company_id: 'mock-company-id',
      invited_by_company_name: 'Mock Company',
      invited_by_user_id: 'mock-user-id',
      invited_by_user_name: 'Mock User',
      status: 'accepted',
      sent_at: new Date().toISOString(),
      expires_at: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString(), // 30 days from now
      accepted_at: new Date().toISOString()
    };
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
   * Get business relationships using simple relationships API
   */
  async getBusinessRelationships(companyId: string): Promise<BusinessRelationship[]> {
    try {
      // Get suppliers and buyers from simple relationships API
      const [suppliersResponse, buyersResponse] = await Promise.all([
        apiClient.get('/simple/relationships/suppliers'),
        apiClient.get('/simple/relationships/buyers')
      ]);

      const suppliers = suppliersResponse.data.suppliers || [];
      const buyers = buyersResponse.data.buyers || [];

      // Transform suppliers to business relationships
      const supplierRelationships = suppliers.map((supplier: any) => ({
        id: `supplier-${supplier.company_id}`,
        buyer_company_id: companyId,
        buyer_company_name: '', // Will be filled by frontend
        seller_company_id: supplier.company_id,
        seller_company_name: supplier.company_name,
        relationship_type: 'supplier',
        status: 'active',
        data_sharing_permissions: {},
        invited_by_company_id: companyId,
        invited_by_company_name: '',
        established_at: supplier.first_transaction_date,
        terminated_at: null,
        total_orders: supplier.total_purchase_orders,
        total_value: supplier.total_value,
        transparency_score: undefined
      }));

      // Transform buyers to business relationships
      const buyerRelationships = buyers.map((buyer: any) => ({
        id: `buyer-${buyer.company_id}`,
        buyer_company_id: buyer.company_id,
        buyer_company_name: buyer.company_name,
        seller_company_id: companyId,
        seller_company_name: '', // Will be filled by frontend
        relationship_type: 'buyer',
        status: 'active',
        data_sharing_permissions: {},
        invited_by_company_id: companyId,
        invited_by_company_name: '',
        established_at: buyer.first_transaction_date,
        terminated_at: null,
        total_orders: buyer.total_purchase_orders,
        total_value: buyer.total_value,
        transparency_score: undefined
      }));

      // Combine and return all relationships
      return [...supplierRelationships, ...buyerRelationships];
    } catch (error) {
      console.error('Failed to get business relationships:', error);
      return [];
    }
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
