#!/usr/bin/env python3
"""
Complete L'Oréal Supply Chain Creation
Creates the entire L'Oréal supply chain with companies, users, products, and purchase orders
"""
import sys
import os
sys.path.append('/Users/elisha/common')

def create_complete_loreal_chain():
    """Create the complete L'Oréal supply chain"""
    
    print("💄 Creating Complete L'Oréal Supply Chain...")
    print("=" * 70)
    print("🌍 From L'Oréal (Brand) to Smallholder Cooperative (Originator)")
    print("=" * 70)
    
    try:
        # Step 1: Create companies and users
        print("\n🏢 STEP 1: Creating Companies and Users...")
        print("-" * 50)
        
        from create_loreal_supply_chain import create_loreal_supply_chain
        create_loreal_supply_chain()
        
        # Step 2: Create purchase order chain
        print("\n📋 STEP 2: Creating Purchase Order Chain...")
        print("-" * 50)
        
        from create_loreal_purchase_orders import create_loreal_purchase_order_chain
        create_loreal_purchase_order_chain()
        
        # Step 3: Display final summary
        print("\n" + "=" * 70)
        print("🎉 COMPLETE L'ORÉAL SUPPLY CHAIN CREATED SUCCESSFULLY!")
        print("=" * 70)
        
        print(f"\n🌍 SUPPLY CHAIN OVERVIEW:")
        print("=" * 70)
        print("🏷️  TIER 1: L'Oréal Group (Brand) - France")
        print("   ↓ Purchase Order: LOR-2025-001")
        print("📈 TIER 2: Wilmar International (Trader) - Singapore")
        print("   ↓ Purchase Order: WIL-2025-001")
        print("🏭 TIER 3: IOI Corporation (Refinery) - Malaysia")
        print("   ↓ Purchase Order: IOI-2025-001")
        print("⚙️  TIER 4: Sime Darby Plantation (Mill) - Malaysia")
        print("   ↓ Purchase Order: SDB-2025-001")
        print("🌱 TIER 5: PT Astra Agro Lestari (Plantation) - Indonesia")
        print("   ↓ Purchase Order: AST-2025-001")
        print("🌱 TIER 6: Koperasi Sawit Berkelanjutan (Smallholders) - Indonesia")
        
        print(f"\n🔐 LOGIN CREDENTIALS (All use password: password123):")
        print("=" * 70)
        
        credentials = [
            ("🏷️  L'Oréal Group", [
                "sustainability@loreal.com - Marie Dubois (brand_manager)",
                "procurement@loreal.com - Jean-Pierre Martin (procurement_director)",
                "csr@loreal.com - Sophie Laurent (csr_manager)"
            ]),
            ("📈 Wilmar International", [
                "trader@wilmar-intl.com - David Chen (trader)",
                "sustainability@wilmar-intl.com - Sarah Tan (sustainability_manager)"
            ]),
            ("🏭 IOI Corporation", [
                "refinery@ioigroup.com - Ahmad Rahman (processor)",
                "quality@ioigroup.com - Fatimah Abdullah (quality_manager)"
            ]),
            ("⚙️  Sime Darby Plantation", [
                "millmanager@simeplantation.com - Raj Kumar (processor)",
                "sustainability@simeplantation.com - Nurul Huda (sustainability_coordinator)"
            ]),
            ("🌱 PT Astra Agro Lestari", [
                "plantation@astra-agro.com - Budi Santoso (originator)",
                "harvest@astra-agro.com - Siti Rahayu (harvest_coordinator)",
                "sustainability@astra-agro.com - Agus Wijaya (sustainability_manager)"
            ]),
            ("🌱 Koperasi Sawit Berkelanjutan", [
                "coop@sawitberkelanjutan.co.id - Mariam Sari (originator)"
            ])
        ]
        
        for company, users in credentials:
            print(f"\n{company}:")
            for user in users:
                print(f"  📧 {user}")
        
        print(f"\n🌐 ACCESS POINTS:")
        print("=" * 70)
        print("  🖥️  Frontend: http://localhost:3000")
        print("  📚 API Docs: http://localhost:8000/docs")
        print("  🔍 Health Check: http://localhost:8000/health/")
        
        print(f"\n💡 TESTING SCENARIOS:")
        print("=" * 70)
        print("  🏷️  L'Oréal: Test brand transparency dashboard and sustainability tracking")
        print("  📈 Wilmar: Test trader operations, risk management, and supply chain oversight")
        print("  🏭 IOI: Test refinery processing, quality control, and batch management")
        print("  ⚙️  Sime Darby: Test mill operations, inventory management, and processing")
        print("  🌱 Astra Agro: Test plantation management, origin data recording, and farm tracking")
        print("  🌱 Koperasi: Test smallholder cooperative features and harvest recording")
        
        print(f"\n🔄 END-TO-END WORKFLOW TESTING:")
        print("=" * 70)
        print("  1. 🌱 Koperasi records harvest data and origin information")
        print("  2. 🌱 Astra Agro manages plantation operations and creates batches")
        print("  3. ⚙️  Sime Darby processes FFB and creates crude palm oil")
        print("  4. 🏭 IOI refines crude oil into refined palm oil")
        print("  5. 📈 Wilmar trades refined oil and manages supply chain")
        print("  6. 🏷️  L'Oréal tracks complete supply chain transparency")
        print("  7. 🔍 All actors can view their portion of the supply chain")
        
        print(f"\n📊 SUPPLY CHAIN METRICS:")
        print("=" * 70)
        print("  💰 Total Chain Value: $3,675,000")
        print("  📦 Total Volume: 6,200 KGM")
        print("  🌍 Countries: 3 (France, Singapore, Malaysia, Indonesia)")
        print("  🏢 Companies: 6")
        print("  👤 Users: 12")
        print("  📋 Purchase Orders: 5")
        print("  🛍️  Products: 3 (FFB, CPO, RBD PO)")
        
        print(f"\n🎯 NEXT STEPS:")
        print("=" * 70)
        print("  1. Start the backend server: python -m uvicorn app.main:app --reload")
        print("  2. Start the frontend: cd frontend && npm start")
        print("  3. Login as L'Oréal user to test brand transparency dashboard")
        print("  4. Login as Astra Agro user to test origin dashboard")
        print("  5. Test the complete supply chain traceability")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    create_complete_loreal_chain()
