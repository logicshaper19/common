/**
 * Farm Management API Service
 * Handles all farm-related API calls for the origin dashboard
 */
import { apiClient } from '../lib/api';

// Types
export interface FarmInformation {
  id: string;
  farm_name: string;
  farm_code: string;
  location: {
    latitude: number;
    longitude: number;
    address: string;
    region: string;
    country: string;
  };
  farm_type: 'plantation' | 'smallholder' | 'cooperative' | 'mill';
  total_area_hectares: number;
  certifications: string[];
  eudr_status: 'compliant' | 'non_compliant' | 'pending';
  last_harvest_date?: string;
  contact_person: {
    name: string;
    email: string;
    phone: string;
  };
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface FarmCreateRequest {
  farm_name: string;
  farm_code: string;
  location: {
    latitude: number;
    longitude: number;
    address: string;
    region: string;
    country: string;
  };
  farm_type: 'plantation' | 'smallholder' | 'cooperative' | 'mill';
  total_area_hectares: number;
  certifications: string[];
  contact_person: {
    name: string;
    email: string;
    phone: string;
  };
}

export interface FarmUpdateRequest extends Partial<FarmCreateRequest> {
  is_active?: boolean;
}

export interface FarmFilters {
  farm_type?: string;
  eudr_status?: string;
  region?: string;
  is_active?: boolean;
  page?: number;
  per_page?: number;
}

export interface FarmListResponse {
  company_id: string;
  total_farms: number;
  farms: FarmInformation[];
}

export interface CompanyCapabilities {
  company_id: string;
  company_name: string;
  company_type: string;
  can_create_pos: boolean;
  can_confirm_pos: boolean;
  has_farm_structure: boolean;
  is_farm_capable: boolean;
  farm_types: string[];
  can_act_as_originator: boolean;
  total_farms: number;
  total_farm_area_hectares: number;
}

export interface BatchCreationRequest {
  batch_data: {
    batch_number: string;
    product_type: string;
    total_quantity: number;
    unit: string;
    harvest_date: string;
    quality_parameters?: Record<string, any>;
  };
  farm_contributions: Array<{
    farm_id: string;
    quantity: number;
    harvest_date: string;
    quality_score?: number;
  }>;
}

export interface BatchCreationResponse {
  batch_id: string;
  batch_number: string;
  total_quantity: number;
  farm_contributions: Array<{
    farm_id: string;
    farm_name: string;
    quantity: number;
    quality_score: number;
  }>;
  created_at: string;
}

export interface BatchTraceabilityResponse {
  batch_id: string;
  batch_number: string;
  product_type: string;
  total_quantity: number;
  unit: string;
  harvest_date: string;
  farms: Array<{
    farm_id: string;
    farm_name: string;
    farm_type: string;
    quantity: number;
    quality_score: number;
    coordinates: {
      latitude: number;
      longitude: number;
    };
    certifications: string[];
    compliance_status: string;
  }>;
  regulatory_compliance: {
    eudr_compliant: boolean;
    us_compliant: boolean;
    overall_status: string;
  };
  traceability_score: number;
}

// API Service
export const farmApi = {
  // Farm Management
  async getCompanyFarms(companyId: string): Promise<FarmListResponse> {
    const response = await apiClient.get(`/farm-management/company/${companyId}/farms`);
    return response.data;
  },

  async getCompanyCapabilities(companyId: string): Promise<CompanyCapabilities> {
    const response = await apiClient.get(`/farm-management/company/${companyId}/capabilities`);
    return response.data;
  },

  async createFarm(farmData: FarmCreateRequest): Promise<FarmInformation> {
    const response = await apiClient.post('/farm-management/farms', farmData);
    return response.data;
  },

  async updateFarm(farmId: string, farmData: FarmUpdateRequest): Promise<FarmInformation> {
    const response = await apiClient.put(`/farm-management/farms/${farmId}`, farmData);
    return response.data;
  },

  async deleteFarm(farmId: string): Promise<void> {
    await apiClient.delete(`/farm-management/farms/${farmId}`);
  },

  async getFarm(farmId: string): Promise<FarmInformation> {
    const response = await apiClient.get(`/farm-management/farms/${farmId}`);
    return response.data;
  },

  // Batch Management
  async createBatchWithFarmContributions(batchRequest: BatchCreationRequest): Promise<BatchCreationResponse> {
    const response = await apiClient.post('/farm-management/batches', batchRequest);
    return response.data;
  },

  async getBatchTraceability(batchId: string): Promise<BatchTraceabilityResponse> {
    const response = await apiClient.get(`/farm-management/batches/${batchId}/traceability`);
    return response.data;
  },

  async getBatchComplianceStatus(batchId: string): Promise<any> {
    const response = await apiClient.get(`/farm-management/batches/${batchId}/compliance`);
    return response.data;
  },

  // Farm Search and Filtering
  async searchFarms(query: string, filters?: FarmFilters): Promise<FarmInformation[]> {
    const params = new URLSearchParams();
    params.append('q', query);
    
    if (filters) {
      Object.entries(filters).forEach(([key, value]) => {
        if (value !== undefined && value !== null && value !== '') {
          params.append(key, value.toString());
        }
      });
    }
    
    const response = await apiClient.get(`/farm-management/farms/search?${params.toString()}`);
    return response.data;
  },

  // Farm Analytics
  async getFarmAnalytics(companyId: string): Promise<any> {
    const response = await apiClient.get(`/farm-management/company/${companyId}/analytics`);
    return response.data;
  },

  // Farm Compliance
  async getFarmComplianceStatus(farmId: string): Promise<any> {
    const response = await apiClient.get(`/farm-management/farms/${farmId}/compliance`);
    return response.data;
  },

  async updateFarmCompliance(farmId: string, complianceData: any): Promise<any> {
    const response = await apiClient.put(`/farm-management/farms/${farmId}/compliance`, complianceData);
    return response.data;
  }
};

export default farmApi;
