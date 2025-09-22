#!/usr/bin/env python3
"""
Add Makmur Selalu Mill to the system using the registration endpoint.
"""

import requests
import json

# API base URL
BASE_URL = "http://127.0.0.1:8000"

def add_makmur_selalu_mill():
    """Add Makmur Selalu Mill using the registration endpoint."""
    
    # Company data for Makmur Selalu Mill
    company_data = {
        "email": "manager@makmurselalu.com",
        "password": "MillProcessor2024!",
        "full_name": "Makmur Selalu Manager",
        "company_name": "Makmur Selalu Mill",
        "company_type": "mill_processor",
        "company_email": "info@makmurselalu.com",
        "role": "seller"
    }
    
    print("🚀 Adding Makmur Selalu Mill to the system...")
    
    try:
        response = requests.post(f"{BASE_URL}/api/v1/auth/register", json=company_data)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Successfully added Makmur Selalu Mill!")
            print(f"   Company ID: {result.get('company_id', 'N/A')}")
            print(f"   User ID: {result.get('user_id', 'N/A')}")
            print(f"   Access Token: {result.get('access_token', 'N/A')[:20]}...")
            return True
        else:
            print(f"❌ Failed to add Makmur Selalu Mill: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error adding Makmur Selalu Mill: {str(e)}")
        return False

def test_login():
    """Test login with Makmur Selalu Mill credentials."""
    print("\n🔐 Testing login with Makmur Selalu Mill...")
    
    login_data = {
        "email": "manager@makmurselalu.com",
        "password": "MillProcessor2024!"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/v1/auth/login", json=login_data)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Login successful!")
            print(f"   Access Token: {result.get('access_token', 'N/A')[:20]}...")
            return result.get('access_token')
        else:
            print(f"❌ Login failed: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error during login: {str(e)}")
        return None

def test_companies_endpoint(token):
    """Test the companies endpoint to see if Makmur Selalu Mill appears."""
    print("\n🏢 Testing companies endpoint...")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(f"{BASE_URL}/api/v1/companies/?for_supplier_selection=true", headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            companies = result.get('data', [])
            print(f"✅ Companies endpoint working! Found {len(companies)} companies")
            
            # Check if Makmur Selalu Mill is in the list
            makmur_found = False
            for company in companies:
                if "Makmur" in company.get('name', ''):
                    makmur_found = True
                    print(f"✅ Found Makmur Selalu Mill: {company.get('name')} ({company.get('company_type')})")
                    break
            
            if not makmur_found:
                print("❌ Makmur Selalu Mill not found in companies list")
                print("   Available companies:")
                for company in companies[:5]:  # Show first 5 companies
                    print(f"   - {company.get('name')} ({company.get('company_type')})")
            
            return makmur_found
        else:
            print(f"❌ Companies endpoint failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing companies endpoint: {str(e)}")
        return False

def main():
    print("🎯 Adding Makmur Selalu Mill to the system...")
    
    # Try to add the company
    success = add_makmur_selalu_mill()
    
    if success:
        # Test login
        token = test_login()
        
        if token:
            # Test companies endpoint
            test_companies_endpoint(token)
    
    print("\n📊 Summary:")
    print("   - If successful, Makmur Selalu Mill should now appear in the seller dropdown")
    print("   - You can now create purchase orders with Makmur Selalu Mill as the seller")

if __name__ == "__main__":
    main()
