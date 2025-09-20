#!/usr/bin/env python3
"""
Create supplier data using the API endpoints.
"""
import requests
import json
import uuid
from datetime import datetime, timedelta

# API base URL
BASE_URL = "http://127.0.0.1:8000"

# Company types and roles (excluding brand/manufacturer)
COMPANY_TYPES = [
    "plantation_grower",
    "smallholder_cooperative", 
    "mill_processor",
    "refinery_crusher",
    "trader_aggregator",
    "oleochemical_producer"
]

# User roles for each company type
ROLE_MAPPING = {
    "plantation_grower": ["admin", "plantation_manager", "harvest_manager"],
    "smallholder_cooperative": ["admin", "cooperative_manager", "harvest_manager"],
    "mill_processor": ["admin", "mill_manager", "operations_manager", "quality_manager"],
    "refinery_crusher": ["admin", "refinery_manager", "quality_manager"],
    "trader_aggregator": ["admin", "trader", "sustainability_manager"],
    "oleochemical_producer": ["admin", "production_manager", "quality_manager"]
}

def create_company_and_users(company_type, company_num):
    """Create a company and its users via API."""
    # Convert company_type to valid email format (replace underscores with hyphens)
    email_safe_type = company_type.replace("_", "-")
    company_name = f"{company_type.replace('_', ' ').title()} Company {company_num}"
    company_email = f"{email_safe_type}{company_num}@example.com"
    
    # Use timestamp to make emails unique
    import time
    timestamp = int(time.time())
    
    # Create company registration data
    registration_data = {
        "email": f"admin{timestamp}@{email_safe_type}{company_num}.com",
        "password": "SecurePass123!",
        "full_name": f"Admin User {company_num}",
        "role": "admin",
        "company_name": f"{company_name} {timestamp}",
        "company_type": company_type,
        "company_email": f"{email_safe_type}{company_num}{timestamp}@example.com"
    }
    
    print(f"  Creating {company_name}...")
    
    # Register the company (this creates both company and admin user)
    response = requests.post(f"{BASE_URL}/api/v1/auth/register", json=registration_data)
    
    if response.status_code == 200:
        data = response.json()
        access_token = data.get("access_token")
        
        # Decode JWT token to get company_id
        import base64
        import json as json_lib
        
        # JWT token has 3 parts separated by dots
        token_parts = access_token.split('.')
        if len(token_parts) >= 2:
            # Decode the payload (second part)
            payload = token_parts[1]
            # Add padding if needed
            payload += '=' * (4 - len(payload) % 4)
            decoded_payload = base64.b64decode(payload)
            token_data = json_lib.loads(decoded_payload)
            company_id = token_data.get("company_id")
        else:
            company_id = None
        
        print(f"    ✅ Created company with ID: {company_id}")
        print(f"    📧 Admin email: {registration_data['email']}")
        print(f"    🔑 Access token: {access_token[:20]}...")
        
        # Create additional users for this company
        roles = ROLE_MAPPING.get(company_type, ["admin"])
        for role in roles[1:]:  # Skip admin as it's already created
            user_data = {
                "email": f"{role}@{email_safe_type}{company_num}.com",
                "password": "SecurePass123!",
                "full_name": f"{role.title()} User",
                "role": role,
                "company_id": company_id
            }
            
            # Note: This would require a user creation endpoint
            # For now, we'll just log what we would create
            print(f"    📝 Would create user: {role}@{email_safe_type}{company_num}.com")
        
        return company_id, access_token
    else:
        print(f"    ❌ Failed to create company: {response.status_code} - {response.text}")
        return None, None

def create_purchase_orders(created_companies):
    """Create purchase orders between companies."""
    print("\n📋 Creating purchase orders...")
    
    if not created_companies:
        print("❌ No companies created, cannot create purchase orders")
        return
    
    # Get all companies (we'll need to authenticate)
    # For now, let's create purchase orders between the companies we just created
    print(f"📊 Created companies: {sum(len(companies) for companies in created_companies.values())}")
    
    # Create purchase orders between different company types
    company_types = list(created_companies.keys())
    for i, company_type in enumerate(company_types):
        if not created_companies[company_type]:
            continue
            
        # Find supplier companies (different types)
        supplier_types = [ct for ct in company_types if ct != company_type]
        
        if not supplier_types:
            continue
        
        print(f"  📦 Creating POs for {company_type} companies...")
        
        # Create 2 purchase orders for each company of this type
        for company_id in created_companies[company_type]:
            for po_num in range(2):
                supplier_type = supplier_types[po_num % len(supplier_types)]
                if created_companies[supplier_type]:
                    supplier_id = created_companies[supplier_type][0]  # Use first supplier
                    
                    po_data = {
                        "po_number": f"PO-{company_type.upper()}-{po_num+1:03d}",
                        "buyer_company_id": company_id,
                        "seller_company_id": supplier_id,
                        "quantity": 1000.00,
                        "unit_price": 500.00,
                        "total_amount": 500000.00,
                        "unit": "kg",
                        "delivery_date": (datetime.now() + timedelta(days=30)).isoformat(),
                        "delivery_location": f"Port of {company_type.replace('_', ' ').title()}",
                        "status": "confirmed",
                        "input_materials": {
                            "palm_oil": {
                                "quantity": 1000,
                                "unit": "kg",
                                "origin": "Malaysia",
                                "certifications": ["RSPO", "ISCC"],
                                "supplier": {
                                    "name": "Malaysian Palm Oil Supplier",
                                    "certifications": ["RSPO", "ISO 9001"]
                                }
                            }
                        },
                        "origin_data": {
                            "traceability": {
                                "batch_id": f"BATCH-{company_type.upper()}-{po_num+1:03d}",
                                "plantation": {
                                    "name": f"Sustainable {company_type.replace('_', ' ').title()} Plantation",
                                    "certified_rspo": True,
                                    "size_ha": 500
                                },
                                "mill": {
                                    "name": f"Green {company_type.replace('_', ' ').title()} Mill",
                                    "capacity_tons_day": 100
                                }
                            },
                            "quality_metrics": {
                                "ffa_content": 0.15,
                                "moisture": 0.1,
                                "impurity": 0.05
                            },
                            "sustainability": {
                                "social_impact_score": 8.5,
                                "carbon_footprint": 2.5,
                                "deforestation_risk": "low"
                            }
                        }
                    }
                    
                    print(f"    📝 Would create PO: {po_data['po_number']} (Buyer: {company_id}, Seller: {supplier_id})")

def check_existing_companies():
    """Check what companies already exist."""
    print("🔍 Checking existing companies...")
    
    # Try to get companies (this might require authentication)
    try:
        response = requests.get(f"{BASE_URL}/api/v1/companies/")
        if response.status_code == 200:
            companies = response.json().get("data", [])
            print(f"Found {len(companies)} existing companies")
            for company in companies:
                print(f"  - {company['name']} ({company['company_type']})")
            return companies
        else:
            print(f"Could not fetch companies: {response.status_code}")
            return []
    except Exception as e:
        print(f"Error fetching companies: {e}")
        return []

def main():
    """Main function to create supplier data."""
    print("🏢 Creating companies and users for each role...")
    
    # Check existing companies first
    existing_companies = check_existing_companies()
    
    created_companies = {}
    
    for company_type in COMPANY_TYPES:
        print(f"\n📦 Creating {company_type} companies...")
        
        # Create 2 companies of each type
        for i in range(2):
            company_id, access_token = create_company_and_users(company_type, i + 1)
            if company_id:
                if company_type not in created_companies:
                    created_companies[company_type] = []
                created_companies[company_type].append(company_id)
    
    print(f"\n✅ Created companies: {sum(len(companies) for companies in created_companies.values())}")
    
    # Create purchase orders
    create_purchase_orders(created_companies)
    
    print(f"\n🎉 Supplier data creation completed!")
    print(f"📊 Summary:")
    for company_type, companies in created_companies.items():
        print(f"  {company_type}: {len(companies)} companies")

if __name__ == "__main__":
    main()
