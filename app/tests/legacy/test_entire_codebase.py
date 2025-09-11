"""
Comprehensive integration tests for the entire codebase
Tests all major API endpoints across the application
"""
import pytest
import requests
import json
import time
import concurrent.futures
from uuid import uuid4


class TestEntireCodebase:
    """Comprehensive tests for all API endpoints."""
    
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
    
    @pytest.fixture
    def test_user_id(self):
        """Test user ID."""
        return "659e5398-ac98-4d28-be64-e53bed8710dd"
    
    # ===== AUTHENTICATION & USER MANAGEMENT =====
    
    def test_auth_login(self):
        """Test login endpoint."""
        login_data = {
            "email": "elisha@common.co",
            "password": "password123"
        }
        
        response = requests.post(
            f"{self.BASE_URL}/api/v1/auth/login",
            json=login_data,
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["access_token"] is not None
    
    def test_auth_me(self, auth_headers):
        """Test current user endpoint."""
        response = requests.get(
            f"{self.BASE_URL}/api/v1/auth/me",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "elisha@common.co"
        assert "id" in data
        assert "full_name" in data
    
    def test_auth_user_by_id(self, auth_headers, test_user_id):
        """Test get user by ID endpoint."""
        response = requests.get(
            f"{self.BASE_URL}/api/v1/auth/users/{test_user_id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["full_name"] == "Elisha"
        assert "email" in data
    
    # ===== COMPANY MANAGEMENT =====
    
    def test_companies_get_by_id(self, auth_headers, test_company_id):
        """Test get company by ID."""
        response = requests.get(
            f"{self.BASE_URL}/api/v1/companies/{test_company_id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Common Platform"
        assert "id" in data
        assert "company_type" in data
    
    def test_admin_companies_get_by_id(self, auth_headers, test_company_id):
        """Test admin companies endpoint."""
        response = requests.get(
            f"{self.BASE_URL}/api/v1/admin/companies/{test_company_id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["company_type"] == "trader_aggregator"
        assert "name" in data
    
    # ===== PURCHASE ORDERS =====
    
    def test_purchase_orders_list(self, auth_headers):
        """Test list purchase orders."""
        response = requests.get(
            f"{self.BASE_URL}/api/v1/purchase-orders/",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "page" in data
        assert "per_page" in data
        assert "purchase_orders" in data
        assert data["total"] == 0  # No purchase orders in test data
    
    def test_purchase_orders_pagination(self, auth_headers):
        """Test purchase orders pagination."""
        response = requests.get(
            f"{self.BASE_URL}/api/v1/purchase-orders/?page=1&per_page=10",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1
        assert data["per_page"] == 10
    
    # ===== PRODUCTS =====
    
    def test_products_list(self, auth_headers):
        """Test list products."""
        response = requests.get(
            f"{self.BASE_URL}/api/v1/products/",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "products" in data
        assert data["total"] == 33  # 33 products in test data
    
    def test_products_pagination(self, auth_headers):
        """Test products pagination."""
        response = requests.get(
            f"{self.BASE_URL}/api/v1/products/?page=1&per_page=5",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["products"]) == 5
        assert data["page"] == 1
        assert data["per_page"] == 5
    
    # ===== DOCUMENTS =====
    
    def test_documents_list(self, auth_headers):
        """Test list documents."""
        response = requests.get(
            f"{self.BASE_URL}/api/v1/documents/",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "documents" in data
        assert data["total"] == 1  # 1 document in test data
    
    def test_documents_upload_endpoint_exists(self, auth_headers):
        """Test documents upload endpoint exists (without actually uploading)."""
        # Just test that the endpoint exists by checking OPTIONS or GET
        response = requests.options(
            f"{self.BASE_URL}/api/v1/documents/upload",
            headers=auth_headers
        )

        # Should not return 404 (endpoint exists)
        assert response.status_code != 404
    
    # ===== BUSINESS RELATIONSHIPS =====
    
    def test_business_relationships_list(self, auth_headers):
        """Test list business relationships."""
        response = requests.get(
            f"{self.BASE_URL}/api/v1/business-relationships/",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert data["total"] == 0  # No business relationships in test data
    
    def test_business_relationships_pagination(self, auth_headers):
        """Test business relationships pagination."""
        response = requests.get(
            f"{self.BASE_URL}/api/v1/business-relationships/?page=1&per_page=10",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1
    
    # ===== BATCHES =====
    
    def test_batches_list(self, auth_headers):
        """Test list batches."""
        response = requests.get(
            f"{self.BASE_URL}/api/v1/batches/",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert data["total"] == 0  # No batches in test data
    
    def test_batches_pagination(self, auth_headers):
        """Test batches pagination."""
        response = requests.get(
            f"{self.BASE_URL}/api/v1/batches/?page=1&per_page=10",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1
    
    # ===== TRANSPARENCY APIs =====
    
    def test_transparency_recent_improvements(self, auth_headers, test_company_id):
        """Test transparency recent improvements endpoint."""
        response = requests.get(
            f"{self.BASE_URL}/api/v1/transparency/v2/companies/{test_company_id}/recent-improvements",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "period_days" in data
        assert "improvements" in data
        assert "recent_actions" in data
        assert data["period_days"] == 30
    
    def test_transparency_dashboard(self, auth_headers, test_company_id):
        """Test transparency dashboard endpoint."""
        response = requests.get(
            f"{self.BASE_URL}/api/v1/transparency/v2/companies/{test_company_id}/transparency-dashboard",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "transparency_score" in data
        assert "compliance_status" in data
        assert "supply_chain_stats" in data
    
    def test_transparency_metrics(self, auth_headers, test_company_id):
        """Test transparency metrics endpoint."""
        response = requests.get(
            f"{self.BASE_URL}/api/v1/transparency/v2/companies/{test_company_id}/metrics",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    # ===== ERROR HANDLING & EDGE CASES =====

    def test_invalid_uuid_format(self, auth_headers):
        """Test invalid UUID format handling."""
        response = requests.get(
            f"{self.BASE_URL}/api/v1/companies/invalid-uuid",
            headers=auth_headers
        )

        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
        assert data["detail"] == "Request validation failed"

    def test_nonexistent_resource(self, auth_headers):
        """Test non-existent resource handling."""
        fake_company_id = str(uuid4())
        response = requests.get(
            f"{self.BASE_URL}/api/v1/companies/{fake_company_id}",
            headers=auth_headers
        )

        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "Company not found"

    def test_unauthorized_access(self):
        """Test unauthorized access."""
        response = requests.get(
            f"{self.BASE_URL}/api/v1/auth/me"
        )

        assert response.status_code == 403
        data = response.json()
        assert data["detail"] == "Not authenticated"

    def test_invalid_token(self):
        """Test invalid token handling."""
        headers = {"Authorization": "Bearer invalid_token"}
        response = requests.get(
            f"{self.BASE_URL}/api/v1/auth/me",
            headers=headers
        )

        assert response.status_code == 401
        data = response.json()
        assert data["detail"] == "Could not validate credentials"

    # ===== PERFORMANCE TESTS =====

    def test_response_times(self, auth_headers):
        """Test response times are reasonable."""
        start_time = time.time()
        response = requests.get(
            f"{self.BASE_URL}/api/v1/products/",
            headers=auth_headers
        )
        response_time = time.time() - start_time

        assert response.status_code == 200
        assert response_time < 2.0  # Should respond within 2 seconds

    def test_concurrent_requests(self, auth_headers):
        """Test handling of concurrent requests."""
        def make_request():
            response = requests.get(
                f"{self.BASE_URL}/api/v1/products/",
                headers=auth_headers
            )
            return response.status_code

        # Make 5 concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request) for _ in range(5)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]

        # All requests should succeed
        assert all(status == 200 for status in results)

    def test_large_pagination(self, auth_headers):
        """Test large pagination requests."""
        response = requests.get(
            f"{self.BASE_URL}/api/v1/products/?page=1&per_page=50",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        # Should return all 33 products since we requested 50
        assert len(data["products"]) == 33


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
