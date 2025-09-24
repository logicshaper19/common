#!/usr/bin/env python3
"""
Pre-deployment script to validate model relationships exist
Validates that PurchaseOrder model has all required relationships configured
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.purchase_order import PurchaseOrder
from app.core.database import get_db
from sqlalchemy.orm import class_mapper
from sqlalchemy import text

def validate_relationships():
    """Validate that required relationships exist on PurchaseOrder model"""
    try:
        mapper = class_mapper(PurchaseOrder)
        relationships = mapper.relationships.keys()
        
        required_relationships = ['buyer_company', 'seller_company', 'product']
        missing = [rel for rel in required_relationships if rel not in relationships]
        
        if missing:
            print(f"❌ Missing relationships: {missing}")
            print("Add these to your PurchaseOrder model:")
            for rel in missing:
                if 'company' in rel:
                    print(f"  {rel} = relationship('Company', foreign_keys=[{rel}_id])")
                else:
                    print(f"  {rel} = relationship('{rel.title()}')")
            return False
        else:
            print("✅ All required relationships exist")
            return True
            
    except Exception as e:
        print(f"❌ Error validating relationships: {e}")
        return False

def validate_database_indexes():
    """Validate that required database indexes exist"""
    try:
        db = next(get_db())
        
        # Check for purchase order indexes
        index_query = """
        SELECT schemaname, tablename, indexname, indexdef 
        FROM pg_indexes 
        WHERE tablename = 'purchase_orders' 
        AND indexname LIKE 'idx_po_%'
        ORDER BY indexname;
        """
        
        indexes = db.execute(text(index_query)).fetchall()
        
        required_indexes = [
            'idx_po_buyer_company_id',
            'idx_po_seller_company_id', 
            'idx_po_product_id',
            'idx_po_status',
            'idx_po_created_at'
        ]
        
        existing_indexes = [row.indexname for row in indexes]
        missing_indexes = [idx for idx in required_indexes if idx not in existing_indexes]
        
        if missing_indexes:
            print(f"❌ Missing database indexes: {missing_indexes}")
            print("Run the migration script to create these indexes:")
            print("python scripts/migrate_to_optimized_po.py")
            return False
        else:
            print("✅ All required database indexes exist")
            return True
            
    except Exception as e:
        print(f"❌ Error validating database indexes: {e}")
        return False
    finally:
        db.close()

def validate_environment_config():
    """Validate that required environment variables are set"""
    required_vars = [
        'V2_FEATURES_ENABLED',
        'V2_COMPANY_DASHBOARDS', 
        'V2_ADMIN_FEATURES',
        'ENABLE_PO_QUERY_OPTIMIZATION',
        'ENABLE_PO_CACHING',
        'ENABLE_PERFORMANCE_MONITORING'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing environment variables: {missing_vars}")
        print("Add these to your .env file:")
        for var in missing_vars:
            print(f"  {var}=true")
        return False
    else:
        print("✅ All required environment variables are set")
        return True

def main():
    """Run all validation checks"""
    print("🔍 Running pre-deployment validation checks...\n")
    
    checks = [
        ("Model Relationships", validate_relationships),
        ("Database Indexes", validate_database_indexes),
        ("Environment Configuration", validate_environment_config)
    ]
    
    all_passed = True
    
    for check_name, check_func in checks:
        print(f"Checking {check_name}...")
        if not check_func():
            all_passed = False
        print()
    
    if all_passed:
        print("🎉 All validation checks passed!")
        print("Safe to proceed with deployment")
        return 0
    else:
        print("❌ Some validation checks failed")
        print("Fix the issues above before deploying")
        return 1

if __name__ == "__main__":
    sys.exit(main())
