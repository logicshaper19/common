#!/usr/bin/env python3
"""
Reset test data script
Cleans up test data and optionally recreates it
"""
import sys
import os
sys.path.append('/Users/elisha/common')

from app.core.database import SessionLocal
from app.models.user import User
from app.models.company import Company
from app.models.purchase_order import PurchaseOrder
from app.models.product import Product
from app.models.batch import Batch

def reset_test_data(create_new=True):
    """Reset test data and optionally create new test data"""
    
    print("🧹 Resetting test data...")
    print("=" * 40)
    
    db = SessionLocal()
    
    try:
        # Define test company names to clean up
        test_company_names = [
            'Green Valley Farms',
            'Valley Processing Mill', 
            'Global Commodities Inc',
            'Food Manufacturing Co',
            'Sustainable Brand Corp',
            'Supply Chain Consultants',
            'Kalimantan Palm Plantation',
            'Sumatra Smallholder Cooperative',
            'Southeast Asia Palm Oil Mill',
            'Tropical Refinery Ltd',
            'Global Commodities Trading',
            'Asian Palm Oil Traders',
            'Food Manufacturing Corp',
            'Sustainable Foods Brand',
            'Global Retail Chain',
            'Premium Consumer Brand',
            'Supply Chain Consultants Ltd',
            'Environmental Regulatory Agency',
            'Test Company',
            'Organic Farms Ltd'
        ]
        
        # Define test user emails to clean up
        test_user_emails = [
            'farmer@greenvalleyfarms.com',
            'processor@valleymill.com',
            'trader@globalcommodities.com',
            'manufacturer@foodmfg.com',
            'brand@sustainablebrand.com',
            'consultant@supplychainconsultants.com',
            'farmmanager@kalimantanplantation.com',
            'harvest@kalimantanplantation.com',
            'coopmanager@sumatracoop.com',
            'millmanager@seapalmill.com',
            'quality@seapalmill.com',
            'refinery@tropicalrefinery.com',
            'trader@globalcommodities.com',
            'analyst@globalcommodities.com',
            'trader@asianpalmtraders.com',
            'production@foodmanufacturing.com',
            'procurement@foodmanufacturing.com',
            'sustainability@sustainablefoods.com',
            'procurement@sustainablefoods.com',
            'csr@globalretail.com',
            'brand@premiumconsumer.com',
            'consultant@supplychainconsultants.com',
            'inspector@envregagency.gov',
            'admin@test.com',
            'manager@test.com',
            'viewer@test.com',
            'originator@organicfarms.com'
        ]
        
        # Clean up test data in reverse dependency order
        print("🗑️  Cleaning up test data...")
        
        # 1. Delete test purchase orders
        test_pos = db.query(PurchaseOrder).join(Company).filter(
            Company.name.in_(test_company_names)
        ).all()
        for po in test_pos:
            db.delete(po)
        print(f"  📋 Deleted {len(test_pos)} test purchase orders")
        
        # 2. Delete test batches
        test_batches = db.query(Batch).join(Company).filter(
            Company.name.in_(test_company_names)
        ).all()
        for batch in test_batches:
            db.delete(batch)
        print(f"  📦 Deleted {len(test_batches)} test batches")
        
        # 3. Delete test users
        test_users = db.query(User).filter(User.email.in_(test_user_emails)).all()
        for user in test_users:
            db.delete(user)
        print(f"  👤 Deleted {len(test_users)} test users")
        
        # 4. Delete test companies
        test_companies = db.query(Company).filter(Company.name.in_(test_company_names)).all()
        for company in test_companies:
            db.delete(company)
        print(f"  🏢 Deleted {len(test_companies)} test companies")
        
        # 5. Delete test products (optional - be careful with this)
        test_products = db.query(Product).filter(
            Product.name.like('Test%') | 
            Product.name.like('%Test%')
        ).all()
        for product in test_products:
            db.delete(product)
        print(f"  🛍️  Deleted {len(test_products)} test products")
        
        # Commit cleanup
        db.commit()
        print("✅ Test data cleanup completed!")
        
        # Create new test data if requested
        if create_new:
            print("\n🌱 Creating new test data...")
            print("-" * 40)
            
            # Import and run the essential test data creation
            try:
                from create_essential_test_data import create_essential_test_data
                create_essential_test_data()
            except ImportError:
                print("❌ Could not import create_essential_test_data.py")
                print("   Make sure the file exists in the same directory")
            except Exception as e:
                print(f"❌ Error creating new test data: {e}")
        
    except Exception as e:
        print(f"❌ Error during reset: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

def main():
    """Main function with command line options"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Reset test data')
    parser.add_argument('--no-create', action='store_true', 
                       help='Only clean up, do not create new test data')
    parser.add_argument('--full', action='store_true',
                       help='Create full supply chain test data instead of essential')
    
    args = parser.parse_args()
    
    create_new = not args.no_create
    
    if create_new and args.full:
        print("🌍 Creating FULL supply chain test data...")
        try:
            from create_complete_supply_chain_test_data import create_complete_supply_chain_test_data
            reset_test_data(create_new=False)  # Clean first
            create_complete_supply_chain_test_data()
        except ImportError:
            print("❌ Could not import create_complete_supply_chain_test_data.py")
            print("   Falling back to essential test data...")
            reset_test_data(create_new=True)
    else:
        reset_test_data(create_new=create_new)

if __name__ == "__main__":
    main()
