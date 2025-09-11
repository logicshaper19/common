"""
Tests for product management system.
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
from app.models.product import Product
from app.core.security import hash_password
from uuid import uuid4

# Create test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_products.db"
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


@pytest.fixture
def regular_user(test_company):
    """Create a regular user."""
    db = TestingSessionLocal()
    user = User(
        id=uuid4(),
        email="user@example.com",
        hashed_password=hash_password("userpassword123"),
        full_name="Regular User",
        role="buyer",
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


def test_create_product_as_admin(admin_user):
    """Test creating a product as admin."""
    headers = get_auth_headers("admin@example.com", "adminpassword123")
    
    product_data = {
        "common_product_id": "TEST-001",
        "name": "Test Product",
        "description": "A test product",
        "category": "raw_material",
        "can_have_composition": False,
        "default_unit": "KGM",
        "hs_code": "1234.56.78"
    }
    
    response = client.post("/products/", json=product_data, headers=headers)
    assert response.status_code == 200
    
    data = response.json()
    assert data["common_product_id"] == "TEST-001"
    assert data["name"] == "Test Product"
    assert data["category"] == "raw_material"
    assert data["can_have_composition"] is False


def test_create_product_as_regular_user(regular_user):
    """Test creating a product as regular user (should fail)."""
    headers = get_auth_headers("user@example.com", "userpassword123")
    
    product_data = {
        "common_product_id": "TEST-001",
        "name": "Test Product",
        "description": "A test product",
        "category": "raw_material",
        "can_have_composition": False,
        "default_unit": "KGM"
    }
    
    response = client.post("/products/", json=product_data, headers=headers)
    assert response.status_code == 403


def test_create_product_with_composition(admin_user):
    """Test creating a product with composition rules."""
    headers = get_auth_headers("admin@example.com", "adminpassword123")
    
    product_data = {
        "common_product_id": "BLEND-001",
        "name": "Palm Oil Blend",
        "description": "80/20 palm oil blend",
        "category": "finished_good",
        "can_have_composition": True,
        "material_breakdown": {
            "palm_oil": 80.0,
            "palm_kernel_oil": 20.0
        },
        "default_unit": "KGM",
        "hs_code": "1511.90.00"
    }
    
    response = client.post("/products/", json=product_data, headers=headers)
    assert response.status_code == 200
    
    data = response.json()
    assert data["can_have_composition"] is True
    assert data["material_breakdown"]["palm_oil"] == 80.0
    assert data["material_breakdown"]["palm_kernel_oil"] == 20.0


def test_create_product_invalid_composition(admin_user):
    """Test creating a product with invalid composition (doesn't sum to 100)."""
    headers = get_auth_headers("admin@example.com", "adminpassword123")
    
    product_data = {
        "common_product_id": "INVALID-001",
        "name": "Invalid Product",
        "category": "finished_good",
        "can_have_composition": True,
        "material_breakdown": {
            "palm_oil": 80.0,
            "palm_kernel_oil": 15.0  # Only sums to 95%
        },
        "default_unit": "KGM"
    }
    
    response = client.post("/products/", json=product_data, headers=headers)
    assert response.status_code == 422  # Validation error


def test_list_products(admin_user, regular_user):
    """Test listing products."""
    # Create some test products first
    headers = get_auth_headers("admin@example.com", "adminpassword123")
    
    products = [
        {
            "common_product_id": "RAW-001",
            "name": "Raw Material",
            "category": "raw_material",
            "can_have_composition": False,
            "default_unit": "KGM"
        },
        {
            "common_product_id": "PROC-001",
            "name": "Processed Product",
            "category": "processed",
            "can_have_composition": True,
            "material_breakdown": {"component": 100.0},
            "default_unit": "KGM"
        }
    ]
    
    for product_data in products:
        response = client.post("/products/", json=product_data, headers=headers)
        assert response.status_code == 200
    
    # Test listing as regular user
    user_headers = get_auth_headers("user@example.com", "userpassword123")
    response = client.get("/products/", headers=user_headers)
    assert response.status_code == 200
    
    data = response.json()
    assert data["total"] == 2
    assert len(data["products"]) == 2


def test_list_products_with_filters(admin_user):
    """Test listing products with filters."""
    headers = get_auth_headers("admin@example.com", "adminpassword123")
    
    # Create test products
    products = [
        {
            "common_product_id": "RAW-001",
            "name": "Raw Material",
            "category": "raw_material",
            "can_have_composition": False,
            "default_unit": "KGM"
        },
        {
            "common_product_id": "PROC-001",
            "name": "Processed Product",
            "category": "processed",
            "can_have_composition": True,
            "material_breakdown": {"component": 100.0},
            "default_unit": "KGM"
        }
    ]
    
    for product_data in products:
        response = client.post("/products/", json=product_data, headers=headers)
        assert response.status_code == 200
    
    # Test category filter
    response = client.get("/products/?category=raw_material", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["products"][0]["category"] == "raw_material"
    
    # Test composition filter
    response = client.get("/products/?can_have_composition=true", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["products"][0]["can_have_composition"] is True


def test_get_product_by_id(admin_user):
    """Test getting a product by ID."""
    headers = get_auth_headers("admin@example.com", "adminpassword123")
    
    # Create a product first
    product_data = {
        "common_product_id": "TEST-001",
        "name": "Test Product",
        "category": "raw_material",
        "can_have_composition": False,
        "default_unit": "KGM"
    }
    
    response = client.post("/products/", json=product_data, headers=headers)
    assert response.status_code == 200
    created_product = response.json()
    
    # Get the product by ID
    response = client.get(f"/products/{created_product['id']}", headers=headers)
    assert response.status_code == 200
    
    data = response.json()
    assert data["id"] == created_product["id"]
    assert data["name"] == "Test Product"


def test_validate_composition(admin_user):
    """Test composition validation."""
    headers = get_auth_headers("admin@example.com", "adminpassword123")
    
    # Create a product with composition rules
    product_data = {
        "common_product_id": "BLEND-001",
        "name": "Palm Oil Blend",
        "category": "finished_good",
        "can_have_composition": True,
        "material_breakdown": {
            "palm_oil": 80.0,
            "palm_kernel_oil": 20.0
        },
        "default_unit": "KGM"
    }
    
    response = client.post("/products/", json=product_data, headers=headers)
    assert response.status_code == 200
    created_product = response.json()
    
    # Test valid composition
    validation_data = {
        "product_id": created_product["id"],
        "composition": {
            "palm_oil": 80.0,
            "palm_kernel_oil": 20.0
        }
    }
    
    response = client.post("/products/validate-composition", json=validation_data, headers=headers)
    assert response.status_code == 200
    
    data = response.json()
    assert data["is_valid"] is True
    assert len(data["errors"]) == 0
