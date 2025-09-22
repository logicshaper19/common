#!/usr/bin/env python3
"""
Test the enhanced PO confirmation flow with existing harvest batches.
"""

import requests
import json
from datetime import datetime, date

# API Configuration
API_BASE_URL = "http://127.0.0.1:8000"
API_VERSION = "v1"

def make_request(method: str, endpoint: str, data: dict = None, headers: dict = None) -> dict:
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
            print(f"Status Code: {e.response.status_code}")
            print(f"Headers: {dict(e.response.headers)}")
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

def get_headers(token: str) -> dict:
    """Get headers with authorization token."""
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

def get_harvest_batches(token: str) -> list:
    """Get harvest batches for the current user."""
    print("📋 Fetching harvest batches...")
    
    response = make_request("GET", "harvest/batches", headers=get_headers(token))
    
    if "batches" in response:
        batches = response["batches"]
        print(f"✅ Found {len(batches)} harvest batches")
        for batch in batches:
            print(f"   - {batch['batch_id']}: {batch['quantity']} {batch['unit']} from {batch.get('origin_data', {}).get('farm_information', {}).get('farm_name', 'Unknown Farm')}")
        return batches
    else:
        print(f"❌ Failed to fetch harvest batches: {response}")
        return []

def create_purchase_order(token: str, seller_company_id: str, product_id: str) -> dict:
    """Create a purchase order."""
    print(f"📝 Creating purchase order to seller: {seller_company_id}")
    
    # Get current user's company ID
    user_response = make_request("GET", f"{API_VERSION}/auth/me", headers=get_headers(token))
    buyer_company_id = user_response.get("company", {}).get("id") if user_response else None
    
    if not buyer_company_id:
        print("❌ Could not get buyer company ID")
        print(f"User response: {user_response}")
        return {}
    
    po_data = {
        "buyer_company_id": buyer_company_id,
        "seller_company_id": seller_company_id,
        "product_id": product_id,
        "quantity": 500.0,
        "unit": "KGM",
        "unit_price": 450.0,
        "delivery_date": (datetime.now().replace(day=datetime.now().day + 7)).date().isoformat(),
        "delivery_location": "Kuala Lumpur Port",
        "notes": "Test PO for enhanced confirmation flow with harvest batch linking"
    }
    
    response = make_request("POST", f"{API_VERSION}/purchase-orders/", po_data, get_headers(token))
    
    if "id" in response:
        print(f"✅ Purchase order created: {response['po_number']}")
        return response
    else:
        print(f"❌ Purchase order creation failed: {response}")
        return {}

def confirm_purchase_order_with_batch(token: str, po_id: str, batch_id: str) -> dict:
    """Confirm purchase order with harvest batch linking."""
    print(f"✅ Confirming PO {po_id} with batch {batch_id}")
    
    confirmation_data = {
        "confirmed_quantity": 500.0,
        "confirmed_unit_price": 450.0,
        "delivery_date": (datetime.now().replace(day=datetime.now().day + 7)).date().isoformat(),
        "delivery_location": "Kuala Lumpur Port",
        "notes": "Confirmed with harvest batch linking",
        "stock_batches": [{"batch_id": batch_id, "quantity": 1000.0}]
    }
    
    url = f"{API_VERSION}/purchase-orders/{po_id}/confirm"
    print(f"DEBUG: Calling URL: {url}")
    print(f"DEBUG: Confirmation data: {confirmation_data}")
    response = make_request("POST", url, confirmation_data, get_headers(token))
    
    if "message" in response:
        print(f"✅ PO confirmed successfully: {response['message']}")
        return response
    else:
        print(f"❌ PO confirmation failed: {response}")
        return {}

def test_enhanced_po_confirmation_flow():
    """Test the complete enhanced PO confirmation flow."""
    print("🚀 Testing Enhanced PO Confirmation Flow with Harvest Batch Linking")
    print("=" * 70)
    
    # Step 1: Login as Tani Maju Cooperative (originator)
    tani_token = login_user("manager@tanimaju.com", "SmallholderCoop2024!")
    if not tani_token:
        print("❌ Cannot proceed without Tani Maju login")
        return
    
    # Step 2: Get existing harvest batches
    batches = get_harvest_batches(tani_token)
    if not batches:
        print("❌ No harvest batches found")
        return
    
    # Step 3: Login as Wilmar Trading (buyer)
    wilmar_token = login_user("manager@wilmar.com", "TraderAggregator2024!")
    if not wilmar_token:
        print("❌ Cannot proceed without Wilmar login")
        return
    
    # Step 4: Get Tani Maju company ID for PO creation
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
    
    # Step 5: Get FFB product ID
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
        ffb_product_id = "9c9b1034-a4c8-4e62-a3c4-2654007fca4d"  # Known FFB product ID
    
    # Step 6: Create purchase order from Wilmar to Tani Maju
    po_result = create_purchase_order(wilmar_token, tani_company_id, ffb_product_id)
    if not po_result:
        print("❌ Cannot proceed without purchase order")
        return
    
    # Step 7: Login back as Tani Maju to confirm PO
    tani_token = login_user("manager@tanimaju.com", "SmallholderCoop2024!")
    
    # Step 8: Get harvest batches again for confirmation
    batches = get_harvest_batches(tani_token)
    if not batches:
        print("❌ No harvest batches available for confirmation")
        return
    
    # Step 9: Confirm PO with batch linking
    confirmation_result = confirm_purchase_order_with_batch(
        tani_token, 
        po_result["id"], 
        batches[0]["id"]
    )
    
    if confirmation_result:
        print("\n🎉 Enhanced PO Confirmation Flow Test Completed Successfully!")
        print("=" * 70)
        print("✅ Harvest batches retrieved")
        print("✅ Purchase order created")
        print("✅ PO confirmed with harvest batch linking")
        print("✅ Origin data should now be linked to the PO")
        print(f"✅ Linked batch: {batches[0]['batch_id']} from {batches[0].get('origin_data', {}).get('farm_information', {}).get('farm_name', 'Unknown Farm')}")
    else:
        print("\n❌ Enhanced PO Confirmation Flow Test Failed")
        print("=" * 70)

if __name__ == "__main__":
    test_enhanced_po_confirmation_flow()
