#!/usr/bin/env python3
"""
Script to create purchase orders between existing L'Oreal and Ekumen companies.
"""
import os
import uuid
from datetime import datetime, date
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

def create_purchase_orders():
    """Create purchase orders between L'Oreal and Ekumen."""
    
    # Get database URL from environment or use default PostgreSQL
    database_url = os.getenv('DATABASE_URL', 'postgresql://common_user:common_password@localhost:5432/common_db')
    
    # Create database engine and session
    engine = create_engine(database_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    
    try:
        # Get L'Oreal company ID
        result = session.execute(text("SELECT id FROM companies WHERE email = 'contact@loreal.com'")).fetchone()
        if not result:
            print("L'Oreal company not found!")
            return
        loreal_id = str(result[0])
        print(f"Found L'Oreal company ID: {loreal_id}")
        
        # Get Ekumen company ID (use the first one we find)
        result = session.execute(text("SELECT id FROM companies WHERE name ILIKE '%ekumen%' LIMIT 1")).fetchone()
        if not result:
            print("Ekumen company not found!")
            return
        ekumen_id = str(result[0])
        print(f"Found Ekumen company ID: {ekumen_id}")

        # Get a product ID (use Crude Palm Oil)
        result = session.execute(text("SELECT id FROM products WHERE name = 'Crude Palm Oil (CPO)' LIMIT 1")).fetchone()
        if not result:
            print("Product not found!")
            return
        product_id = str(result[0])
        print(f"Found product ID: {product_id}")
        
        # Create sample purchase orders
        purchase_orders = [
            {
                'id': str(uuid.uuid4()),
                'po_number': 'PO-LOREAL-001',
                'buyer_company_id': loreal_id,
                'seller_company_id': ekumen_id,
                'product_id': product_id,
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
                'product_id': product_id,
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
                'product_id': product_id,
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
                        id, po_number, buyer_company_id, seller_company_id, product_id, status,
                        quantity, unit_price, total_amount, unit, delivery_date, delivery_location,
                        transparency_to_mill, transparency_to_plantation, transparency_calculated_at,
                        created_at, updated_at
                    ) VALUES (
                        :id, :po_number, :buyer_company_id, :seller_company_id, :product_id, :status,
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
        print("\nPurchase orders created successfully!")
        print(f"L'Oreal company ID: {loreal_id}")
        print(f"Ekumen company ID: {ekumen_id}")
        
    except Exception as e:
        session.rollback()
        print(f"Error creating purchase orders: {e}")
        raise
    finally:
        session.close()

if __name__ == "__main__":
    create_purchase_orders()
