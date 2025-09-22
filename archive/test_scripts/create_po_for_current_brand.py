#!/usr/bin/env python3
"""
Create end-to-end purchase order flow for the current brand company.
"""
import requests
import json
import uuid
import time
from datetime import datetime, timedelta

# API base URL
BASE_URL = "http://127.0.0.1:8000"

# Current brand credentials (from your login)
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

def create_supply_chain_companies():
    """Create supply chain companies."""
    timestamp = int(time.time())
    companies = {}
    
    # Company types in supply chain order
    supply_chain = [
        ("trader_aggregator", "Global Trading Co"),
        ("refinery_crusher", "Premium Refinery Ltd"),
        ("mill_processor", "Sustainable Mill Corp"),
        ("plantation_grower", "Green Acres Plantation")
    ]
    
    for company_type, company_name in supply_chain:
        email_safe_type = company_type.replace("_", "-")
        
        registration_data = {
            "email": f"admin{timestamp}@{email_safe_type}.com",
            "password": "SecurePass123!",
            "full_name": f"Admin User",
            "role": "admin",
            "company_name": f"{company_name} {timestamp}",
            "company_type": company_type,
            "company_email": f"{email_safe_type}{timestamp}@example.com"
        }
        
        print(f"🏢 Creating {company_name}...")
        response = requests.post(f"{BASE_URL}/api/v1/auth/register", json=registration_data)
        
        if response.status_code == 200:
            data = response.json()
            access_token = data.get("access_token")
            
            # Decode JWT to get company_id
            import base64
            token_parts = access_token.split('.')
            payload = token_parts[1]
            payload += '=' * (4 - len(payload) % 4)
            decoded_payload = base64.b64decode(payload)
            token_data = json.loads(decoded_payload)
            company_id = token_data.get("company_id")
            
            companies[company_type] = {
                "id": company_id,
                "name": f"{company_name} {timestamp}",
                "access_token": access_token
            }
            
            print(f"    ✅ {company_name} Created: {company_id}")
            timestamp += 1
        else:
            print(f"    ❌ Failed to create {company_name}: {response.status_code}")
    
    return companies

def create_purchase_order_chain(companies, products):
    """Create purchase order chain for current brand."""
    print("\n🔗 Creating Purchase Order Chain for Current Brand...")
    
    headers = {"Authorization": f"Bearer {BRAND_TOKEN}"}
    
    # Define the supply chain flow
    chain_flow = [
        {
            "from": "brand",
            "to": "trader_aggregator", 
            "product": "refined_palm_oil",
            "quantity": 1000,
            "unit_price": 800.00,
            "po_number": "PO-BRAND-001"
        },
        {
            "from": "trader_aggregator",
            "to": "refinery_crusher",
            "product": "crude_palm_oil", 
            "quantity": 1200,
            "unit_price": 600.00,
            "po_number": "PO-TRADER-001"
        },
        {
            "from": "refinery_crusher",
            "to": "mill_processor",
            "product": "crude_palm_oil",
            "quantity": 1500,
            "unit_price": 500.00,
            "po_number": "PO-REFINERY-001"
        },
        {
            "from": "mill_processor",
            "to": "plantation_grower",
            "product": "fresh_fruit_bunches",
            "quantity": 5000,
            "unit_price": 200.00,
            "po_number": "PO-MILL-001"
        }
    ]
    
    created_pos = []
    
    for i, flow in enumerate(chain_flow):
        # Determine buyer and seller
        if flow["from"] == "brand":
            buyer_id = BRAND_COMPANY_ID
            buyer_token = BRAND_TOKEN
            buyer_headers = headers
        else:
            buyer_id = companies[flow["from"]]["id"]
            buyer_token = companies[flow["from"]]["access_token"]
            buyer_headers = {"Authorization": f"Bearer {buyer_token}"}
        
        seller_id = companies[flow["to"]]["id"]
        product_id = products[flow["product"]]["id"]
        
        # Create purchase order data
        po_data = {
            "buyer_company_id": buyer_id,
            "seller_company_id": seller_id,
            "product_id": product_id,
            "quantity": flow["quantity"],
            "unit_price": flow["unit_price"],
            "unit": "kg",
            "delivery_date": (datetime.now() + timedelta(days=30 + i*7)).date().isoformat(),
            "delivery_location": f"Port of {flow['to'].replace('_', ' ').title()}",
            "notes": f"Supply chain PO {i+1}: {flow['from']} to {flow['to']}"
        }
        
        print(f"  📋 Creating {flow['po_number']}: {flow['from']} → {flow['to']}")
        response = requests.post(f"{BASE_URL}/api/v1/purchase-orders/", json=po_data, headers=buyer_headers)
        
        if response.status_code == 200:
            po = response.json()
            created_pos.append(po)
            print(f"    ✅ PO Created: {po.get('id', 'Unknown ID')}")
        else:
            print(f"    ❌ Failed to create PO: {response.status_code} - {response.text}")
    
    return created_pos

def main():
    """Main function."""
    print("🚀 Creating End-to-End PO Flow for Current Brand")
    print("=" * 60)
    print(f"🏭 Brand Company ID: {BRAND_COMPANY_ID}")
    
    # Step 1: Get products
    print("\n📦 Step 1: Getting Products...")
    products = get_products()
    if not products:
        print("❌ Failed to get products")
        return
    
    # Step 2: Create supply chain companies
    print("\n🏢 Step 2: Creating Supply Chain Companies...")
    companies = create_supply_chain_companies()
    if not companies:
        print("❌ Failed to create companies")
        return
    
    # Step 3: Create purchase order chain
    print("\n🔗 Step 3: Creating Purchase Order Chain...")
    created_pos = create_purchase_order_chain(companies, products)
    if not created_pos:
        print("❌ Failed to create purchase orders")
        return
    
    # Summary
    print("\n🎉 End-to-End Supply Chain Created Successfully!")
    print("=" * 60)
    print("📊 Summary:")
    print(f"  🏭 Brand Company: {BRAND_COMPANY_ID}")
    print(f"  🏢 Supply Chain Companies: {len(companies)}")
    print(f"  📦 Products: {len(products)}")
    print(f"  📋 Purchase Orders: {len(created_pos)}")
    
    print("\n🌱 Complete Traceability Available:")
    print("  Brand → Trader → Refinery → Mill → Plantation")
    
    print("\n💡 You can now:")
    print("  - View your outgoing purchase orders in the dashboard")
    print("  - Trace the complete supply chain")
    print("  - See transformation tracking")
    print("  - Access origin data and certifications")

if __name__ == "__main__":
    main()



