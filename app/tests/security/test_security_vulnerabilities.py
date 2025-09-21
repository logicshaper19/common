"""
Comprehensive security testing module for vulnerability detection.

This module provides security testing utilities and test cases
for identifying and preventing security vulnerabilities.
"""
import pytest
import json
import base64
from typing import Dict, List, Any, Optional
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.core.database import get_db
from app.tests.factories import create_test_company_data, create_test_user_data


class SecurityTestBase:
    """Base class for security tests."""
    
    def __init__(self, client: TestClient, db: Session):
        self.client = client
        self.db = db
    
    def test_sql_injection_vulnerabilities(self):
        """Test for SQL injection vulnerabilities."""
        # Common SQL injection payloads
        sql_payloads = [
            "' OR '1'='1",
            "'; DROP TABLE users; --",
            "' UNION SELECT * FROM users --",
            "1' OR 1=1 --",
            "admin'--",
            "' OR 'x'='x",
            "') OR ('1'='1",
            "' OR 1=1#",
            "' OR 1=1/*",
            "admin' OR '1'='1' --"
        ]
        
        for payload in sql_payloads:
            # Test login endpoint
            response = self.client.post("/api/v1/auth/login", data={
                "username": payload,
                "password": "password"
            })
            # Should not return 200 (successful login)
            assert response.status_code != 200, f"SQL injection vulnerability found with payload: {payload}"
            
            # Test company search
            response = self.client.get(f"/api/v1/companies?search={payload}")
            # Should not return 500 (server error) or expose data
            assert response.status_code not in [500, 200], f"SQL injection vulnerability found in search with payload: {payload}"
    
    def test_xss_vulnerabilities(self):
        """Test for Cross-Site Scripting (XSS) vulnerabilities."""
        # Common XSS payloads
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "javascript:alert('XSS')",
            "<svg onload=alert('XSS')>",
            "<iframe src=javascript:alert('XSS')>",
            "<body onload=alert('XSS')>",
            "<input onfocus=alert('XSS') autofocus>",
            "<select onfocus=alert('XSS') autofocus>",
            "<textarea onfocus=alert('XSS') autofocus>",
            "<keygen onfocus=alert('XSS') autofocus>",
            "<video><source onerror=alert('XSS')>",
            "<audio src=x onerror=alert('XSS')>",
            "<details open ontoggle=alert('XSS')>",
            "<marquee onstart=alert('XSS')>",
            "<math><mi//xlink:href=data:x,<script>alert('XSS')</script>"
        ]
        
        for payload in xss_payloads:
            # Test company name field
            company_data = create_test_company_data()
            company_data["name"] = payload
            
            response = self.client.post("/api/v1/auth/register", json=company_data)
            # Should not execute script or return 500
            assert response.status_code not in [500], f"XSS vulnerability found in company name with payload: {payload}"
            
            # Test user full name field
            user_data = create_test_user_data()
            user_data["full_name"] = payload
            
            response = self.client.post("/api/v1/auth/register", json=user_data)
            # Should not execute script or return 500
            assert response.status_code not in [500], f"XSS vulnerability found in user name with payload: {payload}"
    
    def test_path_traversal_vulnerabilities(self):
        """Test for path traversal vulnerabilities."""
        # Common path traversal payloads
        path_payloads = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\drivers\\etc\\hosts",
            "....//....//....//etc/passwd",
            "..%2F..%2F..%2Fetc%2Fpasswd",
            "..%252F..%252F..%252Fetc%252Fpasswd",
            "..%c0%af..%c0%af..%c0%afetc%c0%afpasswd",
            "..%c1%9c..%c1%9c..%c1%9cetc%c1%9cpasswd",
            "..%c0%2f..%c0%2f..%c0%2fetc%c0%2fpasswd",
            "..%c1%af..%c1%af..%c1%afetc%c1%afpasswd"
        ]
        
        for payload in path_payloads:
            # Test file upload endpoint
            response = self.client.post("/api/v1/documents/upload", files={
                "file": (payload, "test content", "text/plain")
            })
            # Should not return 200 (successful upload) or 500 (server error)
            assert response.status_code not in [200, 500], f"Path traversal vulnerability found with payload: {payload}"
            
            # Test document retrieval
            response = self.client.get(f"/api/v1/documents/{payload}")
            # Should not return 200 (successful retrieval) or 500 (server error)
            assert response.status_code not in [200, 500], f"Path traversal vulnerability found in document retrieval with payload: {payload}"
    
    def test_authentication_bypass(self):
        """Test for authentication bypass vulnerabilities."""
        # Test without authentication
        protected_endpoints = [
            "/api/v1/companies",
            "/api/v1/products",
            "/api/v1/simple-purchase-orders",
            "/api/v1/users",
            "/api/v1/documents"
        ]
        
        for endpoint in protected_endpoints:
            response = self.client.get(endpoint)
            # Should return 401 (unauthorized) or 403 (forbidden)
            assert response.status_code in [401, 403], f"Authentication bypass vulnerability found at {endpoint}"
        
        # Test with invalid token
        response = self.client.get(
            "/api/v1/companies",
            headers={"Authorization": "Bearer invalid_token"}
        )
        assert response.status_code in [401, 403], "Invalid token should not be accepted"
        
        # Test with malformed token
        response = self.client.get(
            "/api/v1/companies",
            headers={"Authorization": "Bearer malformed.token.here"}
        )
        assert response.status_code in [401, 403], "Malformed token should not be accepted"
    
    def test_authorization_bypass(self):
        """Test for authorization bypass vulnerabilities."""
        # This would require setting up test users with different roles
        # and testing that users can't access resources they shouldn't
        
        # Test admin-only endpoints with regular user
        admin_endpoints = [
            "/api/v1/admin/users",
            "/api/v1/admin/companies",
            "/api/v1/admin/system"
        ]
        
        # Create a regular user token (this would need proper setup)
        # For now, just test that endpoints exist and require proper auth
        for endpoint in admin_endpoints:
            response = self.client.get(endpoint)
            # Should return 401 (unauthorized) or 403 (forbidden)
            assert response.status_code in [401, 403], f"Authorization bypass vulnerability found at {endpoint}"
    
    def test_input_validation_bypass(self):
        """Test for input validation bypass vulnerabilities."""
        # Test email validation bypass
        invalid_emails = [
            "not-an-email",
            "@invalid.com",
            "invalid@",
            "invalid@.com",
            "invalid@com",
            "invalid@com.",
            "invalid@.com.",
            "invalid@com..",
            "invalid@.com..",
            "invalid@com...",
            "invalid@.com...",
            "invalid@com....",
            "invalid@.com....",
            "invalid@com.....",
            "invalid@.com.....",
            "invalid@com......",
            "invalid@.com......",
            "invalid@com.......",
            "invalid@.com.......",
            "invalid@com........",
            "invalid@.com........"
        ]
        
        for email in invalid_emails:
            user_data = create_test_user_data()
            user_data["email"] = email
            
            response = self.client.post("/api/v1/auth/register", json=user_data)
            # Should return 400 (bad request) or 422 (validation error)
            assert response.status_code in [400, 422], f"Email validation bypass found with: {email}"
        
        # Test password validation bypass
        weak_passwords = [
            "123",
            "password",
            "123456",
            "qwerty",
            "abc123",
            "password123",
            "admin",
            "root",
            "test",
            "user"
        ]
        
        for password in weak_passwords:
            user_data = create_test_user_data()
            user_data["password"] = password
            
            response = self.client.post("/api/v1/auth/register", json=user_data)
            # Should return 400 (bad request) or 422 (validation error)
            assert response.status_code in [400, 422], f"Weak password accepted: {password}"
    
    def test_csrf_vulnerabilities(self):
        """Test for Cross-Site Request Forgery (CSRF) vulnerabilities."""
        # Test state-changing operations without CSRF protection
        state_changing_endpoints = [
            ("POST", "/api/v1/auth/register"),
            ("POST", "/api/v1/auth/login"),
            ("PUT", "/api/v1/companies/1"),
            ("DELETE", "/api/v1/companies/1"),
            ("POST", "/api/v1/simple-purchase-orders"),
            ("PUT", "/api/v1/simple-purchase-orders/1/confirm")
        ]
        
        for method, endpoint in state_changing_endpoints:
            if method == "POST":
                response = self.client.post(endpoint, json={})
            elif method == "PUT":
                response = self.client.put(endpoint, json={})
            elif method == "DELETE":
                response = self.client.delete(endpoint)
            
            # Should return 401 (unauthorized) or 403 (forbidden) without proper CSRF protection
            # Note: This is a simplified test - real CSRF testing requires more sophisticated setup
            assert response.status_code in [401, 403, 404], f"CSRF vulnerability found at {method} {endpoint}"
    
    def test_information_disclosure(self):
        """Test for information disclosure vulnerabilities."""
        # Test error message information disclosure
        response = self.client.get("/api/v1/nonexistent-endpoint")
        # Should not return detailed error information
        if response.status_code == 404:
            response_data = response.json()
            # Should not contain sensitive information
            sensitive_keywords = ["password", "secret", "key", "token", "database", "sql"]
            for keyword in sensitive_keywords:
                assert keyword not in str(response_data).lower(), f"Information disclosure found: {keyword}"
        
        # Test stack trace disclosure
        response = self.client.get("/api/v1/companies/invalid-id")
        # Should not return stack traces
        if response.status_code == 500:
            response_data = response.json()
            # Should not contain stack trace information
            assert "traceback" not in str(response_data).lower(), "Stack trace disclosure found"
            assert "exception" not in str(response_data).lower(), "Exception details disclosure found"
    
    def test_session_management(self):
        """Test session management vulnerabilities."""
        # Test session fixation
        response1 = self.client.get("/api/v1/auth/login")
        session1 = response1.cookies.get("session")
        
        response2 = self.client.get("/api/v1/auth/login")
        session2 = response2.cookies.get("session")
        
        # Sessions should be different
        if session1 and session2:
            assert session1 != session2, "Session fixation vulnerability found"
        
        # Test session timeout
        # This would require more sophisticated testing with actual session management
        
        # Test session invalidation
        # This would require testing logout functionality
    
    def test_cryptographic_vulnerabilities(self):
        """Test for cryptographic vulnerabilities."""
        # Test weak encryption
        # This would require analyzing the encryption methods used
        
        # Test predictable tokens
        # This would require analyzing token generation
        
        # Test insecure random number generation
        # This would require analyzing random number generation methods
        
        pass  # Placeholder for cryptographic testing
    
    def test_injection_attacks(self):
        """Test for various injection attacks."""
        # Test command injection
        command_payloads = [
            "; ls",
            "| whoami",
            "& dir",
            "` id`",
            "$(id)",
            "; cat /etc/passwd",
            "| cat /etc/passwd",
            "& cat /etc/passwd",
            "` cat /etc/passwd`",
            "$(cat /etc/passwd)"
        ]
        
        for payload in command_payloads:
            # Test in various input fields
            company_data = create_test_company_data()
            company_data["name"] = f"Test Company{payload}"
            
            response = self.client.post("/api/v1/auth/register", json=company_data)
            # Should not execute commands or return 500
            assert response.status_code not in [500], f"Command injection vulnerability found with payload: {payload}"
        
        # Test LDAP injection
        ldap_payloads = [
            "*",
            "*)(uid=*",
            "*)(|(uid=*",
            "*)(|(objectClass=*",
            "*)(|(objectClass=*)(uid=*",
            "*)(|(objectClass=*)(|(uid=*",
            "*)(|(objectClass=*)(|(uid=*)(|(objectClass=*",
            "*)(|(objectClass=*)(|(uid=*)(|(objectClass=*)(|(uid=*"
        ]
        
        for payload in ldap_payloads:
            # Test in search fields
            response = self.client.get(f"/api/v1/companies?search={payload}")
            # Should not return 500 or expose data
            assert response.status_code not in [500], f"LDAP injection vulnerability found with payload: {payload}"
    
    def test_business_logic_vulnerabilities(self):
        """Test for business logic vulnerabilities."""
        # Test negative quantity in purchase orders
        po_data = {
            "seller_company_id": "test-seller",
            "buyer_company_id": "test-buyer",
            "product_id": "test-product",
            "quantity": -100.0,  # Negative quantity
            "unit": "kg",
            "price_per_unit": 5.0,
            "delivery_date": "2024-12-31",
            "status": "pending"
        }
        
        response = self.client.post("/api/v1/simple-purchase-orders", json=po_data)
        # Should return 400 (bad request) or 422 (validation error)
        assert response.status_code in [400, 422], "Negative quantity should not be allowed"
        
        # Test future delivery date validation
        po_data["quantity"] = 100.0
        po_data["delivery_date"] = "2020-01-01"  # Past date
        
        response = self.client.post("/api/v1/simple-purchase-orders", json=po_data)
        # Should return 400 (bad request) or 422 (validation error)
        assert response.status_code in [400, 422], "Past delivery date should not be allowed"
        
        # Test price manipulation
        po_data["delivery_date"] = "2024-12-31"
        po_data["price_per_unit"] = -5.0  # Negative price
        
        response = self.client.post("/api/v1/simple-purchase-orders", json=po_data)
        # Should return 400 (bad request) or 422 (validation error)
        assert response.status_code in [400, 422], "Negative price should not be allowed"


# Security Test Fixtures

@pytest.fixture
def security_client():
    """Create a test client for security testing."""
    return TestClient(app)


@pytest.fixture
def security_db():
    """Create a database session for security testing."""
    from app.core.database import SessionLocal
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def security_tests(security_client, security_db):
    """Create security test instance."""
    return SecurityTestBase(security_client, security_db)


# Security Test Markers

@pytest.mark.security
def test_sql_injection(security_tests):
    """Test for SQL injection vulnerabilities."""
    security_tests.test_sql_injection_vulnerabilities()


@pytest.mark.security
def test_xss(security_tests):
    """Test for XSS vulnerabilities."""
    security_tests.test_xss_vulnerabilities()


@pytest.mark.security
def test_path_traversal(security_tests):
    """Test for path traversal vulnerabilities."""
    security_tests.test_path_traversal_vulnerabilities()


@pytest.mark.security
def test_authentication_bypass(security_tests):
    """Test for authentication bypass vulnerabilities."""
    security_tests.test_authentication_bypass()


@pytest.mark.security
def test_authorization_bypass(security_tests):
    """Test for authorization bypass vulnerabilities."""
    security_tests.test_authorization_bypass()


@pytest.mark.security
def test_input_validation_bypass(security_tests):
    """Test for input validation bypass vulnerabilities."""
    security_tests.test_input_validation_bypass()


@pytest.mark.security
def test_csrf(security_tests):
    """Test for CSRF vulnerabilities."""
    security_tests.test_csrf_vulnerabilities()


@pytest.mark.security
def test_information_disclosure(security_tests):
    """Test for information disclosure vulnerabilities."""
    security_tests.test_information_disclosure()


@pytest.mark.security
def test_session_management(security_tests):
    """Test session management vulnerabilities."""
    security_tests.test_session_management()


@pytest.mark.security
def test_cryptographic_vulnerabilities(security_tests):
    """Test for cryptographic vulnerabilities."""
    security_tests.test_cryptographic_vulnerabilities()


@pytest.mark.security
def test_injection_attacks(security_tests):
    """Test for injection attacks."""
    security_tests.test_injection_attacks()


@pytest.mark.security
def test_business_logic_vulnerabilities(security_tests):
    """Test for business logic vulnerabilities."""
    security_tests.test_business_logic_vulnerabilities()


# Security Test Configuration

SECURITY_TEST_CONFIG = {
    "sql_injection": {
        "enabled": True,
        "payloads": [
            "' OR '1'='1",
            "'; DROP TABLE users; --",
            "' UNION SELECT * FROM users --"
        ]
    },
    "xss": {
        "enabled": True,
        "payloads": [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "javascript:alert('XSS')"
        ]
    },
    "path_traversal": {
        "enabled": True,
        "payloads": [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\drivers\\etc\\hosts"
        ]
    },
    "authentication_bypass": {
        "enabled": True,
        "endpoints": [
            "/api/v1/companies",
            "/api/v1/products",
            "/api/v1/simple-purchase-orders"
        ]
    },
    "input_validation": {
        "enabled": True,
        "fields": ["email", "password", "name", "quantity", "price"]
    }
}
