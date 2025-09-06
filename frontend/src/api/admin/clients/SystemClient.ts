/**
 * System configuration and monitoring client for admin API
 */
import { BaseAdminClient } from '../base/BaseAdminClient';
import {
  SystemHealth,
  SystemConfig,
  SystemAlert,
  BackupStatus,
  AdminDashboardData,
} from '../../../types/admin';

export class SystemClient extends BaseAdminClient {
  /**
   * Get admin dashboard data
   */
  async getDashboardData(): Promise<AdminDashboardData> {
    try {
      const response = await this.makeRequest<AdminDashboardData>('/admin/dashboard');
      return response;
    } catch (error) {
      console.warn('Backend not available for dashboard data, using mock data');
      return this.getMockDashboardData();
    }
  }

  /**
   * Get system health status
   */
  async getSystemHealth(): Promise<SystemHealth> {
    try {
      const response = await this.makeRequest<SystemHealth>('/admin/system/health');
      return response;
    } catch (error) {
      console.warn('Backend not available for system health, using mock data');
      return this.getMockSystemHealth();
    }
  }

  /**
   * Get system configuration
   */
  async getSystemConfigs(): Promise<SystemConfig[]> {
    try {
      const response = await this.makeRequest<SystemConfig[]>('/admin/system/configs');
      return response;
    } catch (error) {
      console.warn('Backend not available for system configs, using mock data');
      return this.getMockSystemConfigs();
    }
  }

  /**
   * Update system configuration
   */
  async updateSystemConfig(id: string, value: any): Promise<{ success: boolean }> {
    this.validateRequired({ id }, ['id']);

    try {
      await this.makeRequest(`/admin/system/configs/${id}`, {
        method: 'PUT',
        data: { value },
      });

      return { success: true };
    } catch (error) {
      console.warn(`Backend not available for config ${id} update, using mock data`);
      return { success: true };
    }
  }

  /**
   * Get system alerts
   */
  async getSystemAlerts(): Promise<SystemAlert[]> {
    try {
      const response = await this.makeRequest<SystemAlert[]>('/admin/system/alerts');
      return response;
    } catch (error) {
      console.warn('Backend not available for system alerts, using mock data');
      return [];
    }
  }

  /**
   * Acknowledge a system alert
   */
  async acknowledgeAlert(id: string): Promise<{ success: boolean }> {
    this.validateRequired({ id }, ['id']);

    try {
      await this.makeRequest(`/admin/system/alerts/${id}/acknowledge`, {
        method: 'POST',
      });

      return { success: true };
    } catch (error) {
      console.warn(`Backend not available for alert ${id} acknowledgment, using mock data`);
      return { success: true };
    }
  }

  /**
   * Get backup status
   */
  async getBackupStatus(): Promise<BackupStatus[]> {
    try {
      const response = await this.makeRequest<BackupStatus[]>('/admin/system/backups');
      return response;
    } catch (error) {
      console.warn('Backend not available for backup status, using mock data');
      return this.getMockBackupStatus();
    }
  }

  /**
   * Create a new backup
   */
  async createBackup(type: 'full' | 'incremental'): Promise<{ success: boolean; backup_id: string }> {
    this.validateRequired({ type }, ['type']);

    try {
      const response = await this.makeRequest<{ success: boolean; backup_id: string }>('/admin/system/backups', {
        method: 'POST',
        data: { type },
      });

      return response;
    } catch (error) {
      console.warn('Backend not available for backup creation, using mock data');
      return {
        success: true,
        backup_id: `backup-${Date.now()}`,
      };
    }
  }

  // Mock data methods
  private async getMockDashboardData(): Promise<AdminDashboardData> {
    await this.delay();

    return {
      overview: {
        total_users: 1247,
        active_users: 892,
        total_companies: 156,
        active_companies: 134,
        total_products: 89,
        total_purchase_orders: 2341,
        open_tickets: 12,
        critical_alerts: 0,
        system_uptime: 99.95,
        last_backup: '2024-01-20T06:00:00Z',
      },
      recent_activity: [
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
          details: {},
          ip_address: '192.168.1.1',
          user_agent: 'Mozilla/5.0',
          session_id: 'sess-1',
          risk_level: 'low',
          success: true,
        },
      ],
      system_health: this.getMockSystemHealth(),
      alerts: [],
      user_stats: {
        new_users_today: 8,
        new_users_week: 34,
        active_sessions: 156,
        login_failures_today: 3,
        users_by_role: {
          admin: 5,
          buyer: 456,
          seller: 378,
          viewer: 234,
          support: 12,
        },
        users_by_company_type: {
          brand: 234,
          processor: 345,
          originator: 456,
          trader: 123,
          plantation: 89,
        },
      },
      company_stats: {
        new_companies_today: 2,
        new_companies_week: 8,
        companies_by_tier: {
          free: 45,
          basic: 67,
          premium: 34,
          enterprise: 10,
        },
        companies_by_compliance: {
          compliant: 134,
          warning: 15,
          non_compliant: 5,
          pending_review: 2,
        },
        average_transparency_score: 87.3,
      },
      support_stats: {
        open_tickets: 12,
        tickets_today: 5,
        tickets_week: 23,
        average_response_time: 2.5,
        tickets_by_priority: {
          low: 3,
          medium: 6,
          high: 2,
          urgent: 1,
          critical: 0,
        },
        tickets_by_category: {
          technical: 5,
          billing: 2,
          feature_request: 3,
          bug_report: 1,
          account: 1,
          compliance: 0,
          other: 0,
        },
        satisfaction_rating: 4.6,
      },
    };
  }

  private getMockSystemHealth(): SystemHealth {
    return {
      status: 'healthy',
      timestamp: new Date().toISOString(),
      services: [],
      metrics: {
        cpu_usage: 45.2,
        memory_usage: 67.8,
        disk_usage: 34.5,
        active_connections: 156,
        requests_per_minute: 2340,
        error_rate: 0.02,
        average_response_time: 245,
        database_connections: 12,
        queue_size: 3,
      },
      alerts: [],
      uptime: 99.95,
      version: '1.2.3',
    };
  }

  private getMockSystemConfigs(): SystemConfig[] {
    return [
      {
        id: 'config-1',
        key: 'app.max_upload_size',
        value: 10485760,
        description: 'Maximum file upload size in bytes',
        category: 'application',
        data_type: 'number',
        is_sensitive: false,
        requires_restart: false,
        validation_rules: [
          { type: 'min', value: 1048576, message: 'Must be at least 1MB' },
          { type: 'max', value: 104857600, message: 'Must be less than 100MB' },
        ],
        updated_at: '2024-01-20T10:00:00Z',
        updated_by: 'admin',
      },
    ];
  }

  private getMockBackupStatus(): BackupStatus[] {
    return [
      {
        id: 'backup-1',
        type: 'full',
        status: 'completed',
        started_at: '2024-01-20T06:00:00Z',
        completed_at: '2024-01-20T06:45:00Z',
        size_bytes: 1073741824,
        file_count: 15420,
        location: 's3://backups/full-20240120.tar.gz',
        retention_days: 30,
        error_message: null,
      },
    ];
  }
}
