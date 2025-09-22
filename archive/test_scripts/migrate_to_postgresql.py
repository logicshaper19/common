#!/usr/bin/env python3
"""
Migration script to consolidate all databases to PostgreSQL
Migrates data from SQLite to PostgreSQL development database
"""

import os
import sys
import sqlite3
import psycopg2
from pathlib import Path
from database_config import get_database_url, get_database_info

def migrate_sqlite_to_postgresql(sqlite_db_path: str, postgres_url: str):
    """
    Migrate data from SQLite database to PostgreSQL
    
    Args:
        sqlite_db_path: Path to SQLite database file
        postgres_url: PostgreSQL connection URL
    """
    print(f"🔄 Migrating {sqlite_db_path} to PostgreSQL...")
    
    # Connect to SQLite
    sqlite_conn = sqlite3.connect(sqlite_db_path)
    sqlite_cursor = sqlite_conn.cursor()
    
    # Connect to PostgreSQL
    postgres_conn = psycopg2.connect(postgres_url)
    postgres_cursor = postgres_conn.cursor()
    
    try:
        # Get all tables from SQLite
        sqlite_cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = sqlite_cursor.fetchall()
        
        for (table_name,) in tables:
            print(f"  📋 Migrating table: {table_name}")
            
            # Get table schema
            sqlite_cursor.execute(f"PRAGMA table_info({table_name});")
            columns = sqlite_cursor.fetchall()
            
            # Get all data from SQLite table
            sqlite_cursor.execute(f"SELECT * FROM {table_name};")
            rows = sqlite_cursor.fetchall()
            
            if not rows:
                print(f"    ⚠️  Table {table_name} is empty, skipping...")
                continue
            
            # Insert data into PostgreSQL
            # Note: This is a simplified migration - in production you'd want more robust handling
            for row in rows:
                try:
                    # Convert SQLite row to PostgreSQL format
                    # This is a basic conversion - you might need more sophisticated handling
                    placeholders = ', '.join(['%s'] * len(row))
                    insert_query = f"INSERT INTO {table_name} VALUES ({placeholders}) ON CONFLICT DO NOTHING;"
                    postgres_cursor.execute(insert_query, row)
                except Exception as e:
                    print(f"    ⚠️  Error inserting row into {table_name}: {e}")
                    continue
            
            postgres_conn.commit()
            print(f"    ✅ Migrated {len(rows)} rows to {table_name}")
    
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        postgres_conn.rollback()
        raise
    finally:
        sqlite_conn.close()
        postgres_conn.close()

def main():
    """Main migration function"""
    print("🚀 Starting PostgreSQL Consolidation Migration")
    print("=" * 60)
    
    # Get database info
    db_info = get_database_info()
    print(f"Target Database: {db_info['database']}")
    print(f"Environment: {db_info['environment']}")
    print()
    
    # Find SQLite databases to migrate
    sqlite_dbs = []
    
    # Main development database
    if os.path.exists('common.db'):
        sqlite_dbs.append(('common.db', 'Main development database'))
    
    # Test databases
    test_dbs = [
        'test_auth.db', 'test_comprehensive.db', 'test_data_access.db',
        'test_debug.db', 'test_farm_management.db', 'test_notifications.db',
        'test_products.db', 'test_purchase_orders.db', 'test_batch_tracking.db'
    ]
    
    for db in test_dbs:
        if os.path.exists(db):
            sqlite_dbs.append((db, f'Test database: {db}'))
    
    if not sqlite_dbs:
        print("ℹ️  No SQLite databases found to migrate.")
        return
    
    print(f"Found {len(sqlite_dbs)} SQLite databases to migrate:")
    for db_path, description in sqlite_dbs:
        print(f"  - {db_path}: {description}")
    print()
    
    # Get target PostgreSQL URL
    target_url = get_database_url('development')
    
    # Migrate each database
    for db_path, description in sqlite_dbs:
        try:
            migrate_sqlite_to_postgresql(db_path, target_url)
        except Exception as e:
            print(f"❌ Failed to migrate {db_path}: {e}")
            continue
    
    print()
    print("✅ Migration completed!")
    print()
    print("Next steps:")
    print("1. Update your .env file to use the development database")
    print("2. Test the application with the new database")
    print("3. Remove old SQLite databases once confirmed working")

if __name__ == "__main__":
    main()
