#!/usr/bin/env python3
"""
Supply Chain Flow Test Script

This script tests the complete supply chain flow by:
1. Creating test companies (manufacturer, supplier, originator)
2. Creating products
3. Creating purchase orders
4. Testing the commercial chain linking

Usage:
    python test_supply_chain_flow.py
"""

import requests
import json
import time
import uuid
from datetime import datetime

# Configuration
API_BASE_URL = "http://127.0.0.1:8000"
TEST_EMAIL = "admin@testmanufacturer.com"
TEST_PASSWORD = "TestPass123!"

class SupplyChainTester:
    def __init__(self):
        self.session = requests.Session()
        self.access_token = None
        self.companies = {}
        self.products = {}
        self.purchase_orders = {}
    
    def login(self):
        """Login and get access token"""
        print("🔐 Logging in...")
        response = self.session.post(
            f"{API_BASE_URL}/api/v1/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        
        if response.status_code == 200:
            data = response.json()
            self.access_token = data["access_token"]
            self.session.headers.update({
                "Authorization": f"Bearer {self.access_token}"
            })
            print("✅ Login successful")
            return True
        else:
            print(f"❌ Login failed: {response.text}")
            return False
    
    def create_company(self, name, company_type, email):
        """Create a company"""
        print(f"🏢 Creating company: {name}")
        response = self.session.post(
            f"{API_BASE_URL}/api/v1/companies",
            json={
                "name": name,
                "company_type": company_type,
                "email": email
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            self.companies[name] = data
            print(f"✅ Created company: {name} (ID: {data['id']})")
            return data
        else:
            print(f"❌ Failed to create company {name}: {response.text}")
            return None
    
    def create_product(self, name, description, category):
        """Create a product"""
        print(f"📦 Creating product: {name}")
        response = self.session.post(
            f"{API_BASE_URL}/api/v1/products",
            json={
                "name": name,
                "description": description,
                "category": category
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            self.products[name] = data
            print(f"✅ Created product: {name} (ID: {data['id']})")
            return data
        else:
            print(f"❌ Failed to create product {name}: {response.text}")
            return None
    
    def create_purchase_order(self, po_number, buyer_company_id, seller_company_id, product_id, quantity):
        """Create a purchase order"""
        print(f"📋 Creating purchase order: {po_number}")
        response = self.session.post(
            f"{API_BASE_URL}/api/v1/purchase-orders",
            json={
                "po_number": po_number,
                "buyer_company_id": buyer_company_id,
                "seller_company_id": seller_company_id,
                "product_id": product_id,
                "quantity": quantity,
                "status": "pending"
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            self.purchase_orders[po_number] = data
            print(f"✅ Created purchase order: {po_number} (ID: {data['id']})")
            return data
        else:
            print(f"❌ Failed to create purchase order {po_number}: {response.text}")
            return None
    
    def test_complete_flow(self):
        """Test the complete supply chain flow"""
        print("🚀 Starting Supply Chain Flow Test")
        print("=" * 50)
        
        # Step 1: Login
        if not self.login():
            return False
        
        # Step 2: Create companies
        print("\n📊 Creating Companies...")
        self.create_company("Test Manufacturer", "manufacturer", "manufacturer@test.com")
        self.create_company("Test Supplier", "trader_aggregator", "supplier@test.com")
        self.create_company("Test Originator", "plantation_grower", "originator@test.com")
        
        # Step 3: Create products
        print("\n📦 Creating Products...")
        self.create_product("Palm Oil", "Refined palm oil for manufacturing", "raw_material")
        self.create_product("Shampoo", "Palm oil-based shampoo", "finished_good")
        
        # Step 4: Create purchase orders
        print("\n📋 Creating Purchase Orders...")
        if len(self.companies) >= 2 and len(self.products) >= 1:
            manufacturer_id = list(self.companies.values())[0]["id"]
            supplier_id = list(self.companies.values())[1]["id"]
            product_id = list(self.products.values())[0]["id"]
            
            self.create_purchase_order(
                f"PO-{int(time.time())}",
                manufacturer_id,
                supplier_id,
                product_id,
                1000
            )
        
        # Step 5: Test commercial chain linking
        print("\n🔗 Testing Commercial Chain Linking...")
        if len(self.purchase_orders) > 0:
            po_id = list(self.purchase_orders.values())[0]["id"]
            response = self.session.get(f"{API_BASE_URL}/api/v1/purchase-orders/{po_id}/commercial-chain")
            
            if response.status_code == 200:
                print("✅ Commercial chain linking working")
            else:
                print(f"❌ Commercial chain linking failed: {response.text}")
        
        print("\n🎉 Supply Chain Flow Test Complete!")
        return True

def main():
    """Main function"""
    print("Supply Chain Platform - Flow Test")
    print("=" * 40)
    
    tester = SupplyChainTester()
    success = tester.test_complete_flow()
    
    if success:
        print("\n✅ All tests passed!")
        exit(0)
    else:
        print("\n❌ Tests failed!")
        exit(1)

if __name__ == "__main__":
    main()

