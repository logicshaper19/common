#!/usr/bin/env python3
"""
Script to clean up all generic companies from the database.
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
    print("🗑️  Cleaning up all generic companies from database...")
    
    conn = get_db_connection()
    if not conn:
        print("❌ Failed to connect to database")
        return
    
    try:
        cursor = conn.cursor()
        
        # Get all companies
        cursor.execute("""
            SELECT id, name, email, company_type, created_at 
            FROM companies 
            ORDER BY created_at DESC
        """)
        
        companies = cursor.fetchall()
        print(f"📊 Found {len(companies)} companies in database")
        
        # Identify generic companies to delete
        companies_to_delete = []
        palm_oil_companies = []
        
        for company in companies:
            company_id, name, email, company_type, created_at = company
            
            # Keep palm oil companies and Common Platform
            if any(x in name.lower() for x in ['wilmar', 'makmur', 'tani', 'plantation estate', 'asian refineries', 'l\'oreal', 'common platform']):
                palm_oil_companies.append((name, email, company_type))
            else:
                companies_to_delete.append(company_id)
        
        print(f"✅ Keeping {len(palm_oil_companies)} palm oil companies:")
        for name, email, company_type in palm_oil_companies:
            print(f"  - {name} ({email}) - {company_type}")
        
        print(f"\n🗑️  Deleting {len(companies_to_delete)} generic companies...")
        
        # Delete companies in batches to avoid foreign key issues
        deleted_count = 0
        for company_id in companies_to_delete:
            try:
                # Delete related records first
                cursor.execute("DELETE FROM batches WHERE source_purchase_order_id IN (SELECT id FROM purchase_orders WHERE buyer_company_id = %s OR seller_company_id = %s)", (company_id, company_id))
                cursor.execute("DELETE FROM purchase_orders WHERE buyer_company_id = %s OR seller_company_id = %s", (company_id, company_id))
                cursor.execute("DELETE FROM users WHERE company_id = %s", (company_id,))
                cursor.execute("DELETE FROM companies WHERE id = %s", (company_id,))
                conn.commit()
                deleted_count += 1
                
                if deleted_count % 50 == 0:
                    print(f"  ✅ Deleted {deleted_count} companies...")
                    
            except Exception as e:
                print(f"  ❌ Error deleting company {company_id}: {e}")
                conn.rollback()
        
        print(f"✅ Successfully deleted {deleted_count} generic companies!")
        
        # Verify final state
        cursor.execute("SELECT COUNT(*) FROM companies")
        final_count = cursor.fetchone()[0]
        print(f"📊 Final company count: {final_count}")
        
        # Show remaining companies
        cursor.execute("SELECT name, email, company_type FROM companies ORDER BY name")
        remaining = cursor.fetchall()
        print(f"\n🏢 Remaining companies:")
        for name, email, company_type in remaining:
            print(f"  ✅ {name} - {email} ({company_type})")
        
    except Exception as e:
        print(f"❌ Error during cleanup: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    main()
