#!/usr/bin/env python3
"""
Test login functionality
"""
import sys
import os
sys.path.append('/Users/elisha/common')

from app.core.database import SessionLocal
from app.models.user import User
from app.core.security import verify_password
from app.core.auth import authenticate_user

def test_login():
    """Test login with different credentials"""
    
    print("🔐 Testing login functionality...")
    print("=" * 50)
    
    db = SessionLocal()
    
    try:
        # Test credentials
        test_credentials = [
            'sustainability@loreal.com',
            'plantation@astra-agro.com',
            'trader@wilmar-intl.com',
            'refinery@ioigroup.com',
            'millmanager@simeplantation.com',
            'coop@sawitberkelanjutan.co.id'
        ]
        
        for email in test_credentials:
            print(f"\n🧪 Testing: {email}")
            print("-" * 30)
            
            # Check if user exists
            user = db.query(User).filter(User.email == email).first()
            if not user:
                print(f"❌ User not found: {email}")
                continue
            
            print(f"✅ User found: {user.full_name}")
            print(f"   Role: {user.role}")
            print(f"   Company: {user.company.name if user.company else 'No company'}")
            print(f"   Active: {user.is_active}")
            
            # Test password verification
            password = 'password123'
            password_valid = verify_password(password, user.hashed_password)
            print(f"   Password 'password123' valid: {password_valid}")
            
            # Test authentication function
            try:
                auth_user = authenticate_user(db, email, password)
                if auth_user:
                    print(f"   ✅ Authentication successful")
                else:
                    print(f"   ❌ Authentication failed")
            except Exception as e:
                print(f"   ❌ Authentication error: {e}")
            
            print()
        
        # Test with wrong password
        print("🧪 Testing with wrong password:")
        print("-" * 30)
        
        test_user = db.query(User).filter(User.email == 'sustainability@loreal.com').first()
        if test_user:
            wrong_password = 'wrongpassword'
            password_valid = verify_password(wrong_password, test_user.hashed_password)
            print(f"Password 'wrongpassword' valid: {password_valid}")
            
            try:
                auth_user = authenticate_user(db, 'sustainability@loreal.com', wrong_password)
                if auth_user:
                    print(f"   ✅ Authentication successful (unexpected)")
                else:
                    print(f"   ❌ Authentication failed (expected)")
            except Exception as e:
                print(f"   ❌ Authentication error: {e}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_login()
