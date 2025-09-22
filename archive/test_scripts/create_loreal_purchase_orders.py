#!/usr/bin/env python3
"""
L'Oréal Supply Chain Purchase Orders
Creates a complete chain of purchase orders from L'Oréal to originator
"""
import sys
import os
sys.path.append('/Users/elisha/common')

from app.core.database import SessionLocal
from app.models.purchase_order import PurchaseOrder
from app.models.product import Product
from app.models.company import Company
from uuid import uuid4
from datetime import datetime, timedelta

def create_loreal_purchase_order_chain():
    """Create a complete chain of purchase orders from L'Oréal to originator"""
    
    print("📋 Creating L'Oréal Purchase Order Chain...")
    print("=" * 60)
    
    db = SessionLocal()
    
    try:
        # Get companies
        companies = {
            'L\'Oréal Group': db.query(Company).filter(Company.name == 'L\'Oréal Group').first(),
            'Wilmar International Limited': db.query(Company).filter(Company.name == 'Wilmar International Limited').first(),
            'IOI Corporation Berhad': db.query(Company).filter(Company.name == 'IOI Corporation Berhad').first(),
            'Sime Darby Plantation Berhad': db.query(Company).filter(Company.name == 'Sime Darby Plantation Berhad').first(),
            'PT Astra Agro Lestari Tbk': db.query(Company).filter(Company.name == 'PT Astra Agro Lestari Tbk').first(),
            'Koperasi Sawit Berkelanjutan': db.query(Company).filter(Company.name == 'Koperasi Sawit Berkelanjutan').first()
        }
        
        # Get products
        products = {
            'RBD-PO-001': db.query(Product).filter(Product.common_product_id == 'RBD-PO-001').first(),
            'CPO-001': db.query(Product).filter(Product.common_product_id == 'CPO-001').first(),
            'FFB-001': db.query(Product).filter(Product.common_product_id == 'FFB-001').first()
        }
        
        # Check if all companies and products exist
        missing = []
        for name, company in companies.items():
            if not company:
                missing.append(f"Company: {name}")
        for name, product in products.items():
            if not product:
                missing.append(f"Product: {name}")
        
        if missing:
            print(f"❌ Missing required data:")
            for item in missing:
                print(f"  - {item}")
            print(f"\n💡 Run 'python create_loreal_supply_chain.py' first to create companies and products")
            return
        
        # Define the purchase order chain
        po_chain = [
            {
                'po_number': 'LOR-2025-001',
                'buyer': 'L\'Oréal Group',
                'seller': 'Wilmar International Limited',
                'product': 'RBD-PO-001',
                'quantity': 1000.0,
                'unit': 'KGM',
                'unit_price': 850.0,
                'total_amount': 850000.0,
                'delivery_date': (datetime.now() + timedelta(days=30)).isoformat(),
                'delivery_location': 'Le Havre Port, France',
                'status': 'confirmed',
                'description': 'Refined palm oil for cosmetic production'
            },
            {
                'po_number': 'WIL-2025-001',
                'buyer': 'Wilmar International Limited',
                'seller': 'IOI Corporation Berhad',
                'product': 'RBD-PO-001',
                'quantity': 1200.0,
                'unit': 'KGM',
                'unit_price': 800.0,
                'total_amount': 960000.0,
                'delivery_date': (datetime.now() + timedelta(days=25)).isoformat(),
                'delivery_location': 'Singapore Port',
                'status': 'confirmed',
                'description': 'Refined palm oil for trading'
            },
            {
                'po_number': 'IOI-2025-001',
                'buyer': 'IOI Corporation Berhad',
                'seller': 'Sime Darby Plantation Berhad',
                'product': 'CPO-001',
                'quantity': 1500.0,
                'unit': 'KGM',
                'unit_price': 750.0,
                'total_amount': 1125000.0,
                'delivery_date': (datetime.now() + timedelta(days=20)).isoformat(),
                'delivery_location': 'Port Klang, Malaysia',
                'status': 'confirmed',
                'description': 'Crude palm oil for refining'
            },
            {
                'po_number': 'SDB-2025-001',
                'buyer': 'Sime Darby Plantation Berhad',
                'seller': 'PT Astra Agro Lestari Tbk',
                'product': 'FFB-001',
                'quantity': 2000.0,
                'unit': 'KGM',
                'unit_price': 300.0,
                'total_amount': 600000.0,
                'delivery_date': (datetime.now() + timedelta(days=15)).isoformat(),
                'delivery_location': 'Medan Port, Indonesia',
                'status': 'confirmed',
                'description': 'Fresh fruit bunches for processing'
            },
            {
                'po_number': 'AST-2025-001',
                'buyer': 'PT Astra Agro Lestari Tbk',
                'seller': 'Koperasi Sawit Berkelanjutan',
                'product': 'FFB-001',
                'quantity': 500.0,
                'unit': 'KGM',
                'unit_price': 280.0,
                'total_amount': 140000.0,
                'delivery_date': (datetime.now() + timedelta(days=10)).isoformat(),
                'delivery_location': 'Plantation Site, North Sumatra',
                'status': 'confirmed',
                'description': 'Fresh fruit bunches from smallholder cooperative'
            }
        ]
        
        created_pos = []
        
        for po_data in po_chain:
            # Check if PO already exists
            existing_po = db.query(PurchaseOrder).filter(
                PurchaseOrder.po_number == po_data['po_number']
            ).first()
            
            if existing_po:
                print(f"📋 PO already exists: {po_data['po_number']}")
                continue
            
            # Create purchase order
            po = PurchaseOrder(
                id=uuid4(),
                po_number=po_data['po_number'],
                buyer_company_id=companies[po_data['buyer']].id,
                seller_company_id=companies[po_data['seller']].id,
                product_id=products[po_data['product']].id,
                quantity=po_data['quantity'],
                unit=po_data['unit'],
                unit_price=po_data['unit_price'],
                total_amount=po_data['total_amount'],
                delivery_date=po_data['delivery_date'],
                delivery_location=po_data['delivery_location'],
                status=po_data['status'],
                notes=po_data['description'],
                created_at=datetime.now().isoformat(),
                updated_at=datetime.now().isoformat()
            )
            
            db.add(po)
            created_pos.append(po)
            print(f"✅ Created: {po_data['po_number']} ({po_data['buyer']} → {po_data['seller']})")
        
        # Commit all changes
        db.commit()
        
        print("\n" + "=" * 60)
        print("✅ L'ORÉAL PURCHASE ORDER CHAIN CREATED!")
        print("=" * 60)
        
        # Display the complete chain
        print(f"\n🔄 COMPLETE SUPPLY CHAIN FLOW:")
        print("=" * 60)
        
        for i, po_data in enumerate(po_chain):
            print(f"{i+1}. {po_data['po_number']}: {po_data['buyer']} → {po_data['seller']}")
            print(f"   📦 Product: {po_data['product']}")
            print(f"   📊 Quantity: {po_data['quantity']} {po_data['unit']}")
            print(f"   💰 Value: ${po_data['total_amount']:,.2f}")
            print(f"   📍 Delivery: {po_data['delivery_location']}")
            print(f"   📅 Date: {po_data['delivery_date'][:10]}")
            print()
        
        print(f"🌍 TOTAL SUPPLY CHAIN VALUE: ${sum(po['total_amount'] for po in po_chain):,.2f}")
        
        print(f"\n💡 TESTING SCENARIOS:")
        print(f"  🏷️  L'Oréal: View complete supply chain transparency")
        print(f"  📈 Wilmar: Track trading operations and risk")
        print(f"  🏭 IOI: Monitor refining and processing")
        print(f"  ⚙️  Sime Darby: Manage mill operations and inventory")
        print(f"  🌱 Astra Agro: Record plantation and origin data")
        print(f"  🌱 Koperasi: Manage smallholder contributions")
        
        print(f"\n🔄 END-TO-END TRACEABILITY:")
        print(f"  1. L'Oréal creates PO for refined palm oil")
        print(f"  2. Wilmar sources from IOI refinery")
        print(f"  3. IOI refines crude oil from Sime Darby mill")
        print(f"  4. Sime Darby processes FFB from Astra Agro plantation")
        print(f"  5. Astra Agro sources from Koperasi smallholders")
        print(f"  6. Complete traceability from brand to origin!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_loreal_purchase_order_chain()
