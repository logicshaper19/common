/**
 * React hook for dashboard configuration and feature flags
 * Provides dashboard type, permissions, and feature flag status
 */
import { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { featureFlags } from '../utils/featureFlags';

export interface DashboardConfig {
  can_create_po: boolean;
  can_confirm_po: boolean;
  can_manage_team: boolean;
  can_view_analytics: boolean;
  can_manage_settings: boolean;
  can_audit_companies: boolean;
  can_regulate_platform: boolean;
  can_manage_trader_chain?: boolean;
  can_view_margin_analysis?: boolean;
  can_report_farm_data?: boolean;
  can_manage_certifications?: boolean;
  dashboard_type: string;
  should_use_v2: boolean;
  feature_flags: Record<string, boolean>;
  user_info: {
    id: string;
    role: string;
    company_type: string;
    company_name: string;
  };
}

export const useDashboardConfig = () => {
  const { user } = useAuth();
  const [config, setConfig] = useState<DashboardConfig | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!user) {
      setLoading(false);
      return;
    }

    loadDashboardConfig();
  }, [user]);

  const loadDashboardConfig = async () => {
    try {
      setLoading(true);
      setError(null);

      // Get auth token from localStorage
      const token = localStorage.getItem('auth_token');
      if (!token) {
        console.warn('No authentication token found, falling back to V1 dashboard');
        throw new Error('No authentication token found');
      }

      // Load feature flags from API first
      await featureFlags.loadFromAPI();

      // Get dashboard configuration
      const response = await fetch(`${process.env.REACT_APP_API_URL}/api/v2/dashboard/config`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        if (response.status === 401 || response.status === 403) {
          console.warn('Authentication failed for Dashboard V2, falling back to V1');
          throw new Error('Authentication failed - please log in again');
        }
        throw new Error(`Failed to load dashboard config: ${response.status} ${response.statusText}`);
      }

      const backendResponse = await response.json();
      
      // Map backend response to frontend DashboardConfig structure
      const dashboardConfig: DashboardConfig = {
        // Map permissions based on user role and company type
        can_create_po: backendResponse.user_info.role === 'buyer' || 
                      (backendResponse.user_info.company_type === 'brand' && backendResponse.user_info.role === 'buyer') ||
                      (backendResponse.user_info.company_type === 'trader' && backendResponse.user_info.role === 'trader'),
        can_confirm_po: backendResponse.user_info.role === 'seller' || 
                       backendResponse.user_info.role === 'originator' ||
                       backendResponse.user_info.company_type === 'plantation_grower' ||
                       backendResponse.user_info.company_type === 'processor',
        can_manage_team: backendResponse.user_info.role === 'admin' || 
                        backendResponse.user_info.role === 'originator' ||
                        backendResponse.user_info.role === 'plantation_manager',
        can_view_analytics: true, // Most users can view analytics
        can_manage_settings: backendResponse.user_info.role === 'admin' || 
                            backendResponse.user_info.role === 'originator' ||
                            backendResponse.user_info.role === 'plantation_manager',
        can_audit_companies: backendResponse.user_info.role === 'auditor',
        can_regulate_platform: backendResponse.user_info.role === 'admin',
        can_manage_trader_chain: backendResponse.user_info.company_type === 'trader',
        can_view_margin_analysis: backendResponse.user_info.company_type === 'trader',
        can_report_farm_data: backendResponse.user_info.company_type === 'originator' || 
                             backendResponse.user_info.company_type === 'plantation_grower' ||
                             backendResponse.user_info.company_type === 'smallholder_cooperative',
        can_manage_certifications: backendResponse.user_info.company_type === 'originator' || 
                                  backendResponse.user_info.company_type === 'plantation_grower' ||
                                  backendResponse.user_info.company_type === 'smallholder_cooperative',
        dashboard_type: backendResponse.dashboard_type,
        should_use_v2: backendResponse.should_use_v2,
        feature_flags: backendResponse.feature_flags,
        user_info: backendResponse.user_info
      };
      
      setConfig(dashboardConfig);
    } catch (err) {
      console.error('Error loading dashboard config:', err);
      setError(err instanceof Error ? err.message : 'Failed to load dashboard config');
      
      // Fallback to frontend permissions if API fails
      if (user) {
        // Import the frontend permissions function
        const { getDashboardConfig } = await import('../utils/permissions');
        const frontendConfig = getDashboardConfig(user);
        
        setConfig({
          ...frontendConfig,
          dashboard_type: user.company?.company_type || 'default',
          should_use_v2: false, // Disable V2 if API fails
          feature_flags: {},
          user_info: {
            id: user.id,
            role: user.role,
            company_type: user.company?.company_type || 'unknown',
            company_name: user.company?.name || 'Unknown Company'
          }
        });
      }
    } finally {
      setLoading(false);
    }
  };

  const shouldUseV2Dashboard = (dashboardType?: string): boolean => {
    if (!config) return false;
    
    const type = dashboardType || config.dashboard_type;
    return config.should_use_v2 && config.feature_flags[`v2_dashboard_${type}`];
  };

  const isFeatureEnabled = (featureName: string): boolean => {
    return config?.feature_flags[featureName] || false;
  };

  const getDashboardType = (): string => {
    return config?.dashboard_type || 'default';
  };

  const canPerformAction = (action: keyof DashboardConfig): boolean => {
    if (!config) return false;
    return Boolean(config[action]);
  };

  return {
    config,
    loading,
    error,
    shouldUseV2Dashboard,
    isFeatureEnabled,
    getDashboardType,
    canPerformAction,
    reload: loadDashboardConfig,
  };
};

/**
 * Hook for getting dashboard metrics based on dashboard type
 */
export const useDashboardMetrics = (dashboardType?: string) => {
  const { config } = useDashboardConfig();
  const [metrics, setMetrics] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const type = dashboardType || config?.dashboard_type;

  useEffect(() => {
    if (!type || !config) return;

    loadMetrics();
  }, [type, config]);

  const loadMetrics = async () => {
    if (!type || type === 'default') {
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      setError(null);

      // Use the correct metrics endpoint without appending the type
      const response = await fetch(`${process.env.REACT_APP_API_URL}/api/v2/dashboard/metrics`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('auth_token')}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to load dashboard metrics: ${response.statusText}`);
      }

      const metricsData = await response.json();
      setMetrics(metricsData);
    } catch (err) {
      console.error(`Error loading dashboard metrics:`, err);
      setError(err instanceof Error ? err.message : `Failed to load dashboard metrics`);
    } finally {
      setLoading(false);
    }
  };

  return {
    metrics,
    loading,
    error,
    reload: loadMetrics,
  };
};

/**
 * Hook for feature flag checking
 */
export const useFeatureFlags = () => {
  const { config } = useDashboardConfig();

  const isEnabled = (flagName: string): boolean => {
    return config?.feature_flags[flagName] || false;
  };

  const getAllFlags = (): Record<string, boolean> => {
    return config?.feature_flags || {};
  };

  return {
    isEnabled,
    getAllFlags,
    flags: config?.feature_flags || {},
  };
};
