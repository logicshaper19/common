/**
 * Company management client for admin API
 */
import { BaseAdminClient } from '../base/BaseAdminClient';
import { PaginatedResponse } from '../base/types';
import {
  Company,
  CompanyFilter,
  CompanyUpdate,
  CompanyBulkOperation,
} from '../../../types/admin';

export class CompanyClient extends BaseAdminClient {

  /**
   * Get paginated list of companies with filtering
   */
  async getCompanies(filters: CompanyFilter): Promise<PaginatedResponse<Company>> {
    const { page, per_page } = this.validatePagination(filters.page, filters.per_page);
    const validatedFilters = { ...filters, page, per_page };

    const response = await this.makeRequest<PaginatedResponse<Company>>(
      '/admin/companies',
      { params: validatedFilters }
    );

    return response;
  }

  /**
   * Get a single company by ID
   */
  async getCompany(id: string): Promise<Company> {
    this.validateRequired({ id }, ['id']);

    const response = await this.makeRequest<Company>(`/admin/companies/${id}`);
    return response;
  }

  /**
   * Update an existing company
   */
  async updateCompany(id: string, data: CompanyUpdate): Promise<Company> {
    this.validateRequired({ id }, ['id']);

    const response = await this.makeRequest<Company>(`/admin/companies/${id}`, {
      method: 'PUT',
      data,
    });

    return response;
  }

  /**
   * Perform bulk operations on multiple companies
   */
  async bulkCompanyOperation(operation: CompanyBulkOperation): Promise<{ success: boolean; affected_count: number }> {
    this.validateRequired(operation, ['operation', 'company_ids']);

    if (!operation.company_ids.length) {
      throw new Error('At least one company ID is required for bulk operations');
    }

    const response = await this.makeRequest<{ success: boolean; affected_count: number }>(
      '/admin/companies/bulk',
      {
        method: 'POST',
        data: operation,
      }
    );

    return response;
  }

  /**
   * Get company statistics
   */
  async getCompanyStats(): Promise<{
    total_companies: number;
    active_companies: number;
    inactive_companies: number;
    by_type: Record<string, number>;
    by_tier: Record<string, number>;
    by_compliance: Record<string, number>;
    average_transparency_score: number;
    recent_activity: number;
  }> {
    const response = await this.makeRequest<any>('/admin/companies/stats');
    return response;
  }

  /**
   * Update company compliance status
   */
  async updateComplianceStatus(id: string, status: 'compliant' | 'warning' | 'non_compliant' | 'pending_review', notes?: string): Promise<{ success: boolean }> {
    this.validateRequired({ id }, ['id']);

    const response = await this.makeRequest<{ success: boolean }>(
      `/admin/companies/${id}/compliance`,
      {
        method: 'PUT',
        data: { status, notes },
      }
    );

    return response;
  }

  /**
   * Update company subscription tier
   */
  async updateSubscriptionTier(id: string, tier: 'free' | 'basic' | 'premium' | 'enterprise'): Promise<{ success: boolean }> {
    this.validateRequired({ id }, ['id']);

    const response = await this.makeRequest<{ success: boolean }>(
      `/admin/companies/${id}/subscription`,
      {
        method: 'PUT',
        data: { tier },
      }
    );

    return response;
  }

  /**
   * Get company activity summary
   */
  async getCompanyActivity(id: string, days: number = 30): Promise<{
    purchase_orders: number;
    active_users: number;
    transparency_updates: number;
    last_login: string;
    recent_activities: Array<{
      type: string;
      description: string;
      timestamp: string;
      user: string;
    }>;
  }> {
    this.validateRequired({ id }, ['id']);

    const response = await this.makeRequest<any>(`/admin/companies/${id}/activity`, {
      params: { days },
    });

    return response;
  }
}
