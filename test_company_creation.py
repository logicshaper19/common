#!/usr/bin/env python3
"""
Test company creation to see if new companies appear in the companies list.
"""

import requests
import json
import uuid
from datetime import datetime

# API base URL
BASE_URL = "http://127.0.0.1:8000"

def create_test_company():
    """Create a test company to see if it appears in the companies list."""
    
    # Generate unique email to avoid conflicts
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    test_email = f"test-{timestamp}@example.com"
    
    company_data = {
        "email": test_email,
        "password": "MillProcessor2024!",
        "full_name": "Test Company Manager",
        "company_name": f"Test Company {timestamp}",
        "company_type": "mill_processor",
        "company_email": f"info-{timestamp}@example.com",
        "role": "seller"
    }
    
    print(f"🚀 Creating test company: {company_data['company_name']}...")
    
    try:
        response = requests.post(f"{BASE_URL}/api/v1/auth/register", json=company_data)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Test company created successfully!")
            print(f"   Company: {company_data['company_name']}")
            print(f"   Email: {test_email}")
            return test_email, company_data['company_name']
        else:
            print(f"❌ Failed to create test company: {response.text}")
            return None, None
            
    except Exception as e:
        print(f"❌ Error creating test company: {str(e)}")
        return None, None

def test_companies_list(test_email, test_company_name):
    """Test if the new company appears in the companies list."""
    
    print(f"\n🔍 Testing if {test_company_name} appears in companies list...")
    
    # Login with the test company
    login_data = {"email": test_email, "password": "MillProcessor2024!"}
    response = requests.post(f"{BASE_URL}/api/v1/auth/login", json=login_data)
    
    if response.status_code == 200:
        token = response.json().get('access_token')
        print("✅ Login successful")
        
        # Check companies endpoint
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{BASE_URL}/api/v1/companies/?for_supplier_selection=true", headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            companies = result.get('data', [])
            print(f"📊 Found {len(companies)} companies in list")
            
            # Check if the test company is in the list
            test_company_found = False
            for company in companies:
                if test_company_name in company.get('name', ''):
                    test_company_found = True
                    print(f"✅ Test company found in list: {company.get('name')}")
                    break
            
            if not test_company_found:
                print(f"❌ Test company NOT found in companies list")
                print("   This confirms there's a filtering issue")
                
                # Show what companies are actually in the list
                print("   Companies in list:")
                for company in companies[:5]:
                    print(f"      - {company.get('name')} ({company.get('company_type')})")
            
            return test_company_found
        else:
            print(f"❌ Companies endpoint failed: {response.text}")
            return False
    else:
        print(f"❌ Login failed: {response.text}")
        return False

def main():
    print("🧪 Testing company creation and visibility...")
    
    # Create a test company
    test_email, test_company_name = create_test_company()
    
    if test_email and test_company_name:
        # Test if it appears in the companies list
        appears_in_list = test_companies_list(test_email, test_company_name)
        
        print(f"\n📊 Test Results:")
        if appears_in_list:
            print("   ✅ New companies DO appear in the companies list")
            print("   💡 The issue is that existing palm oil companies are not in the list")
        else:
            print("   ❌ New companies do NOT appear in the companies list")
            print("   💡 There's a fundamental issue with the companies endpoint")
    
    print(f"\n🎯 Next Steps:")
    print("   - If new companies don't appear: Fix the companies endpoint")
    print("   - If new companies do appear: The palm oil companies are in a different database/table")

if __name__ == "__main__":
    main()
