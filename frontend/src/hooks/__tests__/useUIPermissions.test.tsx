/**
 * Tests for useUIPermissions hook
 */
import React from 'react';
import { renderHook, render, screen } from '@testing-library/react';
import { AuthProvider } from '../../contexts/AuthContext';
import useUIPermissions, { PermissionGate, withPermission } from '../useUIPermissions';
import { notificationApi } from '../../lib/notificationApi';

// Mock the notification API
jest.mock('../../lib/notificationApi');
const mockNotificationApi = notificationApi as jest.Mocked<typeof notificationApi>;

// Mock the auth context
const mockUser = {
  id: 'user-1',
  email: 'test@example.com',
  full_name: 'Test User',
  role: 'buyer' as const,
  is_active: true,
  company_id: 'company-1',
};

const MockAuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <AuthProvider>
    {children}
  </AuthProvider>
);

const mockPermissions = {
  user_role: 'buyer',
  company_id: 'company-1',
  navigation: {
    dashboard: true,
    purchase_orders: true,
    companies: false,
    transparency: true,
    onboarding: true,
    analytics: true,
    users: false,
    settings: true,
  },
  features: {
    create_purchase_order: true,
    edit_purchase_order: true,
    delete_purchase_order: false,
    confirm_purchase_order: false,
    view_all_companies: false,
    invite_suppliers: true,
    manage_users: false,
    view_analytics: true,
    export_data: true,
    manage_company_settings: false,
  },
  data_access: {
    view_pricing: true,
    view_financial_data: true,
    view_supplier_details: true,
    view_transparency_scores: true,
    access_api: false,
  },
};

describe('useUIPermissions', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockNotificationApi.getUIPermissions.mockResolvedValue(mockPermissions);
  });

  const renderHookWithAuth = () => {
    return renderHook(() => useUIPermissions(), {
      wrapper: MockAuthProvider,
    });
  };

  it('loads permissions on mount', async () => {
    const { result, waitForNextUpdate } = renderHookWithAuth();

    expect(result.current.isLoading).toBe(true);
    
    await waitForNextUpdate();
    
    expect(mockNotificationApi.getUIPermissions).toHaveBeenCalled();
    expect(result.current.permissions).toEqual(mockPermissions);
    expect(result.current.isLoading).toBe(false);
  });

  it('provides navigation permission checks', async () => {
    const { result, waitForNextUpdate } = renderHookWithAuth();
    
    await waitForNextUpdate();
    
    expect(result.current.hasNavigation('dashboard')).toBe(true);
    expect(result.current.hasNavigation('companies')).toBe(false);
    expect(result.current.hasNavigation('users')).toBe(false);
  });

  it('provides feature permission checks', async () => {
    const { result, waitForNextUpdate } = renderHookWithAuth();
    
    await waitForNextUpdate();
    
    expect(result.current.hasFeature('create_purchase_order')).toBe(true);
    expect(result.current.hasFeature('delete_purchase_order')).toBe(false);
    expect(result.current.hasFeature('manage_users')).toBe(false);
  });

  it('provides data access permission checks', async () => {
    const { result, waitForNextUpdate } = renderHookWithAuth();
    
    await waitForNextUpdate();
    
    expect(result.current.hasDataAccess('view_pricing')).toBe(true);
    expect(result.current.hasDataAccess('view_financial_data')).toBe(true);
    expect(result.current.hasDataAccess('access_api')).toBe(false);
  });

  it('provides company view permission check', async () => {
    const { result, waitForNextUpdate } = renderHookWithAuth();
    
    await waitForNextUpdate();
    
    // User can view their own company
    expect(result.current.canViewCompany('company-1')).toBe(true);
    
    // User cannot view other companies (not admin)
    expect(result.current.canViewCompany('company-2')).toBe(false);
  });

  it('provides purchase order edit permission check', async () => {
    const { result, waitForNextUpdate } = renderHookWithAuth();
    
    await waitForNextUpdate();
    
    const buyerPO = {
      buyer_company_id: 'company-1',
      seller_company_id: 'company-2',
      status: 'pending',
    };
    
    const otherPO = {
      buyer_company_id: 'company-2',
      seller_company_id: 'company-3',
      status: 'pending',
    };
    
    // Buyer can edit their own POs
    expect(result.current.canEditPurchaseOrder(buyerPO)).toBe(true);
    
    // Buyer cannot edit other company's POs
    expect(result.current.canEditPurchaseOrder(otherPO)).toBe(false);
  });

  it('handles API error with fallback permissions', async () => {
    mockNotificationApi.getUIPermissions.mockRejectedValue(new Error('API Error'));
    
    const { result, waitForNextUpdate } = renderHookWithAuth();
    
    await waitForNextUpdate();
    
    // Should have fallback permissions based on user role
    expect(result.current.permissions).toBeDefined();
    expect(result.current.permissions?.user_role).toBe('buyer');
    expect(result.current.error).toBe('Failed to load permissions');
  });

  it('refreshes permissions', async () => {
    const { result, waitForNextUpdate } = renderHookWithAuth();
    
    await waitForNextUpdate();
    
    await result.current.refreshPermissions();
    
    expect(mockNotificationApi.getUIPermissions).toHaveBeenCalledTimes(2);
  });
});

describe('PermissionGate', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockNotificationApi.getUIPermissions.mockResolvedValue(mockPermissions);
  });

  const renderWithAuth = (component: React.ReactElement) => {
    return render(
      <MockAuthProvider>
        {component}
      </MockAuthProvider>
    );
  };

  it('renders children when navigation permission is granted', async () => {
    renderWithAuth(
      <PermissionGate navigation="dashboard">
        <div>Dashboard Content</div>
      </PermissionGate>
    );

    await screen.findByText('Dashboard Content');
    expect(screen.getByText('Dashboard Content')).toBeInTheDocument();
  });

  it('does not render children when navigation permission is denied', async () => {
    renderWithAuth(
      <PermissionGate navigation="users">
        <div>Users Content</div>
      </PermissionGate>
    );

    // Wait a bit to ensure it doesn't appear
    await new Promise(resolve => setTimeout(resolve, 100));
    expect(screen.queryByText('Users Content')).not.toBeInTheDocument();
  });

  it('renders children when feature permission is granted', async () => {
    renderWithAuth(
      <PermissionGate feature="create_purchase_order">
        <div>Create PO Button</div>
      </PermissionGate>
    );

    await screen.findByText('Create PO Button');
    expect(screen.getByText('Create PO Button')).toBeInTheDocument();
  });

  it('does not render children when feature permission is denied', async () => {
    renderWithAuth(
      <PermissionGate feature="manage_users">
        <div>Manage Users Button</div>
      </PermissionGate>
    );

    await new Promise(resolve => setTimeout(resolve, 100));
    expect(screen.queryByText('Manage Users Button')).not.toBeInTheDocument();
  });

  it('renders children when data access permission is granted', async () => {
    renderWithAuth(
      <PermissionGate dataAccess="view_pricing">
        <div>Pricing Data</div>
      </PermissionGate>
    );

    await screen.findByText('Pricing Data');
    expect(screen.getByText('Pricing Data')).toBeInTheDocument();
  });

  it('renders fallback when permission is denied', async () => {
    renderWithAuth(
      <PermissionGate 
        navigation="users" 
        fallback={<div>Access Denied</div>}
      >
        <div>Users Content</div>
      </PermissionGate>
    );

    await screen.findByText('Access Denied');
    expect(screen.getByText('Access Denied')).toBeInTheDocument();
    expect(screen.queryByText('Users Content')).not.toBeInTheDocument();
  });

  it('handles multiple permissions with requireAll=false (OR logic)', async () => {
    renderWithAuth(
      <PermissionGate 
        navigation="dashboard" 
        feature="manage_users" 
        requireAll={false}
      >
        <div>Content</div>
      </PermissionGate>
    );

    // Should render because dashboard permission is granted (OR logic)
    await screen.findByText('Content');
    expect(screen.getByText('Content')).toBeInTheDocument();
  });

  it('handles multiple permissions with requireAll=true (AND logic)', async () => {
    renderWithAuth(
      <PermissionGate 
        navigation="dashboard" 
        feature="manage_users" 
        requireAll={true}
      >
        <div>Content</div>
      </PermissionGate>
    );

    // Should not render because manage_users is denied (AND logic)
    await new Promise(resolve => setTimeout(resolve, 100));
    expect(screen.queryByText('Content')).not.toBeInTheDocument();
  });

  it('renders children when no permissions specified', () => {
    renderWithAuth(
      <PermissionGate>
        <div>Always Visible</div>
      </PermissionGate>
    );

    expect(screen.getByText('Always Visible')).toBeInTheDocument();
  });
});

describe('withPermission HOC', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockNotificationApi.getUIPermissions.mockResolvedValue(mockPermissions);
  });

  const TestComponent: React.FC<{ message: string }> = ({ message }) => (
    <div>{message}</div>
  );

  const renderWithAuth = (component: React.ReactElement) => {
    return render(
      <MockAuthProvider>
        {component}
      </MockAuthProvider>
    );
  };

  it('renders component when permission is granted', async () => {
    const ProtectedComponent = withPermission(TestComponent, {
      type: 'navigation',
      permission: 'dashboard',
    });

    renderWithAuth(<ProtectedComponent message="Dashboard Component" />);

    await screen.findByText('Dashboard Component');
    expect(screen.getByText('Dashboard Component')).toBeInTheDocument();
  });

  it('does not render component when permission is denied', async () => {
    const ProtectedComponent = withPermission(TestComponent, {
      type: 'navigation',
      permission: 'users',
    });

    renderWithAuth(<ProtectedComponent message="Users Component" />);

    await new Promise(resolve => setTimeout(resolve, 100));
    expect(screen.queryByText('Users Component')).not.toBeInTheDocument();
  });

  it('works with feature permissions', async () => {
    const ProtectedComponent = withPermission(TestComponent, {
      type: 'feature',
      permission: 'create_purchase_order',
    });

    renderWithAuth(<ProtectedComponent message="Create PO Component" />);

    await screen.findByText('Create PO Component');
    expect(screen.getByText('Create PO Component')).toBeInTheDocument();
  });

  it('works with data access permissions', async () => {
    const ProtectedComponent = withPermission(TestComponent, {
      type: 'data_access',
      permission: 'view_pricing',
    });

    renderWithAuth(<ProtectedComponent message="Pricing Component" />);

    await screen.findByText('Pricing Component');
    expect(screen.getByText('Pricing Component')).toBeInTheDocument();
  });
});
