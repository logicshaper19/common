/**
 * Mock data provider for companies
 */
import { MockDataProvider } from './MockDataProvider';
import { PaginatedResponse } from '../base/types';
import {
  Company,
  CompanyFilter,
  CompanyUpdate,
  CompanyBulkOperation,
} from '../../../types/admin';

export class CompanyMockProvider extends MockDataProvider {
  private mockCompanies: Company[] = [
    {
      id: 'company-1',
      name: 'ACME Corp',
      email: 'contact@acme.com',
      company_type: 'brand',
      subscription_tier: 'premium',
      compliance_status: 'compliant',
      transparency_score: 92,
      user_count: 15,
      po_count: 234,
      last_activity: '2024-01-20T10:30:00Z',
      website: 'https://acme.com',
      is_active: true,
    },
    {
      id: 'company-2',
      name: 'Company Inc',
      email: 'hello@company.com',
      company_type: 'processor',
      subscription_tier: 'basic',
      compliance_status: 'warning',
      transparency_score: 78,
      user_count: 8,
      po_count: 156,
      last_activity: '2024-01-19T15:20:00Z',
      website: 'https://company.com',
      is_active: true,
    },
    {
      id: 'company-3',
      name: 'Processor Ltd',
      email: 'info@processor.com',
      company_type: 'processor',
      subscription_tier: 'free',
      compliance_status: 'non_compliant',
      transparency_score: 45,
      user_count: 3,
      po_count: 67,
      last_activity: '2024-01-18T09:15:00Z',
      website: 'https://processor.com',
      is_active: false,
    },
    {
      id: 'company-4',
      name: 'Organic Farms Co',
      email: 'contact@organicfarms.com',
      company_type: 'originator',
      subscription_tier: 'premium',
      compliance_status: 'compliant',
      transparency_score: 95,
      user_count: 12,
      po_count: 189,
      last_activity: '2024-01-21T14:45:00Z',
      website: 'https://organicfarms.com',
      is_active: true,
    },
  ];

  async getCompanies(filters: CompanyFilter): Promise<PaginatedResponse<Company>> {
    await this.delay();

    let filtered = [...this.mockCompanies];

    // Apply filters
    if (filters.search) {
      filtered = this.applySearch(filtered, filters.search, ['name', 'email', 'website']);
    }

    if (filters.company_type) {
      filtered = this.applyEnumFilter(filtered, 'company_type', filters.company_type);
    }

    if (filters.subscription_tier) {
      filtered = this.applyEnumFilter(filtered, 'subscription_tier', filters.subscription_tier);
    }

    if (filters.compliance_status) {
      filtered = this.applyEnumFilter(filtered, 'compliance_status', filters.compliance_status);
    }

    if (filters.is_active !== undefined) {
      filtered = this.applyBooleanFilter(filtered, 'is_active', filters.is_active);
    }

    if (filters.created_after) {
      filtered = this.applyDateRange(filtered, 'last_activity', filters.created_after);
    }

    if (filters.created_before) {
      filtered = this.applyDateRange(filtered, 'last_activity', undefined, filters.created_before);
    }

    if (filters.min_transparency_score !== undefined || filters.max_transparency_score !== undefined) {
      filtered = this.applyNumericRange(filtered, 'transparency_score', filters.min_transparency_score, filters.max_transparency_score);
    }

    return this.applyPagination(filtered, filters.page, filters.per_page);
  }

  async getCompany(id: string): Promise<Company> {
    await this.delay();

    const company = this.mockCompanies.find(c => c.id === id);
    if (!company) {
      throw new Error(`Company with id ${id} not found`);
    }

    return this.deepClone(company);
  }

  async updateCompany(id: string, data: CompanyUpdate): Promise<Company> {
    await this.delay();

    const companyIndex = this.mockCompanies.findIndex(c => c.id === id);
    if (companyIndex === -1) {
      throw new Error(`Company with id ${id} not found`);
    }

    this.mockCompanies[companyIndex] = {
      ...this.mockCompanies[companyIndex],
      ...data,
    };

    return this.deepClone(this.mockCompanies[companyIndex]);
  }

  async bulkCompanyOperation(operation: CompanyBulkOperation): Promise<{ success: boolean; affected_count: number }> {
    await this.delay();

    let affectedCount = 0;

    for (const companyId of operation.company_ids) {
      const companyIndex = this.mockCompanies.findIndex(c => c.id === companyId);
      if (companyIndex === -1) continue;

      switch (operation.operation) {
        case 'activate':
          this.mockCompanies[companyIndex].is_active = true;
          affectedCount++;
          break;
        case 'deactivate':
          this.mockCompanies[companyIndex].is_active = false;
          affectedCount++;
          break;
        case 'upgrade_tier':
          if (operation.new_tier) {
            this.mockCompanies[companyIndex].subscription_tier = operation.new_tier;
          }
          affectedCount++;
          break;
        case 'downgrade_tier':
          if (operation.new_tier) {
            this.mockCompanies[companyIndex].subscription_tier = operation.new_tier;
          }
          affectedCount++;
          break;
        case 'compliance_review':
          this.mockCompanies[companyIndex].compliance_status = 'pending_review';
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
