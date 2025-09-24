#!/usr/bin/env python3
"""
Migration script to set up database on Neon PostgreSQL.
Run this script after connecting to Neon to create all necessary tables and data.
"""

import os
import sys
import asyncio
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import create_engine, text
from alembic.config import Config
from alembic import command
from app.core.config import settings
from app.core.database import engine
from app.core.logging import get_logger

logger = get_logger(__name__)

def test_neon_connection():
    """Test connection to Neon database."""
    try:
        # Test basic connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            logger.info(f"✅ Connected to Neon PostgreSQL: {version}")
            
            # Test SSL connection
            result = conn.execute(text("SELECT ssl_is_used()"))
            ssl_used = result.fetchone()[0]
            logger.info(f"✅ SSL connection: {'Enabled' if ssl_used else 'Disabled'}")
            
            return True
    except Exception as e:
        logger.error(f"❌ Failed to connect to Neon: {e}")
        return False

def run_migrations():
    """Run Alembic migrations on Neon database."""
    try:
        # Configure Alembic
        alembic_cfg = Config("alembic.ini")
        alembic_cfg.set_main_option("sqlalchemy.url", settings.database_url)
        
        # Run migrations
        logger.info("🔄 Running database migrations...")
        command.upgrade(alembic_cfg, "head")
        logger.info("✅ Database migrations completed")
        
        return True
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        return False

def seed_initial_data():
    """Seed initial data for the application."""
    try:
        from app.services.seed_data import SeedDataService
        from app.core.database import get_db
        
        logger.info("🌱 Seeding initial data...")
        db = next(get_db())
        seed_service = SeedDataService(db)
        seed_service.seed_all_data()
        db.close()
        logger.info("✅ Initial data seeded successfully")
        
        return True
    except Exception as e:
        logger.error(f"❌ Data seeding failed: {e}")
        return False

def create_initial_admin():
    """Create initial admin user."""
    try:
        from app.core.database import get_db
        from app.models.user import User
        from app.models.company import Company
        from sqlalchemy.orm import Session
        from passlib.context import CryptContext
        
        logger.info("👤 Creating initial admin user...")
        
        db = next(get_db())
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        
        # Check if admin already exists
        existing_admin = db.query(User).filter(User.email == "admin@common.com").first()
        if existing_admin:
            logger.info("✅ Admin user already exists")
            db.close()
            return True
        
        # Create admin company
        admin_company = Company(
            name="Common Platform Admin",
            company_type="admin",
            is_active=True
        )
        db.add(admin_company)
        db.flush()
        
        # Create admin user
        admin_user = User(
            email="admin@common.com",
            hashed_password=pwd_context.hash("admin123"),
            full_name="System Administrator",
            role="admin",
            is_active=True,
            company_id=admin_company.id
        )
        db.add(admin_user)
        db.commit()
        db.close()
        
        logger.info("✅ Admin user created successfully")
        logger.info("📧 Email: admin@common.com")
        logger.info("🔑 Password: admin123")
        logger.info("⚠️  Please change the password after first login!")
        
        return True
    except Exception as e:
        logger.error(f"❌ Admin user creation failed: {e}")
        return False

def main():
    """Main migration function."""
    logger.info("🚀 Starting Neon database migration...")
    
    # Test connection
    if not test_neon_connection():
        logger.error("❌ Cannot proceed without database connection")
        return False
    
    # Run migrations
    if not run_migrations():
        logger.error("❌ Migration failed")
        return False
    
    # Seed initial data
    if not seed_initial_data():
        logger.error("❌ Data seeding failed")
        return False
    
    # Create admin user
    if not create_initial_admin():
        logger.error("❌ Admin user creation failed")
        return False
    
    logger.info("🎉 Neon database migration completed successfully!")
    logger.info("🌐 Your application is ready to use with Neon PostgreSQL")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
