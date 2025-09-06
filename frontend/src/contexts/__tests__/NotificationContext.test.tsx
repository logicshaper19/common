/**
 * Tests for NotificationContext
 */
import React from 'react';
import { renderHook, act } from '@testing-library/react';
import { AuthProvider } from '../AuthContext';
import { NotificationProvider, useNotifications } from '../NotificationContext';
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

const MockProviders: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <MockAuthProvider>
    <NotificationProvider>
      {children}
    </NotificationProvider>
  </MockAuthProvider>
);

const mockNotifications = [
  {
    id: 'notif-1',
    user_id: 'user-1',
    company_id: 'company-1',
    notification_type: 'po_confirmed' as const,
    title: 'Purchase Order Confirmed',
    message: 'Your purchase order PO-2024-001 has been confirmed.',
    channels: ['in_app', 'email'] as const,
    priority: 'normal' as const,
    status: 'unread' as const,
    created_at: '2024-01-15T10:30:00Z',
    delivery_status: { in_app: 'delivered' as const, email: 'delivered' as const },
  },
  {
    id: 'notif-2',
    user_id: 'user-1',
    company_id: 'company-1',
    notification_type: 'transparency_updated' as const,
    title: 'Transparency Score Updated',
    message: 'Your transparency score has increased to 87.5%.',
    channels: ['in_app'] as const,
    priority: 'low' as const,
    status: 'read' as const,
    created_at: '2024-01-14T16:45:00Z',
    read_at: '2024-01-14T17:00:00Z',
    delivery_status: { in_app: 'delivered' as const },
  },
];

const mockSummary = {
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
  recent_notifications: mockNotifications.slice(0, 3),
  last_updated: '2024-01-15T10:30:00Z',
};

describe('NotificationContext', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    
    mockNotificationApi.getNotifications.mockResolvedValue({
      notifications: mockNotifications,
      total_count: 2,
      page: 1,
      page_size: 20,
      has_next: false,
      has_previous: false,
      summary: mockSummary,
    });

    mockNotificationApi.getNotificationSummary.mockResolvedValue(mockSummary);
    mockNotificationApi.markAsRead.mockResolvedValue();
    mockNotificationApi.markAsUnread.mockResolvedValue();
    mockNotificationApi.archiveNotification.mockResolvedValue();
    mockNotificationApi.deleteNotification.mockResolvedValue();
    mockNotificationApi.bulkOperation.mockResolvedValue();
  });

  const renderHookWithProviders = () => {
    return renderHook(() => useNotifications(), {
      wrapper: MockProviders,
    });
  };

  it('provides initial state', () => {
    const { result } = renderHookWithProviders();

    expect(result.current.notifications).toEqual([]);
    expect(result.current.summary).toBeNull();
    expect(result.current.isLoading).toBe(false);
    expect(result.current.isConnected).toBe(false);
    expect(result.current.error).toBeNull();
  });

  it('loads notifications and summary on mount', async () => {
    const { result, waitForNextUpdate } = renderHookWithProviders();

    await waitForNextUpdate();

    expect(mockNotificationApi.getNotifications).toHaveBeenCalled();
    expect(mockNotificationApi.getNotificationSummary).toHaveBeenCalled();
    expect(result.current.notifications).toEqual(mockNotifications);
    expect(result.current.summary).toEqual(mockSummary);
  });

  it('marks notification as read', async () => {
    const { result, waitForNextUpdate } = renderHookWithProviders();

    await waitForNextUpdate();

    await act(async () => {
      await result.current.markAsRead('notif-1');
    });

    expect(mockNotificationApi.markAsRead).toHaveBeenCalledWith('notif-1');
    
    // Check that local state is updated
    const updatedNotification = result.current.notifications.find(n => n.id === 'notif-1');
    expect(updatedNotification?.status).toBe('read');
    expect(updatedNotification?.read_at).toBeDefined();
  });

  it('marks notification as unread', async () => {
    const { result, waitForNextUpdate } = renderHookWithProviders();

    await waitForNextUpdate();

    await act(async () => {
      await result.current.markAsUnread('notif-2');
    });

    expect(mockNotificationApi.markAsUnread).toHaveBeenCalledWith('notif-2');
    
    // Check that local state is updated
    const updatedNotification = result.current.notifications.find(n => n.id === 'notif-2');
    expect(updatedNotification?.status).toBe('unread');
    expect(updatedNotification?.read_at).toBeUndefined();
  });

  it('archives notification', async () => {
    const { result, waitForNextUpdate } = renderHookWithProviders();

    await waitForNextUpdate();

    await act(async () => {
      await result.current.archiveNotification('notif-1');
    });

    expect(mockNotificationApi.archiveNotification).toHaveBeenCalledWith('notif-1');
    
    // Check that local state is updated
    const updatedNotification = result.current.notifications.find(n => n.id === 'notif-1');
    expect(updatedNotification?.status).toBe('archived');
    expect(updatedNotification?.archived_at).toBeDefined();
  });

  it('deletes notification', async () => {
    const { result, waitForNextUpdate } = renderHookWithProviders();

    await waitForNextUpdate();

    await act(async () => {
      await result.current.deleteNotification('notif-1');
    });

    expect(mockNotificationApi.deleteNotification).toHaveBeenCalledWith('notif-1');
    
    // Check that notification is removed from local state
    const deletedNotification = result.current.notifications.find(n => n.id === 'notif-1');
    expect(deletedNotification).toBeUndefined();
  });

  it('marks all notifications as read', async () => {
    const { result, waitForNextUpdate } = renderHookWithProviders();

    await waitForNextUpdate();

    await act(async () => {
      await result.current.markAllAsRead();
    });

    expect(mockNotificationApi.bulkOperation).toHaveBeenCalledWith({
      operation: 'mark_read',
      notification_ids: ['notif-1'], // Only unread notifications
    });
    
    // Check that all notifications are marked as read
    const unreadNotifications = result.current.notifications.filter(n => n.status === 'unread');
    expect(unreadNotifications).toHaveLength(0);
  });

  it('loads more notifications with filters', async () => {
    const { result, waitForNextUpdate } = renderHookWithProviders();

    await waitForNextUpdate();

    const filters = { status: ['unread'] as const };

    await act(async () => {
      await result.current.loadNotifications(filters, 1);
    });

    expect(mockNotificationApi.getNotifications).toHaveBeenCalledWith(filters, 1);
  });

  it('refreshes summary', async () => {
    const { result, waitForNextUpdate } = renderHookWithProviders();

    await waitForNextUpdate();

    await act(async () => {
      await result.current.refreshSummary();
    });

    expect(mockNotificationApi.getNotificationSummary).toHaveBeenCalledTimes(2);
  });

  it('provides unread count', async () => {
    const { result, waitForNextUpdate } = renderHookWithProviders();

    await waitForNextUpdate();

    expect(result.current.getUnreadCount()).toBe(1);
  });

  it('provides high priority count', async () => {
    const { result, waitForNextUpdate } = renderHookWithProviders();

    await waitForNextUpdate();

    expect(result.current.getHighPriorityCount()).toBe(0);
  });

  it('clears error', async () => {
    const { result, waitForNextUpdate } = renderHookWithProviders();

    await waitForNextUpdate();

    // Simulate an error
    act(() => {
      result.current.clearError();
    });

    expect(result.current.error).toBeNull();
  });

  it('handles API errors gracefully', async () => {
    mockNotificationApi.getNotifications.mockRejectedValue(new Error('API Error'));
    
    const { result, waitForNextUpdate } = renderHookWithProviders();

    await waitForNextUpdate();

    expect(result.current.error).toBe('Failed to load notifications');
    expect(result.current.isLoading).toBe(false);
  });

  it('handles mark as read error gracefully', async () => {
    mockNotificationApi.markAsRead.mockRejectedValue(new Error('API Error'));
    
    const { result, waitForNextUpdate } = renderHookWithProviders();

    await waitForNextUpdate();

    await act(async () => {
      await result.current.markAsRead('notif-1');
    });

    // Should not crash and notification should remain unchanged
    const notification = result.current.notifications.find(n => n.id === 'notif-1');
    expect(notification?.status).toBe('unread'); // Original status
  });

  it('connects and disconnects WebSocket', async () => {
    const { result, waitForNextUpdate } = renderHookWithProviders();

    await waitForNextUpdate();

    // In development mode, should simulate connection
    expect(result.current.isConnected).toBe(true);

    act(() => {
      result.current.disconnect();
    });

    expect(result.current.isConnected).toBe(false);

    act(() => {
      result.current.connect();
    });

    expect(result.current.isConnected).toBe(true);
  });

  it('updates summary when marking notification as read', async () => {
    const { result, waitForNextUpdate } = renderHookWithProviders();

    await waitForNextUpdate();

    const initialUnreadCount = result.current.summary?.unread_count || 0;

    await act(async () => {
      await result.current.markAsRead('notif-1');
    });

    expect(result.current.summary?.unread_count).toBe(initialUnreadCount - 1);
  });

  it('updates summary when deleting notification', async () => {
    const { result, waitForNextUpdate } = renderHookWithProviders();

    await waitForNextUpdate();

    const initialTotalCount = result.current.summary?.total_count || 0;
    const initialUnreadCount = result.current.summary?.unread_count || 0;

    await act(async () => {
      await result.current.deleteNotification('notif-1'); // This is an unread notification
    });

    expect(result.current.summary?.total_count).toBe(initialTotalCount - 1);
    expect(result.current.summary?.unread_count).toBe(initialUnreadCount - 1);
  });

  it('handles pagination correctly', async () => {
    const page2Notifications = [
      {
        id: 'notif-3',
        user_id: 'user-1',
        company_id: 'company-1',
        notification_type: 'system_alert' as const,
        title: 'System Alert',
        message: 'System maintenance scheduled.',
        channels: ['in_app'] as const,
        priority: 'high' as const,
        status: 'unread' as const,
        created_at: '2024-01-13T12:00:00Z',
        delivery_status: { in_app: 'delivered' as const },
      },
    ];

    mockNotificationApi.getNotifications.mockResolvedValueOnce({
      notifications: mockNotifications,
      total_count: 3,
      page: 1,
      page_size: 2,
      has_next: true,
      has_previous: false,
      summary: mockSummary,
    });

    const { result, waitForNextUpdate } = renderHookWithProviders();

    await waitForNextUpdate();

    // Load page 2
    mockNotificationApi.getNotifications.mockResolvedValueOnce({
      notifications: page2Notifications,
      total_count: 3,
      page: 2,
      page_size: 2,
      has_next: false,
      has_previous: true,
      summary: mockSummary,
    });

    await act(async () => {
      await result.current.loadNotifications({}, 2);
    });

    // Should append to existing notifications
    expect(result.current.notifications).toHaveLength(3);
    expect(result.current.notifications[2].id).toBe('notif-3');
  });
});
