/**
 * Company management client for admin API
 */
import { BaseAdminClient } from '../base/BaseAdminClient';
import { CompanyMockProvider } from '../mock/companyMocks';
import { PaginatedResponse } from '../base/types';
import {
  Company,
  CompanyFilter,
  CompanyUpdate,
  CompanyBulkOperation,
} from '../../../types/admin';

export class CompanyClient extends BaseAdminClient {
  private mockProvider = new CompanyMockProvider();

  /**
   * Get paginated list of companies with filtering
   */
  async getCompanies(filters: CompanyFilter): Promise<PaginatedResponse<Company>> {
    try {
      const { page, per_page } = this.validatePagination(filters.page, filters.per_page);
      const validatedFilters = { ...filters, page, per_page };

      const response = await this.makeRequest<PaginatedResponse<Company>>(
        '/admin/companies',
        { params: validatedFilters }
      );

      return response;
    } catch (error) {
      console.warn('Backend not available for companies, using mock data');
      return this.mockProvider.getCompanies(filters);
    }
  }

  /**
   * Get a single company by ID
   */
  async getCompany(id: string): Promise<Company> {
    this.validateRequired({ id }, ['id']);

    try {
      const response = await this.makeRequest<Company>(`/admin/companies/${id}`);
      return response;
    } catch (error) {
      console.warn(`Backend not available for company ${id}, using mock data`);
      return this.mockProvider.getCompany(id);
    }
  }

  /**
   * Update an existing company
   */
  async updateCompany(id: string, data: CompanyUpdate): Promise<Company> {
    this.validateRequired({ id }, ['id']);

    try {
      const response = await this.makeRequest<Company>(`/admin/companies/${id}`, {
        method: 'PUT',
        data,
      });

      return response;
    } catch (error) {
      console.warn(`Backend not available for company ${id} update, using mock data`);
      return this.mockProvider.updateCompany(id, data);
    }
  }

  /**
   * Perform bulk operations on multiple companies
   */
  async bulkCompanyOperation(operation: CompanyBulkOperation): Promise<{ success: boolean; affected_count: number }> {
    this.validateRequired(operation, ['operation', 'company_ids']);

    if (!operation.company_ids.length) {
      throw new Error('At least one company ID is required for bulk operations');
    }

    try {
      const response = await this.makeRequest<{ success: boolean; affected_count: number }>(
        '/admin/companies/bulk',
        {
          method: 'POST',
          data: operation,
        }
      );

      return response;
    } catch (error) {
      console.warn('Backend not available for bulk company operation, using mock data');
      return this.mockProvider.bulkCompanyOperation(operation);
    }
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
    try {
      const response = await this.makeRequest<any>('/admin/companies/stats');
      return response;
    } catch (error) {
      console.warn('Backend not available for company stats, using mock data');
      
      // Generate mock stats
      const allCompanies = await this.mockProvider.getCompanies({
        page: 1,
        per_page: 1000,
      });

      const companies = allCompanies.data;
      
      return {
        total_companies: companies.length,
        active_companies: companies.filter(c => c.is_active).length,
        inactive_companies: companies.filter(c => !c.is_active).length,
        by_type: companies.reduce((acc, c) => {
          acc[c.company_type] = (acc[c.company_type] || 0) + 1;
          return acc;
        }, {} as Record<string, number>),
        by_tier: companies.reduce((acc, c) => {
          acc[c.subscription_tier] = (acc[c.subscription_tier] || 0) + 1;
          return acc;
        }, {} as Record<string, number>),
        by_compliance: companies.reduce((acc, c) => {
          acc[c.compliance_status] = (acc[c.compliance_status] || 0) + 1;
          return acc;
        }, {} as Record<string, number>),
        average_transparency_score: companies.reduce((sum, c) => sum + (c.transparency_score || 0), 0) / companies.length,
        recent_activity: companies.filter(c => 
          c.last_activity && 
          new Date(c.last_activity) > new Date(Date.now() - 7 * 24 * 60 * 60 * 1000)
        ).length,
      };
    }
  }

  /**
   * Update company compliance status
   */
  async updateComplianceStatus(id: string, status: 'compliant' | 'warning' | 'non_compliant' | 'pending_review', notes?: string): Promise<{ success: boolean }> {
    this.validateRequired({ id }, ['id']);

    try {
      const response = await this.makeRequest<{ success: boolean }>(
        `/admin/companies/${id}/compliance`,
        {
          method: 'PUT',
          data: { status, notes },
        }
      );

      return response;
    } catch (error) {
      console.warn(`Backend not available for company ${id} compliance update, using mock data`);
      return { success: true };
    }
  }

  /**
   * Update company subscription tier
   */
  async updateSubscriptionTier(id: string, tier: 'free' | 'basic' | 'premium' | 'enterprise'): Promise<{ success: boolean }> {
    this.validateRequired({ id }, ['id']);

    try {
      const response = await this.makeRequest<{ success: boolean }>(
        `/admin/companies/${id}/subscription`,
        {
          method: 'PUT',
          data: { tier },
        }
      );

      return response;
    } catch (error) {
      console.warn(`Backend not available for company ${id} subscription update, using mock data`);
      return { success: true };
    }
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

    try {
      const response = await this.makeRequest<any>(`/admin/companies/${id}/activity`, {
        params: { days },
      });

      return response;
    } catch (error) {
      console.warn(`Backend not available for company ${id} activity, using mock data`);
      return {
        purchase_orders: 45,
        active_users: 8,
        transparency_updates: 12,
        last_login: new Date().toISOString(),
        recent_activities: [
          {
            type: 'purchase_order',
            description: 'Created new purchase order PO-2024-001',
            timestamp: new Date().toISOString(),
            user: 'John Smith',
          },
        ],
      };
    }
  }
}
