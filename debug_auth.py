#!/usr/bin/env python3

import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.abspath('.'))

try:
    from app.core.database import get_db
    from app.models.user import User
    from app.models.company import Company
    from app.core.security import verify_password, hash_password
    from sqlalchemy.orm import Session
    
    def check_user_and_auth():
        """Check if user exists and can authenticate"""
        
        print("=== Database Connection Test ===")
        try:
            db = next(get_db())
            print("✅ Database connection successful")
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            return
        
        print("\n=== User Existence Check ===")
        try:
            user = db.query(User).filter(User.email == "elisha@common.co").first()
            if user:
                print(f"✅ User found: {user.email}")
                print(f"   Full Name: {user.full_name}")
                print(f"   Role: {user.role}")
                print(f"   Active: {user.is_active}")
                print(f"   Company ID: {user.company_id}")
                print(f"   User ID: {user.id}")
                
                # Check company
                if user.company_id:
                    company = db.query(Company).filter(Company.id == user.company_id).first()
                    if company:
                        print(f"   Company: {company.name} ({company.company_type})")
                    else:
                        print("   ❌ Company not found")
                else:
                    print("   ❌ No company ID")
                
            else:
                print("❌ User not found")
                return None, None
                
        except Exception as e:
            print(f"❌ User query failed: {e}")
            return None, None
        
        print("\n=== Password Verification Test ===")
        try:
            # Test password verification
            test_password = "password123"
            is_valid = verify_password(test_password, user.hashed_password)
            print(f"Password verification result: {is_valid}")
            
            if not is_valid:
                print("❌ Password verification failed")
                print(f"   Stored hash: {user.hashed_password[:50]}...")
                
                # Try to create a new hash and see if it works
                new_hash = hash_password(test_password)
                print(f"   New hash: {new_hash[:50]}...")
                is_new_valid = verify_password(test_password, new_hash)
                print(f"   New hash verification: {is_new_valid}")
                
            else:
                print("✅ Password verification successful")
                
        except Exception as e:
            print(f"❌ Password verification error: {e}")
        
        print("\n=== Manual Authentication Test ===")
        try:
            from app.services.auth import AuthService
            
            auth_service = AuthService(db)
            authenticated_user = auth_service.authenticate_user("elisha@common.co", "password123")
            
            if authenticated_user:
                print("✅ Manual authentication successful")
                print(f"   Authenticated user: {authenticated_user.email}")
            else:
                print("❌ Manual authentication failed")
                
        except Exception as e:
            print(f"❌ Manual authentication error: {e}")
        
        db.close()
        return user, is_valid
    
    if __name__ == "__main__":
        check_user_and_auth()
        
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you're running this from the project root directory")
except Exception as e:
    print(f"❌ Unexpected error: {e}")
