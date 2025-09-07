/**
 * Feature flags for frontend sector system rollout
 */

export enum FeatureFlag {
  ENABLE_SECTOR_SYSTEM = 'ENABLE_SECTOR_SYSTEM',
  ENABLE_DYNAMIC_FORMS = 'ENABLE_DYNAMIC_FORMS',
  ENABLE_TIER_PERMISSIONS = 'ENABLE_TIER_PERMISSIONS',
  ENABLE_SECTOR_MIGRATION = 'ENABLE_SECTOR_MIGRATION',
  ENABLE_SECTOR_PRODUCTS = 'ENABLE_SECTOR_PRODUCTS',
}

class FeatureFlagManager {
  private flags: Record<string, boolean> = {};

  constructor() {
    this.loadFlags();
  }

  private loadFlags() {
    // Default values for feature flags
    const defaults: Record<FeatureFlag, boolean> = {
      [FeatureFlag.ENABLE_SECTOR_SYSTEM]: false,
      [FeatureFlag.ENABLE_DYNAMIC_FORMS]: false,
      [FeatureFlag.ENABLE_TIER_PERMISSIONS]: false,
      [FeatureFlag.ENABLE_SECTOR_MIGRATION]: true,
      [FeatureFlag.ENABLE_SECTOR_PRODUCTS]: false,
    };

    // Load from environment variables (if available)
    Object.entries(defaults).forEach(([flag, defaultValue]) => {
      const envValue = process.env[`REACT_APP_${flag}`];
      if (envValue !== undefined) {
        this.flags[flag] = envValue.toLowerCase() === 'true';
      } else {
        this.flags[flag] = defaultValue;
      }
    });
  }

  isEnabled(flag: FeatureFlag): boolean {
    return this.flags[flag] || false;
  }

  enable(flag: FeatureFlag): void {
    this.flags[flag] = true;
  }

  disable(flag: FeatureFlag): void {
    this.flags[flag] = false;
  }

  getAllFlags(): Record<string, boolean> {
    return { ...this.flags };
  }
}

// Global feature flag manager instance
export const featureFlags = new FeatureFlagManager();

// Convenience functions
export const isSectorSystemEnabled = (): boolean => 
  featureFlags.isEnabled(FeatureFlag.ENABLE_SECTOR_SYSTEM);

export const isDynamicFormsEnabled = (): boolean => 
  featureFlags.isEnabled(FeatureFlag.ENABLE_DYNAMIC_FORMS);

export const isTierPermissionsEnabled = (): boolean => 
  featureFlags.isEnabled(FeatureFlag.ENABLE_TIER_PERMISSIONS);

export const isSectorMigrationEnabled = (): boolean => 
  featureFlags.isEnabled(FeatureFlag.ENABLE_SECTOR_MIGRATION);

export const isSectorProductsEnabled = (): boolean => 
  featureFlags.isEnabled(FeatureFlag.ENABLE_SECTOR_PRODUCTS);

// Rollout configuration
export const ROLLOUT_CONFIG = {
  phases: [
    {
      name: 'Phase 1: Infrastructure',
      flags: [FeatureFlag.ENABLE_SECTOR_MIGRATION],
      description: 'Enable database migration and basic sector models'
    },
    {
      name: 'Phase 2: Basic Sector System',
      flags: [FeatureFlag.ENABLE_SECTOR_SYSTEM],
      description: 'Enable sector selection and tier display'
    },
    {
      name: 'Phase 3: Dynamic Forms',
      flags: [FeatureFlag.ENABLE_DYNAMIC_FORMS],
      description: 'Enable sector-specific form generation'
    },
    {
      name: 'Phase 4: Tier Permissions',
      flags: [FeatureFlag.ENABLE_TIER_PERMISSIONS],
      description: 'Enable tier-based permission system'
    },
    {
      name: 'Phase 5: Sector Products',
      flags: [FeatureFlag.ENABLE_SECTOR_PRODUCTS],
      description: 'Enable sector-specific product catalogs'
    }
  ]
};

export const getCurrentRolloutPhase = () => {
  const enabledFlags = Object.values(FeatureFlag).filter(flag => 
    featureFlags.isEnabled(flag)
  );

  let currentPhase = null;
  for (const phase of ROLLOUT_CONFIG.phases) {
    if (phase.flags.every(flag => featureFlags.isEnabled(flag))) {
      currentPhase = phase;
    }
  }

  return {
    currentPhase,
    enabledFlags,
    totalPhases: ROLLOUT_CONFIG.phases.length
  };
};
