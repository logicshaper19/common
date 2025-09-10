"""
Integration tests for transparency API endpoints
Tests against the running server
"""
import pytest
import requests
import json
from uuid import uuid4


class TestTransparencyIntegration:
    """Integration tests for transparency endpoints."""
    
    BASE_URL = "http://localhost:8000"
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token for testing."""
        login_data = {
            "email": "elisha@common.co",
            "password": "password123"
        }
        
        response = requests.post(
            f"{self.BASE_URL}/api/v1/auth/login",
            json=login_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            return response.json()["access_token"]
        else:
            pytest.skip("Cannot authenticate - server may not be running")
    
    @pytest.fixture
    def auth_headers(self, auth_token):
        """Authentication headers for requests."""
        return {"Authorization": f"Bearer {auth_token}"}
    
    @pytest.fixture
    def test_company_id(self):
        """Test company ID."""
        return "ad172949-0036-4009-b00f-787a40f84699"
    
    def test_recent_improvements_endpoint(self, auth_headers, test_company_id):
        """Test recent improvements endpoint."""
        response = requests.get(
            f"{self.BASE_URL}/api/v1/transparency/v2/companies/{test_company_id}/recent-improvements",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Check response structure
        assert "success" in data
        assert "period_days" in data
        assert "improvements" in data
        assert "recent_actions" in data
        assert "summary" in data
        
        # Check data types
        assert isinstance(data["success"], bool)
        assert isinstance(data["period_days"], int)
        assert isinstance(data["improvements"], list)
        assert isinstance(data["recent_actions"], list)
        assert isinstance(data["summary"], dict)
        
        # Check that period_days is 30
        assert data["period_days"] == 30
    
    def test_transparency_dashboard_endpoint(self, auth_headers, test_company_id):
        """Test transparency dashboard endpoint."""
        response = requests.get(
            f"{self.BASE_URL}/api/v1/transparency/v2/companies/{test_company_id}/transparency-dashboard",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Check response structure
        required_fields = [
            "success", "company_id", "generated_at", "transparency_score",
            "metrics", "recent_improvements", "transparency_gaps",
            "supply_chain_stats", "compliance_status", "summary"
        ]
        
        for field in required_fields:
            assert field in data, f"Missing field: {field}"
        
        # Check transparency score structure
        score = data["transparency_score"]
        score_fields = ["score", "grade", "mill_transparency", "plantation_transparency", "gaps_penalty", "breakdown"]
        for field in score_fields:
            assert field in score, f"Missing transparency score field: {field}"
        
        # Check compliance status structure
        compliance = data["compliance_status"]
        assert "eudr_compliance" in compliance
        assert "uflpa_compliance" in compliance
        assert "overall_compliance_score" in compliance
        
        # Check that company_id matches
        assert data["company_id"] == test_company_id
    
    def test_unauthorized_access(self, test_company_id):
        """Test unauthorized access to endpoints."""
        # Test without auth header
        response = requests.get(
            f"{self.BASE_URL}/api/v1/transparency/v2/companies/{test_company_id}/recent-improvements"
        )
        assert response.status_code in [401, 403]  # Either is acceptable for missing auth

        # Test with invalid token
        headers = {"Authorization": "Bearer invalid_token"}
        response = requests.get(
            f"{self.BASE_URL}/api/v1/transparency/v2/companies/{test_company_id}/transparency-dashboard",
            headers=headers
        )
        assert response.status_code == 401
    
    def test_invalid_uuid(self, auth_headers):
        """Test endpoints with invalid UUID."""
        response = requests.get(
            f"{self.BASE_URL}/api/v1/transparency/v2/companies/invalid-uuid/recent-improvements",
            headers=auth_headers
        )
        assert response.status_code == 422
        
        data = response.json()
        assert "validation_errors" in data
    
    def test_nonexistent_company(self, auth_headers):
        """Test endpoints with non-existent company."""
        fake_company_id = str(uuid4())
        
        response = requests.get(
            f"{self.BASE_URL}/api/v1/transparency/v2/companies/{fake_company_id}/recent-improvements",
            headers=auth_headers
        )
        
        # Should still return 200 with empty data
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["improvements"]) == 0
    
    def test_response_times(self, auth_headers, test_company_id):
        """Test response times are reasonable."""
        import time
        
        # Test recent improvements response time
        start_time = time.time()
        response = requests.get(
            f"{self.BASE_URL}/api/v1/transparency/v2/companies/{test_company_id}/recent-improvements",
            headers=auth_headers
        )
        recent_improvements_time = time.time() - start_time
        
        assert response.status_code == 200
        assert recent_improvements_time < 2.0  # Should respond within 2 seconds
        
        # Test dashboard response time
        start_time = time.time()
        response = requests.get(
            f"{self.BASE_URL}/api/v1/transparency/v2/companies/{test_company_id}/transparency-dashboard",
            headers=auth_headers
        )
        dashboard_time = time.time() - start_time
        
        assert response.status_code == 200
        assert dashboard_time < 3.0  # Dashboard can take a bit longer
    
    def test_concurrent_requests(self, auth_headers, test_company_id):
        """Test handling of concurrent requests."""
        import concurrent.futures
        import threading
        
        def make_request():
            response = requests.get(
                f"{self.BASE_URL}/api/v1/transparency/v2/companies/{test_company_id}/recent-improvements",
                headers=auth_headers
            )
            return response.status_code
        
        # Make 5 concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request) for _ in range(5)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # All requests should succeed
        assert all(status == 200 for status in results)
    
    def test_data_consistency(self, auth_headers, test_company_id):
        """Test data consistency between endpoints."""
        # Get data from both endpoints
        improvements_response = requests.get(
            f"{self.BASE_URL}/api/v1/transparency/v2/companies/{test_company_id}/recent-improvements",
            headers=auth_headers
        )
        
        dashboard_response = requests.get(
            f"{self.BASE_URL}/api/v1/transparency/v2/companies/{test_company_id}/transparency-dashboard",
            headers=auth_headers
        )
        
        assert improvements_response.status_code == 200
        assert dashboard_response.status_code == 200
        
        improvements_data = improvements_response.json()
        dashboard_data = dashboard_response.json()
        
        # Check that recent improvements data is consistent
        # Dashboard should contain the same recent improvements (first 5)
        dashboard_improvements = dashboard_data["recent_improvements"]
        improvements_actions = improvements_data["recent_actions"]
        
        # If there are improvements, they should match
        if dashboard_improvements and improvements_actions:
            # First improvement in dashboard should match first in improvements
            assert dashboard_improvements[0]["type"] == improvements_actions[0]["type"]
    
    def test_openapi_documentation(self):
        """Test that endpoints are documented in OpenAPI."""
        response = requests.get(f"{self.BASE_URL}/openapi.json")
        assert response.status_code == 200
        
        openapi_data = response.json()
        paths = openapi_data.get("paths", {})
        
        # Check that our endpoints are documented
        recent_improvements_path = "/api/v1/transparency/v2/companies/{company_id}/recent-improvements"
        dashboard_path = "/api/v1/transparency/v2/companies/{company_id}/transparency-dashboard"
        
        assert recent_improvements_path in paths
        assert dashboard_path in paths
        
        # Check that GET method is documented
        assert "get" in paths[recent_improvements_path]
        assert "get" in paths[dashboard_path]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
