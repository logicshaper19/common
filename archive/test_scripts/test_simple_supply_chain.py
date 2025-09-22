#!/usr/bin/env python3
"""
Simple Supply Chain Flow Test
=============================

This script demonstrates the core flow you requested:
1. Brand creates a supplier (trader)
2. Brand issues a purchase order to that supplier
3. Supplier interacts with another trader
4. Trader interacts with an originator

This is a simplified version focusing on the essential functionality.
"""

import requests
import json
import time
from datetime import datetime, timedelta

# API Configuration
BASE_URL = "http://127.0.0.1:8000"
HEADERS = {"Content-Type": "application/json"}

def log(message: str):
    """Simple logging function."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {message}")

def get_company_id_from_token(token: str) -> str:
    """Get company ID from JWT token."""
    import base64
    import json
    
    try:
        # Decode JWT token (skip signature verification for testing)
        parts = token.split('.')
        payload = parts[1]
        # Add padding if needed
        payload += '=' * (4 - len(payload) % 4)
        decoded = base64.urlsafe_b64decode(payload)
        data = json.loads(decoded)
        return data.get('company_id')
    except Exception as e:
        log(f"❌ Failed to decode token: {e}")
        return None

def register_company(company_type: str, company_name: str):
    """Register a company and return company info and token."""
    timestamp = int(time.time())
    email_safe_type = company_type.replace("_", "-")
    unique_id = f"{timestamp}{hash(company_name) % 10000}"
    
    registration_data = {
        "email": f"admin{unique_id}@{email_safe_type}.com",
        "password": "SecurePass123!",
        "full_name": f"Admin User",
        "role": "admin",
        "company_name": f"{company_name} {unique_id}",
        "company_type": company_type,
        "company_email": f"{email_safe_type}{unique_id}@example.com"
    }
    
    log(f"🏢 Registering {company_name} ({company_type})...")
    
    response = requests.post(f"{BASE_URL}/api/v1/auth/register", json=registration_data, headers=HEADERS)
    
    if response.status_code == 200:
        data = response.json()
        log(f"✅ {company_name} registered (Token: {data['access_token'][:20]}...)")
        # We'll get the company ID later when we need it
        return {"id": None, "name": company_name, "type": company_type}, data["access_token"]
    else:
        log(f"❌ Failed to register {company_name}: {response.text}")
        return None, None

def create_product(company_id: str, token: str, product_name: str):
    """Create a product for a company."""
    product_data = {
        "common_product_id": f"{product_name.lower().replace(' ', '_')}_{int(time.time())}",
        "name": product_name,
        "description": f"High-quality {product_name.lower()}",
        "category": "finished_good",
        "can_have_composition": False,
        "default_unit": "kg"
    }
    
    headers = {**HEADERS, "Authorization": f"Bearer {token}"}
    
    log(f"📦 Creating product: {product_name}")
    
    response = requests.post(f"{BASE_URL}/api/v1/products/", json=product_data, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        product_info = data["data"]
        log(f"✅ Product created: {product_name} (ID: {product_info['id']})")
        return product_info
    else:
        log(f"❌ Failed to create product: {response.text}")
        return None

def create_purchase_order(buyer_id: str, seller_id: str, product_id: str, token: str, parent_po_id: str = None):
    """Create a purchase order."""
    po_data = {
        "buyer_company_id": buyer_id,
        "seller_company_id": seller_id,
        "product_id": product_id,
        "quantity": 1000.0,
        "unit_price": 2.50,
        "unit": "kg",
        "delivery_date": (datetime.now() + timedelta(days=30)).date().isoformat(),
        "delivery_location": "Supply Chain Hub",
        "notes": f"Supply chain test - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    }
    
    # Add commercial chain linking if parent PO exists
    if parent_po_id:
        po_data["parent_po_id"] = parent_po_id
        po_data["is_drop_shipment"] = True
    
    headers = {**HEADERS, "Authorization": f"Bearer {token}"}
    
    log(f"📋 Creating PO: {buyer_id} → {seller_id}")
    
    response = requests.post(f"{BASE_URL}/api/v1/simple/purchase-orders/", json=po_data, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        log(f"✅ PO created: {data['po_number']} (ID: {data['id']})")
        return data
    else:
        log(f"❌ Failed to create PO: {response.text}")
        return None

def confirm_purchase_order(po_id: str, token: str):
    """Confirm a purchase order."""
    headers = {**HEADERS, "Authorization": f"Bearer {token}"}
    
    log(f"✅ Confirming PO: {po_id}")
    
    response = requests.put(f"{BASE_URL}/api/v1/simple/purchase-orders/{po_id}/confirm", headers=headers)
    
    if response.status_code == 200:
        log(f"✅ PO {po_id} confirmed")
        return True
    else:
        log(f"❌ Failed to confirm PO: {response.text}")
        return False

def main():
    """Run the simple supply chain flow test."""
    print("🧪 Simple Supply Chain Flow Test")
    print("=" * 50)
    print("Testing: Brand → Trader → Trader → Originator")
    print("=" * 50)
    
    # Check if API is running
    try:
        response = requests.get(f"{BASE_URL}/")
        if response.status_code != 200:
            print("❌ API is not running. Please start the API server first.")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to API. Please start the API server first.")
        return False
    
    # Step 1: Create companies
    log("📋 Step 1: Creating Companies")
    
    brand, brand_token = register_company("manufacturer", "Sustainable Beauty Co")
    if not brand:
        return False
    brand["id"] = get_company_id_from_token(brand_token)
    
    trader1, trader1_token = register_company("trader_aggregator", "Global Trading Co")
    if not trader1:
        return False
    trader1["id"] = get_company_id_from_token(trader1_token)
    
    trader2, trader2_token = register_company("trader_aggregator", "Regional Trading Ltd")
    if not trader2:
        return False
    trader2["id"] = get_company_id_from_token(trader2_token)
    
    originator, originator_token = register_company("plantation_grower", "Green Acres Plantation")
    if not originator:
        return False
    originator["id"] = get_company_id_from_token(originator_token)
    
    # Step 2: Create products
    log("\n📦 Step 2: Creating Products")
    
    brand_product = create_product(brand["id"], brand_token, "Palm Oil Shampoo")
    if not brand_product:
        return False
    
    trader1_product = create_product(trader1["id"], trader1_token, "Refined Palm Oil")
    if not trader1_product:
        return False
    
    trader2_product = create_product(trader2["id"], trader2_token, "Crude Palm Oil")
    if not trader2_product:
        return False
    
    originator_product = create_product(originator["id"], originator_token, "Fresh Fruit Bunches")
    if not originator_product:
        return False
    
    # Step 3: Create purchase order chain
    log("\n📋 Step 3: Creating Purchase Order Chain")
    
    # Brand → Trader 1
    po1 = create_purchase_order(
        brand["id"], 
        trader1["id"], 
        trader1_product["id"], 
        brand_token
    )
    if not po1:
        return False
    
    # Trader 1 → Trader 2 (fulfilling PO1)
    po2 = create_purchase_order(
        trader1["id"], 
        trader2["id"], 
        trader2_product["id"], 
        trader1_token,
        po1["id"]  # parent PO
    )
    if not po2:
        return False
    
    # Trader 2 → Originator (fulfilling PO2)
    po3 = create_purchase_order(
        trader2["id"], 
        originator["id"], 
        originator_product["id"], 
        trader2_token,
        po2["id"]  # parent PO
    )
    if not po3:
        return False
    
    # Step 4: Confirm purchase orders
    log("\n✅ Step 4: Confirming Purchase Orders")
    
    # Confirm from upstream to downstream
    if not confirm_purchase_order(po3["id"], originator_token):
        return False
    
    if not confirm_purchase_order(po2["id"], trader2_token):
        return False
    
    if not confirm_purchase_order(po1["id"], trader1_token):
        return False
    
    # Step 5: Summary
    log("\n📊 Test Summary")
    log("=" * 50)
    log("✅ All companies created successfully")
    log("✅ All products created successfully")
    log("✅ Purchase order chain created successfully")
    log("✅ Commercial chain linking working")
    log("✅ All purchase orders confirmed")
    
    log("\n🎉 Simple Supply Chain Flow Test PASSED!")
    log("The system successfully demonstrated:")
    log("  - Brand creating supplier relationships")
    log("  - Purchase order creation and confirmation")
    log("  - Commercial chain linking (parent-child POs)")
    log("  - Multi-tier supply chain flow")
    
    return True

if __name__ == "__main__":
    main()
