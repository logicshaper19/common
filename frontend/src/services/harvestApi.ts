import { apiClient } from '../lib/api';
import axios from 'axios';

// Create a separate client for harvest endpoints (no v1 prefix)
const harvestApiClient = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth interceptor
harvestApiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
    console.log('🔑 Harvest API: Token attached to request', config.url);
  } else {
    console.log('❌ Harvest API: No token found in localStorage');
  }
  return config;
});

export interface HarvestBatch {
  id: string;
  batch_id: string;
  batch_type: string;
  company_id: string;
  product_id: string;
  quantity: number;
  unit: string;
  production_date: string;
  expiry_date?: string;
  status: string;
  location_name?: string;
  location_coordinates?: {
    latitude: number;
    longitude: number;
    accuracy_meters?: number;
  };
  facility_code?: string;
  quality_metrics?: Record<string, any>;
  processing_method?: string;
  storage_conditions?: string;
  transportation_method?: string;
  transformation_id?: string;
  parent_batch_ids?: string[];
  origin_data?: {
    harvest_date: string;
    farm_information: {
      farm_id: string;
      farm_name: string;
      plantation_type: string;
      cultivation_methods: string[];
    };
    geographic_coordinates: {
      latitude: number;
      longitude: number;
      accuracy_meters?: number;
    };
    certifications: string[];
    cultivation_methods: string[];
    processing_notes?: string;
    declared_by_user_id: string;
    declared_at: string;
  };
  certifications?: string[];
  source_purchase_order_id?: string;
  created_at: string;
  updated_at: string;
  created_by_user_id: string;
  company_name?: string;
  product_name?: string;
  batch_metadata?: Record<string, any>;
}

export interface HarvestDeclarationData {
  batch_number: string;
  product_id: string;
  quantity: number;
  unit: string;
  harvest_date: string;
  geographic_coordinates: {
    latitude: number;
    longitude: number;
    accuracy_meters?: number;
  };
  farm_information: {
    farm_id: string;
    farm_name: string;
    plantation_type: 'smallholder' | 'estate';
    cultivation_methods: string[];
  };
  quality_parameters: {
    oil_content?: number;
    moisture_content?: number;
    free_fatty_acid?: number;
    dirt_content?: number;
    kernel_to_fruit_ratio?: number;
  };
  certifications: string[];
  processing_notes?: string;
}

export interface HarvestBatchesResponse {
  batches: HarvestBatch[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
}

export const harvestApi = {
  // Declare a new harvest
  declareHarvest: async (harvestData: HarvestDeclarationData): Promise<HarvestBatch> => {
    const response = await harvestApiClient.post('/api/harvest/declare', harvestData);
    return response.data;
  },

  // Get harvest batches for the current company
  getHarvestBatches: async (
    page: number = 1,
    per_page: number = 20
  ): Promise<HarvestBatchesResponse> => {
    const response = await harvestApiClient.get('/api/harvest/batches', {
      params: { page, per_page }
    });
    return response.data;
  },

  // Get a specific harvest batch
  getHarvestBatch: async (batchId: string): Promise<HarvestBatch> => {
    const response = await harvestApiClient.get(`/api/harvest/batches/${batchId}`);
    return response.data;
  },

  // Get available harvest batches for a specific product (for PO confirmation)
  getAvailableHarvestBatches: async (
    productId: string,
    requiredQuantity?: number,
    requiredUnit?: string
  ): Promise<HarvestBatch[]> => {
    const response = await harvestApiClient.get('/api/harvest/batches', {
      params: {
        product_id: productId,
        status: 'active',
        per_page: 100 // Get more batches for selection
      }
    });
    
    // Return all available batches - let the user select which ones to use
    // The quantity filtering is handled in the UI where users can select partial quantities
    let batches = response.data.batches || [];
    
    // Only filter by unit if specified, but allow partial quantities
    // Handle common unit variations (kg vs KGM, etc.)
    if (requiredUnit) {
      batches = batches.filter((batch: HarvestBatch) => {
        const batchUnit = batch.unit?.toLowerCase();
        const requiredUnitLower = requiredUnit.toLowerCase();
        
        // Direct match
        if (batchUnit === requiredUnitLower) return true;
        
        // Common unit variations
        const unitMappings: { [key: string]: string[] } = {
          'kg': ['kgm', 'kilogram', 'kilograms'],
          'kgm': ['kg', 'kilogram', 'kilograms'],
          'ton': ['tonne', 'tons', 'tonnes'],
          'tonne': ['ton', 'tons', 'tonnes'],
          'lb': ['pound', 'pounds', 'lbs'],
          'pound': ['lb', 'pounds', 'lbs']
        };
        
        // Check if units are equivalent
        for (const [baseUnit, variations] of Object.entries(unitMappings)) {
          if (requiredUnitLower === baseUnit && variations.includes(batchUnit)) return true;
          if (batchUnit === baseUnit && variations.includes(requiredUnitLower)) return true;
        }
        
        return false;
      });
    }
    
    return batches;
  }
};
