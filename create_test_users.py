#!/usr/bin/env python3
"""
Script to create test users for the application
"""
import sys
import os
sys.path.append('/Users/elisha/common')

from app.core.database import SessionLocal
from app.models.user import User
from app.models.company import Company
from app.core.security import hash_password, verify_password

def main():
    print("🔧 Creating test users for the application...")
    
    db = SessionLocal()
    
    try:
        # Delete existing test users if they exist
        test_emails = ['admin@test.com', 'manager@test.com', 'viewer@test.com']
        existing_users = db.query(User).filter(User.email.in_(test_emails)).all()
        
        for user in existing_users:
            print(f"Deleting existing user: {user.email}")
            db.delete(user)
        
        # Create or get test company
        test_company = db.query(Company).filter(Company.name == 'Test Company').first()
        if not test_company:
            test_company = Company(
                name='Test Company',
                company_type='brand',
                address_street='123 Test St',
                address_city='Test City',
                address_country='Test Country'
            )
            db.add(test_company)
            db.flush()
            print(f"Created test company: {test_company.name}")
        else:
            print(f"Using existing company: {test_company.name}")
        
        # Create test users
        test_password = 'testpass123'
        hashed_password = hash_password(test_password)
        
        users_to_create = [
            {
                'email': 'admin@test.com',
                'full_name': 'Test Admin',
                'role': 'admin'
            },
            {
                'email': 'manager@test.com',
                'full_name': 'Test Manager',
                'role': 'supply_chain_manager'
            },
            {
                'email': 'viewer@test.com',
                'full_name': 'Test Viewer',
                'role': 'viewer'
            }
        ]
        
        created_users = []
        for user_data in users_to_create:
            user = User(
                email=user_data['email'],
                hashed_password=hashed_password,
                full_name=user_data['full_name'],
                role=user_data['role'],
                company_id=test_company.id,
                is_active=True
            )
            db.add(user)
            created_users.append(user)
        
        db.commit()
        
        print("\n✅ Successfully created test users!")
        print("=" * 50)
        
        # Verify each user
        for user in created_users:
            db.refresh(user)  # Refresh to get the latest data
            password_valid = verify_password(test_password, user.hashed_password)
            print(f"📧 Email: {user.email}")
            print(f"👤 Name: {user.full_name}")
            print(f"🎭 Role: {user.role}")
            print(f"🏢 Company: {test_company.name}")
            print(f"✅ Active: {user.is_active}")
            print(f"🔑 Password valid: {password_valid}")
            print("-" * 30)
        
        print("\n🔐 LOGIN CREDENTIALS:")
        print("=" * 30)
        print("Admin User:")
        print("  Email: admin@test.com")
        print("  Password: testpass123")
        print()
        print("Manager User:")
        print("  Email: manager@test.com")
        print("  Password: testpass123")
        print()
        print("Viewer User:")
        print("  Email: viewer@test.com")
        print("  Password: testpass123")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    main()
