/**
 * Origin Data API Service
 * Handles all origin-related API calls for the origin dashboard
 */
import { apiClient } from '../lib/api';

// Types
export interface OriginDataRecord {
  id: string;
  farm_name: string;
  batch_id: string;
  harvest_date: string;
  date_of_recording: string;
  eudr_status: 'compliant' | 'non_compliant' | 'pending' | 'not_applicable';
  purchase_order_id: string;
  product_type: string;
  geographic_coordinates: {
    latitude: number;
    longitude: number;
  };
  certifications: string[];
  quality_score?: number;
  status: 'draft' | 'submitted' | 'verified' | 'rejected';
  created_by: string;
  last_updated: string;
}

export interface OriginDataValidationRequest {
  purchase_order_id: string;
  geographic_coordinates: {
    latitude: number;
    longitude: number;
  };
  harvest_date: string;
  certifications: string[];
  farm_information?: {
    farm_name: string;
    farm_id?: string;
    farmer_name?: string;
    contact_info?: string;
  };
  quality_parameters?: Record<string, any>;
}

export interface OriginDataValidationResponse {
  success: boolean;
  validation_result: {
    coordinate_validation: {
      is_valid: boolean;
      palm_oil_region?: string;
      compliance_status: string;
    };
    certification_validation: {
      is_valid: boolean;
      valid_certifications: string[];
      invalid_certifications: string[];
    };
    harvest_date_validation: {
      is_valid: boolean;
      freshness_score: number;
    };
    overall_compliance_score: number;
    compliance_status: 'compliant' | 'non_compliant' | 'pending';
    recommendations: string[];
  };
}

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

export interface CertificationInfo {
  id: string;
  name: string;
  type: string;
  issuing_body: string;
  certificate_number: string;
  issue_date: string;
  expiry_date: string;
  status: 'active' | 'expired' | 'pending_renewal';
  farm_id?: string;
  company_id: string;
}

export interface OriginDataFilters {
  status?: string;
  eudr_status?: string;
  farm_name?: string;
  date_from?: string;
  date_to?: string;
  page?: number;
  per_page?: number;
}

export interface OriginDataListResponse {
  records: OriginDataRecord[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
}

export interface FarmListResponse {
  company_id: string;
  total_farms: number;
  farms: FarmInformation[];
}

export interface CertificationListResponse {
  certifications: CertificationInfo[];
  total: number;
  expiring_soon: number;
}

// API Service
export const originApi = {
  // Origin Data Management
  async getOriginDataRecords(filters?: OriginDataFilters): Promise<OriginDataListResponse> {
    const params = new URLSearchParams();
    if (filters) {
      Object.entries(filters).forEach(([key, value]) => {
        if (value !== undefined && value !== null && value !== '') {
          params.append(key, value.toString());
        }
      });
    }
    
    const response = await apiClient.get(`/origin-data/records?${params.toString()}`);
    return response.data;
  },

  async getOriginDataRecord(id: string): Promise<OriginDataRecord> {
    const response = await apiClient.get(`/origin-data/records/${id}`);
    return response.data;
  },

  async createOriginDataRecord(data: Partial<OriginDataRecord>): Promise<OriginDataRecord> {
    const response = await apiClient.post('/origin-data/records', data);
    return response.data;
  },

  async updateOriginDataRecord(id: string, data: Partial<OriginDataRecord>): Promise<OriginDataRecord> {
    const response = await apiClient.put(`/origin-data/records/${id}`, data);
    return response.data;
  },

  async deleteOriginDataRecord(id: string): Promise<void> {
    await apiClient.delete(`/origin-data/records/${id}`);
  },

  // Origin Data Validation
  async validateOriginData(validationRequest: OriginDataValidationRequest): Promise<OriginDataValidationResponse> {
    const response = await apiClient.post('/origin-data/validate', validationRequest);
    return response.data;
  },

  async getOriginDataRequirements(productId: string, region?: string): Promise<any> {
    const params = new URLSearchParams();
    if (region) {
      params.append('region', region);
    }
    
    const response = await apiClient.get(`/origin-data/requirements/${productId}?${params.toString()}`);
    return response.data;
  },

  async getPalmOilRegions(): Promise<any[]> {
    const response = await apiClient.get('/origin-data/palm-oil-regions');
    return response.data;
  },

  // Farm Management
  async getCompanyFarms(companyId: string): Promise<FarmListResponse> {
    const response = await apiClient.get(`/farm-management/company/${companyId}/farms`);
    return response.data;
  },

  async getCompanyCapabilities(companyId: string): Promise<any> {
    const response = await apiClient.get(`/farm-management/company/${companyId}/capabilities`);
    return response.data;
  },

  async createFarm(farmData: Partial<FarmInformation>): Promise<FarmInformation> {
    const response = await apiClient.post('/farm-management/farms', farmData);
    return response.data;
  },

  async updateFarm(farmId: string, farmData: Partial<FarmInformation>): Promise<FarmInformation> {
    const response = await apiClient.put(`/farm-management/farms/${farmId}`, farmData);
    return response.data;
  },

  async deleteFarm(farmId: string): Promise<void> {
    await apiClient.delete(`/farm-management/farms/${farmId}`);
  },

  // Certification Management
  async getCertifications(companyId?: string): Promise<CertificationListResponse> {
    const params = new URLSearchParams();
    if (companyId) {
      params.append('company_id', companyId);
    }
    
    const response = await apiClient.get(`/certifications?${params.toString()}`);
    return response.data;
  },

  async createCertification(certData: Partial<CertificationInfo>): Promise<CertificationInfo> {
    const response = await apiClient.post('/certifications', certData);
    return response.data;
  },

  async updateCertification(certId: string, certData: Partial<CertificationInfo>): Promise<CertificationInfo> {
    const response = await apiClient.put(`/certifications/${certId}`, certData);
    return response.data;
  },

  async deleteCertification(certId: string): Promise<void> {
    await apiClient.delete(`/certifications/${certId}`);
  },

  // Batch Management
  async createBatchWithFarmContributions(batchData: any): Promise<any> {
    const response = await apiClient.post('/farm-management/batches', batchData);
    return response.data;
  },

  async getBatchTraceability(batchId: string): Promise<any> {
    const response = await apiClient.get(`/farm-management/batches/${batchId}/traceability`);
    return response.data;
  },

  async getBatchComplianceStatus(batchId: string): Promise<any> {
    const response = await apiClient.get(`/farm-management/batches/${batchId}/compliance`);
    return response.data;
  },

  // Dashboard Metrics
  async getOriginatorDashboardMetrics(): Promise<any> {
    const response = await apiClient.get('/dashboard/metrics/originator');
    return response.data;
  }
};

export default originApi;
