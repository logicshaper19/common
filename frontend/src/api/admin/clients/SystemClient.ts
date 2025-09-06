/**
 * System management client for admin API
 */
import { BaseAdminClient } from '../base/BaseAdminClient';
import {
  AdminDashboardData,
  SystemHealth,
  SystemConfig,
  SystemAlert,
  BackupStatus,
} from '../../../types/admin';

export class SystemClient extends BaseAdminClient {

  /**
   * Get admin dashboard data
   */
  async getDashboardData(): Promise<AdminDashboardData> {
    const response = await this.makeRequest<AdminDashboardData>('/admin/dashboard');
    return response;
  }

  /**
   * Get system health status
   */
  async getSystemHealth(): Promise<SystemHealth> {
    const response = await this.makeRequest<SystemHealth>('/admin/system/health');
    return response;
  }

  /**
   * Get system configuration
   */
  async getSystemConfigs(): Promise<SystemConfig[]> {
    const response = await this.makeRequest<SystemConfig[]>('/admin/system/configs');
    return response;
  }

  /**
   * Update system configuration
   */
  async updateSystemConfig(id: string, value: any): Promise<{ success: boolean }> {
    this.validateRequired({ id }, ['id']);

    const response = await this.makeRequest<{ success: boolean }>(`/admin/system/configs/${id}`, {
      method: 'PUT',
      data: { value },
    });

    return { success: true };
  }

  /**
   * Get system alerts
   */
  async getSystemAlerts(): Promise<SystemAlert[]> {
    const response = await this.makeRequest<SystemAlert[]>('/admin/system/alerts');
    return response;
  }

  /**
   * Acknowledge system alert
   */
  async acknowledgeAlert(id: string): Promise<{ success: boolean }> {
    this.validateRequired({ id }, ['id']);

    const response = await this.makeRequest<{ success: boolean }>(`/admin/system/alerts/${id}/acknowledge`, {
      method: 'POST',
    });

    return { success: true };
  }

  /**
   * Get backup status
   */
  async getBackupStatus(): Promise<BackupStatus[]> {
    const response = await this.makeRequest<BackupStatus[]>('/admin/system/backups');
    return response;
  }

  /**
   * Create a new backup
   */
  async createBackup(type: 'full' | 'incremental' | 'differential'): Promise<{
    success: boolean;
    backup_id: string;
  }> {
    this.validateRequired({ type }, ['type']);

    const response = await this.makeRequest<{ success: boolean; backup_id: string }>('/admin/system/backups', {
      method: 'POST',
      data: { type },
    });

    return response;
  }

  /**
   * Get system metrics
   */
  async getSystemMetrics(timeRange: string = '24h'): Promise<{
    cpu_usage: number[];
    memory_usage: number[];
    disk_usage: number[];
    network_io: number[];
    active_connections: number[];
    response_times: number[];
    error_rates: number[];
    timestamps: string[];
  }> {
    const response = await this.makeRequest<any>('/admin/system/metrics', {
      params: { time_range: timeRange },
    });

    return response;
  }

  /**
   * Get system logs
   */
  async getSystemLogs(level: string = 'all', limit: number = 100): Promise<Array<{
    timestamp: string;
    level: string;
    message: string;
    source: string;
    details?: any;
  }>> {
    const response = await this.makeRequest<any>('/admin/system/logs', {
      params: { level, limit },
    });

    return response;
  }

  /**
   * Restart system service
   */
  async restartService(serviceName: string): Promise<{ success: boolean }> {
    this.validateRequired({ serviceName }, ['serviceName']);

    const response = await this.makeRequest<{ success: boolean }>(`/admin/system/services/${serviceName}/restart`, {
      method: 'POST',
    });

    return response;
  }

  /**
   * Get service status
   */
  async getServiceStatus(serviceName?: string): Promise<Array<{
    name: string;
    status: 'running' | 'stopped' | 'error';
    uptime: number;
    memory_usage: number;
    cpu_usage: number;
    last_restart: string;
  }>> {
    const url = serviceName 
      ? `/admin/system/services/${serviceName}/status`
      : '/admin/system/services/status';

    const response = await this.makeRequest<any>(url);
    return response;
  }

  /**
   * Update system maintenance mode
   */
  async setMaintenanceMode(enabled: boolean, message?: string): Promise<{ success: boolean }> {
    const response = await this.makeRequest<{ success: boolean }>('/admin/system/maintenance', {
      method: 'PUT',
      data: { enabled, message },
    });

    return response;
  }

  /**
   * Get maintenance mode status
   */
  async getMaintenanceStatus(): Promise<{
    enabled: boolean;
    message?: string;
    scheduled_start?: string;
    scheduled_end?: string;
  }> {
    const response = await this.makeRequest<any>('/admin/system/maintenance');
    return response;
  }

  /**
   * Clear system cache
   */
  async clearCache(cacheType?: string): Promise<{ success: boolean; cleared_items: number }> {
    const response = await this.makeRequest<{ success: boolean; cleared_items: number }>('/admin/system/cache/clear', {
      method: 'POST',
      data: { cache_type: cacheType },
    });

    return response;
  }

  /**
   * Get cache statistics
   */
  async getCacheStats(): Promise<{
    total_size: number;
    hit_rate: number;
    miss_rate: number;
    eviction_rate: number;
    by_type: Record<string, {
      size: number;
      items: number;
      hit_rate: number;
    }>;
  }> {
    const response = await this.makeRequest<any>('/admin/system/cache/stats');
    return response;
  }
}
