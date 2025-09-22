#!/usr/bin/env python3
"""
Add missing palm oil companies to the system.
This script adds the companies that should appear in the seller dropdown.
"""

import requests
import json
from datetime import datetime

# API base URL
BASE_URL = "http://127.0.0.1:8000"

# Palm oil companies to add
COMPANIES_TO_ADD = [
    {
        "name": "Makmur Selalu Mill",
        "email": "info@makmurselalu.com",
        "company_type": "mill_processor",
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
        "name": "Wilmar Trading Ltd",
        "email": "info@wilmar.com",
        "company_type": "trader_aggregator",
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
        "name": "Tanimaju Cooperative",
        "email": "info@tanimaju.com",
        "company_type": "smallholder_cooperative",
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
        "name": "Plantation Estate Sdn Bhd",
        "email": "info@plantationestate.com",
        "company_type": "plantation_grower",
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
    login_data = {
        "email": "admin@example.com",
        "password": "adminpassword123"
    }
    
    response = requests.post(f"{BASE_URL}/api/v1/auth/login", json=login_data)
    if response.status_code == 200:
        return response.json().get("access_token")
    else:
        print(f"Failed to login as admin: {response.text}")
        return None

def add_company(token, company_data):
    """Add a company to the system."""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    response = requests.post(f"{BASE_URL}/api/v1/companies/", json=company_data, headers=headers)
    if response.status_code == 201:
        result = response.json()
        print(f"✅ Added company: {company_data['name']} (ID: {result['data']['id']})")
        return result['data']['id']
    else:
        print(f"❌ Failed to add company {company_data['name']}: {response.text}")
        return None

def main():
    print("🚀 Adding missing palm oil companies to the system...")
    
    # Login as admin
    token = login_as_admin()
    if not token:
        print("❌ Failed to get admin token")
        return
    
    print("✅ Logged in as admin")
    
    # Add each company
    added_companies = []
    for company_data in COMPANIES_TO_ADD:
        company_id = add_company(token, company_data)
        if company_id:
            added_companies.append({
                "name": company_data["name"],
                "id": company_id,
                "email": company_data["email"],
                "company_type": company_data["company_type"]
            })
    
    print(f"\n📊 Summary:")
    print(f"✅ Successfully added {len(added_companies)} companies:")
    for company in added_companies:
        print(f"   - {company['name']} ({company['company_type']}) - {company['email']}")
    
    if added_companies:
        print(f"\n🎯 These companies should now appear in the seller dropdown!")
        print(f"📝 You can now create purchase orders with these companies as sellers.")

if __name__ == "__main__":
    main()
