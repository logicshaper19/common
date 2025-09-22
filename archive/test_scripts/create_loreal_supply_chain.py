#!/usr/bin/env python3
"""
L'Oréal Supply Chain Test Data Creation
Creates a complete, realistic supply chain from L'Oréal (brand) to originator
with all intermediate actors and realistic company names
"""
import sys
import os
sys.path.append('/Users/elisha/common')

from app.core.database import SessionLocal
from app.models.user import User
from app.models.company import Company
from app.models.product import Product
from app.models.purchase_order import PurchaseOrder
from app.core.security import hash_password
from uuid import uuid4
from datetime import datetime, timedelta

def create_loreal_supply_chain():
    """Create L'Oréal supply chain with all actors from brand to originator"""
    
    print("💄 Creating L'Oréal Supply Chain Test Data...")
    print("=" * 60)
    print("🌍 Supply Chain: L'Oréal → Trader → Processor → Mill → Originator")
    print("=" * 60)
    
    db = SessionLocal()
    
    try:
        # Define the complete L'Oréal supply chain
        supply_chain = [
            # TIER 1: CONSUMER BRAND - L'Oréal
            {
                'company': {
                    'name': "L'Oréal Group",
                    'company_type': 'brand',
                    'email': 'sustainability@loreal.com',
                    'phone': '+33-1-47-56-70-00',
                    'address_street': '14 Rue Royale',
                    'address_city': 'Paris',
                    'address_country': 'France',
                    'website': 'https://www.loreal.com',
                    'sector_id': 'palm_oil',
                    'tier_level': 1
                },
                'users': [
                    {
                        'email': 'sustainability@loreal.com',
                        'password': 'password123',
                        'full_name': 'Marie Dubois',
                        'role': 'brand_manager',
                        'permissions': ['brand_strategy', 'sustainability_tracking', 'supply_chain_oversight']
                    },
                    {
                        'email': 'procurement@loreal.com',
                        'password': 'password123',
                        'full_name': 'Jean-Pierre Martin',
                        'role': 'procurement_director',
                        'permissions': ['strategic_procurement', 'supplier_relationships']
                    },
                    {
                        'email': 'csr@loreal.com',
                        'password': 'password123',
                        'full_name': 'Sophie Laurent',
                        'role': 'csr_manager',
                        'permissions': ['csr_management', 'sustainability_reporting']
                    }
                ]
            },
            
            # TIER 2: GLOBAL TRADER
            {
                'company': {
                    'name': 'Wilmar International Limited',
                    'company_type': 'trader_aggregator',
                    'email': 'trading@wilmar-intl.com',
                    'phone': '+65-6266-3636',
                    'address_street': '5 Tampines Central 1',
                    'address_city': 'Singapore',
                    'address_country': 'Singapore',
                    'website': 'https://www.wilmar-intl.com',
                    'sector_id': 'palm_oil',
                    'tier_level': 2
                },
                'users': [
                    {
                        'email': 'trader@wilmar-intl.com',
                        'password': 'password123',
                        'full_name': 'David Chen',
                        'role': 'trader',
                        'permissions': ['trade_commodities', 'supply_chain_management']
                    },
                    {
                        'email': 'sustainability@wilmar-intl.com',
                        'password': 'password123',
                        'full_name': 'Sarah Tan',
                        'role': 'sustainability_manager',
                        'permissions': ['sustainability_tracking', 'certification_management']
                    }
                ]
            },
            
            # TIER 3: REFINERY/PROCESSOR
            {
                'company': {
                    'name': 'IOI Corporation Berhad',
                    'company_type': 'processor',
                    'email': 'operations@ioigroup.com',
                    'phone': '+60-3-2161-7777',
                    'address_street': 'Level 29, IOI City Tower 2',
                    'address_city': 'Putrajaya',
                    'address_country': 'Malaysia',
                    'website': 'https://www.ioigroup.com',
                    'sector_id': 'palm_oil',
                    'tier_level': 3
                },
                'users': [
                    {
                        'email': 'refinery@ioigroup.com',
                        'password': 'password123',
                        'full_name': 'Ahmad Rahman',
                        'role': 'processor',
                        'permissions': ['process_orders', 'refine_oil', 'manage_batches']
                    },
                    {
                        'email': 'quality@ioigroup.com',
                        'password': 'password123',
                        'full_name': 'Fatimah Abdullah',
                        'role': 'quality_manager',
                        'permissions': ['quality_control', 'certification_management']
                    }
                ]
            },
            
            # TIER 4: MILL
            {
                'company': {
                    'name': 'Sime Darby Plantation Berhad',
                    'company_type': 'mill_processor',
                    'email': 'mill@simeplantation.com',
                    'phone': '+60-3-2691-1000',
                    'address_street': 'Level 3A, Wisma Sime Darby',
                    'address_city': 'Kuala Lumpur',
                    'address_country': 'Malaysia',
                    'website': 'https://www.simeplantation.com',
                    'sector_id': 'palm_oil',
                    'tier_level': 4
                },
                'users': [
                    {
                        'email': 'millmanager@simeplantation.com',
                        'password': 'password123',
                        'full_name': 'Raj Kumar',
                        'role': 'processor',
                        'permissions': ['process_orders', 'manage_inventory', 'confirm_orders']
                    },
                    {
                        'email': 'sustainability@simeplantation.com',
                        'password': 'password123',
                        'full_name': 'Nurul Huda',
                        'role': 'sustainability_coordinator',
                        'permissions': ['sustainability_tracking', 'certification_management']
                    }
                ]
            },
            
            # TIER 5: ORIGINATOR - PLANTATION
            {
                'company': {
                    'name': 'PT Astra Agro Lestari Tbk',
                    'company_type': 'plantation_grower',
                    'email': 'plantation@astra-agro.com',
                    'phone': '+62-21-5315-8888',
                    'address_street': 'Jl. Pulo Ayang Raya Blok OR-1',
                    'address_city': 'Jakarta',
                    'address_country': 'Indonesia',
                    'website': 'https://www.astra-agro.com',
                    'sector_id': 'palm_oil',
                    'tier_level': 5
                },
                'users': [
                    {
                        'email': 'plantation@astra-agro.com',
                        'password': 'password123',
                        'full_name': 'Budi Santoso',
                        'role': 'originator',
                        'permissions': ['add_origin_data', 'provide_farmer_data', 'manage_farms']
                    },
                    {
                        'email': 'harvest@astra-agro.com',
                        'password': 'password123',
                        'full_name': 'Siti Rahayu',
                        'role': 'harvest_coordinator',
                        'permissions': ['add_origin_data', 'record_harvest']
                    },
                    {
                        'email': 'sustainability@astra-agro.com',
                        'password': 'password123',
                        'full_name': 'Agus Wijaya',
                        'role': 'sustainability_manager',
                        'permissions': ['sustainability_tracking', 'certification_management']
                    }
                ]
            },
            
            # TIER 6: SMALLHOLDER COOPERATIVE
            {
                'company': {
                    'name': 'Koperasi Sawit Berkelanjutan',
                    'company_type': 'plantation_grower',
                    'email': 'coop@sawitberkelanjutan.co.id',
                    'phone': '+62-811-2345-6789',
                    'address_street': 'Jl. Koperasi Sawit No. 15',
                    'address_city': 'Medan',
                    'address_country': 'Indonesia',
                    'website': 'https://www.sawitberkelanjutan.co.id',
                    'sector_id': 'palm_oil',
                    'tier_level': 6
                },
                'users': [
                    {
                        'email': 'coop@sawitberkelanjutan.co.id',
                        'password': 'password123',
                        'full_name': 'Mariam Sari',
                        'role': 'originator',
                        'permissions': ['add_origin_data', 'manage_smallholders']
                    }
                ]
            }
        ]
        
        # Create companies and users
        created_companies = []
        created_users = []
        
        for chain_data in supply_chain:
            company_data = chain_data['company']
            users_data = chain_data['users']
            
            # Check if company already exists
            existing_company = db.query(Company).filter(Company.name == company_data['name']).first()
            if existing_company:
                print(f"📋 Using existing company: {company_data['name']}")
                company = existing_company
            else:
                # Create company
                company = Company(
                    id=uuid4(),
                    **company_data
                )
                db.add(company)
                db.flush()
                print(f"🏢 Created: {company_data['name']} (Tier {company_data['tier_level']})")
                created_companies.append(company)
            
            # Create users for this company
            for user_data in users_data:
                # Check if user already exists
                existing_user = db.query(User).filter(User.email == user_data['email']).first()
                if existing_user:
                    print(f"  👤 User exists: {user_data['email']}")
                    continue
                
                # Create user
                hashed_password = hash_password(user_data['password'])
                user = User(
                    id=uuid4(),
                    email=user_data['email'],
                    hashed_password=hashed_password,
                    full_name=user_data['full_name'],
                    role=user_data['role'],
                    company_id=company.id,
                    is_active=True
                )
                db.add(user)
                created_users.append((user, user_data['password']))
                print(f"  👤 Created: {user_data['email']} ({user_data['role']})")
        
        # Create palm oil products if they don't exist
        create_palm_oil_products(db)
        
        # Create sample purchase orders to show the supply chain flow
        create_sample_purchase_orders(db, created_companies)
        
        # Commit all changes
        db.commit()
        
        print("\n" + "=" * 60)
        print("✅ L'ORÉAL SUPPLY CHAIN CREATED SUCCESSFULLY!")
        print("=" * 60)
        
        # Display the supply chain flow
        print(f"\n🌍 SUPPLY CHAIN FLOW:")
        print("=" * 60)
        
        for i, chain_data in enumerate(supply_chain):
            company = chain_data['company']
            tier_emoji = {
                1: "🏷️", 2: "📈", 3: "🏭", 4: "⚙️", 5: "🌱", 6: "🌱"
            }.get(company['tier_level'], "🏢")
            
            print(f"{tier_emoji} TIER {company['tier_level']}: {company['name']}")
            print(f"   📧 {company['email']}")
            print(f"   🌐 {company['website']}")
            print(f"   📍 {company['address_city']}, {company['address_country']}")
            
            if i < len(supply_chain) - 1:
                print("   ⬇️  ↓")
        
        # Display login credentials
        print(f"\n🔐 LOGIN CREDENTIALS (All use password: password123):")
        print("=" * 60)
        
        for chain_data in supply_chain:
            company = chain_data['company']
            print(f"\n{tier_emoji} {company['name']} ({company['company_type'].upper()})")
            for user_data in chain_data['users']:
                print(f"  📧 {user_data['email']} - {user_data['full_name']} ({user_data['role']})")
        
        print(f"\n🌐 ACCESS POINTS:")
        print(f"  🖥️  Frontend: http://localhost:3000")
        print(f"  📚 API Docs: http://localhost:8000/docs")
        
        print(f"\n💡 TESTING SCENARIOS:")
        print(f"  🏷️  L'Oréal: Test brand transparency dashboard")
        print(f"  📈 Wilmar: Test trader operations and risk management")
        print(f"  🏭 IOI: Test refinery processing and quality control")
        print(f"  ⚙️  Sime Darby: Test mill operations and inventory")
        print(f"  🌱 Astra Agro: Test plantation management and origin data")
        print(f"  🌱 Koperasi: Test smallholder cooperative features")
        
        print(f"\n🔄 END-TO-END WORKFLOW:")
        print(f"  1. L'Oréal creates purchase order for palm oil")
        print(f"  2. Wilmar confirms and sources from IOI")
        print(f"  3. IOI refines oil from Sime Darby mill")
        print(f"  4. Sime Darby processes FFB from Astra Agro")
        print(f"  5. Astra Agro records origin data from plantations")
        print(f"  6. Complete traceability from brand to origin!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

def create_palm_oil_products(db):
    """Create palm oil products for the supply chain"""
    print("\n🛍️  Creating palm oil products...")
    
    products = [
        {
            'common_product_id': 'FFB-001',
            'name': 'Fresh Fruit Bunches (FFB)',
            'description': 'Fresh palm fruit bunches harvested from oil palm trees',
            'category': 'raw_material',
            'can_have_composition': False,
            'default_unit': 'KGM',
            'hs_code': '1207.10.00'
        },
        {
            'common_product_id': 'CPO-001',
            'name': 'Crude Palm Oil (CPO)',
            'description': 'Unrefined palm oil extracted from fresh fruit bunches',
            'category': 'processed',
            'can_have_composition': True,
            'material_breakdown': {'palm_oil': 100.0},
            'default_unit': 'KGM',
            'hs_code': '1511.10.00'
        },
        {
            'common_product_id': 'RBD-PO-001',
            'name': 'Refined, Bleached, Deodorized Palm Oil (RBD PO)',
            'description': 'Refined palm oil suitable for food applications',
            'category': 'processed',
            'can_have_composition': True,
            'material_breakdown': {'refined_palm_oil': 100.0},
            'default_unit': 'KGM',
            'hs_code': '1511.90.00'
        }
    ]
    
    for product_data in products:
        existing = db.query(Product).filter(Product.common_product_id == product_data['common_product_id']).first()
        if not existing:
            product = Product(
                id=uuid4(),
                **product_data
            )
            db.add(product)
            print(f"  ✅ Created: {product_data['name']}")

def create_sample_purchase_orders(db, companies):
    """Create sample purchase orders to demonstrate the supply chain flow"""
    print("\n📋 Creating sample purchase orders...")
    
    # Get companies by name for easier reference
    company_map = {company.name: company for company in companies}
    
    # Create a sample PO from L'Oréal to Wilmar
    loreal = company_map.get("L'Oréal Group")
    wilmar = company_map.get('Wilmar International Limited')
    
    if loreal and wilmar:
        # Check if PO already exists
        existing_po = db.query(PurchaseOrder).filter(
            PurchaseOrder.po_number == 'LOR-2025-001'
        ).first()
        
        if not existing_po:
            po = PurchaseOrder(
                id=uuid4(),
                po_number='LOR-2025-001',
                buyer_company_id=loreal.id,
                seller_company_id=wilmar.id,
                product_id=db.query(Product).filter(Product.common_product_id == 'RBD-PO-001').first().id,
                quantity=1000.0,
                unit='KGM',
                unit_price=850.0,
                total_amount=850000.0,
                delivery_date=(datetime.now() + timedelta(days=30)).isoformat(),
                delivery_location='Le Havre Port, France',
                status='confirmed',
                created_at=datetime.now().isoformat(),
                updated_at=datetime.now().isoformat()
            )
            db.add(po)
            print(f"  ✅ Created PO: {po.po_number} (L'Oréal → Wilmar)")

if __name__ == "__main__":
    create_loreal_supply_chain()
