"""
Tests for super admin functionality.
"""
import pytest
from fastapi.testclient import TestClient


def test_super_admin_can_access_admin_endpoints(client, test_super_admin_user, auth_headers):
    """Test that super admin can access admin endpoints."""
    headers = auth_headers(test_super_admin_user.email)
    
    # Test accessing admin companies endpoint
    response = client.get("/api/v1/admin/companies", headers=headers)
    assert response.status_code == 200
    
    # Test accessing admin users endpoint
    response = client.get("/api/v1/admin/users", headers=headers)
    assert response.status_code == 200


def test_regular_admin_cannot_access_admin_endpoints(client, test_admin_user, auth_headers):
    """Test that regular admin cannot access super admin endpoints."""
    headers = auth_headers(test_admin_user.email)
    
    # Test accessing admin companies endpoint (should fail)
    response = client.get("/api/v1/admin/companies", headers=headers)
    assert response.status_code == 403


def test_super_admin_can_access_all_companies(client, test_super_admin_user, auth_headers):
    """Test that super admin can access data from any company."""
    headers = auth_headers(test_super_admin_user.email)
    
    # Test accessing purchase orders from different companies
    response = client.get("/api/v1/purchase-orders/", headers=headers)
    assert response.status_code == 200
    
    # Test accessing companies endpoint
    response = client.get("/api/v1/companies/", headers=headers)
    assert response.status_code == 200


def test_super_admin_role_has_elevated_permissions(client, test_super_admin_user, auth_headers):
    """Test that super admin role has the expected elevated permissions."""
    headers = auth_headers(test_super_admin_user.email)
    
    # Test dashboard access (should work for super_admin)
    response = client.get("/api/v1/dashboard-v2/platform-metrics", headers=headers)
    assert response.status_code == 200


def test_regular_user_cannot_access_admin_endpoints(client, test_user, auth_headers):
    """Test that regular users cannot access admin endpoints."""
    headers = auth_headers(test_user.email)
    
    # Test accessing admin companies endpoint (should fail)
    response = client.get("/api/v1/admin/companies", headers=headers)
    assert response.status_code == 403
    
    # Test accessing admin users endpoint (should fail)
    response = client.get("/api/v1/admin/users", headers=headers)
    assert response.status_code == 403
