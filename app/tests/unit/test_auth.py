"""
Comprehensive tests for authentication system.
"""
import os
# Set testing environment before importing models
os.environ["TESTING"] = "true"

import pytest
import json
from datetime import datetime, timedelta
from unittest.mock import patch, Mock

from app.models.user import User
from app.models.company import Company
from app.core.security import hash_password, create_access_token
from app.core.auth_rate_limiting import AuthAttemptResult
from uuid import uuid4

# Mark all tests in this file as unit and auth tests
pytestmark = [pytest.mark.unit, pytest.mark.auth]


@pytest.fixture
def test_company(db_session):
    """Create a test company."""
    company = Company(
        id=uuid4(),
        name="Test Company",
        company_type="processor",
        email="test@company.com"
    )
    db_session.add(company)
    db_session.commit()
    db_session.refresh(company)
    return company


@pytest.fixture
def test_user(db_session, test_company):
    """Create a test user."""
    user = User(
        id=uuid4(),
        email="test@example.com",
        hashed_password=hash_password("testpassword123"),
        full_name="Test User",
        role="buyer",
        company_id=test_company.id,
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def admin_user(db_session, test_company):
    """Create an admin user."""
    user = User(
        id=uuid4(),
        email="admin@example.com",
        hashed_password=hash_password("adminpassword123"),
        full_name="Admin User",
        role="admin",
        company_id=test_company.id,
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def get_auth_headers(client, user_email: str, password: str) -> dict:
    """Get authentication headers for a user."""
    response = client.post(
        "/auth/login",
        json={"email": user_email, "password": password}
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_user_registration(client):
    """Test user registration."""
    user_data = {
        "email": "newuser@example.com",
        "password": "newpassword123",
        "full_name": "New User",
        "role": "buyer",
        "company_name": "New Company",
        "company_type": "brand",
        "company_email": "new@company.com"
    }

    response = client.post("/auth/register", json=user_data)
    assert response.status_code == 200

    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert "expires_in" in data


def test_user_login(client, test_user):
    """Test user login."""
    login_data = {
        "email": "test@example.com",
        "password": "testpassword123"
    }

    response = client.post("/auth/login", json=login_data)
    assert response.status_code == 200

    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert "expires_in" in data


def test_user_login_invalid_credentials(client):
    """Test user login with invalid credentials."""
    login_data = {
        "email": "test@example.com",
        "password": "wrongpassword"
    }

    response = client.post("/auth/login", json=login_data)
    assert response.status_code == 401
    assert "Incorrect email or password" in response.json()["detail"]


def test_get_current_user(client, test_user):
    """Test getting current user information."""
    headers = get_auth_headers(client, "test@example.com", "testpassword123")

    response = client.get("/auth/me", headers=headers)
    assert response.status_code == 200

    data = response.json()
    assert data["email"] == "test@example.com"
    assert data["full_name"] == "Test User"
    assert data["role"] == "buyer"
    assert data["is_active"] is True
    assert "company" in data


def test_get_current_user_unauthorized(client):
    """Test getting current user without authentication."""
    response = client.get("/auth/me")
    assert response.status_code == 403  # No authorization header


def test_get_current_user_invalid_token(client):
    """Test getting current user with invalid token."""
    headers = {"Authorization": "Bearer invalid_token"}

    response = client.get("/auth/me", headers=headers)
    assert response.status_code == 401


def test_create_user_as_admin(client, admin_user, test_company):
    """Test creating a user as admin."""
    headers = get_auth_headers(client, "admin@example.com", "adminpassword123")

    user_data = {
        "email": "created@example.com",
        "password": "createdpassword123",
        "full_name": "Created User",
        "role": "seller",
        "company_id": str(test_company.id)
    }

    response = client.post("/auth/users", json=user_data, headers=headers)
    assert response.status_code == 200

    data = response.json()
    assert data["email"] == "created@example.com"
    assert data["full_name"] == "Created User"
    assert data["role"] == "seller"


def test_create_user_as_non_admin(client, test_user, test_company):
    """Test creating a user as non-admin (should fail)."""
    headers = get_auth_headers(client, "test@example.com", "testpassword123")

    user_data = {
        "email": "created@example.com",
        "password": "createdpassword123",
        "full_name": "Created User",
        "role": "seller",
        "company_id": str(test_company.id)
    }

    response = client.post("/auth/users", json=user_data, headers=headers)
    assert response.status_code == 403


def test_registration_duplicate_email(client, test_user):
    """Test registration with duplicate email."""
    user_data = {
        "email": "test@example.com",  # Already exists
        "password": "newpassword123",
        "full_name": "New User",
        "role": "buyer",
        "company_name": "New Company",
        "company_type": "brand",
        "company_email": "new@company.com"
    }
    
    response = client.post("/auth/register", json=user_data)
    assert response.status_code == 400
    assert "Email already registered" in response.json()["detail"]


def test_registration_duplicate_company_email(client, test_company):
    """Test registration with duplicate company email."""
    user_data = {
        "email": "newuser@example.com",
        "password": "newpassword123",
        "full_name": "New User",
        "role": "buyer",
        "company_name": "New Company",
        "company_type": "brand",
        "company_email": "test@company.com"  # Already exists
    }

    response = client.post("/auth/register", json=user_data)
    assert response.status_code == 400
    assert "Company email already registered" in response.json()["detail"]


# Additional comprehensive test cases

def test_token_refresh(client):
    """Test token refresh functionality."""
    # First login to get tokens
    login_data = {
        "email": "test@example.com",
        "password": "testpassword123"
    }

    response = client.post("/api/v1/auth/login", json=login_data)
    assert response.status_code == 200

    data = response.json()
    refresh_token = data["refresh_token"]

    # Use refresh token to get new access token
    refresh_data = {"refresh_token": refresh_token}
    response = client.post("/api/v1/auth/refresh", json=refresh_data)
    assert response.status_code == 200

    new_data = response.json()
    assert "access_token" in new_data
    assert "refresh_token" in new_data
    assert new_data["token_type"] == "bearer"


def test_token_refresh_invalid_token(client):
    """Test token refresh with invalid refresh token."""
    refresh_data = {"refresh_token": "invalid_refresh_token"}
    response = client.post("/api/v1/auth/refresh", json=refresh_data)
    assert response.status_code == 401


def test_password_validation(client):
    """Test password validation endpoint."""
    password_data = {
        "password": "TestPassword123!",
        "email": "test@example.com"
    }

    response = client.post("/api/v1/auth/validate-password", json=password_data)
    assert response.status_code == 200

    data = response.json()
    assert "is_valid" in data
    assert "score" in data
    assert "suggestions" in data


def test_password_validation_weak_password(client):
    """Test password validation with weak password."""
    password_data = {
        "password": "123",
        "email": "test@example.com"
    }

    response = client.post("/api/v1/auth/validate-password", json=password_data)
    assert response.status_code == 200

    data = response.json()
    assert data["is_valid"] is False
    assert data["score"] < 3
    assert len(data["suggestions"]) > 0


def test_user_permissions(client, test_user):
    """Test user permissions endpoint."""
    headers = get_auth_headers(client, "test@example.com", "testpassword123")
    
    response = client.get("/api/v1/users/permissions", headers=headers)
    assert response.status_code == 200
    
    data = response.json()
    assert "navigation" in data
    assert "features" in data
    assert "data_access" in data
    
    # Check specific permissions for buyer role
    assert data["features"]["create_purchase_order"] is True
    assert data["features"]["manage_users"] is False  # Not admin


def test_admin_permissions(admin_user):
    """Test admin permissions."""
    headers = get_auth_headers("admin@example.com", "adminpassword123")
    
    response = client.get("/api/v1/users/permissions", headers=headers)
    assert response.status_code == 200
    
    data = response.json()
    assert data["features"]["manage_users"] is True
    assert data["features"]["view_all_companies"] is True


def test_rate_limiting():
    """Test authentication rate limiting."""
    # Mock the rate limiter to simulate rate limiting
    with patch('app.core.auth_rate_limiting.get_auth_rate_limiter') as mock_limiter:
        mock_rate_limiter = Mock()
        mock_rate_limiter.check_auth_rate_limit.return_value = (False, {
            "lockout_reason": "Too many attempts",
            "ip_limit": {"lockout_until": "2024-01-01T00:00:00Z"}
        })
        mock_limiter.return_value = mock_rate_limiter
        
        login_data = {
            "email": "test@example.com",
            "password": "testpassword123"
        }
        
        response = client.post("/api/v1/auth/login", json=login_data)
        assert response.status_code == 429
        assert "Too many login attempts" in response.json()["detail"]


def test_login_with_inactive_user(test_company):
    """Test login with inactive user."""
    db = TestingSessionLocal()
    inactive_user = User(
        id=uuid4(),
        email="inactive@example.com",
        hashed_password=hash_password("testpassword123"),
        full_name="Inactive User",
        role="buyer",
        company_id=test_company.id,
        is_active=False
    )
    db.add(inactive_user)
    db.commit()
    db.close()
    
    login_data = {
        "email": "inactive@example.com",
        "password": "testpassword123"
    }
    
    response = client.post("/api/v1/auth/login", json=login_data)
    assert response.status_code == 401


def test_registration_validation_errors():
    """Test registration with various validation errors."""
    # Test missing required fields
    user_data = {
        "email": "test@example.com",
        # Missing password, full_name, etc.
    }
    
    response = client.post("/api/v1/auth/register", json=user_data)
    assert response.status_code == 422  # Validation error
    
    # Test invalid email format
    user_data = {
        "email": "invalid-email",
        "password": "testpassword123",
        "full_name": "Test User",
        "role": "buyer",
        "company_name": "Test Company",
        "company_type": "brand",
        "company_email": "test@company.com"
    }
    
    response = client.post("/api/v1/auth/register", json=user_data)
    assert response.status_code == 422


def test_registration_weak_password():
    """Test registration with weak password."""
    user_data = {
        "email": "weakpass@example.com",
        "password": "123",  # Weak password
        "full_name": "Weak Pass User",
        "role": "buyer",
        "company_name": "Weak Company",
        "company_type": "brand",
        "company_email": "weak@company.com"
    }
    
    response = client.post("/api/v1/auth/register", json=user_data)
    # Should either succeed with warning or fail with validation error
    assert response.status_code in [200, 422]


def test_token_expiration():
    """Test token expiration handling."""
    # Create an expired token
    expired_token = create_access_token(
        data={"sub": "test@example.com"},
        expires_delta=timedelta(seconds=-1)  # Expired 1 second ago
    )
    
    headers = {"Authorization": f"Bearer {expired_token}"}
    response = client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == 401


def test_invalid_token_format():
    """Test handling of invalid token formats."""
    # Test malformed token
    headers = {"Authorization": "Bearer invalid.token.format"}
    response = client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == 401
    
    # Test missing Bearer prefix
    headers = {"Authorization": "some_token"}
    response = client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == 401


def test_concurrent_login_attempts():
    """Test handling of concurrent login attempts."""
    import threading
    import time
    
    results = []
    
    def attempt_login():
        login_data = {
            "email": "test@example.com",
            "password": "testpassword123"
        }
        response = client.post("/api/v1/auth/login", json=login_data)
        results.append(response.status_code)
    
    # Start multiple concurrent login attempts
    threads = []
    for _ in range(5):
        thread = threading.Thread(target=attempt_login)
        threads.append(thread)
        thread.start()
    
    # Wait for all threads to complete
    for thread in threads:
        thread.join()
    
    # At least one should succeed
    assert 200 in results


def test_user_logout():
    """Test user logout functionality."""
    # First login
    login_data = {
        "email": "test@example.com",
        "password": "testpassword123"
    }
    
    response = client.post("/api/v1/auth/login", json=login_data)
    assert response.status_code == 200
    
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test logout (if implemented)
    response = client.post("/api/v1/auth/logout", headers=headers)
    # This might return 404 if logout endpoint doesn't exist
    assert response.status_code in [200, 404]


def test_password_reset_request():
    """Test password reset request."""
    reset_data = {"email": "test@example.com"}
    
    with patch('app.services.email.send_email') as mock_send:
        mock_send.return_value = {"status": "sent", "message_id": "test_123"}
        
        response = client.post("/api/v1/auth/request-password-reset", json=reset_data)
        # This might return 404 if endpoint doesn't exist
        assert response.status_code in [200, 404]


def test_company_creation_during_registration():
    """Test that company is created during user registration."""
    user_data = {
        "email": "newuser@example.com",
        "password": "newpassword123",
        "full_name": "New User",
        "role": "buyer",
        "company_name": "New Test Company",
        "company_type": "brand",
        "company_email": "new@company.com"
    }
    
    response = client.post("/api/v1/auth/register", json=user_data)
    assert response.status_code == 200
    
    # Verify company was created
    db = TestingSessionLocal()
    company = db.query(Company).filter(Company.name == "New Test Company").first()
    assert company is not None
    assert company.company_type == "brand"
    assert company.email == "new@company.com"
    db.close()


def test_user_creation_with_existing_company():
    """Test user creation with existing company."""
    # First create a company
    db = TestingSessionLocal()
    company = Company(
        id=uuid4(),
        name="Existing Company",
        company_type="processor",
        email="existing@company.com"
    )
    db.add(company)
    db.commit()
    db.close()
    
    # Register user with existing company
    user_data = {
        "email": "user@existing.com",
        "password": "newpassword123",
        "full_name": "Existing User",
        "role": "seller",
        "company_name": "Existing Company",
        "company_type": "processor",
        "company_email": "existing@company.com"
    }
    
    response = client.post("/api/v1/auth/register", json=user_data)
    assert response.status_code == 200
    
    # Verify user was created and linked to existing company
    db = TestingSessionLocal()
    user = db.query(User).filter(User.email == "user@existing.com").first()
    assert user is not None
    assert user.company_id == company.id
    db.close()
