/**
 * API client for transparency visualization endpoints
 */
import { apiClient } from './api';
import {
  TransparencyMetrics,
  SupplyChainVisualization,
  CompanyTransparencySummary,
  MultiClientDashboard,
  GapAnalysisItem,
  TransparencyFilters,
  TransparencyUpdate,
} from '../types/transparency';

export class TransparencyApi {
  /**
   * Get transparency metrics for a company
   */
  async getTransparencyMetrics(companyId: string): Promise<TransparencyMetrics> {
    const response = await apiClient.get<TransparencyMetrics>(`/transparency/${companyId}`);
    return response.data;
  }

  /**
   * Get supply chain visualization for a purchase order
   */
  async getSupplyChainVisualization(
    poId: string,
    includeGapAnalysis: boolean = true
  ): Promise<SupplyChainVisualization> {
    const response = await apiClient.get<SupplyChainVisualization>(`/transparency/po/${poId}`, {
      params: { include_gap_analysis: includeGapAnalysis },
    });
    return response.data;
  }

  /**
   * Get gap analysis for a company
   */
  async getGapAnalysis(companyId: string): Promise<GapAnalysisItem[]> {
    const response = await apiClient.get<GapAnalysisItem[]>(`/transparency/${companyId}/gaps`);
    return response.data;
  }

  /**
   * Get multi-client dashboard for consultants
   */
  async getMultiClientDashboard(consultantId: string): Promise<MultiClientDashboard> {
    const response = await apiClient.get<MultiClientDashboard>(`/transparency/consultant/${consultantId}/dashboard`);
    return response.data;
  }

  /**
   * Trigger transparency recalculation
   */
  async recalculateTransparency(companyId: string): Promise<void> {
    await apiClient.post('/transparency/recalculate', { company_id: companyId });
  }

  /**
   * Get filtered transparency data
   */
  async getFilteredTransparencyData(
    companyId: string,
    filters: TransparencyFilters
  ): Promise<SupplyChainVisualization> {
    const response = await apiClient.post<SupplyChainVisualization>(`/transparency/${companyId}/filtered`, filters);
    return response.data;
  }

  /**
   * Submit transparency update
   */
  async submitTransparencyUpdate(update: TransparencyUpdate): Promise<void> {
    await apiClient.post('/transparency/updates', update);
  }

  /**
   * Get company transparency summary
   */
  async getCompanyTransparencySummary(companyId: string): Promise<CompanyTransparencySummary> {
    const response = await apiClient.get<CompanyTransparencySummary>(`/transparency/${companyId}/summary`);
    return response.data;
  }

  /**
   * Get transparency trends over time
   */
  async getTransparencyTrends(companyId: string, days: number = 30): Promise<{
    dates: string[];
    ttm_scores: number[];
    ttp_scores: number[];
    overall_scores: number[];
    traced_percentages: number[];
  }> {
    const response = await apiClient.get(`/transparency/${companyId}/trends`, {
      params: { days },
    });
    return response.data;
  }

  /**
   * Export transparency report
   */
  async exportTransparencyReport(companyId: string, format: 'pdf' | 'excel' = 'pdf'): Promise<Blob> {
    const response = await apiClient.get(`/transparency/${companyId}/export`, {
      params: { format },
      responseType: 'blob',
    });
    return response.data;
  }
}

// Export singleton instance
export const transparencyApi = new TransparencyApi();

// Legacy exports for backward compatibility
export const getTransparencyMetrics = (companyId: string) => transparencyApi.getTransparencyMetrics(companyId);
export const getSupplyChainVisualization = (poId: string, includeGapAnalysis?: boolean) => 
  transparencyApi.getSupplyChainVisualization(poId, includeGapAnalysis);
export const getGapAnalysis = (companyId: string) => transparencyApi.getGapAnalysis(companyId);
export const getMultiClientDashboard = (consultantId: string) => transparencyApi.getMultiClientDashboard(consultantId);
export const recalculateTransparency = (companyId: string) => transparencyApi.recalculateTransparency(companyId);
export const getFilteredTransparencyData = (companyId: string, filters: TransparencyFilters) => 
  transparencyApi.getFilteredTransparencyData(companyId, filters);
export const submitTransparencyUpdate = (update: TransparencyUpdate) => transparencyApi.submitTransparencyUpdate(update);
export const getCompanyTransparencySummary = (companyId: string) => transparencyApi.getCompanyTransparencySummary(companyId);
export const getTransparencyTrends = (companyId: string, days?: number) => transparencyApi.getTransparencyTrends(companyId, days);
export const exportTransparencyReport = (companyId: string, format?: 'pdf' | 'excel') => 
  transparencyApi.exportTransparencyReport(companyId, format);
