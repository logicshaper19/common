#!/usr/bin/env python3
"""
Script to check what companies actually exist in the database.
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
    print("🔍 Checking companies in database...")
    
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
        
        # Categorize companies
        palm_oil_companies = []
        generic_companies = []
        other_companies = []
        
        for company in companies:
            company_id, name, email, company_type, created_at = company
            
            if any(x in name.lower() for x in ['wilmar', 'makmur', 'tani', 'plantation estate', 'asian refineries', 'l\'oreal']):
                palm_oil_companies.append((name, email, company_type, created_at))
            elif any(x in name.lower() for x in ['company 1', 'company 2', 'green acres plantation']):
                generic_companies.append((name, email, company_type, created_at))
            else:
                other_companies.append((name, email, company_type, created_at))
        
        print(f"\n🌴 Palm Oil Companies ({len(palm_oil_companies)}):")
        for name, email, company_type, created_at in palm_oil_companies:
            print(f"  ✅ {name} - {email} ({company_type}) - {created_at}")
        
        print(f"\n🗑️  Generic Companies ({len(generic_companies)}):")
        for name, email, company_type, created_at in generic_companies[:10]:  # Show first 10
            print(f"  ❌ {name} - {email} ({company_type}) - {created_at}")
        if len(generic_companies) > 10:
            print(f"  ... and {len(generic_companies) - 10} more generic companies")
        
        print(f"\n🏢 Other Companies ({len(other_companies)}):")
        for name, email, company_type, created_at in other_companies:
            print(f"  ℹ️  {name} - {email} ({company_type}) - {created_at}")
        
        # Check if we need to clean up more
        if len(generic_companies) > 0:
            print(f"\n⚠️  There are still {len(generic_companies)} generic companies in the database!")
            print("These are likely appearing in the frontend dropdown.")
            
            # Ask if we should delete them
            response = input("\nDo you want to delete all generic companies? (y/N): ")
            if response.lower() == 'y':
                print("🗑️  Deleting generic companies...")
                
                # Delete in batches to avoid foreign key issues
                generic_company_ids = [company[0] for company in generic_companies]
                
                for company_id in generic_company_ids:
                    try:
                        # Delete related records first
                        cursor.execute("DELETE FROM batches WHERE source_purchase_order_id IN (SELECT id FROM purchase_orders WHERE buyer_company_id = %s OR seller_company_id = %s)", (company_id, company_id))
                        cursor.execute("DELETE FROM purchase_orders WHERE buyer_company_id = %s OR seller_company_id = %s", (company_id, company_id))
                        cursor.execute("DELETE FROM users WHERE company_id = %s", (company_id,))
                        cursor.execute("DELETE FROM companies WHERE id = %s", (company_id,))
                        conn.commit()
                        print(f"  ✅ Deleted company {company_id}")
                    except Exception as e:
                        print(f"  ❌ Error deleting company {company_id}: {e}")
                        conn.rollback()
                
                print("✅ Cleanup completed!")
        
    except Exception as e:
        print(f"❌ Error querying database: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    main()
