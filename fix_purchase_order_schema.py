#!/usr/bin/env python3
"""
Fix purchase order schema by adding missing columns
"""
import sys
import os
sys.path.append('/Users/elisha/common')

from app.core.database import SessionLocal
from sqlalchemy import text

def fix_purchase_order_schema():
    """Add missing columns to purchase_orders table"""
    
    print("🔧 Fixing purchase order schema...")
    
    db = SessionLocal()
    
    try:
        # Add missing columns
        missing_columns = [
            "ADD COLUMN IF NOT EXISTS parent_po_id UUID REFERENCES purchase_orders(id)",
            "ADD COLUMN IF NOT EXISTS supply_chain_level INTEGER DEFAULT 1",
            "ADD COLUMN IF NOT EXISTS is_chain_initiated BOOLEAN DEFAULT FALSE",
            "ADD COLUMN IF NOT EXISTS fulfillment_status VARCHAR(20) DEFAULT 'pending'",
            "ADD COLUMN IF NOT EXISTS fulfillment_percentage INTEGER DEFAULT 0",
            "ADD COLUMN IF NOT EXISTS fulfillment_notes TEXT",
            "ADD COLUMN IF NOT EXISTS po_state VARCHAR(50) DEFAULT 'draft'",
            "ADD COLUMN IF NOT EXISTS fulfilled_quantity NUMERIC(12, 3) DEFAULT 0",
            "ADD COLUMN IF NOT EXISTS linked_po_id UUID REFERENCES purchase_orders(id)"
        ]
        
        for column_sql in missing_columns:
            try:
                db.execute(text(f"ALTER TABLE purchase_orders {column_sql}"))
                print(f"✅ Added column: {column_sql.split()[3]}")
            except Exception as e:
                print(f"⚠️  Column might already exist: {e}")
        
        db.commit()
        print("✅ Purchase order schema updated successfully!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    fix_purchase_order_schema()
