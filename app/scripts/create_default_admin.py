#!/usr/bin/env python3
"""
Script to create a default admin user using environment variables.
Useful for automated deployments and development setups.
"""
import os
import sys
from sqlalchemy.orm import Session

# Add parent directory to path to import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import SessionLocal, engine, Base
from models.company import Company
from models.user import User
from core.auth import hash_password
from core.logging import get_logger

logger = get_logger(__name__)


def create_default_admin():
    """Create default admin user from environment variables."""
    
    # Get configuration from environment variables
    admin_email = os.getenv("ADMIN_EMAIL", "admin@common.local")
    admin_password = os.getenv("ADMIN_PASSWORD", "admin123456")
    admin_name = os.getenv("ADMIN_NAME", "Platform Administrator")
    company_name = os.getenv("ADMIN_COMPANY_NAME", "Common Platform")
    company_email = os.getenv("ADMIN_COMPANY_EMAIL", admin_email)
    
    # Validate required fields
    if len(admin_password) < 8:
        logger.error("Admin password must be at least 8 characters long")
        return False
    
    # Create database session
    db = SessionLocal()
    
    try:
        # Ensure tables exist
        Base.metadata.create_all(bind=engine)
        
        # Check if admin user already exists
        existing_user = db.query(User).filter(User.email == admin_email).first()
        if existing_user:
            logger.info(f"Admin user already exists: {admin_email}")
            return True
        
        # Check if company exists
        company = db.query(Company).filter(Company.email == company_email).first()
        if not company:
            # Create company
            company = Company(
                name=company_name,
                company_type="brand",
                email=company_email
            )
            db.add(company)
            db.flush()
            logger.info(f"Created admin company: {company_name}")
        
        # Create admin user
        hashed_password = hash_password(admin_password)
        admin_user = User(
            email=admin_email,
            hashed_password=hashed_password,
            full_name=admin_name,
            role="admin",
            is_active=True,
            company_id=company.id
        )
        
        db.add(admin_user)
        db.commit()
        
        logger.info(
            "Default admin user created successfully",
            email=admin_email,
            company=company_name
        )
        
        return True
        
    except Exception as e:
        db.rollback()
        logger.error("Failed to create default admin user", error=str(e))
        return False
        
    finally:
        db.close()


if __name__ == "__main__":
    success = create_default_admin()
    sys.exit(0 if success else 1)