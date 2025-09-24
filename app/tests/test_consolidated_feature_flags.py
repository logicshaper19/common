"""
Dedicated tests for consolidated feature flags system
Tests backward compatibility and performance improvements
"""
import pytest
import os
from unittest.mock import patch
from app.core.consolidated_feature_flags import (
    ConsolidatedFeatureFlagService,
    consolidated_feature_flags,
    ConsolidatedFeatureFlag,
    is_v2_dashboard_brand_enabled,
    is_v2_dashboard_processor_enabled,
    is_v2_dashboard_originator_enabled,
    is_v2_dashboard_trader_enabled,
    is_v2_dashboard_platform_admin_enabled,
    is_v2_notification_center_enabled
)


class TestConsolidatedFeatureFlagService:
    """Test the consolidated feature flag service."""
    
    def setup_method(self):
        """Setup for each test method."""
        self.service = ConsolidatedFeatureFlagService()
    
    def test_consolidated_flags_enum(self):
        """Test that consolidated feature flag enum is properly defined."""
        assert hasattr(ConsolidatedFeatureFlag, 'V2_FEATURES_ENABLED')
        assert hasattr(ConsolidatedFeatureFlag, 'V2_COMPANY_DASHBOARDS')
        assert hasattr(ConsolidatedFeatureFlag, 'V2_ADMIN_FEATURES')
        
        # Test enum values
        assert ConsolidatedFeatureFlag.V2_FEATURES_ENABLED == "V2_FEATURES_ENABLED"
        assert ConsolidatedFeatureFlag.V2_COMPANY_DASHBOARDS == "V2_COMPANY_DASHBOARDS"
        assert ConsolidatedFeatureFlag.V2_ADMIN_FEATURES == "V2_ADMIN_FEATURES"
    
    def test_initialization_with_env_vars(self):
        """Test service initialization with environment variables."""
        with patch.dict(os.environ, {
            'V2_FEATURES_ENABLED': 'true',
            'V2_COMPANY_DASHBOARDS': 'false',
            'V2_ADMIN_FEATURES': 'true'
        }):
            service = ConsolidatedFeatureFlagService()
            assert service.v2_enabled is True
            assert service.company_dashboards is False
            assert service.admin_features is True
    
    def test_initialization_with_defaults(self):
        """Test service initialization with default values."""
        with patch.dict(os.environ, {}, clear=True):
            service = ConsolidatedFeatureFlagService()
            assert service.v2_enabled is False
            assert service.company_dashboards is False
            assert service.admin_features is False
    
    def test_v2_enabled_for_user_platform_admin(self):
        """Test V2 enabled check for platform admin users."""
        # Platform admin should use admin_features flag
        result = self.service.is_v2_enabled_for_user("platform_admin", "brand")
        assert result == self.service.admin_features
    
    def test_v2_enabled_for_user_regular_user(self):
        """Test V2 enabled check for regular users."""
        # Regular users should use company_dashboards flag
        result = self.service.is_v2_enabled_for_user("user", "brand")
        assert result == self.service.company_dashboards
    
    def test_v2_enabled_for_user_v2_disabled(self):
        """Test V2 enabled check when V2 features are disabled."""
        # Mock v2_enabled as False
        self.service.v2_enabled = False
        
        result = self.service.is_v2_enabled_for_user("platform_admin", "brand")
        assert result is False
        
        result = self.service.is_v2_enabled_for_user("user", "brand")
        assert result is False
    
    def test_get_enabled_features_platform_admin(self):
        """Test getting enabled features for platform admin."""
        features = self.service.get_enabled_features("platform_admin")
        
        assert "v2_dashboard" in features
        assert "notifications" in features
        assert "admin_panel" in features
        
        # Admin panel should be enabled if admin_features is True
        if self.service.admin_features:
            assert features["admin_panel"] is True
        else:
            assert features["admin_panel"] is False
    
    def test_get_enabled_features_regular_user(self):
        """Test getting enabled features for regular user."""
        features = self.service.get_enabled_features("user")
        
        assert "v2_dashboard" in features
        assert "notifications" in features
        assert "admin_panel" in features
        
        # Regular users should not have admin panel
        assert features["admin_panel"] is False
    
    def test_legacy_feature_flags_mapping_brand_user(self):
        """Test legacy feature flags mapping for brand user."""
        legacy_flags = self.service.get_legacy_feature_flags("user", "brand")
        
        # Brand user should have brand dashboard enabled if company dashboards are enabled
        if self.service.company_dashboards:
            assert legacy_flags["v2_dashboard_brand"] is True
        else:
            assert legacy_flags["v2_dashboard_brand"] is False
        
        # Other company types should be False
        assert legacy_flags["v2_dashboard_processor"] is False
        assert legacy_flags["v2_dashboard_originator"] is False
        assert legacy_flags["v2_dashboard_trader"] is False
        
        # Platform admin should be False for regular user
        assert legacy_flags["v2_dashboard_platform_admin"] is False
        
        # Notification center should match company dashboards
        assert legacy_flags["v2_notification_center"] == self.service.company_dashboards
    
    def test_legacy_feature_flags_mapping_processor_user(self):
        """Test legacy feature flags mapping for processor user."""
        legacy_flags = self.service.get_legacy_feature_flags("user", "processor")
        
        # Processor user should have processor dashboard enabled if company dashboards are enabled
        if self.service.company_dashboards:
            assert legacy_flags["v2_dashboard_processor"] is True
        else:
            assert legacy_flags["v2_dashboard_processor"] is False
        
        # Other company types should be False
        assert legacy_flags["v2_dashboard_brand"] is False
        assert legacy_flags["v2_dashboard_originator"] is False
        assert legacy_flags["v2_dashboard_trader"] is False
    
    def test_legacy_feature_flags_mapping_platform_admin(self):
        """Test legacy feature flags mapping for platform admin."""
        legacy_flags = self.service.get_legacy_feature_flags("platform_admin", "brand")
        
        # Platform admin should have platform admin dashboard enabled if admin features are enabled
        if self.service.admin_features:
            assert legacy_flags["v2_dashboard_platform_admin"] is True
        else:
            assert legacy_flags["v2_dashboard_platform_admin"] is False
        
        # Company-specific dashboards should be False for platform admin
        assert legacy_flags["v2_dashboard_brand"] is False
        assert legacy_flags["v2_dashboard_processor"] is False
        assert legacy_flags["v2_dashboard_originator"] is False
        assert legacy_flags["v2_dashboard_trader"] is False
    
    def test_dashboard_config_structure(self):
        """Test dashboard configuration structure."""
        config = self.service.get_dashboard_config("user", "brand")
        
        # Required top-level keys
        assert "should_use_v2" in config
        assert "dashboard_type" in config
        assert "feature_flags" in config
        assert "user_info" in config
        assert "consolidated_flags" in config
        
        # Dashboard type should match company type
        assert config["dashboard_type"] == "brand"
        
        # User info should contain role and company type
        user_info = config["user_info"]
        assert user_info["role"] == "user"
        assert user_info["company_type"] == "brand"
        
        # Consolidated flags should contain all three flags
        consolidated_flags = config["consolidated_flags"]
        assert "v2_features_enabled" in consolidated_flags
        assert "company_dashboards" in consolidated_flags
        assert "admin_features" in consolidated_flags
    
    def test_refresh_flags(self):
        """Test feature flag refresh functionality."""
        original_v2_enabled = self.service.v2_enabled
        original_company_dashboards = self.service.company_dashboards
        original_admin_features = self.service.admin_features
        
        # Refresh should not change values unless env vars change
        self.service.refresh_flags()
        
        assert self.service.v2_enabled == original_v2_enabled
        assert self.service.company_dashboards == original_company_dashboards
        assert self.service.admin_features == original_admin_features
    
    def test_refresh_flags_with_env_change(self):
        """Test feature flag refresh with environment variable changes."""
        with patch.dict(os.environ, {
            'V2_FEATURES_ENABLED': 'true',
            'V2_COMPANY_DASHBOARDS': 'true',
            'V2_ADMIN_FEATURES': 'false'
        }):
            self.service.refresh_flags()
            
            assert self.service.v2_enabled is True
            assert self.service.company_dashboards is True
            assert self.service.admin_features is False


class TestBackwardCompatibility:
    """Test backward compatibility functions."""
    
    def test_is_v2_dashboard_brand_enabled(self):
        """Test backward compatibility function for brand dashboard."""
        result = is_v2_dashboard_brand_enabled("user", "brand")
        
        # Should return True if company dashboards are enabled
        expected = consolidated_feature_flags.company_dashboards
        assert result == expected
    
    def test_is_v2_dashboard_processor_enabled(self):
        """Test backward compatibility function for processor dashboard."""
        result = is_v2_dashboard_processor_enabled("user", "processor")
        
        # Should return True if company dashboards are enabled
        expected = consolidated_feature_flags.company_dashboards
        assert result == expected
    
    def test_is_v2_dashboard_originator_enabled(self):
        """Test backward compatibility function for originator dashboard."""
        result = is_v2_dashboard_originator_enabled("user", "originator")
        
        # Should return True if company dashboards are enabled
        expected = consolidated_feature_flags.company_dashboards
        assert result == expected
    
    def test_is_v2_dashboard_trader_enabled(self):
        """Test backward compatibility function for trader dashboard."""
        result = is_v2_dashboard_trader_enabled("user", "trader")
        
        # Should return True if company dashboards are enabled
        expected = consolidated_feature_flags.company_dashboards
        assert result == expected
    
    def test_is_v2_dashboard_platform_admin_enabled(self):
        """Test backward compatibility function for platform admin dashboard."""
        result = is_v2_dashboard_platform_admin_enabled("platform_admin", "brand")
        
        # Should return True if admin features are enabled
        expected = consolidated_feature_flags.admin_features
        assert result == expected
    
    def test_is_v2_notification_center_enabled(self):
        """Test backward compatibility function for notification center."""
        result = is_v2_notification_center_enabled("user", "brand")
        
        # Should return True if company dashboards are enabled
        expected = consolidated_feature_flags.company_dashboards
        assert result == expected


class TestGlobalInstance:
    """Test the global consolidated feature flags instance."""
    
    def test_global_instance_exists(self):
        """Test that global instance exists and is properly configured."""
        assert consolidated_feature_flags is not None
        assert isinstance(consolidated_feature_flags, ConsolidatedFeatureFlagService)
    
    def test_global_instance_consistency(self):
        """Test that global instance maintains consistency."""
        # Test that global instance methods work
        result = consolidated_feature_flags.is_v2_enabled_for_user("user", "brand")
        assert isinstance(result, bool)
        
        features = consolidated_feature_flags.get_enabled_features("user")
        assert isinstance(features, dict)
        
        legacy_flags = consolidated_feature_flags.get_legacy_feature_flags("user", "brand")
        assert isinstance(legacy_flags, dict)
        
        config = consolidated_feature_flags.get_dashboard_config("user", "brand")
        assert isinstance(config, dict)


class TestPerformance:
    """Performance tests for consolidated feature flags."""
    
    def test_feature_flag_evaluation_speed(self):
        """Test that feature flag evaluation is fast."""
        import time
        
        start_time = time.time()
        
        # Evaluate feature flags multiple times
        for _ in range(1000):
            consolidated_feature_flags.is_v2_enabled_for_user("user", "brand")
            consolidated_feature_flags.get_legacy_feature_flags("user", "brand")
            consolidated_feature_flags.get_enabled_features("user")
        
        end_time = time.time()
        
        # Should be very fast (under 10ms for 3000 evaluations)
        assert (end_time - start_time) < 0.01
    
    def test_consolidated_vs_individual_flags(self):
        """Test that consolidated approach is more efficient than individual flags."""
        import time
        
        # Test consolidated approach
        start_time = time.time()
        for _ in range(1000):
            consolidated_feature_flags.is_v2_enabled_for_user("user", "brand")
        consolidated_time = time.time() - start_time
        
        # Test individual flag approach (simulated)
        start_time = time.time()
        for _ in range(1000):
            # Simulate checking multiple individual flags
            v2_enabled = consolidated_feature_flags.v2_enabled
            company_dashboards = consolidated_feature_flags.company_dashboards
            admin_features = consolidated_feature_flags.admin_features
            # Additional logic to determine which flags to check
            if "user" == "platform_admin":
                result = admin_features
            else:
                result = company_dashboards
        individual_time = time.time() - start_time
        
        # Consolidated approach should be faster or at least not significantly slower
        # (The difference might be minimal in this simple test, but consolidated approach
        # is more maintainable and reduces complexity)
        assert consolidated_time <= individual_time * 1.1  # Allow 10% tolerance


class TestEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_invalid_user_role(self):
        """Test behavior with invalid user role."""
        # Should handle gracefully
        result = consolidated_feature_flags.is_v2_enabled_for_user("invalid_role", "brand")
        assert isinstance(result, bool)
    
    def test_invalid_company_type(self):
        """Test behavior with invalid company type."""
        # Should handle gracefully
        result = consolidated_feature_flags.is_v2_enabled_for_user("user", "invalid_type")
        assert isinstance(result, bool)
    
    def test_none_values(self):
        """Test behavior with None values."""
        # Should handle gracefully
        result = consolidated_feature_flags.is_v2_enabled_for_user(None, None)
        assert isinstance(result, bool)
    
    def test_empty_strings(self):
        """Test behavior with empty strings."""
        # Should handle gracefully
        result = consolidated_feature_flags.is_v2_enabled_for_user("", "")
        assert isinstance(result, bool)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
