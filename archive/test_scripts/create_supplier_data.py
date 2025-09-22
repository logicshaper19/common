#!/usr/bin/env python3
"""
Script to ensure every role (except brand) has at least two suppliers and two incoming purchase orders.
"""
import asyncio
import json
import uuid
from datetime import datetime, timedelta
from decimal import Decimal

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Database connection
DATABASE_URL = "postgresql+asyncpg://postgres:test@localhost:5433/common_test"

# Company types and roles (excluding brand)
COMPANY_TYPES = [
    "processor",
    "originator", 
    "trader",
    "auditor",
    "regulator"
]

# User roles for each company type
ROLE_MAPPING = {
    "processor": ["admin", "supply_chain_manager", "production_manager", "quality_manager"],
    "originator": ["admin", "plantation_manager", "harvest_manager", "cooperative_manager"],
    "trader": ["admin", "trader", "sustainability_manager"],
    "auditor": ["admin", "auditor"],
    "regulator": ["admin", "regulator"]
}

async def create_supplier_data():
    """Create companies, users, and purchase orders for each role."""
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        print("🔍 Checking current data...")
        
        # Check current companies
        result = await session.execute(sa.text("""
            SELECT company_type, COUNT(*) as count 
            FROM companies 
            WHERE is_active = true 
            GROUP BY company_type 
            ORDER BY company_type
        """))
        current_companies = {row[0]: row[1] for row in result.fetchall()}
        print(f"Current companies: {current_companies}")
        
        # Check current purchase orders
        result = await session.execute(sa.text("""
            SELECT c.company_type, COUNT(*) as po_count
            FROM purchase_orders po
            JOIN companies c ON po.buyer_company_id = c.id
            WHERE c.is_active = true
            GROUP BY c.company_type
            ORDER BY c.company_type
        """))
        current_pos = {row[0]: row[1] for row in result.fetchall()}
        print(f"Current purchase orders: {current_pos}")
        
        # Create companies for each type (need at least 2 per type)
        companies_created = {}
        
        for company_type in COMPANY_TYPES:
            current_count = current_companies.get(company_type, 0)
            needed = max(0, 2 - current_count)
            
            if needed > 0:
                print(f"\n🏢 Creating {needed} {company_type} companies...")
                
                for i in range(needed):
                    company_id = uuid.uuid4()
                    company_name = f"{company_type.title()} Company {i+1}"
                    
                    await session.execute(sa.text("""
                        INSERT INTO companies (
                            id, name, company_type, email, phone, website, country,
                            industry_sector, is_active, is_verified, created_at, updated_at
                        ) VALUES (
                            :id, :name, :company_type, :email, :phone, :website, :country,
                            :industry_sector, :is_active, :is_verified, :created_at, :updated_at
                        )
                    """), {
                        "id": company_id,
                        "name": company_name,
                        "company_type": company_type,
                        "email": f"{company_type}{i+1}@example.com",
                        "phone": f"+1-555-{1000+i:04d}",
                        "website": f"https://{company_type}{i+1}.com",
                        "country": "United States",
                        "industry_sector": "agriculture",
                        "is_active": True,
                        "is_verified": True,
                        "created_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow()
                    })
                    
                    # Create users for this company
                    roles = ROLE_MAPPING.get(company_type, ["admin"])
                    for role in roles:
                        user_id = uuid.uuid4()
                        await session.execute(sa.text("""
                            INSERT INTO users (
                                id, email, hashed_password, full_name, role, is_active,
                                company_id, created_at, updated_at
                            ) VALUES (
                                :id, :email, :hashed_password, :full_name, :role, :is_active,
                                :company_id, :created_at, :updated_at
                            )
                        """), {
                            "id": user_id,
                            "email": f"{role}@{company_type}{i+1}.com",
                            "hashed_password": "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/8KzKz2K",  # "password123"
                            "full_name": f"{role.title()} User",
                            "role": role,
                            "is_active": True,
                            "company_id": company_id,
                            "created_at": datetime.utcnow(),
                            "updated_at": datetime.utcnow()
                        })
                    
                    companies_created[company_type] = companies_created.get(company_type, []) + [company_id]
                    print(f"  ✅ Created {company_name} with {len(roles)} users")
        
        await session.commit()
        print(f"\n✅ Created {sum(len(companies) for companies in companies_created.values())} companies")
        
        # Create purchase orders (need at least 2 incoming POs per company type)
        print(f"\n📋 Creating purchase orders...")
        
        # Get all companies to create POs between them
        result = await session.execute(sa.text("""
            SELECT id, company_type FROM companies WHERE is_active = true
        """))
        all_companies = {row[0]: row[1] for row in result.fetchall()}
        
        # Create POs where each company type receives at least 2 POs
        for company_type in COMPANY_TYPES:
            # Find companies of this type
            target_companies = [cid for cid, ctype in all_companies.items() if ctype == company_type]
            
            if not target_companies:
                continue
                
            # Find supplier companies (other types)
            supplier_companies = [cid for cid, ctype in all_companies.items() if ctype != company_type]
            
            if not supplier_companies:
                continue
            
            # Create 2 POs for each target company
            for target_company in target_companies:
                for po_num in range(2):
                    po_id = uuid.uuid4()
                    supplier_company = supplier_companies[po_num % len(supplier_companies)]
                    
                    # Create a product first
                    product_id = uuid.uuid4()
                    await session.execute(sa.text("""
                        INSERT INTO products (
                            id, name, description, category, can_have_composition,
                            material_breakdown, default_unit, hs_code, origin_data_requirements,
                            created_at, updated_at
                        ) VALUES (
                            :id, :name, :description, :category, :can_have_composition,
                            :material_breakdown, :default_unit, :hs_code, :origin_data_requirements,
                            :created_at, :updated_at
                        )
                    """), {
                        "id": product_id,
                        "name": f"Product for {company_type} {po_num+1}",
                        "description": f"Sample product for testing",
                        "category": "raw_material",
                        "can_have_composition": True,
                        "material_breakdown": json.dumps({
                            "palm_oil": {"percentage": 70, "origin": "Malaysia"},
                            "soy_oil": {"percentage": 30, "origin": "Brazil"}
                        }),
                        "default_unit": "kg",
                        "hs_code": "1511.10",
                        "origin_data_requirements": json.dumps({
                            "traceability_level": "mill",
                            "certifications_required": ["RSPO", "ISCC"]
                        }),
                        "created_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow()
                    })
                    
                    # Create the purchase order
                    await session.execute(sa.text("""
                        INSERT INTO purchase_orders (
                            id, po_number, buyer_company_id, seller_company_id, product_id,
                            quantity, unit_price, total_amount, unit, delivery_date,
                            delivery_location, status, input_materials, origin_data,
                            created_at, updated_at
                        ) VALUES (
                            :id, :po_number, :buyer_company_id, :seller_company_id, :product_id,
                            :quantity, :unit_price, :total_amount, :unit, :delivery_date,
                            :delivery_location, :status, :input_materials, :origin_data,
                            :created_at, :updated_at
                        )
                    """), {
                        "id": po_id,
                        "po_number": f"PO-{company_type.upper()}-{po_num+1:03d}",
                        "buyer_company_id": target_company,
                        "seller_company_id": supplier_company,
                        "product_id": product_id,
                        "quantity": Decimal("1000.00"),
                        "unit_price": Decimal("500.00"),
                        "total_amount": Decimal("500000.00"),
                        "unit": "kg",
                        "delivery_date": (datetime.utcnow() + timedelta(days=30)).date(),
                        "delivery_location": f"Port of {company_type.title()}",
                        "status": "confirmed",
                        "input_materials": json.dumps({
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
                        }),
                        "origin_data": json.dumps({
                            "traceability": {
                                "batch_id": f"BATCH-{company_type.upper()}-{po_num+1:03d}",
                                "plantation": {
                                    "name": f"Sustainable {company_type.title()} Plantation",
                                    "certified_rspo": True,
                                    "size_ha": 500
                                },
                                "mill": {
                                    "name": f"Green {company_type.title()} Mill",
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
                        }),
                        "created_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow()
                    })
                    
                    print(f"  ✅ Created PO {po_id} for {company_type} company")
        
        await session.commit()
        print(f"\n✅ Created purchase orders for all company types")
        
        # Final verification
        print(f"\n🔍 Final verification...")
        
        result = await session.execute(sa.text("""
            SELECT company_type, COUNT(*) as count 
            FROM companies 
            WHERE is_active = true 
            GROUP BY company_type 
            ORDER BY company_type
        """))
        final_companies = {row[0]: row[1] for row in result.fetchall()}
        print(f"Final companies: {final_companies}")
        
        result = await session.execute(sa.text("""
            SELECT c.company_type, COUNT(*) as po_count
            FROM purchase_orders po
            JOIN companies c ON po.buyer_company_id = c.id
            WHERE c.is_active = true
            GROUP BY c.company_type
            ORDER BY c.company_type
        """))
        final_pos = {row[0]: row[1] for row in result.fetchall()}
        print(f"Final purchase orders: {final_pos}")
        
        # Check if requirements are met
        print(f"\n📊 Requirements check:")
        for company_type in COMPANY_TYPES:
            company_count = final_companies.get(company_type, 0)
            po_count = final_pos.get(company_type, 0)
            
            company_ok = "✅" if company_count >= 2 else "❌"
            po_ok = "✅" if po_count >= 2 else "❌"
            
            print(f"  {company_type}: {company_count} companies {company_ok}, {po_count} POs {po_ok}")
    
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(create_supplier_data())
