#!/usr/bin/env python3
"""
Add batch_id column to purchase_orders table.
"""
from app.core.database import engine
from sqlalchemy import text

def add_batch_id_column():
    """Add batch_id column to purchase_orders table."""
    try:
        with engine.connect() as conn:
            # Check if column already exists
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'purchase_orders' 
                AND column_name = 'batch_id'
            """))
            
            if result.fetchone():
                print("Column batch_id already exists")
                return
            
            # Add the column
            conn.execute(text("ALTER TABLE purchase_orders ADD COLUMN batch_id UUID REFERENCES batches(id)"))
            conn.commit()
            print("Successfully added batch_id column to purchase_orders table")
            
    except Exception as e:
        print(f"Error adding batch_id column: {e}")
        raise

if __name__ == "__main__":
    add_batch_id_column()
