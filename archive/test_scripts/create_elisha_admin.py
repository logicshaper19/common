#!/usr/bin/env python3
"""
Create Elisha's admin user directly.
"""
import os
import sys
import sqlite3
from passlib.context import CryptContext
import uuid
from datetime import datetime

# Password hashing context (same as the app)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """Hash password using bcrypt."""
    return pwd_context.hash(password)

def create_elisha_admin():
    """Create Elisha's admin user."""
    
    DB_PATH = "../common.db"
    
    if not os.path.exists(DB_PATH):
        print(f"❌ Database not found at {DB_PATH}")
        return False
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Check if user already exists
        cursor.execute("SELECT * FROM users WHERE email = 'elisha@common.co'")
        existing_user = cursor.fetchone()
        
        if existing_user:
            print("✅ User elisha@common.co already exists!")
            print("📧 Email: elisha@common.co")
            print("🔑 Try password: slp225admin")
            return True
        
        # Check if admin company exists
        cursor.execute("SELECT * FROM companies WHERE email = 'elisha@common.co'")
        company = cursor.fetchone()
        
        if not company:
            # Create company
            company_id = str(uuid.uuid4())
            cursor.execute("""
                INSERT INTO companies (id, name, company_type, email, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                company_id,
                "Common Platform",
                "brand",
                "elisha@common.co",
                datetime.now().isoformat(),
                datetime.now().isoformat()
            ))
            print("✅ Created company for Elisha")
        else:
            company_id = company[0]
            print("📋 Using existing company")
        
        # Create admin user
        user_id = str(uuid.uuid4())
        hashed_password = hash_password("slp225admin")
        
        cursor.execute("""
            INSERT INTO users (id, email, hashed_password, full_name, role, is_active, company_id, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id,
            "elisha@common.co",
            hashed_password,
            "Elisha",
            "admin",
            True,
            company_id,
            datetime.now().isoformat(),
            datetime.now().isoformat()
        ))
        
        conn.commit()
        
        print("🎉 Elisha's admin user created successfully!")
        print("=" * 50)
        print("📧 Email: elisha@common.co")
        print("🔑 Password: slp225admin")
        print("👤 Name: Elisha")
        print("🔓 Role: admin")
        print("=" * 50)
        print("🚀 You can now log in with these credentials!")
        
        return True
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Error: {str(e)}")
        return False
        
    finally:
        conn.close()

if __name__ == "__main__":
    print("🔧 Creating Elisha's admin user...")
    success = create_elisha_admin()
    sys.exit(0 if success else 1)