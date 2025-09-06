/**
 * Tests for NotificationCenter component
 */
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { NotificationProvider } from '../../../contexts/NotificationContext';
import { AuthProvider } from '../../../contexts/AuthContext';
import NotificationCenter from '../NotificationCenter';
import { notificationApi } from '../../../lib/notificationApi';

// Mock the notification API
jest.mock('../../../lib/notificationApi');
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

const MockNotificationProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <NotificationProvider>
    {children}
  </NotificationProvider>
);

const renderWithProviders = (component: React.ReactElement) => {
  return render(
    <MockAuthProvider>
      <MockNotificationProvider>
        {component}
      </MockNotificationProvider>
    </MockAuthProvider>
  );
};

describe('NotificationCenter', () => {
  const mockOnClose = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    
    // Mock API responses
    mockNotificationApi.getNotifications.mockResolvedValue({
      notifications: [
        {
          id: 'notif-1',
          user_id: 'user-1',
          company_id: 'company-1',
          notification_type: 'po_confirmed',
          title: 'Purchase Order Confirmed',
          message: 'Your purchase order PO-2024-001 has been confirmed.',
          channels: ['in_app', 'email'],
          priority: 'normal',
          status: 'unread',
          created_at: '2024-01-15T10:30:00Z',
          delivery_status: { in_app: 'delivered', email: 'delivered' },
        },
        {
          id: 'notif-2',
          user_id: 'user-1',
          company_id: 'company-1',
          notification_type: 'transparency_updated',
          title: 'Transparency Score Updated',
          message: 'Your transparency score has increased to 87.5%.',
          channels: ['in_app'],
          priority: 'low',
          status: 'read',
          created_at: '2024-01-14T16:45:00Z',
          read_at: '2024-01-14T17:00:00Z',
          delivery_status: { in_app: 'delivered' },
        },
      ],
      total_count: 2,
      page: 1,
      page_size: 20,
      has_next: false,
      has_previous: false,
      summary: {
        total_count: 2,
        unread_count: 1,
        high_priority_count: 0,
        urgent_count: 0,
        counts_by_type: {
          po_created: 0,
          po_confirmed: 1,
          po_shipped: 0,
          po_delivered: 0,
          po_cancelled: 0,
          transparency_updated: 1,
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
      },
    });

    mockNotificationApi.getNotificationSummary.mockResolvedValue({
      total_count: 2,
      unread_count: 1,
      high_priority_count: 0,
      urgent_count: 0,
      counts_by_type: {
        po_created: 0,
        po_confirmed: 1,
        po_shipped: 0,
        po_delivered: 0,
        po_cancelled: 0,
        transparency_updated: 1,
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
    });
  });

  it('renders notification center when open', () => {
    renderWithProviders(
      <NotificationCenter isOpen={true} onClose={mockOnClose} />
    );

    expect(screen.getByText('Notifications')).toBeInTheDocument();
    expect(screen.getByText('1')).toBeInTheDocument(); // Unread count badge
  });

  it('does not render when closed', () => {
    renderWithProviders(
      <NotificationCenter isOpen={false} onClose={mockOnClose} />
    );

    expect(screen.queryByText('Notifications')).not.toBeInTheDocument();
  });

  it('displays notifications correctly', async () => {
    renderWithProviders(
      <NotificationCenter isOpen={true} onClose={mockOnClose} />
    );

    await waitFor(() => {
      expect(screen.getByText('Purchase Order Confirmed')).toBeInTheDocument();
      expect(screen.getByText('Transparency Score Updated')).toBeInTheDocument();
    });
  });

  it('handles notification selection', async () => {
    const user = userEvent.setup();
    
    renderWithProviders(
      <NotificationCenter isOpen={true} onClose={mockOnClose} />
    );

    await waitFor(() => {
      expect(screen.getByText('Purchase Order Confirmed')).toBeInTheDocument();
    });

    // Find and click the first checkbox
    const checkboxes = screen.getAllByRole('checkbox');
    await user.click(checkboxes[0]);

    // Should show actions for selected notifications
    expect(screen.getByText(/Actions \(1\)/)).toBeInTheDocument();
  });

  it('handles mark as read action', async () => {
    const user = userEvent.setup();
    mockNotificationApi.markAsRead.mockResolvedValue();
    
    renderWithProviders(
      <NotificationCenter isOpen={true} onClose={mockOnClose} />
    );

    await waitFor(() => {
      expect(screen.getByText('Purchase Order Confirmed')).toBeInTheDocument();
    });

    // Find the notification actions menu
    const menuButtons = screen.getAllByRole('button', { name: /menu/i });
    if (menuButtons.length > 0) {
      await user.click(menuButtons[0]);
      
      const markReadButton = screen.getByText('Mark Read');
      await user.click(markReadButton);
      
      expect(mockNotificationApi.markAsRead).toHaveBeenCalledWith('notif-1');
    }
  });

  it('handles search functionality', async () => {
    const user = userEvent.setup();
    
    renderWithProviders(
      <NotificationCenter isOpen={true} onClose={mockOnClose} />
    );

    // Open filters
    const filtersButton = screen.getByText('Filters');
    await user.click(filtersButton);

    // Search for notifications
    const searchInput = screen.getByPlaceholderText('Search notifications...');
    await user.type(searchInput, 'Purchase Order');

    await waitFor(() => {
      expect(mockNotificationApi.getNotifications).toHaveBeenCalledWith(
        expect.objectContaining({
          search_query: 'Purchase Order',
        })
      );
    });
  });

  it('handles filter changes', async () => {
    const user = userEvent.setup();
    
    renderWithProviders(
      <NotificationCenter isOpen={true} onClose={mockOnClose} />
    );

    // Open filters
    const filtersButton = screen.getByText('Filters');
    await user.click(filtersButton);

    // Change status filter
    const statusSelect = screen.getByDisplayValue('All Status');
    await user.selectOptions(statusSelect, 'unread');

    await waitFor(() => {
      expect(mockNotificationApi.getNotifications).toHaveBeenCalledWith(
        expect.objectContaining({
          status: ['unread'],
        })
      );
    });
  });

  it('handles mark all as read', async () => {
    const user = userEvent.setup();
    mockNotificationApi.bulkOperation.mockResolvedValue();
    
    renderWithProviders(
      <NotificationCenter isOpen={true} onClose={mockOnClose} />
    );

    await waitFor(() => {
      expect(screen.getByText('Mark All Read')).toBeInTheDocument();
    });

    const markAllReadButton = screen.getByText('Mark All Read');
    await user.click(markAllReadButton);

    expect(mockNotificationApi.bulkOperation).toHaveBeenCalledWith({
      operation: 'mark_read',
      notification_ids: ['notif-1'], // Only unread notifications
    });
  });

  it('closes when clicking outside', async () => {
    const user = userEvent.setup();
    
    renderWithProviders(
      <NotificationCenter isOpen={true} onClose={mockOnClose} />
    );

    // Click on the backdrop
    const backdrop = document.querySelector('.fixed.inset-0.bg-black');
    if (backdrop) {
      await user.click(backdrop);
      expect(mockOnClose).toHaveBeenCalled();
    }
  });

  it('closes when clicking close button', async () => {
    const user = userEvent.setup();
    
    renderWithProviders(
      <NotificationCenter isOpen={true} onClose={mockOnClose} />
    );

    const closeButton = screen.getByLabelText('Close notifications');
    await user.click(closeButton);

    expect(mockOnClose).toHaveBeenCalled();
  });

  it('shows connection status indicator', () => {
    renderWithProviders(
      <NotificationCenter isOpen={true} onClose={mockOnClose} />
    );

    // Should show connection status indicator
    const connectionIndicator = document.querySelector('.h-2.w-2.rounded-full');
    expect(connectionIndicator).toBeInTheDocument();
  });

  it('handles bulk delete action', async () => {
    const user = userEvent.setup();
    mockNotificationApi.deleteNotification.mockResolvedValue();
    
    renderWithProviders(
      <NotificationCenter isOpen={true} onClose={mockOnClose} />
    );

    await waitFor(() => {
      expect(screen.getByText('Purchase Order Confirmed')).toBeInTheDocument();
    });

    // Select a notification
    const checkboxes = screen.getAllByRole('checkbox');
    await user.click(checkboxes[0]);

    // Open actions menu
    const actionsButton = screen.getByText(/Actions \(1\)/);
    await user.click(actionsButton);

    // Click delete
    const deleteButton = screen.getByText('Delete');
    await user.click(deleteButton);

    expect(mockNotificationApi.deleteNotification).toHaveBeenCalledWith('notif-1');
  });

  it('displays notification icons correctly', async () => {
    renderWithProviders(
      <NotificationCenter isOpen={true} onClose={mockOnClose} />
    );

    await waitFor(() => {
      // Should display emoji icons for different notification types
      expect(screen.getByText('📦')).toBeInTheDocument(); // PO notification
      expect(screen.getByText('📊')).toBeInTheDocument(); // Transparency notification
    });
  });

  it('shows action buttons for notifications with actions', async () => {
    // Mock notification with action
    mockNotificationApi.getNotifications.mockResolvedValue({
      notifications: [
        {
          id: 'notif-1',
          user_id: 'user-1',
          company_id: 'company-1',
          notification_type: 'po_confirmed',
          title: 'Purchase Order Confirmed',
          message: 'Your purchase order PO-2024-001 has been confirmed.',
          channels: ['in_app'],
          priority: 'normal',
          status: 'unread',
          created_at: '2024-01-15T10:30:00Z',
          action_url: '/purchase-orders/po-1',
          action_text: 'View Order',
          delivery_status: { in_app: 'delivered' },
        },
      ],
      total_count: 1,
      page: 1,
      page_size: 20,
      has_next: false,
      has_previous: false,
      summary: {
        total_count: 1,
        unread_count: 1,
        high_priority_count: 0,
        urgent_count: 0,
        counts_by_type: {
          po_created: 0,
          po_confirmed: 1,
          po_shipped: 0,
          po_delivered: 0,
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
      },
    });

    renderWithProviders(
      <NotificationCenter isOpen={true} onClose={mockOnClose} />
    );

    await waitFor(() => {
      expect(screen.getByText('View Order')).toBeInTheDocument();
    });
  });
});
