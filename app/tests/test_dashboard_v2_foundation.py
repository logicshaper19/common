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

    def setup_method(self):
        """Setup for each test method - store original feature flag state"""
        self.original_flags = {}
        for flag in [
            FeatureFlag.V2_DASHBOARD_BRAND,
            FeatureFlag.V2_DASHBOARD_PROCESSOR,
            FeatureFlag.V2_DASHBOARD_ORIGINATOR,
            FeatureFlag.V2_DASHBOARD_TRADER,
            FeatureFlag.V2_DASHBOARD_PLATFORM_ADMIN,
            FeatureFlag.V2_NOTIFICATION_CENTER
        ]:
            self.original_flags[flag] = feature_flags.is_enabled(flag)

    def teardown_method(self):
        """Cleanup after each test method - restore original feature flag state"""
        for flag, original_state in self.original_flags.items():
            if original_state:
                feature_flags.enable(flag)
            else:
                feature_flags.disable(flag)

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
    
    def test_permission_service_initialization(self):
        """Test that permission service can be initialized"""
        permission_service = PermissionService(None)
        assert permission_service is not None

    def test_get_dashboard_type_brand(self, simple_scenario):
        """Test dashboard type detection for brand users"""
        permission_service = PermissionService(None)
        brand_company = next(c for c in simple_scenario.companies if c.company_type == "brand")
        brand_user = next(u for u in simple_scenario.users if u.company_id == brand_company.id)
        dashboard_type = permission_service.get_dashboard_type(brand_user)
        assert dashboard_type == "brand"

    def test_get_dashboard_type_processor(self, simple_scenario):
        """Test dashboard type detection for processor users"""
        permission_service = PermissionService(None)
        processor_company = next(c for c in simple_scenario.companies if c.company_type == "processor")
        processor_user = next(u for u in simple_scenario.users if u.company_id == processor_company.id)
        dashboard_type = permission_service.get_dashboard_type(processor_user)
        assert dashboard_type == "processor"

    def test_get_dashboard_type_originator(self, simple_scenario):
        """Test dashboard type detection for originator users"""
        permission_service = PermissionService(None)
        originator_company = next(c for c in simple_scenario.companies if c.company_type == "originator")
        originator_user = next(u for u in simple_scenario.users if u.company_id == originator_company.id)
        dashboard_type = permission_service.get_dashboard_type(originator_user)
        assert dashboard_type == "originator"

    def test_dashboard_config_includes_dashboard_type(self, simple_scenario):
        """Test that dashboard config includes dashboard type"""
        permission_service = PermissionService(None)
        brand_company = next(c for c in simple_scenario.companies if c.company_type == "brand")
        brand_user = next(u for u in simple_scenario.users if u.company_id == brand_company.id)
        config = permission_service.get_user_dashboard_config(brand_user)
        assert "dashboard_type" in config
        assert config["dashboard_type"] == "brand"


class TestDashboardV2API:
    """Test Dashboard V2 API endpoints"""

    def test_feature_flags_endpoint_requires_auth(self, client):
        """Test that feature flags endpoint requires authentication"""
        response = client.get("/api/v2/dashboard/feature-flags")
        assert response.status_code == 403  # FastAPI HTTPBearer returns 403, not 401

    def test_dashboard_config_endpoint_requires_auth(self, client):
        """Test that dashboard config endpoint requires authentication"""
        response = client.get("/api/v2/dashboard/config")
        assert response.status_code == 403  # FastAPI HTTPBearer returns 403, not 401

    def test_feature_flags_endpoint_with_auth(self, brand_user_client):
        """Test feature flags endpoint with authentication"""
        response = brand_user_client.get("/api/v2/dashboard/feature-flags")
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
        response = brand_user_client.get("/api/v2/dashboard/config")
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

    def test_platform_admin_metrics_structure(self, brand_user_client):
        """Test platform admin dashboard metrics (using brand user for testing)"""
        # Note: This test uses brand user since admin_user_client fixture doesn't exist
        response = brand_user_client.get("/api/v2/dashboard/metrics/platform-admin")
        # Expect 403 since brand user shouldn't access platform admin metrics
        assert response.status_code == 403


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


class TestDashboardV2EndToEnd:
    """End-to-end tests for complete Dashboard V2 workflows"""

    def test_complete_brand_user_workflow(self, brand_user_client):
        """Test complete workflow for brand user from login to dashboard usage"""

        # Step 1: Get feature flags
        flags_response = brand_user_client.get("/api/v2/dashboard/feature-flags")
        assert flags_response.status_code == 200
        flags = flags_response.json()

        # Step 2: Get dashboard configuration
        config_response = brand_user_client.get("/api/v2/dashboard/config")
        assert config_response.status_code == 200
        config = config_response.json()
        assert config["dashboard_type"] == "brand"

        # Step 3: Get dashboard metrics
        metrics_response = brand_user_client.get("/api/v2/dashboard/metrics/brand")
        assert metrics_response.status_code == 200
        metrics = metrics_response.json()

        # Verify complete dashboard data structure
        assert "supply_chain_overview" in metrics
        assert "supplier_portfolio" in metrics
        assert "recent_activity" in metrics

        # Verify metrics have expected structure
        overview = metrics["supply_chain_overview"]
        assert "total_pos" in overview
        assert "traced_to_mill" in overview
        assert "traced_to_farm" in overview
        assert "transparency_percentage" in overview

    def test_complete_processor_user_workflow(self, processor_user_client):
        """Test complete workflow for processor user"""

        # Step 1: Get dashboard configuration
        config_response = processor_user_client.get("/api/v2/dashboard/config")
        assert config_response.status_code == 200
        config = config_response.json()
        assert config["dashboard_type"] == "processor"

        # Step 2: Get processor-specific metrics
        metrics_response = processor_user_client.get("/api/v2/dashboard/metrics/processor")
        assert metrics_response.status_code == 200
        metrics = metrics_response.json()

        # Verify processor dashboard structure
        assert "incoming_pos" in metrics
        assert "production_overview" in metrics
        assert "recent_activity" in metrics

        # Verify processor can't access brand metrics
        brand_metrics_response = processor_user_client.get("/api/v2/dashboard/metrics/brand")
        assert brand_metrics_response.status_code == 403

    def test_dashboard_permission_enforcement_comprehensive(self, brand_user_client, processor_user_client):
        """Test comprehensive permission enforcement across all dashboard types"""

        # Test brand user permissions
        brand_responses = {
            "brand": brand_user_client.get("/api/v2/dashboard/metrics/brand"),
            "processor": brand_user_client.get("/api/v2/dashboard/metrics/processor"),
            "originator": brand_user_client.get("/api/v2/dashboard/metrics/originator"),
            "trader": brand_user_client.get("/api/v2/dashboard/metrics/trader"),
            "platform-admin": brand_user_client.get("/api/v2/dashboard/metrics/platform-admin")
        }

        # Brand user should only access brand metrics
        assert brand_responses["brand"].status_code == 200
        assert brand_responses["processor"].status_code == 403
        assert brand_responses["originator"].status_code == 403
        assert brand_responses["trader"].status_code == 403
        assert brand_responses["platform-admin"].status_code == 403

        # Test processor user permissions
        processor_responses = {
            "brand": processor_user_client.get("/api/v2/dashboard/metrics/brand"),
            "processor": processor_user_client.get("/api/v2/dashboard/metrics/processor"),
            "originator": processor_user_client.get("/api/v2/dashboard/metrics/originator"),
        }

        # Processor user should only access processor metrics
        assert processor_responses["brand"].status_code == 403
        assert processor_responses["processor"].status_code == 200
        assert processor_responses["originator"].status_code == 403


class TestDashboardV2ErrorHandling:
    """Test Dashboard V2 error scenarios and edge cases"""

    def test_invalid_dashboard_type(self, brand_user_client):
        """Test handling of invalid dashboard type"""
        response = brand_user_client.get("/api/v2/dashboard/metrics/invalid-type")
        assert response.status_code == 404

        error_data = response.json()
        assert "detail" in error_data

    def test_malformed_requests(self, brand_user_client):
        """Test handling of malformed requests"""
        # Test with invalid HTTP methods
        response = brand_user_client.post("/api/v2/dashboard/config")
        assert response.status_code == 405  # Method not allowed

        response = brand_user_client.put("/api/v2/dashboard/feature-flags")
        assert response.status_code == 405  # Method not allowed

    def test_permission_boundaries(self, brand_user_client, processor_user_client):
        """Test strict permission boundaries between user types"""
        # Brand user trying to access all other dashboard types
        forbidden_endpoints = [
            "/api/v2/dashboard/metrics/processor",
            "/api/v2/dashboard/metrics/originator",
            "/api/v2/dashboard/metrics/trader",
            "/api/v2/dashboard/metrics/platform-admin"
        ]

        for endpoint in forbidden_endpoints:
            response = brand_user_client.get(endpoint)
            assert response.status_code == 403, f"Brand user should not access {endpoint}"

        # Processor user trying to access other dashboard types
        processor_forbidden = [
            "/api/v2/dashboard/metrics/brand",
            "/api/v2/dashboard/metrics/originator",
            "/api/v2/dashboard/metrics/trader",
            "/api/v2/dashboard/metrics/platform-admin"
        ]

        for endpoint in processor_forbidden:
            response = processor_user_client.get(endpoint)
            assert response.status_code == 403, f"Processor user should not access {endpoint}"

    def test_invalid_authentication_tokens(self, client):
        """Test handling of invalid authentication tokens"""
        # Test with malformed Bearer token
        headers = {"Authorization": "Bearer invalid-token"}
        response = client.get("/api/v2/dashboard/config", headers=headers)
        assert response.status_code in [401, 403]  # Should reject invalid token

        # Test with wrong token format
        headers = {"Authorization": "Basic invalid-format"}
        response = client.get("/api/v2/dashboard/config", headers=headers)
        assert response.status_code in [401, 403]  # Should reject wrong format


class TestDashboardMetricsAPI:
    """Test Dashboard Metrics API endpoints"""

    def test_brand_metrics_requires_brand_company(self, processor_user_client):
        """Test that brand metrics endpoint requires brand company"""
        response = processor_user_client.get("/api/v2/dashboard/metrics/brand")
        assert response.status_code == 403

    def test_processor_metrics_requires_processor_company(self, brand_user_client):
        """Test that processor metrics endpoint requires processor company"""
        response = brand_user_client.get("/api/v2/dashboard/metrics/processor")
        assert response.status_code == 403

    def test_brand_metrics_with_brand_user(self, brand_user_client):
        """Test brand metrics endpoint with brand user"""
        response = brand_user_client.get("/api/v2/dashboard/metrics/brand")
        assert response.status_code == 200

        data = response.json()
        assert "supply_chain_overview" in data
        assert "supplier_portfolio" in data
        assert "recent_activity" in data

    def test_processor_metrics_with_processor_user(self, processor_user_client):
        """Test processor metrics endpoint with processor user"""
        response = processor_user_client.get("/api/v2/dashboard/metrics/processor")
        assert response.status_code == 200

        data = response.json()
        assert "incoming_pos" in data
        assert "production_overview" in data
        assert "recent_activity" in data


# Note: Using existing fixtures from conftest.py
# - brand_user_client: Authenticated client for brand users
# - processor_user_client: Authenticated client for processor users
# - client: Unauthenticated test client
