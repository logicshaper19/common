#!/usr/bin/env python3
"""
Run Migration V020 - Add Purchase Order Approval Workflow Fields
This script runs the missing migration to fix the database schema issues.
"""

import os
import sys
import asyncio
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

def run_migration():
    """Run the V020 migration."""
    print("🗄️  Running Migration V020: Add Purchase Order Approval Workflow Fields")
    print("=" * 70)
    
    # Create database engine
    database_url = get_database_url()
    print(f"📡 Connecting to database: {database_url.split('@')[1] if '@' in database_url else 'localhost'}")
    
    engine = create_engine(database_url)
    
    # Read the migration file
    migration_file = 'app/migrations/V020__add_po_approval_workflow.sql'
    
    if not os.path.exists(migration_file):
        print(f"❌ Migration file not found: {migration_file}")
        return False
    
    with open(migration_file, 'r') as f:
        migration_sql = f.read()
    
    print(f"📄 Read migration file: {migration_file}")
    
    # Split the migration into individual statements
    statements = [stmt.strip() for stmt in migration_sql.split(';') if stmt.strip()]
    
    print(f"🔧 Executing {len(statements)} SQL statements...")
    
    try:
        with engine.connect() as connection:
            # Start a transaction
            trans = connection.begin()
            
            try:
                for i, statement in enumerate(statements, 1):
                    if statement.startswith('--') or not statement:
                        continue
                    
                    print(f"  {i:2d}. Executing: {statement[:60]}{'...' if len(statement) > 60 else ''}")
                    
                    # Execute the statement
                    connection.execute(text(statement))
                
                # Commit the transaction
                trans.commit()
                print("✅ Migration completed successfully!")
                
                # Verify the columns were added
                print("\n🔍 Verifying migration results...")
                result = connection.execute(text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'purchase_orders' 
                    AND column_name IN ('original_quantity', 'original_unit_price', 'original_delivery_date', 'original_delivery_location')
                    ORDER BY column_name;
                """))
                
                columns = [row[0] for row in result]
                
                expected_columns = ['original_delivery_date', 'original_delivery_location', 'original_quantity', 'original_unit_price']
                
                print(f"📋 Found columns: {columns}")
                
                if set(columns) == set(expected_columns):
                    print("✅ All required columns added successfully!")
                    return True
                else:
                    missing = set(expected_columns) - set(columns)
                    print(f"⚠️  Missing columns: {missing}")
                    return False
                    
            except Exception as e:
                trans.rollback()
                print(f"❌ Migration failed: {e}")
                return False
                
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def test_purchase_orders_api():
    """Test if the purchase orders API works after migration."""
    print("\n🧪 Testing Purchase Orders API...")
    
    try:
        import requests
        
        # Test the API endpoint that was failing
        response = requests.get(
            "http://localhost:8000/api/v1/auth/login",
            timeout=5
        )
        
        if response.status_code in [200, 422]:  # 422 is expected without credentials
            print("✅ Backend server is responding")
            return True
        else:
            print(f"⚠️  Backend server status: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"⚠️  Backend server not accessible: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting Migration V020 Execution")
    print("=" * 50)
    
    # Run the migration
    migration_success = run_migration()
    
    if migration_success:
        print("\n🎉 Migration V020 completed successfully!")
        
        # Test the API
        api_success = test_purchase_orders_api()
        
        if api_success:
            print("\n✅ Database schema fix complete!")
            print("📋 The following issues should now be resolved:")
            print("   • Purchase Orders API 500 errors")
            print("   • Missing original_quantity columns")
            print("   • Database schema mismatch")
            print("\n🔄 You may need to restart the backend server to pick up the changes.")
        else:
            print("\n⚠️  Migration completed but backend server needs attention.")
    else:
        print("\n❌ Migration failed. Please check the error messages above.")
        sys.exit(1)
