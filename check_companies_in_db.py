#!/usr/bin/env python3
"""
Check what companies actually exist in the database.
"""

import requests
import json

# API base URL
BASE_URL = "http://127.0.0.1:8000"

def check_all_companies():
    """Check all companies in the system by trying different approaches."""
    
    print("🔍 Checking all companies in the system...")
    
    # Try to login as different users to see what companies they can see
    users_to_test = [
        {"email": "manager@asianrefineries.com", "password": "RefineryProcessor2024!", "name": "Asian Refineries"},
        {"email": "manager@makmurselalu.com", "password": "MillProcessor2024!", "name": "Makmur Selalu Mill"},
        {"email": "demo@loreal.com", "password": "BeautyCosmetics2024!", "name": "L'Oréal"},
    ]
    
    for user in users_to_test:
        print(f"\n👤 Testing as {user['name']}...")
        
        # Login
        login_data = {"email": user["email"], "password": user["password"]}
        response = requests.post(f"{BASE_URL}/api/v1/auth/login", json=login_data)
        
        if response.status_code == 200:
            token = response.json().get('access_token')
            print(f"   ✅ Login successful")
            
            # Check companies endpoint
            headers = {"Authorization": f"Bearer {token}"}
            response = requests.get(f"{BASE_URL}/api/v1/companies/?for_supplier_selection=true", headers=headers)
            
            if response.status_code == 200:
                result = response.json()
                companies = result.get('data', [])
                print(f"   📊 Can see {len(companies)} companies")
                
                # Check if their own company is in the list
                own_company_found = False
                for company in companies:
                    if user["name"] in company.get('name', ''):
                        own_company_found = True
                        print(f"   ✅ Own company found: {company.get('name')}")
                        break
                
                if not own_company_found:
                    print(f"   ❌ Own company not found in list")
                
                # Show first few companies
                print(f"   📋 First 3 companies:")
                for company in companies[:3]:
                    print(f"      - {company.get('name')} ({company.get('company_type')})")
            else:
                print(f"   ❌ Companies endpoint failed: {response.text}")
        else:
            print(f"   ❌ Login failed: {response.text}")

def check_specific_companies():
    """Check if specific palm oil companies exist by trying to login."""
    
    print("\n🎯 Checking specific palm oil companies...")
    
    palm_oil_companies = [
        {"email": "manager@makmurselalu.com", "password": "MillProcessor2024!", "name": "Makmur Selalu Mill"},
        {"email": "manager@wilmar.com", "password": "TraderAggregator2024!", "name": "Wilmar Trading"},
        {"email": "manager@tanimaju.com", "password": "SmallholderCoop2024!", "name": "Tanimaju Cooperative"},
        {"email": "manager@plantationestate.com", "password": "PlantationGrower2024!", "name": "Plantation Estate"},
    ]
    
    existing_companies = []
    
    for company in palm_oil_companies:
        print(f"\n🏢 Testing {company['name']}...")
        
        login_data = {"email": company["email"], "password": company["password"]}
        response = requests.post(f"{BASE_URL}/api/v1/auth/login", json=login_data)
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ {company['name']} exists and can login")
            existing_companies.append(company['name'])
        else:
            print(f"   ❌ {company['name']} login failed: {response.text}")
    
    print(f"\n📊 Summary:")
    print(f"   ✅ Existing companies: {len(existing_companies)}")
    for company in existing_companies:
        print(f"      - {company}")
    print(f"   ❌ Missing companies: {len(palm_oil_companies) - len(existing_companies)}")

def main():
    print("🔍 Checking companies in the database...")
    
    check_all_companies()
    check_specific_companies()
    
    print(f"\n💡 Conclusion:")
    print(f"   - If companies can login but don't appear in the companies list,")
    print(f"     there might be a filtering issue in the companies endpoint")
    print(f"   - The frontend should now show these companies in the seller dropdown")

if __name__ == "__main__":
    main()
