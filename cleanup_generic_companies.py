#!/usr/bin/env python3
"""
Clean up generic companies from the database to fix the companies endpoint.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.models.company import Company
from app.models.user import User

def cleanup_generic_companies():
    """Remove generic companies from the database."""
    print("🧹 Cleaning up generic companies from the database...")
    
    # Create database connection
    engine = create_engine(settings.database_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # Define patterns for generic companies
        generic_patterns = [
            "Plantation Grower Company",
            "Smallholder Cooperative Company", 
            "Mill Processor Company",
            "Refinery Crusher Company",
            "Trader Aggregator Company",
            "Oleochemical Producer Company",
            "Global Consumer Brand",
            "Global Trading Co",
            "Premium Refinery Ltd",
            "Sustainable Mill Corp",
            "Green Acres Plantation",
            "Sustainable Beauty Co",
            "Regional Trading Ltd",
            "Premium Packaging Solutions",
            "Chemical Components Ltd",
            "Fragrance Ingredients Co",
            "Raw Materials Co",
            "Natural Extracts Ltd",
            "Chemical Suppliers",
            "Organic Farms",
            "Sustainable Harvest",
            "Natural Extracts",
            "Test Company"
        ]
        
        # Find all generic companies
        generic_companies = []
        for pattern in generic_patterns:
            companies = db.query(Company).filter(Company.name.like(f"%{pattern}%")).all()
            generic_companies.extend(companies)
        
        print(f"📊 Found {len(generic_companies)} generic companies to delete")
        
        # Delete users associated with these companies first
        deleted_users = 0
        deleted_companies = 0
        
        for company in generic_companies:
            print(f"🗑️  Deleting: {company.name}")
            
            # Delete users associated with this company
            users = db.query(User).filter(User.company_id == company.id).all()
            for user in users:
                print(f"   👤 Deleting user: {user.full_name} ({user.email})")
                db.delete(user)
                deleted_users += 1
            
            # Delete the company
            db.delete(company)
            deleted_companies += 1
        
        # Commit the changes
        db.commit()
        
        print(f"\n✅ Cleanup completed:")
        print(f"   🗑️  Deleted {deleted_companies} generic companies")
        print(f"   👤 Deleted {deleted_users} associated users")
        
        # Verify palm oil companies still exist
        print(f"\n🌴 Verifying palm oil companies still exist...")
        palm_oil_emails = [
            "manager@wilmar.com",
            "manager@makmurselalu.com", 
            "manager@tanimaju.com",
            "manager@plantationestate.com"
        ]
        
        for email in palm_oil_emails:
            user = db.query(User).filter(User.email == email).first()
            if user:
                company = db.query(Company).filter(Company.id == user.company_id).first()
                if company:
                    print(f"   ✅ {company.name} - {email}")
                else:
                    print(f"   ❌ User exists but no company found for {email}")
            else:
                print(f"   ❌ No user found for {email}")
        
        # Count remaining companies
        remaining_companies = db.query(Company).count()
        print(f"\n📊 Remaining companies in database: {remaining_companies}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during cleanup: {str(e)}")
        db.rollback()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    success = cleanup_generic_companies()
    if success:
        print(f"\n🎉 Generic companies cleanup completed successfully!")
        print(f"🔄 The companies endpoint should now return only real companies")
        print(f"📋 Makmur Selalu Mill and other palm oil companies should now appear in the frontend dropdown")
    else:
        print(f"\n❌ Cleanup failed. Please check the error messages above.")
