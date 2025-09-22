#!/usr/bin/env python3
"""
Test script for the enhanced PO confirmation flow with harvest batch selection.
This script tests the complete flow from harvest declaration to PO confirmation with batch linking.
"""

import requests
import json
import time
from datetime import datetime, date
from typing import Dict, Any

# API Configuration
API_BASE_URL = "http://127.0.0.1:8000"
API_VERSION = "v1"

def make_request(method: str, endpoint: str, data: Dict[str, Any] = None, headers: Dict[str, str] = None) -> Dict[str, Any]:
    """Make HTTP request to API."""
    url = f"{API_BASE_URL}/api/{endpoint}"
    
    try:
        if method.upper() == "GET":
            response = requests.get(url, headers=headers)
        elif method.upper() == "POST":
            response = requests.post(url, json=data, headers=headers)
        elif method.upper() == "PUT":
            response = requests.put(url, json=data, headers=headers)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")
        
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response: {e.response.text}")
        return {}

def login_user(email: str, password: str) -> str:
    """Login user and return access token."""
    print(f"🔐 Logging in user: {email}")
    
    login_data = {
        "email": email,
        "password": password
    }
    
    response = make_request("POST", f"{API_VERSION}/auth/login", login_data)
    
    if "access_token" in response:
        print(f"✅ Login successful for {email}")
        return response["access_token"]
    else:
        print(f"❌ Login failed for {email}: {response}")
        return ""

def get_headers(token: str) -> Dict[str, str]:
    """Get headers with authorization token."""
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

def declare_harvest(token: str, company_name: str) -> Dict[str, Any]:
    """Declare a harvest batch."""
    print(f"🌱 Declaring harvest for {company_name}")
    
    # Get products first to find FFB product ID
    products_response = make_request("GET", f"{API_VERSION}/products", headers=get_headers(token))
    ffb_product = None
    
    # Handle different response structures
    products_list = []
    if isinstance(products_response, list):
        products_list = products_response
    elif "data" in products_response:
        products_list = products_response["data"]
    elif "products" in products_response:
        products_list = products_response["products"]
    
    for product in products_list:
        if isinstance(product, dict):
            product_name = product.get("name", "").lower()
            if "fresh fruit bunch" in product_name or "ffb" in product_name:
                ffb_product = product
                break
    
    if not ffb_product:
        print("❌ FFB product not found, using default product ID")
        # Use a default product ID if FFB not found
        ffb_product = {"id": "550e8400-e29b-41d4-a716-446655440000"}
    
    harvest_data = {
        "product_id": ffb_product["id"],
        "batch_number": f"FFB-{company_name.replace(' ', '').upper()}-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "quantity": 1000.0,
        "unit": "KGM",
        "harvest_date": date.today().isoformat(),
        "geographic_coordinates": {
            "latitude": 3.1390 + (hash(company_name) % 100) / 10000,  # Slightly different coordinates per company
            "longitude": 101.6869 + (hash(company_name) % 100) / 10000,
            "accuracy_meters": 5
        },
        "farm_information": {
            "farm_id": f"FARM-{company_name.replace(' ', '').upper()}-001",
            "farm_name": f"{company_name} Main Farm",
            "plantation_type": "smallholder" if "cooperative" in company_name.lower() else "estate",
            "cultivation_methods": ["organic", "sustainable"]
        },
        "quality_parameters": {
            "oil_content": 22.5,
            "moisture_content": 25.0,
            "free_fatty_acid": 3.2,
            "dirt_content": 2.1,
            "kernel_to_fruit_ratio": 0.15
        },
        "certifications": ["RSPO", "MSPO"],
        "processing_notes": f"High quality FFB from {company_name} sustainable farming practices"
    }
    
    response = make_request("POST", "harvest/declare", harvest_data, get_headers(token))
    
    if "id" in response:
        print(f"✅ Harvest declared successfully: {response['batch_id']}")
        return response
    else:
        print(f"❌ Harvest declaration failed: {response}")
        return {}

def get_harvest_batches(token: str) -> list:
    """Get harvest batches for the current user."""
    print("📋 Fetching harvest batches...")
    
    response = make_request("GET", "harvest/batches", headers=get_headers(token))
    
    if "batches" in response:
        batches = response["batches"]
        print(f"✅ Found {len(batches)} harvest batches")
        return batches
    else:
        print(f"❌ Failed to fetch harvest batches: {response}")
        return []

def create_purchase_order(token: str, seller_company_id: str, product_id: str) -> Dict[str, Any]:
    """Create a purchase order."""
    print(f"📝 Creating purchase order to seller: {seller_company_id}")
    
    po_data = {
        "seller_company_id": seller_company_id,
        "product_id": product_id,
        "quantity": 500.0,
        "unit": "KGM",
        "unit_price": 450.0,
        "delivery_date": (datetime.now().replace(day=datetime.now().day + 7)).isoformat(),
        "delivery_location": "Kuala Lumpur Port",
        "notes": "Test PO for enhanced confirmation flow"
    }
    
    response = make_request("POST", f"{API_VERSION}/purchase_orders/", po_data, get_headers(token))
    
    if "id" in response:
        print(f"✅ Purchase order created: {response['po_number']}")
        return response
    else:
        print(f"❌ Purchase order creation failed: {response}")
        return {}

def confirm_purchase_order_with_batch(token: str, po_id: str, batch_id: str) -> Dict[str, Any]:
    """Confirm purchase order with harvest batch linking."""
    print(f"✅ Confirming PO {po_id} with batch {batch_id}")
    
    confirmation_data = {
        "confirmed_quantity": 500.0,
        "confirmed_unit_price": 450.0,
        "delivery_date": (datetime.now().replace(day=datetime.now().day + 7)).isoformat(),
        "delivery_location": "Kuala Lumpur Port",
        "notes": "Confirmed with harvest batch linking",
        "linked_batch_id": batch_id
    }
    
    response = make_request("PUT", f"{API_VERSION}/purchase_orders/{po_id}/confirm", confirmation_data, get_headers(token))
    
    if "message" in response:
        print(f"✅ PO confirmed successfully: {response['message']}")
        return response
    else:
        print(f"❌ PO confirmation failed: {response}")
        return {}

def test_enhanced_po_confirmation_flow():
    """Test the complete enhanced PO confirmation flow."""
    print("🚀 Testing Enhanced PO Confirmation Flow")
    print("=" * 60)
    
    # Step 1: Login as Tani Maju Cooperative (originator)
    tani_token = login_user("manager@tanimaju.com", "SmallholderCoop2024!")
    if not tani_token:
        print("❌ Cannot proceed without Tani Maju login")
        return
    
    # Step 2: Declare harvest batch
    harvest_result = declare_harvest(tani_token, "Tani Maju Cooperative")
    if not harvest_result:
        print("❌ Cannot proceed without harvest batch")
        return
    
    # Step 3: Get harvest batches to verify
    batches = get_harvest_batches(tani_token)
    if not batches:
        print("❌ No harvest batches found")
        return
    
    # Step 4: Login as Wilmar Trading (buyer)
    wilmar_token = login_user("manager@wilmar.com", "TraderAggregator2024!")
    if not wilmar_token:
        print("❌ Cannot proceed without Wilmar login")
        return
    
    # Step 5: Get Tani Maju company ID for PO creation
    companies_response = make_request("GET", f"{API_VERSION}/companies?for_supplier_selection=true", headers=get_headers(wilmar_token))
    tani_company_id = None
    
    if "data" in companies_response:
        for company in companies_response["data"]:
            if "Tani Maju" in company.get("name", ""):
                tani_company_id = company["id"]
                break
    
    if not tani_company_id:
        print("❌ Tani Maju company not found in supplier list")
        return
    
    # Step 6: Get FFB product ID
    products_response = make_request("GET", f"{API_VERSION}/products", headers=get_headers(wilmar_token))
    ffb_product_id = None
    
    # Handle different response structures
    products_list = []
    if isinstance(products_response, list):
        products_list = products_response
    elif "data" in products_response:
        products_list = products_response["data"]
    elif "products" in products_response:
        products_list = products_response["products"]
    
    for product in products_list:
        if isinstance(product, dict):
            product_name = product.get("name", "").lower()
            if "fresh fruit bunch" in product_name or "ffb" in product_name:
                ffb_product_id = product["id"]
                break
    
    if not ffb_product_id:
        print("❌ FFB product not found, using default product ID")
        ffb_product_id = "550e8400-e29b-41d4-a716-446655440000"
    
    # Step 7: Create purchase order from Wilmar to Tani Maju
    po_result = create_purchase_order(wilmar_token, tani_company_id, ffb_product_id)
    if not po_result:
        print("❌ Cannot proceed without purchase order")
        return
    
    # Step 8: Login back as Tani Maju to confirm PO
    tani_token = login_user("manager@tanimaju.com", "SmallholderCoop2024!")
    
    # Step 9: Get harvest batches again for confirmation
    batches = get_harvest_batches(tani_token)
    if not batches:
        print("❌ No harvest batches available for confirmation")
        return
    
    # Step 10: Confirm PO with batch linking
    confirmation_result = confirm_purchase_order_with_batch(
        tani_token, 
        po_result["id"], 
        batches[0]["id"]
    )
    
    if confirmation_result:
        print("\n🎉 Enhanced PO Confirmation Flow Test Completed Successfully!")
        print("=" * 60)
        print("✅ Harvest batch declared")
        print("✅ Purchase order created")
        print("✅ PO confirmed with harvest batch linking")
        print("✅ Origin data should now be linked to the PO")
    else:
        print("\n❌ Enhanced PO Confirmation Flow Test Failed")
        print("=" * 60)

if __name__ == "__main__":
    test_enhanced_po_confirmation_flow()
