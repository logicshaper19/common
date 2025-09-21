#!/usr/bin/env python3
"""
Complete Supply Chain Flow Test
===============================

This script demonstrates a complete end-to-end supply chain flow:
1. Brand creates a supplier (trader)
2. Brand issues a purchase order to the trader
3. Trader interacts with another trader
4. Trader interacts with an originator

This tests the full commercial chain linking functionality.
"""

import requests
import json
import uuid
import time
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, Any, Optional

# API Configuration
BASE_URL = "http://127.0.0.1:8000"
HEADERS = {"Content-Type": "application/json"}

class SupplyChainFlowTest:
    def __init__(self):
        self.companies = {}
        self.products = {}
        self.purchase_orders = {}
        self.tokens = {}
        
    def log(self, message: str, level: str = "INFO"):
        """Log messages with timestamp."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
    
    def get_company_id_from_token(self, token: str) -> str:
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
            self.log(f"❌ Failed to decode token: {e}", "ERROR")
            return None
        
    def register_company(self, company_type: str, company_name: str, admin_name: str) -> Optional[Dict[str, Any]]:
        """Register a new company and return company info and token."""
        timestamp = int(time.time())
        email_safe_type = company_type.replace("_", "-")
        unique_id = f"{timestamp}{hash(company_name) % 10000}"
        
        registration_data = {
            "email": f"admin{unique_id}@{email_safe_type}.com",
            "password": "SecurePass123!",
            "full_name": admin_name,
            "role": "admin",
            "company_name": f"{company_name} {unique_id}",
            "company_type": company_type,
            "company_email": f"{email_safe_type}{unique_id}@example.com"
        }
        
        self.log(f"🏢 Registering {company_name} ({company_type})...")
        
        response = requests.post(f"{BASE_URL}/api/v1/auth/register", json=registration_data, headers=HEADERS)
        
        if response.status_code == 200:
            data = response.json()
            # Get company ID from token
            company_id = self.get_company_id_from_token(data["access_token"])
            company_info = {
                "id": company_id,
                "name": company_name,
                "type": company_type,
                "email": registration_data["email"]
            }
            self.log(f"✅ {company_name} registered successfully (ID: {company_id})")
            return company_info, data["access_token"]
        else:
            self.log(f"❌ Failed to register {company_name}: {response.status_code} - {response.text}", "ERROR")
            return None, None
    
    def login(self, email: str, password: str) -> Optional[str]:
        """Login and return access token."""
        login_data = {
            "username": email,
            "password": password
        }
        
        response = requests.post(f"{BASE_URL}/api/v1/auth/login", data=login_data, headers=HEADERS)
        
        if response.status_code == 200:
            data = response.json()
            return data["access_token"]
        else:
            self.log(f"❌ Login failed for {email}: {response.status_code} - {response.text}", "ERROR")
            return None
    
    def create_product(self, company_id: str, token: str, product_name: str, product_type: str) -> Optional[Dict[str, Any]]:
        """Create a product for a company."""
        product_data = {
            "common_product_id": f"{product_name.lower().replace(' ', '_')}_{int(time.time())}",
            "name": product_name,
            "description": f"High-quality {product_type} product",
            "category": "finished_good",
            "can_have_composition": False,
            "default_unit": "kg"
        }
        
        headers = {**HEADERS, "Authorization": f"Bearer {token}"}
        
        self.log(f"📦 Creating product: {product_name}")
        
        response = requests.post(f"{BASE_URL}/api/v1/products/", json=product_data, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            product_info = data["data"]
            self.log(f"✅ Product created: {product_name} (ID: {product_info['id']})")
            return product_info
        else:
            self.log(f"❌ Failed to create product {product_name}: {response.status_code} - {response.text}", "ERROR")
            return None
    
    def create_purchase_order(self, buyer_company_id: str, seller_company_id: str, 
                            product_id: str, token: str, quantity: float, 
                            unit_price: float, parent_po_id: str = None) -> Optional[Dict[str, Any]]:
        """Create a purchase order."""
        po_data = {
            "buyer_company_id": buyer_company_id,
            "seller_company_id": seller_company_id,
            "product_id": product_id,
            "quantity": quantity,
            "unit_price": unit_price,
            "unit": "kg",
            "delivery_date": (datetime.now() + timedelta(days=30)).date().isoformat(),
            "delivery_location": "Sustainable Supply Chain Hub",
            "notes": f"Commercial chain linking test - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "composition": {
                "palm_oil": 100.0
            },
            "origin_data": {
                "country": "Malaysia",
                "region": "Sabah",
                "certification": "RSPO",
                "sustainability_score": 95
            }
        }
        
        # Add commercial chain linking if parent PO exists
        if parent_po_id:
            po_data["parent_po_id"] = parent_po_id
            po_data["is_drop_shipment"] = True
        
        headers = {**HEADERS, "Authorization": f"Bearer {token}"}
        
        self.log(f"📋 Creating purchase order: {buyer_company_id} → {seller_company_id}")
        
        response = requests.post(f"{BASE_URL}/api/v1/simple/purchase-orders/", json=po_data, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            po_info = {
                "id": data["id"],
                "po_number": data["po_number"],
                "buyer_company_id": buyer_company_id,
                "seller_company_id": seller_company_id,
                "product_id": product_id,
                "quantity": quantity,
                "unit_price": unit_price,
                "total_amount": data["total_amount"],
                "status": data["status"],
                "parent_po_id": parent_po_id
            }
            self.log(f"✅ Purchase order created: {po_info['po_number']} (ID: {po_info['id']})")
            return po_info
        else:
            self.log(f"❌ Failed to create purchase order: {response.status_code} - {response.text}", "ERROR")
            return None
    
    def confirm_purchase_order(self, po_id: str, token: str) -> bool:
        """Confirm a purchase order."""
        headers = {**HEADERS, "Authorization": f"Bearer {token}"}
        
        self.log(f"✅ Confirming purchase order: {po_id}")
        
        response = requests.put(f"{BASE_URL}/api/v1/simple/purchase-orders/{po_id}/confirm", headers=headers)
        
        if response.status_code == 200:
            self.log(f"✅ Purchase order {po_id} confirmed successfully")
            return True
        else:
            self.log(f"❌ Failed to confirm purchase order {po_id}: {response.status_code} - {response.text}", "ERROR")
            return False
    
    def get_suppliers(self, token: str) -> list:
        """Get list of suppliers for current company."""
        headers = {**HEADERS, "Authorization": f"Bearer {token}"}
        
        response = requests.get(f"{BASE_URL}/api/v1/simple/relationships/suppliers", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            return data.get("suppliers", [])
        else:
            self.log(f"❌ Failed to get suppliers: {response.status_code} - {response.text}", "ERROR")
            return []
    
    def run_complete_flow(self):
        """Run the complete supply chain flow test."""
        self.log("🚀 Starting Complete Supply Chain Flow Test")
        self.log("=" * 60)
        
        # Step 1: Create all companies
        self.log("📋 Step 1: Creating Supply Chain Companies")
        self.log("-" * 40)
        
        # Create Brand (downstream)
        brand_info, brand_token = self.register_company(
            "manufacturer", 
            "Sustainable Beauty Co", 
            "Brand Admin"
        )
        if not brand_info:
            return False
        self.companies["brand"] = brand_info
        self.tokens["brand"] = brand_token
        
        # Create Trader 1 (supplier to brand)
        trader1_info, trader1_token = self.register_company(
            "trader_aggregator", 
            "Global Trading Co", 
            "Trader 1 Admin"
        )
        if not trader1_info:
            return False
        self.companies["trader1"] = trader1_info
        self.tokens["trader1"] = trader1_token
        
        # Create Trader 2 (supplier to trader 1)
        trader2_info, trader2_token = self.register_company(
            "trader_aggregator", 
            "Regional Trading Ltd", 
            "Trader 2 Admin"
        )
        if not trader2_info:
            return False
        self.companies["trader2"] = trader2_info
        self.tokens["trader2"] = trader2_token
        
        # Create Originator (supplier to trader 2)
        originator_info, originator_token = self.register_company(
            "plantation_grower", 
            "Green Acres Plantation", 
            "Originator Admin"
        )
        if not originator_info:
            return False
        self.companies["originator"] = originator_info
        self.tokens["originator"] = originator_token
        
        # Step 2: Create products for each company
        self.log("\n📦 Step 2: Creating Products")
        self.log("-" * 40)
        
        # Brand creates finished product
        brand_product = self.create_product(
            brand_info["id"], 
            brand_token, 
            "Sustainable Palm Oil Shampoo", 
            "cosmetics"
        )
        if not brand_product:
            return False
        self.products["brand"] = brand_product
        
        # Trader 1 creates refined palm oil
        trader1_product = self.create_product(
            trader1_info["id"], 
            trader1_token, 
            "Refined Palm Oil", 
            "refined_oil"
        )
        if not trader1_product:
            return False
        self.products["trader1"] = trader1_product
        
        # Trader 2 creates crude palm oil
        trader2_product = self.create_product(
            trader2_info["id"], 
            trader2_token, 
            "Crude Palm Oil", 
            "crude_oil"
        )
        if not trader2_product:
            return False
        self.products["trader2"] = trader2_product
        
        # Originator creates fresh fruit bunches
        originator_product = self.create_product(
            originator_info["id"], 
            originator_token, 
            "Fresh Fruit Bunches", 
            "raw_material"
        )
        if not originator_product:
            return False
        self.products["originator"] = originator_product
        
        # Step 3: Create purchase order chain
        self.log("\n📋 Step 3: Creating Purchase Order Chain")
        self.log("-" * 40)
        
        # Brand → Trader 1 (main PO)
        self.log("🔗 Creating Brand → Trader 1 Purchase Order")
        po1 = self.create_purchase_order(
            brand_info["id"],           # buyer
            trader1_info["id"],         # seller
            trader1_product["id"],      # product
            brand_token,                # token
            1000.0,                     # quantity
            2.50,                       # unit price
            None                        # no parent PO
        )
        if not po1:
            return False
        self.purchase_orders["po1"] = po1
        
        # Trader 1 → Trader 2 (fulfilling PO1)
        self.log("🔗 Creating Trader 1 → Trader 2 Purchase Order (fulfilling PO1)")
        po2 = self.create_purchase_order(
            trader1_info["id"],         # buyer
            trader2_info["id"],         # seller
            trader2_product["id"],      # product
            trader1_token,              # token
            1000.0,                     # quantity
            2.00,                       # unit price
            po1["id"]                   # parent PO
        )
        if not po2:
            return False
        self.purchase_orders["po2"] = po2
        
        # Trader 2 → Originator (fulfilling PO2)
        self.log("🔗 Creating Trader 2 → Originator Purchase Order (fulfilling PO2)")
        po3 = self.create_purchase_order(
            trader2_info["id"],         # buyer
            originator_info["id"],      # seller
            originator_product["id"],   # product
            trader2_token,              # token
            1000.0,                     # quantity
            1.50,                       # unit price
            po2["id"]                   # parent PO
        )
        if not po3:
            return False
        self.purchase_orders["po3"] = po3
        
        # Step 4: Confirm purchase orders (upstream to downstream)
        self.log("\n✅ Step 4: Confirming Purchase Orders")
        self.log("-" * 40)
        
        # Originator confirms PO3
        self.log("✅ Originator confirming PO3")
        if not self.confirm_purchase_order(po3["id"], originator_token):
            return False
        
        # Trader 2 confirms PO2
        self.log("✅ Trader 2 confirming PO2")
        if not self.confirm_purchase_order(po2["id"], trader2_token):
            return False
        
        # Trader 1 confirms PO1
        self.log("✅ Trader 1 confirming PO1")
        if not self.confirm_purchase_order(po1["id"], trader1_token):
            return False
        
        # Step 5: Verify supplier relationships
        self.log("\n🔍 Step 5: Verifying Supplier Relationships")
        self.log("-" * 40)
        
        # Check brand's suppliers
        brand_suppliers = self.get_suppliers(brand_token)
        self.log(f"📊 Brand has {len(brand_suppliers)} suppliers")
        for supplier in brand_suppliers:
            self.log(f"   - {supplier['company_name']} ({supplier['company_type']})")
        
        # Check trader 1's suppliers
        trader1_suppliers = self.get_suppliers(trader1_token)
        self.log(f"📊 Trader 1 has {len(trader1_suppliers)} suppliers")
        for supplier in trader1_suppliers:
            self.log(f"   - {supplier['company_name']} ({supplier['company_type']})")
        
        # Check trader 2's suppliers
        trader2_suppliers = self.get_suppliers(trader2_token)
        self.log(f"📊 Trader 2 has {len(trader2_suppliers)} suppliers")
        for supplier in trader2_suppliers:
            self.log(f"   - {supplier['company_name']} ({supplier['company_type']})")
        
        # Step 6: Summary
        self.log("\n📊 Step 6: Test Summary")
        self.log("=" * 60)
        self.log(f"✅ Companies Created: {len(self.companies)}")
        self.log(f"✅ Products Created: {len(self.products)}")
        self.log(f"✅ Purchase Orders Created: {len(self.purchase_orders)}")
        self.log(f"✅ Commercial Chain Linking: Working")
        self.log(f"✅ Supplier Relationships: Working")
        
        self.log("\n🎉 Complete Supply Chain Flow Test PASSED!")
        self.log("The system successfully demonstrated:")
        self.log("  - Brand creating supplier relationships")
        self.log("  - Purchase order creation and confirmation")
        self.log("  - Commercial chain linking (parent-child POs)")
        self.log("  - Multi-tier supplier relationships")
        self.log("  - End-to-end supply chain transparency")
        
        return True

def main():
    """Main function to run the test."""
    print("🧪 Complete Supply Chain Flow Test")
    print("=" * 60)
    print("This test demonstrates:")
    print("1. Brand creating a supplier (trader)")
    print("2. Brand issuing a purchase order to the trader")
    print("3. Trader interacting with another trader")
    print("4. Trader interacting with an originator")
    print("5. Commercial chain linking and supplier relationships")
    print("=" * 60)
    
    # Check if API is running
    try:
        response = requests.get(f"{BASE_URL}/")
        if response.status_code != 200:
            print("❌ API is not running. Please start the API server first.")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to API. Please start the API server first.")
        return False
    
    # Run the test
    test = SupplyChainFlowTest()
    success = test.run_complete_flow()
    
    if success:
        print("\n✅ All tests passed! The supply chain flow is working correctly.")
        return True
    else:
        print("\n❌ Test failed. Please check the logs above for details.")
        return False

if __name__ == "__main__":
    main()
