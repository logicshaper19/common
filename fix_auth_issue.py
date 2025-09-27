#!/usr/bin/env python3
"""
Fix the authentication issue for manager@plantationestate.com
The issue is bcrypt thinks the 21-character password is > 72 bytes
"""

import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.user import User
from passlib.context import CryptContext
import bcrypt

def fix_authentication_issue():
    """Fix the bcrypt password issue for manager@plantationestate.com"""
    
    print("🔧 FIXING AUTHENTICATION ISSUE")
    print("=" * 40)
    
    email = "manager@plantationestate.com"
    password = "PlantationGrower2024!"
    
    print(f"Email: {email}")
    print(f"Password: {password}")
    print(f"Password length: {len(password)} characters")
    print(f"Password bytes: {len(password.encode('utf-8'))} bytes")
    
    # Get database session
    db_gen = get_db()
    db: Session = next(db_gen)
    
    try:
        user = db.query(User).filter(User.email == email).first()
        
        if not user:
            print("❌ User not found!")
            return
        
        print(f"✅ User found: {user.full_name}")
        print(f"Current hash: {user.hashed_password[:50]}...")
        
        # The issue: bcrypt has a 72-byte limit, but our password is only 21 chars
        # This suggests there's an encoding issue or bcrypt version problem
        
        # Solution 1: Use direct bcrypt instead of passlib
        print(f"\n🔧 SOLUTION 1: Direct bcrypt hashing")
        try:
            # Ensure password is properly encoded
            password_bytes = password.encode('utf-8')
            print(f"Password as bytes: {len(password_bytes)} bytes")
            
            if len(password_bytes) > 72:
                print(f"⚠️  Password is too long, truncating to 72 bytes")
                password_bytes = password_bytes[:72]
            
            # Create new hash with direct bcrypt
            salt = bcrypt.gensalt(rounds=12)
            new_hash = bcrypt.hashpw(password_bytes, salt)
            new_hash_str = new_hash.decode('utf-8')
            
            print(f"New hash created: {new_hash_str[:50]}...")
            
            # Test verification
            is_valid = bcrypt.checkpw(password_bytes, new_hash)
            print(f"Direct bcrypt verification: {'✅ VALID' if is_valid else '❌ INVALID'}")
            
            if is_valid:
                # Update user password
                old_hash = user.hashed_password
                user.hashed_password = new_hash_str
                db.commit()
                
                print("✅ PASSWORD UPDATED SUCCESSFULLY!")
                
                # Test with passlib now
                from app.core.security import verify_password
                try:
                    passlib_valid = verify_password(password, new_hash_str)
                    print(f"Passlib verification: {'✅ VALID' if passlib_valid else '❌ INVALID'}")
                except Exception as e:
                    print(f"❌ Passlib still failing: {str(e)}")
                    # Revert if passlib still fails
                    user.hashed_password = old_hash
                    db.commit()
                    print("❌ Reverted changes - passlib compatibility issue")
                    return
                
                # Final test with AuthService
                from app.services.auth import AuthService
                try:
                    auth_service = AuthService(db)
                    test_user = auth_service.authenticate_user(email, password)
                    if test_user:
                        print("🎉 AUTHENTICATION SERVICE TEST SUCCESSFUL!")
                        print("✅ User can now log in successfully!")
                    else:
                        print("❌ Authentication service still failing")
                except Exception as e:
                    print(f"❌ Authentication service error: {str(e)}")
                
            else:
                print("❌ Direct bcrypt verification failed")
                
        except Exception as e:
            print(f"❌ Direct bcrypt solution failed: {str(e)}")
        
        # Solution 2: Try with shorter password if the long one doesn't work
        print(f"\n🔧 SOLUTION 2: Testing with shorter password")
        shorter_password = "PlantationGrower"  # 16 characters
        
        try:
            shorter_bytes = shorter_password.encode('utf-8')
            print(f"Shorter password: {shorter_password} ({len(shorter_bytes)} bytes)")
            
            salt = bcrypt.gensalt(rounds=12)
            shorter_hash = bcrypt.hashpw(shorter_bytes, salt)
            shorter_hash_str = shorter_hash.decode('utf-8')
            
            # Test verification
            is_valid_shorter = bcrypt.checkpw(shorter_bytes, shorter_hash)
            print(f"Shorter password verification: {'✅ VALID' if is_valid_shorter else '❌ INVALID'}")
            
            if is_valid_shorter:
                print("✅ Shorter password works with bcrypt")
                print("💡 Consider using a shorter password for this user")
            
        except Exception as e:
            print(f"❌ Shorter password test failed: {str(e)}")
            
    except Exception as e:
        print(f"❌ CRITICAL ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        db.rollback()
        
    finally:
        db.close()

def test_current_authentication():
    """Test if the current authentication is working"""
    
    print("\n🧪 TESTING CURRENT AUTHENTICATION")
    print("=" * 35)
    
    email = "manager@plantationestate.com"
    password = "PlantationGrower2024!"
    
    db_gen = get_db()
    db: Session = next(db_gen)
    
    try:
        from app.services.auth import AuthService
        auth_service = AuthService(db)
        
        print(f"Testing login for: {email}")
        user = auth_service.authenticate_user(email, password)
        
        if user:
            print("🎉 AUTHENTICATION SUCCESSFUL!")
            print(f"Logged in as: {user.full_name}")
            return True
        else:
            print("❌ Authentication failed")
            return False
            
    except Exception as e:
        print(f"❌ Authentication error: {str(e)}")
        return False
        
    finally:
        db.close()

if __name__ == "__main__":
    print("🚀 AUTHENTICATION FIX TOOL")
    print("==========================")
    
    # First test if it's already working
    if test_current_authentication():
        print("✅ Authentication is already working!")
    else:
        print("❌ Authentication is broken - attempting fix...")
        fix_authentication_issue()
        
        # Test again after fix
        print("\n🔄 RETESTING AFTER FIX...")
        if test_current_authentication():
            print("🎉 FIX SUCCESSFUL!")
        else:
            print("❌ Fix failed - manual intervention needed")
    
    print("\n✅ Done!")
