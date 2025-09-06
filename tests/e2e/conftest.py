"""
Pytest fixtures for E2E testing
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.core.database import get_db
from tests.e2e.base.test_data_factory import TestDataFactory
from tests.e2e.helpers.auth_helper import AuthHelper


@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def db_session():
    """Database session for testing."""
    # This should use your existing test database setup
    # Assuming you have a test database session fixture
    from app.tests.conftest import db_session as test_db_session
    return test_db_session


@pytest.fixture
def test_data_factory(db_session):
    """Test data factory instance."""
    return TestDataFactory(db_session)


@pytest.fixture
def auth_helper(client):
    """Authentication helper instance."""
    return AuthHelper(client)


@pytest.fixture(autouse=True)
def cleanup_test_data(db_session):
    """Automatically cleanup test data after each test."""
    yield
    # Cleanup logic here - truncate tables or rollback transactions
    try:
        db_session.rollback()
    except Exception:
        pass