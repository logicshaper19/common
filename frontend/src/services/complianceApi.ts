/**
 * Compliance API Service
 * Following the project plan: Frontend integration with compliance endpoints
 */
import { apiClient } from '../lib/api';

export interface ComplianceCheck {
  check_name: string;
  status: 'pass' | 'fail' | 'warning' | 'pending';
  evidence?: any;
  checked_at?: string;
}

export interface RegulationCompliance {
  status: 'pass' | 'fail' | 'warning' | 'pending';
  checks_passed: number;
  total_checks: number;
  checks: ComplianceCheck[];
}

export interface ComplianceOverviewResponse {
  po_id: string;
  compliance_overview: {
    [regulation: string]: RegulationCompliance;
  };
  retrieved_at?: string;
}

export interface ComplianceEvaluationResponse {
  po_id: string;
  regulation: string;
  evaluation_completed: boolean;
  checks_performed: number;
  results: ComplianceCheck[];
}

export interface ComplianceDashboardItem {
  po_id: string;
  po_number: string;
  regulation: string;
  check_name: string;
  status: string;
  checked_at?: string;
  buyer_company: string;
  seller_company: string;
  product: string;
}

export interface ComplianceDashboardResponse {
  total_count: number;
  returned_count: number;
  offset: number;
  limit: number;
  filters: {
    regulation?: string;
    status?: string;
  };
  results: ComplianceDashboardItem[];
}

export interface AvailableRegulationsResponse {
  available_regulations: string[];
  by_sector: {
    [sectorId: string]: {
      name: string;
      regulations: string[];
    };
  };
}

class ComplianceApiService {
  private baseUrl = '/api/v1/compliance';

  /**
   * Get compliance overview for a purchase order
   */
  async getComplianceOverview(poId: string): Promise<ComplianceOverviewResponse> {
    const response = await apiClient.get(`${this.baseUrl}/overview/${poId}`);
    return response.data;
  }

  /**
   * Manually evaluate compliance for a PO and regulation
   */
  async evaluateCompliance(poId: string, regulation: string): Promise<ComplianceEvaluationResponse> {
    const response = await apiClient.post(`${this.baseUrl}/evaluate/${poId}`, null, {
      params: { regulation }
    });
    return response.data;
  }

  /**
   * Generate and download compliance report PDF
   */
  async generateComplianceReport(poId: string, regulations?: string[]): Promise<Blob> {
    const params: any = {};
    if (regulations && regulations.length > 0) {
      params.regulations = regulations.join(',');
    }

    const response = await apiClient.get(`${this.baseUrl}/report/${poId}`, {
      params,
      responseType: 'blob'
    });

    return response.data;
  }

  /**
   * Get compliance dashboard data
   */
  async getComplianceDashboard(options: {
    regulation?: string;
    status?: string;
    limit?: number;
    offset?: number;
  } = {}): Promise<ComplianceDashboardResponse> {
    const params = {
      limit: 50,
      offset: 0,
      ...options
    };

    const response = await apiClient.get(`${this.baseUrl}/dashboard`, { params });
    return response.data;
  }

  /**
   * Get available regulations for compliance checking
   */
  async getAvailableRegulations(): Promise<AvailableRegulationsResponse> {
    const response = await apiClient.get(`${this.baseUrl}/regulations`);
    return response.data;
  }

  /**
   * Helper method to get compliance status summary
   */
  getComplianceStatusSummary(complianceOverview: { [regulation: string]: RegulationCompliance }) {
    const regulations = Object.keys(complianceOverview);
    
    if (regulations.length === 0) {
      return {
        overallStatus: 'unknown',
        totalRegulations: 0,
        passedRegulations: 0,
        failedRegulations: 0,
        warningRegulations: 0
      };
    }

    let passedRegulations = 0;
    let failedRegulations = 0;
    let warningRegulations = 0;

    regulations.forEach(regulation => {
      const status = complianceOverview[regulation].status;
      if (status === 'pass') {
        passedRegulations++;
      } else if (status === 'fail') {
        failedRegulations++;
      } else if (status === 'warning') {
        warningRegulations++;
      }
    });

    let overallStatus: string;
    if (failedRegulations > 0) {
      overallStatus = 'fail';
    } else if (warningRegulations > 0) {
      overallStatus = 'warning';
    } else if (passedRegulations === regulations.length) {
      overallStatus = 'pass';
    } else {
      overallStatus = 'pending';
    }

    return {
      overallStatus,
      totalRegulations: regulations.length,
      passedRegulations,
      failedRegulations,
      warningRegulations
    };
  }

  /**
   * Helper method to format check names for display
   */
  formatCheckName(checkName: string): string {
    return checkName
      .replace(/_/g, ' ')
      .replace(/\b\w/g, l => l.toUpperCase());
  }

  /**
   * Helper method to get status color class
   */
  getStatusColorClass(status: string): string {
    switch (status) {
      case 'pass':
        return 'text-green-600 bg-green-100';
      case 'fail':
        return 'text-red-600 bg-red-100';
      case 'warning':
        return 'text-yellow-600 bg-yellow-100';
      case 'pending':
        return 'text-gray-600 bg-gray-100';
      default:
        return 'text-gray-600 bg-gray-100';
    }
  }

  /**
   * Helper method to determine if compliance is critical
   */
  isCriticalCompliance(complianceOverview: { [regulation: string]: RegulationCompliance }): boolean {
    return Object.values(complianceOverview).some(regulation => regulation.status === 'fail');
  }

  /**
   * Helper method to get compliance progress percentage
   */
  getComplianceProgress(complianceOverview: { [regulation: string]: RegulationCompliance }): number {
    const regulations = Object.values(complianceOverview);
    if (regulations.length === 0) return 0;

    const totalChecks = regulations.reduce((sum, reg) => sum + reg.total_checks, 0);
    const passedChecks = regulations.reduce((sum, reg) => sum + reg.checks_passed, 0);

    return totalChecks > 0 ? Math.round((passedChecks / totalChecks) * 100) : 0;
  }
}

export const complianceApi = new ComplianceApiService();
