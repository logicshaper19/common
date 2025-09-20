#!/usr/bin/env python3
"""
Create outgoing purchase orders for the brand using existing suppliers.
Brand should only have OUTGOING POs (as buyer), not incoming ones.
"""
import requests
import json
import uuid
import time
from datetime import datetime, timedelta

# API base URL
BASE_URL = "http://127.0.0.1:8000"

# Current brand credentials
BRAND_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJiYTljNTI3Ni05MTMwLTQ3YzAtODgyYS05ZDJmYTI3N2NkZGEiLCJlbWFpbCI6ImJyYW5kMTc1ODAyNTYyN0BtYW51ZmFjdHVyZXIuY29tIiwicm9sZSI6ImFkbWluIiwiY29tcGFueV9pZCI6IjUxZTNkOTc4LTIyNGQtNGViMy1iMmQ0LTFjYzcyNTQyODZiYiIsInR5cGUiOiJhY2Nlc3MiLCJleHAiOjE3NTgwMzQ0NzB9.soSbrnGmHpl8zjRFtXILMqw8_Sr82bJG_1u0MMGrsTM"
BRAND_COMPANY_ID = "51e3d978-224d-4eb3-b2d4-1cc7254286bb"

def get_products():
    """Get available products."""
    print("📦 Getting available products...")
    headers = {"Authorization": f"Bearer {BRAND_TOKEN}"}
    response = requests.get(f"{BASE_URL}/api/v1/products/", headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        if 'data' in data and isinstance(data['data'], list) and len(data['data']) > 0:
            if isinstance(data['data'][0], list) and len(data['data'][0]) > 1:
                products = data['data'][0][1]
            else:
                products = data['data']
        else:
            products = []
        
        print(f"    Found {len(products)} products")
        
        # Map products by name
        product_map = {}
        for product in products:
            if isinstance(product, dict):
                name = product.get('name', '').lower()
                if 'refined' in name and 'palm' in name:
                    product_map['refined_palm_oil'] = product
                elif 'crude' in name and 'palm' in name:
                    product_map['crude_palm_oil'] = product
                elif 'fresh' in name and 'fruit' in name:
                    product_map['fresh_fruit_bunches'] = product
        
        # If we don't have enough products, use any available ones
        if len(product_map) < 2 and products:
            for i, product in enumerate(products[:3]):
                if isinstance(product, dict):
                    if i == 0 and 'refined_palm_oil' not in product_map:
                        product_map['refined_palm_oil'] = product
                    elif i == 1 and 'crude_palm_oil' not in product_map:
                        product_map['crude_palm_oil'] = product
                    elif i == 2 and 'fresh_fruit_bunches' not in product_map:
                        product_map['fresh_fruit_bunches'] = product
        
        print(f"    ✅ Mapped {len(product_map)} products: {list(product_map.keys())}")
        return product_map
    else:
        print(f"    ❌ Failed to get products: {response.status_code}")
        return {}

def get_existing_suppliers():
    """Get existing suppliers from the system."""
    print("🏢 Getting existing suppliers...")
    headers = {"Authorization": f"Bearer {BRAND_TOKEN}"}
    response = requests.get(f"{BASE_URL}/api/v1/companies/", headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        companies = data.get('data', [])
        
        # Filter for suppliers (non-manufacturer companies)
        suppliers = []
        for company in companies:
            if company.get('company_type') != 'manufacturer' and company.get('company_type') != 'brand':
                suppliers.append(company)
        
        print(f"    Found {len(suppliers)} existing suppliers")
        
        # Group by company type
        suppliers_by_type = {}
        for supplier in suppliers:
            company_type = supplier.get('company_type')
            if company_type not in suppliers_by_type:
                suppliers_by_type[company_type] = []
            suppliers_by_type[company_type].append(supplier)
        
        print(f"    ✅ Supplier types: {list(suppliers_by_type.keys())}")
        return suppliers_by_type
    else:
        print(f"    ❌ Failed to get suppliers: {response.status_code}")
        return {}

def create_brand_outgoing_pos(suppliers, products):
    """Create outgoing purchase orders for the brand."""
    print("\n🔗 Creating Brand Outgoing Purchase Orders...")
    
    headers = {"Authorization": f"Bearer {BRAND_TOKEN}"}
    
    # Define supply chain flow - Brand as BUYER
    supply_chain_flow = [
        {
            "supplier_type": "trader_aggregator",
            "product_key": "refined_palm_oil",
            "quantity": 1000,
            "unit_price": 800.00,
            "description": "Refined Palm Oil from Trader"
        },
        {
            "supplier_type": "refinery_crusher", 
            "product_key": "crude_palm_oil",
            "quantity": 1200,
            "unit_price": 600.00,
            "description": "Crude Palm Oil from Refinery"
        },
        {
            "supplier_type": "mill_processor",
            "product_key": "crude_palm_oil", 
            "quantity": 1500,
            "unit_price": 500.00,
            "description": "Crude Palm Oil from Mill"
        },
        {
            "supplier_type": "plantation_grower",
            "product_key": "fresh_fruit_bunches",
            "quantity": 5000,
            "unit_price": 200.00,
            "description": "Fresh Fruit Bunches from Plantation"
        }
    ]
    
    created_pos = []
    
    for i, flow in enumerate(supply_chain_flow):
        supplier_type = flow["supplier_type"]
        product_key = flow["product_key"]
        
        # Get a supplier of this type
        if supplier_type in suppliers and suppliers[supplier_type]:
            supplier = suppliers[supplier_type][0]  # Use first supplier of this type
            supplier_id = supplier["id"]
            supplier_name = supplier["name"]
            
            # Get the product
            if product_key in products:
                product = products[product_key]
                product_id = product["id"]
                product_name = product["name"]
                
                # Create purchase order data - Brand as BUYER
                po_data = {
                    "buyer_company_id": BRAND_COMPANY_ID,  # Brand is the buyer
                    "seller_company_id": supplier_id,      # Supplier is the seller
                    "product_id": product_id,
                    "quantity": flow["quantity"],
                    "unit_price": flow["unit_price"],
                    "unit": "kg",
                    "delivery_date": (datetime.now() + timedelta(days=30 + i*7)).date().isoformat(),
                    "delivery_location": f"Brand Manufacturing Facility",
                    "notes": f"Brand purchasing {product_name} from {supplier_name}"
                }
                
                print(f"  📋 Creating PO {i+1}: Brand → {supplier_name}")
                print(f"      Product: {product_name}")
                print(f"      Quantity: {flow['quantity']} kg @ ${flow['unit_price']}/kg")
                
                response = requests.post(f"{BASE_URL}/api/v1/purchase-orders/", json=po_data, headers=headers)
                
                if response.status_code == 200:
                    po = response.json()
                    created_pos.append(po)
                    print(f"    ✅ PO Created: {po.get('id', 'Unknown ID')}")
                else:
                    print(f"    ❌ Failed to create PO: {response.status_code} - {response.text}")
            else:
                print(f"    ❌ Product {product_key} not found")
        else:
            print(f"    ❌ No suppliers of type {supplier_type} found")
    
    return created_pos

def main():
    """Main function."""
    print("🚀 Creating Brand Outgoing Purchase Orders")
    print("=" * 60)
    print(f"🏭 Brand Company ID: {BRAND_COMPANY_ID}")
    print("📋 Note: Brand will be BUYER in all POs (outgoing only)")
    
    # Step 1: Get products
    print("\n📦 Step 1: Getting Products...")
    products = get_products()
    if not products:
        print("❌ Failed to get products")
        return
    
    # Step 2: Get existing suppliers
    print("\n🏢 Step 2: Getting Existing Suppliers...")
    suppliers = get_existing_suppliers()
    if not suppliers:
        print("❌ Failed to get suppliers")
        return
    
    # Step 3: Create brand outgoing purchase orders
    print("\n🔗 Step 3: Creating Brand Outgoing Purchase Orders...")
    created_pos = create_brand_outgoing_pos(suppliers, products)
    if not created_pos:
        print("❌ Failed to create purchase orders")
        return
    
    # Summary
    print("\n🎉 Brand Outgoing Purchase Orders Created Successfully!")
    print("=" * 60)
    print("📊 Summary:")
    print(f"  🏭 Brand Company: {BRAND_COMPANY_ID}")
    print(f"  🏢 Suppliers Used: {len(suppliers)} types")
    print(f"  📦 Products: {len(products)}")
    print(f"  📋 Outgoing Purchase Orders: {len(created_pos)}")
    
    print("\n🌱 Supply Chain Flow (Brand as Buyer):")
    print("  Brand → Trader (Refined Palm Oil)")
    print("  Brand → Refinery (Crude Palm Oil)")
    print("  Brand → Mill (Crude Palm Oil)")
    print("  Brand → Plantation (Fresh Fruit Bunches)")
    
    print("\n💡 You can now:")
    print("  - View your OUTGOING purchase orders in the dashboard")
    print("  - See all suppliers you're purchasing from")
    print("  - Track your supply chain as a brand")

if __name__ == "__main__":
    main()

