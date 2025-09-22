#!/usr/bin/env python3
"""
Fix the companies endpoint to show actual companies instead of generic ones.
"""

import requests
import json

# API base URL
BASE_URL = "http://127.0.0.1:8000"

def test_companies_endpoint():
    """Test the companies endpoint to see what it returns."""
    
    print("🔍 Testing companies endpoint...")
    
    # Test with different users
    users_to_test = [
        {"email": "manager@asianrefineries.com", "password": "RefineryProcessor2024!", "name": "Asian Refineries"},
        {"email": "manager@makmurselalu.com", "password": "MillProcessor2024!", "name": "Makmur Selalu Mill"},
    ]
    
    for user in users_to_test:
        print(f"\n👤 Testing as {user['name']}...")
        
        # Login
        login_data = {"email": user["email"], "password": user["password"]}
        response = requests.post(f"{BASE_URL}/api/v1/auth/login", json=login_data)
        
        if response.status_code == 200:
            token = response.json().get('access_token')
            print(f"   ✅ Login successful")
            
            # Test companies endpoint
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

def main():
    print("🔧 Testing companies endpoint...")
    
    test_companies_endpoint()
    
    print(f"\n💡 Conclusion:")
    print(f"   - If companies can login but don't appear in the companies list,")
    print(f"     there's a filtering issue in the companies endpoint")
    print(f"   - The companies endpoint should return the actual companies from the database")
    print(f"   - Makmur Selalu Mill should appear in the seller dropdown once this is fixed")

if __name__ == "__main__":
    main()
