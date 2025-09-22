#!/usr/bin/env python3
import sys
sys.path.append('/Users/elisha/common')

from app.core.database import SessionLocal
from app.models.user import User
from app.models.company import Company
from app.core.security import hash_password

def create_test_users():
    """Create additional test users with known credentials"""
    
    db = SessionLocal()
    
    try:
        # Get or create a test company
        company = db.query(Company).filter(Company.name == 'Test Company').first()
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
        
        # Create additional test users with simple passwords
        test_users = [
            ('admin@test.com', 'password123', 'Test Admin', 'admin'),
            ('manager@test.com', 'password123', 'Test Manager', 'supply_chain_manager'),
            ('viewer@test.com', 'password123', 'Test Viewer', 'viewer'),
        ]
        
        created_users = []
        
        for email, password, name, role in test_users:
            # Check if user already exists
            existing_user = db.query(User).filter(User.email == email).first()
            if existing_user:
                print(f"User {email} already exists")
                continue
                
            # Create new user
            hashed_password = hash_password(password)
            user = User(
                email=email,
                hashed_password=hashed_password,
                full_name=name,
                role=role,
                company_id=company.id,
                is_active=True
            )
            db.add(user)
            created_users.append((email, password, role))
        
        db.commit()
        
        print("✅ Test users created successfully!")
        print("\n🔐 AVAILABLE TEST CREDENTIALS:")
        print("=" * 50)
        
        # Show the main admin from .env
        print("📧 MAIN ADMIN (from .env):")
        print("   Email: elisha@common.co")
        print("   Password: password123")
        print("   Role: admin")
        print()
        
        # Show created test users
        if created_users:
            print("📧 ADDITIONAL TEST USERS:")
            for email, password, role in created_users:
                print(f"   Email: {email}")
                print(f"   Password: {password}")
                print(f"   Role: {role}")
                print()
        
        print("🌐 LOGIN URL: http://localhost:3000")
        print("🔗 API DOCS: http://localhost:8001/docs")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_test_users()
