#!/usr/bin/env python3
"""
Create originator user in PostgreSQL database - simplified version
"""

import psycopg2
import bcrypt
from datetime import datetime
import uuid

# Database connection parameters
from database_config import get_database_url
import psycopg2

# Use development database
dev_url = get_database_url('development')

def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def create_originator_user():
    """Create originator user in PostgreSQL"""
    try:
        # Connect to PostgreSQL
        conn = psycopg2.connect(dev_url)
        cursor = conn.cursor()
        
        # First, create the originator company if it doesn't exist
        company_id = str(uuid.uuid4())
        cursor.execute("""
            INSERT INTO companies (id, name, company_type, email, phone, address_street, address_city, address_country, website, is_active, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            company_id,
            'Organic Farms Ltd',
            'plantation_grower',
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
        
        print("✅ Created originator company: Organic Farms Ltd")
        
        # Hash the password
        hashed_password = hash_password("password123")
        
        # Insert originator user
        user_id = str(uuid.uuid4())
        cursor.execute("""
            INSERT INTO users (
                id, email, hashed_password, full_name, 
                role, company_id, is_active, created_at, updated_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            user_id,
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
        
        print("✅ Originator user created successfully!")
        print(f"   Email: originator@organicfarms.com")
        print(f"   Password: password123")
        print(f"   Role: originator")
        print(f"   Company: Organic Farms Ltd")
        
        cursor.close()
        conn.close()
        
    except psycopg2.IntegrityError as e:
        if "duplicate key value" in str(e):
            print("✅ Originator user already exists!")
            print(f"   Email: originator@organicfarms.com")
            print(f"   Password: password123")
        else:
            print(f"❌ Integrity Error: {e}")
    except psycopg2.Error as e:
        print(f"❌ PostgreSQL Error: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    create_originator_user()
