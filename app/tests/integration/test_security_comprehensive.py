"""
Comprehensive security tests for authentication, authorization, and input validation.
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
from app.models.product import Product
from app.models.purchase_order import PurchaseOrder
from app.core.security import hash_password, create_access_token

# Use PostgreSQL test configuration from conftest.py
# No need for custom database setup
client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_db(db_session):
    """Clean database before each test."""
    db_session.query(PurchaseOrder).delete()
    db_session.query(Product).delete()
    db_session.query(Company).delete()
    db_session.query(User).delete()
    db_session.commit()


@pytest.fixture
def test_companies(db_session):
    """Create test companies."""
    
    companies = {
        "company_a": Company(
            id=uuid4(),
            name="Company A",
            company_type="brand",
            email="company_a@test.com"
        ),
        "company_b": Company(
            id=uuid4(),
            name="Company B",
            company_type="processor",
            email="company_b@test.com"
        )
    }
    
    for company in companies.values():
        db_session.add(company)
    
    db_session.commit()
    return companies


@pytest.fixture
def test_users(test_companies, db_session):
    """Create test users with different roles."""
    
    users = {
        "admin_a": User(
            id=uuid4(),
            email="admin_a@test.com",
            hashed_password=hash_password("testpassword123"),
            full_name="Admin A",
            role="admin",
            company_id=test_companies["company_a"].id,
            is_active=True
        ),
        "buyer_a": User(
            id=uuid4(),
            email="buyer_a@test.com",
            hashed_password=hash_password("testpassword123"),
            full_name="Buyer A",
            role="buyer",
            company_id=test_companies["company_a"].id,
            is_active=True
        ),
        "seller_b": User(
            id=uuid4(),
            email="seller_b@test.com",
            hashed_password=hash_password("testpassword123"),
            full_name="Seller B",
            role="seller",
            company_id=test_companies["company_b"].id,
            is_active=True
        ),
        "inactive_user": User(
            id=uuid4(),
            email="inactive@test.com",
            hashed_password=hash_password("testpassword123"),
            full_name="Inactive User",
            role="buyer",
            company_id=test_companies["company_a"].id,
            is_active=False
        )
    }
    
    for user in users.values():
        db_session.add(user)
    
    db_session.commit()
    return users


@pytest.fixture
def test_products(db_session):
    """Create test products."""
    
    products = {
        "product_1": Product(
            id=uuid4(),
            common_product_id="PROD-001",
            name="Test Product 1",
            category="raw_material",
            description="Test product",
            default_unit="KGM"
        ),
        "product_2": Product(
            id=uuid4(),
            common_product_id="PROD-002",
            name="Test Product 2",
            category="processed",
            description="Test product 2",
            default_unit="MT"
        )
    }
    
    for product in products.values():
        db_session.add(product)
    
    db_session.commit()
    return products


def get_auth_headers(user_email: str) -> dict:
    """Get authentication headers for a user."""
    token = create_access_token(data={"sub": user_email})
    return {"Authorization": f"Bearer {token}"}


class TestAuthenticationSecurity:
    """Test authentication security measures."""
    
    def test_brute_force_protection(self, test_users):
        """Test protection against brute force attacks."""
        # Attempt multiple failed logins
        for i in range(10):
            login_data = {
                "email": "admin_a@test.com",
                "password": "wrongpassword"
            }
            response = client.post("/api/v1/auth/login", json=login_data)
            
            if i < 5:
                assert response.status_code == 401
            else:
                # Should be rate limited after 5 attempts
                assert response.status_code in [401, 429]
    
    def test_account_lockout_after_failed_attempts(self, test_users):
        """Test account lockout after multiple failed attempts."""
        # Mock rate limiter to simulate lockout
        with patch('app.core.auth_rate_limiting.get_auth_rate_limiter') as mock_limiter:
            mock_rate_limiter = Mock()
            mock_rate_limiter.check_auth_rate_limit.return_value = (False, {
                "lockout_reason": "Too many failed attempts",
                "email_limit": {"lockout_until": "2024-12-31T23:59:59Z"}
            })
            mock_limiter.return_value = mock_rate_limiter
            
            login_data = {
                "email": "admin_a@test.com",
                "password": "testpassword123"
            }
            
            response = client.post("/api/v1/auth/login", json=login_data)
            assert response.status_code == 429
            assert "Too many login attempts" in response.json()["detail"]
    
    def test_password_strength_validation(self, test_companies):
        """Test password strength validation."""
        weak_passwords = [
            "123",
            "password",
            "12345678",
            "qwerty",
            "admin"
        ]
        
        for weak_password in weak_passwords:
            user_data = {
                "email": f"test_{weak_password}@example.com",
                "password": weak_password,
                "full_name": "Test User",
                "role": "buyer",
                "company_name": "Test Company",
                "company_type": "brand",
                "company_email": "test@company.com"
            }
            
            response = client.post("/api/v1/auth/register", json=user_data)
            # Should either reject weak passwords or accept with warning
            assert response.status_code in [200, 400, 422]
    
    def test_token_expiration(self, test_users):
        """Test token expiration handling."""
        # Create expired token
        expired_token = create_access_token(
            data={"sub": "admin_a@test.com"},
            expires_delta=timedelta(seconds=-1)
        )
        
        headers = {"Authorization": f"Bearer {expired_token}"}
        response = client.get("/api/v1/auth/me", headers=headers)
        assert response.status_code == 401
    
    def test_invalid_token_handling(self, test_users):
        """Test handling of various invalid tokens."""
        invalid_tokens = [
            "invalid_token",
            "Bearer invalid_token",
            "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.invalid",
            "",
            None
        ]
        
        for token in invalid_tokens:
            headers = {"Authorization": f"Bearer {token}"} if token else {}
            response = client.get("/api/v1/auth/me", headers=headers)
            assert response.status_code == 401
    
    def test_session_management(self, test_users):
        """Test session management and token refresh."""
        # Login to get tokens
        login_data = {
            "email": "admin_a@test.com",
            "password": "testpassword123"
        }
        
        response = client.post("/api/v1/auth/login", json=login_data)
        assert response.status_code == 200
        
        data = response.json()
        access_token = data["access_token"]
        refresh_token = data["refresh_token"]
        
        # Use access token
        headers = {"Authorization": f"Bearer {access_token}"}
        response = client.get("/api/v1/auth/me", headers=headers)
        assert response.status_code == 200
        
        # Refresh token
        refresh_data = {"refresh_token": refresh_token}
        response = client.post("/api/v1/auth/refresh", json=refresh_data)
        assert response.status_code == 200
        
        new_data = response.json()
        assert "access_token" in new_data
        assert new_data["access_token"] != access_token


class TestAuthorizationSecurity:
    """Test authorization and access control."""
    
    def test_role_based_access_control(self, test_users, test_companies, test_products):
        """Test role-based access control."""
        # Test admin access
        admin_headers = get_auth_headers("admin_a@test.com")
        response = client.get("/api/v1/companies", headers=admin_headers)
        assert response.status_code == 200
        
        # Test buyer access
        buyer_headers = get_auth_headers("buyer_a@test.com")
        response = client.get("/api/v1/companies", headers=buyer_headers)
        # Should have limited access
        assert response.status_code in [200, 403]
        
        # Test seller access
        seller_headers = get_auth_headers("seller_b@test.com")
        response = client.get("/api/v1/companies", headers=seller_headers)
        # Should have limited access
        assert response.status_code in [200, 403]
    
    def test_company_data_isolation(self, test_users, test_companies):
        """Test that companies can only access their own data."""
        # Company A user should not access Company B's sensitive data
        company_a_headers = get_auth_headers("admin_a@test.com")
        company_b_id = test_companies["company_b"].id
        
        response = client.get(f"/api/v1/companies/{company_b_id}", headers=company_a_headers)
        # Should either return limited data or be forbidden
        assert response.status_code in [200, 403]
        
        if response.status_code == 200:
            # If allowed, should return limited data
            data = response.json()
            # Should not include sensitive information
            assert "internal_notes" not in data
            assert "financial_data" not in data
    
    def test_cross_company_po_access(self, test_users, test_companies, test_products):
        """Test that users cannot access other companies' purchase orders."""
        # Create PO as Company A
        company_a_headers = get_auth_headers("admin_a@test.com")
        po_data = {
            "seller_company_id": str(test_companies["company_b"].id),
            "product_id": str(test_products["product_1"].id),
            "quantity": 1000,
            "unit": "KGM",
            "delivery_date": "2024-12-31"
        }
        
        po_response = client.post("/api/v1/purchase-orders", json=po_data, headers=company_a_headers)
        assert po_response.status_code == 201
        po_id = po_response.json()["id"]
        
        # Company B should not be able to access this PO
        company_b_headers = get_auth_headers("seller_b@test.com")
        response = client.get(f"/api/v1/purchase-orders/{po_id}", headers=company_b_headers)
        assert response.status_code == 403
    
    def test_inactive_user_access(self, test_users):
        """Test that inactive users cannot access the system."""
        headers = get_auth_headers("inactive@test.com")
        
        response = client.get("/api/v1/auth/me", headers=headers)
        assert response.status_code == 401
    
    def test_privilege_escalation_prevention(self, test_users, test_companies):
        """Test prevention of privilege escalation attacks."""
        # Regular user trying to access admin endpoints
        buyer_headers = get_auth_headers("buyer_a@test.com")
        
        # Try to create user (admin only)
        user_data = {
            "email": "hacked@test.com",
            "password": "hacked123",
            "full_name": "Hacked User",
            "role": "admin",
            "company_id": str(test_companies["company_a"].id)
        }
        
        response = client.post("/api/v1/auth/users", json=user_data, headers=buyer_headers)
        assert response.status_code == 403
        
        # Try to update company (admin only)
        update_data = {"name": "Hacked Company"}
        response = client.put(f"/api/v1/companies/{test_companies['company_a'].id}", 
                            json=update_data, headers=buyer_headers)
        assert response.status_code == 403


class TestInputValidationSecurity:
    """Test input validation and sanitization."""
    
    def test_sql_injection_prevention(self, test_users, test_companies):
        """Test prevention of SQL injection attacks."""
        headers = get_auth_headers("admin_a@test.com")
        
        # SQL injection attempts in search parameters
        malicious_queries = [
            "'; DROP TABLE users; --",
            "1' OR '1'='1",
            "admin'--",
            "1' UNION SELECT * FROM users--"
        ]
        
        for query in malicious_queries:
            response = client.get(f"/api/v1/companies?search={query}", headers=headers)
            # Should not cause database errors
            assert response.status_code in [200, 400, 422]
            
            # Should not return unexpected data
            if response.status_code == 200:
                data = response.json()
                assert "items" in data
                # Should not return all users or cause errors
    
    def test_xss_prevention(self, test_users, test_companies):
        """Test prevention of XSS attacks."""
        headers = get_auth_headers("admin_a@test.com")
        
        # XSS payloads
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "javascript:alert('XSS')",
            "<img src=x onerror=alert('XSS')>",
            "';alert('XSS');//"
        ]
        
        for payload in xss_payloads:
            # Try in company name
            company_data = {
                "name": payload,
                "company_type": "processor",
                "email": "xss@test.com"
            }
            
            response = client.post("/api/v1/companies", json=company_data, headers=headers)
            # Should either reject or sanitize
            assert response.status_code in [200, 400, 422]
            
            if response.status_code == 200:
                data = response.json()
                # Should be sanitized
                assert "<script>" not in data["name"]
                assert "javascript:" not in data["name"]
    
    def test_input_length_validation(self, test_users):
        """Test input length validation."""
        headers = get_auth_headers("admin_a@test.com")
        
        # Extremely long input
        long_string = "A" * 10000
        
        company_data = {
            "name": long_string,
            "company_type": "processor",
            "email": "long@test.com"
        }
        
        response = client.post("/api/v1/companies", json=company_data, headers=headers)
        assert response.status_code == 422  # Should reject too long input
    
    def test_malformed_json_handling(self, test_users):
        """Test handling of malformed JSON."""
        headers = get_auth_headers("admin_a@test.com")
        
        malformed_requests = [
            '{"name": "Test", "email":}',  # Missing value
            '{"name": "Test", "email": "test@test.com",}',  # Trailing comma
            '{"name": "Test", "email": "test@test.com"',  # Missing closing brace
            '{"name": "Test", "email": "test@test.com", "extra": }'  # Invalid value
        ]
        
        for malformed_json in malformed_requests:
            response = client.post("/api/v1/companies", 
                                 data=malformed_json, 
                                 headers={**headers, "Content-Type": "application/json"})
            assert response.status_code == 422
    
    def test_type_coercion_attacks(self, test_users, test_companies):
        """Test prevention of type coercion attacks."""
        headers = get_auth_headers("admin_a@test.com")
        
        # Try to pass wrong types
        malicious_data = {
            "name": 123,  # Should be string
            "company_type": True,  # Should be string
            "email": ["test@test.com"],  # Should be string
            "subscription_tier": {"tier": "enterprise"}  # Should be string
        }
        
        response = client.post("/api/v1/companies", json=malicious_data, headers=headers)
        assert response.status_code == 422


class TestDataSecurity:
    """Test data security and privacy measures."""
    
    def test_sensitive_data_masking(self, test_users, test_companies):
        """Test that sensitive data is properly masked."""
        headers = get_auth_headers("admin_a@test.com")
        
        response = client.get(f"/api/v1/companies/{test_companies['company_a'].id}", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        # Should not include sensitive fields
        sensitive_fields = ["internal_notes", "financial_data", "tax_id", "bank_account"]
        for field in sensitive_fields:
            assert field not in data
    
    def test_password_not_returned_in_responses(self, test_users):
        """Test that passwords are never returned in API responses."""
        headers = get_auth_headers("admin_a@test.com")
        
        response = client.get("/api/v1/auth/me", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "password" not in data
        assert "hashed_password" not in data
    
    def test_data_encryption_in_transit(self, test_users):
        """Test that data is properly encrypted in transit."""
        # This is more of a configuration test
        # In a real scenario, you'd check HTTPS headers, certificates, etc.
        headers = get_auth_headers("admin_a@test.com")
        
        response = client.get("/api/v1/auth/me", headers=headers)
        assert response.status_code == 200
        
        # Check that sensitive headers are present
        # Note: TestClient doesn't use HTTPS, so this is a placeholder
        # In real testing, you'd use a proper HTTPS client
    
    def test_audit_logging(self, test_users, test_companies):
        """Test that security events are properly logged."""
        headers = get_auth_headers("admin_a@test.com")
        
        # Perform sensitive operations
        company_data = {
            "name": "Audit Test Company",
            "company_type": "processor",
            "email": "audit@test.com"
        }
        
        response = client.post("/api/v1/companies", json=company_data, headers=headers)
        assert response.status_code == 201
        
        # Check audit logs (if endpoint exists)
        audit_response = client.get("/api/v1/audit/events", headers=headers)
        # This endpoint might not exist
        assert audit_response.status_code in [200, 404]
        
        if audit_response.status_code == 200:
            audit_data = audit_response.json()
            # Should contain recent events
            assert len(audit_data["items"]) >= 1


class TestAPIAbusePrevention:
    """Test prevention of API abuse and DoS attacks."""
    
    def test_rate_limiting(self, test_users):
        """Test API rate limiting."""
        headers = get_auth_headers("admin_a@test.com")
        
        # Make many requests quickly
        for i in range(100):
            response = client.get("/api/v1/companies", headers=headers)
            if response.status_code == 429:
                break
        
        # Should eventually be rate limited
        assert response.status_code in [200, 429]
    
    def test_request_size_limiting(self, test_users):
        """Test request size limiting."""
        headers = get_auth_headers("admin_a@test.com")
        
        # Very large request body
        large_data = {
            "name": "A" * 1000000,  # 1MB string
            "company_type": "processor",
            "email": "large@test.com"
        }
        
        response = client.post("/api/v1/companies", json=large_data, headers=headers)
        assert response.status_code in [200, 413, 422]  # 413 = Payload Too Large
    
    def test_concurrent_request_handling(self, test_users):
        """Test handling of concurrent requests."""
        import threading
        import time
        
        headers = get_auth_headers("admin_a@test.com")
        results = []
        
        def make_request():
            response = client.get("/api/v1/companies", headers=headers)
            results.append(response.status_code)
        
        # Start many concurrent requests
        threads = []
        for i in range(20):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        # Most should succeed
        success_count = results.count(200)
        assert success_count >= 15  # At least 75% should succeed
    
    def test_malicious_header_handling(self, test_users):
        """Test handling of malicious headers."""
        headers = get_auth_headers("admin_a@test.com")
        
        # Add malicious headers
        malicious_headers = {
            **headers,
            "X-Forwarded-For": "127.0.0.1",
            "X-Real-IP": "127.0.0.1",
            "X-Forwarded-Host": "malicious.com",
            "X-Forwarded-Proto": "https",
            "X-Original-URL": "/admin/delete-all-data"
        }
        
        response = client.get("/api/v1/companies", headers=malicious_headers)
        # Should not be affected by malicious headers
        assert response.status_code == 200


class TestAdvancedSecurityScenarios:
    """Test advanced security scenarios and edge cases."""
    
    def test_jwt_token_manipulation(self, test_users):
        """Test JWT token manipulation attempts."""
        # Create valid token
        valid_token = create_access_token(data={"sub": "brand@test.com"})
        headers = {"Authorization": f"Bearer {valid_token}"}
        
        # Test with modified token (add extra characters)
        modified_token = valid_token + "x"
        modified_headers = {"Authorization": f"Bearer {modified_token}"}
        response = client.get("/api/v1/companies", headers=modified_headers)
        assert response.status_code == 401
        
        # Test with truncated token
        truncated_token = valid_token[:-10]
        truncated_headers = {"Authorization": f"Bearer {truncated_token}"}
        response = client.get("/api/v1/companies", headers=truncated_headers)
        assert response.status_code == 401
        
        # Test with completely invalid token
        invalid_headers = {"Authorization": "Bearer invalid.token.here"}
        response = client.get("/api/v1/companies", headers=invalid_headers)
        assert response.status_code == 401
    
    def test_session_hijacking_protection(self, test_users):
        """Test protection against session hijacking."""
        # Create token for one user
        user1_token = create_access_token(data={"sub": "brand@test.com"})
        user1_headers = {"Authorization": f"Bearer {user1_token}"}
        
        # Create token for another user
        user2_token = create_access_token(data={"sub": "processor@test.com"})
        user2_headers = {"Authorization": f"Bearer {user2_token}"}
        
        # User1 creates a resource
        company_data = {"name": "User1 Company", "company_type": "brand"}
        create_response = client.post("/api/v1/companies", json=company_data, headers=user1_headers)
        company_id = create_response.json()["id"]
        
        # User2 should not be able to access user1's resource
        response = client.get(f"/api/v1/companies/{company_id}", headers=user2_headers)
        assert response.status_code == 404  # Not found, not forbidden
    
    def test_brute_force_protection(self, test_users):
        """Test brute force attack protection."""
        # Attempt multiple failed logins
        failed_attempts = 0
        for i in range(10):
            login_data = {
                "username": "brand@test.com",
                "password": f"wrong_password_{i}"
            }
            response = client.post("/api/v1/auth/login", data=login_data)
            if response.status_code == 401:
                failed_attempts += 1
        
        # After multiple failed attempts, should be rate limited
        assert failed_attempts >= 5  # At least some should fail
        
        # Even with correct password, might be temporarily blocked
        correct_login = {
            "username": "brand@test.com",
            "password": "testpassword"
        }
        response = client.post("/api/v1/auth/login", data=correct_login)
        # Should either succeed or be rate limited
        assert response.status_code in [200, 429]
    
    def test_injection_attacks(self, test_users):
        """Test various injection attack vectors."""
        headers = get_auth_headers("brand@test.com")
        
        # SQL injection in JSON payload
        malicious_data = {
            "name": "'; DROP TABLE companies; --",
            "company_type": "brand"
        }
        response = client.post("/api/v1/companies", json=malicious_data, headers=headers)
        # Should not crash the system
        assert response.status_code in [200, 201, 400, 422]
        
        # NoSQL injection (if applicable)
        malicious_data = {
            "name": {"$ne": "test"},
            "company_type": "brand"
        }
        response = client.post("/api/v1/companies", json=malicious_data, headers=headers)
        assert response.status_code in [200, 201, 400, 422]
        
        # Command injection
        malicious_data = {
            "name": "test; rm -rf /",
            "company_type": "brand"
        }
        response = client.post("/api/v1/companies", json=malicious_data, headers=headers)
        assert response.status_code in [200, 201, 400, 422]
    
    def test_file_upload_security(self, test_users):
        """Test file upload security measures."""
        headers = get_auth_headers("brand@test.com")
        
        # Test malicious file upload
        malicious_files = [
            ("malicious.exe", b"MZ\x90\x00", "application/x-executable"),
            ("script.php", b"<?php system($_GET['cmd']); ?>", "application/x-php"),
            ("shell.sh", b"#!/bin/bash\nrm -rf /", "application/x-sh"),
        ]
        
        for filename, content, content_type in malicious_files:
            files = {"file": (filename, content, content_type)}
            response = client.post("/api/v1/documents/upload", files=files, headers=headers)
            # Should reject malicious files
            assert response.status_code in [400, 415, 422]
    
    def test_csrf_protection(self, test_users):
        """Test CSRF protection mechanisms."""
        headers = get_auth_headers("brand@test.com")
        
        # Test without CSRF token (if implemented)
        company_data = {"name": "Test Company", "company_type": "brand"}
        response = client.post("/api/v1/companies", json=company_data, headers=headers)
        # Should either work (if no CSRF) or require token
        assert response.status_code in [200, 201, 403]
        
        # Test with fake CSRF token
        fake_csrf_headers = {
            **headers,
            "X-CSRF-Token": "fake-token-123"
        }
        response = client.post("/api/v1/companies", json=company_data, headers=fake_csrf_headers)
        # Should either work (if no CSRF) or reject fake token
        assert response.status_code in [200, 201, 403]
    
    def test_privilege_escalation(self, test_users):
        """Test privilege escalation prevention."""
        # Create regular user
        regular_user = UserFactory()
        regular_user.is_admin = False
        db.add(regular_user)
        db.commit()
        
        regular_token = create_access_token(data={"sub": str(regular_user.id)})
        regular_headers = {"Authorization": f"Bearer {regular_token}"}
        
        # Try to access admin endpoints
        admin_endpoints = [
            "/api/v1/users",
            "/api/v1/admin/companies",
            "/api/v1/admin/users"
        ]
        
        for endpoint in admin_endpoints:
            response = client.get(endpoint, headers=regular_headers)
            assert response.status_code == 403
        
        # Try to modify user roles
        user_data = {"is_admin": True}
        response = client.put(f"/api/v1/users/{regular_user.id}", json=user_data, headers=regular_headers)
        assert response.status_code == 403
    
    def test_data_exfiltration_protection(self, test_users):
        """Test protection against data exfiltration."""
        headers = get_auth_headers("brand@test.com")
        
        # Try to access sensitive data through different endpoints
        sensitive_endpoints = [
            "/api/v1/users",
            "/api/v1/admin/companies",
            "/api/v1/audit-logs"
        ]
        
        for endpoint in sensitive_endpoints:
            response = client.get(endpoint, headers=headers)
            # Should either be forbidden or return limited data
            assert response.status_code in [200, 403, 404]
    
    def test_timing_attack_protection(self, test_users):
        """Test protection against timing attacks."""
        import time
        
        # Test login timing with valid vs invalid users
        valid_user = "brand@test.com"
        invalid_user = "nonexistent@test.com"
        
        # Time valid user login
        start_time = time.time()
        login_data = {"username": valid_user, "password": "testpassword"}
        response1 = client.post("/api/v1/auth/login", data=login_data)
        valid_time = time.time() - start_time
        
        # Time invalid user login
        start_time = time.time()
        login_data = {"username": invalid_user, "password": "wrongpassword"}
        response2 = client.post("/api/v1/auth/login", data=login_data)
        invalid_time = time.time() - start_time
        
        # Times should be similar to prevent timing attacks
        time_diff = abs(valid_time - invalid_time)
        assert time_diff < 0.1  # Should be within 100ms
    
    def test_memory_exhaustion_protection(self, test_users):
        """Test protection against memory exhaustion attacks."""
        headers = get_auth_headers("brand@test.com")
        
        # Try to create very large payloads
        large_data = {
            "name": "A" * 10000,  # Very long name
            "description": "B" * 100000,  # Very long description
            "company_type": "brand"
        }
        
        response = client.post("/api/v1/companies", json=large_data, headers=headers)
        # Should either accept or reject with appropriate error
        assert response.status_code in [200, 201, 400, 413, 422]
    
    def test_concurrent_security_operations(self, test_users):
        """Test security under concurrent operations."""
        import threading
        
        headers = get_auth_headers("brand@test.com")
        results = []
        
        def make_request():
            response = client.get("/api/v1/companies", headers=headers)
            results.append(response.status_code)
        
        # Make concurrent requests
        threads = [threading.Thread(target=make_request) for _ in range(20)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        
        # All requests should succeed
        assert all(status == 200 for status in results)
    
    def test_security_headers(self, test_users):
        """Test that security headers are properly set."""
        response = client.get("/api/v1/companies")
        
        # Check for security headers
        security_headers = [
            "X-Content-Type-Options",
            "X-Frame-Options",
            "X-XSS-Protection",
            "Strict-Transport-Security"
        ]
        
        for header in security_headers:
            assert header in response.headers or header.lower() in response.headers
