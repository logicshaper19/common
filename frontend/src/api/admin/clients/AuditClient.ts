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
    try {
      const { page, per_page } = this.validatePagination(filters.page, filters.per_page);
      const validatedFilters = { ...filters, page, per_page };

      const response = await this.makeRequest<PaginatedResponse<AuditLogEntry>>(
        '/admin/audit-logs',
        { params: validatedFilters }
      );

      return response;
    } catch (error) {
      console.warn('Backend not available for audit logs, using mock data');
      return this.getMockAuditLogs(filters);
    }
  }

  /**
   * Export audit logs to various formats
   */
  async exportAuditLogs(request: AuditExportRequest): Promise<{ download_url: string }> {
    this.validateRequired(request, ['format']);

    try {
      const response = await this.makeRequest<{ download_url: string }>('/admin/audit-logs/export', {
        method: 'POST',
        data: request,
      });

      return response;
    } catch (error) {
      console.warn('Backend not available for audit log export, using mock data');
      return {
        download_url: `https://example.com/exports/audit-logs-${Date.now()}.${request.format}`,
      };
    }
  }

  /**
   * Get audit log statistics
   */
  async getAuditStats(days: number = 30): Promise<{
    total_events: number;
    by_action: Record<string, number>;
    by_resource: Record<string, number>;
    by_user: Record<string, number>;
    by_risk_level: Record<string, number>;
    failed_actions: number;
    recent_activity: AuditLogEntry[];
  }> {
    try {
      const response = await this.makeRequest<any>('/admin/audit-logs/stats', {
        params: { days },
      });

      return response;
    } catch (error) {
      console.warn('Backend not available for audit stats, using mock data');
      return this.getMockAuditStats();
    }
  }

  // Mock data methods
  private async getMockAuditLogs(filters: AuditFilter): Promise<PaginatedResponse<AuditLogEntry>> {
    await this.delay();

    const mockLogs: AuditLogEntry[] = [
      {
        id: 'audit-1',
        timestamp: '2024-01-20T10:30:00Z',
        user_id: 'user-1',
        user_name: 'John Smith',
        user_email: 'john@example.com',
        company_id: 'company-1',
        company_name: 'ACME Corp',
        action: 'create',
        resource_type: 'product',
        resource_id: 'prod-1',
        resource_name: 'Palm Oil',
        details: {
          changes: [],
          metadata: {},
        },
        ip_address: '192.168.1.1',
        user_agent: 'Mozilla/5.0',
        session_id: 'sess-1',
        risk_level: 'low',
        success: true,
      },
      {
        id: 'audit-2',
        timestamp: '2024-01-20T11:15:00Z',
        user_id: 'user-2',
        user_name: 'Alice Johnson',
        user_email: 'alice@company.com',
        company_id: 'company-2',
        company_name: 'Company Inc',
        action: 'update',
        resource_type: 'user',
        resource_id: 'user-1',
        resource_name: 'John Smith',
        details: {
          changes: [
            {
              field: 'role',
              old_value: 'viewer',
              new_value: 'buyer',
            },
          ],
          metadata: {},
        },
        ip_address: '192.168.1.2',
        user_agent: 'Mozilla/5.0',
        session_id: 'sess-2',
        risk_level: 'medium',
        success: true,
      },
    ];

    return {
      data: mockLogs,
      total: mockLogs.length,
      page: filters.page,
      per_page: filters.per_page,
      total_pages: 1,
    };
  }

  private async getMockAuditStats(): Promise<any> {
    await this.delay();

    return {
      total_events: 1247,
      by_action: {
        create: 456,
        update: 389,
        delete: 123,
        login: 234,
        logout: 45,
      },
      by_resource: {
        product: 234,
        user: 345,
        company: 123,
        purchase_order: 456,
        ticket: 89,
      },
      by_user: {
        'John Smith': 234,
        'Alice Johnson': 189,
        'Bob Wilson': 156,
        'Sarah Davis': 345,
      },
      by_risk_level: {
        low: 1000,
        medium: 200,
        high: 40,
        critical: 7,
      },
      failed_actions: 23,
      recent_activity: [
        {
          id: 'audit-recent-1',
          timestamp: new Date().toISOString(),
          user_id: 'user-1',
          user_name: 'John Smith',
          user_email: 'john@example.com',
          company_id: 'company-1',
          company_name: 'ACME Corp',
          action: 'login',
          resource_type: 'session',
          resource_id: 'sess-123',
          resource_name: 'Login Session',
          details: {},
          ip_address: '192.168.1.1',
          user_agent: 'Mozilla/5.0',
          session_id: 'sess-123',
          risk_level: 'low',
          success: true,
        },
      ],
    };
  }
}
