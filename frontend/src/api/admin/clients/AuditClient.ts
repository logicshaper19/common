/**
 * Audit log management client for admin API
 */
import { BaseAdminClient } from '../base/BaseAdminClient';
import { PaginatedResponse } from '../base/types';
import {
  AuditLogEntry,
  AuditFilter,
  AuditExportRequest,
} from '../../../types/admin';

export class AuditClient extends BaseAdminClient {

  /**
   * Get paginated list of audit logs with filtering
   */
  async getAuditLogs(filters: AuditFilter): Promise<PaginatedResponse<AuditLogEntry>> {
    const { page, per_page } = this.validatePagination(filters.page, filters.per_page);
    const validatedFilters = { ...filters, page, per_page };

    const response = await this.makeRequest<PaginatedResponse<AuditLogEntry>>(
      '/admin/audit-logs',
      { params: validatedFilters }
    );

    return response;
  }

  /**
   * Export audit logs to various formats
   */
  async exportAuditLogs(request: AuditExportRequest): Promise<{ download_url: string }> {
    this.validateRequired(request, ['format']);

    const response = await this.makeRequest<{ download_url: string }>('/admin/audit-logs/export', {
      method: 'POST',
      data: request,
    });

    return response;
  }

  /**
   * Get audit statistics
   */
  async getAuditStats(days: number = 30): Promise<{
    total_events: number;
    by_action: Record<string, number>;
    by_user: Record<string, number>;
    by_resource: Record<string, number>;
    success_rate: number;
    most_active_users: Array<{
      user_id: string;
      user_name: string;
      event_count: number;
    }>;
    recent_critical_events: AuditLogEntry[];
  }> {
    const response = await this.makeRequest<any>('/admin/audit-logs/stats', {
      params: { days },
    });

    return response;
  }

  /**
   * Get audit log details by ID
   */
  async getAuditLog(id: string): Promise<AuditLogEntry> {
    this.validateRequired({ id }, ['id']);

    const response = await this.makeRequest<AuditLogEntry>(`/admin/audit-logs/${id}`);
    return response;
  }

  /**
   * Get user activity audit trail
   */
  async getUserAuditTrail(userId: string, days: number = 30): Promise<PaginatedResponse<AuditLogEntry>> {
    this.validateRequired({ userId }, ['userId']);

    const response = await this.makeRequest<PaginatedResponse<AuditLogEntry>>(
      `/admin/audit-logs/user/${userId}`,
      { params: { days } }
    );

    return response;
  }

  /**
   * Get resource audit trail
   */
  async getResourceAuditTrail(resourceType: string, resourceId: string, days: number = 30): Promise<PaginatedResponse<AuditLogEntry>> {
    this.validateRequired({ resourceType, resourceId }, ['resourceType', 'resourceId']);

    const response = await this.makeRequest<PaginatedResponse<AuditLogEntry>>(
      `/admin/audit-logs/resource/${resourceType}/${resourceId}`,
      { params: { days } }
    );

    return response;
  }

  /**
   * Search audit logs
   */
  async searchAuditLogs(query: string, filters?: Partial<AuditFilter>): Promise<PaginatedResponse<AuditLogEntry>> {
    this.validateRequired({ query }, ['query']);

    const response = await this.makeRequest<PaginatedResponse<AuditLogEntry>>(
      '/admin/audit-logs/search',
      { 
        params: { 
          q: query,
          ...filters 
        } 
      }
    );

    return response;
  }
}
