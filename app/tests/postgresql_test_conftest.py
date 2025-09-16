"""
PostgreSQL test configuration for JSONB compatibility.
This replaces the SQLite configuration for tests that need JSONB functionality.
"""
import pytest
import asyncio
import os
from contextlib import contextmanager
from typing import Generator, Dict, Any, Optional
from unittest.mock import Mock, patch

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import get_db, Base
from app.core.config import settings

# PostgreSQL test database URL
POSTGRESQL_DATABASE_URL = "postgresql://postgres:test@localhost:5433/common_test"

# Create PostgreSQL engine
engine = create_engine(
    POSTGRESQL_DATABASE_URL,
    poolclass=StaticPool,
    echo=False
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    """Override database dependency for PostgreSQL testing."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

# Override the database dependency
app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test."""
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        # Clean up tables after each test
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client():
    """Create a test client with PostgreSQL database."""
    with TestClient(app) as test_client:
        yield test_client

@pytest.fixture(scope="function")
def test_data():
    """Provide test data for JSONB operations."""
    return {
        "supply_chain": {
            "palm_oil": {
                "quantity": 1000,
                "unit": "kg",
                "origin": "Malaysia",
                "certifications": ["RSPO", "ISCC"],
                "supplier": {
                    "name": "Malaysian Palm Oil Supplier",
                    "location": "Kuala Lumpur"
                }
            }
        },
        "quality_metrics": {
            "ffa_content": 0.15,
            "moisture": 0.1
        }
    }
