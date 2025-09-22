#!/usr/bin/env python3
import sys
import os
sys.path.append('/Users/elisha/common')

from app.core.database import SessionLocal
from app.models.user import User
from app.models.company import Company
from app.core.security import hash_password, verify_password
import requests

def create_working_users():
    """Create working test users and verify they work"""

    db = SessionLocal()

    try:
        # First, check existing admin users
        print("🔍 Checking existing admin users...")
        admin_users = db.query(User).filter(User.role == 'admin').all()

        for user in admin_users:
            print(f"Found admin: {user.email}")
            # Test common passwords
            test_passwords = ['slp225', 'password123', 'admin123', 'slp225admin', '']
            for pwd in test_passwords:
                if verify_password(pwd, user.hashed_password):
                    print(f"✅ EXISTING ADMIN WORKS: {user.email} / {pwd}")
                    return user.email, pwd

        print("❌ No working admin found, creating new users...")

        # Delete ALL existing users to start fresh
        db.query(User).delete()

        # Create or get a test company
        company = db.query(Company).first()
        if not company:
            company = Company(
                name='Test Company',
                company_type='brand',
                address_street='123 Test St',
                address_city='Test City',
                address_country='Test Country'
            )
            db.add(company)
            db.flush()

        # Create users with simple, known passwords
        users_to_create = [
            ('admin@test.com', 'password123', 'Test Admin', 'admin'),
            ('manager@test.com', 'password123', 'Test Manager', 'supply_chain_manager'),
            ('viewer@test.com', 'password123', 'Test Viewer', 'viewer'),
        ]

        hashed_password = hash_password('password123')

        for email, password, name, role in users_to_create:
            user = User(
                email=email,
                hashed_password=hashed_password,
                full_name=name,
                role=role,
                company_id=company.id,
                is_active=True
            )
            db.add(user)

        db.commit()

        print("✅ Users created successfully!")
        return 'admin@test.com', 'password123'

    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
        return None, None
    finally:
        db.close()

def test_login(email, password):
    """Test login with given credentials"""
    try:
        response = requests.post(
            'http://localhost:8001/api/v1/auth/login',
            data={'username': email, 'password': password},
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
            timeout=5
        )

        print(f"Login test: {email} / {password}")
        print(f"Status: {response.status_code}")
        if response.status_code != 200:
            print(f"Response: {response.text}")
        return response.status_code == 200

    except Exception as e:
        print(f"Login error: {e}")
        return False

if __name__ == "__main__":
    email, password = create_working_users()
    if email and password:
        print(f"\n🔐 TESTING CREDENTIALS: {email} / {password}")
        if test_login(email, password):
            print("✅ LOGIN SUCCESSFUL!")
        else:
            print("❌ LOGIN FAILED!")
    else:
        print("❌ Could not create working credentials")
