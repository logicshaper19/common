"""
PostgreSQL-compatible test configuration.
This provides full database testing capability with PostgreSQL.
"""
import pytest
import os
import tempfile
from contextlib import contextmanager
from typing import Generator, Dict, Any, Optional
from unittest.mock import Mock, patch

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import get_db, Base
from app.core.config import settings
from app.core.security import create_access_token

# PostgreSQL test database configuration
POSTGRES_TEST_DATABASE_URL = "postgresql://elisha@localhost:5432/common_test"

@pytest.fixture(scope="session")
def test_engine():
    """Create PostgreSQL test database engine."""
    engine = create_engine(
        POSTGRES_TEST_DATABASE_URL,
        echo=False,
        pool_pre_ping=True
    )
    
    # Test connection
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("✅ PostgreSQL test database connected successfully")
    except Exception as e:
        print(f"❌ Failed to connect to PostgreSQL test database: {e}")
        print("   Make sure Docker container is running: docker ps | grep test-postgres")
        raise
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    print("✅ All database tables created")
    
    yield engine
    
    # Cleanup
    engine.dispose()

@pytest.fixture(scope="function")
def db_session(test_engine):
    """Create a database session for testing."""
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = TestingSessionLocal()
    
    try:
        yield session
    finally:
        session.rollback()
        session.close()

@pytest.fixture(scope="function")
def client(db_session):
    """Create a test client with database session."""
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
def test_user():
    """Create a test user."""
    return {
        "id": "test-user-id",
        "email": "test@example.com",
        "full_name": "Test User",
        "company_id": "test-company-id",
        "role": "cooperative_manager"
    }

@pytest.fixture
def test_company():
    """Create a test company."""
    return {
        "id": "test-company-id",
        "name": "Test Company",
        "email": "company@example.com",
        "company_type": "cooperative"
    }

@pytest.fixture
def auth_headers(test_user):
    """Create authentication headers."""
    token = create_access_token(data={"sub": test_user["id"]})
    return {"Authorization": f"Bearer {token}"}

# Test markers
pytestmark = [
    pytest.mark.unit,
    pytest.mark.postgresql
]

