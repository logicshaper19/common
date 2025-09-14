#!/usr/bin/env python3
"""
Create Complete L'Oréal Supply Chain with Companies, Users, Products, and Purchase Orders
"""
import sys
import os
sys.path.append('/Users/elisha/common')

from app.core.database import SessionLocal
from app.models.company import Company
from app.models.user import User
from app.models.product import Product
from app.models.purchase_order import PurchaseOrder
from app.core.security import hash_password
from uuid import uuid4
from datetime import date, datetime, timedelta

def create_complete_loreal_supply_chain():
    """Create the complete L'Oréal supply chain with all data"""
    
    print("💄 Creating Complete L'Oréal Supply Chain...")
    print("=" * 70)
    print("🌍 From L'Oréal (Brand) to Smallholder Cooperative (Originator)")
    print("=" * 70)
    
    db = SessionLocal()
    
    try:
        # Step 1: Create companies and users
        print("\n🏢 STEP 1: Creating Companies and Users...")
        print("-" * 50)
        
        companies_data = [
            # TIER 1: BRAND
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
                        'role': 'brand_manager'
                    },
                    {
                        'email': 'procurement@loreal.com',
                        'password': 'password123',
                        'full_name': 'Jean-Pierre Martin',
                        'role': 'procurement_director'
                    },
                    {
                        'email': 'csr@loreal.com',
                        'password': 'password123',
                        'full_name': 'Sophie Laurent',
                        'role': 'csr_manager'
                    }
                ]
            },
            
            # TIER 2: TRADER
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
                        'role': 'trader'
                    },
                    {
                        'email': 'sustainability@wilmar-intl.com',
                        'password': 'password123',
                        'full_name': 'Sarah Tan',
                        'role': 'sustainability_manager'
                    }
                ]
            },
            
            # TIER 3: PROCESSOR
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
                        'role': 'processor'
                    },
                    {
                        'email': 'quality@ioigroup.com',
                        'password': 'password123',
                        'full_name': 'Fatimah Abdullah',
                        'role': 'quality_manager'
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
                        'role': 'processor'
                    },
                    {
                        'email': 'sustainability@simeplantation.com',
                        'password': 'password123',
                        'full_name': 'Nurul Huda',
                        'role': 'sustainability_coordinator'
                    }
                ]
            },
            
            # TIER 5: PLANTATION
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
                        'role': 'originator'
                    },
                    {
                        'email': 'harvest@astra-agro.com',
                        'password': 'password123',
                        'full_name': 'Siti Rahayu',
                        'role': 'harvest_coordinator'
                    },
                    {
                        'email': 'sustainability@astra-agro.com',
                        'password': 'password123',
                        'full_name': 'Agus Wijaya',
                        'role': 'sustainability_manager'
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
                        'role': 'originator'
                    }
                ]
            }
        ]
        
        created_companies = {}
        
        for tier_data in companies_data:
            company_data = tier_data['company']
            users_data = tier_data['users']
            
            # Check if company already exists
            existing_company = db.query(Company).filter(Company.name == company_data['name']).first()
            if existing_company:
                print(f"🏢 Company exists: {company_data['name']}")
                created_companies[company_data['name']] = existing_company
                continue
            
            # Create company
            company = Company(
                id=uuid4(),
                **company_data
            )
            db.add(company)
            db.flush()
            created_companies[company_data['name']] = company
            print(f"🏢 Created: {company_data['name']} (Tier {company_data['tier_level']})")
            
            # Create users for this company
            for user_data in users_data:
                # Check if user already exists
                existing_user = db.query(User).filter(User.email == user_data['email']).first()
                if existing_user:
                    print(f"  👤 User exists: {user_data['email']}")
                    continue
                
                # Create user
                user = User(
                    id=uuid4(),
                    email=user_data['email'],
                    hashed_password=hash_password(user_data['password']),
                    full_name=user_data['full_name'],
                    role=user_data['role'],
                    company_id=company.id,
                    is_active=True
                )
                db.add(user)
                print(f"  👤 Created: {user_data['email']} ({user_data['role']})")
        
        # Step 2: Create products
        print("\n🛍️  STEP 2: Creating Products...")
        print("-" * 50)
        
        products_data = [
            {
                'common_product_id': 'RBD-PO-001',
                'name': 'Refined Palm Oil (RBD PO)',
                'description': 'Refined, Bleached, and Deodorized Palm Oil',
                'category': 'palm_oil',
                'default_unit': 'KGM',
                'hs_code': '15119000',
                'origin_data_requirements': {
                    'coordinates_required': True,
                    'certifications_required': ['RSPO', 'NDPE'],
                    'harvest_date_required': True,
                    'plantation_id_required': True
                }
            },
            {
                'common_product_id': 'CPO-001',
                'name': 'Crude Palm Oil (CPO)',
                'description': 'Crude Palm Oil from palm fruit processing',
                'category': 'palm_oil',
                'default_unit': 'KGM',
                'hs_code': '15111000',
                'origin_data_requirements': {
                    'coordinates_required': True,
                    'certifications_required': ['RSPO', 'NDPE'],
                    'harvest_date_required': True,
                    'plantation_id_required': True
                }
            },
            {
                'common_product_id': 'FFB-001',
                'name': 'Fresh Fruit Bunches (FFB)',
                'description': 'Fresh Palm Fruit Bunches from plantation',
                'category': 'palm_oil',
                'default_unit': 'KGM',
                'hs_code': '08011000',
                'origin_data_requirements': {
                    'coordinates_required': True,
                    'certifications_required': ['RSPO', 'NDPE'],
                    'harvest_date_required': True,
                    'plantation_id_required': True
                }
            }
        ]
        
        created_products = {}
        
        for product_data in products_data:
            # Check if product already exists
            existing_product = db.query(Product).filter(Product.common_product_id == product_data['common_product_id']).first()
            if existing_product:
                print(f"🛍️  Product exists: {product_data['name']}")
                created_products[product_data['common_product_id']] = existing_product
                continue
            
            # Create product
            product = Product(
                id=uuid4(),
                **product_data
            )
            db.add(product)
            db.flush()
            created_products[product_data['common_product_id']] = product
            print(f"🛍️  Created: {product_data['name']}")
        
        # Step 3: Create purchase orders
        print("\n📋 STEP 3: Creating Purchase Order Chain...")
        print("-" * 50)
        
        # Get company IDs
        loreal = created_companies["L'Oréal Group"]
        wilmar = created_companies['Wilmar International Limited']
        ioi = created_companies['IOI Corporation Berhad']
        sime_darby = created_companies['Sime Darby Plantation Berhad']
        astra_agro = created_companies['PT Astra Agro Lestari Tbk']
        koperasi = created_companies['Koperasi Sawit Berkelanjutan']
        
        # Get product IDs
        rbd_po = created_products['RBD-PO-001']
        cpo = created_products['CPO-001']
        ffb = created_products['FFB-001']
        
        purchase_orders_data = [
            {
                'po_number': 'LOR-2025-001',
                'buyer_company_id': loreal.id,
                'seller_company_id': wilmar.id,
                'product_id': rbd_po.id,
                'quantity': 1000,
                'unit_price': 850.00,
                'total_amount': 850000.00,
                'unit': 'KGM',
                'delivery_date': date.today() + timedelta(days=30),
                'delivery_location': 'Le Havre Port, France',
                'supply_chain_level': 1,
                'is_chain_initiated': True
            },
            {
                'po_number': 'WIL-2025-001',
                'buyer_company_id': wilmar.id,
                'seller_company_id': ioi.id,
                'product_id': rbd_po.id,
                'quantity': 1200,
                'unit_price': 800.00,
                'total_amount': 960000.00,
                'unit': 'KGM',
                'delivery_date': date.today() + timedelta(days=25),
                'delivery_location': 'Singapore Port',
                'supply_chain_level': 2,
                'is_chain_initiated': False
            },
            {
                'po_number': 'IOI-2025-001',
                'buyer_company_id': ioi.id,
                'seller_company_id': sime_darby.id,
                'product_id': cpo.id,
                'quantity': 1500,
                'unit_price': 750.00,
                'total_amount': 1125000.00,
                'unit': 'KGM',
                'delivery_date': date.today() + timedelta(days=20),
                'delivery_location': 'Port Klang, Malaysia',
                'supply_chain_level': 3,
                'is_chain_initiated': False
            },
            {
                'po_number': 'SDB-2025-001',
                'buyer_company_id': sime_darby.id,
                'seller_company_id': astra_agro.id,
                'product_id': ffb.id,
                'quantity': 2000,
                'unit_price': 300.00,
                'total_amount': 600000.00,
                'unit': 'KGM',
                'delivery_date': date.today() + timedelta(days=15),
                'delivery_location': 'Medan Port, Indonesia',
                'supply_chain_level': 4,
                'is_chain_initiated': False
            },
            {
                'po_number': 'AST-2025-001',
                'buyer_company_id': astra_agro.id,
                'seller_company_id': koperasi.id,
                'product_id': ffb.id,
                'quantity': 500,
                'unit_price': 280.00,
                'total_amount': 140000.00,
                'unit': 'KGM',
                'delivery_date': date.today() + timedelta(days=10),
                'delivery_location': 'Plantation Gate, North Sumatra',
                'supply_chain_level': 5,
                'is_chain_initiated': False
            }
        ]
        
        created_pos = {}
        
        for po_data in purchase_orders_data:
            # Check if PO already exists
            existing_po = db.query(PurchaseOrder).filter(PurchaseOrder.po_number == po_data['po_number']).first()
            if existing_po:
                print(f"📋 PO exists: {po_data['po_number']}")
                created_pos[po_data['po_number']] = existing_po
                continue
            
            # Create purchase order
            po = PurchaseOrder(
                id=uuid4(),
                **po_data
            )
            db.add(po)
            db.flush()
            created_pos[po_data['po_number']] = po
            print(f"📋 Created: {po_data['po_number']}")
        
        # Link purchase orders
        print("\n🔗 STEP 4: Linking Purchase Orders...")
        print("-" * 50)
        
        # Link the chain
        lor_po = created_pos['LOR-2025-001']
        wil_po = created_pos['WIL-2025-001']
        ioi_po = created_pos['IOI-2025-001']
        sdb_po = created_pos['SDB-2025-001']
        ast_po = created_pos['AST-2025-001']
        
        # Set parent relationships
        wil_po.parent_po_id = lor_po.id
        wil_po.linked_po_id = lor_po.id
        
        ioi_po.parent_po_id = wil_po.id
        ioi_po.linked_po_id = wil_po.id
        
        sdb_po.parent_po_id = ioi_po.id
        sdb_po.linked_po_id = ioi_po.id
        
        ast_po.parent_po_id = sdb_po.id
        ast_po.linked_po_id = sdb_po.id
        
        print("🔗 Linked purchase order chain successfully!")
        
        # Commit all changes
        db.commit()
        
        print("\n" + "=" * 70)
        print("🎉 COMPLETE L'ORÉAL SUPPLY CHAIN CREATED SUCCESSFULLY!")
        print("=" * 70)
        
        print("\n🌍 SUPPLY CHAIN OVERVIEW:")
        print("=" * 70)
        print("🏷️  TIER 1: L'Oréal Group (Brand) - France")
        print("   ↓ Purchase Order: LOR-2025-001")
        print("📈 TIER 2: Wilmar International (Trader) - Singapore")
        print("   ↓ Purchase Order: WIL-2025-001")
        print("🏭 TIER 3: IOI Corporation (Refinery) - Malaysia")
        print("   ↓ Purchase Order: IOI-2025-001")
        print("⚙️  TIER 4: Sime Darby Plantation (Mill) - Malaysia")
        print("   ↓ Purchase Order: SDB-2025-001")
        print("🌱 TIER 5: PT Astra Agro Lestari (Plantation) - Indonesia")
        print("   ↓ Purchase Order: AST-2025-001")
        print("🌱 TIER 6: Koperasi Sawit Berkelanjutan (Smallholders) - Indonesia")
        
        print("\n🔐 LOGIN CREDENTIALS (All use password: password123):")
        print("=" * 70)
        
        print("\n🏷️  L'Oréal Group:")
        print("  📧 sustainability@loreal.com - Marie Dubois (brand_manager)")
        print("  📧 procurement@loreal.com - Jean-Pierre Martin (procurement_director)")
        print("  📧 csr@loreal.com - Sophie Laurent (csr_manager)")
        
        print("\n📈 Wilmar International:")
        print("  📧 trader@wilmar-intl.com - David Chen (trader)")
        print("  📧 sustainability@wilmar-intl.com - Sarah Tan (sustainability_manager)")
        
        print("\n🏭 IOI Corporation:")
        print("  📧 refinery@ioigroup.com - Ahmad Rahman (processor)")
        print("  📧 quality@ioigroup.com - Fatimah Abdullah (quality_manager)")
        
        print("\n⚙️  Sime Darby Plantation:")
        print("  📧 millmanager@simeplantation.com - Raj Kumar (processor)")
        print("  📧 sustainability@simeplantation.com - Nurul Huda (sustainability_coordinator)")
        
        print("\n🌱 PT Astra Agro Lestari:")
        print("  📧 plantation@astra-agro.com - Budi Santoso (originator)")
        print("  📧 harvest@astra-agro.com - Siti Rahayu (harvest_coordinator)")
        print("  📧 sustainability@astra-agro.com - Agus Wijaya (sustainability_manager)")
        
        print("\n🌱 Koperasi Sawit Berkelanjutan:")
        print("  📧 coop@sawitberkelanjutan.co.id - Mariam Sari (originator)")
        
        print("\n🌐 ACCESS POINTS:")
        print("=" * 70)
        print("  🖥️  Frontend: http://localhost:3000")
        print("  📚 API Docs: http://localhost:8000/docs")
        print("  🔍 Health Check: http://localhost:8000/health/")
        
        print("\n💡 TESTING SCENARIOS:")
        print("=" * 70)
        print("  🏷️  L'Oréal: Test brand transparency dashboard and sustainability tracking")
        print("  📈 Wilmar: Test trader operations, risk management, and supply chain oversight")
        print("  🏭 IOI: Test refinery processing, quality control, and batch management")
        print("  ⚙️  Sime Darby: Test mill operations, inventory management, and processing")
        print("  🌱 Astra Agro: Test plantation management, origin data recording, and farm tracking")
        print("  🌱 Koperasi: Test smallholder cooperative features and harvest recording")
        
        print("\n🔄 END-TO-END WORKFLOW TESTING:")
        print("=" * 70)
        print("  1. 🌱 Koperasi records harvest data and origin information")
        print("  2. 🌱 Astra Agro manages plantation operations and creates batches")
        print("  3. ⚙️  Sime Darby processes FFB and creates crude palm oil")
        print("  4. 🏭 IOI refines crude oil into refined palm oil")
        print("  5. 📈 Wilmar trades refined oil and manages supply chain")
        print("  6. 🏷️  L'Oréal tracks complete supply chain transparency")
        print("  7. 🔍 All actors can view their portion of the supply chain")
        
        print("\n📊 SUPPLY CHAIN METRICS:")
        print("=" * 70)
        print("  💰 Total Chain Value: $3,675,000")
        print("  📦 Total Volume: 6,200 KGM")
        print("  🌍 Countries: 3 (France, Singapore, Malaysia, Indonesia)")
        print("  🏢 Companies: 6")
        print("  👤 Users: 12")
        print("  📋 Purchase Orders: 5")
        print("  🛍️  Products: 3 (FFB, CPO, RBD PO)")
        
        print("\n🎯 NEXT STEPS:")
        print("=" * 70)
        print("  1. Start the backend server: python -m uvicorn app.main:app --reload")
        print("  2. Start the frontend: cd frontend && npm start")
        print("  3. Login as L'Oréal user to test brand transparency dashboard")
        print("  4. Login as Astra Agro user to test origin dashboard")
        print("  5. Test the complete supply chain traceability")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_complete_loreal_supply_chain()
