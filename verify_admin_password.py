#!/usr/bin/env python3
"""
Verify admin password directly against the database.
"""
import os
import sys
import sqlite3
from passlib.context import CryptContext

# Password hashing context (same as the app)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)

def test_admin_password():
    """Test admin password verification."""
    
    DB_PATH = "../common.db"
    
    if not os.path.exists(DB_PATH):
        print(f"❌ Database not found at {DB_PATH}")
        return False
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Get admin user
        cursor.execute("SELECT email, hashed_password, full_name, role, is_active FROM users WHERE role = 'admin'")
        admin_users = cursor.fetchall()
        
        if not admin_users:
            print("❌ No admin users found in database")
            return False
        
        print(f"✅ Found {len(admin_users)} admin user(s):")
        
        for user in admin_users:
            email, hashed_password, full_name, role, is_active = user
            print(f"\n👤 Admin User: {full_name}")
            print(f"📧 Email: {email}")
            print(f"🔓 Active: {bool(is_active)}")
            
            # Test different passwords
            test_passwords = [
                "adminpassword123",
                "admin123456", 
                "password123",
                "admin",
                "slp225"
            ]
            
            print("\n🔐 Testing passwords:")
            for password in test_passwords:
                try:
                    is_valid = verify_password(password, hashed_password)
                    status = "✅ VALID" if is_valid else "❌ Invalid"
                    print(f"   {password}: {status}")
                    
                    if is_valid:
                        print(f"\n🎉 WORKING CREDENTIALS FOUND!")
                        print(f"📧 Email: {email}")
                        print(f"🔑 Password: {password}")
                        return True
                        
                except Exception as e:
                    print(f"   {password}: ❌ Error - {str(e)}")
        
        print("\n❌ No valid passwords found for any admin user")
        return False
        
    except Exception as e:
        print(f"❌ Database error: {str(e)}")
        return False
        
    finally:
        conn.close()

if __name__ == "__main__":
    print("🔍 Verifying admin password...")
    success = test_admin_password()
    
    if not success:
        print("\n💡 Suggestions:")
        print("1. The admin user might have been created with a different password")
        print("2. Try running the create_admin_user.py script to create a new admin")
        print("3. Check if the password hashing method has changed")
        print("4. Look at the test fixtures to see what password was used")