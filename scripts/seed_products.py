#!/usr/bin/env python3
"""
Simple script to seed products into the database
"""
import sys
import os
from pathlib import Path

# Add the app directory to the Python path
app_dir = Path(__file__).parent.parent
sys.path.insert(0, str(app_dir))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from uuid import uuid4

# Import models and config
from app.core.config import settings
from app.models.product import Product

def create_sample_products():
    """Create sample products for testing"""
    
    # Create database connection
    engine = create_engine(settings.database_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    db = SessionLocal()
    
    try:
        # Check if products already exist
        existing_count = db.query(Product).count()
        print(f"Found {existing_count} existing products")
        
        if existing_count > 0:
            print("Products already exist, skipping seeding")
            return
        
        # Sample products to create
        sample_products = [
            {
                "common_product_id": "FFB-001",
                "name": "Fresh Fruit Bunches (FFB)",
                "description": "Fresh palm fruit bunches harvested from oil palm trees",
                "category": "raw_material",
                "can_have_composition": False,
                "default_unit": "KGM",
                "hs_code": "1207.10.00"
            },
            {
                "common_product_id": "CPO-001",
                "name": "Crude Palm Oil (CPO)",
                "description": "Unrefined palm oil extracted from fresh fruit bunches",
                "category": "processed",
                "can_have_composition": True,
                "default_unit": "KGM",
                "hs_code": "1511.10.00"
            },
            {
                "common_product_id": "RBD-001",
                "name": "Refined, Bleached & Deodorized Palm Oil",
                "description": "Refined palm oil ready for food applications",
                "category": "finished_good",
                "can_have_composition": True,
                "default_unit": "KGM",
                "hs_code": "1511.90.00"
            },
            {
                "common_product_id": "OLEIN-001",
                "name": "Palm Olein",
                "description": "Liquid fraction of palm oil after fractionation",
                "category": "finished_good",
                "can_have_composition": True,
                "default_unit": "KGM",
                "hs_code": "1511.90.00"
            },
            {
                "common_product_id": "STEARIN-001",
                "name": "Palm Stearin",
                "description": "Solid fraction of palm oil after fractionation",
                "category": "finished_good",
                "can_have_composition": True,
                "default_unit": "KGM",
                "hs_code": "1511.90.00"
            },
            {
                "common_product_id": "COTTON-001",
                "name": "Organic Cotton",
                "description": "Certified organic cotton fiber",
                "category": "raw_material",
                "can_have_composition": False,
                "default_unit": "KGM",
                "hs_code": "5201.00.00"
            },
            {
                "common_product_id": "POLYESTER-001",
                "name": "Recycled Polyester",
                "description": "Polyester fiber made from recycled materials",
                "category": "processed",
                "can_have_composition": True,
                "default_unit": "KGM",
                "hs_code": "5503.20.00"
            },
            {
                "common_product_id": "HEMP-001",
                "name": "Hemp Fiber",
                "description": "Natural hemp fiber for textile applications",
                "category": "raw_material",
                "can_have_composition": False,
                "default_unit": "KGM",
                "hs_code": "5302.10.00"
            }
        ]
        
        # Create products
        created_count = 0
        for product_data in sample_products:
            try:
                product = Product(
                    id=uuid4(),
                    **product_data
                )
                db.add(product)
                created_count += 1
                print(f"Created product: {product_data['name']}")
            except Exception as e:
                print(f"Error creating product {product_data['name']}: {e}")
        
        # Commit all products
        db.commit()
        print(f"\n✅ Successfully created {created_count} products!")
        
        # Verify creation
        final_count = db.query(Product).count()
        print(f"Total products in database: {final_count}")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error seeding products: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    print("🌱 Seeding sample products...")
    create_sample_products()
    print("✨ Done!")
