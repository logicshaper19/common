#!/usr/bin/env python3
"""
Migration script to add sector-specific tier system to Common platform
This script:
1. Creates new sector tables
2. Seeds sector templates
3. Migrates existing users to the sector system
4. Maintains backward compatibility
"""
import asyncio
import sys
import os
from pathlib import Path

# Add the app directory to the Python path
app_dir = Path(__file__).parent.parent
sys.path.insert(0, str(app_dir))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.core.database import Base
from app.core.config import settings
from app.models import *  # Import all models to ensure they're registered
from app.services.sector_seeder import seed_sectors


def create_sector_tables(engine):
    """Create the new sector-related tables"""
    print("Creating sector tables...")
    
    # SQL for creating sector tables
    sector_tables_sql = """
    -- Create sectors table
    CREATE TABLE IF NOT EXISTS sectors (
        id VARCHAR(50) PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        description TEXT,
        is_active BOOLEAN DEFAULT true,
        regulatory_focus JSONB
    );

    -- Create sector_tiers table
    CREATE TABLE IF NOT EXISTS sector_tiers (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        sector_id VARCHAR(50) NOT NULL REFERENCES sectors(id),
        level INTEGER NOT NULL,
        name VARCHAR(100) NOT NULL,
        description TEXT,
        is_originator BOOLEAN DEFAULT false,
        required_data_fields JSONB,
        permissions JSONB,
        UNIQUE(sector_id, level)
    );

    -- Create sector_products table
    CREATE TABLE IF NOT EXISTS sector_products (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        sector_id VARCHAR(50) NOT NULL REFERENCES sectors(id),
        name VARCHAR(255) NOT NULL,
        category VARCHAR(100),
        hs_code VARCHAR(20),
        specifications JSONB,
        applicable_tiers JSONB
    );

    -- Add sector columns to users table
    ALTER TABLE users 
    ADD COLUMN IF NOT EXISTS sector_id VARCHAR(50) REFERENCES sectors(id),
    ADD COLUMN IF NOT EXISTS tier_level INTEGER;

    -- Add sector columns to companies table
    ALTER TABLE companies 
    ADD COLUMN IF NOT EXISTS sector_id VARCHAR(50) REFERENCES sectors(id),
    ADD COLUMN IF NOT EXISTS tier_level INTEGER;

    -- Create indexes for performance
    CREATE INDEX IF NOT EXISTS idx_users_sector_id ON users(sector_id);
    CREATE INDEX IF NOT EXISTS idx_users_tier_level ON users(tier_level);
    CREATE INDEX IF NOT EXISTS idx_companies_sector_id ON companies(sector_id);
    CREATE INDEX IF NOT EXISTS idx_companies_tier_level ON companies(tier_level);
    CREATE INDEX IF NOT EXISTS idx_sector_tiers_sector_level ON sector_tiers(sector_id, level);
    CREATE INDEX IF NOT EXISTS idx_sector_products_sector ON sector_products(sector_id);
    """
    
    with engine.connect() as conn:
        # Execute each statement separately
        statements = [stmt.strip() for stmt in sector_tables_sql.split(';') if stmt.strip()]
        for statement in statements:
            try:
                conn.execute(text(statement))
                conn.commit()
                print(f"✓ Executed: {statement[:50]}...")
            except Exception as e:
                print(f"✗ Error executing statement: {e}")
                print(f"Statement: {statement}")
                raise


async def main():
    """Main migration function"""
    print("🚀 Starting sector system migration...")
    
    # Get database URL
    database_url = settings.database_url
    print(f"Database URL: {database_url.split('@')[1] if '@' in database_url else 'local'}")
    
    # Create engine and session
    engine = create_engine(database_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    try:
        # Step 1: Create new tables
        print("\n📋 Step 1: Creating sector tables...")
        create_sector_tables(engine)
        print("✅ Sector tables created successfully")
        
        # Step 2: Seed sector data
        print("\n🌱 Step 2: Seeding sector templates...")
        db = SessionLocal()
        try:
            results = await seed_sectors(db)
            print("✅ Sector seeding completed")
            print(f"Template results: {results['template_results']}")
            print(f"Migration stats: {results['migration_stats']}")
        finally:
            db.close()
        
        print("\n🎉 Migration completed successfully!")
        print("\nNext steps:")
        print("1. Restart your application server")
        print("2. Test the new sector functionality")
        print("3. Monitor for any issues")
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        raise
    finally:
        engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
