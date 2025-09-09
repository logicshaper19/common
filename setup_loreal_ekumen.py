#!/usr/bin/env python3
"""
Script to set up L'Oreal and Ekumen companies with sample data for transparency testing.
"""
import os
import uuid
from datetime import datetime, date
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import json

def setup_companies_and_data():
    """Set up L'Oreal and Ekumen companies with sample purchase orders."""

    # Get database URL from environment or use default PostgreSQL
    database_url = os.getenv('DATABASE_URL', 'postgresql://common_user:common_password@localhost:5432/common_db')

    # Create database engine and session
    engine = create_engine(database_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    
    try:
        # Create L'Oreal company (buyer)
        loreal_id = str(uuid.uuid4()).replace('-', '')
        loreal_data = {
            'id': loreal_id,
            'name': 'L\'Oreal',
            'company_type': 'brand',
            'email': 'contact@loreal.com',
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }

        cursor.execute("""
            INSERT INTO companies (id, name, company_type, email, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            loreal_data['id'],
            loreal_data['name'],
            loreal_data['company_type'],
            loreal_data['email'],
            loreal_data['created_at'],
            loreal_data['updated_at']
        ))
        
        # Create Ekumen company (supplier)
        ekumen_id = str(uuid.uuid4()).replace('-', '')
        ekumen_data = {
            'id': ekumen_id,
            'name': 'Ekumen',
            'company_type': 'originator',
            'email': 'contact@ekumen.com',
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }

        cursor.execute("""
            INSERT INTO companies (id, name, company_type, email, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            ekumen_data['id'],
            ekumen_data['name'],
            ekumen_data['company_type'],
            ekumen_data['email'],
            ekumen_data['created_at'],
            ekumen_data['updated_at']
        ))
        
        # Create L'Oreal user
        loreal_user_id = str(uuid.uuid4()).replace('-', '')
        cursor.execute("""
            INSERT INTO users (id, email, hashed_password, full_name, role, is_active, company_id, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            loreal_user_id,
            'buyer@loreal.com',
            '$2b$12$test_password_hash',  # Test password hash
            'L\'Oreal Buyer',
            'buyer',
            True,
            loreal_id,
            datetime.now().isoformat(),
            datetime.now().isoformat()
        ))
        
        # Create Ekumen user
        ekumen_user_id = str(uuid.uuid4()).replace('-', '')
        cursor.execute("""
            INSERT INTO users (id, email, hashed_password, full_name, role, is_active, company_id, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            ekumen_user_id,
            'seller@ekumen.com',
            '$2b$12$test_password_hash',  # Test password hash
            'Ekumen Seller',
            'seller',
            True,
            ekumen_id,
            datetime.now().isoformat(),
            datetime.now().isoformat()
        ))
        
        # Get or create a product for the purchase order
        cursor.execute("SELECT id FROM products LIMIT 1")
        product_result = cursor.fetchone()
        
        if product_result:
            product_id = product_result[0]
        else:
            # Create a sample product
            product_id = str(uuid.uuid4()).replace('-', '')
            cursor.execute("""
                INSERT INTO products (id, common_product_id, name, description, category, default_unit, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                product_id,
                'palm_oil_crude',
                'Crude Palm Oil',
                'Crude palm oil for cosmetic applications',
                'raw_material',
                'KGM',
                datetime.now().isoformat(),
                datetime.now().isoformat()
            ))
        
        # Create sample purchase orders between L'Oreal and Ekumen
        for i in range(3):
            po_id = str(uuid.uuid4()).replace('-', '')
            po_number = f'PO-LOREAL-{i+1:03d}'
            quantity = 1000.0 + (i * 500)
            unit_price = 2.50 + (i * 0.25)
            total_amount = quantity * unit_price

            cursor.execute("""
                INSERT INTO purchase_orders (
                    id, po_number, buyer_company_id, seller_company_id, product_id,
                    quantity, unit_price, total_amount, unit, status, delivery_date,
                    delivery_location, created_at, updated_at,
                    transparency_to_mill, transparency_to_plantation
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                po_id,
                po_number,
                loreal_id,
                ekumen_id,
                product_id,
                quantity,
                unit_price,
                total_amount,
                'KGM',
                'confirmed',
                (date.today().replace(day=1) if i == 0 else date.today()).isoformat(),
                'L\'Oreal Manufacturing Facility',
                datetime.now().isoformat(),
                datetime.now().isoformat(),
                0.8 + (i * 0.05),  # Varying transparency scores
                0.7 + (i * 0.1)
            ))
        
        # Commit all changes
        conn.commit()
        
        print("Successfully created L'Oreal and Ekumen companies with sample data:")
        print(f"L'Oreal ID: {loreal_id}")
        print(f"Ekumen ID: {ekumen_id}")
        print(f"L'Oreal User: buyer@loreal.com")
        print(f"Ekumen User: seller@ekumen.com")
        print("Created 3 sample purchase orders between them")
        
        return loreal_id, ekumen_id
        
    except Exception as e:
        conn.rollback()
        print(f"Error setting up companies: {e}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    setup_companies_and_data()
