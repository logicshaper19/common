/**
 * User management client for admin API
 */
import { BaseAdminClient } from '../base/BaseAdminClient';
import { PaginatedResponse } from '../base/types';
import {
  AdminUser,
  UserFilter,
  UserCreate,
  UserUpdate,
  UserBulkOperation,
} from '../../../types/admin';

export class UserClient extends BaseAdminClient {

  /**
   * Get paginated list of users with filtering
   */
  async getUsers(filters: UserFilter): Promise<PaginatedResponse<AdminUser>> {
    const { page, per_page } = this.validatePagination(filters.page, filters.per_page);
    const validatedFilters = { ...filters, page, per_page };

    const response = await this.makeRequest<PaginatedResponse<AdminUser>>(
      '/admin/users',
      { params: validatedFilters }
    );

    return response;
  }

  /**
   * Get a single user by ID
   */
  async getUser(id: string): Promise<AdminUser> {
    this.validateRequired({ id }, ['id']);

    const response = await this.makeRequest<AdminUser>(`/admin/users/${id}`);
    return response;
  }

  /**
   * Create a new user
   */
  async createUser(data: UserCreate): Promise<AdminUser> {
    this.validateRequired(data, ['email', 'full_name', 'role', 'company_id']);

    const response = await this.makeRequest<AdminUser>('/admin/users', {
      method: 'POST',
      data,
    });

    return response;
  }

  /**
   * Update an existing user
   */
  async updateUser(id: string, data: UserUpdate): Promise<AdminUser> {
    this.validateRequired({ id }, ['id']);

    const response = await this.makeRequest<AdminUser>(`/admin/users/${id}`, {
      method: 'PUT',
      data,
    });

    return response;
  }

  /**
   * Delete a user
   */
  async deleteUser(id: string): Promise<{ success: boolean }> {
    this.validateRequired({ id }, ['id']);

    const response = await this.makeRequest<{ success: boolean }>(`/admin/users/${id}`, {
      method: 'DELETE',
    });

    return { success: true };
  }

  /**
   * Perform bulk operations on multiple users
   */
  async bulkUserOperation(operation: UserBulkOperation): Promise<{ success: boolean; affected_count: number }> {
    this.validateRequired(operation, ['operation', 'user_ids']);

    if (!operation.user_ids.length) {
      throw new Error('At least one user ID is required for bulk operations');
    }

    const response = await this.makeRequest<{ success: boolean; affected_count: number }>(
      '/admin/users/bulk',
      {
        method: 'POST',
        data: operation,
      }
    );

    return response;
  }

  /**
   * Reset user password
   */
  async resetUserPassword(id: string, sendEmail: boolean = true): Promise<{ success: boolean; temporary_password?: string }> {
    this.validateRequired({ id }, ['id']);

    const response = await this.makeRequest<{ success: boolean; temporary_password?: string }>(
      `/admin/users/${id}/reset-password`,
      {
        method: 'POST',
        data: { send_email: sendEmail },
      }
    );

    return response;
  }

  /**
   * Toggle user two-factor authentication
   */
  async toggleUserTwoFactor(id: string, enabled: boolean): Promise<{ success: boolean }> {
    this.validateRequired({ id }, ['id']);

    const response = await this.makeRequest<{ success: boolean }>(
      `/admin/users/${id}/two-factor`,
      {
        method: 'PUT',
        data: { enabled },
      }
    );

    return response;
  }

  /**
   * Get user login history
   */
  async getUserLoginHistory(id: string, days: number = 30): Promise<Array<{
    timestamp: string;
    ip_address: string;
    user_agent: string;
    success: boolean;
    failure_reason?: string;
  }>> {
    this.validateRequired({ id }, ['id']);

    const response = await this.makeRequest<any>(`/admin/users/${id}/login-history`, {
      params: { days },
    });

    return response;
  }

  /**
   * Get user statistics
   */
  async getUserStats(): Promise<{
    total_users: number;
    active_users: number;
    inactive_users: number;
    by_role: Record<string, number>;
    by_company: Record<string, number>;
    two_factor_enabled: number;
    recent_logins: number;
    failed_login_attempts: number;
  }> {
    const response = await this.makeRequest<any>('/admin/users/stats');
    return response;
  }

  /**
   * Update user status (activate/deactivate)
   */
  async updateUserStatus(id: string, isActive: boolean): Promise<{ success: boolean }> {
    this.validateRequired({ id }, ['id']);

    const response = await this.makeRequest<{ success: boolean }>(
      `/admin/users/${id}/status`,
      {
        method: 'PUT',
        data: { is_active: isActive },
      }
    );

    return response;
  }

  /**
   * Get user activity summary
   */
  async getUserActivity(id: string, days: number = 30): Promise<{
    login_count: number;
    purchase_orders_created: number;
    last_activity: string;
    recent_activities: Array<{
      type: string;
      description: string;
      timestamp: string;
    }>;
  }> {
    this.validateRequired({ id }, ['id']);

    const response = await this.makeRequest<any>(`/admin/users/${id}/activity`, {
      params: { days },
    });

    return response;
  }
}
