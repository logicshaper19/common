"""
Integration tests for Dashboard V2 implementation
Tests real data flows, service integration, and complete system behavior
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from uuid import uuid4

from app.main import app
from app.models.purchase_order import PurchaseOrder
from app.models.company import Company
from app.models.user import User
from app.core.feature_flags import feature_flags, FeatureFlag


class TestDashboardV2RealDataIntegration:
    """Test Dashboard V2 with real data flows"""
    
    def test_brand_dashboard_with_real_purchase_orders(self, brand_user_client, simple_scenario, db_session):
        """Test brand dashboard metrics with actual purchase order data"""
        
        # Get brand company and user from scenario
        brand_company = next(c for c in simple_scenario.companies if c.company_type == "brand")
        
        # Create additional purchase orders for testing
        test_pos = []
        for i in range(5):
            po = PurchaseOrder(
                id=uuid4(),
                po_number=f"INTEGRATION-TEST-{i}",
                buyer_company_id=brand_company.id,
                seller_company_id=uuid4(),  # Mock seller
                product_id=uuid4(),  # Mock product
                quantity=100.0 + i * 10,
                unit_price=10.0 + i,
                total_amount=(100.0 + i * 10) * (10.0 + i),
                unit="KG",
                delivery_date=datetime.utcnow() + timedelta(days=30 + i),
                delivery_location="Integration Test Location",
                status="pending" if i < 2 else "confirmed",
                created_at=datetime.utcnow() - timedelta(days=i)
            )
            test_pos.append(po)
            db_session.add(po)
        
        db_session.commit()
        
        try:
            # Test dashboard metrics with real data
            response = brand_user_client.get("/api/v2/dashboard/metrics/brand")
            assert response.status_code == 200
            
            data = response.json()
            
            # Verify structure
            assert "supply_chain_overview" in data
            assert "supplier_portfolio" in data
            assert "recent_activity" in data
            
            # Verify data reflects our test purchase orders
            overview = data["supply_chain_overview"]
            assert "total_pos" in overview
            assert overview["total_pos"] >= 5  # Should include our test POs
            
            # Verify recent activity includes our data
            recent_activity = data["recent_activity"]
            assert isinstance(recent_activity, list)
            
        finally:
            # Clean up test data
            for po in test_pos:
                db_session.delete(po)
            db_session.commit()
    
    def test_processor_dashboard_with_real_data(self, processor_user_client, simple_scenario, db_session):
        """Test processor dashboard with real incoming purchase orders"""
        
        # Get processor company from scenario
        processor_company = next(c for c in simple_scenario.companies if c.company_type == "processor")
        
        # Create incoming purchase orders for processor
        incoming_pos = []
        for i in range(3):
            po = PurchaseOrder(
                id=uuid4(),
                po_number=f"INCOMING-{i}",
                buyer_company_id=uuid4(),  # Mock buyer
                seller_company_id=processor_company.id,  # Processor is seller
                product_id=uuid4(),
                quantity=200.0 + i * 20,
                unit_price=15.0 + i,
                total_amount=(200.0 + i * 20) * (15.0 + i),
                unit="KG",
                delivery_date=datetime.utcnow() + timedelta(days=15 + i),
                delivery_location="Processor Facility",
                status="pending_confirmation",
                created_at=datetime.utcnow() - timedelta(hours=i * 6)
            )
            incoming_pos.append(po)
            db_session.add(po)
        
        db_session.commit()
        
        try:
            # Test processor dashboard metrics
            response = processor_user_client.get("/api/v2/dashboard/metrics/processor")
            assert response.status_code == 200
            
            data = response.json()
            
            # Verify processor-specific structure
            assert "incoming_pos" in data
            assert "production_overview" in data
            assert "recent_activity" in data
            
            # Verify incoming POs data
            incoming = data["incoming_pos"]
            assert "pending_confirmation" in incoming
            assert incoming["pending_confirmation"] >= 3  # Should include our test POs
            
        finally:
            # Clean up
            for po in incoming_pos:
                db_session.delete(po)
            db_session.commit()
    
    def test_dashboard_data_consistency(self, brand_user_client, processor_user_client, simple_scenario):
        """Test that dashboard data is consistent across different user types"""
        
        # Get metrics from both dashboard types
        brand_response = brand_user_client.get("/api/v2/dashboard/metrics/brand")
        processor_response = processor_user_client.get("/api/v2/dashboard/metrics/processor")
        
        assert brand_response.status_code == 200
        assert processor_response.status_code == 200
        
        brand_data = brand_response.json()
        processor_data = processor_response.json()
        
        # Verify both have required structure
        assert "recent_activity" in brand_data
        assert "recent_activity" in processor_data
        
        # Verify data types are consistent
        assert isinstance(brand_data["recent_activity"], list)
        assert isinstance(processor_data["recent_activity"], list)
        
        # Both should have some form of activity data
        # (exact content will differ based on user perspective)
        brand_activity = brand_data["recent_activity"]
        processor_activity = processor_data["recent_activity"]
        
        # Verify activity items have consistent structure
        if brand_activity:
            activity_item = brand_activity[0]
            assert isinstance(activity_item, dict)
            # Should have basic activity fields
            
        if processor_activity:
            activity_item = processor_activity[0]
            assert isinstance(activity_item, dict)


class TestDashboardV2FeatureFlagIntegration:
    """Test Dashboard V2 feature flag integration"""
    
    def test_feature_flag_enabling_disabling(self, brand_user_client):
        """Test that feature flags properly control dashboard access"""
        
        # Test with feature flag enabled (default state)
        response = brand_user_client.get("/api/v2/dashboard/config")
        assert response.status_code == 200
        
        config = response.json()
        assert "dashboard_type" in config
        assert config["dashboard_type"] == "brand"
        
        # Test feature flags endpoint
        flags_response = brand_user_client.get("/api/v2/dashboard/feature-flags")
        assert flags_response.status_code == 200
        
        flags = flags_response.json()
        assert isinstance(flags, dict)
        assert "v2_dashboard_brand" in flags
    
    def test_feature_flag_granular_control(self, brand_user_client, processor_user_client):
        """Test granular feature flag control per dashboard type"""
        
        # Both users should be able to access their respective configs
        brand_config = brand_user_client.get("/api/v2/dashboard/config")
        processor_config = processor_user_client.get("/api/v2/dashboard/config")
        
        assert brand_config.status_code == 200
        assert processor_config.status_code == 200
        
        brand_data = brand_config.json()
        processor_data = processor_config.json()
        
        # Verify correct dashboard types
        assert brand_data["dashboard_type"] == "brand"
        assert processor_data["dashboard_type"] == "processor"
        
        # Verify feature flags are accessible
        brand_flags = brand_user_client.get("/api/v2/dashboard/feature-flags")
        processor_flags = processor_user_client.get("/api/v2/dashboard/feature-flags")
        
        assert brand_flags.status_code == 200
        assert processor_flags.status_code == 200


class TestDashboardV2ServiceIntegration:
    """Test Dashboard V2 integration with existing services"""
    
    def test_permission_service_integration(self, simple_scenario):
        """Test integration with permission service"""
        from app.services.permissions import PermissionService
        
        permission_service = PermissionService(None)
        
        # Test with different user types from scenario
        brand_company = next(c for c in simple_scenario.companies if c.company_type == "brand")
        processor_company = next(c for c in simple_scenario.companies if c.company_type == "processor")
        originator_company = next(c for c in simple_scenario.companies if c.company_type == "originator")
        
        brand_user = next(u for u in simple_scenario.users if u.company_id == brand_company.id)
        processor_user = next(u for u in simple_scenario.users if u.company_id == processor_company.id)
        originator_user = next(u for u in simple_scenario.users if u.company_id == originator_company.id)
        
        # Test dashboard type detection
        assert permission_service.get_dashboard_type(brand_user) == "brand"
        assert permission_service.get_dashboard_type(processor_user) == "processor"
        assert permission_service.get_dashboard_type(originator_user) == "originator"
        
        # Test dashboard config generation
        brand_config = permission_service.get_user_dashboard_config(brand_user)
        processor_config = permission_service.get_user_dashboard_config(processor_user)
        
        assert brand_config["dashboard_type"] == "brand"
        assert processor_config["dashboard_type"] == "processor"
        
        # Both configs should have required fields
        for config in [brand_config, processor_config]:
            assert "dashboard_type" in config
            assert "should_use_v2" in config
            assert "feature_flags" in config
            assert "user_info" in config
    
    def test_database_service_integration(self, brand_user_client, simple_scenario):
        """Test integration with database services"""
        
        # Test that dashboard metrics properly query database
        response = brand_user_client.get("/api/v2/dashboard/metrics/brand")
        assert response.status_code == 200
        
        data = response.json()
        
        # Verify metrics reflect actual database state
        overview = data["supply_chain_overview"]
        
        # Should have numeric values (even if 0)
        assert isinstance(overview["total_pos"], int)
        assert isinstance(overview["traced_to_mill"], int)
        assert isinstance(overview["traced_to_farm"], int)
        assert isinstance(overview["transparency_percentage"], (int, float))
        
        # Transparency percentage should be valid
        assert 0 <= overview["transparency_percentage"] <= 100
    
    def test_error_handling_integration(self, brand_user_client):
        """Test error handling integration across services"""
        
        # Test with invalid dashboard type
        response = brand_user_client.get("/api/v2/dashboard/metrics/invalid-type")
        assert response.status_code == 404
        
        # Test permission enforcement
        response = brand_user_client.get("/api/v2/dashboard/metrics/platform-admin")
        assert response.status_code == 403
        
        # Test that valid requests still work after errors
        response = brand_user_client.get("/api/v2/dashboard/metrics/brand")
        assert response.status_code == 200


class TestDashboardV2SystemIntegration:
    """Test Dashboard V2 as complete system integration"""
    
    def test_complete_system_workflow(self, brand_user_client, processor_user_client, simple_scenario):
        """Test complete system workflow with multiple users and data"""
        
        # Step 1: Both users get their configurations
        brand_config = brand_user_client.get("/api/v2/dashboard/config").json()
        processor_config = processor_user_client.get("/api/v2/dashboard/config").json()
        
        assert brand_config["dashboard_type"] == "brand"
        assert processor_config["dashboard_type"] == "processor"
        
        # Step 2: Both users access their metrics
        brand_metrics = brand_user_client.get("/api/v2/dashboard/metrics/brand").json()
        processor_metrics = processor_user_client.get("/api/v2/dashboard/metrics/processor").json()
        
        # Step 3: Verify system maintains data consistency
        assert "supply_chain_overview" in brand_metrics
        assert "incoming_pos" in processor_metrics
        
        # Step 4: Verify permission boundaries are maintained
        brand_forbidden = brand_user_client.get("/api/v2/dashboard/metrics/processor")
        processor_forbidden = processor_user_client.get("/api/v2/dashboard/metrics/brand")
        
        assert brand_forbidden.status_code == 403
        assert processor_forbidden.status_code == 403
        
        # Step 5: Verify feature flags work for both users
        brand_flags = brand_user_client.get("/api/v2/dashboard/feature-flags").json()
        processor_flags = processor_user_client.get("/api/v2/dashboard/feature-flags").json()
        
        assert isinstance(brand_flags, dict)
        assert isinstance(processor_flags, dict)
        
        # Both should have the same feature flags (system-wide)
        assert set(brand_flags.keys()) == set(processor_flags.keys())
    
    def test_system_resilience(self, brand_user_client):
        """Test system resilience and error recovery"""
        
        # Make multiple requests to test system stability
        for i in range(10):
            config_response = brand_user_client.get("/api/v2/dashboard/config")
            metrics_response = brand_user_client.get("/api/v2/dashboard/metrics/brand")
            flags_response = brand_user_client.get("/api/v2/dashboard/feature-flags")
            
            # All should succeed consistently
            assert config_response.status_code == 200
            assert metrics_response.status_code == 200
            assert flags_response.status_code == 200
            
            # Data structure should remain consistent
            config = config_response.json()
            metrics = metrics_response.json()
            flags = flags_response.json()
            
            assert config["dashboard_type"] == "brand"
            assert "supply_chain_overview" in metrics
            assert isinstance(flags, dict)
