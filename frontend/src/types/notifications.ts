/**
 * Types and interfaces for notification and user management
 */

// Notification types
export type NotificationType = 
  | 'po_created'
  | 'po_confirmed'
  | 'po_shipped'
  | 'po_delivered'
  | 'po_cancelled'
  | 'transparency_updated'
  | 'supplier_invited'
  | 'supplier_joined'
  | 'system_alert'
  | 'user_mention'
  | 'deadline_reminder'
  | 'quality_issue'
  | 'compliance_alert';

export type NotificationChannel = 'in_app' | 'email' | 'sms' | 'webhook';

export type NotificationPriority = 'low' | 'normal' | 'high' | 'urgent';

export type NotificationStatus = 'unread' | 'read' | 'archived' | 'deleted';

// Core notification interface
export interface Notification {
  id: string;
  user_id: string;
  company_id: string;
  notification_type: NotificationType;
  title: string;
  message: string;
  channels: NotificationChannel[];
  priority: NotificationPriority;
  status: NotificationStatus;
  created_at: string;
  read_at?: string;
  archived_at?: string;
  expires_at?: string;
  
  // Related entities
  related_po_id?: string;
  related_company_id?: string;
  related_user_id?: string;
  
  // Metadata
  metadata?: Record<string, any>;
  action_url?: string;
  action_text?: string;
  
  // Delivery tracking
  delivery_status: {
    in_app: 'pending' | 'delivered' | 'failed';
    email?: 'pending' | 'sent' | 'delivered' | 'failed';
    sms?: 'pending' | 'sent' | 'delivered' | 'failed';
    webhook?: 'pending' | 'sent' | 'delivered' | 'failed';
  };
}

// Notification preferences
export interface NotificationPreferences {
  user_id: string;
  
  // Channel preferences by notification type
  preferences: {
    [K in NotificationType]: {
      enabled: boolean;
      channels: NotificationChannel[];
      priority_threshold: NotificationPriority;
      quiet_hours?: {
        enabled: boolean;
        start_time: string; // HH:MM format
        end_time: string;   // HH:MM format
        timezone: string;
      };
    };
  };
  
  // Global settings
  global_settings: {
    email_digest: {
      enabled: boolean;
      frequency: 'immediate' | 'hourly' | 'daily' | 'weekly';
      time: string; // HH:MM format for daily/weekly
      day?: number; // 0-6 for weekly (0 = Sunday)
    };
    mobile_push: {
      enabled: boolean;
      sound: boolean;
      vibration: boolean;
    };
    desktop_notifications: {
      enabled: boolean;
      sound: boolean;
    };
  };
  
  updated_at: string;
}

// Notification summary and stats
export interface NotificationSummary {
  total_count: number;
  unread_count: number;
  high_priority_count: number;
  urgent_count: number;
  
  counts_by_type: {
    [K in NotificationType]: number;
  };
  
  recent_notifications: Notification[];
  last_updated: string;
}

// Real-time notification update
export interface NotificationUpdate {
  type: 'new_notification' | 'notification_read' | 'notification_deleted' | 'bulk_update';
  notification?: Notification;
  notification_ids?: string[];
  summary: NotificationSummary;
  timestamp: string;
}

// User profile and settings
export interface UserProfile {
  id: string;
  email: string;
  full_name: string;
  title?: string;
  phone?: string;
  avatar_url?: string;
  
  // Company information
  company_id: string;
  company_name: string;
  role: 'admin' | 'buyer' | 'seller' | 'viewer';
  department?: string;
  
  // Account settings
  timezone: string;
  language: string;
  date_format: 'MM/DD/YYYY' | 'DD/MM/YYYY' | 'YYYY-MM-DD';
  time_format: '12h' | '24h';
  
  // Security settings
  two_factor_enabled: boolean;
  last_login_at?: string;
  password_changed_at: string;
  
  // Profile completion
  profile_completion: number;
  onboarding_completed: boolean;
  
  // Timestamps
  created_at: string;
  updated_at: string;
  last_active_at?: string;
}

// Company settings
export interface CompanySettings {
  company_id: string;
  company_name: string;
  
  // Basic information
  description?: string;
  website?: string;
  phone?: string;
  
  // Address
  address: {
    street: string;
    city: string;
    state: string;
    postal_code: string;
    country: string;
  };
  
  // Business details
  business_registration_number?: string;
  tax_id?: string;
  industry_sector?: string;
  company_size: 'startup' | 'small' | 'medium' | 'large' | 'enterprise';
  
  // Platform settings
  default_currency: string;
  default_timezone: string;
  
  // Branding
  logo_url?: string;
  primary_color?: string;
  
  // Features and permissions
  features_enabled: {
    transparency_tracking: boolean;
    supplier_onboarding: boolean;
    advanced_analytics: boolean;
    api_access: boolean;
    webhook_notifications: boolean;
  };
  
  // Notification settings
  notification_settings: {
    default_channels: NotificationChannel[];
    webhook_url?: string;
    webhook_secret?: string;
  };
  
  updated_at: string;
}

// User activity and audit log
export interface UserActivity {
  id: string;
  user_id: string;
  action: string;
  resource_type: string;
  resource_id?: string;
  details: Record<string, any>;
  ip_address?: string;
  user_agent?: string;
  timestamp: string;
}

// Role-based UI visibility
export interface UIPermissions {
  user_role: string;
  company_id: string;
  
  // Navigation permissions
  navigation: {
    dashboard: boolean;
    purchase_orders: boolean;
    companies: boolean;
    transparency: boolean;
    onboarding: boolean;
    analytics: boolean;
    users: boolean;
    settings: boolean;
  };
  
  // Feature permissions
  features: {
    create_purchase_order: boolean;
    edit_purchase_order: boolean;
    delete_purchase_order: boolean;
    confirm_purchase_order: boolean;
    view_all_companies: boolean;
    invite_suppliers: boolean;
    manage_users: boolean;
    view_analytics: boolean;
    export_data: boolean;
    manage_company_settings: boolean;
  };
  
  // Data access permissions
  data_access: {
    view_pricing: boolean;
    view_financial_data: boolean;
    view_supplier_details: boolean;
    view_transparency_scores: boolean;
    access_api: boolean;
  };
}

// Notification template
export interface NotificationTemplate {
  id: string;
  notification_type: NotificationType;
  name: string;
  
  // Template content
  subject_template: string;
  body_template: string;
  html_template?: string;
  
  // Template variables
  variables: {
    name: string;
    description: string;
    required: boolean;
    default_value?: string;
  }[];
  
  // Localization
  language: string;
  
  // Metadata
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

// Notification delivery status
export interface NotificationDelivery {
  id: string;
  notification_id: string;
  channel: NotificationChannel;
  status: 'pending' | 'sent' | 'delivered' | 'failed' | 'bounced';
  
  // Delivery details
  sent_at?: string;
  delivered_at?: string;
  failed_at?: string;
  error_message?: string;
  
  // External tracking
  external_id?: string; // Email service ID, SMS ID, etc.
  tracking_data?: Record<string, any>;
  
  // Retry information
  retry_count: number;
  next_retry_at?: string;
  max_retries: number;
}

// Bulk notification operations
export interface BulkNotificationOperation {
  operation: 'mark_read' | 'mark_unread' | 'archive' | 'delete';
  notification_ids: string[];
  filters?: {
    notification_type?: NotificationType;
    priority?: NotificationPriority;
    date_range?: {
      start: string;
      end: string;
    };
  };
}

// Notification search and filtering
export interface NotificationFilters {
  status?: NotificationStatus[];
  types?: NotificationType[];
  priorities?: NotificationPriority[];
  channels?: NotificationChannel[];
  date_range?: {
    start: string;
    end: string;
  };
  search_query?: string;
  related_po_id?: string;
  related_company_id?: string;
  // Pagination
  page?: number;
  per_page?: number;
}

// Notification pagination
export interface NotificationListResponse {
  notifications: Notification[];
  total_count: number;
  page: number;
  page_size: number;
  has_next: boolean;
  has_previous: boolean;
  summary: NotificationSummary;
}

// All types are exported inline above
