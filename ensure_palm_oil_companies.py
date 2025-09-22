#!/usr/bin/env python3
"""
Ensure palm oil companies exist and can be used in the system.
"""

import requests
import json

# API base URL
BASE_URL = "http://127.0.0.1:8000"

# Palm oil companies to ensure exist
PALM_OIL_COMPANIES = [
    {
        "name": "Wilmar Trading",
        "email": "manager@wilmar.com",
        "password": "TraderAggregator2024!",
        "company_type": "trader_aggregator",
        "role": "seller"
    },
    {
        "name": "Makmur Selalu Mill",
        "email": "manager@makmurselalu.com",
        "password": "MillProcessor2024!",
        "company_type": "mill_processor",
        "role": "seller"
    },
    {
        "name": "Tani Maju Cooperative",
        "email": "manager@tanimaju.com",
        "password": "SmallholderCoop2024!",
        "company_type": "smallholder_cooperative",
        "role": "seller"
    },
    {
        "name": "Plantation Estate",
        "email": "manager@plantationestate.com",
        "password": "PlantationGrower2024!",
        "company_type": "plantation_grower",
        "role": "seller"
    }
]

def test_company_login(company_data):
    """Test if a company can login."""
    print(f"🔐 Testing login for {company_data['name']}...")
    
    login_data = {
        "email": company_data["email"],
        "password": company_data["password"]
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/v1/auth/login", json=login_data)
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ {company_data['name']} can login successfully")
            return True, result.get('access_token')
        else:
            print(f"   ❌ {company_data['name']} login failed: {response.text}")
            return False, None
    except Exception as e:
        print(f"   ❌ Error testing login for {company_data['name']}: {str(e)}")
        return False, None

def register_company(company_data):
    """Register a company if it doesn't exist."""
    print(f"📝 Registering {company_data['name']}...")
    
    registration_data = {
        "email": company_data["email"],
        "password": company_data["password"],
        "full_name": f"{company_data['name']} Manager",
        "company_name": company_data["name"],
        "company_type": company_data["company_type"],
        "company_email": f"info@{company_data['name'].lower().replace(' ', '')}.com",
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

def check_company_in_list(token, company_name):
    """Check if a company appears in the companies list."""
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(f"{BASE_URL}/api/v1/companies/?for_supplier_selection=true", headers=headers)
        if response.status_code == 200:
            result = response.json()
            companies = result.get('data', [])
            
            for company in companies:
                if company_name in company.get('name', ''):
                    return True, company.get('name')
            
            return False, None
        else:
            print(f"   ❌ Failed to get companies list: {response.text}")
            return False, None
    except Exception as e:
        print(f"   ❌ Error checking companies list: {str(e)}")
        return False, None

def main():
    print("🏢 Ensuring palm oil companies exist and are accessible...")
    
    working_companies = []
    
    for company_data in PALM_OIL_COMPANIES:
        print(f"\n{'='*50}")
        print(f"Processing: {company_data['name']}")
        print(f"{'='*50}")
        
        # Test if company can login
        can_login, token = test_company_login(company_data)
        
        if can_login:
            # Check if company appears in the companies list
            print(f"🔍 Checking if {company_data['name']} appears in companies list...")
            in_list, actual_name = check_company_in_list(token, company_data['name'])
            
            if in_list:
                print(f"   ✅ {company_data['name']} appears in companies list as: {actual_name}")
                working_companies.append(company_data['name'])
            else:
                print(f"   ❌ {company_data['name']} does NOT appear in companies list")
        else:
            # Try to register the company
            print(f"🔄 Attempting to register {company_data['name']}...")
            if register_company(company_data):
                # Test login again
                can_login, token = test_company_login(company_data)
                if can_login:
                    working_companies.append(company_data['name'])
    
    print(f"\n{'='*50}")
    print(f"📊 SUMMARY")
    print(f"{'='*50}")
    print(f"✅ Working companies: {len(working_companies)}/{len(PALM_OIL_COMPANIES)}")
    
    for company in working_companies:
        print(f"   - {company}")
    
    missing_companies = [c['name'] for c in PALM_OIL_COMPANIES if c['name'] not in working_companies]
    if missing_companies:
        print(f"\n❌ Missing companies:")
        for company in missing_companies:
            print(f"   - {company}")
    
    print(f"\n🎯 Next Steps:")
    if len(working_companies) == len(PALM_OIL_COMPANIES):
        print(f"   🎉 All palm oil companies are working!")
        print(f"   📋 They should now appear in the seller dropdown")
        print(f"   🔄 Refresh the frontend to see the updated list")
    else:
        print(f"   ⚠️  Some companies still need to be fixed")
        print(f"   🔧 Check the registration process for missing companies")

if __name__ == "__main__":
    main()
