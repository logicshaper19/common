#!/usr/bin/env python3
"""
Debug script to check what companies exist in the database.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.models.company import Company
from app.models.user import User

def check_database_companies():
    """Check what companies exist in the database."""
    print("🔍 Checking companies in the database...")
    
    # Create database connection
    engine = create_engine(settings.database_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # Query all companies
        companies = db.query(Company).all()
        print(f"📊 Found {len(companies)} companies in the database:")
        
        for company in companies:
            print(f"   - {company.name} ({company.company_type}) - {company.email}")
        
        # Query all users
        users = db.query(User).all()
        print(f"\n👥 Found {len(users)} users in the database:")
        
        for user in users:
            print(f"   - {user.full_name} ({user.email}) - Role: {user.role}")
        
        # Check if palm oil companies exist
        palm_oil_emails = [
            "manager@wilmar.com",
            "manager@makmurselalu.com", 
            "manager@tanimaju.com",
            "manager@plantationestate.com"
        ]
        
        print(f"\n🌴 Checking for palm oil companies...")
        for email in palm_oil_emails:
            user = db.query(User).filter(User.email == email).first()
            if user:
                company = db.query(Company).filter(Company.id == user.company_id).first()
                if company:
                    print(f"   ✅ {company.name} - {email} (User: {user.full_name})")
                else:
                    print(f"   ❌ User exists but no company found for {email}")
            else:
                print(f"   ❌ No user found for {email}")
        
        # Check for generic companies
        print(f"\n🏭 Checking for generic companies...")
        generic_companies = db.query(Company).filter(
            Company.name.like("%Company%")
        ).all()
        
        if generic_companies:
            print(f"   Found {len(generic_companies)} generic companies:")
            for company in generic_companies:
                print(f"   - {company.name} ({company.company_type})")
        else:
            print(f"   ✅ No generic companies found")
            
    except Exception as e:
        print(f"❌ Error querying database: {str(e)}")
    finally:
        db.close()

if __name__ == "__main__":
    check_database_companies()
