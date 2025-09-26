#!/usr/bin/env python3
"""
Debug script for authentication issues with manager@plantationestate.com
Run this from the project root: python debug_auth_manager.py
"""

import asyncio
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
from app.models.company import Company
from passlib.context import CryptContext
from app.core.security import verify_password, hash_password
from app.services.auth import AuthService

def debug_authentication_issue():
    """Debug the authentication issue for manager@plantationestate.com"""
    
    print("🔍 DEBUGGING AUTHENTICATION ISSUE")
    print("=" * 50)
    
    email = "manager@plantationestate.com"
    password = "PlantationGrower2024!"
    
    # Get database session
    db_gen = get_db()
    db: Session = next(db_gen)
    
    try:
        # Step 1: Check if user exists
        print(f"\n1️⃣ CHECKING USER EXISTENCE")
        print(f"Email: {email}")
        
        user = db.query(User).filter(User.email == email).first()
        
        if not user:
            print("❌ USER NOT FOUND!")
            print("   This user does not exist in the database.")
            
            # Check similar emails
            similar_users = db.query(User).filter(User.email.like(f"%plantation%")).all()
            if similar_users:
                print(f"\n📧 Found {len(similar_users)} similar emails:")
                for u in similar_users:
                    print(f"   - {u.email} (Active: {u.is_active})")
            
            # Check all users
            all_users = db.query(User).limit(10).all()
            print(f"\n👥 First 10 users in database:")
            for u in all_users:
                print(f"   - {u.email} (Active: {u.is_active}, Role: {u.role})")
            return
        
        print(f"✅ USER FOUND!")
        print(f"   - ID: {user.id}")
        print(f"   - Email: {user.email}")
        print(f"   - Full Name: {user.full_name}")
        print(f"   - Role: {user.role}")
        print(f"   - Is Active: {user.is_active}")
        print(f"   - Company ID: {user.company_id}")
        print(f"   - Created: {user.created_at}")
        
        # Step 2: Check company
        print(f"\n2️⃣ CHECKING COMPANY")
        if user.company_id:
            company = db.query(Company).filter(Company.id == user.company_id).first()
            
            if not company:
                print("❌ COMPANY NOT FOUND!")
                print(f"   User has company_id: {user.company_id}, but company doesn't exist!")
            else:
                print(f"✅ COMPANY FOUND!")
                print(f"   - Company Name: {company.name}")
                print(f"   - Company Type: {company.company_type}")
        else:
            print("⚠️  No company_id set for user")
        
        # Step 3: Check user active status
        print(f"\n3️⃣ CHECKING USER STATUS")
        if not user.is_active:
            print("❌ USER IS INACTIVE!")
            print("   This user account has been deactivated.")
            return
        
        print("✅ USER IS ACTIVE!")
        
        # Step 4: Debug password verification
        print(f"\n4️⃣ DEBUGGING PASSWORD VERIFICATION")
        print(f"Password to verify: {password}")
        print(f"Password length: {len(password)} characters")
        print(f"Stored hash: {user.hashed_password[:50]}...")
        print(f"Hash length: {len(user.hashed_password)} characters")
        
        # Test with different bcrypt contexts
        contexts_to_test = [
            ("Default Context", CryptContext(schemes=["bcrypt"], deprecated="auto")),
            ("Simple Context", CryptContext(schemes=["bcrypt"])),
            ("12 Rounds", CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)),
        ]
        
        for name, ctx in contexts_to_test:
            try:
                is_valid = ctx.verify(password, user.hashed_password)
                print(f"   {name}: {'✅ VALID' if is_valid else '❌ INVALID'}")
                if is_valid:
                    print(f"   🎉 PASSWORD VERIFICATION SUCCESSFUL with {name}!")
            except Exception as e:
                print(f"   {name}: ❌ ERROR - {str(e)}")
        
        # Test with your security module function
        try:
            print(f"\n   Testing with security module...")
            is_valid_security = verify_password(password, user.hashed_password)
            print(f"   Security Module: {'✅ VALID' if is_valid_security else '❌ INVALID'}")
        except Exception as e:
            print(f"   Security Module: ❌ ERROR - {str(e)}")
        
        # Step 5: Test password hash recreation
        print(f"\n5️⃣ TESTING PASSWORD HASH RECREATION")
        try:
            new_hash = hash_password(password)
            print(f"New hash: {new_hash[:50]}...")
            
            # Test verification with new hash
            is_valid_new = verify_password(password, new_hash)
            print(f"New hash verification: {'✅ VALID' if is_valid_new else '❌ INVALID'}")
            
        except Exception as e:
            print(f"❌ ERROR creating new hash: {str(e)}")
        
        # Step 6: Test AuthService
        print(f"\n6️⃣ TESTING AUTH SERVICE")
        try:
            auth_service = AuthService(db)
            authenticated_user = auth_service.authenticate_user(email, password)
            
            if authenticated_user:
                print("✅ AUTH SERVICE SUCCESSFUL!")
                print(f"   Returned user: {authenticated_user.email}")
            else:
                print("❌ AUTH SERVICE FAILED!")
                print("   authenticate_user returned None")
                
        except Exception as e:
            print(f"❌ AUTH SERVICE ERROR: {str(e)}")
            import traceback
            traceback.print_exc()
        
        # Step 7: Check for common issues
        print(f"\n7️⃣ CHECKING FOR COMMON ISSUES")
        
        # Check password encoding
        if password != password.strip():
            print("⚠️  PASSWORD HAS LEADING/TRAILING WHITESPACE!")
        else:
            print("✅ Password has no whitespace issues")
        
        # Check for special characters
        print(f"   Password contains: {repr(password)}")
        
        # Step 8: Environment checks
        print(f"\n8️⃣ ENVIRONMENT CHECKS")
        print(f"   JWT_SECRET_KEY exists: {bool(os.getenv('JWT_SECRET_KEY'))}")
        print(f"   OPENAI_API_KEY exists: {bool(os.getenv('OPENAI_API_KEY'))}")
        print(f"   DATABASE_URL: {os.getenv('DATABASE_URL', 'Not set')}")
        print(f"   DEBUG mode: {os.getenv('DEBUG', 'Not set')}")
        
    except Exception as e:
        print(f"❌ CRITICAL ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        
    finally:
        db.close()

def fix_password_if_needed():
    """Fix the password hash if the issue is identified"""
    
    print("\n🔧 ATTEMPTING TO FIX PASSWORD HASH")
    print("=" * 40)
    
    email = "manager@plantationestate.com"
    password = "PlantationGrower2024!"
    
    # Get database session
    db_gen = get_db()
    db: Session = next(db_gen)
    
    try:
        user = db.query(User).filter(User.email == email).first()
        
        if not user:
            print("❌ User not found - cannot fix")
            return
        
        # Create new password hash
        new_hash = hash_password(password)
        
        print(f"Old hash: {user.hashed_password[:50]}...")
        print(f"New hash: {new_hash[:50]}...")
        
        # Test new hash
        is_valid = verify_password(password, new_hash)
        if not is_valid:
            print("❌ New hash is invalid - something is seriously wrong")
            return
        
        print("✅ New hash is valid")
        
        # Update user password
        old_hash = user.hashed_password
        user.hashed_password = new_hash
        db.commit()
        
        print("✅ PASSWORD HASH UPDATED SUCCESSFULLY!")
        print("   Try logging in now.")
        
        # Test the fix
        test_auth = AuthService(db)
        test_user = test_auth.authenticate_user(email, password)
        if test_user:
            print("✅ AUTHENTICATION TEST SUCCESSFUL!")
        else:
            print("❌ Authentication still failing - reverting change")
            user.hashed_password = old_hash
            db.commit()
        
    except Exception as e:
        print(f"❌ ERROR FIXING PASSWORD: {str(e)}")
        db.rollback()
        import traceback
        traceback.print_exc()
        
    finally:
        db.close()

if __name__ == "__main__":
    print("🚀 AUTHENTICATION DEBUG TOOL")
    print("============================")
    
    debug_authentication_issue()
    
    print("\n" + "="*50)
    fix_choice = input("Would you like to attempt to fix the password hash? (y/N): ")
    
    if fix_choice.lower() in ['y', 'yes']:
        fix_password_if_needed()
    
    print("\n✅ Debug complete!")
