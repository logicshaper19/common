#!/usr/bin/env python3
"""
Aggressive cleanup script to remove all unwanted companies and their related data.
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
    print("🔥 Aggressive cleanup - removing all unwanted companies...")
    
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
        cursor.execute("SELECT id, name FROM companies")
        companies = cursor.fetchall()
        
        companies_to_delete = []
        for company_id, name in companies:
            if name not in companies_to_keep:
                companies_to_delete.append(company_id)
        
        print(f"🗑️  Deleting {len(companies_to_delete)} companies and all their related data...")
        
        # Delete in the correct order to handle foreign key constraints
        for company_id in companies_to_delete:
            try:
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
                
            except Exception as e:
                print(f"  ❌ Error deleting company {company_id}: {e}")
                conn.rollback()
        
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
