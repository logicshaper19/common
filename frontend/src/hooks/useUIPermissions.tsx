/**
 * Hook for role-based UI permissions
 * Manages UI element visibility and feature access based on user roles
 */
import React, { useState, useEffect, useCallback, Fragment } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { notificationApi } from '../lib/notificationApi';
import { UIPermissions } from '../types/notifications';

interface UseUIPermissionsReturn {
  permissions: UIPermissions | null;
  isLoading: boolean;
  error: string | null;
  hasNavigation: (section: keyof UIPermissions['navigation']) => boolean;
  hasFeature: (feature: keyof UIPermissions['features']) => boolean;
  hasDataAccess: (access: keyof UIPermissions['data_access']) => boolean;
  canViewCompany: (companyId: string) => boolean;
  canEditPurchaseOrder: (po: any) => boolean;
  refreshPermissions: () => Promise<void>;
}

export function useUIPermissions(): UseUIPermissionsReturn {
  const { user, isAuthenticated } = useAuth();
  const [permissions, setPermissions] = useState<UIPermissions | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Load permissions
  const loadPermissions = useCallback(async () => {
    if (!isAuthenticated || !user) {
      setPermissions(null);
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const data = await notificationApi.getUIPermissions();
      setPermissions(data);
    } catch (error) {
      console.error('Failed to load UI permissions:', error);
      setError('Failed to load permissions');
      
      // Fallback to basic permissions based on user role
      const fallbackPermissions: UIPermissions = {
        user_role: user.role,
        company_id: user.company?.id || '',
        navigation: {
          dashboard: true,
          purchase_orders: user.role !== 'viewer',
          companies: user.role === 'admin',
          transparency: true,
          onboarding: user.role !== 'viewer',
          analytics: user.role !== 'viewer',
          users: user.role === 'admin',
          settings: true,
        },
        features: {
          create_purchase_order: user.role === 'buyer' || user.role === 'admin',
          edit_purchase_order: user.role === 'buyer' || user.role === 'admin',
          delete_purchase_order: user.role === 'admin',
          confirm_purchase_order: user.role === 'seller' || user.role === 'admin',
          view_all_companies: user.role === 'admin',
          invite_suppliers: user.role !== 'viewer',
          manage_users: user.role === 'admin',
          view_analytics: user.role !== 'viewer',
          export_data: user.role !== 'viewer',
          manage_company_settings: user.role === 'admin',
        },
        data_access: {
          view_pricing: user.role !== 'viewer',
          view_financial_data: user.role === 'buyer' || user.role === 'admin',
          view_supplier_details: user.role !== 'viewer',
          view_transparency_scores: true,
          access_api: user.role === 'admin',
        },
      };
      
      setPermissions(fallbackPermissions);
    } finally {
      setIsLoading(false);
    }
  }, [isAuthenticated, user]);

  // Load permissions when user changes
  useEffect(() => {
    loadPermissions();
  }, [loadPermissions]);

  // Permission check functions
  const hasNavigation = useCallback((section: keyof UIPermissions['navigation']): boolean => {
    return permissions?.navigation[section] || false;
  }, [permissions]);

  const hasFeature = useCallback((feature: keyof UIPermissions['features']): boolean => {
    return permissions?.features[feature] || false;
  }, [permissions]);

  const hasDataAccess = useCallback((access: keyof UIPermissions['data_access']): boolean => {
    return permissions?.data_access[access] || false;
  }, [permissions]);

  // Company-specific permissions
  const canViewCompany = useCallback((companyId: string): boolean => {
    if (!user || !permissions) return false;
    
    // Admin can view all companies
    if (user.role === 'admin') return true;
    
    // Users can view their own company
    if (user.company.id === companyId) return true;
    
    // Check if user has permission to view all companies
    return permissions.features.view_all_companies;
  }, [user, permissions]);

  // Purchase order specific permissions
  const canEditPurchaseOrder = useCallback((po: any): boolean => {
    if (!user || !permissions) return false;
    
    // Admin can edit all POs
    if (user.role === 'admin') return true;
    
    // Check general edit permission first
    if (!permissions.features.edit_purchase_order) return false;
    
    // Buyers can edit their own POs
    if (user.role === 'buyer' && po.buyer_company_id === user.company.id) {
      return true;
    }

    // Sellers can confirm POs (limited editing)
    if (user.role === 'seller' && po.seller_company_id === user.company.id) {
      return po.status === 'pending' && permissions.features.confirm_purchase_order;
    }
    
    return false;
  }, [user, permissions]);

  // Refresh permissions
  const refreshPermissions = useCallback(async () => {
    await loadPermissions();
  }, [loadPermissions]);

  return {
    permissions,
    isLoading,
    error,
    hasNavigation,
    hasFeature,
    hasDataAccess,
    canViewCompany,
    canEditPurchaseOrder,
    refreshPermissions,
  };
}

// Higher-order component for conditional rendering based on permissions
export function withPermission<T extends object>(
  Component: React.ComponentType<T>,
  requiredPermission: {
    type: 'navigation' | 'feature' | 'data_access';
    permission: string;
  }
) {
  return function PermissionWrappedComponent(props: T) {
    const { hasNavigation, hasFeature, hasDataAccess } = useUIPermissions();
    
    let hasPermission = false;
    
    switch (requiredPermission.type) {
      case 'navigation':
        hasPermission = hasNavigation(requiredPermission.permission as any);
        break;
      case 'feature':
        hasPermission = hasFeature(requiredPermission.permission as any);
        break;
      case 'data_access':
        hasPermission = hasDataAccess(requiredPermission.permission as any);
        break;
    }
    
    if (!hasPermission) {
      return null;
    }
    
    return <Component {...props} />;
  };
}

// Component for conditional rendering
interface PermissionGateProps {
  children: React.ReactNode;
  navigation?: keyof UIPermissions['navigation'];
  feature?: keyof UIPermissions['features'];
  dataAccess?: keyof UIPermissions['data_access'];
  fallback?: React.ReactNode;
  requireAll?: boolean; // If true, all specified permissions must be granted
}

export function PermissionGate({
  children,
  navigation,
  feature,
  dataAccess,
  fallback = null,
  requireAll = false,
}: PermissionGateProps) {
  const { hasNavigation, hasFeature, hasDataAccess } = useUIPermissions();
  
  const permissions = [];
  
  if (navigation !== undefined) {
    permissions.push(hasNavigation(navigation));
  }
  
  if (feature !== undefined) {
    permissions.push(hasFeature(feature));
  }
  
  if (dataAccess !== undefined) {
    permissions.push(hasDataAccess(dataAccess));
  }
  
  // If no permissions specified, allow access
  if (permissions.length === 0) {
    return <Fragment>{children}</Fragment>;
  }

  // Check permissions based on requireAll flag
  const hasAccess = requireAll
    ? permissions.every(p => p)
    : permissions.some(p => p);

  return hasAccess ? <Fragment>{children}</Fragment> : <Fragment>{fallback ? (React.isValidElement(fallback) ? fallback : fallback) : null}</Fragment>;
}

// Hook for role-based styling
export function useRoleBasedStyling() {
  const { permissions } = useUIPermissions();
  
  const getRoleColor = useCallback(() => {
    switch (permissions?.user_role) {
      case 'admin': return 'text-error-600';
      case 'buyer': return 'text-primary-600';
      case 'seller': return 'text-success-600';
      case 'viewer': return 'text-neutral-600';
      default: return 'text-neutral-600';
    }
  }, [permissions]);
  
  const getRoleBadgeVariant = useCallback(() => {
    switch (permissions?.user_role) {
      case 'admin': return 'error';
      case 'buyer': return 'primary';
      case 'seller': return 'success';
      case 'viewer': return 'neutral';
      default: return 'neutral';
    }
  }, [permissions]);
  
  const getRoleIcon = useCallback(() => {
    switch (permissions?.user_role) {
      case 'admin': return '👑';
      case 'buyer': return '🛒';
      case 'seller': return '🏭';
      case 'viewer': return '👁️';
      default: return '👤';
    }
  }, [permissions]);
  
  return {
    getRoleColor,
    getRoleBadgeVariant,
    getRoleIcon,
  };
}

export default useUIPermissions;
