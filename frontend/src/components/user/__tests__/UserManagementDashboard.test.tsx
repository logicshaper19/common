/**
 * Tests for UserManagementDashboard component
 */
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { AuthProvider } from '../../../contexts/AuthContext';
import { NotificationProvider } from '../../../contexts/NotificationContext';
import UserManagementDashboard from '../UserManagementDashboard';
import { notificationApi } from '../../../lib/notificationApi';

// Mock the notification API
jest.mock('../../../lib/notificationApi');
const mockNotificationApi = notificationApi as jest.Mocked<typeof notificationApi>;

// Mock child components
jest.mock('../../notifications/NotificationCenter', () => {
  return function MockNotificationCenter({ isOpen, onClose }: any) {
    return isOpen ? (
      <div data-testid="notification-center">
        <button onClick={onClose}>Close</button>
      </div>
    ) : null;
  };
});

jest.mock('../../notifications/NotificationPreferences', () => {
  return function MockNotificationPreferences() {
    return <div data-testid="notification-preferences">Notification Preferences</div>;
  };
});

jest.mock('../../notifications/NotificationHistory', () => {
  return function MockNotificationHistory() {
    return <div data-testid="notification-history">Notification History</div>;
  };
});

jest.mock('../UserProfile', () => {
  return function MockUserProfile() {
    return <div data-testid="user-profile">User Profile</div>;
  };
});

jest.mock('../CompanySettings', () => {
  return function MockCompanySettings() {
    return <div data-testid="company-settings">Company Settings</div>;
  };
});

const MockProviders: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <AuthProvider>
    <NotificationProvider>
      {children}
    </NotificationProvider>
  </AuthProvider>
);

const mockSummary = {
  total_count: 5,
  unread_count: 2,
  high_priority_count: 1,
  urgent_count: 0,
  counts_by_type: {
    po_created: 1,
    po_confirmed: 2,
    po_shipped: 1,
    po_delivered: 1,
    po_cancelled: 0,
    transparency_updated: 0,
    supplier_invited: 0,
    supplier_joined: 0,
    system_alert: 0,
    user_mention: 0,
    deadline_reminder: 0,
    quality_issue: 0,
    compliance_alert: 0,
  },
  recent_notifications: [],
  last_updated: '2024-01-15T10:30:00Z',
};

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

describe('UserManagementDashboard', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    
    mockNotificationApi.getNotificationSummary.mockResolvedValue(mockSummary);
    mockNotificationApi.getUIPermissions.mockResolvedValue(mockPermissions);
    mockNotificationApi.getNotifications.mockResolvedValue({
      notifications: [],
      total_count: 0,
      page: 1,
      page_size: 20,
      has_next: false,
      has_previous: false,
      summary: mockSummary,
    });
  });

  const renderWithProviders = (component: React.ReactElement) => {
    return render(
      <MockProviders>
        {component}
      </MockProviders>
    );
  };

  it('renders user management dashboard', async () => {
    renderWithProviders(<UserManagementDashboard />);

    expect(screen.getByText('User Management')).toBeInTheDocument();
    expect(screen.getByText('Manage your notifications, profile, and account settings')).toBeInTheDocument();
  });

  it('shows connection status', async () => {
    renderWithProviders(<UserManagementDashboard />);

    await waitFor(() => {
      expect(screen.getByText('Connected')).toBeInTheDocument();
    });
  });

  it('displays notification badge with unread count', async () => {
    renderWithProviders(<UserManagementDashboard />);

    await waitFor(() => {
      expect(screen.getByText('2')).toBeInTheDocument(); // Unread count
    });
  });

  it('renders tab navigation', async () => {
    renderWithProviders(<UserManagementDashboard />);

    await waitFor(() => {
      expect(screen.getByText('Overview')).toBeInTheDocument();
      expect(screen.getByText('Notifications')).toBeInTheDocument();
      expect(screen.getByText('Preferences')).toBeInTheDocument();
      expect(screen.getByText('History')).toBeInTheDocument();
      expect(screen.getByText('Profile')).toBeInTheDocument();
    });

    // Company tab should not be visible for buyer role
    expect(screen.queryByText('Company')).not.toBeInTheDocument();
  });

  it('shows overview tab by default', async () => {
    renderWithProviders(<UserManagementDashboard />);

    await waitFor(() => {
      expect(screen.getByText('Dashboard overview and quick actions')).toBeInTheDocument();
    });
  });

  it('switches between tabs', async () => {
    const user = userEvent.setup();
    renderWithProviders(<UserManagementDashboard />);

    await waitFor(() => {
      expect(screen.getByText('Preferences')).toBeInTheDocument();
    });

    // Click on Preferences tab
    const preferencesTab = screen.getByText('Preferences');
    await user.click(preferencesTab);

    expect(screen.getByTestId('notification-preferences')).toBeInTheDocument();
  });

  it('switches to history tab', async () => {
    const user = userEvent.setup();
    renderWithProviders(<UserManagementDashboard />);

    await waitFor(() => {
      expect(screen.getByText('History')).toBeInTheDocument();
    });

    // Click on History tab
    const historyTab = screen.getByText('History');
    await user.click(historyTab);

    expect(screen.getByTestId('notification-history')).toBeInTheDocument();
  });

  it('switches to profile tab', async () => {
    const user = userEvent.setup();
    renderWithProviders(<UserManagementDashboard />);

    await waitFor(() => {
      expect(screen.getByText('Profile')).toBeInTheDocument();
    });

    // Click on Profile tab
    const profileTab = screen.getByText('Profile');
    await user.click(profileTab);

    expect(screen.getByTestId('user-profile')).toBeInTheDocument();
  });

  it('opens notification center when clicking notifications button', async () => {
    const user = userEvent.setup();
    renderWithProviders(<UserManagementDashboard />);

    await waitFor(() => {
      expect(screen.getByText('Notifications')).toBeInTheDocument();
    });

    // Click on the notifications button in header
    const notificationsButton = screen.getByRole('button', { name: /notifications/i });
    await user.click(notificationsButton);

    expect(screen.getByTestId('notification-center')).toBeInTheDocument();
  });

  it('closes notification center', async () => {
    const user = userEvent.setup();
    renderWithProviders(<UserManagementDashboard />);

    await waitFor(() => {
      expect(screen.getByText('Notifications')).toBeInTheDocument();
    });

    // Open notification center
    const notificationsButton = screen.getByRole('button', { name: /notifications/i });
    await user.click(notificationsButton);

    expect(screen.getByTestId('notification-center')).toBeInTheDocument();

    // Close notification center
    const closeButton = screen.getByText('Close');
    await user.click(closeButton);

    expect(screen.queryByTestId('notification-center')).not.toBeInTheDocument();
  });

  it('displays overview tab content correctly', async () => {
    renderWithProviders(<UserManagementDashboard />);

    await waitFor(() => {
      // Should show notification summary
      expect(screen.getByText('Recent activity summary')).toBeInTheDocument();
      expect(screen.getByText('2')).toBeInTheDocument(); // Unread count
      expect(screen.getByText('5')).toBeInTheDocument(); // Total count
      
      // Should show profile section
      expect(screen.getByText('Your account information')).toBeInTheDocument();
      
      // Should show quick actions
      expect(screen.getByText('Common tasks and settings')).toBeInTheDocument();
    });
  });

  it('shows high priority notification warning in overview', async () => {
    const highPrioritySummary = {
      ...mockSummary,
      high_priority_count: 2,
    };
    
    mockNotificationApi.getNotificationSummary.mockResolvedValue(highPrioritySummary);
    
    renderWithProviders(<UserManagementDashboard />);

    await waitFor(() => {
      expect(screen.getByText('2 high priority notifications')).toBeInTheDocument();
    });
  });

  it('handles loading state', () => {
    mockNotificationApi.getNotificationSummary.mockImplementation(
      () => new Promise(() => {}) // Never resolves
    );

    renderWithProviders(<UserManagementDashboard />);

    expect(screen.getByText('Loading...')).toBeInTheDocument();
  });

  it('shows correct tab descriptions', async () => {
    const user = userEvent.setup();
    renderWithProviders(<UserManagementDashboard />);

    await waitFor(() => {
      expect(screen.getByText('Dashboard overview and quick actions')).toBeInTheDocument();
    });

    // Switch to preferences tab
    const preferencesTab = screen.getByText('Preferences');
    await user.click(preferencesTab);

    expect(screen.getByText('Notification and communication preferences')).toBeInTheDocument();
  });

  it('shows notification badge on notifications tab', async () => {
    renderWithProviders(<UserManagementDashboard />);

    await waitFor(() => {
      // Find the notifications tab and check for badge
      const notificationsTab = screen.getByText('Notifications');
      const tabContainer = notificationsTab.closest('button');
      expect(tabContainer).toBeInTheDocument();
      
      // Should show unread count badge
      expect(screen.getByText('2')).toBeInTheDocument();
    });
  });

  it('handles role-based tab visibility', async () => {
    // Mock admin permissions
    const adminPermissions = {
      ...mockPermissions,
      user_role: 'admin',
      features: {
        ...mockPermissions.features,
        manage_company_settings: true,
      },
    };
    
    mockNotificationApi.getUIPermissions.mockResolvedValue(adminPermissions);
    
    renderWithProviders(<UserManagementDashboard />);

    await waitFor(() => {
      // Admin should see Company tab
      expect(screen.getByText('Company')).toBeInTheDocument();
    });
  });

  it('switches to company tab for admin users', async () => {
    const user = userEvent.setup();
    
    // Mock admin permissions
    const adminPermissions = {
      ...mockPermissions,
      user_role: 'admin',
      features: {
        ...mockPermissions.features,
        manage_company_settings: true,
      },
    };
    
    mockNotificationApi.getUIPermissions.mockResolvedValue(adminPermissions);
    
    renderWithProviders(<UserManagementDashboard />);

    await waitFor(() => {
      expect(screen.getByText('Company')).toBeInTheDocument();
    });

    // Click on Company tab
    const companyTab = screen.getByText('Company');
    await user.click(companyTab);

    expect(screen.getByTestId('company-settings')).toBeInTheDocument();
  });

  it('shows disconnected status when not connected', async () => {
    // Mock disconnected state
    mockNotificationApi.getNotificationSummary.mockImplementation(
      () => new Promise(() => {}) // Simulate connection issue
    );

    renderWithProviders(<UserManagementDashboard />);

    // Should show disconnected status
    expect(screen.getByText('Disconnected')).toBeInTheDocument();
  });

  it('handles quick actions in overview', async () => {
    const user = userEvent.setup();
    renderWithProviders(<UserManagementDashboard />);

    await waitFor(() => {
      expect(screen.getByText('Notification Preferences')).toBeInTheDocument();
      expect(screen.getByText('View History')).toBeInTheDocument();
      expect(screen.getByText('Update Profile')).toBeInTheDocument();
    });

    // Quick actions should be clickable
    const preferencesAction = screen.getByText('Notification Preferences');
    expect(preferencesAction).toBeInTheDocument();
  });

  it('shows user role information in overview', async () => {
    renderWithProviders(<UserManagementDashboard />);

    await waitFor(() => {
      expect(screen.getByText('Buyer Role')).toBeInTheDocument();
    });
  });

  it('displays profile completion in overview', async () => {
    renderWithProviders(<UserManagementDashboard />);

    await waitFor(() => {
      expect(screen.getByText('Profile Completion')).toBeInTheDocument();
      expect(screen.getByText('85%')).toBeInTheDocument();
    });
  });
});
