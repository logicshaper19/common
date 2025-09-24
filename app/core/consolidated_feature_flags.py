"""
Consolidated Feature Flag Service for Phase 5 Performance Optimization
Simplified feature flag management with minimal conditional logic.
"""
import os
from typing import Dict, Any
from enum import Enum

from app.core.logging import get_logger

logger = get_logger(__name__)


class ConsolidatedFeatureFlag(str, Enum):
    """Consolidated feature flags - reduced from 7 to 3 flags."""
    
    # Core V2 features
    V2_FEATURES_ENABLED = "V2_FEATURES_ENABLED"
    
    # Company dashboard features (covers brand, processor, originator, trader)
    V2_COMPANY_DASHBOARDS = "V2_COMPANY_DASHBOARDS"
    
    # Admin features
    V2_ADMIN_FEATURES = "V2_ADMIN_FEATURES"


class ConsolidatedFeatureFlagService:
    """Simplified feature flag management with minimal conditional logic."""
    
    def __init__(self):
        # Cache flag values to avoid repeated env lookups
        self.v2_enabled = self._get_bool_flag(ConsolidatedFeatureFlag.V2_FEATURES_ENABLED)
        self.company_dashboards = self._get_bool_flag(ConsolidatedFeatureFlag.V2_COMPANY_DASHBOARDS)
        self.admin_features = self._get_bool_flag(ConsolidatedFeatureFlag.V2_ADMIN_FEATURES)
        
        logger.info(f"Feature flags initialized: V2={self.v2_enabled}, Company={self.company_dashboards}, Admin={self.admin_features}")
    
    def is_v2_enabled_for_user(self, user_role: str, company_type: str) -> bool:
        """Single method to check V2 feature availability."""
        if not self.v2_enabled:
            return False
        
        # Simple logic - no complex conditionals
        if user_role == "platform_admin":
            return self.admin_features
        else:
            return self.company_dashboards
    
    def get_enabled_features(self, user_role: str) -> Dict[str, bool]:
        """Get all enabled features for a user in one call."""
        base_enabled = self.is_v2_enabled_for_user(user_role, "")
        
        return {
            "v2_dashboard": base_enabled,
            "notifications": base_enabled and self.company_dashboards,
            "admin_panel": user_role == "platform_admin" and self.admin_features
        }
    
    def get_legacy_feature_flags(self, user_role: str, company_type: str) -> Dict[str, bool]:
        """
        Get legacy feature flags for backward compatibility.
        Maps the 3 consolidated flags to the original 6 flags.
        """
        v2_enabled = self.is_v2_enabled_for_user(user_role, company_type)
        
        # Map consolidated flags to legacy flags
        legacy_flags = {
            "v2_dashboard_brand": v2_enabled and company_type == "brand",
            "v2_dashboard_processor": v2_enabled and company_type == "processor", 
            "v2_dashboard_originator": v2_enabled and company_type in ["originator", "plantation_grower"],
            "v2_dashboard_trader": v2_enabled and company_type == "trader",
            "v2_dashboard_platform_admin": v2_enabled and user_role == "platform_admin",
            "v2_notification_center": v2_enabled and self.company_dashboards
        }
        
        return legacy_flags
    
    def get_dashboard_config(self, user_role: str, company_type: str) -> Dict[str, Any]:
        """Get complete dashboard configuration based on consolidated flags."""
        v2_enabled = self.is_v2_enabled_for_user(user_role, company_type)
        legacy_flags = self.get_legacy_feature_flags(user_role, company_type)
        
        return {
            "should_use_v2": v2_enabled,
            "dashboard_type": company_type,
            "feature_flags": legacy_flags,
            "user_info": {
                "role": user_role,
                "company_type": company_type
            },
            "consolidated_flags": {
                "v2_features_enabled": self.v2_enabled,
                "company_dashboards": self.company_dashboards,
                "admin_features": self.admin_features
            }
        }
    
    def _get_bool_flag(self, flag_name: str) -> bool:
        """Get boolean flag with caching."""
        return os.getenv(flag_name, "false").lower() == "true"
    
    def refresh_flags(self):
        """Refresh flag values from environment (useful for testing)."""
        self.v2_enabled = self._get_bool_flag(ConsolidatedFeatureFlag.V2_FEATURES_ENABLED)
        self.company_dashboards = self._get_bool_flag(ConsolidatedFeatureFlag.V2_COMPANY_DASHBOARDS)
        self.admin_features = self._get_bool_flag(ConsolidatedFeatureFlag.V2_ADMIN_FEATURES)
        
        logger.info(f"Feature flags refreshed: V2={self.v2_enabled}, Company={self.company_dashboards}, Admin={self.admin_features}")


# Global feature flag service instance
consolidated_feature_flags = ConsolidatedFeatureFlagService()


# Convenience functions for backward compatibility
def is_v2_dashboard_brand_enabled(user_role: str, company_type: str) -> bool:
    """Check if V2 brand dashboard is enabled."""
    return consolidated_feature_flags.get_legacy_feature_flags(user_role, company_type)["v2_dashboard_brand"]


def is_v2_dashboard_processor_enabled(user_role: str, company_type: str) -> bool:
    """Check if V2 processor dashboard is enabled."""
    return consolidated_feature_flags.get_legacy_feature_flags(user_role, company_type)["v2_dashboard_processor"]


def is_v2_dashboard_originator_enabled(user_role: str, company_type: str) -> bool:
    """Check if V2 originator dashboard is enabled."""
    return consolidated_feature_flags.get_legacy_feature_flags(user_role, company_type)["v2_dashboard_originator"]


def is_v2_dashboard_trader_enabled(user_role: str, company_type: str) -> bool:
    """Check if V2 trader dashboard is enabled."""
    return consolidated_feature_flags.get_legacy_feature_flags(user_role, company_type)["v2_dashboard_trader"]


def is_v2_dashboard_platform_admin_enabled(user_role: str, company_type: str) -> bool:
    """Check if V2 platform admin dashboard is enabled."""
    return consolidated_feature_flags.get_legacy_feature_flags(user_role, company_type)["v2_dashboard_platform_admin"]


def is_v2_notification_center_enabled(user_role: str, company_type: str) -> bool:
    """Check if V2 notification center is enabled."""
    return consolidated_feature_flags.get_legacy_feature_flags(user_role, company_type)["v2_notification_center"]
