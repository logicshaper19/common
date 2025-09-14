/**
 * React hook for origin dashboard data management
 * Provides comprehensive data fetching and state management for origin/originator features
 */
import { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { originApi, OriginDataRecord, OriginDataFilters } from '../services/originApi';
import { farmApi, FarmInformation, CompanyCapabilities } from '../services/farmApi';

export interface OriginDashboardData {
  // Origin Data
  originDataRecords: OriginDataRecord[];
  originDataLoading: boolean;
  originDataError: string | null;
  
  // Farm Data
  farms: FarmInformation[];
  farmsLoading: boolean;
  farmsError: string | null;
  
  // Company Capabilities
  capabilities: CompanyCapabilities | null;
  capabilitiesLoading: boolean;
  capabilitiesError: string | null;
  
  // Dashboard Metrics
  metrics: any;
  metricsLoading: boolean;
  metricsError: string | null;
}

export interface UseOriginDashboardOptions {
  companyId?: string;
  autoLoad?: boolean;
  refreshInterval?: number;
}

export const useOriginDashboard = (options: UseOriginDashboardOptions = {}) => {
  const { user } = useAuth();
  const { companyId, autoLoad = true, refreshInterval } = options;
  
  const targetCompanyId = companyId || user?.company?.id;
  
  // State
  const [data, setData] = useState<OriginDashboardData>({
    originDataRecords: [],
    originDataLoading: false,
    originDataError: null,
    farms: [],
    farmsLoading: false,
    farmsError: null,
    capabilities: null,
    capabilitiesLoading: false,
    capabilitiesError: null,
    metrics: null,
    metricsLoading: false,
    metricsError: null,
  });

  // Load origin data records
  const loadOriginData = useCallback(async (filters?: OriginDataFilters) => {
    if (!targetCompanyId) return;
    
    setData(prev => ({ ...prev, originDataLoading: true, originDataError: null }));
    
    try {
      const response = await originApi.getOriginDataRecords(filters);
      setData(prev => ({
        ...prev,
        originDataRecords: response.records,
        originDataLoading: false,
      }));
    } catch (error) {
      console.error('Error loading origin data:', error);
      setData(prev => ({
        ...prev,
        originDataError: error instanceof Error ? error.message : 'Failed to load origin data',
        originDataLoading: false,
      }));
    }
  }, [targetCompanyId]);

  // Load farm information
  const loadFarms = useCallback(async () => {
    if (!targetCompanyId) return;
    
    setData(prev => ({ ...prev, farmsLoading: true, farmsError: null }));
    
    try {
      const response = await farmApi.getCompanyFarms(targetCompanyId);
      setData(prev => ({
        ...prev,
        farms: response.farms,
        farmsLoading: false,
      }));
    } catch (error) {
      console.error('Error loading farms:', error);
      setData(prev => ({
        ...prev,
        farmsError: error instanceof Error ? error.message : 'Failed to load farms',
        farmsLoading: false,
      }));
    }
  }, [targetCompanyId]);

  // Load company capabilities
  const loadCapabilities = useCallback(async () => {
    if (!targetCompanyId) return;
    
    setData(prev => ({ ...prev, capabilitiesLoading: true, capabilitiesError: null }));
    
    try {
      const capabilities = await farmApi.getCompanyCapabilities(targetCompanyId);
      setData(prev => ({
        ...prev,
        capabilities,
        capabilitiesLoading: false,
      }));
    } catch (error) {
      console.error('Error loading capabilities:', error);
      setData(prev => ({
        ...prev,
        capabilitiesError: error instanceof Error ? error.message : 'Failed to load capabilities',
        capabilitiesLoading: false,
      }));
    }
  }, [targetCompanyId]);

  // Load dashboard metrics
  const loadMetrics = useCallback(async () => {
    if (!targetCompanyId) return;
    
    setData(prev => ({ ...prev, metricsLoading: true, metricsError: null }));
    
    try {
      const metrics = await originApi.getOriginatorDashboardMetrics();
      setData(prev => ({
        ...prev,
        metrics,
        metricsLoading: false,
      }));
    } catch (error) {
      console.error('Error loading metrics:', error);
      setData(prev => ({
        ...prev,
        metricsError: error instanceof Error ? error.message : 'Failed to load metrics',
        metricsLoading: false,
      }));
    }
  }, [targetCompanyId]);

  // Load all data
  const loadAllData = useCallback(async () => {
    if (!targetCompanyId) return;
    
    await Promise.all([
      loadOriginData(),
      loadFarms(),
      loadCapabilities(),
      loadMetrics(),
    ]);
  }, [targetCompanyId, loadOriginData, loadFarms, loadCapabilities, loadMetrics]);

  // Refresh all data
  const refreshData = useCallback(async () => {
    await loadAllData();
  }, [loadAllData]);

  // Create origin data record
  const createOriginDataRecord = useCallback(async (recordData: Partial<OriginDataRecord>) => {
    try {
      const newRecord = await originApi.createOriginDataRecord(recordData);
      setData(prev => ({
        ...prev,
        originDataRecords: [newRecord, ...prev.originDataRecords],
      }));
      return newRecord;
    } catch (error) {
      console.error('Error creating origin data record:', error);
      throw error;
    }
  }, []);

  // Update origin data record
  const updateOriginDataRecord = useCallback(async (id: string, recordData: Partial<OriginDataRecord>) => {
    try {
      const updatedRecord = await originApi.updateOriginDataRecord(id, recordData);
      setData(prev => ({
        ...prev,
        originDataRecords: prev.originDataRecords.map(record =>
          record.id === id ? updatedRecord : record
        ),
      }));
      return updatedRecord;
    } catch (error) {
      console.error('Error updating origin data record:', error);
      throw error;
    }
  }, []);

  // Delete origin data record
  const deleteOriginDataRecord = useCallback(async (id: string) => {
    try {
      await originApi.deleteOriginDataRecord(id);
      setData(prev => ({
        ...prev,
        originDataRecords: prev.originDataRecords.filter(record => record.id !== id),
      }));
    } catch (error) {
      console.error('Error deleting origin data record:', error);
      throw error;
    }
  }, []);

  // Create farm
  const createFarm = useCallback(async (farmData: any) => {
    try {
      const newFarm = await farmApi.createFarm(farmData);
      setData(prev => ({
        ...prev,
        farms: [...prev.farms, newFarm],
      }));
      return newFarm;
    } catch (error) {
      console.error('Error creating farm:', error);
      throw error;
    }
  }, []);

  // Update farm
  const updateFarm = useCallback(async (farmId: string, farmData: any) => {
    try {
      const updatedFarm = await farmApi.updateFarm(farmId, farmData);
      setData(prev => ({
        ...prev,
        farms: prev.farms.map(farm => farm.id === farmId ? updatedFarm : farm),
      }));
      return updatedFarm;
    } catch (error) {
      console.error('Error updating farm:', error);
      throw error;
    }
  }, []);

  // Delete farm
  const deleteFarm = useCallback(async (farmId: string) => {
    try {
      await farmApi.deleteFarm(farmId);
      setData(prev => ({
        ...prev,
        farms: prev.farms.filter(farm => farm.id !== farmId),
      }));
    } catch (error) {
      console.error('Error deleting farm:', error);
      throw error;
    }
  }, []);

  // Auto-load data on mount
  useEffect(() => {
    if (autoLoad && targetCompanyId) {
      loadAllData();
    }
  }, [autoLoad, targetCompanyId, loadAllData]);

  // Set up refresh interval
  useEffect(() => {
    if (refreshInterval && refreshInterval > 0) {
      const interval = setInterval(refreshData, refreshInterval);
      return () => clearInterval(interval);
    }
  }, [refreshInterval, refreshData]);

  return {
    // Data
    ...data,
    
    // Actions
    loadOriginData,
    loadFarms,
    loadCapabilities,
    loadMetrics,
    loadAllData,
    refreshData,
    
    // Origin Data Actions
    createOriginDataRecord,
    updateOriginDataRecord,
    deleteOriginDataRecord,
    
    // Farm Actions
    createFarm,
    updateFarm,
    deleteFarm,
    
    // Computed values
    hasData: data.originDataRecords.length > 0 || data.farms.length > 0,
    isLoading: data.originDataLoading || data.farmsLoading || data.capabilitiesLoading || data.metricsLoading,
    hasError: !!(data.originDataError || data.farmsError || data.capabilitiesError || data.metricsError),
  };
};

export default useOriginDashboard;
