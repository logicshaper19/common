#!/usr/bin/env python3
"""
Clean up generic companies and ensure palm oil companies exist in the system.
"""

import requests
import json
from datetime import datetime

# API base URL
BASE_URL = "http://127.0.0.1:8000"

# Palm oil companies to ensure exist
PALM_OIL_COMPANIES = [
    {
        "name": "Wilmar Trading",
        "email": "manager@wilmar.com",
        "password": "TraderAggregator2024!",
        "company_type": "trader_aggregator",
        "role": "seller",
        "company_email": "info@wilmar.com",
        "phone": "+65-6-1234-5678",
        "address": "456 Trading Street",
        "city": "Singapore",
        "state": "Singapore",
        "country": "Singapore",
        "postal_code": "018956",
        "website": "https://wilmar.com",
        "description": "Global palm oil trader and aggregator"
    },
    {
        "name": "Makmur Selalu Mill",
        "email": "manager@makmurselalu.com",
        "password": "MillProcessor2024!",
        "company_type": "mill_processor",
        "role": "seller",
        "company_email": "info@makmurselalu.com",
        "phone": "+60-3-1234-5678",
        "address": "123 Palm Oil Road",
        "city": "Kuala Lumpur",
        "state": "Selangor",
        "country": "Malaysia",
        "postal_code": "50000",
        "website": "https://makmurselalu.com",
        "description": "Leading palm oil mill processor in Malaysia"
    },
    {
        "name": "Tani Maju Cooperative",
        "email": "manager@tanimaju.com",
        "password": "SmallholderCoop2024!",
        "company_type": "smallholder_cooperative",
        "role": "seller",
        "company_email": "info@tanimaju.com",
        "phone": "+60-3-2345-6789",
        "address": "789 Cooperative Lane",
        "city": "Johor Bahru",
        "state": "Johor",
        "country": "Malaysia",
        "postal_code": "80000",
        "website": "https://tanimaju.com",
        "description": "Smallholder cooperative for sustainable palm oil"
    },
    {
        "name": "Plantation Estate",
        "email": "manager@plantationestate.com",
        "password": "PlantationGrower2024!",
        "company_type": "plantation_grower",
        "role": "seller",
        "company_email": "info@plantationestate.com",
        "phone": "+60-3-3456-7890",
        "address": "321 Estate Road",
        "city": "Kota Kinabalu",
        "state": "Sabah",
        "country": "Malaysia",
        "postal_code": "88000",
        "website": "https://plantationestate.com",
        "description": "Sustainable palm oil plantation grower"
    }
]

def login_as_admin():
    """Login as admin to get authentication token."""
    # Try different admin credentials
    admin_credentials = [
        {"email": "admin@example.com", "password": "adminpassword123"},
        {"email": "elisha@common.co", "password": "password123"},
    ]
    
    for creds in admin_credentials:
        login_data = {
            "email": creds["email"],
            "password": creds["password"]
        }
        
        response = requests.post(f"{BASE_URL}/api/v1/auth/login", json=login_data)
        if response.status_code == 200:
            return response.json().get("access_token")
    
    print("❌ Failed to login as admin with any credentials")
    return None

def get_all_companies(token):
    """Get all companies from the system."""
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(f"{BASE_URL}/api/v1/companies/?for_supplier_selection=true", headers=headers)
        if response.status_code == 200:
            result = response.json()
            return result.get('data', [])
        else:
            print(f"❌ Failed to get companies: {response.text}")
            return []
    except Exception as e:
        print(f"❌ Error getting companies: {str(e)}")
        return []

def delete_generic_companies(token, companies):
    """Delete generic companies from the system."""
    headers = {"Authorization": f"Bearer {token}"}
    
    generic_patterns = [
        "Plantation Grower Company",
        "Smallholder Cooperative Company", 
        "Mill Processor Company",
        "Refinery Crusher Company",
        "Trader Aggregator Company",
        "Oleochemical Producer Company"
    ]
    
    deleted_count = 0
    
    for company in companies:
        company_name = company.get('name', '')
        
        # Check if this is a generic company
        is_generic = any(pattern in company_name for pattern in generic_patterns)
        
        if is_generic:
            company_id = company.get('id')
            print(f"🗑️  Deleting generic company: {company_name}")
            
            try:
                # Try to delete via admin endpoint
                response = requests.delete(f"{BASE_URL}/api/v1/admin/companies/{company_id}", headers=headers)
                if response.status_code == 200:
                    deleted_count += 1
                    print(f"   ✅ Deleted: {company_name}")
                else:
                    print(f"   ❌ Failed to delete {company_name}: {response.text}")
            except Exception as e:
                print(f"   ❌ Error deleting {company_name}: {str(e)}")
    
    print(f"📊 Deleted {deleted_count} generic companies")
    return deleted_count

def ensure_palm_oil_company_exists(company_data):
    """Ensure a palm oil company exists in the system."""
    print(f"🏢 Ensuring {company_data['name']} exists...")
    
    # Try to login with the company credentials
    login_data = {
        "email": company_data["email"],
        "password": company_data["password"]
    }
    
    response = requests.post(f"{BASE_URL}/api/v1/auth/login", json=login_data)
    if response.status_code == 200:
        print(f"   ✅ {company_data['name']} already exists and can login")
        return True
    else:
        print(f"   ❌ {company_data['name']} login failed: {response.text}")
        
        # Try to register the company
        print(f"   🔄 Attempting to register {company_data['name']}...")
        
        registration_data = {
            "email": company_data["email"],
            "password": company_data["password"],
            "full_name": f"{company_data['name']} Manager",
            "company_name": company_data["name"],
            "company_type": company_data["company_type"],
            "company_email": company_data["company_email"],
            "role": company_data["role"]
        }
        
        try:
            response = requests.post(f"{BASE_URL}/api/v1/auth/register", json=registration_data)
            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ Successfully registered {company_data['name']}")
                return True
            else:
                print(f"   ❌ Failed to register {company_data['name']}: {response.text}")
                return False
        except Exception as e:
            print(f"   ❌ Error registering {company_data['name']}: {str(e)}")
            return False

def verify_companies_in_list(token):
    """Verify that palm oil companies appear in the companies list."""
    print(f"\n🔍 Verifying palm oil companies appear in the list...")
    
    companies = get_all_companies(token)
    if not companies:
        print("❌ No companies found in the list")
        return False
    
    print(f"📊 Found {len(companies)} companies in the list")
    
    palm_oil_found = 0
    for company_data in PALM_OIL_COMPANIES:
        company_name = company_data["name"]
        
        # Check if this company is in the list
        found = False
        for company in companies:
            if company_name in company.get('name', ''):
                found = True
                palm_oil_found += 1
                print(f"   ✅ Found: {company.get('name')} ({company.get('company_type')})")
                break
        
        if not found:
            print(f"   ❌ Missing: {company_name}")
    
    print(f"\n📊 Summary:")
    print(f"   ✅ Palm oil companies found: {palm_oil_found}/{len(PALM_OIL_COMPANIES)}")
    print(f"   📋 Total companies in list: {len(companies)}")
    
    if palm_oil_found == len(PALM_OIL_COMPANIES):
        print(f"   🎉 All palm oil companies are now in the list!")
        return True
    else:
        print(f"   ⚠️  Some palm oil companies are still missing")
        return False

def main():
    print("🧹 Cleaning up generic companies and ensuring palm oil companies exist...")
    
    # Login as admin
    token = login_as_admin()
    if not token:
        print("❌ Failed to get admin token")
        return
    
    print("✅ Logged in as admin")
    
    # Get all companies
    companies = get_all_companies(token)
    if not companies:
        print("❌ No companies found")
        return
    
    print(f"📊 Found {len(companies)} companies in the system")
    
    # Delete generic companies
    print(f"\n🗑️  Deleting generic companies...")
    deleted_count = delete_generic_companies(token, companies)
    
    # Ensure palm oil companies exist
    print(f"\n🏢 Ensuring palm oil companies exist...")
    success_count = 0
    for company_data in PALM_OIL_COMPANIES:
        if ensure_palm_oil_company_exists(company_data):
            success_count += 1
    
    print(f"\n📊 Palm oil companies status: {success_count}/{len(PALM_OIL_COMPANIES)}")
    
    # Verify companies appear in the list
    verify_companies_in_list(token)
    
    print(f"\n🎯 Next Steps:")
    print(f"   - Refresh the frontend to see the updated companies list")
    print(f"   - Makmur Selalu Mill should now appear in the seller dropdown")
    print(f"   - All palm oil companies should be available for purchase orders")

if __name__ == "__main__":
    main()
