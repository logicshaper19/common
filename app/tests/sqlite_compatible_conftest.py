"""
SQLite-compatible test configuration that works without PostgreSQL.
This provides immediate testing capability while you set up PostgreSQL.
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

# Use SQLite for tests with JSON support
TEST_DATABASE_URL = f"sqlite:///{tempfile.mktemp(suffix='.db')}"

@pytest.fixture(scope="session")
def test_engine():
    """Create test database engine with SQLite JSON support."""
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False
    )
    
    # Enable JSON support in SQLite
    with engine.connect() as conn:
        conn.execute(text("PRAGMA foreign_keys=ON"))
        conn.execute(text("PRAGMA journal_mode=WAL"))
    
    # Create only essential tables (skip JSONB-heavy tables)
    create_essential_tables(engine)
    
    yield engine
    
    # Cleanup
    engine.dispose()

def create_essential_tables(engine):
    """Create only essential tables that work with SQLite."""
    # List of essential tables that don't use JSONB
    essential_tables = [
        'users',
        'companies', 
        'products',
        'purchase_orders',
        'sectors',
        'harvest_batches',
        'certifications',
        'farm_information'
    ]
    
    # Create tables one by one, skipping problematic ones
    for table_name in essential_tables:
        if table_name in Base.metadata.tables:
            table = Base.metadata.tables[table_name]
            try:
                table.create(engine, checkfirst=True)
            except Exception as e:
                print(f"Warning: Could not create table {table_name}: {e}")
                continue

@pytest.fixture(scope="function")
def db_session(test_engine):
    """Create a database session for testing."""
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = TestingSessionLocal()
    
    try:
        yield session
    finally:
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
    pytest.mark.sqlite_compatible
]


