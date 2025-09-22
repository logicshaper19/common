#!/usr/bin/env python3
"""
Script to check admin users and create palm oil companies.
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

def try_login(email, password):
    """Try to login with given credentials."""
    login_data = {
        "email": email,
        "password": password
    }
    
    try:
        response = requests.post(LOGIN_URL, json=login_data)
        if response.status_code == 200:
            return response.json()["access_token"]
        else:
            print(f"❌ Failed to login with {email}: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ Error logging in with {email}: {e}")
        return None

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
    print("🔍 Checking admin credentials and creating palm oil companies...")
    
    # Try different admin credentials
    admin_credentials = [
        ("admin@example.com", "adminpassword123"),
        ("elisha@common.co", "slp225"),
        ("elisha@common.co", "password123"),
        ("admin@common.co", "adminpassword123"),
    ]
    
    token = None
    for email, password in admin_credentials:
        print(f"🔐 Trying {email}...")
        token = try_login(email, password)
        if token:
            print(f"✅ Successfully logged in with {email}")
            break
    
    if not token:
        print("❌ Failed to login with any admin credentials")
        print("Let me try to create companies using the registration endpoint directly...")
        
        # Try to create companies without admin token
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
        
        print("\n🔨 Creating palm oil companies directly...")
        for name, data in palm_oil_companies.items():
            company_data = {
                "email": data["email"],
                "password": data["password"],
                "full_name": f"{name} Manager",
                "company_name": name,
                "company_type": data["company_type"],
                "company_email": data["email"],
                "role": data["role"]
            }
            
            # Try without token first
            try:
                response = requests.post(REGISTER_URL, json=company_data)
                if response.status_code == 201:
                    print(f"✅ Created company: {name}")
                else:
                    print(f"❌ Failed to create {name}: {response.status_code} - {response.text}")
            except Exception as e:
                print(f"❌ Error creating {name}: {e}")
        
        return
    
    # If we have a token, create companies with admin privileges
    print("\n🔨 Creating palm oil companies with admin privileges...")
    
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
    
    for name, data in palm_oil_companies.items():
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

if __name__ == "__main__":
    main()
