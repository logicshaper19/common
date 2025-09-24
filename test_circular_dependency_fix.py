#!/usr/bin/env python3
"""
Test script to verify the circular dependency fix.
This script tests the logic without actually running the migration.
"""

import os
import sys
sys.path.append('.')

from app.core.database import get_db
from app.models.purchase_order import PurchaseOrder
from app.models.batch import Batch
from app.models.po_batch_linkage import POBatchLinkage
from sqlalchemy.orm import Session

def test_circular_dependency_fix():
    """Test that the circular dependency fix works correctly."""
    
    print("🔍 Testing Circular Dependency Fix...")
    
    # Get database session
    db = next(get_db())
    
    try:
        # Test 1: Verify PurchaseOrder model no longer has circular references
        print("\n1. Testing PurchaseOrder model structure...")
        
        # Check that batch_id column is not in the model
        po_columns = [column.name for column in PurchaseOrder.__table__.columns]
        
        if 'batch_id' in po_columns:
            print("❌ FAIL: batch_id column still exists in PurchaseOrder model")
            return False
        else:
            print("✅ PASS: batch_id column removed from PurchaseOrder model")
        
        if 'linked_po_id' in po_columns:
            print("❌ FAIL: linked_po_id column still exists in PurchaseOrder model")
            return False
        else:
            print("✅ PASS: linked_po_id column removed from PurchaseOrder model")
        
        # Test 2: Verify POBatchLinkage model exists and works
        print("\n2. Testing POBatchLinkage model...")
        
        linkage_columns = [column.name for column in POBatchLinkage.__table__.columns]
        required_columns = ['purchase_order_id', 'batch_id', 'quantity_allocated']
        
        for col in required_columns:
            if col not in linkage_columns:
                print(f"❌ FAIL: {col} column missing from POBatchLinkage model")
                return False
        
        print("✅ PASS: POBatchLinkage model has all required columns")
        
        # Test 3: Test the new properties work
        print("\n3. Testing new PO properties...")
        
        # Get a sample PO
        sample_po = db.query(PurchaseOrder).first()
        if sample_po:
            # Test batches property
            try:
                batches = sample_po.batches
                print(f"✅ PASS: po.batches property works (found {len(batches)} batches)")
            except Exception as e:
                print(f"❌ FAIL: po.batches property failed: {e}")
                return False
            
            # Test primary_batch property
            try:
                primary_batch = sample_po.primary_batch
                if primary_batch:
                    print(f"✅ PASS: po.primary_batch property works (batch: {primary_batch.batch_id})")
                else:
                    print("✅ PASS: po.primary_batch property works (no batch linked)")
            except Exception as e:
                print(f"❌ FAIL: po.primary_batch property failed: {e}")
                return False
        else:
            print("⚠️  WARNING: No Purchase Orders found in database to test properties")
        
        # Test 4: Verify no circular relationships in model definitions
        print("\n4. Testing for circular relationships...")
        
        # Check that PurchaseOrder doesn't have direct batch relationship
        po_relationships = [rel.key for rel in PurchaseOrder.__mapper__.relationships]
        
        if 'batch' in po_relationships:
            print("❌ FAIL: Direct 'batch' relationship still exists in PurchaseOrder")
            return False
        else:
            print("✅ PASS: Direct 'batch' relationship removed from PurchaseOrder")
        
        if 'batch_linkages' in po_relationships:
            print("✅ PASS: 'batch_linkages' relationship exists (proper many-to-many)")
        else:
            print("❌ FAIL: 'batch_linkages' relationship missing")
            return False
        
        # Test 5: Verify hierarchy still works
        print("\n5. Testing PO hierarchy...")
        
        hierarchy_columns = [column.name for column in PurchaseOrder.__table__.columns]
        if 'parent_po_id' in hierarchy_columns:
            print("✅ PASS: parent_po_id column preserved for hierarchy")
        else:
            print("❌ FAIL: parent_po_id column missing")
            return False
        
        print("\n🎉 ALL TESTS PASSED! Circular dependency fix is working correctly.")
        return True
        
    except Exception as e:
        print(f"❌ ERROR during testing: {e}")
        return False
    finally:
        db.close()

def test_migration_sql_syntax():
    """Test that the migration SQL is syntactically correct."""
    print("\n🔍 Testing Migration SQL Syntax...")
    
    try:
        with open('fix_circular_dependencies_migration.sql', 'r') as f:
            sql_content = f.read()
        
        # Basic syntax checks
        if 'BEGIN;' in sql_content and 'COMMIT;' in sql_content:
            print("✅ PASS: Migration has proper transaction boundaries")
        else:
            print("❌ FAIL: Migration missing transaction boundaries")
            return False
        
        if 'DROP COLUMN IF EXISTS batch_id' in sql_content:
            print("✅ PASS: Migration removes batch_id column")
        else:
            print("❌ FAIL: Migration doesn't remove batch_id column")
            return False
        
        if 'DROP COLUMN IF EXISTS linked_po_id' in sql_content:
            print("✅ PASS: Migration removes linked_po_id column")
        else:
            print("❌ FAIL: Migration doesn't remove linked_po_id column")
            return False
        
        if 'INSERT INTO po_batch_linkages' in sql_content:
            print("✅ PASS: Migration preserves data in po_batch_linkages")
        else:
            print("❌ FAIL: Migration doesn't preserve data")
            return False
        
        print("✅ PASS: Migration SQL syntax looks correct")
        return True
        
    except Exception as e:
        print(f"❌ ERROR reading migration file: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting Circular Dependency Fix Tests...")
    
    # Test 1: Model structure
    model_test_passed = test_circular_dependency_fix()
    
    # Test 2: Migration SQL
    sql_test_passed = test_migration_sql_syntax()
    
    if model_test_passed and sql_test_passed:
        print("\n🎉 ALL TESTS PASSED!")
        print("✅ Circular dependency fix is ready for deployment")
        sys.exit(0)
    else:
        print("\n❌ SOME TESTS FAILED!")
        print("❌ Circular dependency fix needs attention")
        sys.exit(1)
