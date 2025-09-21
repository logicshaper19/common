"""
Test configuration to handle SQLite compatibility issues.
"""
import os
import tempfile
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Use PostgreSQL for tests with JSON support
TEST_DATABASE_URL = f"sqlite:///{tempfile.mktemp(suffix='.db')}"

def create_test_engine():
    """Create a test engine that works with SQLite."""
    engine = create_engine(
        TEST_DATABASE_URL,
        pool_pre_ping=True,
        poolclass=StaticPool,
        echo=False
    )
    return engine

def create_test_session_factory(engine):
    """Create a test session factory."""
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)


