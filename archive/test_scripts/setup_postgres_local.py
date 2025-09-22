#!/usr/bin/env python3
"""
Local PostgreSQL Setup Script
============================

This script sets up PostgreSQL locally without Docker.
It creates the database, user, and initializes the schema.
"""

import os
import sys
import subprocess
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def run_command(command, description):
    """Run a shell command and return the result."""
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description} completed successfully")
            return True
        else:
            print(f"❌ {description} failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ {description} failed with exception: {e}")
        return False

def setup_postgres():
    """Set up PostgreSQL database and user."""
    print("🚀 Setting up PostgreSQL locally...")
    print("=" * 50)
    
    # Database configuration
    DB_NAME = "common_db"
    DB_USER = "common_user"
    DB_PASSWORD = "common_password"
    DB_HOST = "localhost"
    DB_PORT = "5432"
    
    # Try to connect to PostgreSQL
    try:
        print("🔌 Connecting to PostgreSQL...")
        # Connect to default postgres database first
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database="postgres",
            user=os.getenv("USER", "postgres")  # Use current user or postgres
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Create database
        print(f"📊 Creating database '{DB_NAME}'...")
        cursor.execute(f"DROP DATABASE IF EXISTS {DB_NAME}")
        cursor.execute(f"CREATE DATABASE {DB_NAME}")
        print(f"✅ Database '{DB_NAME}' created successfully")
        
        # Create user (handle existing user)
        print(f"👤 Creating/updating user '{DB_USER}'...")
        try:
            cursor.execute(f"DROP USER IF EXISTS {DB_USER}")
        except:
            pass  # Ignore if user doesn't exist
        try:
            cursor.execute(f"CREATE USER {DB_USER} WITH PASSWORD '{DB_PASSWORD}'")
        except psycopg2.errors.DuplicateObject:
            print(f"   User '{DB_USER}' already exists, updating password...")
            cursor.execute(f"ALTER USER {DB_USER} WITH PASSWORD '{DB_PASSWORD}'")
        cursor.execute(f"GRANT ALL PRIVILEGES ON DATABASE {DB_NAME} TO {DB_USER}")
        print(f"✅ User '{DB_USER}' configured successfully")
        
        cursor.close()
        conn.close()
        
        # Test connection with new credentials
        print("🔍 Testing connection with new credentials...")
        test_conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        test_conn.close()
        print("✅ Connection test successful!")
        
        # Create environment file
        print("📝 Creating environment configuration...")
        env_content = f"""# Local PostgreSQL Configuration
DATABASE_URL=postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}
DB_HOST={DB_HOST}
DB_PORT={DB_PORT}
DB_NAME={DB_NAME}
DB_USER={DB_USER}
DB_PASSWORD={DB_PASSWORD}

# Application Configuration
JWT_SECRET_KEY=dev-secret-key-change-in-production
DEBUG=True
LOG_LEVEL=DEBUG
ENVIRONMENT=development

# Redis (optional for local development)
REDIS_URL=redis://localhost:6379
"""
        
        with open(".env.local", "w") as f:
            f.write(env_content)
        print("✅ Environment file '.env.local' created")
        
        print("\n🎉 PostgreSQL setup completed successfully!")
        print("=" * 50)
        print("Database Details:")
        print(f"  Host: {DB_HOST}")
        print(f"  Port: {DB_PORT}")
        print(f"  Database: {DB_NAME}")
        print(f"  User: {DB_USER}")
        print(f"  Password: {DB_PASSWORD}")
        print(f"  Connection URL: postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}")
        print("\nNext steps:")
        print("1. Run: python3 run_api_local.py")
        print("2. Run: python3 test_complete_supply_chain_flow.py")
        
        return True
        
    except psycopg2.OperationalError as e:
        print(f"❌ Cannot connect to PostgreSQL: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure PostgreSQL is running: brew services start postgresql@15")
        print("2. Check if PostgreSQL is listening on port 5432")
        print("3. Try connecting manually: psql postgres")
        return False
    except Exception as e:
        print(f"❌ Setup failed: {e}")
        return False

if __name__ == "__main__":
    success = setup_postgres()
    sys.exit(0 if success else 1)
