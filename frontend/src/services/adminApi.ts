/**
 * Admin API Service
 * Handles admin override operations and audit trail management
 */
import { apiClient } from '../lib/api';

export interface AdminOverrideRequest {
  resourceType: 'document' | 'purchase_order' | 'company';
  resourceId: string;
  reason: string;
}

export interface AdminOverrideResponse {
  success: boolean;
  message: string;
  auditEventId?: string;
}

export interface AuditEvent {
  id: string;
  event_type: string;
  user_id: string;
  company_id?: string;
  resource_type: string;
  resource_id: string;
  action: string;
  details: Record<string, any>;
  severity: string;
  timestamp: string;
}

export interface AuditTrailResponse {
  events: AuditEvent[];
  total: number;
  page: number;
  limit: number;
}

export interface AuditTrailFilters {
  admin_user_id?: string;
  company_id?: string;
  action_type?: string;
  start_date?: string;
  end_date?: string;
  page?: number;
  limit?: number;
}

class AdminApiService {
  /**
   * Delete a resource with admin override
   */
  async deleteResource(request: AdminOverrideRequest): Promise<AdminOverrideResponse> {
    try {
      const { resourceType, resourceId, reason } = request;
      
      if (resourceType === 'document') {
        // Use the existing document deletion endpoint with reason
        const response = await apiClient.delete(`/api/v1/documents/${resourceId}`, {
          params: { deletion_reason: reason }
        });
        
        return {
          success: true,
          message: 'Document deleted successfully with admin override'
        };
      }
      
      // For other resource types, we would implement specific endpoints
      throw new Error(`Admin deletion not implemented for resource type: ${resourceType}`);
      
    } catch (error) {
      console.error('Admin delete resource failed:', error);
      throw error;
    }
  }

  /**
   * Access a resource with admin override (logs the access)
   */
  async accessResource(request: AdminOverrideRequest): Promise<AdminOverrideResponse> {
    try {
      const { resourceType, resourceId, reason } = request;
      
      // For document access, we can use the existing endpoint which already logs admin access
      if (resourceType === 'document') {
        const response = await apiClient.get(`/api/v1/documents/${resourceId}`);
        
        return {
          success: true,
          message: 'Document accessed successfully with admin override'
        };
      }
      
      // For other resource types, we would implement specific endpoints
      throw new Error(`Admin access not implemented for resource type: ${resourceType}`);
      
    } catch (error) {
      console.error('Admin access resource failed:', error);
      throw error;
    }
  }

  /**
   * Get admin audit trail
   */
  async getAuditTrail(filters: AuditTrailFilters = {}): Promise<AuditTrailResponse> {
    try {
      const params = new URLSearchParams();
      
      if (filters.admin_user_id) params.append('admin_user_id', filters.admin_user_id);
      if (filters.company_id) params.append('company_id', filters.company_id);
      if (filters.action_type) params.append('action_type', filters.action_type);
      if (filters.start_date) params.append('start_date', filters.start_date);
      if (filters.end_date) params.append('end_date', filters.end_date);
      if (filters.page) params.append('page', filters.page.toString());
      if (filters.limit) params.append('limit', filters.limit.toString());

      const response = await apiClient.get(`/api/v1/admin/audit-trail?${params.toString()}`);
      return response.data;
      
    } catch (error) {
      console.error('Get audit trail failed:', error);
      throw error;
    }
  }

  /**
   * Get audit events for a specific resource
   */
  async getResourceAuditEvents(
    resourceType: string, 
    resourceId: string
  ): Promise<AuditEvent[]> {
    try {
      const response = await apiClient.get(
        `/api/v1/admin/audit-trail/resource/${resourceType}/${resourceId}`
      );
      return response.data.events || [];
      
    } catch (error) {
      console.error('Get resource audit events failed:', error);
      throw error;
    }
  }

  /**
   * Get admin override statistics
   */
  async getOverrideStatistics(timeframe: '24h' | '7d' | '30d' = '7d') {
    try {
      const response = await apiClient.get(`/api/v1/admin/override-stats?timeframe=${timeframe}`);
      return response.data;
      
    } catch (error) {
      console.error('Get override statistics failed:', error);
      throw error;
    }
  }
}

export const adminApi = new AdminApiService();
