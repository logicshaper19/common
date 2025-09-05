"""
Tests for authentication system.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import Base, get_db
from app.models.user import User
from app.models.company import Company
from app.core.security import hash_password
from uuid import uuid4

# Create test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
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
    # Drop all tables and recreate them
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    # Clean up after test
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def test_company():
    """Create a test company."""
    db = TestingSessionLocal()
    company = Company(
        id=uuid4(),
        name="Test Company",
        company_type="processor",
        email="test@company.com"
    )
    db.add(company)
    db.commit()
    db.refresh(company)
    db.close()
    return company


@pytest.fixture
def test_user(test_company):
    """Create a test user."""
    db = TestingSessionLocal()
    user = User(
        id=uuid4(),
        email="test@example.com",
        hashed_password=hash_password("testpassword123"),
        full_name="Test User",
        role="buyer",
        company_id=test_company.id,
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    db.close()
    return user


@pytest.fixture
def admin_user(test_company):
    """Create an admin user."""
    db = TestingSessionLocal()
    user = User(
        id=uuid4(),
        email="admin@example.com",
        hashed_password=hash_password("adminpassword123"),
        full_name="Admin User",
        role="admin",
        company_id=test_company.id,
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    db.close()
    return user


def get_auth_headers(user_email: str, password: str) -> dict:
    """Get authentication headers for a user."""
    response = client.post(
        "/auth/login",
        json={"email": user_email, "password": password}
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_user_registration():
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


def test_user_login(test_user):
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


def test_user_login_invalid_credentials():
    """Test user login with invalid credentials."""
    login_data = {
        "email": "test@example.com",
        "password": "wrongpassword"
    }
    
    response = client.post("/auth/login", json=login_data)
    assert response.status_code == 401
    assert "Incorrect email or password" in response.json()["detail"]


def test_get_current_user(test_user):
    """Test getting current user information."""
    headers = get_auth_headers("test@example.com", "testpassword123")
    
    response = client.get("/auth/me", headers=headers)
    assert response.status_code == 200
    
    data = response.json()
    assert data["email"] == "test@example.com"
    assert data["full_name"] == "Test User"
    assert data["role"] == "buyer"
    assert data["is_active"] is True
    assert "company" in data


def test_get_current_user_unauthorized():
    """Test getting current user without authentication."""
    response = client.get("/auth/me")
    assert response.status_code == 403  # No authorization header


def test_get_current_user_invalid_token():
    """Test getting current user with invalid token."""
    headers = {"Authorization": "Bearer invalid_token"}
    
    response = client.get("/auth/me", headers=headers)
    assert response.status_code == 401


def test_create_user_as_admin(admin_user, test_company):
    """Test creating a user as admin."""
    headers = get_auth_headers("admin@example.com", "adminpassword123")
    
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


def test_create_user_as_non_admin(test_user, test_company):
    """Test creating a user as non-admin (should fail)."""
    headers = get_auth_headers("test@example.com", "testpassword123")
    
    user_data = {
        "email": "created@example.com",
        "password": "createdpassword123",
        "full_name": "Created User",
        "role": "seller",
        "company_id": str(test_company.id)
    }
    
    response = client.post("/auth/users", json=user_data, headers=headers)
    assert response.status_code == 403


def test_registration_duplicate_email(test_user):
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


def test_registration_duplicate_company_email(test_company):
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
