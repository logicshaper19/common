#!/usr/bin/env python3
"""
Manually create admin user with correct password.
"""
import sqlite3
import uuid
from datetime import datetime
from passlib.context import CryptContext

# Password hashing context (same as the app)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """Hash password using bcrypt."""
    return pwd_context.hash(password)

def create_admin():
    """Create admin user manually."""
    
    DB_PATH = "common.db"
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Check if company exists
        cursor.execute("SELECT id FROM companies WHERE email = ?", ("elisha@common.co",))
        company_result = cursor.fetchone()
        
        if not company_result:
            print("❌ Company not found")
            return False
        
        company_id = company_result[0]
        print(f"✅ Found company with ID: {company_id}")
        
        # Delete existing admin user if exists
        cursor.execute("DELETE FROM users WHERE email = ?", ("elisha@common.co",))
        print("🗑️ Deleted existing admin user")
        
        # Create new admin user
        user_id = str(uuid.uuid4()).replace('-', '')
        hashed_password = hash_password("password123")
        
        cursor.execute("""
            INSERT INTO users (id, email, hashed_password, full_name, role, is_active, company_id, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id,
            "elisha@common.co",
            hashed_password,
            "Elisha",
            "admin",
            1,
            company_id,
            datetime.utcnow().isoformat(),
            datetime.utcnow().isoformat()
        ))
        
        conn.commit()
        print("✅ Admin user created successfully!")
        print(f"   Email: elisha@common.co")
        print(f"   Password: password123")
        print(f"   User ID: {user_id}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    create_admin()
