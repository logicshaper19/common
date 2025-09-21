"""
PostgreSQL-only test configuration for comprehensive testing.

This conftest ensures all tests use PostgreSQL consistently,
eliminating SQLite compatibility issues.
"""
import os
import pytest
import asyncio
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient
from typing import Generator, AsyncGenerator

# Set test environment
os.environ["TESTING"] = "true"
os.environ["DATABASE_URL"] = "postgresql://postgres:password@localhost:5432/test_common_platform"

from app.core.database import get_db, Base
from app.main import app
from app.core.config import settings


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_engine():
    """Create a PostgreSQL test database engine."""
    # Force PostgreSQL for all tests
    database_url = "postgresql://postgres:password@localhost:5432/test_common_platform"
    
    engine = create_engine(
        database_url,
        echo=False,
        pool_pre_ping=True,
        pool_recycle=300,
    )
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    yield engine
    
    # Clean up
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture(scope="function")
def test_db(test_engine):
    """Create a fresh database session for each test."""
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    
    # Start a transaction
    connection = test_engine.connect()
    transaction = connection.begin()
    
    session = TestingSessionLocal(bind=connection)
    
    yield session
    
    # Rollback the transaction
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def client(test_db):
    """Create a test client with database dependency override."""
    def override_get_db():
        try:
            yield test_db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def clean_db(test_db):
    """Provide a clean database for each test."""
    # Clean all tables
    for table in reversed(Base.metadata.sorted_tables):
        test_db.execute(f"TRUNCATE TABLE {table.name} RESTART IDENTITY CASCADE")
    
    test_db.commit()
    yield test_db
    test_db.rollback()


@pytest.fixture
def test_user_data():
    """Sample user data for testing."""
    return {
        "email": "test@example.com",
        "password": "TestPassword123!",
        "full_name": "Test User",
        "role": "admin"
    }


@pytest.fixture
def test_company_data():
    """Sample company data for testing."""
    return {
        "name": "Test Company",
        "email": "admin@testcompany.com",
        "password": "TestPassword123!",
        "company_type": "manufacturer",
        "full_name": "Test Company Admin",
        "role": "admin",
        "company_email": "info@testcompany.com",
        "website": "https://testcompany.com",
        "phone": "+1-555-0123",
        "address": "123 Test Street",
        "city": "Test City",
        "state_province": "Test State",
        "country": "US",
        "postal_code": "12345"
    }


@pytest.fixture
def test_product_data():
    """Sample product data for testing."""
    return {
        "name": "Test Product",
        "description": "A test product for testing",
        "category": "raw_material",
        "unit": "kg",
        "common_product_id": "TEST-PRODUCT-001",
        "material_breakdown": [{"material": "Test Material", "percentage": 100.0}],
        "price_per_unit": 10.50,
        "supplier_id": None
    }


@pytest.fixture
def test_purchase_order_data():
    """Sample purchase order data for testing."""
    return {
        "seller_company_id": None,  # Will be set in test
        "buyer_company_id": None,   # Will be set in test
        "product_id": None,         # Will be set in test
        "quantity": 100.0,
        "unit": "kg",
        "price_per_unit": 5.25,
        "delivery_date": "2024-12-31",
        "delivery_location": "Test Location",
        "status": "pending",
        "notes": "Test purchase order"
    }


@pytest.fixture
def authenticated_client(client, test_db, test_company_data):
    """Create an authenticated test client."""
    from app.models.company import Company
    from app.models.user import User
    from app.core.auth import get_password_hash
    
    # Create test company
    company = Company(
        name=test_company_data["name"],
        email=test_company_data["email"],
        company_type=test_company_data["company_type"],
        website=test_company_data["website"],
        phone=test_company_data["phone"],
        address=test_company_data["address"],
        city=test_company_data["city"],
        state_province=test_company_data["state_province"],
        country=test_company_data["country"],
        postal_code=test_company_data["postal_code"]
    )
    test_db.add(company)
    test_db.flush()
    
    # Create test user
    user = User(
        email=test_company_data["email"],
        hashed_password=get_password_hash(test_company_data["password"]),
        full_name=test_company_data["full_name"],
        role=test_company_data["role"],
        company_id=company.id,
        is_active=True
    )
    test_db.add(user)
    test_db.commit()
    
    # Login to get token
    login_data = {
        "username": test_company_data["email"],
        "password": test_company_data["password"]
    }
    
    response = client.post("/api/v1/auth/login", data=login_data)
    assert response.status_code == 200
    
    token_data = response.json()
    access_token = token_data["access_token"]
    
    # Set authorization header
    client.headers.update({"Authorization": f"Bearer {access_token}"})
    
    return client, company, user


@pytest.fixture
def test_batch_data():
    """Sample batch data for testing."""
    return {
        "batch_id": "TEST-BATCH-001",
        "product_id": None,  # Will be set in test
        "quantity": 50.0,
        "unit": "kg",
        "quality_grade": "A1",
        "certification_status": "certified",
        "source_purchase_order_id": None  # Will be set in test
    }


@pytest.fixture
def test_transformation_data():
    """Sample transformation data for testing."""
    return {
        "transformation_type": "milling",
        "input_batch_id": None,  # Will be set in test
        "company_id": None,      # Will be set in test
        "facility_id": "TEST-FACILITY-001",
        "process_name": "Test Milling Process",
        "process_description": "A test milling process",
        "start_time": "2024-01-01T10:00:00Z",
        "end_time": "2024-01-01T18:00:00Z",
        "status": "completed"
    }


# Performance testing fixtures
@pytest.fixture
def performance_test_data():
    """Generate large datasets for performance testing."""
    import random
    from decimal import Decimal
    
    companies = []
    for i in range(100):
        companies.append({
            "name": f"Performance Test Company {i}",
            "email": f"company{i}@test.com",
            "company_type": random.choice(["manufacturer", "supplier", "trader"]),
            "password": "TestPassword123!"
        })
    
    products = []
    for i in range(50):
        products.append({
            "name": f"Performance Test Product {i}",
            "category": random.choice(["raw_material", "semi_finished", "finished_good"]),
            "unit": random.choice(["kg", "liters", "pieces"]),
            "price_per_unit": Decimal(str(round(random.uniform(1.0, 100.0), 2)))
        })
    
    return {
        "companies": companies,
        "products": products
    }


# Security testing fixtures
@pytest.fixture
def security_test_data():
    """Data for security testing scenarios."""
    return {
        "malicious_inputs": [
            "<script>alert('xss')</script>",
            "'; DROP TABLE users; --",
            "../../../etc/passwd",
            "{{7*7}}",
            "javascript:alert(1)"
        ],
        "sql_injection_payloads": [
            "' OR '1'='1",
            "'; DROP TABLE companies; --",
            "' UNION SELECT * FROM users --",
            "1' OR 1=1 --",
            "admin'--"
        ],
        "xss_payloads": [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "javascript:alert('XSS')",
            "<svg onload=alert('XSS')>",
            "<iframe src=javascript:alert('XSS')>"
        ]
    }


# Database state management
@pytest.fixture(autouse=True)
def reset_database_state(test_db):
    """Reset database state before each test."""
    # This runs before each test
    yield
    # This runs after each test
    test_db.rollback()


# Test markers
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "e2e: mark test as an end-to-end test"
    )
    config.addinivalue_line(
        "markers", "performance: mark test as a performance test"
    )
    config.addinivalue_line(
        "markers", "security: mark test as a security test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "postgresql: mark test as requiring PostgreSQL"
    )


# Test collection hooks
def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on file location."""
    for item in items:
        # Add markers based on file path
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        elif "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        elif "e2e" in str(item.fspath):
            item.add_marker(pytest.mark.e2e)
        elif "performance" in str(item.fspath):
            item.add_marker(pytest.mark.performance)
        elif "security" in str(item.fspath):
            item.add_marker(pytest.mark.security)
        
        # All tests require PostgreSQL
        item.add_marker(pytest.mark.postgresql)