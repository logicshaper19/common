#!/usr/bin/env python3
"""
Create admin user in development PostgreSQL database
"""

import psycopg2
import bcrypt
from datetime import datetime
import uuid
from database_config import get_database_url

def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def create_admin_user():
    """Create admin user in development database"""
    try:
        # Connect to development database
        dev_url = get_database_url('development')
        conn = psycopg2.connect(dev_url)
        cursor = conn.cursor()
        
        # First, create the admin company if it doesn't exist
        company_id = str(uuid.uuid4())
        cursor.execute("""
            INSERT INTO companies (id, name, company_type, email, phone, website, country, 
                                 industry_sector, industry_subcategory, address_street, address_city, 
                                 address_state, address_postal_code, address_country, subscription_tier, 
                                 compliance_status, is_active, is_verified, transparency_score, 
                                 last_activity, sector_id, tier_level, erp_integration_enabled, 
                                 erp_system_type, erp_api_endpoint, erp_webhook_url, erp_sync_frequency, 
                                 erp_last_sync_at, erp_sync_enabled, erp_configuration, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (email) DO NOTHING
        """, (
            company_id,
            'Common Platform',
            'brand',
            'elisha@common.co',
            None, None, None, None, None, None, None, None, None, None,
            'free', 'pending_review', True, False, None, None, None, None,
            False, None, None, None, None, None, False, 'null',
            datetime.now(), datetime.now()
        ))
        
        # Get the company ID (either newly created or existing)
        cursor.execute("SELECT id FROM companies WHERE email = %s", ('elisha@common.co',))
        company_result = cursor.fetchone()
        if company_result:
            company_id = company_result[0]
            print(f"Using company: {company_id}")
        else:
            print("Failed to create/find company")
            return
        
        # Create admin user
        user_id = str(uuid.uuid4())
        password = "password123"
        hashed_password = hash_password(password)
        
        cursor.execute("""
            INSERT INTO users (id, email, hashed_password, full_name, role, is_active, 
                             company_id, sector_id, tier_level, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (email) DO NOTHING
        """, (
            user_id,
            'elisha@common.co',
            hashed_password,
            'Elisha',
            'admin',
            True,
            company_id,
            None,
            None,
            datetime.now(),
            datetime.now()
        ))
        
        conn.commit()
        print("✅ Admin user created successfully!")
        print(f"Email: elisha@common.co")
        print(f"Password: {password}")
        print(f"Role: admin")
        
    except Exception as e:
        print(f"❌ Error creating admin user: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    create_admin_user()
