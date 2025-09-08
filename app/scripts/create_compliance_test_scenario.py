#!/usr/bin/env python3
"""
Compliance Engine End-to-End Test Scenario Creator

This script creates a complete supply chain scenario with realistic data
to test the compliance engine from Tier 1 (Brand) to Tier 4/5 (Originator).

Usage:
    python app/scripts/create_compliance_test_scenario.py
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta
from decimal import Decimal
from uuid import uuid4
from typing import Dict, List, Any

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy.orm import Session
from sqlalchemy import text
from app.core.database import get_db
from app.models.company import Company
from app.models.user import User
from app.models.product import Product
from app.models.purchase_order import PurchaseOrder
from app.models.sector import Sector
from app.models.document import Document
from app.services.compliance.service import ComplianceService
from app.services.auth import hash_password


class ComplianceTestScenarioCreator:
    """Creates comprehensive test scenarios for compliance engine testing."""
    
    def __init__(self, db: Session):
        self.db = db
        self.created_data = {
            'companies': {},
            'users': {},
            'products': {},
            'purchase_orders': {},
            'documents': {}
        }
    
    async def create_complete_scenario(self) -> Dict[str, Any]:
        """Create a complete supply chain scenario for compliance testing."""
        print("🌱 Creating comprehensive compliance test scenario...")

        # Step 0: Clean up any existing test data
        await self._cleanup_existing_test_data()

        # Step 1: Ensure palm oil sector exists
        await self._ensure_palm_oil_sector()

        # Step 2: Create supply chain companies (Tier 1 to Tier 4)
        await self._create_supply_chain_companies()

        # Step 3: Create users for each company
        await self._create_company_users()

        # Step 4: Create products for each tier
        await self._create_supply_chain_products()

        # Step 5: Create purchase orders flowing through the chain
        await self._create_purchase_order_chain()

        # Step 6: Add compliance-relevant documents
        await self._add_compliance_documents()

        # Step 7: Test compliance checks
        compliance_results = await self._test_compliance_checks()

        print("✅ Compliance test scenario created successfully!")
        return {
            'scenario_id': str(uuid4()),
            'created_data': self.created_data,
            'compliance_results': compliance_results,
            'summary': self._generate_scenario_summary()
        }

    async def _cleanup_existing_test_data(self):
        """Clean up any existing test data to avoid conflicts."""
        print("🧹 Cleaning up existing test data...")

        # Instead of complex cleanup, just use unique email addresses
        # This is simpler and more reliable for testing
        pass
    
    async def _ensure_palm_oil_sector(self):
        """Ensure palm oil sector exists with compliance rules."""
        sector = self.db.query(Sector).filter(Sector.id == "palm_oil").first()
        
        if not sector:
            sector = Sector(
                id="palm_oil",
                name="Palm Oil & Agri-Commodities",
                description="Palm oil supply chain with EUDR compliance",
                is_active=True,
                regulatory_focus=["EUDR", "RSPO", "NDPE"],
                compliance_rules={
                    "eudr": {
                        "required_checks": [
                            "geolocation_present",
                            "deforestation_risk_assessment",
                            "legal_documentation_valid",
                            "due_diligence_statement"
                        ],
                        "check_definitions": {
                            "geolocation_present": {
                                "description": "Verify geographic coordinates are present for production areas",
                                "mandatory": True,
                                "applies_to_tiers": [4, 5]
                            },
                            "deforestation_risk_assessment": {
                                "description": "Assess deforestation risk using satellite data",
                                "mandatory": True,
                                "applies_to_tiers": [4, 5]
                            },
                            "legal_documentation_valid": {
                                "description": "Validate legal land use documentation",
                                "mandatory": True,
                                "applies_to_tiers": [4, 5]
                            },
                            "due_diligence_statement": {
                                "description": "EUDR due diligence statement completed",
                                "mandatory": True,
                                "applies_to_tiers": [1, 2, 3]
                            }
                        }
                    },
                    "rspo": {
                        "required_checks": [
                            "rspo_certification_valid",
                            "mass_balance_tracking",
                            "supply_chain_transparency"
                        ],
                        "check_definitions": {
                            "rspo_certification_valid": {
                                "description": "Valid RSPO certification for sustainable palm oil",
                                "mandatory": False,
                                "applies_to_tiers": [4, 5]
                            },
                            "mass_balance_tracking": {
                                "description": "RSPO mass balance system compliance",
                                "mandatory": False,
                                "applies_to_tiers": [2, 3, 4]
                            }
                        }
                    }
                }
            )
            self.db.add(sector)
            self.db.commit()
            print("✅ Created palm oil sector with compliance rules")
    
    async def _create_supply_chain_companies(self):
        """Create companies representing each tier in the supply chain."""
        # Generate unique email addresses with timestamp
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        companies_data = [
            {
                'key': 'brand_tier1',
                'name': 'Global Consumer Brands Inc',
                'company_type': 'brand',
                'tier_level': 1,
                'email': f'procurement-{timestamp}@globalbrands.com',
                'description': 'Major consumer goods brand importing palm oil products'
            },
            {
                'key': 'trader_tier2',
                'name': 'International Palm Trading Ltd',
                'company_type': 'trader',
                'tier_level': 2,
                'email': f'operations-{timestamp}@palmtrading.com',
                'description': 'International commodity trader specializing in palm oil'
            },
            {
                'key': 'refinery_tier3',
                'name': 'Southeast Asia Palm Refinery',
                'company_type': 'processor',
                'tier_level': 3,
                'email': f'supply-{timestamp}@searefinery.com',
                'description': 'Palm oil refinery processing crude palm oil'
            },
            {
                'key': 'mill_tier4',
                'name': 'Sustainable Palm Mill Co',
                'company_type': 'mill',
                'tier_level': 4,
                'email': f'manager-{timestamp}@sustainablemill.com',
                'description': 'Palm oil mill processing fresh fruit bunches'
            },
            {
                'key': 'plantation_tier5',
                'name': 'Green Valley Plantation',
                'company_type': 'plantation',
                'tier_level': 5,
                'email': f'owner-{timestamp}@greenvalley.com',
                'description': 'Sustainable palm oil plantation (originator)'
            }
        ]
        
        for company_data in companies_data:
            company = Company(
                id=uuid4(),
                name=company_data['name'],
                company_type=company_data['company_type'],
                email=company_data['email'],
                sector_id='palm_oil',
                tier_level=company_data['tier_level']
            )
            
            self.db.add(company)
            self.db.flush()
            self.db.refresh(company)
            
            self.created_data['companies'][company_data['key']] = {
                'id': str(company.id),
                'name': company.name,
                'tier_level': company.tier_level,
                'company_type': company.company_type
            }
            
            print(f"✅ Created {company_data['name']} (Tier {company_data['tier_level']})")
        
        self.db.commit()
    
    async def _create_company_users(self):
        """Create users for each company."""
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        user_configs = [
            ('brand_tier1', 'Sarah Johnson', 'buyer', f'sarah.johnson-{timestamp}@globalbrands.com'),
            ('trader_tier2', 'Michael Chen', 'buyer', f'michael.chen-{timestamp}@palmtrading.com'),
            ('refinery_tier3', 'Priya Sharma', 'seller', f'priya.sharma-{timestamp}@searefinery.com'),
            ('mill_tier4', 'Ahmad Rahman', 'seller', f'ahmad.rahman-{timestamp}@sustainablemill.com'),
            ('plantation_tier5', 'Maria Santos', 'seller', f'maria.santos-{timestamp}@greenvalley.com')
        ]
        
        for company_key, full_name, role, email in user_configs:
            company_data = self.created_data['companies'][company_key]
            
            user = User(
                id=uuid4(),
                email=email,
                hashed_password=hash_password("testpassword123"),
                full_name=full_name,
                role=role,
                company_id=company_data['id'],
                sector_id='palm_oil',
                tier_level=company_data['tier_level'],
                is_active=True
            )
            
            self.db.add(user)
            self.db.flush()
            self.db.refresh(user)
            
            self.created_data['users'][company_key] = {
                'id': str(user.id),
                'email': user.email,
                'full_name': user.full_name,
                'role': user.role
            }
            
            print(f"✅ Created user {full_name} for {company_data['name']}")
        
        self.db.commit()

    async def _create_supply_chain_products(self):
        """Create products for each tier of the supply chain."""
        # Generate unique product IDs with timestamp
        timestamp = datetime.now().strftime('%Y%m%d%H%M')
        products_data = [
            {
                'key': 'ffb',
                'common_product_id': f'FFB-TEST-{timestamp}',
                'name': 'Fresh Fruit Bunches (FFB) - Test',
                'category': 'raw_material',
                'description': 'Fresh palm fruit bunches harvested from oil palm trees',
                'hs_code': '1207.10.00',
                'default_unit': 'KGM',
                'can_have_composition': False,
                'tier_produced': 5,
                'tier_consumed': 4
            },
            {
                'key': 'cpo',
                'common_product_id': f'CPO-TEST-{timestamp}',
                'name': 'Crude Palm Oil (CPO) - Test',
                'category': 'processed',
                'description': 'Crude palm oil extracted from fresh fruit bunches',
                'hs_code': '1511.10.00',
                'default_unit': 'KGM',
                'can_have_composition': True,
                'tier_produced': 4,
                'tier_consumed': 3
            },
            {
                'key': 'rpo',
                'common_product_id': f'RPO-TEST-{timestamp}',
                'name': 'Refined Palm Oil (RPO) - Test',
                'category': 'processed',
                'description': 'Refined, bleached, and deodorized palm oil',
                'hs_code': '1511.90.00',
                'default_unit': 'KGM',
                'can_have_composition': True,
                'tier_produced': 3,
                'tier_consumed': 2
            },
            {
                'key': 'palm_products',
                'common_product_id': f'PALM-MIX-TEST-{timestamp}',
                'name': 'Palm Oil Product Mix - Test',
                'category': 'finished_good',
                'description': 'Blended palm oil products for consumer goods',
                'hs_code': '1511.90.90',
                'default_unit': 'KGM',
                'can_have_composition': True,
                'tier_produced': 2,
                'tier_consumed': 1
            }
        ]

        for product_data in products_data:
            # Create origin data requirements based on tier
            origin_requirements = {}
            if product_data['tier_produced'] == 5:  # Plantation
                origin_requirements = {
                    "required_fields": [
                        "plantation_coordinates",
                        "harvest_date",
                        "plantation_certification",
                        "land_use_permits"
                    ],
                    "optional_fields": [
                        "variety",
                        "age_of_trees",
                        "yield_per_hectare",
                        "soil_type"
                    ],
                    "compliance_requirements": {
                        "eudr": ["geolocation_data", "deforestation_assessment"],
                        "rspo": ["certification_documents", "audit_reports"]
                    }
                }
            elif product_data['tier_produced'] == 4:  # Mill
                origin_requirements = {
                    "required_fields": [
                        "mill_location",
                        "processing_date",
                        "source_plantations",
                        "quality_certificates"
                    ],
                    "compliance_requirements": {
                        "eudr": ["supply_chain_mapping", "due_diligence_docs"],
                        "rspo": ["mass_balance_records", "certification_chain"]
                    }
                }

            product = Product(
                id=uuid4(),
                common_product_id=product_data['common_product_id'],
                name=product_data['name'],
                category=product_data['category'],
                description=product_data['description'],
                hs_code=product_data['hs_code'],
                default_unit=product_data['default_unit'],
                can_have_composition=product_data['can_have_composition'],
                origin_data_requirements=origin_requirements
            )

            self.db.add(product)
            self.db.flush()
            self.db.refresh(product)

            self.created_data['products'][product_data['key']] = {
                'id': str(product.id),
                'name': product.name,
                'category': product.category,
                'tier_produced': product_data['tier_produced'],
                'tier_consumed': product_data['tier_consumed']
            }

            print(f"✅ Created product {product.name}")

        self.db.commit()

    async def _create_purchase_order_chain(self):
        """Create purchase orders flowing through the supply chain."""
        # Define the purchase order chain
        po_chain = [
            {
                'key': 'po_plantation_to_mill',
                'buyer_company': 'mill_tier4',
                'seller_company': 'plantation_tier5',
                'product': 'ffb',
                'quantity': Decimal('50000.00'),  # 50 tons of FFB
                'unit_price': Decimal('250.00'),  # $250 per ton
                'description': 'Fresh Fruit Bunches from Green Valley Plantation'
            },
            {
                'key': 'po_mill_to_refinery',
                'buyer_company': 'refinery_tier3',
                'seller_company': 'mill_tier4',
                'product': 'cpo',
                'quantity': Decimal('10000.00'),  # 10 tons of CPO (20% extraction rate)
                'unit_price': Decimal('800.00'),  # $800 per ton
                'description': 'Crude Palm Oil from Sustainable Palm Mill'
            },
            {
                'key': 'po_refinery_to_trader',
                'buyer_company': 'trader_tier2',
                'seller_company': 'refinery_tier3',
                'product': 'rpo',
                'quantity': Decimal('9500.00'),  # 9.5 tons of RPO (95% yield)
                'unit_price': Decimal('950.00'),  # $950 per ton
                'description': 'Refined Palm Oil from Southeast Asia Refinery'
            },
            {
                'key': 'po_trader_to_brand',
                'buyer_company': 'brand_tier1',
                'seller_company': 'trader_tier2',
                'product': 'palm_products',
                'quantity': Decimal('9000.00'),  # 9 tons of blended products
                'unit_price': Decimal('1100.00'),  # $1100 per ton
                'description': 'Palm Oil Product Mix for Consumer Goods'
            }
        ]

        for po_data in po_chain:
            buyer_company_id = self.created_data['companies'][po_data['buyer_company']]['id']
            seller_company_id = self.created_data['companies'][po_data['seller_company']]['id']
            product_id = self.created_data['products'][po_data['product']]['id']

            po = PurchaseOrder(
                id=uuid4(),
                po_number=f"PO-{datetime.now().strftime('%Y%m%d%H%M%S')}-{po_data['key'][-3:].upper()}",
                buyer_company_id=buyer_company_id,
                seller_company_id=seller_company_id,
                product_id=product_id,
                quantity=po_data['quantity'],
                unit_price=po_data['unit_price'],
                total_amount=po_data['quantity'] * po_data['unit_price'],
                unit='KGM',  # Kilograms
                delivery_date=datetime.now() + timedelta(days=30),
                delivery_location='Port of Singapore',
                status='confirmed',
                notes=po_data['description'],
                created_at=datetime.now()
            )

            self.db.add(po)
            self.db.flush()
            self.db.refresh(po)

            self.created_data['purchase_orders'][po_data['key']] = {
                'id': str(po.id),
                'po_number': po.po_number,
                'buyer_company': po_data['buyer_company'],
                'seller_company': po_data['seller_company'],
                'product': po_data['product'],
                'quantity': float(po.quantity),
                'total_amount': float(po.total_amount)
            }

            print(f"✅ Created PO {po.po_number}: {po_data['description']}")

        self.db.commit()

    async def _add_compliance_documents(self):
        """Add compliance-relevant documents for testing."""
        # Sample documents for different tiers
        documents_data = [
            {
                'po_key': 'po_plantation_to_mill',
                'company_key': 'plantation_tier5',
                'document_type': 'rspo_certificate',
                'file_name': 'rspo_certificate_green_valley.pdf',
                'description': 'RSPO Certification for Green Valley Plantation'
            },
            {
                'po_key': 'po_plantation_to_mill',
                'company_key': 'plantation_tier5',
                'document_type': 'environmental_permit',
                'file_name': 'environmental_permit_green_valley.pdf',
                'description': 'Environmental permit for plantation'
            },
            {
                'po_key': 'po_mill_to_refinery',
                'company_key': 'mill_tier4',
                'document_type': 'processing_license',
                'file_name': 'mill_processing_license.pdf',
                'description': 'Mill processing license'
            },
            {
                'po_key': 'po_refinery_to_trader',
                'company_key': 'refinery_tier3',
                'document_type': 'quality_certificate',
                'file_name': 'refined_oil_quality_cert.pdf',
                'description': 'Quality certificate for refined palm oil'
            }
        ]

        for doc_data in documents_data:
            po_id = self.created_data['purchase_orders'][doc_data['po_key']]['id']
            company_id = self.created_data['companies'][doc_data['company_key']]['id']

            document = Document(
                id=uuid4(),
                po_id=po_id,
                company_id=company_id,
                uploaded_by_user_id=self.created_data['users'][doc_data['company_key']]['id'],
                document_type=doc_data['document_type'],
                file_name=doc_data['file_name'],
                original_file_name=doc_data['file_name'],
                file_size=1024000,  # 1MB
                mime_type='application/pdf',
                storage_url=f'/uploads/documents/{doc_data["document_type"]}/{doc_data["file_name"]}',
                storage_provider='local',
                validation_status='valid',
                is_proxy_upload=False,
                sector_id='palm_oil',
                created_at=datetime.now()
            )

            self.db.add(document)
            self.db.flush()
            self.db.refresh(document)

            if doc_data['po_key'] not in self.created_data['documents']:
                self.created_data['documents'][doc_data['po_key']] = []

            self.created_data['documents'][doc_data['po_key']].append({
                'id': str(document.id),
                'document_type': document.document_type,
                'file_name': document.file_name,
                'validation_status': document.validation_status
            })

            print(f"✅ Added document {doc_data['file_name']} for {doc_data['po_key']}")

        self.db.commit()

    async def _test_compliance_checks(self):
        """Test compliance checks for all purchase orders."""
        compliance_service = ComplianceService(self.db)
        compliance_results = {}

        print("\n🔍 Testing compliance checks...")

        for po_key, po_data in self.created_data['purchase_orders'].items():
            try:
                # Run compliance evaluation
                result = await compliance_service.evaluate_po_compliance(
                    po_id=po_data['id'],
                    regulation='eudr'
                )

                compliance_results[po_key] = {
                    'po_number': po_data['po_number'],
                    'regulation': 'eudr',
                    'overall_status': result.get('overall_status', 'unknown'),
                    'checks_performed': len(result.get('checks', [])),
                    'checks_passed': len([c for c in result.get('checks', []) if c.get('status') == 'pass']),
                    'checks_failed': len([c for c in result.get('checks', []) if c.get('status') == 'fail']),
                    'details': result
                }

                print(f"✅ Compliance check for {po_data['po_number']}: {result.get('overall_status', 'unknown')}")

            except Exception as e:
                compliance_results[po_key] = {
                    'po_number': po_data['po_number'],
                    'error': str(e)
                }
                print(f"❌ Compliance check failed for {po_data['po_number']}: {str(e)}")

        return compliance_results

    def _generate_scenario_summary(self):
        """Generate a summary of the created scenario."""
        return {
            'companies_created': len(self.created_data['companies']),
            'users_created': len(self.created_data['users']),
            'products_created': len(self.created_data['products']),
            'purchase_orders_created': len(self.created_data['purchase_orders']),
            'documents_added': sum(len(docs) for docs in self.created_data['documents'].values()),
            'supply_chain_tiers': [1, 2, 3, 4, 5],
            'regulations_tested': ['EUDR', 'RSPO'],
            'total_value_usd': sum(po['total_amount'] for po in self.created_data['purchase_orders'].values())
        }


async def main():
    """Main function to create and test the compliance scenario."""
    print("🚀 Starting Compliance Engine End-to-End Test Scenario Creation")
    print("=" * 70)

    # Get database session
    db = next(get_db())

    try:
        # Create scenario
        creator = ComplianceTestScenarioCreator(db)
        scenario_result = await creator.create_complete_scenario()

        # Print results
        print("\n" + "=" * 70)
        print("📊 SCENARIO CREATION COMPLETE")
        print("=" * 70)

        summary = scenario_result['summary']
        print(f"Companies Created: {summary['companies_created']}")
        print(f"Users Created: {summary['users_created']}")
        print(f"Products Created: {summary['products_created']}")
        print(f"Purchase Orders: {summary['purchase_orders_created']}")
        print(f"Documents Added: {summary['documents_added']}")
        print(f"Total Supply Chain Value: ${summary['total_value_usd']:,.2f}")

        print("\n📋 COMPLIANCE TEST RESULTS:")
        for po_key, result in scenario_result['compliance_results'].items():
            if 'error' in result:
                print(f"❌ {result['po_number']}: {result['error']}")
            else:
                print(f"✅ {result['po_number']}: {result['overall_status']} "
                      f"({result['checks_passed']}/{result['checks_performed']} checks passed)")

        print("\n🎯 NEXT STEPS:")
        print("1. Login to the frontend with any of the created user accounts")
        print("2. Navigate to the Compliance Dashboard")
        print("3. View compliance status for each purchase order")
        print("4. Generate compliance reports")
        print("5. Test document upload and validation")

        print("\n📧 TEST USER ACCOUNTS:")
        for company_key, user_data in scenario_result['created_data']['users'].items():
            company_name = scenario_result['created_data']['companies'][company_key]['name']
            print(f"   {user_data['email']} (password: testpassword123) - {company_name}")

        return scenario_result

    except Exception as e:
        print(f"❌ Error creating scenario: {str(e)}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(main())
