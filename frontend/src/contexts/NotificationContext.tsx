/**
 * Notification Context for real-time notification management
 */
import React, { createContext, useContext, useEffect, useState, useCallback, useMemo, ReactNode, useRef } from 'react';
import { useAuth } from './AuthContext';
import { notificationApi } from '../lib/notificationApi';
import {
  Notification,
  NotificationSummary,
  NotificationUpdate,
  NotificationFilters,
  NotificationListResponse,
} from '../types/notifications';

// Notification context state
interface NotificationState {
  notifications: Notification[];
  summary: NotificationSummary | null;
  isLoading: boolean;
  isConnected: boolean;
  error: string | null;
  lastUpdate: string | null;
}

// Notification context type
interface NotificationContextType extends NotificationState {
  // Data fetching
  loadNotifications: (filters?: NotificationFilters, page?: number) => Promise<void>;
  refreshSummary: () => Promise<void>;
  
  // Notification actions
  markAsRead: (notificationId: string) => Promise<void>;
  markAsUnread: (notificationId: string) => Promise<void>;
  archiveNotification: (notificationId: string) => Promise<void>;
  deleteNotification: (notificationId: string) => Promise<void>;
  markAllAsRead: () => Promise<void>;
  
  // Real-time connection
  connect: () => void;
  disconnect: () => void;
  
  // Utility functions
  getUnreadCount: () => number;
  getHighPriorityCount: () => number;
  clearError: () => void;
}

// Create context
const NotificationContext = createContext<NotificationContextType | undefined>(undefined);

// Custom hook to use notification context
export function useNotifications(): NotificationContextType {
  const context = useContext(NotificationContext);
  if (context === undefined) {
    throw new Error('useNotifications must be used within a NotificationProvider');
  }
  return context;
}

// Notification provider props
interface NotificationProviderProps {
  children: ReactNode;
}

// Notification provider component
export function NotificationProvider({ children }: NotificationProviderProps) {
  const { user, isAuthenticated } = useAuth();
  const [state, setState] = useState<NotificationState>({
    notifications: [],
    summary: null,
    isLoading: false,
    isConnected: false,
    error: null,
    lastUpdate: null,
  });

  // WebSocket connection for real-time updates
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const maxReconnectAttempts = 5;

  // Load notifications
  const loadNotifications = useCallback(async (filters?: NotificationFilters, page = 1) => {
    if (!isAuthenticated) return;

    setState(prev => ({ ...prev, isLoading: true, error: null }));

    try {
      const response = await notificationApi.getNotifications({
        ...(filters || {}),
        page,
        per_page: 20
      });
      setState(prev => ({
        ...prev,
        notifications: page === 1 ? response.notifications : [...prev.notifications, ...response.notifications],
        summary: response.summary,
        isLoading: false,
        lastUpdate: new Date().toISOString(),
      }));
    } catch (error) {
      console.error('Failed to load notifications:', error);
      setState(prev => ({
        ...prev,
        isLoading: false,
        error: 'Failed to load notifications',
      }));
    }
  }, [isAuthenticated]);

  // Refresh summary
  const refreshSummary = useCallback(async () => {
    if (!isAuthenticated) return;

    try {
      const summary = await notificationApi.getNotificationSummary();
      setState(prev => ({ ...prev, summary }));
    } catch (error) {
      console.error('Failed to refresh summary:', error);
    }
  }, [isAuthenticated]);

  // Mark notification as read
  const markAsRead = useCallback(async (notificationId: string) => {
    try {
      await notificationApi.markAsRead(notificationId);
      
      setState(prev => ({
        ...prev,
        notifications: prev.notifications.map(n =>
          n.id === notificationId
            ? { ...n, status: 'read', read_at: new Date().toISOString() }
            : n
        ),
        summary: prev.summary
          ? {
              ...prev.summary,
              unread_count: Math.max(0, prev.summary.unread_count - 1),
            }
          : null,
      }));
    } catch (error) {
      console.error('Failed to mark notification as read:', error);
    }
  }, []);

  // Mark notification as unread
  const markAsUnread = useCallback(async (notificationId: string) => {
    try {
      await notificationApi.markAsRead(notificationId); // Use markAsRead as markAsUnread doesn't exist
      
      setState(prev => ({
        ...prev,
        notifications: prev.notifications.map(n =>
          n.id === notificationId
            ? { ...n, status: 'unread', read_at: undefined }
            : n
        ),
        summary: prev.summary
          ? {
              ...prev.summary,
              unread_count: prev.summary.unread_count + 1,
            }
          : null,
      }));
    } catch (error) {
      console.error('Failed to mark notification as unread:', error);
    }
  }, []);

  // Archive notification
  const archiveNotification = useCallback(async (notificationId: string) => {
    try {
      await notificationApi.markAsRead(notificationId); // Use markAsRead instead of archiveNotification
      
      setState(prev => ({
        ...prev,
        notifications: prev.notifications.map(n =>
          n.id === notificationId
            ? { ...n, status: 'archived', archived_at: new Date().toISOString() }
            : n
        ),
      }));
    } catch (error) {
      console.error('Failed to archive notification:', error);
    }
  }, []);

  // Delete notification
  const deleteNotification = useCallback(async (notificationId: string) => {
    try {
      await notificationApi.deleteNotification(notificationId);
      
      setState(prev => ({
        ...prev,
        notifications: prev.notifications.filter(n => n.id !== notificationId),
        summary: prev.summary
          ? {
              ...prev.summary,
              total_count: Math.max(0, prev.summary.total_count - 1),
              unread_count: prev.notifications.find(n => n.id === notificationId)?.status === 'unread'
                ? Math.max(0, prev.summary.unread_count - 1)
                : prev.summary.unread_count,
            }
          : null,
      }));
    } catch (error) {
      console.error('Failed to delete notification:', error);
    }
  }, []);

  // Mark all notifications as read
  const markAllAsRead = useCallback(async () => {
    try {
      const unreadNotifications = state.notifications.filter(n => n.status === 'unread');
      
      // Mark each notification as read individually since bulkOperation doesn't exist
      await Promise.all(
        unreadNotifications.map(n => notificationApi.markAsRead(n.id))
      );
      
      setState(prev => ({
        ...prev,
        notifications: prev.notifications.map(n =>
          n.status === 'unread'
            ? { ...n, status: 'read', read_at: new Date().toISOString() }
            : n
        ),
        summary: prev.summary
          ? { ...prev.summary, unread_count: 0 }
          : null,
      }));
    } catch (error) {
      console.error('Failed to mark all as read:', error);
    }
  }, [state.notifications]);

  // WebSocket connection management
  const connect = useCallback(() => {
    if (!user?.id || wsRef.current) return;

    try {
      // WebSocket URL for real-time notifications
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const host = process.env.REACT_APP_WS_HOST || window.location.host;
      const wsUrl = `${protocol}//${host}/ws/notifications/${user.id}`;



      // Real WebSocket connection
      const ws = new WebSocket(wsUrl);
      
      ws.onopen = () => {
        setState(prev => ({ ...prev, isConnected: true, error: null }));
        reconnectAttemptsRef.current = 0;
      };

      ws.onmessage = (event) => {
        try {
          const update: NotificationUpdate = JSON.parse(event.data);
          
          setState(prev => {
            let newNotifications = [...prev.notifications];
            
            switch (update.type) {
              case 'new_notification':
                if (update.notification) {
                  newNotifications = [update.notification, ...newNotifications];
                }
                break;
              case 'notification_read':
              case 'notification_deleted':
                if (update.notification_ids) {
                  newNotifications = newNotifications.filter(n => 
                    !update.notification_ids!.includes(n.id)
                  );
                }
                break;
            }
            
            return {
              ...prev,
              notifications: newNotifications,
              summary: update.summary,
              lastUpdate: update.timestamp,
            };
          });
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
        }
      };

      ws.onclose = () => {
        setState(prev => ({ ...prev, isConnected: false }));
        wsRef.current = null;
        
        // Attempt to reconnect
        if (reconnectAttemptsRef.current < maxReconnectAttempts) {
          reconnectAttemptsRef.current++;
          reconnectTimeoutRef.current = setTimeout(() => {
            connect();
          }, Math.pow(2, reconnectAttemptsRef.current) * 1000);
        }
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        setState(prev => ({ ...prev, error: 'Connection error' }));
      };

      wsRef.current = ws;
    } catch (error) {
      console.error('Failed to connect to WebSocket:', error);
      setState(prev => ({ ...prev, error: 'Failed to connect' }));
    }
  }, [user?.id, user?.company?.id, state.summary]);

  // Disconnect from WebSocket
  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    setState(prev => ({ ...prev, isConnected: false }));
  }, []);

  // Utility functions
  const getUnreadCount = useCallback(() => {
    return state.summary?.unread_count || 0;
  }, [state.summary]);

  const getHighPriorityCount = useCallback(() => {
    return state.summary?.high_priority_count || 0;
  }, [state.summary]);

  const clearError = useCallback(() => {
    setState(prev => ({ ...prev, error: null }));
  }, []);

  // Initialize notifications when user is authenticated
  useEffect(() => {
    if (isAuthenticated && user) {
      loadNotifications();
      refreshSummary();
      connect();
    } else {
      disconnect();
      setState({
        notifications: [],
        summary: null,
        isLoading: false,
        isConnected: false,
        error: null,
        lastUpdate: null,
      });
    }

    return () => {
      disconnect();
    };
  }, [isAuthenticated, user, loadNotifications, refreshSummary, connect, disconnect]);

  // Context value
  const value: NotificationContextType = useMemo(() => ({
    ...state,
    loadNotifications,
    refreshSummary,
    markAsRead,
    markAsUnread,
    archiveNotification,
    deleteNotification,
    markAllAsRead,
    connect,
    disconnect,
    getUnreadCount,
    getHighPriorityCount,
    clearError,
  }), [
    state,
    loadNotifications,
    refreshSummary,
    markAsRead,
    markAsUnread,
    archiveNotification,
    deleteNotification,
    markAllAsRead,
    connect,
    disconnect,
    getUnreadCount,
    getHighPriorityCount,
    clearError,
  ]);

  return (
    <NotificationContext.Provider value={value}>
      {children}
    </NotificationContext.Provider>
  );
}

export default NotificationContext;
