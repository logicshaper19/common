"""
Performance tests for Dashboard V2 implementation
Tests response times, concurrent requests, and load handling
"""
import pytest
import time
import asyncio
import concurrent.futures
from fastapi.testclient import TestClient
from typing import List, Dict, Any

from app.main import app


class TestDashboardV2Performance:
    """Performance tests for Dashboard V2 system"""
    
    def test_dashboard_config_response_time(self, brand_user_client):
        """Test that dashboard config endpoint responds quickly"""
        start_time = time.time()
        response = brand_user_client.get("/api/v2/dashboard/config")
        response_time = time.time() - start_time
        
        assert response.status_code == 200
        assert response_time < 1.0  # Should respond within 1 second
        
        print(f"Dashboard config response time: {response_time:.3f}s")
    
    def test_dashboard_metrics_response_time(self, brand_user_client):
        """Test that dashboard metrics endpoint responds quickly"""
        start_time = time.time()
        response = brand_user_client.get("/api/v2/dashboard/metrics/brand")
        response_time = time.time() - start_time
        
        assert response.status_code == 200
        assert response_time < 2.0  # Should respond within 2 seconds
        
        print(f"Dashboard metrics response time: {response_time:.3f}s")
    
    def test_feature_flags_response_time(self, brand_user_client):
        """Test that feature flags endpoint responds quickly"""
        start_time = time.time()
        response = brand_user_client.get("/api/v2/dashboard/feature-flags")
        response_time = time.time() - start_time
        
        assert response.status_code == 200
        assert response_time < 0.5  # Should respond within 500ms
        
        print(f"Feature flags response time: {response_time:.3f}s")
    
    def test_concurrent_dashboard_requests(self, brand_user_client):
        """Test dashboard handles concurrent requests efficiently"""
        
        def make_request():
            return brand_user_client.get("/api/v2/dashboard/config")
        
        # Make 10 concurrent requests
        start_time = time.time()
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        total_time = time.time() - start_time
        
        # All requests should succeed
        for response in results:
            assert response.status_code == 200
        
        # Total time should be reasonable (not much more than single request)
        assert total_time < 5.0  # 10 concurrent requests in under 5 seconds
        
        print(f"10 concurrent requests completed in: {total_time:.3f}s")
    
    def test_metrics_data_size(self, brand_user_client):
        """Test that metrics response size is reasonable"""
        response = brand_user_client.get("/api/v2/dashboard/metrics/brand")
        assert response.status_code == 200
        
        # Check response size
        content_length = len(response.content)
        assert content_length < 100_000  # Should be less than 100KB
        
        # Check JSON structure efficiency
        data = response.json()
        assert isinstance(data, dict)
        assert len(data) > 0  # Should have actual data
        
        print(f"Metrics response size: {content_length} bytes")
    
    def test_dashboard_memory_efficiency(self, brand_user_client):
        """Test that dashboard endpoints don't cause memory leaks"""
        import psutil
        import os
        
        # Get initial memory usage
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # Make multiple requests
        for _ in range(50):
            response = brand_user_client.get("/api/v2/dashboard/config")
            assert response.status_code == 200
        
        # Check memory usage after requests
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be minimal (less than 50MB)
        assert memory_increase < 50_000_000
        
        print(f"Memory increase after 50 requests: {memory_increase / 1024 / 1024:.2f}MB")


class TestDashboardV2LoadTesting:
    """Load testing for Dashboard V2 under stress"""
    
    def test_sustained_load_dashboard_config(self, brand_user_client):
        """Test dashboard config under sustained load"""
        success_count = 0
        error_count = 0
        total_time = 0
        
        # Make 100 requests and measure performance
        for i in range(100):
            start_time = time.time()
            try:
                response = brand_user_client.get("/api/v2/dashboard/config")
                request_time = time.time() - start_time
                total_time += request_time
                
                if response.status_code == 200:
                    success_count += 1
                else:
                    error_count += 1
                    
            except Exception as e:
                error_count += 1
                print(f"Request {i} failed: {e}")
        
        # Calculate metrics
        success_rate = success_count / 100
        average_response_time = total_time / 100
        
        # Assertions
        assert success_rate >= 0.95  # At least 95% success rate
        assert average_response_time < 1.0  # Average response under 1 second
        assert error_count < 5  # Less than 5% errors
        
        print(f"Load test results:")
        print(f"  Success rate: {success_rate:.2%}")
        print(f"  Average response time: {average_response_time:.3f}s")
        print(f"  Error count: {error_count}")
    
    def test_mixed_endpoint_load(self, brand_user_client):
        """Test mixed load across different dashboard endpoints"""
        endpoints = [
            "/api/v2/dashboard/config",
            "/api/v2/dashboard/feature-flags",
            "/api/v2/dashboard/metrics/brand"
        ]
        
        results = {endpoint: {"success": 0, "error": 0, "total_time": 0} for endpoint in endpoints}
        
        # Make requests to different endpoints
        for i in range(60):  # 20 requests per endpoint
            endpoint = endpoints[i % len(endpoints)]
            
            start_time = time.time()
            try:
                response = brand_user_client.get(endpoint)
                request_time = time.time() - start_time
                results[endpoint]["total_time"] += request_time
                
                if response.status_code == 200:
                    results[endpoint]["success"] += 1
                else:
                    results[endpoint]["error"] += 1
                    
            except Exception as e:
                results[endpoint]["error"] += 1
                print(f"Request to {endpoint} failed: {e}")
        
        # Verify all endpoints perform well
        for endpoint, metrics in results.items():
            success_rate = metrics["success"] / 20
            avg_time = metrics["total_time"] / 20
            
            assert success_rate >= 0.90  # At least 90% success rate
            assert avg_time < 2.0  # Average response under 2 seconds
            
            print(f"{endpoint}: {success_rate:.2%} success, {avg_time:.3f}s avg")


class TestDashboardV2Scalability:
    """Test Dashboard V2 scalability characteristics"""
    
    def test_user_scaling(self, brand_user_client, processor_user_client):
        """Test dashboard performance with multiple user types"""
        
        def test_user_workflow(client, dashboard_type):
            """Test complete workflow for a user type"""
            start_time = time.time()
            
            # Get config
            config_response = client.get("/api/v2/dashboard/config")
            assert config_response.status_code == 200
            
            # Get metrics
            metrics_response = client.get(f"/api/v2/dashboard/metrics/{dashboard_type}")
            assert metrics_response.status_code == 200
            
            return time.time() - start_time
        
        # Test both user types concurrently
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            futures = [
                executor.submit(test_user_workflow, brand_user_client, "brand"),
                executor.submit(test_user_workflow, brand_user_client, "brand"),
                executor.submit(test_user_workflow, processor_user_client, "processor"),
                executor.submit(test_user_workflow, processor_user_client, "processor"),
            ]
            
            times = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # All workflows should complete reasonably quickly
        for workflow_time in times:
            assert workflow_time < 3.0  # Each workflow under 3 seconds
        
        avg_time = sum(times) / len(times)
        print(f"Average workflow time with concurrent users: {avg_time:.3f}s")
    
    def test_data_volume_scaling(self, brand_user_client):
        """Test dashboard performance doesn't degrade with data volume"""
        # This test assumes the simple_scenario has created some data
        # In a real scenario, you'd create varying amounts of test data
        
        response = brand_user_client.get("/api/v2/dashboard/metrics/brand")
        assert response.status_code == 200
        
        data = response.json()
        
        # Verify the response contains data and is structured properly
        assert "supply_chain_overview" in data
        assert "supplier_portfolio" in data
        assert "recent_activity" in data
        
        # Response should be fast even with data
        start_time = time.time()
        response = brand_user_client.get("/api/v2/dashboard/metrics/brand")
        response_time = time.time() - start_time
        
        assert response.status_code == 200
        assert response_time < 2.0  # Should still be fast with data
        
        print(f"Metrics response time with data: {response_time:.3f}s")
