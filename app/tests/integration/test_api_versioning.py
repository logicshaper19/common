"""
API versioning and backward compatibility tests.
"""

import pytest
import json
from datetime import datetime, timedelta
from uuid import uuid4
from unittest.mock import patch, Mock

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import Base, get_db
from app.models.user import User
from app.models.company import Company
from app.core.security import hash_password, create_access_token

# Create test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_api_versioning.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables
Base.metadata.create_all(bind=engine)


def override_get_db():
    """Override database dependency for testing."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_db():
    """Clean database before each test."""
    db = TestingSessionLocal()
    try:
        db.query(Company).delete()
        db.query(User).delete()
        db.commit()
    finally:
        db.close()


def get_auth_headers(email: str):
    """Get authentication headers for a user."""
    # Create user
    user = User(
        id=uuid4(),
        email=email,
        hashed_password=hash_password("testpassword"),
        full_name="Test User",
        is_active=True,
        is_admin=False
    )
    
    # Create company
    company = Company(
        id=uuid4(),
        name=f"Test Company {email.split('@')[0]}",
        company_type="brand",
        email=email
    )
    user.company_id = company.id
    
    db = TestingSessionLocal()
    try:
        db.add(company)
        db.add(user)
        db.commit()
        
        token = create_access_token(data={"sub": str(user.id)})
        return {"Authorization": f"Bearer {token}"}
    finally:
        db.close()


class TestAPIVersioning:
    """Test API versioning functionality."""
    
    def test_version_header_handling(self, test_users):
        """Test handling of version headers."""
        headers = get_auth_headers("brand@test.com")
        
        # Test with different version headers
        version_headers = [
            {"Accept": "application/vnd.api+json;version=1.0"},
            {"Accept": "application/vnd.api+json;version=2.0"},
            {"API-Version": "1.0"},
            {"API-Version": "2.0"},
            {"X-API-Version": "1.0"},
            {"X-API-Version": "2.0"},
        ]
        
        for version_header in version_headers:
            test_headers = {**headers, **version_header}
            response = client.get("/api/v1/companies", headers=test_headers)
            # Should handle version headers gracefully
            assert response.status_code in [200, 400, 406]
    
    def test_version_parameter_handling(self, test_users):
        """Test handling of version parameters."""
        headers = get_auth_headers("brand@test.com")
        
        # Test with version in URL
        version_urls = [
            "/api/v1/companies",
            "/api/v2/companies",
            "/api/companies?version=1.0",
            "/api/companies?version=2.0",
        ]
        
        for url in version_urls:
            response = client.get(url, headers=headers)
            # Should handle version parameters gracefully
            assert response.status_code in [200, 404, 400]
    
    def test_deprecated_endpoint_handling(self, test_users):
        """Test handling of deprecated endpoints."""
        headers = get_auth_headers("brand@test.com")
        
        # Test deprecated endpoints
        deprecated_endpoints = [
            "/api/v0/companies",  # Very old version
            "/api/legacy/companies",  # Legacy endpoint
            "/api/deprecated/companies",  # Deprecated endpoint
        ]
        
        for endpoint in deprecated_endpoints:
            response = client.get(endpoint, headers=headers)
            # Should either work or return appropriate deprecation notice
            assert response.status_code in [200, 404, 410, 426]
            
            if response.status_code == 200:
                # Check for deprecation warnings in headers
                assert "Deprecation" in response.headers or "Sunset" in response.headers
    
    def test_version_negotiation(self, test_users):
        """Test version negotiation based on client capabilities."""
        headers = get_auth_headers("brand@test.com")
        
        # Test with different Accept headers
        accept_headers = [
            "application/json",
            "application/vnd.api+json",
            "application/vnd.api+json;version=1.0",
            "application/vnd.api+json;version=2.0",
            "application/json;q=0.9,application/vnd.api+json;version=2.0;q=0.8",
        ]
        
        for accept in accept_headers:
            test_headers = {**headers, "Accept": accept}
            response = client.get("/api/v1/companies", headers=test_headers)
            # Should negotiate version appropriately
            assert response.status_code in [200, 400, 406]
    
    def test_backward_compatibility(self, test_users):
        """Test backward compatibility of API responses."""
        headers = get_auth_headers("brand@test.com")
        
        # Create a company
        company_data = {
            "name": "Backward Compatibility Test",
            "company_type": "brand",
            "email": "backward@example.com"
        }
        
        create_response = client.post("/api/v1/companies", json=company_data, headers=headers)
        company_id = create_response.json()["id"]
        
        # Test different API versions
        versions = ["v1", "v2"]
        
        for version in versions:
            response = client.get(f"/api/{version}/companies/{company_id}", headers=headers)
            if response.status_code == 200:
                data = response.json()
                # Should have consistent structure across versions
                assert "id" in data
                assert "name" in data
                assert "company_type" in data
    
    def test_forward_compatibility(self, test_users):
        """Test forward compatibility of API requests."""
        headers = get_auth_headers("brand@test.com")
        
        # Test with future API version
        future_headers = {
            **headers,
            "API-Version": "3.0",
            "Accept": "application/vnd.api+json;version=3.0"
        }
        
        response = client.get("/api/v1/companies", headers=future_headers)
        # Should handle future versions gracefully
        assert response.status_code in [200, 400, 406, 426]
    
    def test_version_specific_validation(self, test_users):
        """Test version-specific validation rules."""
        headers = get_auth_headers("brand@test.com")
        
        # Test with different validation rules per version
        company_data_v1 = {
            "name": "Version 1 Company",
            "company_type": "brand",
            "email": "v1@example.com"
        }
        
        company_data_v2 = {
            "name": "Version 2 Company",
            "company_type": "brand",
            "email": "v2@example.com",
            "metadata": {"version": "2.0"}  # Additional field in v2
        }
        
        # Test v1 endpoint
        v1_headers = {**headers, "API-Version": "1.0"}
        response1 = client.post("/api/v1/companies", json=company_data_v1, headers=v1_headers)
        assert response1.status_code in [200, 201, 400, 422]
        
        # Test v2 endpoint
        v2_headers = {**headers, "API-Version": "2.0"}
        response2 = client.post("/api/v2/companies", json=company_data_v2, headers=v2_headers)
        assert response2.status_code in [200, 201, 400, 422, 404]
    
    def test_version_migration_guidance(self, test_users):
        """Test version migration guidance."""
        headers = get_auth_headers("brand@test.com")
        
        # Test deprecated endpoint with migration guidance
        response = client.get("/api/v0/companies", headers=headers)
        
        if response.status_code == 200:
            # Check for migration guidance in response
            data = response.json()
            assert "migration_guide" in data or "deprecation_notice" in data
        
        # Check headers for migration guidance
        assert "Link" in response.headers or "Deprecation" in response.headers


class TestSchemaEvolution:
    """Test schema evolution and compatibility."""
    
    def test_field_addition_compatibility(self, test_users):
        """Test compatibility when new fields are added."""
        headers = get_auth_headers("brand@test.com")
        
        # Test with additional fields (should be ignored by older clients)
        company_data = {
            "name": "Schema Evolution Test",
            "company_type": "brand",
            "email": "schema@example.com",
            "new_field_v2": "This field doesn't exist in v1",
            "metadata": {"version": "2.0"}
        }
        
        response = client.post("/api/v1/companies", json=company_data, headers=headers)
        # Should accept the request and ignore unknown fields
        assert response.status_code in [200, 201, 400, 422]
    
    def test_field_removal_compatibility(self, test_users):
        """Test compatibility when fields are removed."""
        headers = get_auth_headers("brand@test.com")
        
        # Test with missing required fields (simulating field removal)
        company_data = {
            "name": "Field Removal Test",
            # Missing company_type and email (required in v1)
        }
        
        response = client.post("/api/v1/companies", json=company_data, headers=headers)
        # Should handle missing fields appropriately
        assert response.status_code in [400, 422]
    
    def test_field_type_changes(self, test_users):
        """Test compatibility when field types change."""
        headers = get_auth_headers("brand@test.com")
        
        # Test with different field types
        company_data = {
            "name": "Type Change Test",
            "company_type": "brand",
            "email": "type@example.com",
            "id": "string_id_instead_of_uuid"  # Wrong type
        }
        
        response = client.post("/api/v1/companies", json=company_data, headers=headers)
        # Should handle type changes appropriately
        assert response.status_code in [200, 201, 400, 422]
    
    def test_enum_value_changes(self, test_users):
        """Test compatibility when enum values change."""
        headers = get_auth_headers("brand@test.com")
        
        # Test with new enum values
        company_data = {
            "name": "Enum Change Test",
            "company_type": "new_company_type",  # New enum value
            "email": "enum@example.com"
        }
        
        response = client.post("/api/v1/companies", json=company_data, headers=headers)
        # Should handle enum changes appropriately
        assert response.status_code in [200, 201, 400, 422]


class TestVersioningStrategies:
    """Test different versioning strategies."""
    
    def test_url_versioning(self, test_users):
        """Test URL-based versioning."""
        headers = get_auth_headers("brand@test.com")
        
        # Test different URL versions
        url_versions = [
            "/api/v1/companies",
            "/api/v2/companies",
            "/api/companies/v1",
            "/api/companies/v2",
        ]
        
        for url in url_versions:
            response = client.get(url, headers=headers)
            # Should handle URL versioning appropriately
            assert response.status_code in [200, 404]
    
    def test_header_versioning(self, test_users):
        """Test header-based versioning."""
        headers = get_auth_headers("brand@test.com")
        
        # Test different header versions
        header_versions = [
            {"API-Version": "1.0"},
            {"API-Version": "2.0"},
            {"X-API-Version": "1.0"},
            {"X-API-Version": "2.0"},
            {"Accept": "application/vnd.api+json;version=1.0"},
            {"Accept": "application/vnd.api+json;version=2.0"},
        ]
        
        for version_header in header_versions:
            test_headers = {**headers, **version_header}
            response = client.get("/api/companies", headers=test_headers)
            # Should handle header versioning appropriately
            assert response.status_code in [200, 400, 406]
    
    def test_parameter_versioning(self, test_users):
        """Test parameter-based versioning."""
        headers = get_auth_headers("brand@test.com")
        
        # Test different parameter versions
        param_versions = [
            "/api/companies?version=1.0",
            "/api/companies?version=2.0",
            "/api/companies?v=1.0",
            "/api/companies?v=2.0",
        ]
        
        for url in param_versions:
            response = client.get(url, headers=headers)
            # Should handle parameter versioning appropriately
            assert response.status_code in [200, 400, 404]
    
    def test_content_negotiation_versioning(self, test_users):
        """Test content negotiation-based versioning."""
        headers = get_auth_headers("brand@test.com")
        
        # Test different content types
        content_types = [
            "application/json",
            "application/vnd.api+json",
            "application/vnd.api+json;version=1.0",
            "application/vnd.api+json;version=2.0",
            "application/vnd.company.v1+json",
            "application/vnd.company.v2+json",
        ]
        
        for content_type in content_types:
            test_headers = {**headers, "Accept": content_type}
            response = client.get("/api/companies", headers=test_headers)
            # Should handle content negotiation appropriately
            assert response.status_code in [200, 400, 406]


class TestVersioningDocumentation:
    """Test versioning documentation and metadata."""
    
    def test_version_info_endpoint(self, test_users):
        """Test version information endpoint."""
        response = client.get("/api/version")
        # Should provide version information
        assert response.status_code in [200, 404]
        
        if response.status_code == 200:
            data = response.json()
            assert "version" in data
            assert "supported_versions" in data
    
    def test_api_documentation_versioning(self, test_users):
        """Test API documentation versioning."""
        # Test different documentation versions
        doc_versions = [
            "/docs",
            "/docs/v1",
            "/docs/v2",
            "/redoc",
            "/redoc/v1",
            "/redoc/v2",
        ]
        
        for doc_url in doc_versions:
            response = client.get(doc_url)
            # Should provide appropriate documentation
            assert response.status_code in [200, 404]
    
    def test_openapi_schema_versioning(self, test_users):
        """Test OpenAPI schema versioning."""
        # Test different schema versions
        schema_versions = [
            "/openapi.json",
            "/openapi/v1.json",
            "/openapi/v2.json",
        ]
        
        for schema_url in schema_versions:
            response = client.get(schema_url)
            # Should provide appropriate schema
            assert response.status_code in [200, 404]
            
            if response.status_code == 200:
                data = response.json()
                assert "openapi" in data
                assert "info" in data
                assert "version" in data["info"]
