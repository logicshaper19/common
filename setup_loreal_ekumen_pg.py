#!/usr/bin/env python3
"""
Script to set up L'Oreal and Ekumen companies with sample data for transparency testing in PostgreSQL.
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
        loreal_id = str(uuid.uuid4())
        
        # Check if L'Oreal already exists
        result = session.execute(text("SELECT id FROM companies WHERE name = 'L''Oreal'")).fetchone()
        if result:
            loreal_id = str(result[0])
            print(f"L'Oreal company already exists with ID: {loreal_id}")
        else:
            session.execute(text('''
                INSERT INTO companies (id, name, company_type, email, created_at, updated_at)
                VALUES (:id, :name, :company_type, :email, :created_at, :updated_at)
            '''), {
                'id': loreal_id,
                'name': 'L\'Oreal',
                'company_type': 'manufacturer',
                'email': 'contact@loreal.com',
                'created_at': datetime.now(),
                'updated_at': datetime.now()
            })
            print(f"Created L'Oreal company with ID: {loreal_id}")
        
        # Create Ekumen company (supplier)
        ekumen_id = str(uuid.uuid4())
        
        # Check if Ekumen already exists
        result = session.execute(text("SELECT id FROM companies WHERE name = 'Ekumen'")).fetchone()
        if result:
            ekumen_id = str(result[0])
            print(f"Ekumen company already exists with ID: {ekumen_id}")
        else:
            session.execute(text('''
                INSERT INTO companies (id, name, company_type, email, created_at, updated_at)
                VALUES (:id, :name, :company_type, :email, :created_at, :updated_at)
            '''), {
                'id': ekumen_id,
                'name': 'Ekumen',
                'company_type': 'plantation_grower',
                'email': 'contact@ekumen.com',
                'created_at': datetime.now(),
                'updated_at': datetime.now()
            })
            print(f"Created Ekumen company with ID: {ekumen_id}")
        
        # Create users for both companies
        # L'Oreal user
        loreal_user_id = str(uuid.uuid4())
        result = session.execute(text("SELECT id FROM users WHERE email = 'buyer@loreal.com'")).fetchone()
        if not result:
            session.execute(text('''
                INSERT INTO users (id, email, hashed_password, full_name, role, company_id, is_active, created_at, updated_at)
                VALUES (:id, :email, :hashed_password, :full_name, :role, :company_id, :is_active, :created_at, :updated_at)
            '''), {
                'id': loreal_user_id,
                'email': 'buyer@loreal.com',
                'hashed_password': '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj9/4L5VSM7S',  # password123
                'full_name': 'L\'Oreal Buyer',
                'role': 'buyer',
                'company_id': loreal_id,
                'is_active': True,
                'created_at': datetime.now(),
                'updated_at': datetime.now()
            })
            print(f"Created L'Oreal user with ID: {loreal_user_id}")
        
        # Ekumen user
        ekumen_user_id = str(uuid.uuid4())
        result = session.execute(text("SELECT id FROM users WHERE email = 'seller@ekumen.com'")).fetchone()
        if not result:
            session.execute(text('''
                INSERT INTO users (id, email, hashed_password, full_name, role, company_id, is_active, created_at, updated_at)
                VALUES (:id, :email, :hashed_password, :full_name, :role, :company_id, :is_active, :created_at, :updated_at)
            '''), {
                'id': ekumen_user_id,
                'email': 'seller@ekumen.com',
                'hashed_password': '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj9/4L5VSM7S',  # password123
                'full_name': 'Ekumen Seller',
                'role': 'seller',
                'company_id': ekumen_id,
                'is_active': True,
                'created_at': datetime.now(),
                'updated_at': datetime.now()
            })
            print(f"Created Ekumen user with ID: {ekumen_user_id}")
        
        # Create sample purchase orders
        purchase_orders = [
            {
                'id': str(uuid.uuid4()),
                'po_number': 'PO-LOREAL-001',
                'buyer_company_id': loreal_id,
                'seller_company_id': ekumen_id,
                'status': 'confirmed',
                'quantity': 1000,
                'unit_price': 25.50,
                'total_amount': 25500.00,
                'unit': 'kg',
                'delivery_date': date(2024, 12, 15),
                'delivery_location': 'Paris, France',
                'transparency_to_mill': 0.8,
                'transparency_to_plantation': 0.7,
                'transparency_calculated_at': datetime.now(),
                'created_at': datetime.now(),
                'updated_at': datetime.now()
            },
            {
                'id': str(uuid.uuid4()),
                'po_number': 'PO-LOREAL-002',
                'buyer_company_id': loreal_id,
                'seller_company_id': ekumen_id,
                'status': 'confirmed',
                'quantity': 1500,
                'unit_price': 28.75,
                'total_amount': 43125.00,
                'unit': 'kg',
                'delivery_date': date(2024, 12, 30),
                'delivery_location': 'Lyon, France',
                'transparency_to_mill': 0.85,
                'transparency_to_plantation': 0.8,
                'transparency_calculated_at': datetime.now(),
                'created_at': datetime.now(),
                'updated_at': datetime.now()
            },
            {
                'id': str(uuid.uuid4()),
                'po_number': 'PO-LOREAL-003',
                'buyer_company_id': loreal_id,
                'seller_company_id': ekumen_id,
                'status': 'pending',
                'quantity': 2000,
                'unit_price': 30.00,
                'total_amount': 60000.00,
                'unit': 'kg',
                'delivery_date': date(2025, 1, 15),
                'delivery_location': 'Marseille, France',
                'transparency_to_mill': 0.9,
                'transparency_to_plantation': 0.9,
                'transparency_calculated_at': datetime.now(),
                'created_at': datetime.now(),
                'updated_at': datetime.now()
            }
        ]
        
        for po in purchase_orders:
            # Check if PO already exists
            result = session.execute(text("SELECT id FROM purchase_orders WHERE po_number = :po_number"), 
                                   {'po_number': po['po_number']}).fetchone()
            if not result:
                session.execute(text('''
                    INSERT INTO purchase_orders (
                        id, po_number, buyer_company_id, seller_company_id, status,
                        quantity, unit_price, total_amount, unit, delivery_date, delivery_location,
                        transparency_to_mill, transparency_to_plantation, transparency_calculated_at,
                        created_at, updated_at
                    ) VALUES (
                        :id, :po_number, :buyer_company_id, :seller_company_id, :status,
                        :quantity, :unit_price, :total_amount, :unit, :delivery_date, :delivery_location,
                        :transparency_to_mill, :transparency_to_plantation, :transparency_calculated_at,
                        :created_at, :updated_at
                    )
                '''), po)
                print(f"Created purchase order: {po['po_number']}")
            else:
                print(f"Purchase order already exists: {po['po_number']}")
        
        # Commit all changes
        session.commit()
        print("\nSetup completed successfully!")
        print(f"L'Oreal company ID: {loreal_id}")
        print(f"Ekumen company ID: {ekumen_id}")
        
    except Exception as e:
        session.rollback()
        print(f"Error setting up companies and data: {e}")
        raise
    finally:
        session.close()

if __name__ == "__main__":
    setup_companies_and_data()
