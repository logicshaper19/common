"""
Test API response format standardization.

This test suite verifies that all API endpoints return responses in the
standardized format defined in app.core.response_models.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from uuid import uuid4
import json

from app.main import app
from app.core.database import get_db
from app.models.user import User
from app.models.company import Company
from app.models.product import Product
from app.core.security import create_access_token


def test_companies_list_response_format(client, simple_scenario):
    """Test that companies list endpoint returns standardized format."""
    # Get a user from the scenario
    brand_company = next(c for c in simple_scenario.companies if c.company_type == "brand")
    brand_user = next(u for u in simple_scenario.users if u.company_id == brand_company.id)

    # Create auth token
    auth_token = create_access_token(data={"sub": str(brand_user.id)})
    headers = {"Authorization": f"Bearer {auth_token}"}

    response = client.get("/api/companies/", headers=headers)

    assert response.status_code == 200
    data = response.json()

    # Check standardized response structure
    assert "success" in data
    assert "status" in data
    assert "message" in data
    assert "data" in data
    assert "pagination" in data
    assert "request_id" in data
    assert "timestamp" in data

    # Check response values
    assert data["success"] is True
    assert data["status"] == "success"
    assert isinstance(data["data"], list)

    # Check pagination structure
    pagination = data["pagination"]
    assert "page" in pagination
    assert "per_page" in pagination
    assert "total" in pagination
    assert "total_pages" in pagination
    assert "has_next" in pagination
    assert "has_prev" in pagination


def test_company_detail_response_format(client, simple_scenario):
    """Test that company detail endpoint returns standardized format."""
    # Get a user from the scenario
    brand_company = next(c for c in simple_scenario.companies if c.company_type == "brand")
    brand_user = next(u for u in simple_scenario.users if u.company_id == brand_company.id)

    # Create auth token
    auth_token = create_access_token(data={"sub": str(brand_user.id)})
    headers = {"Authorization": f"Bearer {auth_token}"}

    response = client.get(f"/api/companies/{brand_company.id}", headers=headers)

    assert response.status_code == 200
    data = response.json()

    # Check standardized response structure
    assert "success" in data
    assert "status" in data
    assert "message" in data
    assert "data" in data
    assert "request_id" in data
    assert "timestamp" in data

    # Check response values
    assert data["success"] is True
    assert data["status"] == "success"
    assert isinstance(data["data"], dict)

    # Check company data structure
    company_data = data["data"]
    assert "id" in company_data
    assert "name" in company_data
    assert "company_type" in company_data
    assert "created_at" in company_data
    assert "updated_at" in company_data


def test_products_list_response_format(client, simple_scenario):
    """Test that products list endpoint returns standardized format."""
    # Get a user from the scenario
    brand_company = next(c for c in simple_scenario.companies if c.company_type == "brand")
    brand_user = next(u for u in simple_scenario.users if u.company_id == brand_company.id)

    # Create auth token
    auth_token = create_access_token(data={"sub": str(brand_user.id)})
    headers = {"Authorization": f"Bearer {auth_token}"}

    response = client.get("/api/products/", headers=headers)

    assert response.status_code == 200
    data = response.json()

    # Check standardized response structure
    assert "success" in data
    assert "status" in data
    assert "message" in data
    assert "data" in data
    assert "pagination" in data
    assert "request_id" in data
    assert "timestamp" in data

    # Check response values
    assert data["success"] is True
    assert data["status"] == "success"
    assert isinstance(data["data"], list)
    
    def test_companies_list_response_format(self):
        """Test that companies list endpoint returns standardized format."""
        response = self.client.get("/api/companies/", headers=self.headers)
        
        assert response.status_code == 200
        data = response.json()
        
        # Check standardized response structure
        assert "success" in data
        assert "status" in data
        assert "message" in data
        assert "data" in data
        assert "pagination" in data
        assert "request_id" in data
        assert "timestamp" in data
        
        # Check response values
        assert data["success"] is True
        assert data["status"] == "success"
        assert isinstance(data["data"], list)
        
        # Check pagination structure
        pagination = data["pagination"]
        assert "page" in pagination
        assert "per_page" in pagination
        assert "total" in pagination
        assert "total_pages" in pagination
        assert "has_next" in pagination
        assert "has_prev" in pagination
    
    def test_company_detail_response_format(self):
        """Test that company detail endpoint returns standardized format."""
        response = self.client.get(f"/api/companies/{self.test_company.id}", headers=self.headers)
        
        assert response.status_code == 200
        data = response.json()
        
        # Check standardized response structure
        assert "success" in data
        assert "status" in data
        assert "message" in data
        assert "data" in data
        assert "request_id" in data
        assert "timestamp" in data
        
        # Check response values
        assert data["success"] is True
        assert data["status"] == "success"
        assert isinstance(data["data"], dict)
        
        # Check company data structure
        company_data = data["data"]
        assert "id" in company_data
        assert "name" in company_data
        assert "company_type" in company_data
        assert "created_at" in company_data
        assert "updated_at" in company_data
    
    def test_products_list_response_format(self):
        """Test that products list endpoint returns standardized format."""
        response = self.client.get("/api/products/", headers=self.headers)
        
        assert response.status_code == 200
        data = response.json()
        
        # Check standardized response structure
        assert "success" in data
        assert "status" in data
        assert "message" in data
        assert "data" in data
        assert "pagination" in data
        assert "request_id" in data
        assert "timestamp" in data
        
        # Check response values
        assert data["success"] is True
        assert data["status"] == "success"
        assert isinstance(data["data"], list)
    
    def test_error_response_format(self):
        """Test that error responses follow standardized format."""
        # Test 404 error
        response = self.client.get(f"/api/companies/{uuid4()}", headers=self.headers)
        
        assert response.status_code == 404
        data = response.json()
        
        # Check error response structure
        assert "success" in data
        assert "status" in data
        assert "message" in data
        assert "errors" in data
        assert "request_id" in data
        assert "timestamp" in data
        
        # Check error response values
        assert data["success"] is False
        assert data["status"] == "error"
        assert isinstance(data["errors"], list)
        assert len(data["errors"]) > 0
    
    def test_unauthorized_response_format(self):
        """Test that unauthorized responses follow standardized format."""
        # Test without auth token
        response = self.client.get("/api/companies/")
        
        assert response.status_code == 401
        data = response.json()
        
        # Check error response structure
        assert "detail" in data  # FastAPI default for 401
    
    def test_validation_error_response_format(self):
        """Test that validation errors follow standardized format."""
        # Test invalid product creation
        invalid_product = {
            "name": "",  # Invalid: empty name
            "category": "invalid_category"  # Invalid category
        }
        
        response = self.client.post("/api/products/", json=invalid_product, headers=self.headers)
        
        assert response.status_code == 422
        data = response.json()
        
        # FastAPI validation errors have a specific format
        assert "detail" in data
        assert isinstance(data["detail"], list)
    
    def test_response_consistency_across_endpoints(self):
        """Test that all successful responses have consistent structure."""
        endpoints_to_test = [
            "/api/companies/",
            "/api/products/",
        ]
        
        for endpoint in endpoints_to_test:
            response = self.client.get(endpoint, headers=self.headers)
            
            if response.status_code == 200:
                data = response.json()
                
                # All successful responses should have these fields
                required_fields = ["success", "status", "message", "request_id", "timestamp"]
                for field in required_fields:
                    assert field in data, f"Missing {field} in {endpoint} response"
                
                # Success responses should have success=True and status="success"
                assert data["success"] is True, f"success should be True for {endpoint}"
                assert data["status"] == "success", f"status should be 'success' for {endpoint}"
    
    def test_timestamp_format(self):
        """Test that timestamps are in ISO format."""
        response = self.client.get("/api/companies/", headers=self.headers)
        
        assert response.status_code == 200
        data = response.json()
        
        # Check timestamp format (should be ISO 8601)
        timestamp = data["timestamp"]
        assert "T" in timestamp  # ISO format contains 'T'
        assert timestamp.endswith("Z") or "+" in timestamp or "-" in timestamp[-6:]  # Timezone info
    
    def test_request_id_uniqueness(self):
        """Test that request IDs are unique across requests."""
        response1 = self.client.get("/api/companies/", headers=self.headers)
        response2 = self.client.get("/api/companies/", headers=self.headers)
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        data1 = response1.json()
        data2 = response2.json()
        
        # Request IDs should be different
        assert data1["request_id"] != data2["request_id"]
    
    def test_pagination_metadata_accuracy(self):
        """Test that pagination metadata is accurate."""
        # Test with specific pagination parameters
        response = self.client.get("/api/companies/?page=1&per_page=5", headers=self.headers)
        
        assert response.status_code == 200
        data = response.json()
        
        pagination = data["pagination"]
        
        # Check pagination values
        assert pagination["page"] == 1
        assert pagination["per_page"] == 5
        assert pagination["total"] >= 0
        assert pagination["total_pages"] >= 0
        
        # Check has_next and has_prev logic
        if pagination["total"] > 5:
            assert pagination["has_next"] is True
        else:
            assert pagination["has_next"] is False
        
        assert pagination["has_prev"] is False  # First page should not have previous
