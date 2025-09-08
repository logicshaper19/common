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

    # Amendment system feature flags
    ENABLE_PHASE_1_AMENDMENTS = "ENABLE_PHASE_1_AMENDMENTS"
    ENABLE_PHASE_2_ERP_AMENDMENTS = "ENABLE_PHASE_2_ERP_AMENDMENTS"
    ENABLE_AMENDMENT_NOTIFICATIONS = "ENABLE_AMENDMENT_NOTIFICATIONS"
    ENABLE_AMENDMENT_AUDIT = "ENABLE_AMENDMENT_AUDIT"


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

            # Amendment system defaults
            FeatureFlag.ENABLE_PHASE_1_AMENDMENTS.value: True,  # Phase 1 enabled by default
            FeatureFlag.ENABLE_PHASE_2_ERP_AMENDMENTS.value: False,  # Phase 2 disabled by default
            FeatureFlag.ENABLE_AMENDMENT_NOTIFICATIONS.value: True,
            FeatureFlag.ENABLE_AMENDMENT_AUDIT.value: True,
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


# Amendment system feature flag functions
def is_phase_1_amendments_enabled() -> bool:
    """Check if Phase 1 MVP amendments are enabled"""
    return feature_flags.is_enabled(FeatureFlag.ENABLE_PHASE_1_AMENDMENTS)


def is_phase_2_erp_amendments_enabled() -> bool:
    """Check if Phase 2 ERP amendments are enabled"""
    return feature_flags.is_enabled(FeatureFlag.ENABLE_PHASE_2_ERP_AMENDMENTS)


def is_amendment_notifications_enabled() -> bool:
    """Check if amendment notifications are enabled"""
    return feature_flags.is_enabled(FeatureFlag.ENABLE_AMENDMENT_NOTIFICATIONS)


def is_amendment_audit_enabled() -> bool:
    """Check if amendment audit logging is enabled"""
    return feature_flags.is_enabled(FeatureFlag.ENABLE_AMENDMENT_AUDIT)


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


# Amendment-specific feature flag manager
class AmendmentFeatureFlags:
    """
    Amendment-specific feature flag manager.

    This class provides amendment-specific feature flag logic,
    including company-level and global controls.
    """

    def __init__(self, db_session=None):
        self.db = db_session

    def get_amendment_phase_for_company(self, company_id) -> str:
        """
        Determine which amendment phase is enabled for a company.

        Args:
            company_id: Company UUID or string

        Returns:
            'phase_1_mvp' or 'phase_2_erp'
        """
        # Global check first
        if not is_phase_2_erp_amendments_enabled():
            return "phase_1_mvp"

        # If we have a database session, check company-specific settings
        if self.db and company_id:
            try:
                from app.models.company import Company
                from uuid import UUID

                if isinstance(company_id, str):
                    company_id = UUID(company_id)

                company = self.db.query(Company).filter(Company.id == company_id).first()

                if company and company.erp_integration_enabled and company.erp_sync_enabled:
                    return "phase_2_erp"
            except Exception:
                # Fall back to Phase 1 on any error
                pass

        return "phase_1_mvp"

    def is_phase_1_for_company(self, company_id) -> bool:
        """Check if company should use Phase 1 amendments."""
        return self.get_amendment_phase_for_company(company_id) == "phase_1_mvp"

    def is_phase_2_for_company(self, company_id) -> bool:
        """Check if company should use Phase 2 amendments."""
        return self.get_amendment_phase_for_company(company_id) == "phase_2_erp"

    def should_send_notifications(self) -> bool:
        """Check if amendment notifications should be sent."""
        return is_amendment_notifications_enabled()

    def should_audit_amendments(self) -> bool:
        """Check if amendment actions should be audited."""
        return is_amendment_audit_enabled()

    def get_amendment_config(self, company_id=None) -> Dict[str, Any]:
        """
        Get complete amendment configuration.

        Args:
            company_id: Optional company ID for company-specific settings

        Returns:
            Amendment configuration dictionary
        """
        phase = self.get_amendment_phase_for_company(company_id) if company_id else "phase_1_mvp"

        return {
            "phase": phase,
            "is_phase_1": phase == "phase_1_mvp",
            "is_phase_2": phase == "phase_2_erp",
            "notifications_enabled": self.should_send_notifications(),
            "audit_enabled": self.should_audit_amendments(),
            "global_phase_1_enabled": is_phase_1_amendments_enabled(),
            "global_phase_2_enabled": is_phase_2_erp_amendments_enabled()
        }


# Global amendment feature flag instance
def get_amendment_feature_flags(db_session=None) -> AmendmentFeatureFlags:
    """Get amendment feature flags instance."""
    return AmendmentFeatureFlags(db_session)
