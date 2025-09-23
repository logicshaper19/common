/**
 * Universal Access Control Hook
 * Provides role-agnostic, component-agnostic access control for the frontend.
 * 
 * This hook ensures that access control logic is consistent across all components
 * and works for all user roles and company types.
 */
import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../contexts/AuthContext';

export interface AccessDecision {
  allowed: boolean;
  access_level: 'none' | 'read' | 'write' | 'admin' | 'audit';
  relationship_type: string;
  reason: string;
  restrictions?: string[];
}

export interface UniversalAccessOptions {
  resource_type: 'purchase_order' | 'amendment' | 'traceability' | 'farm_data' | 'company_data';
  resource_id: string;
  required_level?: 'read' | 'write' | 'admin' | 'audit';
  company_id?: string; // For company-specific resources
}

export const useUniversalAccess = () => {
  const { user } = useAuth();
  const [accessCache, setAccessCache] = useState<Map<string, AccessDecision>>(new Map());

  /**
   * Check access for any resource using universal access control
   */
  const checkAccess = useCallback(async (options: UniversalAccessOptions): Promise<AccessDecision> => {
    if (!user) {
      return {
        allowed: false,
        access_level: 'none',
        relationship_type: 'none',
        reason: 'User not authenticated'
      };
    }

    // Create cache key
    const cacheKey = `${options.resource_type}:${options.resource_id}:${user.id}`;
    
    // Check cache first
    if (accessCache.has(cacheKey)) {
      return accessCache.get(cacheKey)!;
    }

    try {
      // Call the universal access control API
      const response = await fetch('/api/v1/access-control/check', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('auth_token')}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          resource_type: options.resource_type,
          resource_id: options.resource_id,
          required_level: options.required_level || 'read',
          company_id: options.company_id
        })
      });

      if (!response.ok) {
        throw new Error(`Access check failed: ${response.statusText}`);
      }

      const decision: AccessDecision = await response.json();
      
      // Cache the result
      setAccessCache(prev => new Map(prev).set(cacheKey, decision));
      
      return decision;
    } catch (error) {
      console.error('Error checking access:', error);
      return {
        allowed: false,
        access_level: 'none',
        relationship_type: 'error',
        reason: 'Failed to check access permissions'
      };
    }
  }, [user, accessCache]);

  /**
   * Check if user can access a purchase order
   */
  const canAccessPurchaseOrder = useCallback(async (
    poId: string, 
    requiredLevel: 'read' | 'write' | 'admin' = 'read'
  ): Promise<AccessDecision> => {
    return checkAccess({
      resource_type: 'purchase_order',
      resource_id: poId,
      required_level: requiredLevel
    });
  }, [checkAccess]);

  /**
   * Check if user can access an amendment
   */
  const canAccessAmendment = useCallback(async (
    amendmentId: string, 
    requiredLevel: 'read' | 'write' | 'admin' = 'read'
  ): Promise<AccessDecision> => {
    return checkAccess({
      resource_type: 'amendment',
      resource_id: amendmentId,
      required_level: requiredLevel
    });
  }, [checkAccess]);

  /**
   * Check if user can access traceability data
   */
  const canAccessTraceability = useCallback(async (
    poId: string, 
    requiredLevel: 'read' | 'write' | 'admin' = 'read'
  ): Promise<AccessDecision> => {
    return checkAccess({
      resource_type: 'traceability',
      resource_id: poId,
      required_level: requiredLevel
    });
  }, [checkAccess]);

  /**
   * Check if user can access farm data
   */
  const canAccessFarmData = useCallback(async (
    companyId: string, 
    requiredLevel: 'read' | 'write' | 'admin' = 'read'
  ): Promise<AccessDecision> => {
    return checkAccess({
      resource_type: 'farm_data',
      resource_id: companyId,
      required_level: requiredLevel,
      company_id: companyId
    });
  }, [checkAccess]);

  /**
   * Check if user can access company data
   */
  const canAccessCompanyData = useCallback(async (
    companyId: string, 
    requiredLevel: 'read' | 'write' | 'admin' = 'read'
  ): Promise<AccessDecision> => {
    return checkAccess({
      resource_type: 'company_data',
      resource_id: companyId,
      required_level: requiredLevel,
      company_id: companyId
    });
  }, [checkAccess]);

  /**
   * Clear access cache (useful when user permissions change)
   */
  const clearAccessCache = useCallback(() => {
    setAccessCache(new Map());
  }, []);

  /**
   * Get access summary for debugging
   */
  const getAccessSummary = useCallback(async (options: UniversalAccessOptions) => {
    const decision = await checkAccess(options);
    return {
      ...decision,
      user_id: user?.id,
      company_id: user?.company?.id,
      user_role: user?.role,
      company_type: user?.company?.company_type,
      timestamp: new Date().toISOString()
    };
  }, [checkAccess, user]);

  return {
    // Core access checking
    checkAccess,
    
    // Convenience methods for specific resource types
    canAccessPurchaseOrder,
    canAccessAmendment,
    canAccessTraceability,
    canAccessFarmData,
    canAccessCompanyData,
    
    // Utility methods
    clearAccessCache,
    getAccessSummary,
    
    // State
    accessCache
  };
};

/**
 * Higher-order component for access-controlled components
 */
export const withAccessControl = <P extends object>(
  Component: React.ComponentType<P>,
  accessOptions: UniversalAccessOptions
) => {
  return (props: P) => {
    const { checkAccess } = useUniversalAccess();
    const [accessDecision, setAccessDecision] = useState<AccessDecision | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
      const checkAccessPermissions = async () => {
        try {
          const decision = await checkAccess(accessOptions);
          setAccessDecision(decision);
        } catch (error) {
          console.error('Error checking access:', error);
          setAccessDecision({
            allowed: false,
            access_level: 'none',
            relationship_type: 'error',
            reason: 'Failed to check access permissions'
          });
        } finally {
          setLoading(false);
        }
      };

      checkAccessPermissions();
    }, [checkAccess]);

    if (loading) {
      return React.createElement('div', null, 'Checking permissions...');
    }

    if (!accessDecision?.allowed) {
      return React.createElement('div', {
        className: 'p-4 bg-red-50 border border-red-200 rounded-lg'
      }, [
        React.createElement('h3', {
          key: 'title',
          className: 'text-red-800 font-medium'
        }, 'Access Denied'),
        React.createElement('p', {
          key: 'reason',
          className: 'text-red-600 text-sm mt-1'
        }, accessDecision?.reason)
      ]);
    }

    return React.createElement(Component, { ...props, accessDecision });
  };
};

/**
 * Hook for conditional rendering based on access
 */
export const useAccessControl = (options: UniversalAccessOptions) => {
  const { checkAccess } = useUniversalAccess();
  const [accessDecision, setAccessDecision] = useState<AccessDecision | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const checkAccessPermissions = async () => {
      try {
        const decision = await checkAccess(options);
        setAccessDecision(decision);
      } catch (error) {
        console.error('Error checking access:', error);
        setAccessDecision({
          allowed: false,
          access_level: 'none',
          relationship_type: 'error',
          reason: 'Failed to check access permissions'
        });
      } finally {
        setLoading(false);
      }
    };

    checkAccessPermissions();
  }, [checkAccess, options.resource_type, options.resource_id]);

  return {
    accessDecision,
    loading,
    allowed: accessDecision?.allowed || false,
    accessLevel: accessDecision?.access_level || 'none',
    restrictions: accessDecision?.restrictions || [],
    reason: accessDecision?.reason || 'Unknown'
  };
};
