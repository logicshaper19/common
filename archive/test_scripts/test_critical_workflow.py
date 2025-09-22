#!/usr/bin/env python3
"""
Comprehensive testing script for critical API workflows.
Based on the engineer's feedback and implementation plan.
"""
import requests
import json
import sys
import uuid
from typing import Dict, Any

BASE_URL = "http://localhost:8000/api/v1"

def get_auth_token(email: str, password: str) -> str:
    """Get authentication token for testing."""
    response = requests.post(f"{BASE_URL}/auth/login", json={
        "email": email,
        "password": password
    })
    
    if response.status_code == 200:
        data = response.json()
        return data["access_token"]
    else:
        print(f"❌ Failed to get token for {email}: {response.status_code}")
        print(f"Response: {response.text}")
        return None

def test_companies_api_returns_list():
    """Test that the /companies API always returns a list, not None."""
    print("🧪 Testing Companies API...")
    
    # Test with L'Oréal user
    token = get_auth_token("sustainability@loreal.com", "password123")
    if not token:
        return False
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/companies/", headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        if isinstance(data.get("data"), list):
            print("✅ Companies API returns a list")
            print(f"   Found {len(data['data'])} companies")
            return True
        else:
            print(f"❌ Companies API data is not a list: {type(data.get('data'))}")
            return False
    else:
        print(f"❌ Companies API failed: {response.status_code}")
        print(f"Response: {response.text}")
        return False

def test_transparency_api_returns_ok():
    """Test that the /transparency API is populated and returns successfully."""
    print("🧪 Testing Transparency API...")
    
    # Test with L'Oréal user
    token = get_auth_token("sustainability@loreal.com", "password123")
    if not token:
        return False
    
    headers = {"Authorization": f"Bearer {token}"}
    company_id = "6ee843c0-2f5a-4f2d-816f-de3379c1f9eb"  # L'Oréal company ID
    
    response = requests.get(f"{BASE_URL}/transparency/v2/companies/{company_id}/metrics", headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        if "transparency_to_mill_percentage" in data.get("data", {}):
            print("✅ Transparency API is populated and working")
            print(f"   Transparency to mill: {data['data']['transparency_to_mill_percentage']}%")
            print(f"   Transparency to plantation: {data['data']['transparency_to_plantation_percentage']}%")
            return True
        else:
            print(f"❌ Transparency API missing expected fields: {data}")
            return False
    else:
        print(f"❌ Transparency API failed: {response.status_code}")
        print(f"Response: {response.text}")
        return False

def test_purchase_orders_api_returns_data():
    """Test that the /purchase-orders API returns the seeded data."""
    print("🧪 Testing Purchase Orders API...")
    
    # Test with L'Oréal user
    token = get_auth_token("sustainability@loreal.com", "password123")
    if not token:
        return False
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/purchase-orders/", headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        if "purchase_orders" in data and len(data["purchase_orders"]) > 0:
            print("✅ Purchase Orders API returns data")
            print(f"   Found {len(data['purchase_orders'])} purchase orders")
            return True
        else:
            print(f"❌ Purchase Orders API has no data: {data}")
            return False
    else:
        print(f"❌ Purchase Orders API failed: {response.status_code}")
        print(f"Response: {response.text}")
        return False

def test_complete_workflow():
    """Test the complete workflow from smallholder to brand."""
    print("🧪 Testing Complete Workflow...")
    
    # Test 1: Smallholder (Koperasi) can log in
    print("   Testing smallholder login...")
    token = get_auth_token("coop@sawitberkelanjutan.co.id", "password123")
    if not token:
        print("❌ Smallholder login failed")
        return False
    print("✅ Smallholder login successful")
    
    # Test 2: Plantation (Astra Agro) can log in
    print("   Testing plantation login...")
    token = get_auth_token("harvest@astra-agro.com", "password123")
    if not token:
        print("❌ Plantation login failed")
        return False
    print("✅ Plantation login successful")
    
    # Test 3: Mill (Sime Darby) can log in
    print("   Testing mill login...")
    token = get_auth_token("millmanager@simeplantation.com", "password123")
    if not token:
        print("❌ Mill login failed")
        return False
    print("✅ Mill login successful")
    
    # Test 4: Refinery (IOI) can log in
    print("   Testing refinery login...")
    token = get_auth_token("refinery@ioigroup.com", "password123")
    if not token:
        print("❌ Refinery login failed")
        return False
    print("✅ Refinery login successful")
    
    # Test 5: Trader (Wilmar) can log in
    print("   Testing trader login...")
    token = get_auth_token("trader@wilmar-intl.com", "password123")
    if not token:
        print("❌ Trader login failed")
        return False
    print("✅ Trader login successful")
    
    # Test 6: Brand (L'Oréal) can log in
    print("   Testing brand login...")
    token = get_auth_token("sustainability@loreal.com", "password123")
    if not token:
        print("❌ Brand login failed")
        return False
    print("✅ Brand login successful")
    
    print("✅ Complete workflow authentication successful")
    return True

def test_batch_creation_workflow():
    """Test batch creation workflow."""
    print("🧪 Testing Batch Creation Workflow...")
    
    # Test with plantation user
    token = get_auth_token("harvest@astra-agro.com", "password123")
    if not token:
        print("❌ Plantation login failed")
        return False
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test batch creation
    batch_id = f"BATCH-TEST-{uuid.uuid4().hex[:8].upper()}"
    batch_data = {
        "batch_id": batch_id,
        "batch_type": "harvest",
        "product_id": "ab70f396-86a1-4272-abf5-e68a9ca7b34b",  # RBD PO product
        "quantity": 100.0,
        "unit": "KGM",
        "production_date": "2025-09-13",
        "location_coordinates": {
            "latitude": 3.1390,
            "longitude": 101.6869,
            "accuracy_meters": 10.0
        },
        "origin_data": {
            "harvest_date": "2025-09-13",
            "farm_id": "FARM-001",
            "certifications": ["RSPO", "ISCC"]
        }
    }
    
    response = requests.post(f"{BASE_URL}/batches/", json=batch_data, headers=headers)
    
    if response.status_code in [200, 201]:
        print("✅ Batch creation successful")
        return True
    else:
        print(f"❌ Batch creation failed: {response.status_code}")
        print(f"Response: {response.text}")
        return False

def main():
    """Run all critical pathway tests."""
    print("🚀 Starting Critical Workflow Tests")
    print("=" * 50)
    
    tests = [
        ("Companies API", test_companies_api_returns_list),
        ("Transparency API", test_transparency_api_returns_ok),
        ("Purchase Orders API", test_purchase_orders_api_returns_data),
        ("Complete Workflow", test_complete_workflow),
        ("Batch Creation", test_batch_creation_workflow)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 Running {test_name}...")
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} PASSED")
            else:
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            print(f"❌ {test_name} ERROR: {str(e)}")
    
    print("\n" + "=" * 50)
    print(f"📊 RESULTS: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All critical pathway tests passed!")
        return 0
    else:
        print("⚠️  Some tests failed. Check the output above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
