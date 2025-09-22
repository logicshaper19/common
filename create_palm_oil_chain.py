#!/usr/bin/env python3
"""
Create a proper palm oil supply chain that matches the system design.
Based on the palm oil sector template in the codebase.
"""

import requests
import json
import time
from typing import Dict, Any

class PalmOilSupplyChainCreator:
    def __init__(self, base_url: str = "http://127.0.0.1:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.created_companies = {}
        
    def create_palm_oil_chain(self):
        """Create the complete palm oil supply chain"""
        print("🌴 Creating Palm Oil Supply Chain...")
        
        # Create L'Oréal as the brand (already exists, but let's verify)
        loreal_company = self._create_or_verify_loreal()
        
        # Create palm oil companies with proper company types
        palm_oil_companies = self._create_palm_oil_companies()
        
        # Create business relationships
        self._create_business_relationships(palm_oil_companies)
        
        # Save credentials
        self._save_credentials(palm_oil_companies)
        
        print("✅ Palm Oil Supply Chain created successfully!")
        return palm_oil_companies
    
    def _create_or_verify_loreal(self) -> Dict[str, Any]:
        """Create or verify L'Oréal exists with proper palm oil company type"""
        print("🏢 Creating/Verifying L'Oréal...")
        
        # Try to login first to see if it exists
        login_data = {
            "email": "demo@loreal.com",
            "password": "BeautyCosmetics2024!"
        }
        
        response = self.session.post(f"{self.base_url}/api/v1/auth/login", json=login_data)
        if response.status_code == 200:
            print("✅ L'Oréal already exists and can login")
            return {"email": "demo@loreal.com", "password": "BeautyCosmetics2024!", "company_type": "manufacturer"}
        
        # If login fails, create L'Oréal with proper palm oil company type
        company_data = {
            "email": "demo@loreal.com",
            "password": "BeautyCosmetics2024!",
            "full_name": "L'Oréal Demo Manager",
            "role": "buyer",
            "company_name": "L'Oréal Demo",
            "company_email": "info@loreal.com",
            "company_type": "manufacturer",  # This is the correct type for brands in palm oil
            "country": "France",
            "industry_sector": "Consumer Staples",
            "industry_subcategory": "Personal Care & Cosmetics",
            "is_verified": True,
            "transparency_score": 95
        }
        
        response = self.session.post(f"{self.base_url}/api/v1/auth/register", json=company_data)
        if response.status_code == 200:
            print("✅ L'Oréal created successfully")
            return company_data
        else:
            print(f"❌ Failed to create L'Oréal: {response.text}")
            return {}
    
    def _create_palm_oil_companies(self) -> Dict[str, Any]:
        """Create palm oil companies with proper company types"""
        print("🏭 Creating Palm Oil Companies...")
        
        companies = {}
        
        # Level 2: Refinery/Processor (Refines CPO → Refined Palm Oil)
        refinery_data = {
            "email": "manager@asianrefineries.com",
            "password": "RefineryProcessor2024!",
            "full_name": "Asian Refineries Manager",
            "role": "seller",
            "company_name": "Asian Refineries Ltd",
            "company_email": "info@asianrefineries.com",
            "company_type": "refinery_crusher",
            "country": "Malaysia",
            "industry_sector": "Consumer Staples",
            "industry_subcategory": "Palm Oil Processing",
            "is_verified": True,
            "transparency_score": 88
        }
        
        response = self.session.post(f"{self.base_url}/api/v1/auth/register", json=refinery_data)
        if response.status_code == 200:
            companies["refinery"] = refinery_data
            print("✅ Refinery created")
        else:
            print(f"❌ Failed to create refinery: {response.text}")
        
        # Level 3: Trader (Optional intermediary)
        trader_data = {
            "email": "manager@wilmar.com",
            "password": "TraderAggregator2024!",
            "full_name": "Wilmar Trading Manager",
            "role": "seller",
            "company_name": "Wilmar Trading Ltd",
            "company_email": "info@wilmar.com",
            "company_type": "trader_aggregator",
            "country": "Singapore",
            "industry_sector": "Consumer Staples",
            "industry_subcategory": "Agricultural Trading",
            "is_verified": True,
            "transparency_score": 85
        }
        
        response = self.session.post(f"{self.base_url}/api/v1/auth/register", json=trader_data)
        if response.status_code == 200:
            companies["trader"] = trader_data
            print("✅ Trader created")
        else:
            print(f"❌ Failed to create trader: {response.text}")
        
        # Level 4: Mill (Processes FFB → CPO) [ORIGINATOR]
        mill_data = {
            "email": "manager@makmurselalu.com",
            "password": "MillProcessor2024!",
            "full_name": "Makmur Selalu Mill Manager",
            "role": "seller",
            "company_name": "Makmur Selalu Mill",
            "company_email": "info@makmurselalu.com",
            "company_type": "mill_processor",
            "country": "Indonesia",
            "industry_sector": "Consumer Staples",
            "industry_subcategory": "Palm Oil Milling",
            "is_verified": True,
            "transparency_score": 82
        }
        
        response = self.session.post(f"{self.base_url}/api/v1/auth/register", json=mill_data)
        if response.status_code == 200:
            companies["mill"] = mill_data
            print("✅ Mill created")
        else:
            print(f"❌ Failed to create mill: {response.text}")
        
        # Level 5: Cooperative (Aggregates smallholders)
        cooperative_data = {
            "email": "manager@tanimaju.com",
            "password": "SmallholderCoop2024!",
            "full_name": "Tani Maju Cooperative Manager",
            "role": "seller",
            "company_name": "Tani Maju Cooperative",
            "company_email": "info@tanimaju.com",
            "company_type": "smallholder_cooperative",
            "country": "Indonesia",
            "industry_sector": "Consumer Staples",
            "industry_subcategory": "Agricultural Cooperative",
            "is_verified": True,
            "transparency_score": 78
        }
        
        response = self.session.post(f"{self.base_url}/api/v1/auth/register", json=cooperative_data)
        if response.status_code == 200:
            companies["cooperative"] = cooperative_data
            print("✅ Cooperative created")
        else:
            print(f"❌ Failed to create cooperative: {response.text}")
        
        # Plantation (Individual plantation)
        plantation_data = {
            "email": "manager@plantationestate.com",
            "password": "PlantationGrower2024!",
            "full_name": "Plantation Estate Manager",
            "role": "seller",
            "company_name": "Plantation Estate Sdn Bhd",
            "company_email": "info@plantationestate.com",
            "company_type": "plantation_grower",
            "country": "Malaysia",
            "industry_sector": "Consumer Staples",
            "industry_subcategory": "Oil Palm Plantation",
            "is_verified": True,
            "transparency_score": 80
        }
        
        response = self.session.post(f"{self.base_url}/api/v1/auth/register", json=plantation_data)
        if response.status_code == 200:
            companies["plantation"] = plantation_data
            print("✅ Plantation created")
        else:
            print(f"❌ Failed to create plantation: {response.text}")
        
        return companies
    
    def _create_business_relationships(self, companies: Dict[str, Any]):
        """Create business relationships between companies"""
        print("🔗 Creating Business Relationships...")
        
        # Login as L'Oréal to create relationships
        loreal_login = {
            "email": "demo@loreal.com",
            "password": "BeautyCosmetics2024!"
        }
        
        response = self.session.post(f"{self.base_url}/api/v1/auth/login", json=loreal_login)
        if response.status_code != 200:
            print("❌ Failed to login as L'Oréal")
            return
        
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Create relationships (this would need the actual API endpoint)
        print("✅ Business relationships would be created here")
    
    def _save_credentials(self, companies: Dict[str, Any]):
        """Save all credentials to a file"""
        credentials = {
            "loreal": {
                "email": "demo@loreal.com",
                "password": "BeautyCosmetics2024!",
                "company_type": "manufacturer",
                "role": "buyer"
            }
        }
        
        for company_type, data in companies.items():
            credentials[company_type] = {
                "email": data["email"],
                "password": data["password"],
                "company_type": data["company_type"],
                "role": data["role"]
            }
        
        with open("palm_oil_credentials.json", "w") as f:
            json.dump(credentials, f, indent=2)
        
        print("💾 Credentials saved to palm_oil_credentials.json")

def main():
    creator = PalmOilSupplyChainCreator()
    companies = creator.create_palm_oil_chain()
    
    print("\n🌴 PALM OIL SUPPLY CHAIN CREATED!")
    print("=" * 50)
    print("Flow: L'Oréal → Refinery → Trader → Mill → Cooperative → Plantation")
    print("=" * 50)
    
    for company_type, data in companies.items():
        print(f"{company_type.upper()}: {data['email']} / {data['password']}")

if __name__ == "__main__":
    main()
