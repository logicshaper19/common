#!/usr/bin/env python3
"""
Final script to delete all companies except admin companies.
Handles deletions in the correct order to avoid foreign key violations.
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
    Delete all companies except admin companies.
    Handles deletions in the correct order to avoid foreign key violations.
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
        
        # Get companies to delete
        placeholders = ','.join([f"'{company_id}'" for company_id in admin_company_ids])
        companies_to_delete_result = db.execute(text(f"""
            SELECT id, name, email FROM companies 
            WHERE id NOT IN ({placeholders})
        """)).fetchall()
        
        if not companies_to_delete_result:
            print("✅ No companies to delete (only admin companies exist).")
            return True
        
        company_ids_to_delete = [str(company[0]) for company in companies_to_delete_result]
        company_placeholders = ','.join([f"'{company_id}'" for company_id in company_ids_to_delete])
        
        print(f"📊 Found {len(companies_to_delete_result)} companies to delete")
        
        # Show companies that will be deleted
        print(f"\n📋 Companies to be deleted:")
        for i, company in enumerate(companies_to_delete_result[:10]):  # Show first 10
            print(f"  - {company[1]} ({company[2]})")
        
        if len(companies_to_delete_result) > 10:
            print(f"  ... and {len(companies_to_delete_result) - 10} more companies")
        
        # Final confirmation
        final_confirm = input(f"\n⚠️  Are you sure you want to delete {len(companies_to_delete_result)} companies? (yes/no): ")
        if final_confirm.lower() != 'yes':
            print("❌ Operation cancelled.")
            return False
        
        print("\n🗑️  Deleting companies and related data in correct order...")
        
        # Step 1: Delete data that references users from these companies
        print("🗑️  Step 1: Deleting user-related data...")
        
        # Get users from companies to delete
        users_result = db.execute(text(f"""
            SELECT id FROM users WHERE company_id IN ({company_placeholders})
        """)).fetchall()
        
        if users_result:
            user_ids = [str(user[0]) for user in users_result]
            user_placeholders = ','.join([f"'{user_id}'" for user_id in user_ids])
            
            # Delete documents
            try:
                docs_result = db.execute(text(f"""
                    DELETE FROM documents WHERE uploaded_by_user_id IN ({user_placeholders})
                """))
                print(f"   Deleted {docs_result.rowcount} documents")
            except Exception as e:
                print(f"   Documents: {e}")
            
            # Delete notifications
            try:
                notif_result = db.execute(text(f"""
                    DELETE FROM notifications WHERE user_id IN ({user_placeholders})
                """))
                print(f"   Deleted {notif_result.rowcount} notifications")
            except Exception as e:
                print(f"   Notifications: {e}")
        
        # Step 2: Delete purchase orders
        print("🗑️  Step 2: Deleting purchase orders...")
        try:
            po_result = db.execute(text(f"""
                DELETE FROM purchase_orders 
                WHERE buyer_company_id IN ({company_placeholders}) 
                OR seller_company_id IN ({company_placeholders})
            """))
            print(f"   Deleted {po_result.rowcount} purchase orders")
        except Exception as e:
            print(f"   Purchase orders: {e}")
        
        # Step 3: Delete business relationships
        print("🗑️  Step 3: Deleting business relationships...")
        try:
            br_result = db.execute(text(f"""
                DELETE FROM business_relationships 
                WHERE company_a_id IN ({company_placeholders}) 
                OR company_b_id IN ({company_placeholders})
            """))
            print(f"   Deleted {br_result.rowcount} business relationships")
        except Exception as e:
            print(f"   Business relationships: {e}")
        
        # Step 4: Delete users
        print("🗑️  Step 4: Deleting users...")
        try:
            users_delete_result = db.execute(text(f"""
                DELETE FROM users WHERE company_id IN ({company_placeholders})
            """))
            print(f"   Deleted {users_delete_result.rowcount} users")
        except Exception as e:
            print(f"   Users: {e}")
        
        # Step 5: Finally delete companies
        print("🗑️  Step 5: Deleting companies...")
        result = db.execute(text(f"""
            DELETE FROM companies WHERE id IN ({company_placeholders})
        """))
        deleted_count = result.rowcount
        
        # Commit the transaction
        db.commit()
        
        print(f"✅ Successfully deleted {deleted_count} companies!")
        print(f"🔒 Preserved {len(admin_company_names)} admin companies: {', '.join(admin_company_names)}")
        
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
    print("🏢 Company Management Script (Final)")
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
            print("  python delete_companies_final.py list                           # List all companies")
            print("  python delete_companies_final.py delete-all-except-admin        # Delete all companies except admin")
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
