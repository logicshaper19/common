#!/usr/bin/env python3
"""
Script to delete all companies from the database.
WARNING: This will permanently delete all company data!
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


def delete_all_companies():
    """
    Delete all companies from the database EXCEPT the admin company.
    This preserves the ability to log in.
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

        # Get list of user IDs from non-admin companies
        users_to_delete_result = db.execute(text(f"""
            SELECT id FROM users
            WHERE company_id NOT IN ({placeholders}) AND role != 'admin'
        """)).fetchall()

        user_ids_to_delete = [str(user[0]) for user in users_to_delete_result]

        if user_ids_to_delete:
            user_placeholders = ','.join([f"'{user_id}'" for user_id in user_ids_to_delete])

            # Step 1: Delete related data that references users
            print("🗑️  Step 1: Deleting user-related data...")

            # Delete documents uploaded by these users
            docs_result = db.execute(text(f"""
                DELETE FROM documents WHERE uploaded_by_user_id IN ({user_placeholders})
            """))
            print(f"   Deleted {docs_result.rowcount} documents")

            # Delete notifications for these users
            notif_result = db.execute(text(f"""
                DELETE FROM notifications WHERE user_id IN ({user_placeholders})
            """))
            print(f"   Deleted {notif_result.rowcount} notifications")

            # Delete audit events by these users
            audit_result = db.execute(text(f"""
                DELETE FROM audit_events WHERE user_id IN ({user_placeholders})
            """))
            print(f"   Deleted {audit_result.rowcount} audit events")

            # Step 2: Delete users from non-admin companies
            print("🗑️  Step 2: Deleting users from non-admin companies...")
            users_result = db.execute(text(f"""
                DELETE FROM users WHERE id IN ({user_placeholders})
            """))
            deleted_users = users_result.rowcount
            print(f"   Deleted {deleted_users} non-admin users")

        # Step 3: Delete company-related data
        print("🗑️  Step 3: Deleting company-related data...")

        # Delete purchase orders from these companies
        po_result = db.execute(text(f"""
            DELETE FROM purchase_orders
            WHERE buyer_company_id NOT IN ({placeholders})
            OR seller_company_id NOT IN ({placeholders})
        """))
        print(f"   Deleted {po_result.rowcount} purchase orders")

        # Step 4: Delete companies
        print("🗑️  Step 4: Deleting companies...")
        result = db.execute(text(f"""
            DELETE FROM companies
            WHERE id NOT IN ({placeholders})
        """))
        deleted_count = result.rowcount

        # Commit the transaction
        db.commit()

        print(f"✅ Successfully deleted {deleted_count} companies!")
        print(f"🔒 Preserved {len(admin_company_names)} admin companies: {', '.join(admin_company_names)}")
        print("🔄 All related data (users, purchase orders, etc.) has been automatically deleted due to foreign key constraints.")

        return True

    except Exception as e:
        db.rollback()
        print(f"❌ Error deleting companies: {str(e)}")
        return False

    finally:
        db.close()


def delete_specific_company(company_email: str):
    """
    Delete a specific company by email.
    """
    try:
        db = SessionLocal()

        # Find the company
        company_result = db.execute(text("SELECT name, email FROM companies WHERE email = :email"), {"email": company_email}).fetchone()

        if not company_result:
            print(f"❌ Company with email '{company_email}' not found.")
            return False

        company_name = company_result[0]
        print(f"🔍 Found company: {company_name} ({company_email})")

        # Confirm deletion
        confirm = input(f"⚠️  Delete company '{company_name}'? (yes/no): ")
        if confirm.lower() != 'yes':
            print("❌ Operation cancelled.")
            return False

        # Delete the company
        result = db.execute(text("DELETE FROM companies WHERE email = :email"), {"email": company_email})
        db.commit()

        print(f"✅ Successfully deleted company '{company_name}'!")

        return True

    except Exception as e:
        db.rollback()
        print(f"❌ Error deleting company: {str(e)}")
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
    print("🏢 Company Management Script")
    print("=" * 50)
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "list":
            list_companies()
        elif command == "delete-all-except-admin":
            delete_all_companies()
        elif command == "delete" and len(sys.argv) > 2:
            company_email = sys.argv[2]
            delete_specific_company(company_email)
        else:
            print("❌ Invalid command.")
            print("\nUsage:")
            print("  python delete_all_companies.py list                           # List all companies")
            print("  python delete_all_companies.py delete-all-except-admin        # Delete all companies except admin")
            print("  python delete_all_companies.py delete <email>                 # Delete specific company")
    else:
        print("Available commands:")
        print("1. List all companies")
        print("2. Delete all companies (except admin)")
        print("3. Delete specific company")

        choice = input("\nEnter your choice (1-3): ")

        if choice == "1":
            list_companies()
        elif choice == "2":
            delete_all_companies()
        elif choice == "3":
            email = input("Enter company email: ")
            delete_specific_company(email)
        else:
            print("❌ Invalid choice.")
