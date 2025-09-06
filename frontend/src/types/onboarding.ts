/**
 * Types and interfaces for supplier onboarding and relationship management
 */

// Company onboarding types
export interface CompanyOnboardingData {
  // Unique identifier
  id?: string;
  
  // Basic company information
  company_name: string;
  company_type: 'brand' | 'processor' | 'originator';
  email: string;
  phone?: string;
  website?: string;
  description?: string;
  
  // Address information
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
  annual_revenue?: string;
  employee_count?: string;
  
  // Certifications and compliance
  certifications: string[];
  compliance_standards: string[];
  
  // Contact person
  primary_contact: {
    full_name: string;
    email: string;
    phone?: string;
    title: string;
  };
}

// User onboarding data
export interface UserOnboardingData {
  full_name: string;
  email: string;
  password: string;
  confirm_password: string;
  title: string;
  phone?: string;
  role: 'admin' | 'buyer' | 'seller';
  department?: string;
}

// Onboarding step configuration
export interface OnboardingStep {
  id: string;
  title: string;
  description: string;
  component: string;
  required: boolean;
  order: number;
  company_types?: string[];
  roles?: string[];
  estimated_time?: number;
}

// Onboarding progress
export interface OnboardingProgress {
  user_id: string;
  company_id: string;
  current_step: string;
  completed_steps: string[];
  total_steps: number;
  completion_percentage: number;
  started_at: string;
  last_updated: string;
  completed_at?: string;
  skipped_steps: string[];
}

// Supplier invitation types
export interface SupplierInvitation {
  id: string;
  supplier_email: string;
  supplier_name: string;
  company_type: 'brand' | 'processor' | 'originator';
  relationship_type: 'supplier' | 'customer' | 'partner';
  invitation_message?: string;
  data_sharing_permissions: DataSharingPermissions;
  invited_by_company_id: string;
  invited_by_company_name: string;
  invited_by_user_id: string;
  invited_by_user_name: string;
  status: 'pending' | 'accepted' | 'declined' | 'expired';
  sent_at: string;
  expires_at: string;
  accepted_at?: string;
  declined_at?: string;
  decline_reason?: string;
}

// Data sharing permissions
export interface DataSharingPermissions {
  view_purchase_orders: boolean;
  view_product_details: boolean;
  view_pricing: boolean;
  view_delivery_schedules: boolean;
  view_quality_metrics: boolean;
  view_sustainability_data: boolean;
  view_transparency_scores: boolean;
  edit_order_confirmations: boolean;
  edit_delivery_updates: boolean;
  edit_quality_reports: boolean;
  receive_notifications: boolean;
  access_analytics: boolean;
}

// Business relationship types
export interface BusinessRelationship {
  id: string;
  buyer_company_id: string;
  buyer_company_name: string;
  seller_company_id: string;
  seller_company_name: string;
  relationship_type: 'supplier' | 'customer' | 'partner';
  status: 'pending' | 'active' | 'suspended' | 'terminated';
  data_sharing_permissions: DataSharingPermissions;
  invited_by_company_id?: string;
  invited_by_company_name?: string;
  established_at: string;
  terminated_at?: string;
  last_interaction?: string;
  total_orders: number;
  total_value: number;
  transparency_score?: number;
}

// Viral cascade analytics
export interface ViralCascadeMetrics {
  total_invitations_sent: number;
  total_companies_onboarded: number;
  conversion_rate: number;
  average_time_to_onboard: number;
  cascade_levels: CascadeLevel[];
  top_inviters: TopInviter[];
  onboarding_funnel: OnboardingFunnelStep[];
  geographic_distribution: GeographicDistribution[];
  company_type_distribution: CompanyTypeDistribution[];
  time_series_data: TimeSeriesPoint[];
}

export interface CascadeLevel {
  level: number;
  companies_invited: number;
  companies_onboarded: number;
  conversion_rate: number;
  average_time_to_onboard: number;
}

export interface TopInviter {
  company_id: string;
  company_name: string;
  company_type: string;
  invitations_sent: number;
  successful_onboardings: number;
  conversion_rate: number;
  cascade_impact: number;
}

export interface OnboardingFunnelStep {
  step: string;
  companies_entered: number;
  companies_completed: number;
  completion_rate: number;
  average_time_spent: number;
  drop_off_rate: number;
}

export interface GeographicDistribution {
  country: string;
  region?: string;
  companies_count: number;
  invitations_sent: number;
  onboarding_rate: number;
}

export interface CompanyTypeDistribution {
  company_type: string;
  count: number;
  percentage: number;
  average_onboarding_time: number;
}

export interface TimeSeriesPoint {
  date: string;
  invitations_sent: number;
  companies_onboarded: number;
  cumulative_companies: number;
  conversion_rate: number;
}

// Invitation template
export interface InvitationTemplate {
  id: string;
  name: string;
  subject: string;
  body: string;
  company_type?: string;
  relationship_type?: string;
  is_default: boolean;
  created_by: string;
  created_at: string;
  variables: string[];
}

// Onboarding configuration
export interface OnboardingConfiguration {
  company_type: string;
  role: string;
  steps: OnboardingStep[];
  welcome_message: string;
  completion_message: string;
  estimated_total_time: number;
  required_steps_count: number;
  optional_steps_count: number;
}

// Company setup status
export interface CompanySetupStatus {
  company_id: string;
  basic_info_completed: boolean;
  address_completed: boolean;
  business_details_completed: boolean;
  certifications_completed: boolean;
  primary_contact_completed: boolean;
  data_sharing_configured: boolean;
  first_supplier_invited: boolean;
  first_order_created: boolean;
  transparency_configured: boolean;
  overall_completion: number;
  setup_completed_at?: string;
}

// Relationship analytics
export interface RelationshipAnalytics {
  company_id: string;
  total_relationships: number;
  active_relationships: number;
  pending_relationships: number;
  supplier_relationships: number;
  customer_relationships: number;
  partner_relationships: number;
  average_relationship_duration: number;
  relationship_growth_rate: number;
  top_suppliers: TopPartner[];
  top_customers: TopPartner[];
  relationship_health_score: number;
  data_sharing_utilization: number;
}

export interface TopPartner {
  company_id: string;
  company_name: string;
  company_type: string;
  relationship_type: string;
  total_orders: number;
  total_value: number;
  relationship_duration: number;
  transparency_score: number;
  last_interaction: string;
}

// Email integration types
export interface EmailTemplate {
  id: string;
  name: string;
  type: 'invitation' | 'welcome' | 'reminder' | 'completion';
  subject: string;
  html_body: string;
  text_body: string;
  variables: EmailVariable[];
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface EmailVariable {
  name: string;
  description: string;
  example: string;
  required: boolean;
}

export interface EmailSendRequest {
  template_id: string;
  recipient_email: string;
  recipient_name: string;
  variables: Record<string, string>;
  send_at?: string;
  priority: 'low' | 'normal' | 'high';
}


