# conftest.py - Place this in your tests/ directory
import pytest
import os
import sys
from test_database_manager import TestDatabaseManager

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

@pytest.fixture(scope="session")
def test_db_manager():
    """Provide TestDatabaseManager instance for tests"""
    return TestDatabaseManager()

@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Set up test environment before any tests run"""
    # Ensure we're using test database
    os.environ['DATABASE_URL'] = 'postgresql://elisha@localhost:5432/common_test'
    os.environ['TESTING'] = 'true'
    
    # Set up test database
    manager = TestDatabaseManager()
    manager.setup_test_database()
    
    yield
    
    # Optional: Add cleanup here if needed
    print("🧹 Test session completed")

@pytest.fixture
def clean_db():
    """Provide a clean database state for individual tests"""
    manager = TestDatabaseManager()
    
    yield
    
    # Clean up after each test
    manager.cleanup_test_data()
    manager.seed_test_data()  # Re-seed for next test
