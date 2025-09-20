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
POSTGRESQL_DATABASE_URL = "postgresql://elisha@localhost:5432/common_test"

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

@pytest.fixture(scope="session")
def db_session():
    """Create a database session for the test session."""
    # Tables should already exist from previous setup
    # Just verify they exist, don't recreate
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()

@pytest.fixture(scope="function")
def db_session_clean(db_session):
    """Clean database for each test."""
    # Clean all tables but keep schema
    try:
        for table in reversed(Base.metadata.sorted_tables):
            db_session.execute(f"TRUNCATE TABLE {table.name} RESTART IDENTITY CASCADE")
        db_session.commit()
    except Exception as e:
        # If truncate fails, try to delete all records
        for table in reversed(Base.metadata.sorted_tables):
            try:
                db_session.execute(table.delete())
            except Exception:
                pass
        db_session.commit()
    yield db_session

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
