#!/usr/bin/env python3
"""
Script to create an admin user for the Common Supply Chain Platform.
Run this script to create your first admin user for accessing the admin dashboard.
"""
import sys
import os
from getpass import getpass

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine, Base
from app.models.company import Company
from app.models.user import User
from app.core.auth import hash_password


def create_admin_user():
    """Create an admin user interactively."""
    
    print("🚀 Common Supply Chain Platform - Admin User Creation")
    print("=" * 60)
    
    # Get user input
    print("\n📝 Please provide the following information:")
    
    # Company information
    company_name = input("Company Name (e.g., 'Platform Admin'): ").strip()
    if not company_name:
        company_name = "Platform Admin"
    
    company_email = input("Company Email (e.g., 'admin@yourcompany.com'): ").strip()
    if not company_email:
        print("❌ Company email is required!")
        return False
    
    # User information
    user_name = input("Admin Full Name (e.g., 'Admin User'): ").strip()
    if not user_name:
        user_name = "Admin User"
    
    user_email = input("Admin Email (e.g., 'admin@yourcompany.com'): ").strip()
    if not user_email:
        user_email = company_email
    
    # Password
    while True:
        password = getpass("Admin Password (min 8 characters): ")
        if len(password) < 8:
            print("❌ Password must be at least 8 characters long!")
            continue
        
        confirm_password = getpass("Confirm Password: ")
        if password != confirm_password:
            print("❌ Passwords don't match!")
            continue
        break
    
    # Create database session
    db = SessionLocal()
    
    try:
        # Check if company already exists
        existing_company = db.query(Company).filter(Company.email == company_email).first()
        if existing_company:
            print(f"📋 Using existing company: {existing_company.name}")
            company = existing_company
        else:
            # Create company
            company = Company(
                name=company_name,
                company_type="brand",  # Default to brand for admin
                email=company_email
            )
            db.add(company)
            db.flush()  # Get the company ID
            print(f"✅ Created company: {company_name}")
        
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == user_email).first()
        if existing_user:
            print(f"❌ User with email {user_email} already exists!")
            return False
        
        # Create admin user
        hashed_password = hash_password(password)
        admin_user = User(
            email=user_email,
            hashed_password=hashed_password,
            full_name=user_name,
            role="admin",
            is_active=True,
            company_id=company.id
        )
        
        db.add(admin_user)
        db.commit()
        
        print("\n🎉 Admin user created successfully!")
        print("=" * 60)
        print(f"📧 Email: {user_email}")
        print(f"🏢 Company: {company_name}")
        print(f"👤 Role: admin")
        print("=" * 60)
        print("\n🔐 You can now log in to the admin dashboard with these credentials.")
        print("🌐 Navigate to your frontend application and use the login form.")
        
        return True
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error creating admin user: {str(e)}")
        return False
        
    finally:
        db.close()


def check_database():
    """Check if database tables exist."""
    try:
        # Create tables if they don't exist
        Base.metadata.create_all(bind=engine)
        return True
    except Exception as e:
        print(f"❌ Database error: {str(e)}")
        return False


if __name__ == "__main__":
    print("🔍 Checking database connection...")
    
    if not check_database():
        print("❌ Failed to connect to database. Please check your database configuration.")
        sys.exit(1)
    
    print("✅ Database connection successful!")
    
    if create_admin_user():
        print("\n🚀 Ready to go! Start your application and log in with your new admin credentials.")
    else:
        print("\n❌ Failed to create admin user. Please try again.")
        sys.exit(1)