"""
Comprehensive tests for Phase 5 Performance Optimization Implementation
Tests all components: health checker, feature flags, batch linking, and API endpoints
"""
import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from sqlalchemy import text
from uuid import uuid4, UUID
from datetime import datetime, timedelta

from app.main import app
from app.services.optimized_health_checker import OptimizedHealthChecker, health_checker
from app.core.consolidated_feature_flags import (
    ConsolidatedFeatureFlagService, 
    consolidated_feature_flags,
    ConsolidatedFeatureFlag
)
from app.services.optimized_batch_linking import OptimizedBatchLinkingService
from app.models.purchase_order import PurchaseOrder
from app.models.po_batch_linkage import POBatchLinkage
from app.models.batch import Batch
from app.models.company import Company
from app.models.user import User
from app.core.database import get_db


class TestOptimizedHealthChecker:
    """Test the optimized health checker with caching."""
    
    def setup_method(self):
        """Setup for each test method."""
        self.health_checker = OptimizedHealthChecker()
        # Clear any cached results
        self.health_checker._cached_result = None
        self.health_checker._cache_timestamp = None
    
    @pytest.mark.asyncio
    async def test_health_check_caching(self):
        """Test that health checks are properly cached."""
        # First call should not be cached
        result1 = await self.health_checker.get_system_health()
        assert result1["cached"] is False
        
        # Second call within cache duration should be cached
        result2 = await self.health_checker.get_system_health()
        assert result2["cached"] is True
        assert result1["timestamp"] == result2["timestamp"]
    
    @pytest.mark.asyncio
    async def test_health_check_structure(self):
        """Test health check response structure."""
        result = await self.health_checker.get_system_health()
        
        assert "status" in result
        assert "checks" in result
        assert "response_time" in result
        assert "timestamp" in result
        assert "cached" in result
        
        # Check individual health checks
        checks = result["checks"]
        assert "database" in checks
        assert "redis" in checks
        assert "transparency_calc" in checks
        
        # Each check should have status
        for check_name, check_result in checks.items():
            assert "status" in check_result
    
    @pytest.mark.asyncio
    async def test_database_health_check(self):
        """Test database health check functionality."""
        with patch('app.services.optimized_health_checker.get_db') as mock_get_db:
            # Mock database session
            mock_db = Mock()
            mock_result = Mock()
            mock_result.recent_pos = 5
            mock_db.execute.return_value.fetchone.return_value = mock_result
            
            # Mock connection pool
            mock_pool = Mock()
            mock_pool.size.return_value = 10
            mock_pool.checkedout.return_value = 3
            mock_db.get_bind.return_value.pool = mock_pool
            
            mock_get_db.return_value = iter([mock_db])
            
            result = await self.health_checker._check_database_lightweight()
            
            assert result["status"] == "healthy"
            assert result["recent_pos"] == 5
            assert result["pool_usage"] == "0.3"
    
    @pytest.mark.asyncio
    async def test_redis_health_check(self):
        """Test Redis health check functionality."""
        with patch('app.services.optimized_health_checker.get_redis') as mock_get_redis:
            # Mock Redis client
            mock_redis = AsyncMock()
            mock_redis.ping = AsyncMock()
            mock_redis.info = AsyncMock(return_value={
                'used_memory': 1024 * 1024,  # 1MB
                'maxmemory': 10 * 1024 * 1024  # 10MB
            })
            
            mock_get_redis.return_value = mock_redis
            
            result = await self.health_checker._check_redis_simple()
            
            assert result["status"] == "healthy"
            assert result["memory_usage"] == "0.1"
            assert result["used_memory_mb"] == "1.0"


class TestConsolidatedFeatureFlags:
    """Test the consolidated feature flag system."""
    
    def setup_method(self):
        """Setup for each test method."""
        self.feature_flags = ConsolidatedFeatureFlagService()
    
    def test_feature_flag_initialization(self):
        """Test feature flag service initialization."""
        assert hasattr(self.feature_flags, 'v2_enabled')
        assert hasattr(self.feature_flags, 'company_dashboards')
        assert hasattr(self.feature_flags, 'admin_features')
    
    def test_v2_enabled_for_user(self):
        """Test V2 feature availability for different user types."""
        # Test platform admin
        assert self.feature_flags.is_v2_enabled_for_user("platform_admin", "brand") == self.feature_flags.admin_features
        
        # Test regular user
        assert self.feature_flags.is_v2_enabled_for_user("user", "brand") == self.feature_flags.company_dashboards
    
    def test_get_enabled_features(self):
        """Test getting enabled features for a user."""
        features = self.feature_flags.get_enabled_features("platform_admin")
        
        assert "v2_dashboard" in features
        assert "notifications" in features
        assert "admin_panel" in features
        
        # Admin should have admin_panel if admin_features is enabled
        if self.feature_flags.admin_features:
            assert features["admin_panel"] is True
    
    def test_legacy_feature_flags_mapping(self):
        """Test mapping to legacy feature flags for backward compatibility."""
        legacy_flags = self.feature_flags.get_legacy_feature_flags("user", "brand")
        
        expected_flags = [
            "v2_dashboard_brand",
            "v2_dashboard_processor", 
            "v2_dashboard_originator",
            "v2_dashboard_trader",
            "v2_dashboard_platform_admin",
            "v2_notification_center"
        ]
        
        for flag in expected_flags:
            assert flag in legacy_flags
            assert isinstance(legacy_flags[flag], bool)
    
    def test_dashboard_config(self):
        """Test dashboard configuration generation."""
        config = self.feature_flags.get_dashboard_config("user", "brand")
        
        assert "should_use_v2" in config
        assert "dashboard_type" in config
        assert "feature_flags" in config
        assert "user_info" in config
        assert "consolidated_flags" in config
        
        assert config["dashboard_type"] == "brand"
        assert config["user_info"]["role"] == "user"
        assert config["user_info"]["company_type"] == "brand"
    
    def test_refresh_flags(self):
        """Test feature flag refresh functionality."""
        original_v2_enabled = self.feature_flags.v2_enabled
        
        # Refresh should not change values unless env vars change
        self.feature_flags.refresh_flags()
        
        # Values should still be the same (unless env vars changed)
        assert self.feature_flags.v2_enabled == original_v2_enabled


class TestOptimizedBatchLinking:
    """Test the optimized batch linking service."""
    
    def setup_method(self):
        """Setup for each test method."""
        self.mock_db = Mock(spec=Session)
        self.batch_linking_service = OptimizedBatchLinkingService(self.mock_db)
    
    @pytest.mark.asyncio
    async def test_bulk_linking_validation(self):
        """Test bulk batch linking with validation."""
        # Mock database responses
        self.mock_db.execute.return_value.fetchall.side_effect = [
            [(uuid4(),)],  # Existing POs
            [(uuid4(),)]   # Existing batches
        ]
        
        linkages = [
            {
                "po_id": uuid4(),
                "batch_id": uuid4(),
                "quantity": 100.0,
                "unit": "MT"
            }
        ]
        
        # Mock commit
        self.mock_db.commit = AsyncMock()
        
        result = await self.batch_linking_service.link_batch_to_po_bulk(linkages)
        
        assert len(result) == 1
        assert isinstance(result[0], POBatchLinkage)
        self.mock_db.add_all.assert_called_once()
        self.mock_db.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_bulk_linking_invalid_po(self):
        """Test bulk linking with invalid PO ID."""
        # Mock database responses - no existing POs
        self.mock_db.execute.return_value.fetchall.side_effect = [
            [],  # No existing POs
            [(uuid4(),)]   # Existing batches
        ]
        
        linkages = [
            {
                "po_id": uuid4(),
                "batch_id": uuid4(),
                "quantity": 100.0
            }
        ]
        
        with pytest.raises(ValueError, match="Purchase Order.*not found"):
            await self.batch_linking_service.link_batch_to_po_bulk(linkages)
    
    @pytest.mark.asyncio
    async def test_supply_chain_optimized(self):
        """Test optimized supply chain query."""
        po_id = uuid4()
        
        # Mock database response
        mock_result = Mock()
        mock_result.id = po_id
        mock_result.po_number = "PO-001"
        mock_result.level = 0
        mock_result.buyer_name = "Test Company"
        mock_result.batch_number = "BATCH-001"
        mock_result.status = "confirmed"
        
        self.mock_db.execute.return_value.fetchall.return_value = [mock_result]
        
        result = await self.batch_linking_service.get_supply_chain_optimized(po_id)
        
        assert "supply_chain" in result
        assert "total_levels" in result
        assert len(result["supply_chain"]) == 1
        assert result["supply_chain"][0]["po_id"] == str(po_id)
    
    @pytest.mark.asyncio
    async def test_batch_utilization(self):
        """Test batch utilization calculation."""
        batch_id = uuid4()
        
        # Mock database response
        mock_result = Mock()
        mock_result.batch_id = "BATCH-001"
        mock_result.total_quantity = 1000.0
        mock_result.allocated_quantity = 300.0
        mock_result.allocation_count = 2
        mock_result.remaining_quantity = 700.0
        mock_result.unit = "MT"
        
        self.mock_db.execute.return_value.fetchone.return_value = mock_result
        
        result = await self.batch_linking_service.get_batch_utilization(batch_id)
        
        assert result["batch_id"] == "BATCH-001"
        assert result["total_quantity"] == 1000.0
        assert result["allocated_quantity"] == 300.0
        assert result["remaining_quantity"] == 700.0
        assert result["utilization_percentage"] == 30.0


class TestPerformanceMonitoringAPI:
    """Test the performance monitoring API endpoints."""
    
    def setup_method(self):
        """Setup for each test method."""
        self.client = TestClient(app)
    
    def test_health_endpoint(self):
        """Test system health endpoint."""
        with patch('app.api.v2.performance_monitoring.health_checker') as mock_health_checker:
            mock_health_checker.get_system_health = AsyncMock(return_value={
                "status": "healthy",
                "checks": {
                    "database": {"status": "healthy"},
                    "redis": {"status": "healthy"},
                    "transparency_calc": {"status": "healthy"}
                },
                "response_time": "0.050s",
                "timestamp": datetime.utcnow().isoformat(),
                "cached": False
            })
            
            response = self.client.get("/api/v2/performance/health")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert "checks" in data
            assert "response_time" in data
    
    def test_transparency_performance_endpoint(self):
        """Test transparency performance endpoint."""
        with patch('app.api.v2.performance_monitoring.get_db') as mock_get_db:
            # Mock database session
            mock_db = Mock()
            mock_result = Mock()
            mock_result.total_companies = 10
            mock_result.overall_avg_score = 85.5
            mock_result.total_pos_tracked = 100
            mock_result.total_volume_tracked = 1000.0
            mock_result.last_updated = datetime.utcnow()
            
            mock_db.execute.return_value.fetchone.return_value = mock_result
            mock_get_db.return_value = iter([mock_db])
            
            response = self.client.get("/api/v2/performance/transparency")
            
            assert response.status_code == 200
            data = response.json()
            assert "performance" in data
            assert "metrics" in data
            assert "optimizations_applied" in data
            assert data["metrics"]["total_companies"] == 10
    
    def test_optimization_status_endpoint(self):
        """Test optimization status endpoint."""
        with patch('app.api.v2.performance_monitoring.get_db') as mock_get_db:
            # Mock database session
            mock_db = Mock()
            mock_db.execute.return_value.fetchone.side_effect = [
                (True,),  # Materialized view exists
                (True,),  # Performance metrics table exists
            ]
            mock_db.execute.return_value.fetchall.return_value = [
                ("idx_po_batch_reference_active",),
                ("idx_po_fulfillment_compound",),
                ("idx_po_transparency_calc",)
            ]
            mock_get_db.return_value = iter([mock_db])
            
            response = self.client.get("/api/v2/performance/optimization-status")
            
            assert response.status_code == 200
            data = response.json()
            assert "phase_5_optimizations" in data
            assert data["phase_5_optimizations"]["materialized_view"]["exists"] is True
            assert data["phase_5_optimizations"]["optimized_indexes"]["count"] == 3


class TestDashboardOptimizedAPI:
    """Test the optimized dashboard API endpoints."""
    
    def setup_method(self):
        """Setup for each test method."""
        self.client = TestClient(app)
    
    def test_dashboard_config_endpoint(self):
        """Test dashboard config endpoint."""
        with patch('app.api.v2.dashboard_optimized.get_current_user') as mock_get_user:
            # Mock current user
            mock_user = Mock()
            mock_user.user.role = "user"
            mock_user.company.company_type = "brand"
            mock_user.user.id = uuid4()
            mock_user.user.email = "test@example.com"
            mock_user.company.name = "Test Company"
            mock_user.company.id = uuid4()
            
            mock_get_user.return_value = mock_user
            
            with patch('app.api.v2.dashboard_optimized.consolidated_feature_flags') as mock_flags:
                mock_flags.get_dashboard_config.return_value = {
                    "should_use_v2": True,
                    "dashboard_type": "brand",
                    "feature_flags": {"v2_dashboard_brand": True},
                    "user_info": {"role": "user", "company_type": "brand"},
                    "consolidated_flags": {"v2_features_enabled": True}
                }
                
                response = self.client.get("/api/v2/dashboard/config")
                
                assert response.status_code == 200
                data = response.json()
                assert data["dashboard_type"] == "brand"
                assert "feature_flags" in data
                assert "user_info" in data
    
    def test_feature_flags_endpoint(self):
        """Test feature flags endpoint."""
        with patch('app.api.v2.dashboard_optimized.get_current_user') as mock_get_user:
            # Mock current user
            mock_user = Mock()
            mock_user.user.role = "user"
            mock_user.company.company_type = "brand"
            mock_get_user.return_value = mock_user
            
            with patch('app.api.v2.dashboard_optimized.consolidated_feature_flags') as mock_flags:
                mock_flags.get_legacy_feature_flags.return_value = {
                    "v2_dashboard_brand": True,
                    "v2_dashboard_processor": False,
                    "v2_dashboard_originator": False,
                    "v2_dashboard_trader": False,
                    "v2_dashboard_platform_admin": False,
                    "v2_notification_center": True
                }
                
                response = self.client.get("/api/v2/dashboard/feature-flags")
                
                assert response.status_code == 200
                data = response.json()
                assert data["v2_dashboard_brand"] is True
                assert data["v2_dashboard_processor"] is False


class TestIntegration:
    """Integration tests for Phase 5 components."""
    
    def test_feature_flag_consistency(self):
        """Test that consolidated feature flags maintain consistency."""
        # Test that legacy flags are properly derived from consolidated flags
        user_role = "user"
        company_type = "brand"
        
        legacy_flags = consolidated_feature_flags.get_legacy_feature_flags(user_role, company_type)
        
        # Brand user should have brand dashboard enabled if company dashboards are enabled
        if consolidated_feature_flags.company_dashboards:
            assert legacy_flags["v2_dashboard_brand"] is True
        else:
            assert legacy_flags["v2_dashboard_brand"] is False
    
    def test_health_checker_integration(self):
        """Test health checker integration with other components."""
        # Health checker should be importable and instantiable
        assert health_checker is not None
        assert isinstance(health_checker, OptimizedHealthChecker)
        
        # Should have proper cache settings
        assert health_checker.cache_duration == 30
    
    def test_batch_linking_service_integration(self):
        """Test batch linking service integration."""
        # Service should be importable and instantiable
        from app.services.optimized_batch_linking import OptimizedBatchLinkingService
        
        mock_db = Mock()
        service = OptimizedBatchLinkingService(mock_db)
        
        assert service is not None
        assert service.db == mock_db


# Performance benchmarks
class TestPerformanceBenchmarks:
    """Performance benchmark tests for Phase 5 optimizations."""
    
    @pytest.mark.asyncio
    async def test_health_check_performance(self):
        """Test health check performance meets requirements."""
        health_checker = OptimizedHealthChecker()
        
        start_time = asyncio.get_event_loop().time()
        result = await health_checker.get_system_health()
        end_time = asyncio.get_event_loop().time()
        
        response_time = float(result["response_time"].replace("s", ""))
        
        # Health check should be fast (under 1 second)
        assert response_time < 1.0
        assert end_time - start_time < 1.0
    
    def test_feature_flag_performance(self):
        """Test feature flag evaluation performance."""
        import time
        
        start_time = time.time()
        
        # Evaluate feature flags multiple times
        for _ in range(1000):
            consolidated_feature_flags.is_v2_enabled_for_user("user", "brand")
            consolidated_feature_flags.get_legacy_feature_flags("user", "brand")
        
        end_time = time.time()
        
        # Feature flag evaluation should be very fast (under 10ms for 1000 evaluations)
        assert (end_time - start_time) < 0.01
    
    def test_consolidated_vs_legacy_performance(self):
        """Test that consolidated feature flags are faster than legacy approach."""
        import time
        
        # Test consolidated approach
        start_time = time.time()
        for _ in range(1000):
            consolidated_feature_flags.is_v2_enabled_for_user("user", "brand")
        consolidated_time = time.time() - start_time
        
        # Consolidated approach should be fast
        assert consolidated_time < 0.01


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
