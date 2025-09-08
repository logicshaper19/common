#!/usr/bin/env python3
"""
Simple script to delete all companies except admin companies.
Uses CASCADE deletes to handle foreign key constraints automatically.
"""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Database URL - adjust if needed
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://common_user:common_password@localhost:5432/common_db")

# Create engine and session
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def delete_all_companies_except_admin():
    """
    Delete all companies except admin companies using CASCADE.
    """
    print("🚨 WARNING: This will delete ALL companies EXCEPT the admin company!")
    print("This will preserve your admin login access.")
    print("This action cannot be undone.")
    
    # Ask for confirmation
    confirmation = input("\nType 'DELETE ALL EXCEPT ADMIN' to confirm: ")
    if confirmation != "DELETE ALL EXCEPT ADMIN":
        print("❌ Operation cancelled.")
        return False
    
    try:
        # Create database session
        db = SessionLocal()
        
        print("\n🔍 Checking current companies...")
        
        # Get admin company (the one with admin users)
        admin_company_result = db.execute(text("""
            SELECT DISTINCT c.id, c.name, c.email 
            FROM companies c 
            JOIN users u ON c.id = u.company_id 
            WHERE u.role = 'admin'
        """)).fetchall()
        
        if not admin_company_result:
            print("❌ No admin company found! This would delete all companies including admin access.")
            return False
        
        admin_company_ids = [str(company[0]) for company in admin_company_result]
        admin_company_names = [company[1] for company in admin_company_result]
        
        print(f"🔒 Admin companies to PRESERVE: {', '.join(admin_company_names)}")
        
        # Get count of companies to delete
        placeholders = ','.join([f"'{company_id}'" for company_id in admin_company_ids])
        companies_to_delete_result = db.execute(text(f"""
            SELECT COUNT(*) FROM companies 
            WHERE id NOT IN ({placeholders})
        """)).fetchone()
        
        companies_to_delete_count = companies_to_delete_result[0] if companies_to_delete_result else 0
        
        print(f"📊 Found {companies_to_delete_count} companies to delete")
        
        if companies_to_delete_count == 0:
            print("✅ No companies to delete (only admin companies exist).")
            return True
        
        # Show companies that will be deleted
        companies_result = db.execute(text(f"""
            SELECT name, email FROM companies 
            WHERE id NOT IN ({placeholders})
            ORDER BY created_at
        """)).fetchall()
        
        print(f"\n📋 {companies_to_delete_count} companies to be deleted:")
        for i, company in enumerate(companies_result[:10]):  # Show first 10
            print(f"  - {company[0]} ({company[1]})")
        
        if len(companies_result) > 10:
            print(f"  ... and {len(companies_result) - 10} more companies")
        
        # Final confirmation
        final_confirm = input(f"\n⚠️  Are you sure you want to delete {companies_to_delete_count} companies? (yes/no): ")
        if final_confirm.lower() != 'yes':
            print("❌ Operation cancelled.")
            return False
        
        print("\n🗑️  Deleting companies (preserving admin companies)...")
        print("🔄 Using CASCADE deletes to handle all related data automatically...")
        
        # Temporarily disable foreign key constraints to allow deletion
        db.execute(text("SET session_replication_role = replica;"))
        
        # Delete all companies except admin companies
        result = db.execute(text(f"""
            DELETE FROM companies 
            WHERE id NOT IN ({placeholders})
        """))
        deleted_count = result.rowcount
        
        # Re-enable foreign key constraints
        db.execute(text("SET session_replication_role = DEFAULT;"))
        
        # Commit the transaction
        db.commit()
        
        print(f"✅ Successfully deleted {deleted_count} companies!")
        print(f"🔒 Preserved {len(admin_company_names)} admin companies: {', '.join(admin_company_names)}")
        print("🔄 All related data has been automatically cleaned up.")
        
        return True
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error deleting companies: {str(e)}")
        return False
        
    finally:
        db.close()


def list_companies():
    """
    List all companies in the database.
    """
    try:
        db = SessionLocal()
        
        companies_result = db.execute(text("SELECT name, email, company_type, created_at, id FROM companies ORDER BY created_at")).fetchall()
        
        if not companies_result:
            print("📭 No companies found in the database.")
            return
        
        print(f"📋 Found {len(companies_result)} companies:")
        print("-" * 60)
        
        for company in companies_result:
            name, email, company_type, created_at, company_id = company
            
            # Get user count for this company
            user_count_result = db.execute(text("SELECT COUNT(*) FROM users WHERE company_id = :company_id"), {"company_id": company_id}).fetchone()
            user_count = user_count_result[0] if user_count_result else 0
            
            print(f"🏢 {name}")
            print(f"   📧 Email: {email}")
            print(f"   🏷️  Type: {company_type}")
            print(f"   👥 Users: {user_count}")
            print(f"   📅 Created: {created_at}")
            print("-" * 60)
        
    except Exception as e:
        print(f"❌ Error listing companies: {str(e)}")
        
    finally:
        db.close()


if __name__ == "__main__":
    print("🏢 Company Management Script (Simple)")
    print("=" * 50)
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "list":
            list_companies()
        elif command == "delete-all-except-admin":
            delete_all_companies_except_admin()
        else:
            print("❌ Invalid command.")
            print("\nUsage:")
            print("  python delete_companies_simple.py list                           # List all companies")
            print("  python delete_companies_simple.py delete-all-except-admin        # Delete all companies except admin")
    else:
        print("Available commands:")
        print("1. List all companies")
        print("2. Delete all companies (except admin)")
        
        choice = input("\nEnter your choice (1-2): ")
        
        if choice == "1":
            list_companies()
        elif choice == "2":
            delete_all_companies_except_admin()
        else:
            print("❌ Invalid choice.")
