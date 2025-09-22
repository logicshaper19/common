#!/usr/bin/env python3
"""
Script to create an originator test user
"""
import sys
import os
sys.path.append('/Users/elisha/common')

from app.core.database import SessionLocal
from app.models.user import User
from app.models.company import Company
from app.core.security import hash_password

def main():
    print("🌱 Creating originator test user...")
    
    db = SessionLocal()
    
    try:
        # Create or get originator company
        originator_company = db.query(Company).filter(Company.name == 'Organic Farms Ltd').first()
        if not originator_company:
            originator_company = Company(
                name='Organic Farms Ltd',
                company_type='originator',
                email='contact@organicfarms.com',
                phone='+1-555-0123',
                address_street='123 Farm Road',
                address_city='Rural Valley',
                address_country='United States',
                website='https://www.organicfarms.com'
            )
            db.add(originator_company)
            db.flush()
            print(f"Created originator company: {originator_company.name}")
        else:
            print(f"Using existing company: {originator_company.name}")
        
        # Check if originator user already exists
        existing_user = db.query(User).filter(User.email == 'originator@organicfarms.com').first()
        if existing_user:
            print(f"Originator user already exists: {existing_user.email}")
            return
        
        # Create originator user
        test_password = 'password123'
        hashed_password = hash_password(test_password)
        
        originator_user = User(
            email='originator@organicfarms.com',
            hashed_password=hashed_password,
            full_name='Farm Manager',
            role='originator',
            company_id=originator_company.id,
            is_active=True
        )
        
        db.add(originator_user)
        db.commit()
        
        print("\n✅ Successfully created originator user!")
        print("=" * 50)
        print(f"📧 Email: {originator_user.email}")
        print(f"👤 Name: {originator_user.full_name}")
        print(f"🎭 Role: {originator_user.role}")
        print(f"🏢 Company: {originator_company.name}")
        print(f"✅ Active: {originator_user.is_active}")
        
        print("\n🔐 LOGIN CREDENTIALS:")
        print("=" * 30)
        print("Originator User:")
        print("  Email: originator@organicfarms.com")
        print("  Password: password123")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    main()
