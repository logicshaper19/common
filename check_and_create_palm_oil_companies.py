#!/usr/bin/env python3
"""
Script to check what companies exist and create the missing palm oil companies.
"""

import requests
import json
import sys
from datetime import datetime

# API Configuration
API_BASE_URL = "http://127.0.0.1:8000"
LOGIN_URL = f"{API_BASE_URL}/api/v1/auth/login"
REGISTER_URL = f"{API_BASE_URL}/api/v1/auth/register"
COMPANIES_URL = f"{API_BASE_URL}/api/v1/companies/"

def login_as_admin():
    """Login as admin to get authentication token."""
    login_data = {
        "email": "admin@example.com",
        "password": "adminpassword123"
    }
    
    try:
        response = requests.post(LOGIN_URL, json=login_data)
        if response.status_code == 200:
            return response.json()["access_token"]
        else:
            print(f"Failed to login as admin: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"Error logging in as admin: {e}")
        return None

def get_all_companies(token):
    """Get all companies from the API."""
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(COMPANIES_URL, headers=headers)
        if response.status_code == 200:
            return response.json()["data"]
        else:
            print(f"Failed to get companies: {response.status_code} - {response.text}")
            return []
    except Exception as e:
        print(f"Error getting companies: {e}")
        return []

def create_company(token, company_data):
    """Create a new company."""
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.post(REGISTER_URL, json=company_data)
        if response.status_code == 201:
            print(f"✅ Created company: {company_data['company_name']}")
            return True
        else:
            print(f"❌ Failed to create {company_data['company_name']}: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error creating {company_data['company_name']}: {e}")
        return False

def main():
    print("🔍 Checking existing companies and creating missing palm oil companies...")
    
    # Login as admin
    token = login_as_admin()
    if not token:
        print("❌ Failed to login as admin")
        return
    
    print("✅ Logged in as admin")
    
    # Get all existing companies
    companies = get_all_companies(token)
    print(f"📊 Found {len(companies)} existing companies")
    
    # Check which palm oil companies exist
    palm_oil_companies = {
        "Wilmar Trading Ltd": {
            "email": "manager@wilmar.com",
            "password": "TraderAggregator2024!",
            "company_type": "trader_aggregator",
            "role": "seller"
        },
        "Makmur Selalu Mill": {
            "email": "manager@makmurselalu.com", 
            "password": "MillProcessor2024!",
            "company_type": "mill_processor",
            "role": "seller"
        },
        "Tani Maju Cooperative": {
            "email": "manager@tanimaju.com",
            "password": "SmallholderCoop2024!",
            "company_type": "smallholder_cooperative",
            "role": "seller"
        },
        "Plantation Estate Sdn Bhd": {
            "email": "manager@plantationestate.com",
            "password": "PlantationGrower2024!",
            "company_type": "plantation_grower",
            "role": "seller"
        }
    }
    
    # Check which companies exist
    existing_company_emails = {company["email"] for company in companies}
    print("\n📋 Existing company emails:")
    for email in sorted(existing_company_emails):
        print(f"  - {email}")
    
    # Check which palm oil companies are missing
    missing_companies = []
    for name, data in palm_oil_companies.items():
        if data["email"] not in existing_company_emails:
            missing_companies.append((name, data))
            print(f"❌ Missing: {name} ({data['email']})")
        else:
            print(f"✅ Exists: {name} ({data['email']})")
    
    # Create missing companies
    if missing_companies:
        print(f"\n🔨 Creating {len(missing_companies)} missing companies...")
        
        for name, data in missing_companies:
            company_data = {
                "email": data["email"],
                "password": data["password"],
                "full_name": f"{name} Manager",
                "company_name": name,
                "company_type": data["company_type"],
                "company_email": data["email"],
                "role": data["role"]
            }
            
            create_company(token, company_data)
    else:
        print("\n✅ All palm oil companies already exist!")
    
    # Final check - get updated company list
    print("\n🔍 Final company list:")
    updated_companies = get_all_companies(token)
    palm_oil_company_names = set(palm_oil_companies.keys())
    
    for company in updated_companies:
        if company["name"] in palm_oil_company_names:
            print(f"✅ {company['name']} - {company['email']} ({company['company_type']})")
        elif "Company" in company["name"] and any(x in company["name"] for x in ["Plantation Grower", "Mill Processor", "Refinery Crusher", "Trader Aggregator", "Smallholder Cooperative", "Oleochemical Producer"]):
            print(f"🗑️  {company['name']} - {company['email']} ({company['company_type']}) - GENERIC COMPANY")

if __name__ == "__main__":
    main()
