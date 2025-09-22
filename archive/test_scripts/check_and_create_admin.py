#!/usr/bin/env python3
"""
Simple script to check and create admin user.
"""
import os
import sys
import sqlite3
import hashlib
import uuid
from datetime import datetime

# Database path
DB_PATH = "common.db"

def hash_password(password: str) -> str:
    """Hash password using the same method as the app."""
    return hashlib.sha256(password.encode()).hexdigest()

def check_and_create_admin():
    """Check if admin exists and create if not."""
    
    if not os.path.exists(DB_PATH):
        print(f"❌ Database not found at {DB_PATH}")
        return False
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Check if users table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        if not cursor.fetchone():
            print("❌ Users table doesn't exist. Please run the backend first to initialize the database.")
            return False
        
        # Check if any admin users exist
        cursor.execute("SELECT * FROM users WHERE role = 'admin'")
        admin_users = cursor.fetchall()
        
        if admin_users:
            print(f"✅ Found {len(admin_users)} admin user(s):")
            for user in admin_users:
                print(f"   📧 Email: {user[1]}")  # email is column 1
                print(f"   👤 Name: {user[3]}")   # full_name is column 3
                print(f"   🔓 Active: {user[5]}")  # is_active is column 5
            return True
        
        # Check if companies table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='companies'")
        if not cursor.fetchone():
            print("❌ Companies table doesn't exist. Please run the backend first.")
            return False
        
        # Create admin company if it doesn't exist
        cursor.execute("SELECT * FROM companies WHERE email = 'admin@common.local'")
        company = cursor.fetchone()
        
        if not company:
            company_id = str(uuid.uuid4())
            cursor.execute("""
                INSERT INTO companies (id, name, company_type, email, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                company_id,
                "Common Platform",
                "brand",
                "admin@common.local",
                datetime.now().isoformat(),
                datetime.now().isoformat()
            ))
            print("✅ Created admin company")
        else:
            company_id = company[0]
            print("📋 Using existing admin company")
        
        # Create admin user
        user_id = str(uuid.uuid4())
        hashed_password = hash_password("admin123456")
        
        cursor.execute("""
            INSERT INTO users (id, email, hashed_password, full_name, role, is_active, company_id, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id,
            "admin@common.local",
            hashed_password,
            "Platform Administrator",
            "admin",
            True,
            company_id,
            datetime.now().isoformat(),
            datetime.now().isoformat()
        ))
        
        conn.commit()
        
        print("🎉 Admin user created successfully!")
        print("=" * 50)
        print("📧 Email: admin@common.local")
        print("🔑 Password: admin123456")
        print("👤 Role: admin")
        print("=" * 50)
        print("🚀 You can now log in to the admin dashboard!")
        
        return True
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Error: {str(e)}")
        return False
        
    finally:
        conn.close()

if __name__ == "__main__":
    print("🔍 Checking admin user status...")
    success = check_and_create_admin()
    sys.exit(0 if success else 1)