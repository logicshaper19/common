/**
 * Admin and Support Interface Types
 * Comprehensive type definitions for admin and support functionality
 */

// Product Catalog Management Types
export interface Product {
  id: string;
  common_product_id: string;
  name: string;
  description?: string;
  category: ProductCategory;
  can_have_composition: boolean;
  material_breakdown?: MaterialBreakdown;
  default_unit: string;
  hs_code?: string;
  origin_data_requirements?: OriginDataRequirements;
  created_at: string;
  updated_at: string;
  status: 'active' | 'inactive' | 'deprecated';
  usage_count: number;
  last_used?: string;
}

export type ProductCategory = 'raw_material' | 'processed' | 'finished_good';

export interface MaterialBreakdown {
  [material: string]: {
    min_percentage: number;
    max_percentage: number;
    required: boolean;
    description?: string;
  };
}

export interface OriginDataRequirements {
  coordinates?: 'required' | 'optional' | 'not_required';
  certifications?: string[];
  batch_tracking?: boolean;
  supplier_verification?: boolean;
  custom_fields?: CustomField[];
}

export interface CustomField {
  name: string;
  type: 'text' | 'number' | 'date' | 'boolean' | 'select';
  required: boolean;
  options?: string[];
  validation?: string;
}

export interface ProductFilter {
  category?: ProductCategory;
  can_have_composition?: boolean;
  status?: 'active' | 'inactive' | 'deprecated';
  search?: string;
  hs_code?: string;
  created_after?: string;
  created_before?: string;
  usage_min?: number;
  usage_max?: number;
  page: number;
  per_page: number;
}

export interface ProductListResponse {
  products: Product[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
  filters_applied: ProductFilter;
}

export interface ProductCreate {
  common_product_id: string;
  name: string;
  description?: string;
  category: ProductCategory;
  can_have_composition: boolean;
  material_breakdown?: MaterialBreakdown;
  default_unit: string;
  hs_code?: string;
  origin_data_requirements?: OriginDataRequirements;
}

export interface ProductUpdate {
  name?: string;
  description?: string;
  category?: ProductCategory;
  can_have_composition?: boolean;
  material_breakdown?: MaterialBreakdown;
  default_unit?: string;
  hs_code?: string;
  origin_data_requirements?: OriginDataRequirements;
  status?: 'active' | 'inactive' | 'deprecated';
}

export interface ProductBulkOperation {
  operation: 'activate' | 'deactivate' | 'deprecate' | 'delete' | 'export';
  product_ids: string[];
  reason?: string;
}

export interface ProductValidationResult {
  is_valid: boolean;
  errors: string[];
  warnings: string[];
  suggestions: string[];
}

// User and Company Management Types
export interface AdminUser {
  id: string;
  email: string;
  full_name: string;
  role: UserRole;
  company_id: string;
  company_name: string;
  is_active: boolean;
  last_login?: string;
  created_at: string;
  updated_at: string;
  permissions: string[];
  two_factor_enabled: boolean;
  login_attempts: number;
  locked_until?: string;
}

export type UserRole = 'admin' | 'buyer' | 'seller' | 'viewer' | 'support';

export interface Company {
  id: string;
  name: string;
  company_type: CompanyType;
  email: string;
  phone?: string;
  website?: string;
  address: Address;
  is_active: boolean;
  subscription_tier: SubscriptionTier;
  created_at: string;
  updated_at: string;
  user_count: number;
  po_count: number;
  transparency_score?: number;
  compliance_status: ComplianceStatus;
  last_activity?: string;
}

export type CompanyType = 'brand' | 'processor' | 'originator' | 'trader' | 'plantation';
export type SubscriptionTier = 'free' | 'basic' | 'premium' | 'enterprise';
export type ComplianceStatus = 'compliant' | 'warning' | 'non_compliant' | 'pending_review';

export interface Address {
  street: string;
  city: string;
  state?: string;
  postal_code?: string;
  country: string;
  coordinates?: {
    latitude: number;
    longitude: number;
  };
}

export interface UserFilter {
  role?: UserRole;
  company_id?: string;
  is_active?: boolean;
  has_two_factor?: boolean;
  last_login_after?: string;
  last_login_before?: string;
  search?: string;
  page: number;
  per_page: number;
}

export interface CompanyFilter {
  company_type?: CompanyType;
  subscription_tier?: SubscriptionTier;
  compliance_status?: ComplianceStatus;
  is_active?: boolean;
  created_after?: string;
  created_before?: string;
  min_transparency_score?: number;
  max_transparency_score?: number;
  search?: string;
  page: number;
  per_page: number;
}

export interface UserCreate {
  email: string;
  full_name: string;
  role: UserRole;
  company_id: string;
  send_invitation: boolean;
  permissions?: string[];
}

export interface UserUpdate {
  full_name?: string;
  role?: UserRole;
  is_active?: boolean;
  permissions?: string[];
  force_password_reset?: boolean;
}

export interface CompanyUpdate {
  name?: string;
  email?: string;
  phone?: string;
  website?: string;
  address?: Address;
  is_active?: boolean;
  subscription_tier?: SubscriptionTier;
  compliance_status?: ComplianceStatus;
}

export interface UserBulkOperation {
  operation: 'activate' | 'deactivate' | 'reset_password' | 'enable_2fa' | 'disable_2fa' | 'delete';
  user_ids: string[];
  reason?: string;
  notify_users?: boolean;
}

export interface CompanyBulkOperation {
  operation: 'activate' | 'deactivate' | 'upgrade_tier' | 'downgrade_tier' | 'compliance_review';
  company_ids: string[];
  reason?: string;
  new_tier?: SubscriptionTier;
  notify_admins?: boolean;
}

// Support Ticket System Types
export interface SupportTicket {
  id: string;
  ticket_number: string;
  title: string;
  description: string;
  priority: TicketPriority;
  status: TicketStatus;
  category: TicketCategory;
  reporter_id: string;
  reporter_name: string;
  reporter_email: string;
  reporter_company: string;
  assignee_id?: string;
  assignee_name?: string;
  created_at: string;
  updated_at: string;
  resolved_at?: string;
  first_response_at?: string;
  tags: string[];
  attachments: TicketAttachment[];
  messages: TicketMessage[];
  escalation_level: number;
  sla_breach: boolean;
  satisfaction_rating?: number;
  satisfaction_feedback?: string;
}

export type TicketPriority = 'low' | 'medium' | 'high' | 'urgent' | 'critical';
export type TicketStatus = 'open' | 'in_progress' | 'waiting_customer' | 'waiting_internal' | 'resolved' | 'closed';
export type TicketCategory = 'technical' | 'billing' | 'feature_request' | 'bug_report' | 'account' | 'compliance' | 'other';

export interface TicketAttachment {
  id: string;
  filename: string;
  file_size: number;
  content_type: string;
  uploaded_by: string;
  uploaded_at: string;
  download_url: string;
}

export interface TicketMessage {
  id: string;
  content: string;
  author_id: string;
  author_name: string;
  author_type: 'customer' | 'support' | 'system';
  created_at: string;
  is_internal: boolean;
  attachments: TicketAttachment[];
}

export interface TicketFilter {
  status?: TicketStatus;
  priority?: TicketPriority;
  category?: TicketCategory;
  assignee_id?: string;
  reporter_company?: string;
  created_after?: string;
  created_before?: string;
  sla_breach?: boolean;
  escalation_level?: number;
  search?: string;
  tags?: string[];
  page: number;
  per_page: number;
}

export interface TicketCreate {
  title: string;
  description: string;
  priority: TicketPriority;
  category: TicketCategory;
  tags?: string[];
  attachments?: File[];
}

export interface TicketUpdate {
  title?: string;
  description?: string;
  priority?: TicketPriority;
  status?: TicketStatus;
  category?: TicketCategory;
  assignee_id?: string;
  tags?: string[];
  escalation_level?: number;
}

export interface TicketMessageCreate {
  content: string;
  is_internal: boolean;
  attachments?: File[];
}

export interface TicketBulkOperation {
  operation: 'assign' | 'close' | 'escalate' | 'change_priority' | 'add_tag' | 'remove_tag';
  ticket_ids: string[];
  assignee_id?: string;
  priority?: TicketPriority;
  tag?: string;
  reason?: string;
}

// Audit Log Types
export interface AuditLogEntry {
  id: string;
  timestamp: string;
  user_id: string;
  user_name: string;
  user_email: string;
  company_id: string;
  company_name: string;
  action: AuditAction;
  resource_type: ResourceType;
  resource_id: string;
  resource_name?: string;
  details: AuditDetails;
  ip_address: string;
  user_agent: string;
  session_id: string;
  risk_level: RiskLevel;
  success: boolean;
  error_message?: string;
  duration_ms?: number;
}

export type AuditAction =
  | 'create' | 'read' | 'update' | 'delete'
  | 'login' | 'logout' | 'password_reset' | 'password_change'
  | 'invite_user' | 'activate_user' | 'deactivate_user'
  | 'export_data' | 'import_data' | 'bulk_operation'
  | 'permission_change' | 'role_change' | 'company_change'
  | 'api_access' | 'file_upload' | 'file_download'
  | 'system_config' | 'backup_create' | 'backup_restore';

export type ResourceType =
  | 'user' | 'company' | 'product' | 'purchase_order'
  | 'notification' | 'support_ticket' | 'audit_log'
  | 'system_config' | 'backup' | 'api_key' | 'session';

export interface AuditDetails {
  changes?: {
    field: string;
    old_value: any;
    new_value: any;
  }[];
  metadata?: Record<string, any>;
  affected_records?: number;
  query_params?: Record<string, any>;
  request_body?: Record<string, any>;
}

export type RiskLevel = 'low' | 'medium' | 'high' | 'critical';

export interface AuditFilter {
  user_id?: string;
  company_id?: string;
  action?: AuditAction;
  resource_type?: ResourceType;
  risk_level?: RiskLevel;
  success?: boolean;
  start_date?: string;
  end_date?: string;
  ip_address?: string;
  search?: string;
  page: number;
  per_page: number;
}

export interface AuditExportRequest {
  filters: AuditFilter;
  format: 'csv' | 'json' | 'xlsx';
  include_details: boolean;
  date_range: {
    start: string;
    end: string;
  };
}

// System Configuration and Monitoring Types
export interface SystemConfig {
  id: string;
  category: ConfigCategory;
  key: string;
  value: any;
  description: string;
  data_type: 'string' | 'number' | 'boolean' | 'json' | 'array';
  is_sensitive: boolean;
  requires_restart: boolean;
  validation_rules?: ValidationRule[];
  updated_by: string;
  updated_at: string;
  environment: 'development' | 'staging' | 'production';
}

export type ConfigCategory =
  | 'authentication' | 'database' | 'email' | 'storage'
  | 'api' | 'security' | 'monitoring' | 'features'
  | 'integrations' | 'performance' | 'backup';

export interface ValidationRule {
  type: 'required' | 'min' | 'max' | 'pattern' | 'enum';
  value: any;
  message: string;
}

export interface SystemHealth {
  status: 'healthy' | 'warning' | 'critical' | 'down';
  timestamp: string;
  services: ServiceHealth[];
  metrics: SystemMetrics;
  alerts: SystemAlert[];
  uptime: number;
  version: string;
}

export interface ServiceHealth {
  name: string;
  status: 'healthy' | 'warning' | 'critical' | 'down';
  response_time_ms: number;
  last_check: string;
  error_message?: string;
  dependencies: string[];
}

export interface SystemMetrics {
  cpu_usage: number;
  memory_usage: number;
  disk_usage: number;
  active_connections: number;
  requests_per_minute: number;
  error_rate: number;
  average_response_time: number;
  database_connections: number;
  queue_size: number;
}

export interface SystemAlert {
  id: string;
  type: AlertType;
  severity: AlertSeverity;
  title: string;
  description: string;
  created_at: string;
  resolved_at?: string;
  acknowledged_by?: string;
  acknowledged_at?: string;
  metadata: Record<string, any>;
}

export type AlertType =
  | 'performance' | 'security' | 'error' | 'capacity'
  | 'availability' | 'compliance' | 'backup' | 'integration';

export type AlertSeverity = 'info' | 'warning' | 'error' | 'critical';

export interface PerformanceMetric {
  timestamp: string;
  metric_name: string;
  value: number;
  unit: string;
  tags: Record<string, string>;
}

export interface BackupStatus {
  id: string;
  type: 'full' | 'incremental' | 'differential';
  status: 'running' | 'completed' | 'failed' | 'scheduled';
  started_at: string;
  completed_at?: string;
  size_bytes?: number;
  file_count?: number;
  error_message?: string;
  retention_days: number;
  location: string;
}

// Dashboard and Analytics Types
export interface AdminDashboardData {
  overview: AdminOverview;
  recent_activity: AuditLogEntry[];
  system_health: SystemHealth;
  alerts: SystemAlert[];
  user_stats: UserStatistics;
  company_stats: CompanyStatistics;
  support_stats: SupportStatistics;
}

export interface AdminOverview {
  total_users: number;
  active_users: number;
  total_companies: number;
  active_companies: number;
  total_products: number;
  total_purchase_orders: number;
  open_tickets: number;
  critical_alerts: number;
  system_uptime: number;
  last_backup: string;
}

export interface UserStatistics {
  new_users_today: number;
  new_users_week: number;
  active_sessions: number;
  login_failures_today: number;
  users_by_role: Record<UserRole, number>;
  users_by_company_type: Record<CompanyType, number>;
}

export interface CompanyStatistics {
  new_companies_today: number;
  new_companies_week: number;
  companies_by_tier: Record<SubscriptionTier, number>;
  companies_by_compliance: Record<ComplianceStatus, number>;
  average_transparency_score: number;
}

export interface SupportStatistics {
  open_tickets: number;
  tickets_today: number;
  tickets_week: number;
  average_response_time: number;
  tickets_by_priority: Record<TicketPriority, number>;
  tickets_by_category: Record<TicketCategory, number>;
  satisfaction_rating: number;
}


