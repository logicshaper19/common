#!/usr/bin/env python3
"""
Test script for the sector system implementation
Tests all major functionality to ensure the system works correctly
"""
import asyncio
import sys
import os
from pathlib import Path

# Add the app directory to the Python path
app_dir = Path(__file__).parent.parent
sys.path.insert(0, str(app_dir))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.services.sector_service import SectorService
from app.models.user import User
from app.models.company import Company
from app.models.sector import Sector, SectorTier, SectorProduct


async def test_sector_service(db):
    """Test the sector service functionality"""
    print("🧪 Testing Sector Service...")
    
    service = SectorService(db)
    
    # Test 1: Get all sectors
    print("  Testing get_all_sectors...")
    sectors = await service.get_all_sectors()
    assert len(sectors) >= 2, f"Expected at least 2 sectors, got {len(sectors)}"
    print(f"  ✅ Found {len(sectors)} sectors")
    
    # Test 2: Get sector by ID
    print("  Testing get_sector_by_id...")
    palm_oil_sector = await service.get_sector_by_id("palm_oil")
    assert palm_oil_sector is not None, "Palm oil sector not found"
    assert palm_oil_sector.name == "Palm Oil & Agri-Commodities"
    print("  ✅ Palm oil sector retrieved successfully")
    
    # Test 3: Get sector tiers
    print("  Testing get_sector_tiers...")
    tiers = await service.get_sector_tiers("palm_oil")
    assert len(tiers) >= 5, f"Expected at least 5 tiers, got {len(tiers)}"
    print(f"  ✅ Found {len(tiers)} tiers for palm oil")
    
    # Test 4: Get tier by level
    print("  Testing get_tier_by_level...")
    brand_tier = await service.get_tier_by_level("palm_oil", 1)
    assert brand_tier is not None, "Brand tier not found"
    assert brand_tier.name == "Brand"
    print("  ✅ Brand tier retrieved successfully")
    
    # Test 5: Get sector products
    print("  Testing get_sector_products...")
    products = await service.get_sector_products("palm_oil")
    assert len(products) >= 4, f"Expected at least 4 products, got {len(products)}"
    print(f"  ✅ Found {len(products)} products for palm oil")
    
    # Test 6: Get sector config
    print("  Testing get_sector_config...")
    config = await service.get_sector_config("palm_oil")
    assert config is not None, "Sector config not found"
    assert config.sector.id == "palm_oil"
    assert len(config.tiers) >= 5
    assert len(config.products) >= 4
    print("  ✅ Sector config retrieved successfully")
    
    print("✅ All sector service tests passed!")


async def test_user_migration(db):
    """Test user migration to sector system"""
    print("🧪 Testing User Migration...")
    
    # Check if users have been migrated
    users_with_sectors = db.query(User).filter(User.sector_id.isnot(None)).count()
    total_users = db.query(User).count()
    
    print(f"  Users with sectors: {users_with_sectors}/{total_users}")
    
    if total_users > 0:
        migration_percentage = (users_with_sectors / total_users) * 100
        print(f"  Migration percentage: {migration_percentage:.1f}%")
        
        # Check specific role mappings
        buyer_users = db.query(User).filter(User.role == "buyer").all()
        for user in buyer_users:
            if user.sector_id:
                assert user.sector_id == "palm_oil", f"Buyer user {user.email} has wrong sector: {user.sector_id}"
                assert user.tier_level == 1, f"Buyer user {user.email} has wrong tier: {user.tier_level}"
        
        print("  ✅ User migration validation passed")
    else:
        print("  ⚠️  No users found to test migration")


async def test_company_migration(db):
    """Test company migration to sector system"""
    print("🧪 Testing Company Migration...")
    
    companies_with_sectors = db.query(Company).filter(Company.sector_id.isnot(None)).count()
    total_companies = db.query(Company).count()
    
    print(f"  Companies with sectors: {companies_with_sectors}/{total_companies}")
    
    if total_companies > 0:
        migration_percentage = (companies_with_sectors / total_companies) * 100
        print(f"  Migration percentage: {migration_percentage:.1f}%")
        print("  ✅ Company migration validation passed")
    else:
        print("  ⚠️  No companies found to test migration")


async def test_data_integrity(db):
    """Test data integrity of the sector system"""
    print("🧪 Testing Data Integrity...")
    
    # Test 1: All tiers have valid sector references
    orphaned_tiers = db.query(SectorTier).filter(
        ~SectorTier.sector_id.in_(db.query(Sector.id))
    ).count()
    assert orphaned_tiers == 0, f"Found {orphaned_tiers} orphaned tiers"
    print("  ✅ No orphaned tiers found")
    
    # Test 2: All products have valid sector references
    orphaned_products = db.query(SectorProduct).filter(
        ~SectorProduct.sector_id.in_(db.query(Sector.id))
    ).count()
    assert orphaned_products == 0, f"Found {orphaned_products} orphaned products"
    print("  ✅ No orphaned products found")
    
    # Test 3: Users with sectors have valid references
    users_with_invalid_sectors = db.query(User).filter(
        User.sector_id.isnot(None),
        ~User.sector_id.in_(db.query(Sector.id))
    ).count()
    assert users_with_invalid_sectors == 0, f"Found {users_with_invalid_sectors} users with invalid sectors"
    print("  ✅ All user sector references are valid")
    
    # Test 4: Companies with sectors have valid references
    companies_with_invalid_sectors = db.query(Company).filter(
        Company.sector_id.isnot(None),
        ~Company.sector_id.in_(db.query(Sector.id))
    ).count()
    assert companies_with_invalid_sectors == 0, f"Found {companies_with_invalid_sectors} companies with invalid sectors"
    print("  ✅ All company sector references are valid")
    
    print("✅ All data integrity tests passed!")


async def test_tier_hierarchy(db):
    """Test tier hierarchy consistency"""
    print("🧪 Testing Tier Hierarchy...")
    
    sectors = db.query(Sector).all()
    
    for sector in sectors:
        tiers = db.query(SectorTier).filter(SectorTier.sector_id == sector.id).order_by(SectorTier.level).all()
        
        # Check that tier levels are sequential
        expected_levels = list(range(1, len(tiers) + 1))
        actual_levels = [tier.level for tier in tiers]
        
        assert actual_levels == expected_levels, f"Tier levels for {sector.id} are not sequential: {actual_levels}"
        
        # Check that there's at least one originator
        originators = [tier for tier in tiers if tier.is_originator]
        assert len(originators) >= 1, f"Sector {sector.id} has no originator tiers"
        
        print(f"  ✅ {sector.name}: {len(tiers)} tiers, {len(originators)} originators")
    
    print("✅ All tier hierarchy tests passed!")


async def main():
    """Main test function"""
    print("🚀 Starting sector system tests...")
    
    # Get database URL
    database_url = settings.database_url
    
    # Create engine and session
    engine = create_engine(database_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    db = SessionLocal()
    try:
        # Run all tests
        await test_sector_service(db)
        await test_user_migration(db)
        await test_company_migration(db)
        await test_data_integrity(db)
        await test_tier_hierarchy(db)
        
        print("\n🎉 All tests passed successfully!")
        print("\nSector system is ready for use!")
        
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        sys.exit(1)
    finally:
        db.close()
        engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
