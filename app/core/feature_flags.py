"""
Feature flags for gradual rollout of sector system
"""
import os
from typing import Dict, Any
from enum import Enum


class FeatureFlag(Enum):
    """Available feature flags"""
    ENABLE_SECTOR_SYSTEM = "ENABLE_SECTOR_SYSTEM"
    ENABLE_DYNAMIC_FORMS = "ENABLE_DYNAMIC_FORMS"
    ENABLE_TIER_PERMISSIONS = "ENABLE_TIER_PERMISSIONS"
    ENABLE_SECTOR_MIGRATION = "ENABLE_SECTOR_MIGRATION"
    ENABLE_SECTOR_PRODUCTS = "ENABLE_SECTOR_PRODUCTS"


class FeatureFlagManager:
    """Manages feature flags for the application"""
    
    def __init__(self):
        self._flags: Dict[str, bool] = {}
        self._load_flags()
    
    def _load_flags(self):
        """Load feature flags from environment variables"""
        # Default values for feature flags
        defaults = {
            FeatureFlag.ENABLE_SECTOR_SYSTEM.value: False,
            FeatureFlag.ENABLE_DYNAMIC_FORMS.value: False,
            FeatureFlag.ENABLE_TIER_PERMISSIONS.value: False,
            FeatureFlag.ENABLE_SECTOR_MIGRATION.value: True,  # Enable migration by default
            FeatureFlag.ENABLE_SECTOR_PRODUCTS.value: False,
        }
        
        # Load from environment with defaults
        for flag, default in defaults.items():
            env_value = os.getenv(flag, str(default)).lower()
            self._flags[flag] = env_value in ('true', '1', 'yes', 'on')
    
    def is_enabled(self, flag: FeatureFlag) -> bool:
        """Check if a feature flag is enabled"""
        return self._flags.get(flag.value, False)
    
    def enable(self, flag: FeatureFlag):
        """Enable a feature flag (for testing)"""
        self._flags[flag.value] = True
    
    def disable(self, flag: FeatureFlag):
        """Disable a feature flag (for testing)"""
        self._flags[flag.value] = False
    
    def get_all_flags(self) -> Dict[str, bool]:
        """Get all feature flags and their states"""
        return self._flags.copy()


# Global feature flag manager instance
feature_flags = FeatureFlagManager()


def is_sector_system_enabled() -> bool:
    """Check if the sector system is enabled"""
    return feature_flags.is_enabled(FeatureFlag.ENABLE_SECTOR_SYSTEM)


def is_dynamic_forms_enabled() -> bool:
    """Check if dynamic forms are enabled"""
    return feature_flags.is_enabled(FeatureFlag.ENABLE_DYNAMIC_FORMS)


def is_tier_permissions_enabled() -> bool:
    """Check if tier-based permissions are enabled"""
    return feature_flags.is_enabled(FeatureFlag.ENABLE_TIER_PERMISSIONS)


def is_sector_migration_enabled() -> bool:
    """Check if sector migration is enabled"""
    return feature_flags.is_enabled(FeatureFlag.ENABLE_SECTOR_MIGRATION)


def is_sector_products_enabled() -> bool:
    """Check if sector-specific products are enabled"""
    return feature_flags.is_enabled(FeatureFlag.ENABLE_SECTOR_PRODUCTS)


# Utility functions for backward compatibility
def get_user_role_or_tier(user) -> str:
    """Get user role or tier name for backward compatibility"""
    if is_sector_system_enabled() and user.sector_id and user.tier_level:
        # Return tier-based role
        from app.services.sector_service import SectorService
        # This would need a database session - simplified for now
        return f"tier_{user.tier_level}"
    else:
        # Return legacy role
        return user.role


def get_user_permissions(user) -> list:
    """Get user permissions based on role or tier"""
    if is_tier_permissions_enabled() and user.sector_id and user.tier_level:
        # Return tier-based permissions
        from app.services.sector_service import SectorService
        # This would need a database session - simplified for now
        return []  # Would fetch from tier configuration
    else:
        # Return legacy role-based permissions
        legacy_permissions = {
            'admin': ['all'],
            'buyer': ['create_po', 'view_transparency'],
            'seller': ['confirm_po', 'provide_data'],
            'supplier': ['confirm_po', 'add_origin_data']
        }
        return legacy_permissions.get(user.role, [])


# Configuration for gradual rollout
ROLLOUT_CONFIG = {
    "phases": [
        {
            "name": "Phase 1: Infrastructure",
            "flags": [FeatureFlag.ENABLE_SECTOR_MIGRATION],
            "description": "Enable database migration and basic sector models"
        },
        {
            "name": "Phase 2: Basic Sector System",
            "flags": [FeatureFlag.ENABLE_SECTOR_SYSTEM],
            "description": "Enable sector selection and tier display"
        },
        {
            "name": "Phase 3: Dynamic Forms",
            "flags": [FeatureFlag.ENABLE_DYNAMIC_FORMS],
            "description": "Enable sector-specific form generation"
        },
        {
            "name": "Phase 4: Tier Permissions",
            "flags": [FeatureFlag.ENABLE_TIER_PERMISSIONS],
            "description": "Enable tier-based permission system"
        },
        {
            "name": "Phase 5: Sector Products",
            "flags": [FeatureFlag.ENABLE_SECTOR_PRODUCTS],
            "description": "Enable sector-specific product catalogs"
        }
    ]
}


def get_current_rollout_phase() -> Dict[str, Any]:
    """Get the current rollout phase based on enabled flags"""
    enabled_flags = [flag for flag in FeatureFlag if feature_flags.is_enabled(flag)]
    
    current_phase = None
    for phase in ROLLOUT_CONFIG["phases"]:
        phase_flags = phase["flags"]
        if all(feature_flags.is_enabled(flag) for flag in phase_flags):
            current_phase = phase
    
    return {
        "current_phase": current_phase,
        "enabled_flags": [flag.value for flag in enabled_flags],
        "total_phases": len(ROLLOUT_CONFIG["phases"])
    }
