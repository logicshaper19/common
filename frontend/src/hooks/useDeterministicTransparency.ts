/**
 * React hook for deterministic transparency metrics
 * 
 * Provides fast, auditable transparency data based on explicit user-created links.
 * Replaces complex scoring algorithms with binary traced/not-traced states.
 */

import { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { apiClient } from '../lib/api';

export interface TransparencyMetrics {
  company_id: string;
  total_volume: number;
  traced_to_mill_volume: number;
  traced_to_plantation_volume: number;
  transparency_to_mill_percentage: number;
  transparency_to_plantation_percentage: number;
  total_purchase_orders: number;
  traced_purchase_orders: number;
  calculation_timestamp: string;
}

export interface TransparencyGap {
  po_id: string;
  po_number: string;
  seller_company_name: string;
  product_name: string;
  quantity: number;
  unit: string;
  gap_type: 'not_traced_to_mill' | 'not_traced_to_plantation';
  trace_depth: number;
  last_known_company_type: string;
}

export interface SupplyChainTrace {
  po_id: string;
  po_number: string;
  trace_path: string;
  trace_depth: number;
  origin_company_id: string;
  origin_company_type: string;
  is_traced_to_mill: boolean;
  is_traced_to_plantation: boolean;
  path_companies: string[];
}

interface TransparencyResponse<T> {
  success: boolean;
  data: T;
  message: string;
  calculation_method?: string;
}

interface TransparencyGapsResponse {
  success: boolean;
  data: TransparencyGap[];
  total_gaps: number;
  message: string;
}

export const useDeterministicTransparency = (companyId?: string) => {
  const { user } = useAuth();
  const [metrics, setMetrics] = useState<TransparencyMetrics | null>(null);
  const [gaps, setGaps] = useState<TransparencyGap[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const targetCompanyId = companyId || user?.company?.id;

  const fetchTransparencyMetrics = useCallback(async (refresh: boolean = false) => {
    if (!targetCompanyId) return;

    setLoading(true);
    setError(null);

    try {
      const response = await apiClient.get<TransparencyResponse<TransparencyMetrics>>(
        `/transparency/v2/companies/${targetCompanyId}/metrics?refresh=${refresh}`
      );

      const result = response.data;
      
      if (result.success) {
        setMetrics(result.data);
      } else {
        throw new Error(result.message || 'Failed to fetch transparency metrics');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error occurred';
      setError(errorMessage);
      console.error('Error fetching transparency metrics:', err);
    } finally {
      setLoading(false);
    }
  }, [targetCompanyId]);

  const fetchTransparencyGaps = useCallback(async (
    gapType?: 'mill' | 'plantation',
    limit: number = 50
  ) => {
    if (!targetCompanyId) return;

    setLoading(true);
    setError(null);

    try {
      const params = new URLSearchParams({
        limit: limit.toString(),
      });
      
      if (gapType) {
        params.append('gap_type', gapType);
      }

      const response = await apiClient.get<TransparencyGapsResponse>(
        `/transparency/v2/companies/${targetCompanyId}/gaps?${params}`
      );

      const result = response.data;
      
      if (result.success) {
        setGaps(result.data);
      } else {
        throw new Error(result.message || 'Failed to fetch transparency gaps');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error occurred';
      setError(errorMessage);
      console.error('Error fetching transparency gaps:', err);
    } finally {
      setLoading(false);
    }
  }, [targetCompanyId]);

  const getSupplyChainTrace = useCallback(async (poId: string): Promise<SupplyChainTrace | null> => {
    try {
      const response = await apiClient.get<TransparencyResponse<SupplyChainTrace>>(
        `/transparency/v2/purchase-orders/${poId}/trace`
      );

      const result = response.data;
      
      if (result.success && result.data) {
        return result.data;
      } else {
        console.warn('No supply chain trace found for PO:', poId);
        return null;
      }
    } catch (err) {
      console.error('Error fetching supply chain trace:', err);
      throw err;
    }
  }, []);

  const refreshTransparencyData = useCallback(async () => {
    try {
      const response = await apiClient.post(
        '/transparency/v2/refresh',
        { force_refresh: true }
      );

      const result = response.data;
      
      if (result.success) {
        // Automatically refetch metrics after refresh
        await fetchTransparencyMetrics(false);
        return true;
      } else {
        throw new Error(result.message || 'Failed to refresh transparency data');
      }
    } catch (err) {
      console.error('Error refreshing transparency data:', err);
      throw err;
    }
  }, [fetchTransparencyMetrics]);

  const getTransparencyAuditTrail = useCallback(async (poId: string) => {
    try {
      const response = await apiClient.get(
        `/transparency/v2/purchase-orders/${poId}/audit`
      );

      const result = response.data;
      
      if (result.success) {
        return result.data;
      } else {
        throw new Error(result.message || 'Failed to fetch audit trail');
      }
    } catch (err) {
      console.error('Error fetching transparency audit trail:', err);
      throw err;
    }
  }, []);

  // Auto-fetch metrics when component mounts or company changes
  useEffect(() => {
    if (targetCompanyId) {
      fetchTransparencyMetrics();
    }
  }, [targetCompanyId, fetchTransparencyMetrics]);

  return {
    // Data
    metrics,
    gaps,
    loading,
    error,
    
    // Actions
    fetchTransparencyMetrics,
    fetchTransparencyGaps,
    getSupplyChainTrace,
    refreshTransparencyData,
    getTransparencyAuditTrail,
    
    // Computed values
    hasData: !!metrics,
    isFullyTraced: metrics ? 
      metrics.transparency_to_mill_percentage === 100 && 
      metrics.transparency_to_plantation_percentage === 100 : false,
    averageTransparency: metrics ? 
      (metrics.transparency_to_mill_percentage + metrics.transparency_to_plantation_percentage) / 2 : 0,
  };
};

export default useDeterministicTransparency;
