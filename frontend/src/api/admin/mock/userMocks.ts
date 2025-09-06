/**
 * Mock data provider for users
 */
import { MockDataProvider } from './MockDataProvider';
import { PaginatedResponse } from '../base/types';
import {
  AdminUser,
  UserFilter,
  UserCreate,
  UserUpdate,
  UserBulkOperation,
} from '../../../types/admin';

export class UserMockProvider extends MockDataProvider {
  private mockUsers: AdminUser[] = [
    {
      id: 'user-1',
      email: 'john@example.com',
      full_name: 'John Smith',
      role: 'buyer',
      is_active: true,
      company_id: 'company-1',
      company_name: 'ACME Corp',
      created_at: '2024-01-10T10:00:00Z',
      last_login: '2024-01-20T09:30:00Z',
      two_factor_enabled: true,
      login_attempts: 0,
    },
    {
      id: 'user-2',
      email: 'alice@company.com',
      full_name: 'Alice Johnson',
      role: 'seller',
      is_active: true,
      company_id: 'company-2',
      company_name: 'Company Inc',
      created_at: '2024-01-12T14:00:00Z',
      last_login: '2024-01-19T16:45:00Z',
      two_factor_enabled: false,
      login_attempts: 0,
    },
    {
      id: 'user-3',
      email: 'bob@processor.com',
      full_name: 'Bob Wilson',
      role: 'seller',
      is_active: false,
      company_id: 'company-3',
      company_name: 'Processor Ltd',
      created_at: '2024-01-05T08:30:00Z',
      last_login: '2024-01-15T12:20:00Z',
      two_factor_enabled: true,
      login_attempts: 2,
    },
    {
      id: 'user-4',
      email: 'sarah@admin.com',
      full_name: 'Sarah Davis',
      role: 'admin',
      is_active: true,
      company_id: 'company-1',
      company_name: 'ACME Corp',
      created_at: '2023-12-01T09:00:00Z',
      last_login: '2024-01-21T08:15:00Z',
      two_factor_enabled: true,
      login_attempts: 0,
    },
  ];

  async getUsers(filters: UserFilter): Promise<PaginatedResponse<AdminUser>> {
    await this.delay();

    let filtered = [...this.mockUsers];

    // Apply filters
    if (filters.search) {
      filtered = this.applySearch(filtered, filters.search, ['full_name', 'email', 'company_name']);
    }

    if (filters.role) {
      filtered = this.applyEnumFilter(filtered, 'role', filters.role);
    }

    if (filters.is_active !== undefined) {
      filtered = this.applyBooleanFilter(filtered, 'is_active', filters.is_active);
    }

    if (filters.company_id) {
      filtered = filtered.filter(u => u.company_id === filters.company_id);
    }

    if (filters.has_two_factor !== undefined) {
      filtered = this.applyBooleanFilter(filtered, 'two_factor_enabled', filters.has_two_factor);
    }

    if (filters.last_login_after) {
      filtered = this.applyDateRange(filtered, 'last_login', filters.last_login_after);
    }

    if (filters.last_login_before) {
      filtered = this.applyDateRange(filtered, 'last_login', undefined, filters.last_login_before);
    }

    return this.applyPagination(filtered, filters.page, filters.per_page);
  }

  async getUser(id: string): Promise<AdminUser> {
    await this.delay();

    const user = this.mockUsers.find(u => u.id === id);
    if (!user) {
      throw new Error(`User with id ${id} not found`);
    }

    return this.deepClone(user);
  }

  async createUser(data: UserCreate): Promise<AdminUser> {
    await this.delay();

    // Check if email already exists
    if (this.mockUsers.some(u => u.email === data.email)) {
      throw new Error('User with this email already exists');
    }

    const newUser: AdminUser = {
      id: this.generateId('user'),
      email: data.email,
      full_name: data.full_name,
      role: data.role,
      is_active: true,
      company_id: data.company_id,
      company_name: 'Mock Company', // In real implementation, would fetch from company service
      created_at: this.getCurrentTimestamp(),
      last_login: undefined,
      two_factor_enabled: false,
      login_attempts: 0,
    };

    this.mockUsers.push(newUser);
    return this.deepClone(newUser);
  }

  async updateUser(id: string, data: UserUpdate): Promise<AdminUser> {
    await this.delay();

    const userIndex = this.mockUsers.findIndex(u => u.id === id);
    if (userIndex === -1) {
      throw new Error(`User with id ${id} not found`);
    }

    this.mockUsers[userIndex] = {
      ...this.mockUsers[userIndex],
      ...data,
    };

    return this.deepClone(this.mockUsers[userIndex]);
  }

  async deleteUser(id: string): Promise<{ success: boolean }> {
    await this.delay();

    const userIndex = this.mockUsers.findIndex(u => u.id === id);
    if (userIndex === -1) {
      throw new Error(`User with id ${id} not found`);
    }

    this.mockUsers.splice(userIndex, 1);
    return { success: true };
  }

  async bulkUserOperation(operation: UserBulkOperation): Promise<{ success: boolean; affected_count: number }> {
    await this.delay();

    let affectedCount = 0;

    for (const userId of operation.user_ids) {
      const userIndex = this.mockUsers.findIndex(u => u.id === userId);
      if (userIndex === -1) continue;

      switch (operation.operation) {
        case 'activate':
          this.mockUsers[userIndex].is_active = true;
          affectedCount++;
          break;
        case 'deactivate':
          this.mockUsers[userIndex].is_active = false;
          affectedCount++;
          break;
        case 'reset_password':
          // In real implementation, would trigger password reset
          affectedCount++;
          break;
        case 'enable_2fa':
          this.mockUsers[userIndex].two_factor_enabled = true;
          affectedCount++;
          break;
        case 'disable_2fa':
          this.mockUsers[userIndex].two_factor_enabled = false;
          affectedCount++;
          break;
        case 'delete':
          this.mockUsers.splice(userIndex, 1);
          affectedCount++;
          break;
      }
    }

    return {
      success: true,
      affected_count: affectedCount,
    };
  }
}
