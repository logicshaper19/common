/**
 * API client for notification system
 */
import { apiClient } from './api';
import {
  Notification,
  NotificationSummary,
  NotificationPreferences,
  NotificationFilters,
  UserProfile,
  CompanySettings,
  UIPermissions,
} from '../types/notifications';

export class NotificationApi {
  /**
   * Get paginated notifications with filtering
   */
  async getNotifications(filters: NotificationFilters = {}): Promise<{
    notifications: Notification[];
    total: number;
    page: number;
    per_page: number;
    has_next: boolean;
    summary: NotificationSummary;
  }> {
    const response = await apiClient.get('/notifications', { params: filters });
    return response.data;
  }

  /**
   * Get notification summary
   */
  async getNotificationSummary(): Promise<NotificationSummary> {
    const response = await apiClient.get('/notifications/summary');
    return response.data;
  }

  /**
   * Mark notification as read
   */
  async markAsRead(notificationId: string): Promise<void> {
    await apiClient.put(`/notifications/${notificationId}/read`);
  }

  /**
   * Mark multiple notifications as read
   */
  async markMultipleAsRead(notificationIds: string[]): Promise<void> {
    await apiClient.put('/notifications/mark-read', { notification_ids: notificationIds });
  }

  /**
   * Mark all notifications as read
   */
  async markAllAsRead(): Promise<void> {
    await apiClient.put('/notifications/mark-all-read');
  }

  /**
   * Delete notification
   */
  async deleteNotification(notificationId: string): Promise<void> {
    await apiClient.delete(`/notifications/${notificationId}`);
  }

  /**
   * Delete multiple notifications
   */
  async deleteMultipleNotifications(notificationIds: string[]): Promise<void> {
    await apiClient.delete('/notifications/bulk-delete', { data: { notification_ids: notificationIds } });
  }

  /**
   * Get notification preferences
   */
  async getNotificationPreferences(): Promise<NotificationPreferences> {
    const response = await apiClient.get('/notifications/preferences');
    return response.data;
  }

  /**
   * Update notification preferences
   */
  async updateNotificationPreferences(preferences: Partial<NotificationPreferences>): Promise<NotificationPreferences> {
    const response = await apiClient.put('/notifications/preferences', preferences);
    return response.data;
  }

  /**
   * Get user profile
   */
  async getUserProfile(): Promise<UserProfile> {
    const response = await apiClient.get('/users/profile');
    return response.data;
  }

  /**
   * Update user profile
   */
  async updateUserProfile(profile: Partial<UserProfile>): Promise<UserProfile> {
    const response = await apiClient.put('/users/profile', profile);
    return response.data;
  }

  /**
   * Get company settings
   */
  async getCompanySettings(companyId: string): Promise<CompanySettings> {
    const response = await apiClient.get(`/companies/${companyId}/settings`);
    return response.data;
  }

  /**
   * Update company settings
   */
  async updateCompanySettings(companyId: string, settings: Partial<CompanySettings>): Promise<CompanySettings> {
    const response = await apiClient.put(`/companies/${companyId}/settings`, settings);
    return response.data;
  }

  /**
   * Get UI permissions for current user
   */
  async getUIPermissions(): Promise<UIPermissions> {
    const response = await apiClient.get('/users/permissions');
    return response.data;
  }

  /**
   * Test notification delivery
   */
  async testNotification(type: 'email' | 'sms' | 'push', message: string): Promise<{ success: boolean; message: string }> {
    const response = await apiClient.post('/notifications/test', { type, message });
    return response.data;
  }

  /**
   * Get notification templates
   */
  async getNotificationTemplates(): Promise<Array<{
    id: string;
    name: string;
    type: string;
    subject: string;
    content: string;
    variables: string[];
  }>> {
    const response = await apiClient.get('/notifications/templates');
    return response.data;
  }

  /**
   * Subscribe to real-time notifications
   */
  subscribeToNotifications(callback: (notification: Notification) => void): () => void {
    // WebSocket or SSE implementation would go here
    // For now, return a no-op unsubscribe function
    return () => {};
  }
}

// Export singleton instance
export const notificationApi = new NotificationApi();

// Legacy exports for backward compatibility
export const getNotifications = (filters?: NotificationFilters) => notificationApi.getNotifications(filters);
export const getNotificationSummary = () => notificationApi.getNotificationSummary();
export const markAsRead = (notificationId: string) => notificationApi.markAsRead(notificationId);
export const markMultipleAsRead = (notificationIds: string[]) => notificationApi.markMultipleAsRead(notificationIds);
export const markAllAsRead = () => notificationApi.markAllAsRead();
export const deleteNotification = (notificationId: string) => notificationApi.deleteNotification(notificationId);
export const deleteMultipleNotifications = (notificationIds: string[]) => notificationApi.deleteMultipleNotifications(notificationIds);
export const getNotificationPreferences = () => notificationApi.getNotificationPreferences();
export const updateNotificationPreferences = (preferences: Partial<NotificationPreferences>) => 
  notificationApi.updateNotificationPreferences(preferences);
export const getUserProfile = () => notificationApi.getUserProfile();
export const updateUserProfile = (profile: Partial<UserProfile>) => notificationApi.updateUserProfile(profile);
export const getCompanySettings = (companyId: string) => notificationApi.getCompanySettings(companyId);
export const updateCompanySettings = (companyId: string, settings: Partial<CompanySettings>) => 
  notificationApi.updateCompanySettings(companyId, settings);
export const getUIPermissions = () => notificationApi.getUIPermissions();
export const testNotification = (type: 'email' | 'sms' | 'push', message: string) => 
  notificationApi.testNotification(type, message);
export const getNotificationTemplates = () => notificationApi.getNotificationTemplates();
export const subscribeToNotifications = (callback: (notification: Notification) => void) => 
  notificationApi.subscribeToNotifications(callback);
