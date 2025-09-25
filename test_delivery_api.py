#!/usr/bin/env python3
"""
Simple test script for delivery API endpoints
"""
import requests
import json
import sys
from uuid import uuid4

# Configuration
API_BASE_URL = "http://localhost:8000"
TEST_PO_ID = "your-test-po-id-here"  # Replace with actual PO ID
AUTH_TOKEN = "your-auth-token-here"  # Replace with actual token

def test_delivery_endpoints():
    """Test the delivery API endpoints"""
    
    headers = {
        "Authorization": f"Bearer {AUTH_TOKEN}",
        "Content-Type": "application/json"
    }
    
    print("🚚 Testing Delivery API Endpoints")
    print("=" * 50)
    
    # Test 1: Get delivery information
    print("\n1. Testing GET /api/v1/purchase-orders/{po_id}/delivery")
    try:
        response = requests.get(
            f"{API_BASE_URL}/api/v1/purchase-orders/{TEST_PO_ID}/delivery",
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Success!")
            print(f"   Delivery Status: {data.get('delivery_status')}")
            print(f"   Delivery Date: {data.get('delivery_date')}")
            print(f"   Delivery Location: {data.get('delivery_location')}")
        else:
            print(f"❌ Failed: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 2: Update delivery status
    print("\n2. Testing PATCH /api/v1/purchase-orders/{po_id}/delivery")
    try:
        update_data = {
            "status": "in_transit",
            "notes": "Package picked up and in transit"
        }
        
        response = requests.patch(
            f"{API_BASE_URL}/api/v1/purchase-orders/{TEST_PO_ID}/delivery",
            headers=headers,
            json=update_data
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Success!")
            print(f"   Updated Status: {data.get('delivery_status')}")
            print(f"   Notes Added: {data.get('delivery_notes')}")
        else:
            print(f"❌ Failed: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 3: Get delivery history
    print("\n3. Testing GET /api/v1/purchase-orders/{po_id}/delivery/history")
    try:
        response = requests.get(
            f"{API_BASE_URL}/api/v1/purchase-orders/{TEST_PO_ID}/delivery/history",
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Success!")
            print(f"   Current Status: {data.get('current_status')}")
            print(f"   History Entries: {len(data.get('history', []))}")
        else:
            print(f"❌ Failed: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 Test Complete!")
    print("\nTo test with real data:")
    print("1. Replace TEST_PO_ID with an actual purchase order ID")
    print("2. Replace AUTH_TOKEN with a valid authentication token")
    print("3. Make sure the API server is running on localhost:8000")

if __name__ == "__main__":
    if TEST_PO_ID == "your-test-po-id-here" or AUTH_TOKEN == "your-auth-token-here":
        print("⚠️  Please update TEST_PO_ID and AUTH_TOKEN in the script before running")
        print("   This is just a template - update with real values to test")
        sys.exit(1)
    
    test_delivery_endpoints()
