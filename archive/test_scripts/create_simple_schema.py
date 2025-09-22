#!/usr/bin/env python3
"""
Simple Schema Creator
====================

Creates a minimal database schema for testing the supply chain flow.
"""

import psycopg2
from datetime import datetime

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'port': '5432',
    'database': 'common_db',
    'user': 'common_user',
    'password': 'common_password'
}

def create_schema():
    """Create a simple database schema."""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        conn.autocommit = True
        cursor = conn.cursor()
        
        print("🗄️  Creating simple database schema...")
        
        # Create companies table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS companies (
                id UUID PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                company_type VARCHAR(100) NOT NULL,
                email VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("✅ Created companies table")
        
        # Create users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id UUID PRIMARY KEY,
                email VARCHAR(255) UNIQUE NOT NULL,
                full_name VARCHAR(255),
                role VARCHAR(50) DEFAULT 'user',
                company_id UUID REFERENCES companies(id),
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("✅ Created users table")
        
        # Create products table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id UUID PRIMARY KEY,
                common_product_id VARCHAR(255) UNIQUE NOT NULL,
                name VARCHAR(255) NOT NULL,
                description TEXT,
                category VARCHAR(100),
                can_have_composition BOOLEAN DEFAULT FALSE,
                default_unit VARCHAR(50) DEFAULT 'kg',
                company_id UUID REFERENCES companies(id),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("✅ Created products table")
        
        # Create purchase_orders table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS purchase_orders (
                id UUID PRIMARY KEY,
                po_number VARCHAR(255) UNIQUE NOT NULL,
                buyer_company_id UUID REFERENCES companies(id),
                seller_company_id UUID REFERENCES companies(id),
                product_id UUID REFERENCES products(id),
                quantity DECIMAL(15,2) NOT NULL,
                unit_price DECIMAL(15,2) NOT NULL,
                unit VARCHAR(50) DEFAULT 'kg',
                delivery_date DATE,
                delivery_location VARCHAR(255),
                notes TEXT,
                status VARCHAR(50) DEFAULT 'pending',
                parent_po_id UUID REFERENCES purchase_orders(id),
                is_drop_shipment BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("✅ Created purchase_orders table")
        
        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_companies_type ON companies(company_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_company ON users(company_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_products_company ON products(company_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_po_buyer ON purchase_orders(buyer_company_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_po_seller ON purchase_orders(seller_company_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_po_parent ON purchase_orders(parent_po_id)")
        print("✅ Created indexes")
        
        cursor.close()
        conn.close()
        
        print("\n🎉 Simple database schema created successfully!")
        print("Tables created:")
        print("  - companies")
        print("  - users")
        print("  - products")
        print("  - purchase_orders")
        
        return True
        
    except Exception as e:
        print(f"❌ Schema creation failed: {e}")
        return False

if __name__ == "__main__":
    success = create_schema()
    exit(0 if success else 1)
