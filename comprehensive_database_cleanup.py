#!/usr/bin/env python3
"""
Comprehensive database cleanup to remove all generic companies except our specific palm oil companies.
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
    print("🧹 Comprehensive database cleanup - removing all generic companies...")
    
    conn = get_db_connection()
    if not conn:
        print("❌ Failed to connect to database")
        return
    
    try:
        cursor = conn.cursor()
        
        # Define the exact companies we want to keep
        companies_to_keep = [
            "Common Platform",
            "Asian Refineries Ltd", 
            "Wilmar Trading Ltd",
            "Makmur Selalu Mill",
            "Tani Maju Cooperative",
            "Plantation Estate Sdn Bhd",
        ]
        
        # Get all companies
        cursor.execute("SELECT id, name, email FROM companies ORDER BY name")
        companies = cursor.fetchall()
        
        print(f"📊 Found {len(companies)} companies in database")
        
        # Identify companies to delete
        companies_to_delete = []
        companies_keeping = []
        
        for company_id, name, email in companies:
            if name in companies_to_keep:
                companies_keeping.append((name, email))
            else:
                companies_to_delete.append((company_id, name, email))
        
        print(f"✅ Keeping {len(companies_keeping)} companies:")
        for name, email in companies_keeping:
            print(f"  - {name} ({email})")
        
        print(f"\n🗑️  Deleting {len(companies_to_delete)} generic companies...")
        
        # Delete companies one by one with proper error handling
        deleted_count = 0
        for company_id, name, email in companies_to_delete:
            try:
                # Delete in the correct order to handle foreign key constraints
                # 1. Delete audit events
                cursor.execute("DELETE FROM audit_events WHERE actor_user_id IN (SELECT id FROM users WHERE company_id = %s)", (company_id,))
                
                # 2. Delete access attempts
                cursor.execute("DELETE FROM access_attempts WHERE requesting_user_id IN (SELECT id FROM users WHERE company_id = %s)", (company_id,))
                
                # 3. Delete batch transactions
                cursor.execute("DELETE FROM batch_transactions WHERE source_batch_id IN (SELECT id FROM batches WHERE company_id = %s) OR destination_batch_id IN (SELECT id FROM batches WHERE company_id = %s)", (company_id, company_id))
                
                # 4. Delete batches
                cursor.execute("DELETE FROM batches WHERE company_id = %s", (company_id,))
                
                # 5. Delete purchase orders
                cursor.execute("DELETE FROM purchase_orders WHERE buyer_company_id = %s OR seller_company_id = %s", (company_id, company_id))
                
                # 6. Delete business relationships
                cursor.execute("DELETE FROM business_relationships WHERE buyer_company_id = %s OR seller_company_id = %s", (company_id, company_id))
                
                # 7. Delete users
                cursor.execute("DELETE FROM users WHERE company_id = %s", (company_id,))
                
                # 8. Delete company
                cursor.execute("DELETE FROM companies WHERE id = %s", (company_id,))
                
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
        
        # Verify we have exactly the companies we want
        remaining_names = [company[0] for company in remaining]
        missing_companies = [name for name in companies_to_keep if name not in remaining_names]
        extra_companies = [name for name in remaining_names if name not in companies_to_keep]
        
        if missing_companies:
            print(f"\n⚠️  Missing companies: {missing_companies}")
        if extra_companies:
            print(f"\n⚠️  Extra companies: {extra_companies}")
        
        if not missing_companies and not extra_companies:
            print(f"\n🎉 Perfect! Database cleanup completed successfully!")
            print(f"   - All generic companies removed")
            print(f"   - Only palm oil companies remain")
            print(f"   - Frontend dropdown should now show only relevant companies")
        
    except Exception as e:
        print(f"❌ Error during cleanup: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    main()
