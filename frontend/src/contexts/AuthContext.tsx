/**
 * Authentication Context for Common Supply Chain Platform
 * Manages user authentication state and provides auth-related functions
 */
import React, { createContext, useContext, useEffect, useState, useCallback, useMemo, ReactNode } from 'react';
import { apiClient, User, LoginRequest, ApiError } from '../lib/api';
import { parseErrorMessage } from '../lib/utils';

// Types
interface AuthState {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  error: string | null;
}

interface AuthContextType extends AuthState {
  login: (credentials: LoginRequest) => Promise<void>;
  logout: () => Promise<void>;
  clearError: () => void;
  refreshUser: () => Promise<void>;
}

// Create context
const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Custom hook to use auth context
export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

// Auth provider props
interface AuthProviderProps {
  children: ReactNode;
}

// Auth provider component
export function AuthProvider({ children }: AuthProviderProps) {
  const [state, setState] = useState<AuthState>({
    user: null,
    isLoading: true,
    isAuthenticated: false,
    error: null,
  });

  // Initialize authentication state
  const initializeAuth = useCallback(async () => {
    try {
      // Check if we have a token in localStorage
      const token = localStorage.getItem('auth_token');
      if (!token) {
        setState(prev => ({ ...prev, isLoading: false }));
        return;
      }

      // Try to get current user with existing token
      const user = await apiClient.getCurrentUser();
      setState(prev => ({
        ...prev,
        user,
        isAuthenticated: true,
        isLoading: false,
        error: null,
      }));
    } catch (error) {
      // Token is invalid or expired
      apiClient.clearToken();
      setState(prev => ({
        ...prev,
        user: null,
        isAuthenticated: false,
        isLoading: false,
        error: null,
      }));
    }
  }, []); // No dependencies - this function should only be created once

  // Initialize auth state on mount
  useEffect(() => {
    initializeAuth();
  }, [initializeAuth]);

  // Login function
  const login = useCallback(async (credentials: LoginRequest) => {
    setState(prev => ({ ...prev, isLoading: true, error: null }));

    try {
      const response = await apiClient.login(credentials);

      setState(prev => ({
        ...prev,
        user: response.user,
        isAuthenticated: true,
        isLoading: false,
        error: null,
      }));
    } catch (error) {
      const errorMessage = parseErrorMessage(error);
      setState(prev => ({
        ...prev,
        user: null,
        isAuthenticated: false,
        isLoading: false,
        error: errorMessage,
      }));
      throw error;
    }
  }, []);

  // Logout function
  const logout = useCallback(async () => {
    setState(prev => ({ ...prev, isLoading: true }));

    try {
      await apiClient.logout();
    } catch (error) {
      // Even if logout fails on server, clear local state
      console.error('Logout error:', error);
    } finally {
      setState({
        user: null,
        isAuthenticated: false,
        isLoading: false,
        error: null,
      });
    }
  }, []);

  // Clear error function
  const clearError = useCallback(() => {
    setState(prev => ({ ...prev, error: null }));
  }, []);

  // Refresh user data
  const refreshUser = useCallback(async () => {
    if (!state.isAuthenticated) return;

    try {
      const user = await apiClient.getCurrentUser();
      setState(prev => ({ ...prev, user }));
    } catch (error) {
      console.error('Failed to refresh user:', error);
      // If refresh fails, user might need to re-authenticate
      await logout();
    }
  }, [state.isAuthenticated, logout]);

  // Context value - memoized to prevent unnecessary re-renders
  const value: AuthContextType = useMemo(() => ({
    ...state,
    login,
    logout,
    clearError,
    refreshUser,
  }), [state, login, logout, clearError, refreshUser]);

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

// Higher-order component for protected routes
interface ProtectedRouteProps {
  children: ReactNode;
  requiredRole?: string;
  fallback?: ReactNode;
}

export function ProtectedRoute({
  children,
  requiredRole,
  fallback
}: ProtectedRouteProps): React.ReactElement {
  const { isAuthenticated, isLoading, user } = useAuth();

  // Show loading state
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  // Not authenticated
  if (!isAuthenticated) {
    return fallback ? <>{fallback}</> : <LoginRedirect />;
  }

  // Check role permission if required
  if (requiredRole && user) {
    const hasPermission = checkRolePermission(user.role, requiredRole);
    if (!hasPermission) {
      return (
        <div className="min-h-screen flex items-center justify-center">
          <div className="text-center">
            <h2 className="text-2xl font-semibold text-neutral-900 mb-2">
              Access Denied
            </h2>
            <p className="text-neutral-600">
              You don't have permission to access this page.
            </p>
          </div>
        </div>
      );
    }
  }

  return <>{children}</>;
}

// Login redirect component
function LoginRedirect(): React.ReactElement {
  useEffect(() => {
    // Redirect to login page
    window.location.href = '/login';
  }, []);

  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="text-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600 mx-auto mb-4"></div>
        <p className="text-neutral-600">Redirecting to login...</p>
      </div>
    </div>
  );
}

// Role permission checker
function checkRolePermission(userRole: string, requiredRole: string): boolean {
  const roleHierarchy: Record<string, number> = {
    viewer: 1,
    buyer: 2,
    seller: 2,
    admin: 3,
  };

  const userLevel = roleHierarchy[userRole] || 0;
  const requiredLevel = roleHierarchy[requiredRole] || 0;

  return userLevel >= requiredLevel;
}

// Hook for checking permissions
export function usePermissions() {
  const { user } = useAuth();

  const hasRole = (role: string): boolean => {
    return user?.role === role;
  };

  const hasPermission = (requiredRole: string): boolean => {
    if (!user) return false;
    return checkRolePermission(user.role, requiredRole);
  };

  const canViewCompany = (companyId: string): boolean => {
    if (!user) return false;
    if (user.role === 'admin') return true;
    return user.company_id === companyId;
  };

  const canEditPurchaseOrder = (po: any): boolean => {
    if (!user) return false;
    if (user.role === 'admin') return true;
    
    // Buyers can edit their own POs
    if (user.role === 'buyer' && po.buyer_company_id === user.company_id) {
      return true;
    }
    
    // Sellers can confirm POs
    if (user.role === 'seller' && po.seller_company_id === user.company_id) {
      return po.status === 'pending';
    }
    
    return false;
  };

  return {
    user,
    hasRole,
    hasPermission,
    canViewCompany,
    canEditPurchaseOrder,
  };
}

export default AuthContext;
