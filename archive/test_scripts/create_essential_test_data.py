#!/usr/bin/env python3
"""
Essential test data creation script
Creates the minimum viable set of companies and users for comprehensive testing
"""
import sys
import os
sys.path.append('/Users/elisha/common')

from app.core.database import SessionLocal
from app.models.user import User
from app.models.company import Company
from app.core.security import hash_password
from uuid import uuid4

def create_essential_test_data():
    """Create essential test data for comprehensive testing"""
    
    print("🎯 Creating essential test data...")
    print("=" * 50)
    
    db = SessionLocal()
    
    try:
        # Essential supply chain companies
        essential_data = [
            # ORIGINATOR
            {
                'company': {
                    'name': 'Green Valley Farms',
                    'company_type': 'originator',
                    'email': 'contact@greenvalleyfarms.com',
                    'phone': '+1-555-100-0001',
                    'address_street': '123 Farm Road',
                    'address_city': 'Rural Valley',
                    'address_country': 'United States',
                    'website': 'https://www.greenvalleyfarms.com',
                    'sector_id': 'palm_oil',
                    'tier_level': 6
                },
                'users': [
                    {
                        'email': 'farmer@greenvalleyfarms.com',
                        'password': 'password123',
                        'full_name': 'John Farmer',
                        'role': 'originator'
                    }
                ]
            },
            
            # MILL/PROCESSOR
            {
                'company': {
                    'name': 'Valley Processing Mill',
                    'company_type': 'mill_processor',
                    'email': 'info@valleymill.com',
                    'phone': '+1-555-200-0002',
                    'address_street': '456 Industrial Blvd',
                    'address_city': 'Processing City',
                    'address_country': 'United States',
                    'website': 'https://www.valleymill.com',
                    'sector_id': 'palm_oil',
                    'tier_level': 5
                },
                'users': [
                    {
                        'email': 'processor@valleymill.com',
                        'password': 'password123',
                        'full_name': 'Sarah Processor',
                        'role': 'processor'
                    }
                ]
            },
            
            # TRADER
            {
                'company': {
                    'name': 'Global Commodities Inc',
                    'company_type': 'trader',
                    'email': 'trading@globalcommodities.com',
                    'phone': '+1-555-300-0003',
                    'address_street': '789 Trading Floor',
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
                        'full_name': 'Mike Trader',
                        'role': 'trader'
                    }
                ]
            },
            
            # MANUFACTURER
            {
                'company': {
                    'name': 'Food Manufacturing Co',
                    'company_type': 'manufacturer',
                    'email': 'production@foodmfg.com',
                    'phone': '+1-555-400-0004',
                    'address_street': '321 Factory Lane',
                    'address_city': 'Manufacturing City',
                    'address_country': 'United States',
                    'website': 'https://www.foodmfg.com',
                    'sector_id': 'palm_oil',
                    'tier_level': 3
                },
                'users': [
                    {
                        'email': 'manufacturer@foodmfg.com',
                        'password': 'password123',
                        'full_name': 'Lisa Manufacturer',
                        'role': 'manufacturer'
                    }
                ]
            },
            
            # BRAND
            {
                'company': {
                    'name': 'Sustainable Brand Corp',
                    'company_type': 'brand',
                    'email': 'brand@sustainablebrand.com',
                    'phone': '+1-555-500-0005',
                    'address_street': '654 Brand Avenue',
                    'address_city': 'Brand City',
                    'address_country': 'United States',
                    'website': 'https://www.sustainablebrand.com',
                    'sector_id': 'palm_oil',
                    'tier_level': 2
                },
                'users': [
                    {
                        'email': 'brand@sustainablebrand.com',
                        'password': 'password123',
                        'full_name': 'Emma Brand Manager',
                        'role': 'brand_manager'
                    }
                ]
            },
            
            # CONSULTANT
            {
                'company': {
                    'name': 'Supply Chain Consultants',
                    'company_type': 'consultant',
                    'email': 'consulting@supplychainconsultants.com',
                    'phone': '+1-555-600-0006',
                    'address_street': '987 Consulting Tower',
                    'address_city': 'Consulting City',
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
                        'role': 'consultant'
                    }
                ]
            }
        ]
        
        # Create companies and users
        created_count = 0
        
        for data in essential_data:
            company_data = data['company']
            users_data = data['users']
            
            # Check if company already exists
            existing_company = db.query(Company).filter(Company.name == company_data['name']).first()
            if existing_company:
                print(f"📋 Using existing: {company_data['name']}")
                company = existing_company
            else:
                # Create company
                company = Company(
                    id=uuid4(),
                    **company_data
                )
                db.add(company)
                db.flush()
                print(f"🏢 Created: {company_data['name']} ({company_data['company_type']})")
                created_count += 1
            
            # Create users for this company
            for user_data in users_data:
                # Check if user already exists
                existing_user = db.query(User).filter(User.email == user_data['email']).first()
                if existing_user:
                    print(f"  👤 User exists: {user_data['email']}")
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
                    is_active=True
                )
                db.add(user)
                print(f"  👤 Created: {user_data['email']} ({user_data['role']})")
                created_count += 1
        
        # Commit all changes
        db.commit()
        
        print("\n" + "=" * 50)
        print("✅ ESSENTIAL TEST DATA CREATED SUCCESSFULLY!")
        print("=" * 50)
        
        # Display login credentials
        print(f"\n🔐 LOGIN CREDENTIALS (All use password: password123):")
        print("-" * 50)
        
        for data in essential_data:
            company = data['company']
            print(f"\n🏢 {company['name']} ({company['company_type'].upper()})")
            for user_data in data['users']:
                print(f"  📧 {user_data['email']} - {user_data['full_name']} ({user_data['role']})")
        
        print(f"\n🌐 ACCESS:")
        print(f"  🖥️  Frontend: http://localhost:3000")
        print(f"  📚 API Docs: http://localhost:8000/docs")
        
        print(f"\n💡 TESTING SCENARIOS:")
        print(f"  🌱 Originator: Test origin dashboard, farm management")
        print(f"  ⚙️  Processor: Test processing workflows, inventory")
        print(f"  📈 Trader: Test trading, risk management")
        print(f"  🏭 Manufacturer: Test production, quality control")
        print(f"  🏷️  Brand: Test transparency dashboard, sustainability")
        print(f"  🔧 Consultant: Test multi-client features, analytics")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_essential_test_data()
