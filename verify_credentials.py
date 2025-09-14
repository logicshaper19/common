#!/usr/bin/env python3
"""
Verify L'Oréal supply chain credentials
"""
import sys
import os
sys.path.append('/Users/elisha/common')

from app.core.database import SessionLocal
from app.models.user import User
from app.models.company import Company
from app.models.purchase_order import PurchaseOrder
from app.core.security import verify_password

def verify_credentials():
    """Verify all L'Oréal supply chain credentials"""
    
    print("🔐 VERIFYING L'ORÉAL SUPPLY CHAIN CREDENTIALS")
    print("=" * 60)
    
    db = SessionLocal()
    
    try:
        # Test credentials
        test_credentials = [
            'sustainability@loreal.com',
            'procurement@loreal.com', 
            'csr@loreal.com',
            'trader@wilmar-intl.com',
            'sustainability@wilmar-intl.com',
            'refinery@ioigroup.com',
            'quality@ioigroup.com',
            'millmanager@simeplantation.com',
            'sustainability@simeplantation.com',
            'plantation@astra-agro.com',
            'harvest@astra-agro.com',
            'sustainability@astra-agro.com',
            'coop@sawitberkelanjutan.co.id'
        ]
        
        print(f"\n🧪 Testing {len(test_credentials)} credentials...")
        print("-" * 60)
        
        success_count = 0
        for email in test_credentials:
            user = db.query(User).filter(User.email == email).first()
            if user:
                # Test password verification
                if verify_password('password123', user.hashed_password):
                    print(f"✅ {email} - {user.full_name} ({user.role})")
                    success_count += 1
                else:
                    print(f"❌ {email} - Password verification failed")
            else:
                print(f"❌ {email} - User not found")
        
        print(f"\n📊 RESULTS: {success_count}/{len(test_credentials)} credentials working")
        
        # Show company summary
        print(f"\n🏢 COMPANIES CREATED:")
        print("-" * 60)
        companies = db.query(Company).filter(Company.sector_id == 'palm_oil').all()
        for company in companies:
            user_count = db.query(User).filter(User.company_id == company.id).count()
            print(f"  {company.name} (Tier {company.tier_level}) - {user_count} users")
        
        # Show purchase order summary
        print(f"\n📋 PURCHASE ORDERS CREATED:")
        print("-" * 60)
        pos = db.query(PurchaseOrder).all()
        for po in pos:
            print(f"  {po.po_number} - Level {po.supply_chain_level} - ${po.total_amount:,.2f}")
        
        print(f"\n🎯 READY FOR TESTING!")
        print("=" * 60)
        print("All credentials use password: password123")
        print("Start backend: python -m uvicorn app.main:app --reload")
        print("Start frontend: cd frontend && npm start")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    verify_credentials()
