#!/usr/bin/env python3
"""
Script to keep only the specific palm oil companies we want.
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
    print("🎯 Final cleanup - keeping only specific palm oil companies...")
    
    conn = get_db_connection()
    if not conn:
        print("❌ Failed to connect to database")
        return
    
    try:
        cursor = conn.cursor()
        
        # Define the exact companies we want to keep
        companies_to_keep = [
            "Common Platform",  # Admin platform
            "Asian Refineries Ltd",  # Our palm oil refinery
            "Wilmar Trading Ltd",  # Our palm oil trader
            "Makmur Selalu Mill",  # Our palm oil mill
            "Tani Maju Cooperative",  # Our palm oil cooperative
            "Plantation Estate Sdn Bhd",  # Our palm oil plantation
        ]
        
        # Get all companies
        cursor.execute("""
            SELECT id, name, email, company_type, created_at 
            FROM companies 
            ORDER BY name
        """)
        
        companies = cursor.fetchall()
        print(f"📊 Found {len(companies)} companies in database")
        
        # Identify companies to delete
        companies_to_delete = []
        companies_keeping = []
        
        for company in companies:
            company_id, name, email, company_type, created_at = company
            
            if name in companies_to_keep:
                companies_keeping.append((name, email, company_type))
            else:
                companies_to_delete.append(company_id)
        
        print(f"✅ Keeping {len(companies_keeping)} companies:")
        for name, email, company_type in companies_keeping:
            print(f"  - {name} ({email}) - {company_type}")
        
        print(f"\n🗑️  Deleting {len(companies_to_delete)} remaining companies...")
        
        # Delete companies in batches
        deleted_count = 0
        for company_id in companies_to_delete:
            try:
                # Delete related records first
                cursor.execute("DELETE FROM batch_transactions WHERE source_batch_id IN (SELECT id FROM batches WHERE company_id = %s) OR destination_batch_id IN (SELECT id FROM batches WHERE company_id = %s)", (company_id, company_id))
                cursor.execute("DELETE FROM batches WHERE company_id = %s", (company_id,))
                cursor.execute("DELETE FROM purchase_orders WHERE buyer_company_id = %s OR seller_company_id = %s", (company_id, company_id))
                cursor.execute("DELETE FROM business_relationships WHERE buyer_company_id = %s OR seller_company_id = %s", (company_id, company_id))
                cursor.execute("DELETE FROM access_attempts WHERE requesting_user_id IN (SELECT id FROM users WHERE company_id = %s)", (company_id,))
                cursor.execute("DELETE FROM users WHERE company_id = %s", (company_id,))
                cursor.execute("DELETE FROM companies WHERE id = %s", (company_id,))
                conn.commit()
                deleted_count += 1
                
            except Exception as e:
                print(f"  ❌ Error deleting company {company_id}: {e}")
                conn.rollback()
        
        print(f"✅ Successfully deleted {deleted_count} companies!")
        
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
