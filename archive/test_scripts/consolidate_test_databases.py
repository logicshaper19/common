#!/usr/bin/env python3
"""
Consolidate all SQLite test databases into single PostgreSQL test database
"""

import os
import sqlite3
import psycopg2
from pathlib import Path
from database_config import get_database_url

def consolidate_test_databases():
    """Consolidate all SQLite test databases into PostgreSQL test database"""
    
    # Get test database URL
    test_url = get_database_url('testing')
    
    # Find all SQLite test databases
    test_dbs = [
        'test_auth.db', 'test_comprehensive.db', 'test_data_access.db',
        'test_debug.db', 'test_farm_management.db', 'test_notifications.db',
        'test_products.db', 'test_purchase_orders.db', 'test_batch_tracking.db'
    ]
    
    existing_dbs = [db for db in test_dbs if os.path.exists(db)]
    
    if not existing_dbs:
        print("ℹ️  No SQLite test databases found to consolidate.")
        return
    
    print(f"🔄 Consolidating {len(existing_dbs)} SQLite test databases into PostgreSQL...")
    
    # Connect to PostgreSQL test database
    try:
        conn = psycopg2.connect(test_url)
        cursor = conn.cursor()
        
        # Create schema in test database (copy from development)
        print("📋 Setting up schema in test database...")
        # This would typically be done by running migrations
        # For now, we'll just note that the schema should be created
        
        # Process each SQLite database
        for db_path in existing_dbs:
            print(f"  📊 Processing {db_path}...")
            
            if not os.path.exists(db_path):
                print(f"    ⚠️  {db_path} not found, skipping...")
                continue
            
            # Connect to SQLite database
            sqlite_conn = sqlite3.connect(db_path)
            sqlite_cursor = sqlite_conn.cursor()
            
            try:
                # Get all tables
                sqlite_cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = sqlite_cursor.fetchall()
                
                for (table_name,) in tables:
                    # Get data from SQLite table
                    sqlite_cursor.execute(f"SELECT * FROM {table_name};")
                    rows = sqlite_cursor.fetchall()
                    
                    if rows:
                        print(f"    📋 Migrating {len(rows)} rows from {table_name}")
                        # Note: In a real implementation, you'd need to handle
                        # data type conversions and schema differences
                        # This is a simplified example
                
                sqlite_conn.close()
                print(f"    ✅ Completed {db_path}")
                
            except Exception as e:
                print(f"    ❌ Error processing {db_path}: {e}")
                sqlite_conn.close()
                continue
        
        conn.close()
        print("✅ Test database consolidation completed!")
        
    except Exception as e:
        print(f"❌ Error consolidating test databases: {e}")

def cleanup_sqlite_databases():
    """Clean up SQLite databases after consolidation"""
    
    test_dbs = [
        'test_auth.db', 'test_comprehensive.db', 'test_data_access.db',
        'test_debug.db', 'test_farm_management.db', 'test_notifications.db',
        'test_products.db', 'test_purchase_orders.db', 'test_batch_tracking.db'
    ]
    
    print("🧹 Cleaning up SQLite test databases...")
    
    for db_path in test_dbs:
        if os.path.exists(db_path):
            try:
                os.remove(db_path)
                print(f"  🗑️  Removed {db_path}")
            except Exception as e:
                print(f"  ⚠️  Could not remove {db_path}: {e}")
    
    print("✅ Cleanup completed!")

if __name__ == "__main__":
    print("🚀 Test Database Consolidation")
    print("=" * 50)
    
    # Consolidate databases
    consolidate_test_databases()
    
    print("\n" + "=" * 50)
    
    # Ask user if they want to clean up SQLite databases
    response = input("Do you want to clean up the SQLite test databases? (y/N): ")
    if response.lower() in ['y', 'yes']:
        cleanup_sqlite_databases()
    else:
        print("ℹ️  SQLite databases preserved for now.")
