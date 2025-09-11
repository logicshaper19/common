#!/usr/bin/env python3
"""
Test script for the tier-based supplier requirements system
"""
import requests
import json
import sys

# Configuration
BASE_URL = "http://localhost:8000"
TEST_TOKEN = "your-test-token-here"  # Replace with actual token

def test_tier_requirements_api():
    """Test the tier requirements API endpoints."""
    headers = {
        "Authorization": f"Bearer {TEST_TOKEN}",
        "Content-Type": "application/json"
    }
    
    print("🧪 Testing Tier Requirements System")
    print("=" * 50)
    
    # Test 1: Get company types
    print("\n1. Testing company types endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/tier-requirements/company-types", headers=headers)
        if response.status_code == 200:
            data = response.json()
            print("✅ Company types retrieved successfully")
            print(f"   Found {len(data['company_types'])} company types")
            for ct in data['company_types']:
                print(f"   - {ct['label']}: {ct['transparency_weight']} transparency weight")
        else:
            print(f"❌ Failed to get company types: {response.status_code}")
    except Exception as e:
        print(f"❌ Error testing company types: {e}")
    
    # Test 2: Get sectors
    print("\n2. Testing sectors endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/tier-requirements/sectors", headers=headers)
        if response.status_code == 200:
            data = response.json()
            print("✅ Sectors retrieved successfully")
            print(f"   Found {len(data['sectors'])} sectors")
            for sector in data['sectors']:
                print(f"   - {sector['name']}: {len(sector['tiers'])} tiers")
        else:
            print(f"❌ Failed to get sectors: {response.status_code}")
    except Exception as e:
        print(f"❌ Error testing sectors: {e}")
    
    # Test 3: Get originator profile for palm oil
    print("\n3. Testing originator profile for palm oil...")
    try:
        response = requests.get(
            f"{BASE_URL}/api/v1/tier-requirements/profile/originator/palm_oil", 
            headers=headers
        )
        if response.status_code == 200:
            data = response.json()
            print("✅ Originator profile retrieved successfully")
            print(f"   Company Type: {data['company_type']}")
            print(f"   Tier Level: {data['tier_level']}")
            print(f"   Transparency Weight: {data['transparency_weight']}")
            print(f"   Base Requirements: {len(data['base_requirements'])}")
            print(f"   Sector Requirements: {len(data['sector_specific_requirements'])}")
            
            # Show requirements
            all_reqs = data['base_requirements'] + data['sector_specific_requirements']
            mandatory_reqs = [req for req in all_reqs if req['is_mandatory']]
            print(f"   Mandatory Requirements ({len(mandatory_reqs)}):")
            for req in mandatory_reqs:
                print(f"     - {req['name']} ({req['type']})")
        else:
            print(f"❌ Failed to get originator profile: {response.status_code}")
    except Exception as e:
        print(f"❌ Error testing originator profile: {e}")
    
    # Test 4: Test requirements validation
    print("\n4. Testing requirements validation...")
    try:
        validation_data = {
            "company_type": "originator",
            "sector_id": "palm_oil",
            "coordinates": {
                "latitude": 1.2345,
                "longitude": 103.6789
            },
            "documents": {
                "operating_license": "license.pdf"
            },
            "certifications": {
                "rspo_certificate": "rspo_cert.pdf"
            }
        }
        
        response = requests.post(
            f"{BASE_URL}/api/v1/tier-requirements/validate",
            headers=headers,
            json=validation_data
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Requirements validation completed")
            print(f"   Is Valid: {data['is_valid']}")
            print(f"   Missing Requirements: {len(data['missing_requirements'])}")
            if data['missing_requirements']:
                for req in data['missing_requirements']:
                    print(f"     - {req['name']} ({req['type']})")
        else:
            print(f"❌ Failed to validate requirements: {response.status_code}")
    except Exception as e:
        print(f"❌ Error testing requirements validation: {e}")
    
    # Test 5: Get requirements summary
    print("\n5. Testing requirements summary...")
    try:
        response = requests.get(
            f"{BASE_URL}/api/v1/tier-requirements/requirements/summary/originator/palm_oil",
            headers=headers
        )
        if response.status_code == 200:
            data = response.json()
            print("✅ Requirements summary retrieved successfully")
            print(f"   Total Requirements: {data['total_requirements']}")
            print(f"   Mandatory: {data['mandatory_requirements']}")
            print(f"   Optional: {data['optional_requirements']}")
            print(f"   Requirement Types: {data['requirement_types']}")
        else:
            print(f"❌ Failed to get requirements summary: {response.status_code}")
    except Exception as e:
        print(f"❌ Error testing requirements summary: {e}")

def test_supplier_addition_flow():
    """Test the complete supplier addition flow with tier requirements."""
    headers = {
        "Authorization": f"Bearer {TEST_TOKEN}",
        "Content-Type": "application/json"
    }
    
    print("\n🚀 Testing Supplier Addition Flow")
    print("=" * 50)
    
    # Test supplier addition with tier information
    supplier_data = {
        "supplier_email": "test-originator@example.com",
        "supplier_name": "Test Palm Oil Mill",
        "company_type": "originator",
        "sector_id": "palm_oil",
        "relationship_type": "supplier",
        "data_sharing_permissions": {
            "view_purchase_orders": True,
            "view_product_details": True,
            "view_pricing": False,
            "view_delivery_schedules": True,
            "view_quality_metrics": True,
            "view_sustainability_data": True,
            "view_transparency_scores": True,
            "edit_order_confirmations": True,
            "edit_delivery_updates": True,
            "edit_quality_reports": True,
            "receive_notifications": True,
            "access_analytics": False
        }
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/business-relationships/invite-supplier",
            headers=headers,
            json=supplier_data
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Supplier added successfully with tier information")
            print(f"   Company ID: {data.get('company_id')}")
            print(f"   Relationship ID: {data.get('relationship_id')}")
            print(f"   Status: {data.get('status')}")
        else:
            print(f"❌ Failed to add supplier: {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ Error testing supplier addition: {e}")

def main():
    """Run all tests."""
    print("🔧 Tier-Based Supplier Requirements System Test")
    print("=" * 60)
    
    if len(sys.argv) > 1 and sys.argv[1] == "--token":
        global TEST_TOKEN
        TEST_TOKEN = sys.argv[2] if len(sys.argv) > 2 else input("Enter your test token: ")
    
    # Test the tier requirements API
    test_tier_requirements_api()
    
    # Test the supplier addition flow
    test_supplier_addition_flow()
    
    print("\n" + "=" * 60)
    print("🎉 Testing completed!")
    print("\nTo run with authentication:")
    print("python test_tier_requirements.py --token YOUR_TOKEN_HERE")

if __name__ == "__main__":
    main()
