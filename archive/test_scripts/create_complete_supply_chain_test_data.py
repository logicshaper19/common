#!/usr/bin/env python3
"""
Comprehensive test data creation script for the complete supply chain
Creates users and companies for all company types from originators to brands
"""
import sys
import os
sys.path.append('/Users/elisha/common')

from app.core.database import SessionLocal
from app.models.user import User
from app.models.company import Company
from app.core.security import hash_password
from uuid import uuid4

def create_complete_supply_chain_test_data():
    """Create comprehensive test data for the entire supply chain"""
    
    print("🌍 Creating complete supply chain test data...")
    print("=" * 60)
    
    db = SessionLocal()
    
    try:
        # Define the complete supply chain with all company types
        supply_chain_data = [
            # TIER 6-7: ORIGINATORS (Primary Producers)
            {
                'company': {
                    'name': 'Kalimantan Palm Plantation',
                    'company_type': 'originator',
                    'email': 'contact@kalimantanplantation.com',
                    'phone': '+62-123-456-7890',
                    'address_street': 'Jalan Sawit No. 1',
                    'address_city': 'Pontianak',
                    'address_country': 'Indonesia',
                    'website': 'https://www.kalimantanplantation.com',
                    'sector_id': 'palm_oil',
                    'tier_level': 6
                },
                'users': [
                    {
                        'email': 'farmmanager@kalimantanplantation.com',
                        'password': 'password123',
                        'full_name': 'Ahmad Farm Manager',
                        'role': 'originator',
                        'permissions': ['add_origin_data', 'provide_farmer_data', 'manage_farms']
                    },
                    {
                        'email': 'harvest@kalimantanplantation.com',
                        'password': 'password123',
                        'full_name': 'Siti Harvest Coordinator',
                        'role': 'harvest_coordinator',
                        'permissions': ['add_origin_data', 'record_harvest']
                    }
                ]
            },
            {
                'company': {
                    'name': 'Sumatra Smallholder Cooperative',
                    'company_type': 'originator',
                    'email': 'info@sumatracoop.com',
                    'phone': '+62-987-654-3210',
                    'address_street': 'Jalan Koperasi No. 15',
                    'address_city': 'Medan',
                    'address_country': 'Indonesia',
                    'website': 'https://www.sumatracoop.com',
                    'sector_id': 'palm_oil',
                    'tier_level': 6
                },
                'users': [
                    {
                        'email': 'coopmanager@sumatracoop.com',
                        'password': 'password123',
                        'full_name': 'Budi Cooperative Manager',
                        'role': 'originator',
                        'permissions': ['add_origin_data', 'manage_smallholders']
                    }
                ]
            },
            
            # TIER 5: MILLS/PROCESSORS
            {
                'company': {
                    'name': 'Southeast Asia Palm Oil Mill',
                    'company_type': 'mill_processor',
                    'email': 'operations@seapalmill.com',
                    'phone': '+60-3-1234-5678',
                    'address_street': 'Industrial Zone 1',
                    'address_city': 'Kuala Lumpur',
                    'address_country': 'Malaysia',
                    'website': 'https://www.seapalmill.com',
                    'sector_id': 'palm_oil',
                    'tier_level': 5
                },
                'users': [
                    {
                        'email': 'millmanager@seapalmill.com',
                        'password': 'password123',
                        'full_name': 'Chen Mill Manager',
                        'role': 'processor',
                        'permissions': ['process_orders', 'manage_inventory', 'confirm_orders']
                    },
                    {
                        'email': 'quality@seapalmill.com',
                        'password': 'password123',
                        'full_name': 'Maria Quality Control',
                        'role': 'quality_manager',
                        'permissions': ['quality_control', 'certification_management']
                    }
                ]
            },
            {
                'company': {
                    'name': 'Tropical Refinery Ltd',
                    'company_type': 'processor',
                    'email': 'contact@tropicalrefinery.com',
                    'phone': '+65-6123-4567',
                    'address_street': 'Refinery Complex A',
                    'address_city': 'Singapore',
                    'address_country': 'Singapore',
                    'website': 'https://www.tropicalrefinery.com',
                    'sector_id': 'palm_oil',
                    'tier_level': 5
                },
                'users': [
                    {
                        'email': 'refinery@tropicalrefinery.com',
                        'password': 'password123',
                        'full_name': 'David Refinery Manager',
                        'role': 'processor',
                        'permissions': ['process_orders', 'refine_oil', 'manage_batches']
                    }
                ]
            },
            
            # TIER 4: TRADERS
            {
                'company': {
                    'name': 'Global Commodities Trading',
                    'company_type': 'trader',
                    'email': 'trading@globalcommodities.com',
                    'phone': '+1-555-123-4567',
                    'address_street': 'Wall Street 100',
                    'address_city': 'New York',
                    'address_country': 'United States',
                    'website': 'https://www.globalcommodities.com',
                    'sector_id': 'palm_oil',
                    'tier_level': 4
                },
                'users': [
                    {
                        'email': 'trader@globalcommodities.com',
                        'password': 'password123',
                        'full_name': 'John Trader',
                        'role': 'trader',
                        'permissions': ['trade_commodities', 'manage_contracts', 'risk_management']
                    },
                    {
                        'email': 'analyst@globalcommodities.com',
                        'password': 'password123',
                        'full_name': 'Sarah Market Analyst',
                        'role': 'market_analyst',
                        'permissions': ['market_analysis', 'price_forecasting']
                    }
                ]
            },
            {
                'company': {
                    'name': 'Asian Palm Oil Traders',
                    'company_type': 'trader',
                    'email': 'info@asianpalmtraders.com',
                    'phone': '+60-3-9876-5432',
                    'address_street': 'Kuala Lumpur Financial District',
                    'address_city': 'Kuala Lumpur',
                    'address_country': 'Malaysia',
                    'website': 'https://www.asianpalmtraders.com',
                    'sector_id': 'palm_oil',
                    'tier_level': 4
                },
                'users': [
                    {
                        'email': 'trader@asianpalmtraders.com',
                        'password': 'password123',
                        'full_name': 'Ahmad Trading Manager',
                        'role': 'trader',
                        'permissions': ['trade_commodities', 'supply_chain_management']
                    }
                ]
            },
            
            # TIER 3: MANUFACTURERS/PROCESSORS
            {
                'company': {
                    'name': 'Food Manufacturing Corp',
                    'company_type': 'manufacturer',
                    'email': 'contact@foodmanufacturing.com',
                    'phone': '+1-555-987-6543',
                    'address_street': 'Industrial Park 500',
                    'address_city': 'Chicago',
                    'address_country': 'United States',
                    'website': 'https://www.foodmanufacturing.com',
                    'sector_id': 'palm_oil',
                    'tier_level': 3
                },
                'users': [
                    {
                        'email': 'production@foodmanufacturing.com',
                        'password': 'password123',
                        'full_name': 'Mike Production Manager',
                        'role': 'manufacturer',
                        'permissions': ['manufacture_products', 'quality_control', 'manage_suppliers']
                    },
                    {
                        'email': 'procurement@foodmanufacturing.com',
                        'password': 'password123',
                        'full_name': 'Lisa Procurement Manager',
                        'role': 'procurement_manager',
                        'permissions': ['procure_materials', 'supplier_management']
                    }
                ]
            },
            
            # TIER 2: BRANDS/RETAILERS
            {
                'company': {
                    'name': 'Sustainable Foods Brand',
                    'company_type': 'brand',
                    'email': 'sustainability@sustainablefoods.com',
                    'phone': '+1-555-456-7890',
                    'address_street': 'Sustainability Plaza 1',
                    'address_city': 'San Francisco',
                    'address_country': 'United States',
                    'website': 'https://www.sustainablefoods.com',
                    'sector_id': 'palm_oil',
                    'tier_level': 2
                },
                'users': [
                    {
                        'email': 'sustainability@sustainablefoods.com',
                        'password': 'password123',
                        'full_name': 'Emma Sustainability Director',
                        'role': 'brand_manager',
                        'permissions': ['brand_management', 'sustainability_tracking', 'supply_chain_oversight']
                    },
                    {
                        'email': 'procurement@sustainablefoods.com',
                        'password': 'password123',
                        'full_name': 'James Procurement Director',
                        'role': 'procurement_director',
                        'permissions': ['strategic_procurement', 'supplier_relationships']
                    }
                ]
            },
            {
                'company': {
                    'name': 'Global Retail Chain',
                    'company_type': 'brand',
                    'email': 'csr@globalretail.com',
                    'phone': '+44-20-7123-4567',
                    'address_street': 'Oxford Street 1',
                    'address_city': 'London',
                    'address_country': 'United Kingdom',
                    'website': 'https://www.globalretail.com',
                    'sector_id': 'palm_oil',
                    'tier_level': 2
                },
                'users': [
                    {
                        'email': 'csr@globalretail.com',
                        'password': 'password123',
                        'full_name': 'Charlotte CSR Manager',
                        'role': 'brand_manager',
                        'permissions': ['csr_management', 'sustainability_reporting']
                    }
                ]
            },
            
            # TIER 1: CONSUMER BRANDS
            {
                'company': {
                    'name': 'Premium Consumer Brand',
                    'company_type': 'brand',
                    'email': 'brand@premiumconsumer.com',
                    'phone': '+1-555-789-0123',
                    'address_street': 'Brand Avenue 100',
                    'address_city': 'Los Angeles',
                    'address_country': 'United States',
                    'website': 'https://www.premiumconsumer.com',
                    'sector_id': 'palm_oil',
                    'tier_level': 1
                },
                'users': [
                    {
                        'email': 'brand@premiumconsumer.com',
                        'password': 'password123',
                        'full_name': 'Alex Brand Manager',
                        'role': 'brand_manager',
                        'permissions': ['brand_strategy', 'consumer_engagement', 'transparency_reporting']
                    }
                ]
            },
            
            # CONSULTANTS/AUDITORS
            {
                'company': {
                    'name': 'Supply Chain Consultants Ltd',
                    'company_type': 'consultant',
                    'email': 'info@supplychainconsultants.com',
                    'phone': '+1-555-321-0987',
                    'address_street': 'Consulting Tower 50',
                    'address_city': 'Boston',
                    'address_country': 'United States',
                    'website': 'https://www.supplychainconsultants.com',
                    'sector_id': 'palm_oil',
                    'tier_level': 0
                },
                'users': [
                    {
                        'email': 'consultant@supplychainconsultants.com',
                        'password': 'password123',
                        'full_name': 'Dr. Smith Consultant',
                        'role': 'consultant',
                        'permissions': ['multi_client_access', 'audit_supply_chains', 'compliance_consulting']
                    }
                ]
            },
            
            # REGULATORS
            {
                'company': {
                    'name': 'Environmental Regulatory Agency',
                    'company_type': 'regulator',
                    'email': 'compliance@envregagency.gov',
                    'phone': '+1-555-654-3210',
                    'address_street': 'Government Building 1',
                    'address_city': 'Washington DC',
                    'address_country': 'United States',
                    'website': 'https://www.envregagency.gov',
                    'sector_id': 'palm_oil',
                    'tier_level': 0
                },
                'users': [
                    {
                        'email': 'inspector@envregagency.gov',
                        'password': 'password123',
                        'full_name': 'Agent Johnson Inspector',
                        'role': 'regulator',
                        'permissions': ['regulatory_oversight', 'compliance_monitoring', 'audit_access']
                    }
                ]
            }
        ]
        
        # Create companies and users
        created_companies = []
        created_users = []
        
        for chain_data in supply_chain_data:
            company_data = chain_data['company']
            users_data = chain_data['users']
            
            # Check if company already exists
            existing_company = db.query(Company).filter(Company.name == company_data['name']).first()
            if existing_company:
                print(f"📋 Using existing company: {company_data['name']}")
                company = existing_company
            else:
                # Create company
                company = Company(
                    id=uuid4(),
                    **company_data
                )
                db.add(company)
                db.flush()
                print(f"🏢 Created company: {company_data['name']} ({company_data['company_type']})")
                created_companies.append(company)
            
            # Create users for this company
            for user_data in users_data:
                # Check if user already exists
                existing_user = db.query(User).filter(User.email == user_data['email']).first()
                if existing_user:
                    print(f"  👤 User already exists: {user_data['email']}")
                    continue
                
                # Create user
                hashed_password = hash_password(user_data['password'])
                user = User(
                    id=uuid4(),
                    email=user_data['email'],
                    hashed_password=hashed_password,
                    full_name=user_data['full_name'],
                    role=user_data['role'],
                    company_id=company.id,
                    is_active=True,
                    permissions=user_data.get('permissions', [])
                )
                db.add(user)
                created_users.append((user, user_data['password']))
                print(f"  👤 Created user: {user_data['email']} ({user_data['role']})")
        
        # Commit all changes
        db.commit()
        
        print("\n" + "=" * 60)
        print("✅ SUCCESSFULLY CREATED COMPLETE SUPPLY CHAIN TEST DATA!")
        print("=" * 60)
        
        # Display summary
        print(f"\n📊 SUMMARY:")
        print(f"  🏢 Companies created: {len(created_companies)}")
        print(f"  👤 Users created: {len(created_users)}")
        
        # Display login credentials by tier
        print(f"\n🔐 LOGIN CREDENTIALS BY SUPPLY CHAIN TIER:")
        print("=" * 60)
        
        tiers = {}
        for chain_data in supply_chain_data:
            tier = chain_data['company']['tier_level']
            if tier not in tiers:
                tiers[tier] = []
            tiers[tier].append(chain_data)
        
        for tier in sorted(tiers.keys(), reverse=True):
            if tier == 0:
                print(f"\n🔧 TIER {tier}: CONSULTANTS & REGULATORS")
            elif tier == 1:
                print(f"\n🏷️  TIER {tier}: CONSUMER BRANDS")
            elif tier == 2:
                print(f"\n🏪 TIER {tier}: BRANDS & RETAILERS")
            elif tier == 3:
                print(f"\n🏭 TIER {tier}: MANUFACTURERS")
            elif tier == 4:
                print(f"\n📈 TIER {tier}: TRADERS")
            elif tier == 5:
                print(f"\n⚙️  TIER {tier}: MILLS & PROCESSORS")
            elif tier >= 6:
                print(f"\n🌱 TIER {tier}: ORIGINATORS")
            
            for chain_data in tiers[tier]:
                company = chain_data['company']
                print(f"\n  🏢 {company['name']} ({company['company_type']})")
                for user_data in chain_data['users']:
                    print(f"    📧 {user_data['email']} / {user_data['password']} ({user_data['role']})")
        
        print(f"\n🌐 ACCESS POINTS:")
        print(f"  🖥️  Frontend: http://localhost:3000")
        print(f"  📚 API Docs: http://localhost:8000/docs")
        print(f"  🔍 Health Check: http://localhost:8000/health/")
        
        print(f"\n💡 TESTING TIPS:")
        print(f"  • Use originator accounts to test origin dashboard")
        print(f"  • Use brand accounts to test transparency dashboard")
        print(f"  • Use consultant accounts to test multi-client features")
        print(f"  • All accounts use password: password123")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_complete_supply_chain_test_data()
