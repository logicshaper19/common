"""
Tests for Dashboard V2 Foundation (Phase 0)
Tests feature flags, permissions, and basic API endpoints
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.core.feature_flags import (
    feature_flags,
    FeatureFlag,
    is_v2_dashboard_brand_enabled,
    is_v2_dashboard_processor_enabled,
    is_v2_dashboard_originator_enabled,
    is_v2_dashboard_trader_enabled,
    is_v2_dashboard_platform_admin_enabled,
    is_v2_notification_center_enabled
)
from app.services.permissions import PermissionService
from app.models.user import User
from app.models.company import Company


class TestFeatureFlags:
    """Test feature flag system for dashboard v2"""
    
    def test_dashboard_v2_flags_exist(self):
        """Test that all dashboard v2 feature flags are defined"""
        assert hasattr(FeatureFlag, 'V2_DASHBOARD_BRAND')
        assert hasattr(FeatureFlag, 'V2_DASHBOARD_PROCESSOR')
        assert hasattr(FeatureFlag, 'V2_DASHBOARD_ORIGINATOR')
        assert hasattr(FeatureFlag, 'V2_DASHBOARD_TRADER')
        assert hasattr(FeatureFlag, 'V2_DASHBOARD_PLATFORM_ADMIN')
        assert hasattr(FeatureFlag, 'V2_NOTIFICATION_CENTER')
    
    def test_dashboard_v2_flags_disabled_by_default(self):
        """Test that dashboard v2 flags are disabled by default"""
        assert not is_v2_dashboard_brand_enabled()
        assert not is_v2_dashboard_processor_enabled()
        assert not is_v2_dashboard_originator_enabled()
        assert not is_v2_dashboard_trader_enabled()
        assert not is_v2_dashboard_platform_admin_enabled()
        assert not is_v2_notification_center_enabled()
    
    def test_can_enable_dashboard_v2_flags(self):
        """Test that dashboard v2 flags can be enabled"""
        # Enable brand dashboard flag
        feature_flags.enable(FeatureFlag.V2_DASHBOARD_BRAND)
        assert is_v2_dashboard_brand_enabled()
        
        # Disable it again
        feature_flags.disable(FeatureFlag.V2_DASHBOARD_BRAND)
        assert not is_v2_dashboard_brand_enabled()


class TestPermissionService:
    """Test enhanced permission service"""
    
    def test_get_dashboard_type_brand(self, sample_brand_user):
        """Test dashboard type detection for brand users"""
        permission_service = PermissionService(None)  # No DB needed for this test
        dashboard_type = permission_service.get_dashboard_type(sample_brand_user)
        assert dashboard_type == "brand"
    
    def test_get_dashboard_type_processor(self, sample_processor_user):
        """Test dashboard type detection for processor users"""
        permission_service = PermissionService(None)
        dashboard_type = permission_service.get_dashboard_type(sample_processor_user)
        assert dashboard_type == "processor"
    
    def test_get_dashboard_type_platform_admin(self, sample_super_admin_user):
        """Test dashboard type detection for platform admin users"""
        permission_service = PermissionService(None)
        dashboard_type = permission_service.get_dashboard_type(sample_super_admin_user)
        assert dashboard_type == "platform_admin"
    
    def test_dashboard_config_includes_dashboard_type(self, sample_brand_user):
        """Test that dashboard config includes dashboard type"""
        permission_service = PermissionService(None)
        config = permission_service.get_user_dashboard_config(sample_brand_user)
        
        assert "dashboard_type" in config
        assert config["dashboard_type"] == "brand"


class TestDashboardV2API:
    """Test Dashboard V2 API endpoints"""

    def test_feature_flags_endpoint_requires_auth(self, client):
        """Test that feature flags endpoint requires authentication"""
        response = client.get("/api/dashboard-v2/feature-flags")
        assert response.status_code == 401

    def test_dashboard_config_endpoint_requires_auth(self, client):
        """Test that dashboard config endpoint requires authentication"""
        response = client.get("/api/dashboard-v2/config")
        assert response.status_code == 401

    def test_feature_flags_endpoint_with_auth(self, brand_user_client):
        """Test feature flags endpoint with authentication"""
        response = brand_user_client.get("/api/dashboard-v2/feature-flags")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, dict)
        assert "v2_dashboard_brand" in data
        assert "v2_dashboard_processor" in data
        assert "v2_dashboard_originator" in data
        assert "v2_dashboard_trader" in data
        assert "v2_dashboard_platform_admin" in data
        assert "v2_notification_center" in data

    def test_dashboard_config_endpoint_with_auth(self, brand_user_client):
        """Test dashboard config endpoint with authentication"""
        response = brand_user_client.get("/api/dashboard-v2/config")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, dict)
        assert "dashboard_type" in data
        assert "should_use_v2" in data
        assert "feature_flags" in data
        assert "user_info" in data

        # Check user info structure
        user_info = data["user_info"]
        assert "id" in user_info
        assert "role" in user_info
        assert "company_type" in user_info
        assert "company_name" in user_info


class TestDashboardV2Metrics:
    """Test dashboard metrics endpoints"""

    def test_brand_dashboard_metrics_structure(self, brand_user_client):
        """Test brand dashboard metrics endpoint structure"""
        response = brand_user_client.get("/api/v2/dashboard/metrics/brand")
        assert response.status_code == 200

        data = response.json()
        assert "supply_chain_overview" in data
        assert "supplier_portfolio" in data
        assert "recent_activity" in data

    def test_processor_dashboard_metrics_structure(self, processor_user_client):
        """Test processor dashboard metrics endpoint structure"""
        response = processor_user_client.get("/api/v2/dashboard/metrics/processor")
        assert response.status_code == 200

        data = response.json()
        assert "incoming_pos" in data
        assert "production_overview" in data
        assert "recent_activity" in data

    def test_platform_admin_metrics_structure(self, admin_user_client):
        """Test platform admin dashboard metrics"""
        response = admin_user_client.get("/api/v2/dashboard/metrics/platform-admin")
        assert response.status_code == 200

        data = response.json()
        assert "platform_overview" in data
        assert "system_health" in data
        assert "recent_activity" in data


class TestDashboardV2Integration:
    """Integration tests for complete dashboard system"""

    def test_dashboard_permission_enforcement(self, brand_user_client):
        """Test that users can only access appropriate dashboard metrics"""

        # Brand user should access brand metrics
        response = brand_user_client.get("/api/v2/dashboard/metrics/brand")
        assert response.status_code == 200

        # Brand user should NOT access processor metrics
        response = brand_user_client.get("/api/v2/dashboard/metrics/processor")
        assert response.status_code == 403


class TestDashboardMetricsAPI:
    """Test Dashboard Metrics API endpoints"""

    def test_brand_metrics_requires_brand_company(self, processor_user_client):
        """Test that brand metrics endpoint requires brand company"""
        response = processor_user_client.get("/api/dashboard-v2/metrics/brand")
        assert response.status_code == 403

    def test_processor_metrics_requires_processor_company(self, brand_user_client):
        """Test that processor metrics endpoint requires processor company"""
        response = brand_user_client.get("/api/dashboard-v2/metrics/processor")
        assert response.status_code == 403

    def test_brand_metrics_with_brand_user(self, brand_user_client):
        """Test brand metrics endpoint with brand user"""
        response = brand_user_client.get("/api/dashboard-v2/metrics/brand")
        assert response.status_code == 200

        data = response.json()
        assert "supply_chain_overview" in data
        assert "supplier_portfolio" in data
        assert "recent_activity" in data

    def test_processor_metrics_with_processor_user(self, processor_user_client):
        """Test processor metrics endpoint with processor user"""
        response = processor_user_client.get("/api/dashboard-v2/metrics/processor")
        assert response.status_code == 200

        data = response.json()
        assert "incoming_pos" in data
        assert "production_overview" in data
        assert "recent_activity" in data


# Note: Using existing fixtures from conftest.py
# - brand_user_client: Authenticated client for brand users
# - processor_user_client: Authenticated client for processor users
# - client: Unauthenticated test client
