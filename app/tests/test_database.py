"""
Test database configuration using PostgreSQL.
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Use PostgreSQL for tests
TEST_DATABASE_URL = "postgresql://postgres:password@localhost:5432/test_common_platform"

def create_test_engine():
    """Create a test engine that works with PostgreSQL."""
    engine = create_engine(
        TEST_DATABASE_URL,
        poolclass=StaticPool,
        echo=False,
        pool_pre_ping=True
    )
    return engine

def create_test_session_factory(engine):
    """Create a test session factory."""
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)

def setup_test_database():
    """Set up the test database with only essential tables."""
    from app.tests.test_models import Base as TestBase
    from app.core.database import Base as AppBase
    
    engine = create_test_engine()
    
    # Create only the test-compatible tables
    TestBase.metadata.create_all(bind=engine)
    
    # Create essential app tables (without JSONB columns)
    essential_tables = [
        'users', 'companies', 'products', 'purchase_orders', 
        'sectors', 'harvest_batches', 'certifications', 'farm_information'
    ]
    
    # Filter metadata to only include essential tables
    for table_name in essential_tables:
        if table_name in AppBase.metadata.tables:
            table = AppBase.metadata.tables[table_name]
            # Create table without JSONB columns
            table.create(engine, checkfirst=True)
    
    return engine


