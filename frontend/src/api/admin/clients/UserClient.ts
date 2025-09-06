/**
 * User management client for admin API
 */
import { BaseAdminClient } from '../base/BaseAdminClient';
import { UserMockProvider } from '../mock/userMocks';
import { PaginatedResponse } from '../base/types';
import {
  AdminUser,
  UserFilter,
  UserCreate,
  UserUpdate,
  UserBulkOperation,
} from '../../../types/admin';

export class UserClient extends BaseAdminClient {
  private mockProvider = new UserMockProvider();

  /**
   * Get paginated list of users with filtering
   */
  async getUsers(filters: UserFilter): Promise<PaginatedResponse<AdminUser>> {
    try {
      const { page, per_page } = this.validatePagination(filters.page, filters.per_page);
      const validatedFilters = { ...filters, page, per_page };

      const response = await this.makeRequest<PaginatedResponse<AdminUser>>(
        '/admin/users',
        { params: validatedFilters }
      );

      return response;
    } catch (error) {
      console.warn('Backend not available for users, using mock data');
      return this.mockProvider.getUsers(filters);
    }
  }

  /**
   * Get a single user by ID
   */
  async getUser(id: string): Promise<AdminUser> {
    this.validateRequired({ id }, ['id']);

    try {
      const response = await this.makeRequest<AdminUser>(`/admin/users/${id}`);
      return response;
    } catch (error) {
      console.warn(`Backend not available for user ${id}, using mock data`);
      return this.mockProvider.getUser(id);
    }
  }

  /**
   * Create a new user
   */
  async createUser(data: UserCreate): Promise<AdminUser> {
    this.validateRequired(data, ['email', 'full_name', 'role', 'company_id']);

    try {
      const response = await this.makeRequest<AdminUser>('/admin/users', {
        method: 'POST',
        data,
      });

      return response;
    } catch (error) {
      console.warn('Backend not available for user creation, using mock data');
      return this.mockProvider.createUser(data);
    }
  }

  /**
   * Update an existing user
   */
  async updateUser(id: string, data: UserUpdate): Promise<AdminUser> {
    this.validateRequired({ id }, ['id']);

    try {
      const response = await this.makeRequest<AdminUser>(`/admin/users/${id}`, {
        method: 'PUT',
        data,
      });

      return response;
    } catch (error) {
      console.warn(`Backend not available for user ${id} update, using mock data`);
      return this.mockProvider.updateUser(id, data);
    }
  }

  /**
   * Delete a user
   */
  async deleteUser(id: string): Promise<{ success: boolean }> {
    this.validateRequired({ id }, ['id']);

    try {
      await this.makeRequest(`/admin/users/${id}`, {
        method: 'DELETE',
      });

      return { success: true };
    } catch (error) {
      console.warn(`Backend not available for user ${id} deletion, using mock data`);
      return this.mockProvider.deleteUser(id);
    }
  }

  /**
   * Perform bulk operations on multiple users
   */
  async bulkUserOperation(operation: UserBulkOperation): Promise<{ success: boolean; affected_count: number }> {
    this.validateRequired(operation, ['operation', 'user_ids']);

    if (!operation.user_ids.length) {
      throw new Error('At least one user ID is required for bulk operations');
    }

    try {
      const response = await this.makeRequest<{ success: boolean; affected_count: number }>(
        '/admin/users/bulk',
        {
          method: 'POST',
          data: operation,
        }
      );

      return response;
    } catch (error) {
      console.warn('Backend not available for bulk user operation, using mock data');
      return this.mockProvider.bulkUserOperation(operation);
    }
  }

  /**
   * Reset user password
   */
  async resetUserPassword(id: string, sendEmail: boolean = true): Promise<{ success: boolean; temporary_password?: string }> {
    this.validateRequired({ id }, ['id']);

    try {
      const response = await this.makeRequest<{ success: boolean; temporary_password?: string }>(
        `/admin/users/${id}/reset-password`,
        {
          method: 'POST',
          data: { send_email: sendEmail },
        }
      );

      return response;
    } catch (error) {
      console.warn(`Backend not available for user ${id} password reset, using mock data`);
      return {
        success: true,
        temporary_password: sendEmail ? undefined : 'temp123456',
      };
    }
  }

  /**
   * Enable/disable two-factor authentication for user
   */
  async toggleTwoFactor(id: string, enabled: boolean): Promise<{ success: boolean }> {
    this.validateRequired({ id }, ['id']);

    try {
      const response = await this.makeRequest<{ success: boolean }>(
        `/admin/users/${id}/two-factor`,
        {
          method: 'PUT',
          data: { enabled },
        }
      );

      return response;
    } catch (error) {
      console.warn(`Backend not available for user ${id} 2FA toggle, using mock data`);
      return { success: true };
    }
  }

  /**
   * Get user activity log
   */
  async getUserActivity(id: string, limit: number = 50): Promise<{
    activities: Array<{
      id: string;
      action: string;
      resource: string;
      timestamp: string;
      ip_address: string;
      user_agent: string;
    }>;
  }> {
    this.validateRequired({ id }, ['id']);

    try {
      const response = await this.makeRequest<any>(`/admin/users/${id}/activity`, {
        params: { limit },
      });

      return response;
    } catch (error) {
      console.warn(`Backend not available for user ${id} activity, using mock data`);
      return {
        activities: [
          {
            id: 'activity-1',
            action: 'login',
            resource: 'session',
            timestamp: new Date().toISOString(),
            ip_address: '192.168.1.1',
            user_agent: 'Mozilla/5.0',
          },
        ],
      };
    }
  }

  /**
   * Get user statistics
   */
  async getUserStats(): Promise<{
    total_users: number;
    active_users: number;
    inactive_users: number;
    by_role: Record<string, number>;
    by_company_type: Record<string, number>;
    recent_logins: number;
    two_factor_enabled: number;
  }> {
    try {
      const response = await this.makeRequest<any>('/admin/users/stats');
      return response;
    } catch (error) {
      console.warn('Backend not available for user stats, using mock data');
      
      // Generate mock stats
      const allUsers = await this.mockProvider.getUsers({
        page: 1,
        per_page: 1000,
      });

      const users = allUsers.data;
      
      return {
        total_users: users.length,
        active_users: users.filter(u => u.is_active).length,
        inactive_users: users.filter(u => !u.is_active).length,
        by_role: users.reduce((acc, u) => {
          acc[u.role] = (acc[u.role] || 0) + 1;
          return acc;
        }, {} as Record<string, number>),
        by_company_type: {}, // Would need company data to populate
        recent_logins: users.filter(u => 
          u.last_login && 
          new Date(u.last_login) > new Date(Date.now() - 24 * 60 * 60 * 1000)
        ).length,
        two_factor_enabled: users.filter(u => u.two_factor_enabled).length,
      };
    }
  }
}
