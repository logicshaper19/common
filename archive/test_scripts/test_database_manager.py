# test_database_manager.py
import os
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import pytest
from datetime import datetime
import uuid

class TestDatabaseManager:
    """Manages test database lifecycle - reset, seed, cleanup"""
    
    def __init__(self, test_db_url=None):
        self.test_db_url = test_db_url or os.getenv('TEST_DATABASE_URL', 'postgresql://elisha@localhost:5432/common_test')
        self.base_db_url = 'postgresql://elisha@localhost:5432/postgres'  # For admin operations
        
    def reset_test_database(self):
        """Drop and recreate the test database"""
        print("🔄 Resetting test database...")
        
        # Connect to postgres db to manage test db
        conn = psycopg2.connect(self.base_db_url)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        try:
            # Terminate existing connections to test db
            cursor.execute("""
                SELECT pg_terminate_backend(pid)
                FROM pg_stat_activity
                WHERE datname = 'common_test' AND pid <> pg_backend_pid()
            """)
            
            # Drop and recreate test database
            cursor.execute("DROP DATABASE IF EXISTS common_test")
            cursor.execute("CREATE DATABASE common_test")
            print("✅ Test database reset complete")
            
        finally:
            cursor.close()
            conn.close()
    
    def apply_schema(self):
        """Apply the current schema to test database"""
        print("📋 Applying schema to test database...")
        
        # Get schema from production/development database
        dev_db_url = os.getenv('DEV_DATABASE_URL', 'postgresql://elisha@localhost:5432/common_dev')
        
        # Use pg_dump to get schema and apply it
        import subprocess
        
        # Export schema from dev database
        dump_cmd = f'pg_dump --schema-only "{dev_db_url}"'
        result = subprocess.run(dump_cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode != 0:
            raise Exception(f"Schema export failed: {result.stderr}")
        
        # Apply schema to test database
        test_conn = psycopg2.connect(self.test_db_url)
        test_cursor = test_conn.cursor()
        
        try:
            test_cursor.execute(result.stdout)
            test_conn.commit()
            print("✅ Schema applied to test database")
            
        finally:
            test_cursor.close()
            test_conn.close()
    
    def seed_test_data(self):
        """Seed the test database with known test data"""
        print("🌱 Seeding test database with test data...")
        
        conn = psycopg2.connect(self.test_db_url)
        cursor = conn.cursor()
        
        try:
            # Seed test users
            test_users = [
                (str(uuid.uuid4()), 'testuser1@example.com', 'Test User 1', 'farmer', True),
                (str(uuid.uuid4()), 'testuser2@example.com', 'Test User 2', 'admin', True),
                (str(uuid.uuid4()), 'testcompany@example.com', 'Test Company', 'company', True),
            ]
            
            cursor.executemany("""
                INSERT INTO users (id, email, name, user_type, is_active)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (email) DO NOTHING
            """, test_users)
            
            # Seed test companies
            test_companies = [
                (str(uuid.uuid4()), 'Test Farm Co', 'Organic vegetables and fruits'),
                (str(uuid.uuid4()), 'Green Valley Farm', 'Dairy and livestock'),
            ]
            
            cursor.executemany("""
                INSERT INTO companies (id, name, description)
                VALUES (%s, %s, %s)
                ON CONFLICT DO NOTHING
            """, test_companies)
            
            # Seed test products
            test_products = [
                (str(uuid.uuid4()), 'Test Tomatoes', 'Fresh organic tomatoes', 2.50),
                (str(uuid.uuid4()), 'Test Carrots', 'Fresh organic carrots', 1.80),
            ]
            
            cursor.executemany("""
                INSERT INTO products (id, name, description, price)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT DO NOTHING
            """, test_products)
            
            conn.commit()
            print("✅ Test data seeded successfully")
            
        except Exception as e:
            conn.rollback()
            print(f"❌ Error seeding test data: {e}")
            raise
        finally:
            cursor.close()
            conn.close()
    
    def setup_test_database(self):
        """Complete test database setup - reset, schema, seed"""
        print("🏗️  Setting up test database...")
        self.reset_test_database()
        self.apply_schema()
        self.seed_test_data()
        print("🎉 Test database setup complete!")
    
    def cleanup_test_data(self):
        """Clean up test data after tests (optional)"""
        print("🧹 Cleaning up test data...")
        
        conn = psycopg2.connect(self.test_db_url)
        cursor = conn.cursor()
        
        try:
            # Clean up in reverse order of dependencies
            cursor.execute("DELETE FROM purchase_orders WHERE 1=1")
            cursor.execute("DELETE FROM products WHERE name LIKE 'Test%'")
            cursor.execute("DELETE FROM companies WHERE name LIKE 'Test%'")
            cursor.execute("DELETE FROM users WHERE email LIKE '%@example.com'")
            
            conn.commit()
            print("✅ Test data cleaned up")
            
        except Exception as e:
            conn.rollback()
            print(f"❌ Error cleaning up test data: {e}")
        finally:
            cursor.close()
            conn.close()


# Pytest fixtures for automatic setup/teardown
@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """Automatically set up test database at start of test session"""
    manager = TestDatabaseManager()
    manager.setup_test_database()
    
    yield  # Run tests
    
    # Optional: cleanup after all tests
    # manager.cleanup_test_data()


@pytest.fixture(scope="function")
def test_db_transaction():
    """Provide a database transaction that's rolled back after each test"""
    conn = psycopg2.connect(os.getenv('TEST_DATABASE_URL', 'postgresql://elisha@localhost:5432/common_test'))
    trans = conn.begin()
    
    yield conn
    
    trans.rollback()
    conn.close()


# Manual usage example
if __name__ == "__main__":
    manager = TestDatabaseManager()
    manager.setup_test_database()
