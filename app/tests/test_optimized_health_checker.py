"""
Dedicated tests for optimized health checker
Tests caching, performance, and error handling
"""
import pytest
import asyncio
import time
from unittest.mock import Mock, patch, AsyncMock
from app.services.optimized_health_checker import OptimizedHealthChecker, health_checker


class TestOptimizedHealthChecker:
    """Test the optimized health checker functionality."""
    
    def setup_method(self):
        """Setup for each test method."""
        self.health_checker = OptimizedHealthChecker()
        # Clear any cached results
        self.health_checker._cached_result = None
        self.health_checker._cache_timestamp = None
    
    @pytest.mark.asyncio
    async def test_health_check_caching_behavior(self):
        """Test that health checks are properly cached and returned."""
        # First call should not be cached
        result1 = await self.health_checker.get_system_health()
        assert result1["cached"] is False
        assert "timestamp" in result1
        assert "response_time" in result1
        
        # Second call within cache duration should be cached
        result2 = await self.health_checker.get_system_health()
        assert result2["cached"] is True
        assert result1["timestamp"] == result2["timestamp"]
        assert result1["response_time"] == result2["response_time"]
    
    @pytest.mark.asyncio
    async def test_cache_expiration(self):
        """Test that cache expires after the specified duration."""
        # Set cache duration to 0.1 seconds for testing
        self.health_checker.cache_duration = 0.1
        
        # First call
        result1 = await self.health_checker.get_system_health()
        assert result1["cached"] is False
        
        # Wait for cache to expire
        await asyncio.sleep(0.2)
        
        # Second call should not be cached
        result2 = await self.health_checker.get_system_health()
        assert result2["cached"] is False
    
    @pytest.mark.asyncio
    async def test_health_check_structure(self):
        """Test health check response structure."""
        result = await self.health_checker.get_system_health()
        
        # Required top-level keys
        assert "status" in result
        assert "checks" in result
        assert "response_time" in result
        assert "timestamp" in result
        assert "cached" in result
        
        # Status should be a string
        assert isinstance(result["status"], str)
        assert result["status"] in ["healthy", "degraded", "unhealthy"]
        
        # Response time should be a string with 's' suffix
        assert isinstance(result["response_time"], str)
        assert result["response_time"].endswith("s")
        
        # Timestamp should be a valid ISO format string
        assert isinstance(result["timestamp"], str)
        # Should be able to parse as datetime
        from datetime import datetime
        datetime.fromisoformat(result["timestamp"].replace('Z', '+00:00'))
        
        # Checks should contain expected health check types
        checks = result["checks"]
        assert "database" in checks
        assert "redis" in checks
        assert "transparency_calc" in checks
        
        # Each check should have status
        for check_name, check_result in checks.items():
            assert "status" in check_result
            assert check_result["status"] in ["healthy", "degraded", "unhealthy"]
    
    @pytest.mark.asyncio
    async def test_database_health_check_success(self):
        """Test successful database health check."""
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
            assert "query_time" in result
            assert result["query_time"].endswith("s")
    
    @pytest.mark.asyncio
    async def test_database_health_check_degraded(self):
        """Test degraded database health check."""
        with patch('app.services.optimized_health_checker.get_db') as mock_get_db:
            # Mock database session with slow query
            mock_db = Mock()
            mock_result = Mock()
            mock_result.recent_pos = 1000
            mock_db.execute.return_value.fetchone.return_value = mock_result
            
            # Mock connection pool with high usage
            mock_pool = Mock()
            mock_pool.size.return_value = 10
            mock_pool.checkedout.return_value = 9  # 90% usage
            mock_db.get_bind.return_value.pool = mock_pool
            
            mock_get_db.return_value = iter([mock_db])
            
            # Mock slow query time
            with patch('time.time', side_effect=[0, 0.6]):  # 0.6 second query
                result = await self.health_checker._check_database_lightweight()
                
                assert result["status"] == "degraded"
                assert result["recent_pos"] == 1000
                assert result["pool_usage"] == "0.9"
    
    @pytest.mark.asyncio
    async def test_database_health_check_error(self):
        """Test database health check with error."""
        with patch('app.services.optimized_health_checker.get_db') as mock_get_db:
            # Mock database error
            mock_get_db.side_effect = Exception("Database connection failed")
            
            result = await self.health_checker._check_database_lightweight()
            
            assert result["status"] == "unhealthy"
            assert "error" in result
            assert "Database connection failed" in result["error"]
    
    @pytest.mark.asyncio
    async def test_redis_health_check_success(self):
        """Test successful Redis health check."""
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
            assert "ping_time" in result
            assert result["ping_time"].endswith("s")
    
    @pytest.mark.asyncio
    async def test_redis_health_check_degraded(self):
        """Test degraded Redis health check."""
        with patch('app.services.optimized_health_checker.get_redis') as mock_get_redis:
            # Mock Redis client with high memory usage
            mock_redis = AsyncMock()
            mock_redis.ping = AsyncMock()
            mock_redis.info = AsyncMock(return_value={
                'used_memory': 9 * 1024 * 1024,  # 9MB
                'maxmemory': 10 * 1024 * 1024  # 10MB
            })
            
            mock_get_redis.return_value = mock_redis
            
            # Mock slow ping time
            with patch('time.time', side_effect=[0, 0.2]):  # 0.2 second ping
                result = await self.health_checker._check_redis_simple()
                
                assert result["status"] == "degraded"
                assert result["memory_usage"] == "0.9"
                assert result["used_memory_mb"] == "9.0"
    
    @pytest.mark.asyncio
    async def test_redis_health_check_no_client(self):
        """Test Redis health check when no client is available."""
        with patch('app.services.optimized_health_checker.get_redis') as mock_get_redis:
            mock_get_redis.return_value = None
            
            result = await self.health_checker._check_redis_simple()
            
            assert result["status"] == "unhealthy"
            assert "error" in result
            assert "Redis client not available" in result["error"]
    
    @pytest.mark.asyncio
    async def test_redis_health_check_error(self):
        """Test Redis health check with error."""
        with patch('app.services.optimized_health_checker.get_redis') as mock_get_redis:
            # Mock Redis error
            mock_redis = AsyncMock()
            mock_redis.ping = AsyncMock(side_effect=Exception("Redis connection failed"))
            
            mock_get_redis.return_value = mock_redis
            
            result = await self.health_checker._check_redis_simple()
            
            assert result["status"] == "unhealthy"
            assert "error" in result
            assert "Redis connection failed" in result["error"]
    
    @pytest.mark.asyncio
    async def test_transparency_performance_check_success(self):
        """Test successful transparency performance check."""
        with patch('app.services.optimized_health_checker.get_db') as mock_get_db:
            # Mock database session
            mock_db = Mock()
            mock_result = Mock()
            mock_result.companies_with_transparency = 10
            mock_result.overall_avg_score = 85.5
            mock_db.execute.return_value.fetchone.return_value = mock_result
            
            mock_get_db.return_value = iter([mock_db])
            
            result = await self.health_checker._check_transparency_performance()
            
            assert result["status"] == "healthy"
            assert result["companies_tracked"] == 10
            assert result["avg_score"] == "85.5%"
            assert "calculation_time" in result
            assert result["calculation_time"].endswith("s")
    
    @pytest.mark.asyncio
    async def test_transparency_performance_check_degraded(self):
        """Test degraded transparency performance check."""
        with patch('app.services.optimized_health_checker.get_db') as mock_get_db:
            # Mock database session
            mock_db = Mock()
            mock_result = Mock()
            mock_result.companies_with_transparency = 5
            mock_result.overall_avg_score = 75.0
            mock_db.execute.return_value.fetchone.return_value = mock_result
            
            mock_get_db.return_value = iter([mock_db])
            
            # Mock slow query time
            with patch('time.time', side_effect=[0, 0.2]):  # 0.2 second query
                result = await self.health_checker._check_transparency_performance()
                
                assert result["status"] == "degraded"
                assert result["companies_tracked"] == 5
                assert result["avg_score"] == "75.0%"
    
    @pytest.mark.asyncio
    async def test_transparency_performance_check_error(self):
        """Test transparency performance check with error."""
        with patch('app.services.optimized_health_checker.get_db') as mock_get_db:
            # Mock database error
            mock_get_db.side_effect = Exception("Materialized view not found")
            
            result = await self.health_checker._check_transparency_performance()
            
            assert result["status"] == "unhealthy"
            assert "error" in result
            assert "Materialized view not found" in result["error"]
    
    @pytest.mark.asyncio
    async def test_transparency_performance_check_no_data(self):
        """Test transparency performance check with no data."""
        with patch('app.services.optimized_health_checker.get_db') as mock_get_db:
            # Mock database session with no results
            mock_db = Mock()
            mock_result = Mock()
            mock_result.companies_with_transparency = 0
            mock_result.overall_avg_score = None
            mock_db.execute.return_value.fetchone.return_value = mock_result
            
            mock_get_db.return_value = iter([mock_db])
            
            result = await self.health_checker._check_transparency_performance()
            
            assert result["status"] == "healthy"
            assert result["companies_tracked"] == 0
            assert result["avg_score"] == "0.0%"
    
    @pytest.mark.asyncio
    async def test_get_performance_metrics_success(self):
        """Test successful performance metrics retrieval."""
        with patch('app.services.optimized_health_checker.get_db') as mock_get_db:
            # Mock database session
            mock_db = Mock()
            mock_result = Mock()
            mock_result.metric_name = "test_metric"
            mock_result.avg_value = 1.5
            mock_result.max_value = 2.0
            mock_result.min_value = 1.0
            mock_result.sample_count = 10
            mock_db.execute.return_value.fetchall.return_value = [mock_result]
            
            mock_get_db.return_value = iter([mock_db])
            
            result = await self.health_checker.get_performance_metrics()
            
            assert result["status"] == "healthy"
            assert "metrics" in result
            assert "test_metric" in result["metrics"]
            assert result["metrics"]["test_metric"]["avg"] == "1.500"
            assert result["metrics"]["test_metric"]["max"] == "2.000"
            assert result["metrics"]["test_metric"]["min"] == "1.000"
            assert result["metrics"]["test_metric"]["samples"] == 10
    
    @pytest.mark.asyncio
    async def test_get_performance_metrics_error(self):
        """Test performance metrics retrieval with error."""
        with patch('app.services.optimized_health_checker.get_db') as mock_get_db:
            # Mock database error
            mock_get_db.side_effect = Exception("Performance metrics table not found")
            
            result = await self.health_checker.get_performance_metrics()
            
            assert result["status"] == "unhealthy"
            assert "error" in result
            assert "Performance metrics table not found" in result["error"]


class TestHealthCheckerPerformance:
    """Performance tests for health checker."""
    
    @pytest.mark.asyncio
    async def test_health_check_response_time(self):
        """Test that health check response time meets requirements."""
        health_checker = OptimizedHealthChecker()
        
        start_time = asyncio.get_event_loop().time()
        result = await health_checker.get_system_health()
        end_time = asyncio.get_event_loop().time()
        
        response_time = float(result["response_time"].replace("s", ""))
        
        # Health check should be fast (under 1 second)
        assert response_time < 1.0
        assert end_time - start_time < 1.0
    
    @pytest.mark.asyncio
    async def test_cached_response_time(self):
        """Test that cached health check is very fast."""
        health_checker = OptimizedHealthChecker()
        
        # First call (not cached)
        await health_checker.get_system_health()
        
        # Second call (cached)
        start_time = asyncio.get_event_loop().time()
        result = await health_checker.get_system_health()
        end_time = asyncio.get_event_loop().time()
        
        # Cached response should be very fast (under 10ms)
        assert end_time - start_time < 0.01
        assert result["cached"] is True
    
    def test_cache_duration_configuration(self):
        """Test that cache duration is properly configured."""
        health_checker = OptimizedHealthChecker()
        
        # Default cache duration should be 30 seconds
        assert health_checker.cache_duration == 30
        
        # Should be configurable
        health_checker.cache_duration = 60
        assert health_checker.cache_duration == 60


class TestGlobalHealthChecker:
    """Test the global health checker instance."""
    
    def test_global_instance_exists(self):
        """Test that global health checker instance exists."""
        assert health_checker is not None
        assert isinstance(health_checker, OptimizedHealthChecker)
    
    def test_global_instance_configuration(self):
        """Test that global instance is properly configured."""
        assert health_checker.cache_duration == 30
        assert health_checker._cached_result is None or isinstance(health_checker._cached_result, dict)
        assert health_checker._cache_timestamp is None or isinstance(health_checker._cache_timestamp, float)
    
    @pytest.mark.asyncio
    async def test_global_instance_functionality(self):
        """Test that global instance works correctly."""
        # Clear any existing cache
        health_checker._cached_result = None
        health_checker._cache_timestamp = None
        
        result = await health_checker.get_system_health()
        
        assert "status" in result
        assert "checks" in result
        assert "response_time" in result
        assert "timestamp" in result
        assert "cached" in result


class TestErrorHandling:
    """Test error handling in health checker."""
    
    @pytest.mark.asyncio
    async def test_database_connection_error(self):
        """Test handling of database connection errors."""
        health_checker = OptimizedHealthChecker()
        
        with patch('app.services.optimized_health_checker.get_db') as mock_get_db:
            mock_get_db.side_effect = Exception("Database connection failed")
            
            result = await health_checker._check_database_lightweight()
            
            assert result["status"] == "unhealthy"
            assert "error" in result
            assert len(result["error"]) <= 100  # Error should be truncated
    
    @pytest.mark.asyncio
    async def test_redis_connection_error(self):
        """Test handling of Redis connection errors."""
        health_checker = OptimizedHealthChecker()
        
        with patch('app.services.optimized_health_checker.get_redis') as mock_get_redis:
            mock_redis = AsyncMock()
            mock_redis.ping = AsyncMock(side_effect=Exception("Redis connection failed"))
            mock_get_redis.return_value = mock_redis
            
            result = await self.health_checker._check_redis_simple()
            
            assert result["status"] == "unhealthy"
            assert "error" in result
            assert len(result["error"]) <= 100  # Error should be truncated
    
    @pytest.mark.asyncio
    async def test_transparency_calculation_error(self):
        """Test handling of transparency calculation errors."""
        health_checker = OptimizedHealthChecker()
        
        with patch('app.services.optimized_health_checker.get_db') as mock_get_db:
            mock_get_db.side_effect = Exception("Materialized view not found")
            
            result = await health_checker._check_transparency_performance()
            
            assert result["status"] == "unhealthy"
            assert "error" in result
            assert len(result["error"]) <= 100  # Error should be truncated


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
