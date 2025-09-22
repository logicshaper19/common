#!/usr/bin/env python3
"""
Final targeted cleanup to remove all generic companies except our specific palm oil companies.
"""

import psycopg2
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_db_connection():
    """Get database connection."""
    try:
        # Try to get from environment variable first
        database_url = os.getenv('DATABASE_URL')
        if database_url:
            return psycopg2.connect(database_url)
        
        # Fallback to individual components
        return psycopg2.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            port=os.getenv('DB_PORT', '5432'),
            database=os.getenv('DB_NAME', 'common_supply_chain'),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD', 'password')
        )
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return None

def main():
    print("🎯 Final targeted cleanup - removing all generic companies...")
    
    conn = get_db_connection()
    if not conn:
        print("❌ Failed to connect to database")
        return
    
    try:
        cursor = conn.cursor()
        
        # Get all companies
        cursor.execute("SELECT id, name, email FROM companies ORDER BY name")
        companies = cursor.fetchall()
        
        print(f"📊 Found {len(companies)} companies in database")
        
        # Identify companies to delete (all except our specific palm oil companies)
        companies_to_delete = []
        companies_keeping = []
        
        for company_id, name, email in companies:
            # Keep only our specific palm oil companies
            if name in ["Common Platform", "Asian Refineries Ltd", "Wilmar Trading Ltd", "Makmur Selalu Mill", "Tani Maju Cooperative", "Plantation Estate Sdn Bhd"]:
                companies_keeping.append((name, email))
            else:
                companies_to_delete.append((company_id, name, email))
        
        print(f"✅ Keeping {len(companies_keeping)} companies:")
        for name, email in companies_keeping:
            print(f"  - {name} ({email})")
        
        print(f"\n🗑️  Deleting {len(companies_to_delete)} generic companies:")
        for company_id, name, email in companies_to_delete:
            print(f"  - {name} ({email})")
        
        # Delete companies one by one with proper error handling
        deleted_count = 0
        for company_id, name, email in companies_to_delete:
            try:
                # Use CASCADE to handle foreign key constraints
                cursor.execute("DELETE FROM companies WHERE id = %s CASCADE", (company_id,))
                conn.commit()
                deleted_count += 1
                print(f"  ✅ Deleted {name}")
                
            except Exception as e:
                print(f"  ❌ Error deleting {name}: {e}")
                conn.rollback()
        
        print(f"\n✅ Successfully deleted {deleted_count} companies!")
        
        # Verify final state
        cursor.execute("SELECT COUNT(*) FROM companies")
        final_count = cursor.fetchone()[0]
        print(f"📊 Final company count: {final_count}")
        
        # Show remaining companies
        cursor.execute("SELECT name, email, company_type FROM companies ORDER BY name")
        remaining = cursor.fetchall()
        print(f"\n🏢 Final companies list:")
        for name, email, company_type in remaining:
            print(f"  ✅ {name} - {email} ({company_type})")
        
    except Exception as e:
        print(f"❌ Error during cleanup: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    main()
