#!/usr/bin/env python3
"""
Fix Database Schema - Add Missing Columns to Purchase Orders
This script adds only the missing columns needed to fix the API errors.
"""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

def get_database_url():
    """Get database URL from environment or use default."""
    return os.getenv(
        'DATABASE_URL', 
        'postgresql://common_user:common_password@localhost:5432/common_db'
    )

def check_existing_columns(connection):
    """Check which columns already exist in purchase_orders table."""
    print("🔍 Checking existing columns in purchase_orders table...")
    
    result = connection.execute(text("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'purchase_orders' 
        ORDER BY column_name;
    """))
    
    existing_columns = [row[0] for row in result]
    print(f"📋 Found {len(existing_columns)} existing columns")
    
    # Check for the specific columns we need
    required_columns = [
        'original_quantity',
        'original_unit_price', 
        'original_delivery_date',
        'original_delivery_location',
        'buyer_approved_at',
        'buyer_approval_user_id',
        'discrepancy_reason',
        'seller_confirmed_data'
    ]
    
    missing_columns = [col for col in required_columns if col not in existing_columns]
    
    print(f"✅ Existing required columns: {[col for col in required_columns if col in existing_columns]}")
    print(f"❌ Missing required columns: {missing_columns}")
    
    return missing_columns, existing_columns

def add_missing_columns(connection, missing_columns):
    """Add only the missing columns."""
    if not missing_columns:
        print("✅ All required columns already exist!")
        return True
    
    print(f"🔧 Adding {len(missing_columns)} missing columns...")
    
    # Column definitions
    column_definitions = {
        'original_quantity': 'DECIMAL(12,3)',
        'original_unit_price': 'DECIMAL(12,2)',
        'original_delivery_date': 'DATE',
        'original_delivery_location': 'VARCHAR(500)',
        'buyer_approved_at': 'TIMESTAMP WITH TIME ZONE',
        'buyer_approval_user_id': 'UUID REFERENCES users(id)',
        'discrepancy_reason': 'TEXT',
        'seller_confirmed_data': 'JSONB'
    }
    
    try:
        trans = connection.begin()
        
        for column in missing_columns:
            if column in column_definitions:
                sql = f"ALTER TABLE purchase_orders ADD COLUMN {column} {column_definitions[column]};"
                print(f"  Adding: {column} ({column_definitions[column]})")
                connection.execute(text(sql))
        
        # Migrate existing data for original_* fields if they were just added
        original_fields = ['original_quantity', 'original_unit_price', 'original_delivery_date', 'original_delivery_location']
        newly_added_original_fields = [col for col in original_fields if col in missing_columns]
        
        if newly_added_original_fields:
            print("🔄 Migrating existing data to original_* fields...")
            
            # Build the SET clause dynamically
            set_clauses = []
            if 'original_quantity' in newly_added_original_fields:
                set_clauses.append('original_quantity = quantity')
            if 'original_unit_price' in newly_added_original_fields:
                set_clauses.append('original_unit_price = unit_price')
            if 'original_delivery_date' in newly_added_original_fields:
                set_clauses.append('original_delivery_date = delivery_date')
            if 'original_delivery_location' in newly_added_original_fields:
                set_clauses.append('original_delivery_location = delivery_location')
            
            if set_clauses:
                update_sql = f"UPDATE purchase_orders SET {', '.join(set_clauses)} WHERE original_quantity IS NULL;"
                print(f"  Executing: {update_sql}")
                connection.execute(text(update_sql))
        
        trans.commit()
        print("✅ Successfully added missing columns!")
        return True
        
    except Exception as e:
        trans.rollback()
        print(f"❌ Failed to add columns: {e}")
        return False

def verify_fix(connection):
    """Verify that the fix worked by checking the columns."""
    print("\n🔍 Verifying the fix...")
    
    # Check if all required columns exist
    missing_columns, existing_columns = check_existing_columns(connection)
    
    if not missing_columns:
        print("✅ All required columns are now present!")
        
        # Check if we have any data in the original_* fields
        result = connection.execute(text("""
            SELECT COUNT(*) as total_pos,
                   COUNT(original_quantity) as with_original_quantity,
                   COUNT(original_unit_price) as with_original_price
            FROM purchase_orders;
        """))
        
        row = result.fetchone()
        print(f"📊 Purchase Orders: {row[0]} total, {row[1]} with original_quantity, {row[2]} with original_price")
        
        return True
    else:
        print(f"❌ Still missing columns: {missing_columns}")
        return False

def main():
    """Main function to fix the database schema."""
    print("🚀 Starting Database Schema Fix")
    print("=" * 50)
    
    # Create database engine
    database_url = get_database_url()
    print(f"📡 Connecting to database: {database_url.split('@')[1] if '@' in database_url else 'localhost'}")
    
    try:
        engine = create_engine(database_url)
        
        with engine.connect() as connection:
            # Check what's missing
            missing_columns, existing_columns = check_existing_columns(connection)
            
            if not missing_columns:
                print("✅ Database schema is already up to date!")
                return True
            
            # Add missing columns
            success = add_missing_columns(connection, missing_columns)
            
            if success:
                # Verify the fix
                verify_success = verify_fix(connection)
                
                if verify_success:
                    print("\n🎉 Database schema fix completed successfully!")
                    print("📋 The following issues should now be resolved:")
                    print("   • Purchase Orders API 500 errors")
                    print("   • Missing original_quantity columns")
                    print("   • Database schema mismatch")
                    print("\n🔄 You may need to restart the backend server to pick up the changes.")
                    return True
                else:
                    print("\n❌ Verification failed.")
                    return False
            else:
                print("\n❌ Failed to add missing columns.")
                return False
                
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)
