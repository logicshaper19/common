/**
 * Frontend permission utilities for role-based access control
 * Mirrors the backend PermissionService logic
 */

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: string;
  is_active: boolean;
  company: {
    id: string;
    name: string;
    company_type: string;
  };
}

export interface DashboardConfig {
  can_create_po: boolean;
  can_confirm_po: boolean;
  can_manage_team: boolean;
  can_view_analytics: boolean;
  can_manage_settings: boolean;
  can_audit_companies: boolean;
  can_regulate_platform: boolean;
  can_manage_trader_chain?: boolean;
  can_view_margin_analysis?: boolean;
  can_report_farm_data?: boolean;
  can_manage_certifications?: boolean;
}

// Company Types
export const CompanyType = {
  BRAND: 'brand',
  PROCESSOR: 'processor',
  ORIGINATOR: 'originator',
  TRADER: 'trader',
  AUDITOR: 'auditor',
  REGULATOR: 'regulator'
} as const;

// User Roles
export const UserRole = {
  ADMIN: 'admin',
  SUPPLY_CHAIN_MANAGER: 'supply_chain_manager',
  PRODUCTION_MANAGER: 'production_manager',
  VIEWER: 'viewer',
  AUDITOR: 'auditor',
  // Brand roles
  BRAND_MANAGER: 'brand_manager',
  PROCUREMENT_DIRECTOR: 'procurement_director',
  CSR_MANAGER: 'csr_manager',
  // Trader roles
  TRADER: 'trader',
  SUSTAINABILITY_MANAGER: 'sustainability_manager',
  // Processor roles
  REFINERY_MANAGER: 'refinery_manager',
  QUALITY_MANAGER: 'quality_manager',
  // Mill roles
  MILL_MANAGER: 'mill_manager',
  OPERATIONS_MANAGER: 'operations_manager',
  // Plantation roles
  PLANTATION_MANAGER: 'plantation_manager',
  HARVEST_MANAGER: 'harvest_manager',
  // Originator roles
  COOPERATIVE_MANAGER: 'cooperative_manager'
} as const;

/**
 * Check if user can create purchase orders
 * Brands, Traders, and Processors issue POs DOWNSTREAM
 * Originators are the source - they don't create POs, they only receive them
 */
export const canCreatePO = (user: User): boolean => {
  // Brand roles that can create POs
  const brandRoles = [
    UserRole.BRAND_MANAGER,
    UserRole.PROCUREMENT_DIRECTOR,
    UserRole.CSR_MANAGER,
    UserRole.SUPPLY_CHAIN_MANAGER
  ];
  
  // Trader roles that can create POs
  const traderRoles = [
    UserRole.TRADER,
    UserRole.SUSTAINABILITY_MANAGER,
    UserRole.SUPPLY_CHAIN_MANAGER
  ];
  
  // Processor roles that can create POs
  const processorRoles = [
    UserRole.REFINERY_MANAGER,
    UserRole.QUALITY_MANAGER,
    UserRole.SUPPLY_CHAIN_MANAGER
  ];
  
  return (
    (user.company.company_type === CompanyType.BRAND && brandRoles.includes(user.role as any)) ||
    (user.company.company_type === CompanyType.TRADER && traderRoles.includes(user.role as any)) ||
    (user.company.company_type === CompanyType.PROCESSOR && processorRoles.includes(user.role as any))
  );
};

/**
 * Check if user can confirm purchase orders
 * Processors and Originators confirm POs received from UPSTREAM
 */
export const canConfirmPO = (user: User): boolean => {
  // Processor roles that can confirm POs
  const processorRoles = [
    UserRole.REFINERY_MANAGER,
    UserRole.QUALITY_MANAGER,
    UserRole.PRODUCTION_MANAGER,
    'processor',  // Generic processor role
    'quality_manager'  // Quality manager role
  ];
  
  // Mill roles that can confirm POs
  const millRoles = [
    UserRole.MILL_MANAGER,
    UserRole.OPERATIONS_MANAGER,
    UserRole.PRODUCTION_MANAGER
  ];
  
  // Plantation roles that can confirm POs
  const plantationRoles = [
    UserRole.PLANTATION_MANAGER,
    UserRole.HARVEST_MANAGER,
    UserRole.PRODUCTION_MANAGER
  ];
  
  // Originator roles that can confirm POs
  const originatorRoles = [
    UserRole.COOPERATIVE_MANAGER,
    'originator'
  ];
  
  return (
    (user.company.company_type === CompanyType.PROCESSOR && processorRoles.includes(user.role as any)) ||
    (user.company.company_type === 'mill_processor' && millRoles.includes(user.role as any)) ||
    (user.company.company_type === 'plantation_grower' && plantationRoles.includes(user.role as any)) ||
    ([CompanyType.ORIGINATOR, 'smallholder_cooperative', 'plantation_grower'].includes(user.company.company_type) && originatorRoles.includes(user.role as any))
  );
};

/**
 * Check if user can manage team members
 */
export const canManageTeam = (user: User): boolean => {
  return user.role === UserRole.ADMIN || 
         user.role === 'originator' ||
         user.role === UserRole.BRAND_MANAGER ||
         user.role === UserRole.PLANTATION_MANAGER ||
         user.role === UserRole.COOPERATIVE_MANAGER;
};

/**
 * Check if user can manage company settings
 */
export const canManageSettings = (user: User): boolean => {
  return user.role === UserRole.ADMIN || 
         user.role === 'originator' ||
         user.role === UserRole.BRAND_MANAGER ||
         user.role === UserRole.PLANTATION_MANAGER ||
         user.role === UserRole.COOPERATIVE_MANAGER;
};

/**
 * Check if user can audit companies
 */
export const canAuditCompanies = (user: User): boolean => {
  return user.role === UserRole.AUDITOR;
};

/**
 * Check if user can regulate platform
 */
export const canRegulatePlatform = (user: User): boolean => {
  return user.role === UserRole.ADMIN; // Using ADMIN instead of REGULATOR
};

/**
 * Check if user can manage trader chain (for trader companies)
 */
export const canManageTraderChain = (user: User): boolean => {
  return user.company.company_type === CompanyType.TRADER;
};

/**
 * Check if user can view margin analysis (for trader companies)
 */
export const canViewMarginAnalysis = (user: User): boolean => {
  return user.company.company_type === CompanyType.TRADER;
};

/**
 * Check if user can report farm data (for originator companies)
 */
export const canReportFarmData = (user: User): boolean => {
  return user.company.company_type === CompanyType.ORIGINATOR || 
         user.company.company_type === 'plantation_grower' ||
         user.company.company_type === 'smallholder_cooperative';
};

/**
 * Check if user can manage certifications (for originator companies)
 */
export const canManageCertifications = (user: User): boolean => {
  return user.company.company_type === CompanyType.ORIGINATOR || 
         user.company.company_type === 'plantation_grower' ||
         user.company.company_type === 'smallholder_cooperative';
};

/**
 * Get dashboard configuration for a user
 */
export const getDashboardConfig = (user: User): DashboardConfig => {
  return {
    can_create_po: canCreatePO(user),
    can_confirm_po: canConfirmPO(user),
    can_manage_team: canManageTeam(user),
    can_view_analytics: true, // Most users can view analytics
    can_manage_settings: canManageSettings(user),
    can_audit_companies: canAuditCompanies(user),
    can_regulate_platform: canRegulatePlatform(user),
    can_manage_trader_chain: canManageTraderChain(user),
    can_view_margin_analysis: canViewMarginAnalysis(user),
    can_report_farm_data: canReportFarmData(user),
    can_manage_certifications: canManageCertifications(user)
  };
};

/**
 * Check if user should see a specific navigation item
 */
export const shouldShowNavigationItem = (user: User, itemKey: string): boolean => {
  const config = getDashboardConfig(user);
  
  switch (itemKey) {
    case 'purchase-orders':
      return config.can_create_po || config.can_confirm_po;
    case 'incoming-orders':
      return config.can_create_po || config.can_confirm_po;
    case 'outgoing-orders':
      return config.can_create_po || config.can_confirm_po;
    case 'team':
      return config.can_manage_team;
    case 'settings':
      return config.can_manage_settings;
    case 'transparency':
      return config.can_view_analytics;
    case 'audit':
      return config.can_audit_companies;
    case 'regulate':
      return config.can_regulate_platform;
    case 'trader-chain':
      return config.can_manage_trader_chain ?? true;
    case 'margin-analysis':
      return config.can_view_margin_analysis ?? true;
    case 'farm-data':
      return config.can_report_farm_data ?? true;
    case 'certifications':
      return config.can_manage_certifications ?? true;
    default:
      return true; // Show by default if not specified
  }
};

/**
 * Get user-friendly role display name
 */
export const getRoleDisplayName = (role: string): string => {
  switch (role) {
    case UserRole.ADMIN:
      return 'Administrator';
    case UserRole.SUPPLY_CHAIN_MANAGER:
      return 'Supply Chain Manager';
    case UserRole.PRODUCTION_MANAGER:
      return 'Production Manager';
    case UserRole.VIEWER:
      return 'Viewer';
    case UserRole.AUDITOR:
      return 'Auditor';
    default:
      return role;
  }
};

/**
 * Get user-friendly company type display name
 */
export const getCompanyTypeDisplayName = (companyType: string): string => {
  switch (companyType) {
    case CompanyType.BRAND:
      return 'Brand';
    case CompanyType.PROCESSOR:
      return 'Processor';
    case CompanyType.ORIGINATOR:
      return 'Originator';
    case CompanyType.TRADER:
      return 'Trader';
    case CompanyType.AUDITOR:
      return 'Auditor';
    case CompanyType.REGULATOR:
      return 'Regulator';
    default:
      return companyType;
  }
};
