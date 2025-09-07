/**
 * TypeScript types for sector-specific tier system
 */

export interface Sector {
  id: string;
  name: string;
  description?: string;
  isActive: boolean;
  regulatoryFocus?: string[];
}

export interface SectorTier {
  id: string;
  sectorId: string;
  level: number;
  name: string;
  description?: string;
  isOriginator: boolean;
  requiredDataFields?: string[];
  permissions?: string[];
}

export interface SectorProduct {
  id: string;
  sectorId: string;
  name: string;
  category?: string;
  hsCode?: string;
  specifications?: Record<string, any>;
  applicableTiers?: number[];
}

export interface SectorConfig {
  sector: Sector;
  tiers: SectorTier[];
  products: SectorProduct[];
}

export interface UserSectorInfo {
  sectorId?: string;
  tierLevel?: number;
  tierName?: string;
  tierPermissions?: string[];
  isOriginator?: boolean;
}

export interface CompanySectorInfo {
  sectorId?: string;
  tierLevel?: number;
  tierName?: string;
}

// Form field types for dynamic forms
export interface FormField {
  name: string;
  label: string;
  type: 'text' | 'number' | 'email' | 'textarea' | 'select' | 'checkbox' | 'date' | 'file' | 'coordinates';
  required: boolean;
  placeholder?: string;
  options?: { value: string; label: string }[];
  validation?: {
    min?: number;
    max?: number;
    pattern?: string;
    message?: string;
  };
  description?: string;
}

export interface OriginDataSchema {
  [tierLevel: number]: FormField[];
}

// Permission types
export type SectorPermission = 
  | 'create_po'
  | 'confirm_po'
  | 'link_inputs'
  | 'add_origin_data'
  | 'manage_suppliers'
  | 'view_transparency'
  | 'provide_processing_data'
  | 'provide_farmer_data'
  | 'confirm_deliveries'
  | 'audit_suppliers'
  | 'provide_social_data'
  | 'manage_cooperatives';

// Sector-specific data types
export interface PalmOilOriginData {
  gpsCoordinates: {
    latitude: number;
    longitude: number;
  };
  rspocertification?: string;
  plantationType: 'own_estate' | 'smallholder' | 'mixed';
  harvestDate: string;
  certificationStatus: string[];
}

export interface ApparelOriginData {
  farmLocation: {
    latitude: number;
    longitude: number;
  };
  bciCertification?: string;
  harvestDate: string;
  cottonGrade: string;
  organicCertification?: string;
}

export interface ElectronicsOriginData {
  mineSiteLocation: {
    latitude: number;
    longitude: number;
  };
  conflictFreeCertification: string;
  smelterIds: string[];
  ownershipStructure: string;
  extractionMethod: string;
}

// Union type for all origin data types
export type OriginData = PalmOilOriginData | ApparelOriginData | ElectronicsOriginData;

// Sector template definitions
export interface SectorTemplate {
  sector: Sector;
  tiers: Omit<SectorTier, 'id'>[];
  products: Omit<SectorProduct, 'id'>[];
  originDataSchema: OriginDataSchema;
}

// API response types
export interface SectorListResponse {
  sectors: Sector[];
  total: number;
}

export interface SectorConfigResponse {
  config: SectorConfig;
}

// Migration types for backward compatibility
export interface LegacyRoleMapping {
  [legacyRole: string]: {
    sectorId: string;
    tierLevel: number;
  };
}

export const DEFAULT_ROLE_MAPPING: LegacyRoleMapping = {
  'buyer': { sectorId: 'palm_oil', tierLevel: 1 },
  'supplier': { sectorId: 'palm_oil', tierLevel: 4 },
  'seller': { sectorId: 'palm_oil', tierLevel: 2 },
  'admin': { sectorId: 'palm_oil', tierLevel: 0 } // Special case for admin
};

// Feature flag types
export interface SectorFeatureFlags {
  ENABLE_SECTOR_SYSTEM: boolean;
  ENABLE_DYNAMIC_FORMS: boolean;
  ENABLE_TIER_PERMISSIONS: boolean;
  ENABLE_SECTOR_MIGRATION: boolean;
}
