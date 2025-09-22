#!/usr/bin/env python3
"""
Create Additional Suppliers for L'Oréal Supply Chain
===================================================

This script creates additional suppliers to make the L'Oréal supply chain more comprehensive
by building on the existing users we already have.
"""

import os
import sys
import uuid
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Any

class AdditionalSuppliersCreator:
    """Creates additional suppliers for the L'Oréal supply chain."""
    
    def __init__(self):
        self.base_url = "http://127.0.0.1:8000"
        self.created_data = {
            'companies': {},
            'users': {},
            'credentials': {}
        }
        self.session = requests.Session()
        
    def create_additional_suppliers(self):
        """Create additional suppliers to make the supply chain more comprehensive."""
        print("🏭 Creating Additional Suppliers for L'Oréal Supply Chain...")
        print("=" * 70)
        
        try:
            # 1. Create Tier 1 Suppliers (Major Manufacturers)
            self._create_tier1_suppliers()
            
            # 2. Create Tier 2 Suppliers (Component suppliers)
            self._create_tier2_suppliers()
            
            # 3. Create Tier 3 Suppliers (Raw material suppliers)
            self._create_tier3_suppliers()
            
            # 4. Create Originators (Farmers/Extractors)
            self._create_originators()
            
            # 5. Save credentials to file
            self._save_credentials()
            
            print("\n✅ Additional suppliers created successfully!")
            
        except Exception as e:
            print(f"❌ Error creating additional suppliers: {e}")
            raise
    
    def _create_tier1_suppliers(self):
        """Create Tier 1 suppliers (Major Manufacturers)."""
        print("🏭 Creating Tier 1 Suppliers (Major Manufacturers)...")
        
        tier1_suppliers = [
            {
                'name': 'European Beauty Manufacturing',
                'email': 'contact@europeanbeauty.fr',
                'country': 'France',
                'city': 'Lyon',
                'specialty': 'Professional beauty products',
                'user_email': 'manager@europeanbeauty.fr'
            },
            {
                'name': 'Nordic Cosmetics AB',
                'email': 'info@nordiccosmetics.se',
                'country': 'Sweden',
                'city': 'Stockholm',
                'specialty': 'Natural and organic cosmetics',
                'user_email': 'manager@nordiccosmetics.se'
            },
            {
                'name': 'Mediterranean Beauty Solutions',
                'email': 'hello@medbeauty.es',
                'country': 'Spain',
                'city': 'Barcelona',
                'specialty': 'Mediterranean-inspired cosmetics',
                'user_email': 'manager@medbeauty.es'
            },
            {
                'name': 'Alpine Cosmetics GmbH',
                'email': 'contact@alpinecosmetics.at',
                'country': 'Austria',
                'city': 'Vienna',
                'specialty': 'Alpine natural ingredients',
                'user_email': 'manager@alpinecosmetics.at'
            }
        ]
        
        for i, supplier_data in enumerate(tier1_suppliers, 1):
            response = self.session.post(f"{self.base_url}/api/v1/auth/register", json={
                "email": supplier_data['user_email'],
                "password": f"Tier1Supplier{i+2}2024!",
                "full_name": f"Manager {supplier_data['name']}",
                "role": "seller",
                "company_name": supplier_data['name'],
                "company_email": supplier_data['email'],
                "company_type": "manufacturer",
                "country": supplier_data['country']
            })
            
            if response.status_code == 200:
                user_data = response.json()
                self.created_data['companies'][f'tier1_{i+2}'] = {
                    'id': user_data.get('company_id', str(uuid.uuid4())),
                    'name': supplier_data['name'],
                    'type': 'manufacturer',
                    'tier': 1,
                    'parent': 'loreal',
                    'user_email': supplier_data['user_email'],
                    'password': f"Tier1Supplier{i+2}2024!"
                }
                print(f"✅ Created Tier 1 Supplier {i+2}: {supplier_data['name']}")
            else:
                print(f"❌ Failed to create Tier 1 Supplier {i+2}: {response.text}")
    
    def _create_tier2_suppliers(self):
        """Create Tier 2 suppliers (Component suppliers)."""
        print("🔧 Creating Tier 2 Suppliers (Component suppliers)...")
        
        # Create 3 suppliers for each Tier 1 supplier (including existing ones)
        tier2_suppliers = []
        
        for tier1_idx in range(1, 6):  # 5 tier1 suppliers total
            for sub_idx in range(1, 4):  # 3 suppliers per tier1
                supplier_num = (tier1_idx - 1) * 3 + sub_idx
                
                # Create diverse supplier types
                supplier_types = [
                    {
                        'name': f'Premium Packaging Solutions {supplier_num}',
                        'specialty': 'Luxury packaging and containers',
                        'country': 'Germany',
                        'city': 'Munich'
                    },
                    {
                        'name': f'Chemical Components Ltd {supplier_num}',
                        'specialty': 'Cosmetic chemicals and ingredients',
                        'country': 'France',
                        'city': 'Lyon'
                    },
                    {
                        'name': f'Fragrance Ingredients Co {supplier_num}',
                        'specialty': 'Perfume and fragrance ingredients',
                        'country': 'Italy',
                        'city': 'Florence'
                    }
                ]
                
                supplier_data = supplier_types[sub_idx - 1]
                
                response = self.session.post(f"{self.base_url}/api/v1/auth/register", json={
                    "email": f"manager@tier2{supplier_num}.com",
                    "password": f"Tier2Supplier{supplier_num}2024!",
                    "full_name": f"Manager {supplier_data['name']}",
                    "role": "seller",
                    "company_name": supplier_data['name'],
                    "company_email": f"contact@tier2{supplier_num}.com",
                    "company_type": "manufacturer",
                    "country": supplier_data['country']
                })
                
                if response.status_code == 200:
                    user_data = response.json()
                    self.created_data['companies'][f'tier2_{supplier_num}'] = {
                        'id': user_data.get('company_id', str(uuid.uuid4())),
                        'name': supplier_data['name'],
                        'type': 'component_supplier',
                        'tier': 2,
                        'parent': f'tier1_{tier1_idx}',
                        'user_email': f"manager@tier2{supplier_num}.com",
                        'password': f"Tier2Supplier{supplier_num}2024!"
                    }
                    
                    if supplier_num % 3 == 0:  # Print every 3rd to avoid spam
                        print(f"✅ Created Tier 2 Suppliers {supplier_num-2}-{supplier_num}")
                else:
                    print(f"❌ Failed to create Tier 2 Supplier {supplier_num}: {response.text}")
    
    def _create_tier3_suppliers(self):
        """Create Tier 3 suppliers (Raw material suppliers)."""
        print("🌿 Creating Tier 3 Suppliers (Raw material suppliers)...")
        
        # Create 3 suppliers for each tier2 supplier
        for tier2_idx in range(1, 16):  # 15 tier2 suppliers
            for sub_idx in range(1, 4):  # 3 suppliers per tier2
                supplier_num = (tier2_idx - 1) * 3 + sub_idx
                
                # Create diverse supplier types
                supplier_types = [
                    {
                        'name': f'Raw Materials Co {supplier_num}',
                        'specialty': 'Base ingredients and raw materials',
                        'country': 'Spain',
                        'city': f'City{supplier_num}'
                    },
                    {
                        'name': f'Natural Extracts Ltd {supplier_num}',
                        'specialty': 'Plant extracts and natural ingredients',
                        'country': 'Portugal',
                        'city': f'Porto{supplier_num}'
                    },
                    {
                        'name': f'Chemical Suppliers {supplier_num}',
                        'specialty': 'Synthetic ingredients and chemicals',
                        'country': 'Netherlands',
                        'city': f'Amsterdam{supplier_num}'
                    }
                ]
                
                supplier_data = supplier_types[sub_idx - 1]
                
                response = self.session.post(f"{self.base_url}/api/v1/auth/register", json={
                    "email": f"manager@tier3{supplier_num}.com",
                    "password": f"Tier3Supplier{supplier_num}2024!",
                    "full_name": f"Manager {supplier_data['name']}",
                    "role": "seller",
                    "company_name": supplier_data['name'],
                    "company_email": f"contact@tier3{supplier_num}.com",
                    "company_type": "manufacturer",
                    "country": supplier_data['country']
                })
                
                if response.status_code == 200:
                    user_data = response.json()
                    self.created_data['companies'][f'tier3_{supplier_num}'] = {
                        'id': user_data.get('company_id', str(uuid.uuid4())),
                        'name': supplier_data['name'],
                        'type': 'raw_material_supplier',
                        'tier': 3,
                        'parent': f'tier2_{tier2_idx}',
                        'user_email': f"manager@tier3{supplier_num}.com",
                        'password': f"Tier3Supplier{supplier_num}2024!"
                    }
                    
                    if supplier_num % 9 == 0:  # Print every 9th to avoid spam
                        print(f"✅ Created Tier 3 Suppliers {supplier_num-8}-{supplier_num}")
                else:
                    print(f"❌ Failed to create Tier 3 Supplier {supplier_num}: {response.text}")
    
    def _create_originators(self):
        """Create Originators (Farmers/Extractors)."""
        print("🌱 Creating Originators (Farmers/Extractors)...")
        
        originator_types = [
            {'name': 'Organic Farms', 'specialty': 'Organic ingredients', 'country': 'Morocco'},
            {'name': 'Sustainable Harvest', 'specialty': 'Sustainable farming', 'country': 'Tunisia'},
            {'name': 'Natural Extracts', 'specialty': 'Plant extraction', 'country': 'Algeria'}
        ]
        
        for tier3_idx in range(1, 46):  # 45 tier3 suppliers
            for sub_idx in range(1, 4):  # 3 originators per tier3
                originator_num = (tier3_idx - 1) * 3 + sub_idx
                originator_data = originator_types[sub_idx - 1]
                
                response = self.session.post(f"{self.base_url}/api/v1/auth/register", json={
                    "email": f"manager@originator{originator_num}.com",
                    "password": f"Originator{originator_num}2024!",
                    "full_name": f"Manager {originator_data['name']} {originator_num}",
                    "role": "seller",
                    "company_name": f"{originator_data['name']} {originator_num}",
                    "company_email": f"contact@originator{originator_num}.com",
                    "company_type": "plantation_grower",
                    "country": originator_data['country']
                })
                
                if response.status_code == 200:
                    user_data = response.json()
                    self.created_data['companies'][f'originator_{originator_num}'] = {
                        'id': user_data.get('company_id', str(uuid.uuid4())),
                        'name': f"{originator_data['name']} {originator_num}",
                        'type': 'originator',
                        'tier': 4,
                        'parent': f'tier3_{tier3_idx}',
                        'user_email': f"manager@originator{originator_num}.com",
                        'password': f"Originator{originator_num}2024!"
                    }
                else:
                    print(f"❌ Failed to create Originator {originator_num}: {response.text}")
        
        print("✅ Created 135 Originators")
    
    def _save_credentials(self):
        """Save credentials to a file."""
        print("💾 Saving credentials...")
        
        # Combine with existing credentials
        all_credentials = {
            # Existing credentials
            'loreal': {
                'company_name': "L'Oréal Demo",
                'company_type': 'brand',
                'admin_user': {
                    'email': 'demo@loreal.com',
                    'password': 'BeautyCosmetics2024!',
                    'role': 'buyer'
                }
            },
            'tier1_1': {
                'company_name': 'Cosmetic Manufacturing Solutions',
                'company_type': 'manufacturer',
                'admin_user': {
                    'email': 'supplier@manufacturing.com',
                    'password': 'Manufacturing2024!',
                    'role': 'seller'
                }
            },
            'originator_1': {
                'company_name': 'Organic Farms Morocco',
                'company_type': 'originator',
                'admin_user': {
                    'email': 'originator@organicfarms.com',
                    'password': 'OrganicFarms2024!',
                    'role': 'seller'
                }
            }
        }
        
        # Add new credentials
        for company_key, company_data in self.created_data['companies'].items():
            all_credentials[company_key] = {
                'company_name': company_data['name'],
                'company_type': company_data['type'],
                'admin_user': {
                    'email': company_data['user_email'],
                    'password': company_data['password'],
                    'role': 'seller'
                }
            }
        
        credentials_file = "comprehensive_loreal_credentials.json"
        
        with open(credentials_file, 'w') as f:
            json.dump(all_credentials, f, indent=2)
        
        print(f"✅ Credentials saved to {credentials_file}")
        
        # Create comprehensive summary
        summary_file = "comprehensive_loreal_summary.md"
        
        with open(summary_file, 'w') as f:
            f.write("# Comprehensive L'Oréal Supply Chain - Complete Test Credentials\n\n")
            f.write("## Overview\n")
            f.write(f"- **Total Companies**: {len(all_credentials)}\n")
            f.write(f"- **Brand**: 1 (L'Oréal)\n")
            f.write(f"- **Tier 1 Suppliers**: 5 (Major Manufacturers)\n")
            f.write(f"- **Tier 2 Suppliers**: 15 (Component suppliers)\n")
            f.write(f"- **Tier 3 Suppliers**: 45 (Raw material suppliers)\n")
            f.write(f"- **Originators**: 135 (Farmers/Extractors)\n\n")
            
            f.write("## Complete Supply Chain Structure\n\n")
            f.write("```\n")
            f.write("L'Oréal Group (Brand)\n")
            f.write("├── Tier 1: Cosmetic Manufacturing Solutions (Germany) - EXISTING\n")
            f.write("│   ├── Tier 2: Premium Packaging Solutions 1\n")
            f.write("│   │   ├── Tier 3: Raw Materials Co 1\n")
            f.write("│   │   │   ├── Originator: Organic Farms 1 - EXISTING\n")
            f.write("│   │   │   ├── Originator: Sustainable Harvest 2\n")
            f.write("│   │   │   └── Originator: Natural Extracts 3\n")
            f.write("│   │   ├── Tier 3: Natural Extracts Ltd 2\n")
            f.write("│   │   └── Tier 3: Chemical Suppliers 3\n")
            f.write("│   ├── Tier 2: Chemical Components Ltd 2\n")
            f.write("│   └── Tier 2: Fragrance Ingredients Co 3\n")
            f.write("├── Tier 1: Beauty Production International (Italy) - NEW\n")
            f.write("├── Tier 1: Global Cosmetics Ltd (UK) - NEW\n")
            f.write("├── Tier 1: European Beauty Manufacturing (France) - NEW\n")
            f.write("└── Tier 1: Nordic Cosmetics AB (Sweden) - NEW\n")
            f.write("```\n\n")
            
            f.write("## Test Credentials\n\n")
            f.write("### Existing Users (Already Working)\n")
            f.write("#### L'Oréal Brand\n")
            f.write("- **Email**: `demo@loreal.com`\n")
            f.write("- **Password**: `BeautyCosmetics2024!`\n")
            f.write("- **Role**: Buyer\n\n")
            
            f.write("#### Cosmetic Manufacturing Solutions (Tier 1)\n")
            f.write("- **Email**: `supplier@manufacturing.com`\n")
            f.write("- **Password**: `Manufacturing2024!`\n")
            f.write("- **Role**: Seller\n\n")
            
            f.write("#### Organic Farms Morocco (Originator)\n")
            f.write("- **Email**: `originator@organicfarms.com`\n")
            f.write("- **Password**: `OrganicFarms2024!`\n")
            f.write("- **Role**: Seller\n\n")
            
            f.write("### New Tier 1 Suppliers (Major Manufacturers)\n")
            for i in range(3, 7):  # tier1_3 to tier1_6
                if f'tier1_{i}' in all_credentials:
                    creds = all_credentials[f'tier1_{i}']
                    f.write(f"#### {creds['company_name']}\n")
                    f.write(f"- **Email**: `{creds['admin_user']['email']}`\n")
                    f.write(f"- **Password**: `{creds['admin_user']['password']}`\n")
                    f.write(f"- **Role**: Seller\n\n")
            
            f.write("### Sample Tier 2 Suppliers (Component Suppliers)\n")
            for i in [1, 4, 7, 10, 13]:  # Sample 5 from different tier1s
                if f'tier2_{i}' in all_credentials:
                    creds = all_credentials[f'tier2_{i}']
                    f.write(f"#### {creds['company_name']}\n")
                    f.write(f"- **Email**: `{creds['admin_user']['email']}`\n")
                    f.write(f"- **Password**: `{creds['admin_user']['password']}`\n")
                    f.write(f"- **Role**: Seller\n\n")
            
            f.write("### Sample Tier 3 Suppliers (Raw Material Suppliers)\n")
            for i in [1, 4, 7, 10, 13, 16, 19, 22, 25]:  # Sample 9
                if f'tier3_{i}' in all_credentials:
                    creds = all_credentials[f'tier3_{i}']
                    f.write(f"#### {creds['company_name']}\n")
                    f.write(f"- **Email**: `{creds['admin_user']['email']}`\n")
                    f.write(f"- **Password**: `{creds['admin_user']['password']}`\n")
                    f.write(f"- **Role**: Seller\n\n")
            
            f.write("### Sample Originators (Farmers/Extractors)\n")
            for i in [1, 4, 7, 10, 13, 16, 19, 22, 25, 28, 31, 34]:  # Sample 12
                if f'originator_{i}' in all_credentials:
                    creds = all_credentials[f'originator_{i}']
                    f.write(f"#### {creds['company_name']}\n")
                    f.write(f"- **Email**: `{creds['admin_user']['email']}`\n")
                    f.write(f"- **Password**: `{creds['admin_user']['password']}`\n")
                    f.write(f"- **Role**: Seller\n\n")
            
            f.write("## Testing Instructions\n\n")
            f.write("1. **Access the System**: Open http://localhost:3000\n")
            f.write("2. **Start with Existing Users**: Use the existing credentials to test basic functionality\n")
            f.write("3. **Test New Suppliers**: Use the new credentials to test the expanded supply chain\n")
            f.write("4. **Create Purchase Orders**: Test the complete flow from brand to originator\n")
            f.write("5. **Test Multi-Tier Relationships**: Verify relationships between different tiers\n\n")
            
            f.write("## Key Features to Test\n\n")
            f.write("- **Multi-Tier Supply Chain**: 4 levels from brand to originator\n")
            f.write("- **Multiple Suppliers per Tier**: Realistic supplier diversity\n")
            f.write("- **Geographic Distribution**: Suppliers across Europe and North Africa\n")
            f.write("- **Role-Based Access**: Different permissions for different user types\n")
            f.write("- **Supply Chain Transparency**: Complete traceability from origin to brand\n")
            f.write("- **Purchase Order Chaining**: Automatic creation of downstream orders\n\n")
            
            f.write("## API Endpoints for Testing\n\n")
            f.write("- **Login**: `POST /api/v1/auth/login`\n")
            f.write("- **Purchase Orders**: `GET /api/v1/simple/purchase-orders`\n")
            f.write("- **Relationships**: `GET /api/v1/simple/relationships/suppliers`\n")
            f.write("- **Traceability**: `GET /api/v1/traceability`\n")
            f.write("- **Companies**: `GET /api/v1/companies`\n")
        
        print(f"✅ Summary saved to {summary_file}")


def main():
    """Main function."""
    print("🏭 Additional Suppliers Creator for L'Oréal Supply Chain")
    print("=" * 70)
    
    creator = AdditionalSuppliersCreator()
    creator.create_additional_suppliers()
    
    print("\n🎉 Additional suppliers creation completed!")
    print("Check the generated files for credentials and summary.")


if __name__ == "__main__":
    main()
