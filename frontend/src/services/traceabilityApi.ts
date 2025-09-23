/**
 * Traceability API Service
 * Handles traceability data for purchase orders and supply chain transparency
 */
import { apiClient } from '../lib/api';

export interface SupplyChainTraceData {
  po_id: string;
  po_number: string;
  trace_depth: number;
  is_traced_to_mill: boolean;
  is_traced_to_plantation: boolean;
  trace_path: string; // This is actually a string from the backend
  origin_company_id?: string;
  origin_company_type?: string;
  path_companies?: string[];
}

export interface SupplyChainTraceResponse {
  success: boolean;
  data: SupplyChainTraceData | null;
  message: string;
}

export interface TransparencyMetrics {
  transparency_to_mill_percentage: number;
  transparency_to_plantation_percentage: number;
  total_volume: number;
  total_pos: number;
  traced_pos: number;
  calculation_timestamp: string;
}

export interface TransparencyGap {
  gap_type: 'mill' | 'plantation';
  po_id: string;
  po_number: string;
  quantity: number;
  unit: string;
  buyer_company: string;
  seller_company: string;
  gap_reason: string;
  created_at: string;
}

export interface TransparencyGapsResponse {
  success: boolean;
  gaps: TransparencyGap[];
  total_gaps: number;
  message: string;
}

export interface CompanyInfo {
  id: string;
  name: string;
  company_type: string;
  email?: string;
  location?: string;
}

export const traceabilityApi = {
  /**
   * Get supply chain trace for a specific purchase order
   */
  getSupplyChainTrace: async (poId: string): Promise<SupplyChainTraceData> => {
    const response = await apiClient.get(`/transparency/v2/purchase-orders/${poId}/trace`);
    const traceResponse: SupplyChainTraceResponse = response.data;
    
    if (!traceResponse.success || !traceResponse.data) {
      throw new Error(traceResponse.message || 'Failed to get traceability data');
    }
    
    return traceResponse.data;
  },

  /**
   * Get transparency metrics for a company
   */
  getTransparencyMetrics: async (companyId: string): Promise<TransparencyMetrics> => {
    const response = await apiClient.get(`/transparency/${companyId}`);
    return response.data;
  },

  /**
   * Get transparency gaps for a company
   */
  getTransparencyGaps: async (
    companyId: string, 
    gapType?: 'mill' | 'plantation',
    limit: number = 50
  ): Promise<TransparencyGapsResponse> => {
    const params: any = { limit };
    if (gapType) {
      params.gap_type = gapType;
    }
    
    const response = await apiClient.get(`/transparency/v2/companies/${companyId}/gaps`, {
      params
    });
    return response.data;
  },

  /**
   * Refresh transparency data
   */
  refreshTransparencyData: async (companyId: string): Promise<void> => {
    await apiClient.post('/transparency/v2/refresh', {
      company_id: companyId
    });
  },

  /**
   * Get company information by ID
   */
  getCompanyInfo: async (companyId: string): Promise<CompanyInfo> => {
    const response = await apiClient.get(`/companies/${companyId}`);
    return response.data;
  },

  /**
   * Get batch details with origin data
   */
  getBatchDetails: async (batchId: string): Promise<any> => {
    const response = await apiClient.get(`/batches/${batchId}`);
    return response.data;
  }
};

export default traceabilityApi;
