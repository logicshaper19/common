#!/usr/bin/env python3
"""
Create L'Oréal Supply Chain Flow - Direct Database Approach
==========================================================

This script creates a comprehensive supply chain for L'Oréal by directly
inserting data into the database, bypassing API authentication issues.
"""

import os
import sys
import uuid
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.core.database import get_db
from app.models.company import Company
from app.models.user import User
from app.models.brand import Brand
from app.models.product import Product
from app.models.purchase_order import PurchaseOrder
from app.core.security import hash_password
from app.core.logging import get_logger

logger = get_logger(__name__)

class LOréalSupplyChainCreator:
    """Creates the complete L'Oréal supply chain hierarchy directly in the database."""
    
    def __init__(self):
        self.created_data = {
            'companies': {},
            'users': {},
            'brands': {},
            'products': {},
            'purchase_orders': {}
        }
        self.credentials = {}
        
    def create_supply_chain(self):
        """Create the complete supply chain."""
        print("🏭 Creating L'Oréal Supply Chain...")
        print("=" * 60)
        
        # Get database session
        db = next(get_db())
        
        try:
            # 1. Create L'Oréal brand and company
            self._create_loreal_brand(db)
            
            # 2. Create Tier 1 suppliers (Manufacturers)
            self._create_tier1_suppliers(db)
            
            # 3. Create Tier 2 suppliers (Component suppliers)
            self._create_tier2_suppliers(db)
            
            # 4. Create Tier 3 suppliers (Raw material suppliers)
            self._create_tier3_suppliers(db)
            
            # 5. Create Originators (Farmers/Extractors)
            self._create_originators(db)
            
            # 6. Create users for all companies
            self._create_all_users(db)
            
            # 7. Create products
            self._create_products(db)
            
            # 8. Create a test purchase order chain
            self._create_test_purchase_order_chain(db)
            
            # 9. Save credentials to file
            self._save_credentials()
            
            db.commit()
            print("\n✅ L'Oréal Supply Chain created successfully!")
            
        except Exception as e:
            db.rollback()
            print(f"❌ Error creating supply chain: {e}")
            raise
        finally:
            db.close()
    
    def _create_loreal_brand(self, db):
        """Create L'Oréal brand and company."""
        print("🏢 Creating L'Oréal brand...")
        
        # Create L'Oréal company
        loreal_company = Company(
            id=uuid.uuid4(),
            name="L'Oréal Group",
            company_type="brand",
            email="contact@loreal.com",
            phone="+33-1-47-56-70-00",
            website="https://www.loreal.com",
            country="France",
            industry_sector="Consumer Staples",
            industry_subcategory="Personal Care & Cosmetics",
            address_street="14 Rue Royale",
            address_city="Paris",
            address_state="Île-de-France",
            address_postal_code="75008",
            address_country="France",
            subscription_tier="enterprise",
            compliance_status="compliant",
            is_active=True,
            is_verified=True,
            transparency_score=95,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.add(loreal_company)
        db.flush()
        db.refresh(loreal_company)
        
        # Create L'Oréal brand
        loreal_brand = Brand(
            id=uuid.uuid4(),
            name="L'Oréal",
            company_id=loreal_company.id,
            description="Global leader in beauty and cosmetics",
            website="https://www.loreal.com",
            logo_url="https://www.loreal.com/logo.png",
            is_active=True
        )
        
        db.add(loreal_brand)
        db.flush()
        db.refresh(loreal_brand)
        
        self.created_data['companies']['loreal'] = {
            'id': str(loreal_company.id),
            'name': loreal_company.name,
            'type': 'brand'
        }
        
        self.created_data['brands']['loreal'] = {
            'id': str(loreal_brand.id),
            'name': loreal_brand.name
        }
        
        print(f"✅ Created L'Oréal: {loreal_company.name}")
    
    def _create_tier1_suppliers(self, db):
        """Create Tier 1 suppliers (Manufacturers)."""
        print("🏭 Creating Tier 1 Suppliers (Manufacturers)...")
        
        tier1_suppliers = [
            {
                'name': 'Cosmetic Manufacturing Solutions',
                'email': 'contact@cosmeticsolutions.com',
                'country': 'Germany',
                'city': 'Hamburg',
                'specialty': 'Premium cosmetics manufacturing'
            },
            {
                'name': 'Beauty Production International',
                'email': 'info@beautyprod.com',
                'country': 'Italy',
                'city': 'Milan',
                'specialty': 'Luxury beauty products'
            },
            {
                'name': 'Global Cosmetics Ltd',
                'email': 'hello@globalcosmetics.com',
                'country': 'United Kingdom',
                'city': 'London',
                'specialty': 'Mass market cosmetics'
            }
        ]
        
        for i, supplier_data in enumerate(tier1_suppliers, 1):
            company = Company(
                id=uuid.uuid4(),
                name=supplier_data['name'],
                company_type="processor",
                email=supplier_data['email'],
                phone=f"+49-40-{1234567 + i}",
                website=f"https://www.{supplier_data['email'].split('@')[1]}",
                country=supplier_data['country'],
                industry_sector="Consumer Staples",
                industry_subcategory="Personal Care & Cosmetics",
                address_city=supplier_data['city'],
                address_country=supplier_data['country'],
                subscription_tier="professional",
                compliance_status="compliant",
                is_active=True,
                is_verified=True,
                transparency_score=90,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            db.add(company)
            db.flush()
            db.refresh(company)
            
            self.created_data['companies'][f'tier1_{i}'] = {
                'id': str(company.id),
                'name': company.name,
                'type': 'processor',
                'tier': 1,
                'parent': 'loreal'
            }
            
            print(f"✅ Created Tier 1 Supplier {i}: {company.name}")
    
    def _create_tier2_suppliers(self, db):
        """Create Tier 2 suppliers (Component suppliers)."""
        print("🔧 Creating Tier 2 Suppliers (Component suppliers)...")
        
        tier2_suppliers = [
            # For Tier 1 Supplier 1
            {'name': 'Premium Packaging Solutions', 'email': 'contact@premiumpack.com', 'country': 'Germany', 'city': 'Munich', 'specialty': 'Luxury packaging'},
            {'name': 'Chemical Components Ltd', 'email': 'info@chemcomp.com', 'country': 'Germany', 'city': 'Frankfurt', 'specialty': 'Cosmetic chemicals'},
            {'name': 'Fragrance Ingredients Co', 'email': 'hello@fragranceing.com', 'country': 'France', 'city': 'Grasse', 'specialty': 'Perfume ingredients'},
            
            # For Tier 1 Supplier 2
            {'name': 'Italian Glass Works', 'email': 'contact@italianglass.com', 'country': 'Italy', 'city': 'Venice', 'specialty': 'Glass containers'},
            {'name': 'Mediterranean Oils', 'email': 'info@medoils.com', 'country': 'Italy', 'city': 'Naples', 'specialty': 'Natural oils'},
            {'name': 'Alpine Minerals', 'email': 'hello@alpineminerals.com', 'country': 'Switzerland', 'city': 'Zurich', 'specialty': 'Mineral ingredients'},
            
            # For Tier 1 Supplier 3
            {'name': 'British Textiles', 'email': 'contact@britishtextiles.com', 'country': 'United Kingdom', 'city': 'Manchester', 'specialty': 'Cosmetic applicators'},
            {'name': 'Celtic Herbs', 'email': 'info@celticherbs.com', 'country': 'Ireland', 'city': 'Dublin', 'specialty': 'Herbal extracts'},
            {'name': 'Nordic Seaweed', 'email': 'hello@nordicseaweed.com', 'country': 'Norway', 'city': 'Oslo', 'specialty': 'Seaweed extracts'}
        ]
        
        for i, supplier_data in enumerate(tier2_suppliers, 1):
            company = Company(
                id=uuid.uuid4(),
                name=supplier_data['name'],
                company_type="processor",
                email=supplier_data['email'],
                phone=f"+49-{89 + i}-{1234567 + i}",
                website=f"https://www.{supplier_data['email'].split('@')[1]}",
                country=supplier_data['country'],
                industry_sector="Consumer Staples",
                industry_subcategory="Personal Care & Cosmetics",
                address_city=supplier_data['city'],
                address_country=supplier_data['country'],
                subscription_tier="basic",
                compliance_status="compliant",
                is_active=True,
                is_verified=True,
                transparency_score=85,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            db.add(company)
            db.flush()
            db.refresh(company)
            
            # Determine parent tier1 supplier
            parent_tier1 = ((i - 1) // 3) + 1
            
            self.created_data['companies'][f'tier2_{i}'] = {
                'id': str(company.id),
                'name': company.name,
                'type': 'processor',
                'tier': 2,
                'parent': f'tier1_{parent_tier1}'
            }
            
            print(f"✅ Created Tier 2 Supplier {i}: {company.name}")
    
    def _create_tier3_suppliers(self, db):
        """Create Tier 3 suppliers (Raw material suppliers)."""
        print("🌿 Creating Tier 3 Suppliers (Raw material suppliers)...")
        
        # Create 3 suppliers for each tier2 supplier
        for tier2_idx in range(1, 10):  # 9 tier2 suppliers
            for sub_idx in range(1, 4):  # 3 suppliers per tier2
                supplier_num = (tier2_idx - 1) * 3 + sub_idx
                
                # Create diverse supplier types
                supplier_types = [
                    {'name': f'Raw Materials Co {supplier_num}', 'specialty': 'Base ingredients', 'country': 'Spain'},
                    {'name': f'Natural Extracts Ltd {supplier_num}', 'specialty': 'Plant extracts', 'country': 'Portugal'},
                    {'name': f'Chemical Suppliers {supplier_num}', 'specialty': 'Synthetic ingredients', 'country': 'Netherlands'}
                ]
                
                supplier_data = supplier_types[sub_idx - 1]
                
                company = Company(
                    id=uuid.uuid4(),
                    name=supplier_data['name'],
                    company_type="processor",
                    email=f"contact@{supplier_data['name'].lower().replace(' ', '').replace('ltd', '').replace('co', '')}.com",
                    phone=f"+34-{91 + supplier_num}-{1234567 + supplier_num}",
                    website=f"https://www.{supplier_data['name'].lower().replace(' ', '').replace('ltd', '').replace('co', '')}.com",
                    country=supplier_data['country'],
                    industry_sector="Consumer Staples",
                    industry_subcategory="Personal Care & Cosmetics",
                    address_city=f"City{supplier_num}",
                    address_country=supplier_data['country'],
                    subscription_tier="basic",
                    compliance_status="compliant",
                    is_active=True,
                    is_verified=True,
                    transparency_score=80,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                
                db.add(company)
                db.flush()
                db.refresh(company)
                
                self.created_data['companies'][f'tier3_{supplier_num}'] = {
                    'id': str(company.id),
                    'name': company.name,
                    'type': 'processor',
                    'tier': 3,
                    'parent': f'tier2_{tier2_idx}'
                }
                
                if supplier_num % 9 == 0:  # Print every 9th to avoid spam
                    print(f"✅ Created Tier 3 Suppliers {supplier_num-8}-{supplier_num}")
    
    def _create_originators(self, db):
        """Create Originators (Farmers/Extractors)."""
        print("🌱 Creating Originators (Farmers/Extractors)...")
        
        originator_types = [
            {'name': 'Organic Farms', 'specialty': 'Organic ingredients', 'country': 'Morocco'},
            {'name': 'Sustainable Harvest', 'specialty': 'Sustainable farming', 'country': 'Tunisia'},
            {'name': 'Natural Extracts', 'specialty': 'Plant extraction', 'country': 'Algeria'}
        ]
        
        for tier3_idx in range(1, 28):  # 27 tier3 suppliers
            for sub_idx in range(1, 4):  # 3 originators per tier3
                originator_num = (tier3_idx - 1) * 3 + sub_idx
                originator_data = originator_types[sub_idx - 1]
                
                company = Company(
                    id=uuid.uuid4(),
                    name=f"{originator_data['name']} {originator_num}",
                    company_type="originator",
                    email=f"contact@{originator_data['name'].lower().replace(' ', '')}{originator_num}.com",
                    phone=f"+212-{5 + (originator_num % 10)}-{1234567 + originator_num}",
                    website=f"https://www.{originator_data['name'].lower().replace(' ', '')}{originator_num}.com",
                    country=originator_data['country'],
                    industry_sector="Consumer Staples",
                    industry_subcategory="Personal Care & Cosmetics",
                    address_city=f"Farm{originator_num}",
                    address_country=originator_data['country'],
                    subscription_tier="free",
                    compliance_status="compliant",
                    is_active=True,
                    is_verified=True,
                    transparency_score=75,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                
                db.add(company)
                db.flush()
                db.refresh(company)
                
                self.created_data['companies'][f'originator_{originator_num}'] = {
                    'id': str(company.id),
                    'name': company.name,
                    'type': 'originator',
                    'tier': 4,
                    'parent': f'tier3_{tier3_idx}'
                }
        
        print("✅ Created 81 Originators")
    
    def _create_all_users(self, db):
        """Create users for all companies."""
        print("👥 Creating users for all companies...")
        
        for company_key, company_data in self.created_data['companies'].items():
            # Create admin user
            admin_user = User(
                id=uuid.uuid4(),
                email=f"admin@{company_data['name'].lower().replace(' ', '').replace('group', '').replace('ltd', '').replace('co', '')}.com",
                hashed_password=hash_password("password123"),
                full_name=f"Admin {company_data['name']}",
                role="admin",
                is_active=True,
                company_id=uuid.UUID(company_data['id']),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            db.add(admin_user)
            db.flush()
            db.refresh(admin_user)
            
            # Create role-specific user
            if company_data['type'] == "brand":
                role_user = User(
                    id=uuid.uuid4(),
                    email=f"buyer@{company_data['name'].lower().replace(' ', '').replace('group', '').replace('ltd', '').replace('co', '')}.com",
                    hashed_password=hash_password("password123"),
                    full_name=f"Buyer {company_data['name']}",
                    role="buyer",
                    is_active=True,
                    company_id=uuid.UUID(company_data['id']),
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
            elif company_data['type'] == "originator":
                role_user = User(
                    id=uuid.uuid4(),
                    email=f"seller@{company_data['name'].lower().replace(' ', '').replace('group', '').replace('ltd', '').replace('co', '')}.com",
                    hashed_password=hash_password("password123"),
                    full_name=f"Seller {company_data['name']}",
                    role="seller",
                    is_active=True,
                    company_id=uuid.UUID(company_data['id']),
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
            else:  # processor
                role_user = User(
                    id=uuid.uuid4(),
                    email=f"manager@{company_data['name'].lower().replace(' ', '').replace('group', '').replace('ltd', '').replace('co', '')}.com",
                    hashed_password=hash_password("password123"),
                    full_name=f"Manager {company_data['name']}",
                    role="seller",
                    is_active=True,
                    company_id=uuid.UUID(company_data['id']),
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
            
            db.add(role_user)
            db.flush()
            db.refresh(role_user)
            
            # Store credentials
            self.credentials[company_key] = {
                'company_name': company_data['name'],
                'company_type': company_data['type'],
                'admin_user': {
                    'email': admin_user.email,
                    'password': 'password123',
                    'role': 'admin'
                },
                'role_user': {
                    'email': role_user.email,
                    'password': 'password123',
                    'role': role_user.role
                }
            }
        
        print(f"✅ Created users for {len(self.credentials)} companies")
    
    def _create_products(self, db):
        """Create sample products."""
        print("📦 Creating products...")
        
        products_data = [
            {
                'name': 'Premium Face Cream',
                'description': 'Anti-aging face cream with natural ingredients',
                'category': 'Skincare',
                'unit': 'pieces',
                'unit_price': 45.00
            },
            {
                'name': 'Luxury Shampoo',
                'description': 'Premium hair care shampoo',
                'category': 'Hair Care',
                'unit': 'bottles',
                'unit_price': 25.00
            },
            {
                'name': 'Natural Lipstick',
                'description': 'Organic lipstick with natural pigments',
                'category': 'Makeup',
                'unit': 'pieces',
                'unit_price': 18.00
            }
        ]
        
        for i, product_data in enumerate(products_data, 1):
            product = Product(
                id=uuid.uuid4(),
                name=product_data['name'],
                description=product_data['description'],
                category=product_data['category'],
                unit=product_data['unit'],
                unit_price=product_data['unit_price'],
                is_active=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            db.add(product)
            db.flush()
            db.refresh(product)
            
            self.created_data['products'][f'product_{i}'] = {
                'id': str(product.id),
                'name': product.name,
                'unit_price': product.unit_price
            }
            
            print(f"✅ Created product: {product.name}")
    
    def _create_test_purchase_order_chain(self, db):
        """Create a test purchase order chain from brand to originator."""
        print("📋 Creating test purchase order chain...")
        
        # Get the product
        product = db.query(Product).first()
        if not product:
            print("❌ No products found")
            return
        
        # Create PO chain: L'Oréal -> Tier1 -> Tier2 -> Tier3 -> Originator
        loreal_id = uuid.UUID(self.created_data['companies']['loreal']['id'])
        tier1_id = uuid.UUID(self.created_data['companies']['tier1_1']['id'])
        tier2_id = uuid.UUID(self.created_data['companies']['tier2_1']['id'])
        tier3_id = uuid.UUID(self.created_data['companies']['tier3_1']['id'])
        originator_id = uuid.UUID(self.created_data['companies']['originator_1']['id'])
        
        # PO 1: L'Oréal -> Tier 1
        po1 = PurchaseOrder(
            id=uuid.uuid4(),
            po_number=f"PO-LOREAL-{datetime.now().strftime('%Y%m%d')}-001",
            buyer_company_id=loreal_id,
            seller_company_id=tier1_id,
            product_id=product.id,
            quantity=1000,
            unit_price=35.00,
            total_amount=35000.00,
            unit="pieces",
            delivery_date=datetime.utcnow() + timedelta(days=30),
            delivery_location="L'Oréal Distribution Center, Paris",
            notes="Premium face cream order",
            status="confirmed",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.add(po1)
        db.flush()
        db.refresh(po1)
        
        # PO 2: Tier 1 -> Tier 2
        po2 = PurchaseOrder(
            id=uuid.uuid4(),
            po_number=f"PO-TIER1-{datetime.now().strftime('%Y%m%d')}-001",
            buyer_company_id=tier1_id,
            seller_company_id=tier2_id,
            product_id=product.id,
            quantity=1000,
            unit_price=25.00,
            total_amount=25000.00,
            unit="pieces",
            delivery_date=datetime.utcnow() + timedelta(days=25),
            delivery_location="Cosmetic Manufacturing Solutions, Hamburg",
            notes="Component supply for face cream",
            status="confirmed",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.add(po2)
        db.flush()
        db.refresh(po2)
        
        # PO 3: Tier 2 -> Tier 3
        po3 = PurchaseOrder(
            id=uuid.uuid4(),
            po_number=f"PO-TIER2-{datetime.now().strftime('%Y%m%d')}-001",
            buyer_company_id=tier2_id,
            seller_company_id=tier3_id,
            product_id=product.id,
            quantity=1000,
            unit_price=15.00,
            total_amount=15000.00,
            unit="pieces",
            delivery_date=datetime.utcnow() + timedelta(days=20),
            delivery_location="Premium Packaging Solutions, Munich",
            notes="Raw materials for components",
            status="confirmed",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.add(po3)
        db.flush()
        db.refresh(po3)
        
        # PO 4: Tier 3 -> Originator
        po4 = PurchaseOrder(
            id=uuid.uuid4(),
            po_number=f"PO-TIER3-{datetime.now().strftime('%Y%m%d')}-001",
            buyer_company_id=tier3_id,
            seller_company_id=originator_id,
            product_id=product.id,
            quantity=1000,
            unit_price=8.00,
            total_amount=8000.00,
            unit="pieces",
            delivery_date=datetime.utcnow() + timedelta(days=15),
            delivery_location="Raw Materials Co 1, Spain",
            notes="Natural ingredients for raw materials",
            status="confirmed",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.add(po4)
        db.flush()
        db.refresh(po4)
        
        self.created_data['purchase_orders'] = {
            'po1': {'id': str(po1.id), 'from': 'L\'Oréal', 'to': 'Tier 1'},
            'po2': {'id': str(po2.id), 'from': 'Tier 1', 'to': 'Tier 2'},
            'po3': {'id': str(po3.id), 'from': 'Tier 2', 'to': 'Tier 3'},
            'po4': {'id': str(po4.id), 'from': 'Tier 3', 'to': 'Originator'}
        }
        
        print("✅ Created 4-level purchase order chain")
    
    def _save_credentials(self):
        """Save credentials to a file."""
        print("💾 Saving credentials...")
        
        credentials_file = "loreal_supply_chain_credentials.json"
        
        with open(credentials_file, 'w') as f:
            json.dump(self.credentials, f, indent=2)
        
        print(f"✅ Credentials saved to {credentials_file}")
        
        # Also create a summary file
        summary_file = "loreal_supply_chain_summary.md"
        
        with open(summary_file, 'w') as f:
            f.write("# L'Oréal Supply Chain - Test Credentials\n\n")
            f.write("## Overview\n")
            f.write(f"- **Total Companies**: {len(self.credentials)}\n")
            f.write(f"- **Brand**: 1 (L'Oréal)\n")
            f.write(f"- **Tier 1 Suppliers**: 3 (Manufacturers)\n")
            f.write(f"- **Tier 2 Suppliers**: 9 (Component suppliers)\n")
            f.write(f"- **Tier 3 Suppliers**: 27 (Raw material suppliers)\n")
            f.write(f"- **Originators**: 81 (Farmers/Extractors)\n\n")
            
            f.write("## Test Credentials\n\n")
            f.write("All users have the password: `password123`\n\n")
            
            f.write("### Key Test Accounts\n\n")
            
            # L'Oréal
            if 'loreal' in self.credentials:
                loreal_creds = self.credentials['loreal']
                f.write(f"#### L'Oréal (Brand)\n")
                f.write(f"- **Admin**: {loreal_creds['admin_user']['email']}\n")
                f.write(f"- **Buyer**: {loreal_creds['role_user']['email']}\n\n")
            
            # Sample from each tier
            for tier in [1, 2, 3]:
                if tier == 1:
                    key = 'tier1_1'
                    tier_name = 'Tier 1 (Manufacturer)'
                elif tier == 2:
                    key = 'tier2_1'
                    tier_name = 'Tier 2 (Component Supplier)'
                else:
                    key = 'tier3_1'
                    tier_name = 'Tier 3 (Raw Material Supplier)'
                
                if key in self.credentials:
                    creds = self.credentials[key]
                    f.write(f"#### {tier_name}\n")
                    f.write(f"- **Company**: {creds['company_name']}\n")
                    f.write(f"- **Admin**: {creds['admin_user']['email']}\n")
                    f.write(f"- **Manager**: {creds['role_user']['email']}\n\n")
            
            # Originator
            if 'originator_1' in self.credentials:
                originator_creds = self.credentials['originator_1']
                f.write(f"#### Originator (Farmer/Extractor)\n")
                f.write(f"- **Company**: {originator_creds['company_name']}\n")
                f.write(f"- **Admin**: {originator_creds['admin_user']['email']}\n")
                f.write(f"- **Seller**: {originator_creds['role_user']['email']}\n\n")
            
            f.write("## Purchase Order Chain\n\n")
            f.write("A complete 4-level purchase order chain has been created:\n")
            f.write("1. L'Oréal → Tier 1 Supplier (Manufacturer)\n")
            f.write("2. Tier 1 → Tier 2 Supplier (Component supplier)\n")
            f.write("3. Tier 2 → Tier 3 Supplier (Raw material supplier)\n")
            f.write("4. Tier 3 → Originator (Farmer/Extractor)\n\n")
            
            f.write("## Testing Instructions\n\n")
            f.write("1. Use the credentials above to log into the system\n")
            f.write("2. Test different user roles and permissions\n")
            f.write("3. Verify purchase order visibility and traceability\n")
            f.write("4. Test the supply chain transparency features\n\n")
            
            f.write("## API Endpoints for Testing\n\n")
            f.write("- **Login**: `POST /api/v1/auth/login`\n")
            f.write("- **Purchase Orders**: `GET /api/v1/simple/purchase-orders`\n")
            f.write("- **Relationships**: `GET /api/v1/simple/relationships/suppliers`\n")
            f.write("- **Traceability**: `GET /api/v1/traceability`\n")
        
        print(f"✅ Summary saved to {summary_file}")


def main():
    """Main function."""
    print("🏭 L'Oréal Supply Chain Creator")
    print("=" * 60)
    
    creator = LOréalSupplyChainCreator()
    creator.create_supply_chain()
    
    print("\n🎉 Supply chain creation completed!")
    print("Check the generated files for credentials and summary.")


if __name__ == "__main__":
    main()
