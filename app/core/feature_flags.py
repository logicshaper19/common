"""
Legacy Feature Flags Module for Backward Compatibility
This module provides backward compatibility for existing code that imports from app.core.feature_flags
"""
from typing import Dict, Any
from app.core.consolidated_feature_flags import consolidated_feature_flags
from app.core.logging import get_logger

logger = get_logger(__name__)


class FeatureFlag:
    """Legacy feature flag enum for backward compatibility."""
    
    # V2 Dashboard flags (mapped to consolidated system)
    V2_DASHBOARD_BRAND = "V2_DASHBOARD_BRAND"
    V2_DASHBOARD_PROCESSOR = "V2_DASHBOARD_PROCESSOR"
    V2_DASHBOARD_ORIGINATOR = "V2_DASHBOARD_ORIGINATOR"
    V2_DASHBOARD_TRADER = "V2_DASHBOARD_TRADER"
    V2_DASHBOARD_PLATFORM_ADMIN = "V2_DASHBOARD_PLATFORM_ADMIN"
    V2_NOTIFICATION_CENTER = "V2_NOTIFICATION_CENTER"
    
    # Amendment feature flags (legacy)
    AMENDMENT_WORKFLOW_ENABLED = "AMENDMENT_WORKFLOW_ENABLED"
    AMENDMENT_APPROVAL_REQUIRED = "AMENDMENT_APPROVAL_REQUIRED"


class FeatureFlagService:
    """Legacy feature flag service for backward compatibility."""
    
    def __init__(self):
        self.flags = {}
        self._load_defaults()
    
    def _load_defaults(self):
        """Load default feature flag values."""
        self.flags = {
            FeatureFlag.V2_DASHBOARD_BRAND: False,
            FeatureFlag.V2_DASHBOARD_PROCESSOR: False,
            FeatureFlag.V2_DASHBOARD_ORIGINATOR: False,
            FeatureFlag.V2_DASHBOARD_TRADER: False,
            FeatureFlag.V2_DASHBOARD_PLATFORM_ADMIN: False,
            FeatureFlag.V2_NOTIFICATION_CENTER: False,
            FeatureFlag.AMENDMENT_WORKFLOW_ENABLED: True,
            FeatureFlag.AMENDMENT_APPROVAL_REQUIRED: True,
        }
    
    def is_enabled(self, flag: str) -> bool:
        """Check if a feature flag is enabled."""
        return self.flags.get(flag, False)
    
    def enable(self, flag: str):
        """Enable a feature flag."""
        self.flags[flag] = True
        logger.info(f"Feature flag enabled: {flag}")
    
    def disable(self, flag: str):
        """Disable a feature flag."""
        self.flags[flag] = False
        logger.info(f"Feature flag disabled: {flag}")
    
    def get_all_flags(self) -> Dict[str, bool]:
        """Get all feature flags."""
        return self.flags.copy()


# Global feature flag service instance
feature_flags = FeatureFlagService()


# Legacy convenience functions for backward compatibility
def is_v2_dashboard_brand_enabled() -> bool:
    """Check if V2 brand dashboard is enabled (legacy function)."""
    return feature_flags.is_enabled(FeatureFlag.V2_DASHBOARD_BRAND)


def is_v2_dashboard_processor_enabled() -> bool:
    """Check if V2 processor dashboard is enabled (legacy function)."""
    return feature_flags.is_enabled(FeatureFlag.V2_DASHBOARD_PROCESSOR)


def is_v2_dashboard_originator_enabled() -> bool:
    """Check if V2 originator dashboard is enabled (legacy function)."""
    return feature_flags.is_enabled(FeatureFlag.V2_DASHBOARD_ORIGINATOR)


def is_v2_dashboard_trader_enabled() -> bool:
    """Check if V2 trader dashboard is enabled (legacy function)."""
    return feature_flags.is_enabled(FeatureFlag.V2_DASHBOARD_TRADER)


def is_v2_dashboard_platform_admin_enabled() -> bool:
    """Check if V2 platform admin dashboard is enabled (legacy function)."""
    return feature_flags.is_enabled(FeatureFlag.V2_DASHBOARD_PLATFORM_ADMIN)


def is_v2_notification_center_enabled() -> bool:
    """Check if V2 notification center is enabled (legacy function)."""
    return feature_flags.is_enabled(FeatureFlag.V2_NOTIFICATION_CENTER)


def get_amendment_feature_flags() -> Dict[str, bool]:
    """Get amendment-related feature flags (legacy function)."""
    return {
        "amendment_workflow_enabled": feature_flags.is_enabled(FeatureFlag.AMENDMENT_WORKFLOW_ENABLED),
        "amendment_approval_required": feature_flags.is_enabled(FeatureFlag.AMENDMENT_APPROVAL_REQUIRED),
    }


def get_v2_dashboard_flags() -> Dict[str, bool]:
    """Get all V2 dashboard feature flags (legacy function)."""
    return {
        "v2_dashboard_brand": is_v2_dashboard_brand_enabled(),
        "v2_dashboard_processor": is_v2_dashboard_processor_enabled(),
        "v2_dashboard_originator": is_v2_dashboard_originator_enabled(),
        "v2_dashboard_trader": is_v2_dashboard_trader_enabled(),
        "v2_dashboard_platform_admin": is_v2_dashboard_platform_admin_enabled(),
        "v2_notification_center": is_v2_notification_center_enabled(),
    }


# Migration helper function
def migrate_to_consolidated_flags():
    """Helper function to migrate from legacy flags to consolidated flags."""
    logger.info("Migrating from legacy feature flags to consolidated system")
    
    # This function can be used to sync legacy flags with consolidated flags
    # For now, we maintain backward compatibility by keeping both systems
    
    # Example migration logic (commented out to avoid breaking existing functionality):
    # if consolidated_feature_flags.v2_enabled:
    #     feature_flags.enable(FeatureFlag.V2_DASHBOARD_BRAND)
    #     feature_flags.enable(FeatureFlag.V2_DASHBOARD_PROCESSOR)
    #     # ... etc
    
    logger.info("Legacy feature flags maintained for backward compatibility")
