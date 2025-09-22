#!/usr/bin/env python3
"""
Check credentials and test data
"""
import sys
import os
sys.path.append('/Users/elisha/common')

from app.core.database import SessionLocal
from app.models.user import User
from app.models.company import Company
from app.core.security import verify_password

def check_credentials():
    """Check what credentials exist in the database"""
    
    print("🔍 Checking credentials and test data...")
    print("=" * 50)
    
    db = SessionLocal()
    
    try:
        # Check all companies
        companies = db.query(Company).all()
        print(f"\n🏢 COMPANIES FOUND: {len(companies)}")
        print("-" * 30)
        
        for company in companies:
            print(f"  {company.name} ({company.company_type}) - {company.email}")
        
        # Check all users
        users = db.query(User).all()
        print(f"\n👤 USERS FOUND: {len(users)}")
        print("-" * 30)
        
        for user in users:
            print(f"  {user.email} - {user.full_name} ({user.role})")
            print(f"    Company: {user.company.name if user.company else 'No company'}")
            print(f"    Active: {user.is_active}")
            print()
        
        # Test specific L'Oréal credentials
        print("🧪 TESTING L'ORÉAL CREDENTIALS:")
        print("-" * 30)
        
        loreal_users = [
            'sustainability@loreal.com',
            'procurement@loreal.com',
            'csr@loreal.com'
        ]
        
        for email in loreal_users:
            user = db.query(User).filter(User.email == email).first()
            if user:
                print(f"✅ {email} - EXISTS")
                print(f"   Name: {user.full_name}")
                print(f"   Role: {user.role}")
                print(f"   Company: {user.company.name if user.company else 'No company'}")
                print(f"   Active: {user.is_active}")
                
                # Test password
                test_password = 'password123'
                password_valid = verify_password(test_password, user.hashed_password)
                print(f"   Password 'password123' valid: {password_valid}")
            else:
                print(f"❌ {email} - NOT FOUND")
            print()
        
        # Test Astra Agro credentials
        print("🧪 TESTING ASTRA AGRO CREDENTIALS:")
        print("-" * 30)
        
        astra_users = [
            'plantation@astra-agro.com',
            'harvest@astra-agro.com',
            'sustainability@astra-agro.com'
        ]
        
        for email in astra_users:
            user = db.query(User).filter(User.email == email).first()
            if user:
                print(f"✅ {email} - EXISTS")
                print(f"   Name: {user.full_name}")
                print(f"   Role: {user.role}")
                print(f"   Company: {user.company.name if user.company else 'No company'}")
                print(f"   Active: {user.is_active}")
                
                # Test password
                test_password = 'password123'
                password_valid = verify_password(test_password, user.hashed_password)
                print(f"   Password 'password123' valid: {password_valid}")
            else:
                print(f"❌ {email} - NOT FOUND")
            print()
        
        # Check if L'Oréal company exists
        loreal_company = db.query(Company).filter(Company.name == "L'Oréal Group").first()
        if loreal_company:
            print(f"✅ L'Oréal Group company exists")
            print(f"   Type: {loreal_company.company_type}")
            print(f"   Email: {loreal_company.email}")
        else:
            print(f"❌ L'Oréal Group company NOT FOUND")
        
        # Check if Astra Agro company exists
        astra_company = db.query(Company).filter(Company.name == 'PT Astra Agro Lestari Tbk').first()
        if astra_company:
            print(f"✅ PT Astra Agro Lestari Tbk company exists")
            print(f"   Type: {astra_company.company_type}")
            print(f"   Email: {astra_company.email}")
        else:
            print(f"❌ PT Astra Agro Lestari Tbk company NOT FOUND")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    check_credentials()
