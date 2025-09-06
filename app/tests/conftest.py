"""
Pytest configuration and shared fixtures for comprehensive testing.
"""
import pytest
import asyncio
import os
import tempfile
from typing import Generator, Dict, Any
from unittest.mock import Mock, patch

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import get_db, Base
from app.core.config import settings
from app.core.security import create_access_token
from app.tests.factories import (
    SupplyChainScenarioFactory,
    CompanyFactory,
    UserFactory,
    ProductFactory,
    PurchaseOrderFactory
)


# Test database configuration
TEST_DATABASE_URL = "sqlite:///./test_comprehensive.db"


@pytest.fixture(scope="session")
def test_engine():
    """Create test database engine."""
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False  # Set to True for SQL debugging
    )
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    yield engine
    
    # Cleanup
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="session")
def TestingSessionLocal(test_engine):
    """Create test session factory."""
    return sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture
def db_session(TestingSessionLocal):
    """Create database session for testing."""
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture
def client(db_session):
    """Create test client with database override."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers():
    """Create authentication headers factory."""
    def _create_headers(user_email: str) -> Dict[str, str]:
        token = create_access_token(data={"sub": user_email})
        return {"Authorization": f"Bearer {token}"}
    
    return _create_headers


@pytest.fixture
def simple_scenario(db_session):
    """Create simple supply chain scenario."""
    scenario = SupplyChainScenarioFactory.create_simple_scenario()
    
    # Add to database
    for company in scenario.companies:
        db_session.add(company)
    
    for user in scenario.users:
        db_session.add(user)
    
    for product in scenario.products:
        db_session.add(product)
    
    for relationship in scenario.relationships:
        db_session.add(relationship)
    
    db_session.commit()
    
    for po in scenario.purchase_orders:
        db_session.add(po)
    
    db_session.commit()
    
    return scenario


@pytest.fixture
def complex_scenario(db_session):
    """Create complex supply chain scenario."""
    scenario = SupplyChainScenarioFactory.create_complex_scenario()
    
    # Add to database
    for company in scenario.companies:
        db_session.add(company)
    
    for user in scenario.users:
        db_session.add(user)
    
    for product in scenario.products:
        db_session.add(product)
    
    for relationship in scenario.relationships:
        db_session.add(relationship)
    
    db_session.commit()
    
    for po in scenario.purchase_orders:
        db_session.add(po)
    
    db_session.commit()
    
    return scenario


@pytest.fixture
def brand_user_client(simple_scenario, auth_headers, client):
    """Create client authenticated as brand user."""
    brand_company = next(c for c in simple_scenario.companies if c.company_type == "brand")
    brand_user = next(u for u in simple_scenario.users if u.company_id == brand_company.id)
    
    headers = auth_headers(brand_user.email)
    
    class AuthenticatedClient:
        def __init__(self, client, headers):
            self.client = client
            self.headers = headers
            self.user = brand_user
            self.company = brand_company
        
        def get(self, url, **kwargs):
            kwargs.setdefault('headers', {}).update(self.headers)
            return self.client.get(url, **kwargs)
        
        def post(self, url, **kwargs):
            kwargs.setdefault('headers', {}).update(self.headers)
            return self.client.post(url, **kwargs)
        
        def put(self, url, **kwargs):
            kwargs.setdefault('headers', {}).update(self.headers)
            return self.client.put(url, **kwargs)
        
        def delete(self, url, **kwargs):
            kwargs.setdefault('headers', {}).update(self.headers)
            return self.client.delete(url, **kwargs)
    
    return AuthenticatedClient(client, headers)


@pytest.fixture
def processor_user_client(simple_scenario, auth_headers, client):
    """Create client authenticated as processor user."""
    processor_company = next(c for c in simple_scenario.companies if c.company_type == "processor")
    processor_user = next(u for u in simple_scenario.users if u.company_id == processor_company.id)
    
    headers = auth_headers(processor_user.email)
    
    class AuthenticatedClient:
        def __init__(self, client, headers):
            self.client = client
            self.headers = headers
            self.user = processor_user
            self.company = processor_company
        
        def get(self, url, **kwargs):
            kwargs.setdefault('headers', {}).update(self.headers)
            return self.client.get(url, **kwargs)
        
        def post(self, url, **kwargs):
            kwargs.setdefault('headers', {}).update(self.headers)
            return self.client.post(url, **kwargs)
        
        def put(self, url, **kwargs):
            kwargs.setdefault('headers', {}).update(self.headers)
            return self.client.put(url, **kwargs)
        
        def delete(self, url, **kwargs):
            kwargs.setdefault('headers', {}).update(self.headers)
            return self.client.delete(url, **kwargs)
    
    return AuthenticatedClient(client, headers)


@pytest.fixture
def originator_user_client(simple_scenario, auth_headers, client):
    """Create client authenticated as originator user."""
    originator_company = next(c for c in simple_scenario.companies if c.company_type == "originator")
    originator_user = next(u for u in simple_scenario.users if u.company_id == originator_company.id)
    
    headers = auth_headers(originator_user.email)
    
    class AuthenticatedClient:
        def __init__(self, client, headers):
            self.client = client
            self.headers = headers
            self.user = originator_user
            self.company = originator_company
        
        def get(self, url, **kwargs):
            kwargs.setdefault('headers', {}).update(self.headers)
            return self.client.get(url, **kwargs)
        
        def post(self, url, **kwargs):
            kwargs.setdefault('headers', {}).update(self.headers)
            return self.client.post(url, **kwargs)
        
        def put(self, url, **kwargs):
            kwargs.setdefault('headers', {}).update(self.headers)
            return self.client.put(url, **kwargs)
        
        def delete(self, url, **kwargs):
            kwargs.setdefault('headers', {}).update(self.headers)
            return self.client.delete(url, **kwargs)
    
    return AuthenticatedClient(client, headers)


@pytest.fixture
def mock_redis():
    """Mock Redis for testing."""
    with patch('app.core.performance_cache.redis') as mock_redis:
        mock_client = Mock()
        mock_client.ping.return_value = True
        mock_client.get.return_value = None
        mock_client.setex.return_value = True
        mock_client.delete.return_value = 1
        mock_client.keys.return_value = []
        mock_client.flushdb.return_value = True
        
        mock_redis.from_url.return_value = mock_client
        yield mock_client


@pytest.fixture
def mock_email_service():
    """Mock email service for testing."""
    with patch('app.services.email.send_email') as mock_send:
        mock_send.return_value = {"status": "sent", "message_id": "test_123"}
        yield mock_send


@pytest.fixture
def mock_external_apis():
    """Mock external API services."""
    mocks = {}
    
    with patch('app.services.external_apis.verify_certification') as mock_cert:
        mock_cert.return_value = {
            "status": "valid",
            "certification_id": "TEST-123",
            "expiry_date": "2024-12-31"
        }
        mocks['certification'] = mock_cert
        
        with patch('app.services.blockchain.record_transparency_data') as mock_blockchain:
            mock_blockchain.return_value = {
                "status": "confirmed",
                "transaction_hash": "0x123456789",
                "block_number": 12345
            }
            mocks['blockchain'] = mock_blockchain
            
            yield mocks


@pytest.fixture
def temp_file():
    """Create temporary file for testing."""
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(b"test file content")
        tmp.flush()
        yield tmp.name
    
    # Cleanup
    try:
        os.unlink(tmp.name)
    except OSError:
        pass


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# Test markers
pytest.mark.unit = pytest.mark.unit
pytest.mark.integration = pytest.mark.integration
pytest.mark.e2e = pytest.mark.e2e
pytest.mark.load = pytest.mark.load
pytest.mark.slow = pytest.mark.slow


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "e2e: End-to-end tests")
    config.addinivalue_line("markers", "load: Load tests")
    config.addinivalue_line("markers", "slow: Slow tests")


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on file names."""
    for item in items:
        # Add markers based on test file names
        if "test_unit" in item.fspath.basename:
            item.add_marker(pytest.mark.unit)
        elif "test_integration" in item.fspath.basename:
            item.add_marker(pytest.mark.integration)
        elif "test_end_to_end" in item.fspath.basename:
            item.add_marker(pytest.mark.e2e)
        elif "test_load" in item.fspath.basename:
            item.add_marker(pytest.mark.load)
        elif "test_performance" in item.fspath.basename:
            item.add_marker(pytest.mark.slow)


# Test utilities
class TestDataManager:
    """Utility class for managing test data."""
    
    @staticmethod
    def create_test_company(company_type: str = "brand"):
        """Create a test company."""
        return CompanyFactory.create_company(company_type)
    
    @staticmethod
    def create_test_user(company, role: str = "admin"):
        """Create a test user."""
        return UserFactory.create_user(company, role=role)
    
    @staticmethod
    def create_test_product(category: str = "finished_good"):
        """Create a test product."""
        return ProductFactory.create_product(category)
    
    @staticmethod
    def create_test_po(buyer_company, seller_company, product):
        """Create a test purchase order."""
        return PurchaseOrderFactory.create_purchase_order(
            buyer_company=buyer_company,
            seller_company=seller_company,
            product=product
        )


@pytest.fixture
def test_data_manager():
    """Provide test data manager."""
    return TestDataManager()


# Performance test utilities
class PerformanceAssertions:
    """Utility class for performance assertions."""
    
    @staticmethod
    def assert_response_time(response_time: float, max_time: float):
        """Assert response time is within acceptable limits."""
        assert response_time <= max_time, f"Response time {response_time}s exceeds limit {max_time}s"
    
    @staticmethod
    def assert_success_rate(success_count: int, total_count: int, min_rate: float):
        """Assert success rate meets minimum threshold."""
        success_rate = (success_count / total_count) * 100 if total_count > 0 else 0
        assert success_rate >= min_rate, f"Success rate {success_rate}% below minimum {min_rate}%"
    
    @staticmethod
    def assert_throughput(request_count: int, duration: float, min_rps: float):
        """Assert throughput meets minimum requests per second."""
        rps = request_count / duration if duration > 0 else 0
        assert rps >= min_rps, f"Throughput {rps} RPS below minimum {min_rps} RPS"


@pytest.fixture
def performance_assertions():
    """Provide performance assertions utility."""
    return PerformanceAssertions()


# Error testing utilities
class ErrorTestUtils:
    """Utility class for error testing."""
    
    @staticmethod
    def assert_error_response(response, expected_status: int, expected_error_code: str = None):
        """Assert error response format and content."""
        assert response.status_code == expected_status
        
        error_data = response.json()
        assert "error" in error_data
        assert "request_id" in error_data
        assert "timestamp" in error_data
        
        if expected_error_code:
            assert error_data["error"]["code"] == expected_error_code
    
    @staticmethod
    def assert_validation_error(response, field_name: str = None):
        """Assert validation error response."""
        assert response.status_code == 422
        error_data = response.json()
        assert error_data["error"]["code"] == "VALIDATION_ERROR"
        
        if field_name:
            details = error_data["error"]["details"]
            assert any(detail["field"] == field_name for detail in details)


@pytest.fixture
def error_test_utils():
    """Provide error testing utilities."""
    return ErrorTestUtils()
