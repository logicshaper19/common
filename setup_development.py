#!/usr/bin/env python3
"""
Development Setup Script

This script sets up the development environment by:
1. Creating the PostgreSQL database
2. Creating the test user
3. Verifying the setup

Usage:
    python setup_development.py
"""

import psycopg2
import uuid
from datetime import datetime
from passlib.context import CryptContext

def setup_database():
    """Setup PostgreSQL database and user"""
    print("🗄️  Setting up PostgreSQL database...")
    
    try:
        # Connect to PostgreSQL as superuser
        conn = psycopg2.connect(
            host="localhost",
            port="5432",
            user="postgres",
            database="postgres"
        )
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Create database
        cursor.execute("CREATE DATABASE common_db")
        print("✅ Database 'common_db' created")
        
        # Create user
        cursor.execute("CREATE USER common_user WITH PASSWORD 'common_password'")
        print("✅ User 'common_user' created")
        
        # Grant privileges
        cursor.execute("GRANT ALL PRIVILEGES ON DATABASE common_db TO common_user")
        print("✅ Privileges granted")
        
        conn.close()
        return True
        
    except psycopj2.errors.DuplicateDatabase:
        print("ℹ️  Database already exists")
        return True
    except Exception as e:
        print(f"❌ Database setup failed: {e}")
        return False

def setup_test_data():
    """Setup test data"""
    print("👤 Setting up test user...")
    
    try:
        # Connect to the database
        conn = psycopg2.connect(
            host="localhost",
            port="5432",
            user="common_user",
            password="common_password",
            database="common_db"
        )
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Create companies table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS companies (
                id UUID PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                company_type VARCHAR(50) NOT NULL,
                email VARCHAR(255) UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id UUID PRIMARY KEY,
                email VARCHAR(255) UNIQUE NOT NULL,
                hashed_password VARCHAR(255) NOT NULL,
                full_name VARCHAR(255),
                role VARCHAR(50) DEFAULT 'user',
                is_active BOOLEAN DEFAULT TRUE,
                company_id UUID REFERENCES companies(id),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create products table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id UUID PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                description TEXT,
                category VARCHAR(100),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create purchase_orders table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS purchase_orders (
                id UUID PRIMARY KEY,
                po_number VARCHAR(100) UNIQUE NOT NULL,
                status VARCHAR(50) DEFAULT 'pending',
                buyer_company_id UUID REFERENCES companies(id),
                seller_company_id UUID REFERENCES companies(id),
                product_id UUID REFERENCES products(id),
                quantity INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        print("✅ Database tables created")
        
        # Create test company
        company_id = str(uuid.uuid4())
        cursor.execute("""
            INSERT INTO companies (id, name, company_type, email, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (email) DO NOTHING
        """, (
            company_id,
            "Test Manufacturing Company",
            "manufacturer",
            "test@manufacturer.com",
            datetime.now(),
            datetime.now()
        ))
        
        # Create test user
        user_id = str(uuid.uuid4())
        password = "TestPass123!"
        pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
        hashed_password = pwd_context.hash(password)
        
        cursor.execute("""
            INSERT INTO users (id, email, hashed_password, full_name, role, is_active, company_id, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (email) DO NOTHING
        """, (
            user_id,
            "admin@testmanufacturer.com",
            hashed_password,
            "Test Admin User",
            "admin",
            True,
            company_id,
            datetime.now(),
            datetime.now()
        ))
        
        print("✅ Test data created")
        print("   Company: Test Manufacturing Company")
        print("   User: admin@testmanufacturer.com")
        print("   Password: TestPass123!")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Test data setup failed: {e}")
        return False

def verify_setup():
    """Verify the setup"""
    print("🔍 Verifying setup...")
    
    try:
        # Test database connection
        conn = psycopg2.connect(
            host="localhost",
            port="5432",
            user="common_user",
            password="common_password",
            database="common_db"
        )
        cursor = conn.cursor()
        
        # Check tables
        cursor.execute("SELECT COUNT(*) FROM companies")
        company_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        
        print(f"✅ Database connection successful")
        print(f"✅ Companies: {company_count}")
        print(f"✅ Users: {user_count}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        return False

def main():
    """Main function"""
    print("Supply Chain Platform - Development Setup")
    print("=" * 45)
    
    # Setup database
    if not setup_database():
        print("❌ Database setup failed")
        return False
    
    # Setup test data
    if not setup_test_data():
        print("❌ Test data setup failed")
        return False
    
    # Verify setup
    if not verify_setup():
        print("❌ Setup verification failed")
        return False
    
    print("\n🎉 Development setup complete!")
    print("\nNext steps:")
    print("1. Start the API: python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload")
    print("2. Start the frontend: cd frontend && npm start")
    print("3. Test the flow: python test_supply_chain_flow.py")
    
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)



