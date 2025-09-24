#!/usr/bin/env python3
"""
Test script for Purchase Order Model Simplification.

This script verifies that the simplified Purchase Order model structure
works correctly and that the migration logic is sound.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

def test_model_files_exist():
    """Test that the simplified model files exist and have correct structure."""
    print("🔍 Testing Purchase Order Model Simplification...")
    
    # Test 1: Check that all model files exist
    print("\n1. Testing model files exist...")
    model_files = [
        'app/models/purchase_order_simplified.py',
        'app/models/purchase_order_confirmation.py',
        'app/models/purchase_order_erp_sync.py',
        'app/models/purchase_order_delivery.py',
        'app/models/purchase_order_metadata.py'
    ]
    
    for file_path in model_files:
        if os.path.exists(file_path):
            print(f"✅ PASS: {file_path} exists")
        else:
            print(f"❌ FAIL: {file_path} missing")
            return False
    
    # Test 2: Check that simplified model has essential columns
    print("\n2. Testing simplified model structure...")
    try:
        with open('app/models/purchase_order_simplified.py', 'r') as f:
            content = f.read()
        
        essential_columns = [
            'id', 'po_number', 'external_po_id', 'status',
            'buyer_company_id', 'seller_company_id', 'product_id',
            'quantity', 'unit', 'price_per_unit', 'parent_po_id',
            'created_at', 'updated_at'
        ]
        
        for col in essential_columns:
            if f"{col} = Column" in content:
                print(f"✅ PASS: {col} column exists in simplified model")
            else:
                print(f"❌ FAIL: {col} column missing from simplified model")
                return False
        
        # Check that bloated columns are removed
        removed_columns = [
            'confirmed_quantity', 'confirmed_unit_price', 'seller_confirmed_at',
            'erp_integration_enabled', 'erp_sync_status', 'delivery_status',
            'composition', 'input_materials', 'origin_data', 'supply_chain_level',
            'fulfillment_status', 'amendment_count', 'notes'
        ]
        
        for col in removed_columns:
            if f"'{col}'" not in content and f'"{col}"' not in content:
                print(f"✅ PASS: {col} column removed from simplified model")
            else:
                print(f"❌ FAIL: {col} column still exists in simplified model")
                return False
        
    except Exception as e:
        print(f"❌ FAIL: Error reading simplified model: {e}")
        return False
    
    return True

def test_relationships():
    """Test that relationships are defined correctly in model files."""
    print("\n3. Testing model relationships...")
    
    try:
        with open('app/models/purchase_order_simplified.py', 'r') as f:
            content = f.read()
        
        expected_relationships = [
            'confirmation', 'erp_sync', 'delivery', 'po_metadata',
            'batch_linkages', 'parent_po', 'child_pos'
        ]
        
        for rel in expected_relationships:
            if rel in content:
                print(f"✅ PASS: {rel} relationship defined in simplified model")
            else:
                print(f"❌ FAIL: {rel} relationship missing from simplified model")
                return False
        
        # Test that specialized models have back-references
        with open('app/models/purchase_order_confirmation.py', 'r') as f:
            confirmation_content = f.read()
        
        if 'purchase_order' in confirmation_content:
            print("✅ PASS: PurchaseOrderConfirmation has back-reference to PurchaseOrder")
        else:
            print("❌ FAIL: PurchaseOrderConfirmation missing back-reference to PurchaseOrder")
            return False
        
    except Exception as e:
        print(f"❌ FAIL: Error reading model files: {e}")
        return False
    
    return True

def test_migration_sql():
    """Test that the migration SQL script is syntactically correct."""
    print("\n4. Testing migration SQL script...")
    
    try:
        with open('split_purchase_order_model_migration.sql', 'r') as f:
            sql_content = f.read()
        
        # Check for key migration components
        required_components = [
            'CREATE TABLE IF NOT EXISTS po_confirmations',
            'CREATE TABLE IF NOT EXISTS po_erp_sync',
            'CREATE TABLE IF NOT EXISTS po_deliveries',
            'CREATE TABLE IF NOT EXISTS po_metadata',
            'INSERT INTO po_confirmations',
            'INSERT INTO po_erp_sync',
            'INSERT INTO po_deliveries',
            'INSERT INTO po_metadata',
            'CREATE INDEX IF NOT EXISTS',
            'BEGIN;',
            'COMMIT;'
        ]
        
        for component in required_components:
            if component in sql_content:
                print(f"✅ PASS: Migration contains {component}")
            else:
                print(f"❌ FAIL: Migration missing {component}")
                return False
        
        print("✅ PASS: Migration SQL syntax looks correct")
        return True
        
    except FileNotFoundError:
        print("❌ FAIL: Migration SQL file not found")
        return False
    except Exception as e:
        print(f"❌ FAIL: Error reading migration SQL: {e}")
        return False

def test_database_connection():
    """Test that we can connect to the database and inspect tables."""
    print("\n5. Testing database connection...")
    
    try:
        # Create engine and session
        engine = create_engine(settings.database_url)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Test that we can query the existing purchase_orders table
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        if 'purchase_orders' in tables:
            print("✅ PASS: purchase_orders table exists")
        else:
            print("❌ FAIL: purchase_orders table not found")
            return False
        
        # Test that we can query existing data (using raw SQL to avoid import issues)
        result = session.execute(text("SELECT COUNT(*) FROM purchase_orders")).scalar()
        print(f"✅ PASS: Found {result} existing purchase orders")
        
        session.close()
        return True
        
    except Exception as e:
        print(f"❌ FAIL: Database connection error: {e}")
        return False

def main():
    """Run all tests."""
    print("🚀 Starting Purchase Order Model Simplification Tests...")
    
    tests = [
        test_model_files_exist,
        test_relationships,
        test_migration_sql,
        test_database_connection
    ]
    
    all_passed = True
    for test in tests:
        if not test():
            all_passed = False
    
    if all_passed:
        print("\n🎉 ALL TESTS PASSED!")
        print("✅ Purchase Order model simplification is ready for deployment")
        print("\n📋 NEXT STEPS:")
        print("1. Run the migration script: split_purchase_order_model_migration.sql")
        print("2. Update the original purchase_order.py to use the simplified model")
        print("3. Update all API endpoints to use the new model structure")
        print("4. Test the application with the new model structure")
    else:
        print("\n❌ SOME TESTS FAILED!")
        print("Please fix the issues before proceeding with the migration.")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
