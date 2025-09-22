#!/usr/bin/env python3
"""
Create originator user in PostgreSQL database
"""

import psycopg2
import bcrypt
from datetime import datetime
import uuid

# Database connection parameters
DB_CONFIG = {
    'host': 'localhost',
    'database': 'common_db',
    'user': 'elisha',
    'password': 'password123',
    'port': '5432'
}

def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def create_originator_user():
    """Create originator user in PostgreSQL"""
    try:
        # Connect to PostgreSQL
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # First, create the originator company if it doesn't exist
        cursor.execute("""
            INSERT INTO companies (id, name, company_type, email, phone, address_street, address_city, address_country, website, is_active, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (name) DO NOTHING
        """, (
            str(uuid.uuid4()),
            'Organic Farms Ltd',
            'originator',
            'contact@organicfarms.com',
            '+1-555-0123',
            '123 Farm Road',
            'Rural Valley',
            'United States',
            'https://www.organicfarms.com',
            True,
            datetime.now(),
            datetime.now()
        ))
        
        # Get the company ID
        cursor.execute("SELECT id FROM companies WHERE name = %s", ('Organic Farms Ltd',))
        company_result = cursor.fetchone()
        company_id = company_result[0] if company_result else str(uuid.uuid4())
        
        # Hash the password
        hashed_password = hash_password("password123")
        
        # Insert originator user
        cursor.execute("""
            INSERT INTO users (
                id, email, hashed_password, full_name, 
                role, company_id, is_active, created_at, updated_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (email) 
            DO UPDATE SET 
                hashed_password = EXCLUDED.hashed_password,
                updated_at = EXCLUDED.updated_at
        """, (
            str(uuid.uuid4()),
            'originator@organicfarms.com',
            hashed_password,
            'Farm Manager',
            'originator',
            company_id,
            True,
            datetime.now(),
            datetime.now()
        ))
        
        # Commit the transaction
        conn.commit()
        
        # Verify the user was created
        cursor.execute("SELECT email, role, full_name FROM users WHERE email = %s", 
                      ('originator@organicfarms.com',))
        user = cursor.fetchone()
        
        if user:
            print("✅ Originator user created successfully!")
            print(f"   Email: {user[0]}")
            print(f"   Role: {user[1]}")
            print(f"   Name: {user[2]}")
            print(f"   Password: password123")
        
        cursor.close()
        conn.close()
        
    except psycopg2.Error as e:
        print(f"❌ PostgreSQL Error: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    create_originator_user()
