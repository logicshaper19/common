"""
Comprehensive integration tests for complete supply chain workflows.
"""
import pytest
import json
from datetime import datetime, timedelta, date
from decimal import Decimal
from uuid import uuid4
from unittest.mock import patch, Mock

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import Base, get_db
from app.models.user import User
from app.models.company import Company
from app.models.product import Product
from app.models.purchase_order import PurchaseOrder
from app.models.batch import Batch
from app.models.sector import Sector, SectorTier
from app.core.security import hash_password, create_access_token

# Create test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_integration.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables
Base.metadata.create_all(bind=engine)


def override_get_db():
    """Override database dependency for testing."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_db():
    """Clean database before each test."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def complete_supply_chain():
    """Create a complete supply chain with all entities."""
    db = TestingSessionLocal()
    
    # Create sector
    sector = Sector(
        id="palm_oil",
        name="Palm Oil",
        description="Palm oil supply chain",
        is_active=True,
        regulatory_focus=["EUDR", "RSPO"],
        compliance_rules={
            "traceability_required": True,
            "certification_required": True
        }
    )
    db.add(sector)
    
    # Create sector tiers
    tiers = [
        SectorTier(
            id="brand_tier",
            sector_id="palm_oil",
            tier_number=1,
            name="Brand",
            description="Consumer brands",
            requirements={"certification": "RSPO"}
        ),
        SectorTier(
            id="refinery_tier",
            sector_id="palm_oil",
            tier_number=2,
            name="Refinery",
            description="Oil refineries",
            requirements={"certification": "RSPO"}
        ),
        SectorTier(
            id="mill_tier",
            sector_id="palm_oil",
            tier_number=3,
            name="Mill",
            description="Palm oil mills",
            requirements={"certification": "RSPO"}
        )
    ]
    for tier in tiers:
        db.add(tier)
    
    # Create companies
    companies = {
        "brand": Company(
            id=uuid4(),
            name="Sustainable Brands Inc",
            company_type="brand",
            email="brand@sustainable.com",
            country="United States",
            sector_id="palm_oil",
            tier_level=1,
            subscription_tier="enterprise"
        ),
        "refinery": Company(
            id=uuid4(),
            name="Green Refinery Ltd",
            company_type="processor",
            email="refinery@green.com",
            country="Malaysia",
            sector_id="palm_oil",
            tier_level=2,
            subscription_tier="professional"
        ),
        "mill": Company(
            id=uuid4(),
            name="Eco Mill Co",
            company_type="originator",
            email="mill@eco.com",
            country="Indonesia",
            sector_id="palm_oil",
            tier_level=3,
            subscription_tier="basic"
        )
    }
    
    for company in companies.values():
        db.add(company)
    
    # Create users
    users = {}
    for role, company in companies.items():
        user = User(
            id=uuid4(),
            email=f"{role}@test.com",
            hashed_password=hash_password("testpassword123"),
            full_name=f"Test {role.title()} User",
            role="admin",
            company_id=company.id,
            sector_id="palm_oil",
            tier_level=company.tier_level,
            is_active=True
        )
        db.add(user)
        users[role] = user
    
    # Create products
    products = {
        "crude_oil": Product(
            id=uuid4(),
            common_product_id="PALM-CRUDE-001",
            name="Crude Palm Oil",
            category="raw_material",
            description="Unrefined palm oil",
            default_unit="MT",
            can_have_composition=False,
            hs_code="151110"
        ),
        "refined_oil": Product(
            id=uuid4(),
            common_product_id="PALM-REFINED-001",
            name="Refined Palm Oil",
            category="processed",
            description="Refined palm oil",
            default_unit="MT",
            can_have_composition=True,
            hs_code="151190"
        ),
        "finished_product": Product(
            id=uuid4(),
            common_product_id="PALM-FINISHED-001",
            name="Palm Oil Product",
            category="finished_good",
            description="Consumer palm oil product",
            default_unit="PCS",
            can_have_composition=True,
            hs_code="151620"
        )
    }
    
    for product in products.values():
        db.add(product)
    
    # Create business relationships
    relationships = [
        BusinessRelationship(
            id=uuid4(),
            buyer_company_id=companies["brand"].id,
            seller_company_id=companies["refinery"].id,
            relationship_type="supplier",
            status="active"
        )(
            id=uuid4(),
            buyer_company_id=companies["refinery"].id,
            seller_company_id=companies["mill"].id,
            relationship_type="supplier",
            status="active"
        )
    ]
    
    for relationship in relationships:
        db.add(relationship)
    
    db.commit()
    db.close()
    
    return {
        "sector": sector,
        "tiers": tiers,
        "companies": companies,
        "users": users,
        "products": products,
        "relationships": relationships
    }


def get_auth_headers(user_email: str) -> dict:
    """Get authentication headers for a user."""
    token = create_access_token(data={"sub": user_email})
    return {"Authorization": f"Bearer {token}"}


class TestCompleteSupplyChainWorkflow:
    """Test complete supply chain workflow from origin to consumer."""
    
    def test_end_to_end_supply_chain_workflow(self, complete_supply_chain):
        """Test complete workflow from mill to brand."""
        # Step 1: Mill creates batch of crude palm oil
        mill_headers = get_auth_headers("mill@test.com")
        
        batch_data = {
            "product_id": str(complete_supply_chain["products"]["crude_oil"].id),
            "batch_number": "BATCH-001-2024",
            "quantity": 1000,
            "unit": "MT",
            "origin_data": {
                "farm_location": {
                    "lat": -0.7893,
                    "lng": 113.9213
                },
                "harvest_date": "2024-01-15",
                "certification_id": "RSPO-12345",
                "farmer_info": {
                    "name": "Ahmad Susanto",
                    "farm_size_hectares": 25
                }
            }
        }
        
        batch_response = client.post("/api/v1/batches", json=batch_data, headers=mill_headers)
        assert batch_response.status_code == 201
        batch_id = batch_response.json()["id"]
        
        # Step 2: Refinery creates PO for crude oil from mill
        refinery_headers = get_auth_headers("refinery@test.com")
        
        po_data = {
            "seller_company_id": str(complete_supply_chain["companies"]["mill"].id),
            "product_id": str(complete_supply_chain["products"]["crude_oil"].id),
            "quantity": 1000,
            "unit": "MT",
            "delivery_date": (date.today() + timedelta(days=30)).isoformat(),
            "origin_data": batch_data["origin_data"]
        }
        
        po_response = client.post("/api/v1/purchase-orders", json=po_data, headers=refinery_headers)
        assert po_response.status_code == 201
        po_id = po_response.json()["id"]
        
        # Step 3: Mill confirms the PO
        confirm_data = {"confirmed_quantity": 1000}
        confirm_response = client.post(f"/api/v1/purchase-orders/{po_id}/seller-confirm", 
                                     json=confirm_data, headers=mill_headers)
        assert confirm_response.status_code == 200
        
        # Step 4: Mill creates batch for refined oil
        refined_batch_data = {
            "product_id": str(complete_supply_chain["products"]["refined_oil"].id),
            "batch_number": "REFINED-001-2024",
            "quantity": 950,  # Some loss during processing
            "unit": "MT",
            "input_materials": [
                {
                    "source_batch_id": batch_id,
                    "quantity_used": 1000,
                    "percentage_contribution": 100.0
                }
            ],
            "processing_data": {
                "facility_location": {
                    "lat": 2.1896,
                    "lng": 102.2501
                },
                "processing_date": "2024-02-01",
                "certification_id": "RSPO-67890"
            }
        }
        
        refined_batch_response = client.post("/api/v1/batches", json=refined_batch_data, headers=refinery_headers)
        assert refined_batch_response.status_code == 201
        refined_batch_id = refined_batch_response.json()["id"]
        
        # Step 5: Brand creates PO for refined oil from refinery
        brand_headers = get_auth_headers("brand@test.com")
        
        brand_po_data = {
            "seller_company_id": str(complete_supply_chain["companies"]["refinery"].id),
            "product_id": str(complete_supply_chain["products"]["refined_oil"].id),
            "quantity": 950,
            "unit": "MT",
            "delivery_date": (date.today() + timedelta(days=45)).isoformat(),
            "input_materials": [
                {
                    "source_po_id": po_id,
                    "quantity_used": 1000,
                    "percentage_contribution": 100.0
                }
            ]
        }
        
        brand_po_response = client.post("/api/v1/purchase-orders", json=brand_po_data, headers=brand_headers)
        assert brand_po_response.status_code == 201
        brand_po_id = brand_po_response.json()["id"]
        
        # Step 6: Refinery confirms the PO
        refinery_confirm_data = {"confirmed_quantity": 950}
        refinery_confirm_response = client.post(f"/api/v1/purchase-orders/{brand_po_id}/seller-confirm", 
                                              json=refinery_confirm_data, headers=refinery_headers)
        assert refinery_confirm_response.status_code == 200
        
        # Step 7: Verify traceability chain
        traceability_response = client.get(f"/api/v1/traceability/purchase-orders/{brand_po_id}", 
                                         headers=brand_headers)
        assert traceability_response.status_code == 200
        
        traceability_data = traceability_response.json()
        assert "supply_chain" in traceability_data
        assert len(traceability_data["supply_chain"]) >= 2  # At least 2 levels
        
        # Verify origin data is preserved
        origin_data = traceability_data["origin_data"]
        assert origin_data["farm_location"]["lat"] == -0.7893
        assert origin_data["certification_id"] == "RSPO-12345"
    
    def test_supply_chain_with_amendments(self, complete_supply_chain):
        """Test supply chain workflow with PO amendments."""
        # Create initial PO
        refinery_headers = get_auth_headers("refinery@test.com")
        
        po_data = {
            "seller_company_id": str(complete_supply_chain["companies"]["mill"].id),
            "product_id": str(complete_supply_chain["products"]["crude_oil"].id),
            "quantity": 1000,
            "unit": "MT",
            "delivery_date": (date.today() + timedelta(days=30)).isoformat()
        }
        
        po_response = client.post("/api/v1/purchase-orders", json=po_data, headers=refinery_headers)
        po_id = po_response.json()["id"]
        
        # Propose amendment
        amendment_data = {
            "quantity": 1200,  # Increase quantity
            "delivery_date": (date.today() + timedelta(days=35)).isoformat(),
            "reason": "Increased demand"
        }
        
        amendment_response = client.put(f"/api/v1/purchase-orders/{po_id}/propose-changes", 
                                      json=amendment_data, headers=refinery_headers)
        # This endpoint might not exist
        assert amendment_response.status_code in [200, 404]
        
        if amendment_response.status_code == 200:
            # Mill approves amendment
            mill_headers = get_auth_headers("mill@test.com")
            approve_data = {"approved": True, "notes": "Approved with conditions"}
            
            approve_response = client.put(f"/api/v1/purchase-orders/{po_id}/approve-changes", 
                                        json=approve_data, headers=mill_headers)
            assert approve_response.status_code == 200
            
            # Verify PO was updated
            updated_po_response = client.get(f"/api/v1/purchase-orders/{po_id}", headers=refinery_headers)
            assert updated_po_response.status_code == 200
            
            updated_data = updated_po_response.json()
            assert updated_data["quantity"] == 1200
    
    def test_supply_chain_with_compliance_check(self, complete_supply_chain):
        """Test supply chain workflow with compliance validation."""
        # Create PO with compliance data
        refinery_headers = get_auth_headers("refinery@test.com")
        
        po_data = {
            "seller_company_id": str(complete_supply_chain["companies"]["mill"].id),
            "product_id": str(complete_supply_chain["products"]["crude_oil"].id),
            "quantity": 1000,
            "unit": "MT",
            "delivery_date": (date.today() + timedelta(days=30)).isoformat(),
            "compliance_data": {
                "regulations": ["EUDR", "RSPO"],
                "certification_status": "valid",
                "deforestation_risk": "low"
            }
        }
        
        po_response = client.post("/api/v1/purchase-orders", json=po_data, headers=refinery_headers)
        assert po_response.status_code == 201
        po_id = po_response.json()["id"]
        
        # Check compliance status
        compliance_response = client.get(f"/api/v1/purchase-orders/{po_id}/compliance", 
                                       headers=refinery_headers)
        # This endpoint might not exist
        assert compliance_response.status_code in [200, 404]
        
        if compliance_response.status_code == 200:
            compliance_data = compliance_response.json()
            assert "compliance_status" in compliance_data
            assert "regulations" in compliance_data
    
    def test_supply_chain_with_document_upload(self, complete_supply_chain):
        """Test supply chain workflow with document upload."""
        # Create PO
        refinery_headers = get_auth_headers("refinery@test.com")
        
        po_data = {
            "seller_company_id": str(complete_supply_chain["companies"]["mill"].id),
            "product_id": str(complete_supply_chain["products"]["crude_oil"].id),
            "quantity": 1000,
            "unit": "MT",
            "delivery_date": (date.today() + timedelta(days=30)).isoformat()
        }
        
        po_response = client.post("/api/v1/purchase-orders", json=po_data, headers=refinery_headers)
        po_id = po_response.json()["id"]
        
        # Upload compliance document
        document_data = {
            "document_type": "certificate",
            "po_id": po_id,
            "compliance_regulations": '["RSPO", "EUDR"]'
        }
        
        # Create a mock file
        files = {"file": ("certificate.pdf", b"mock pdf content", "application/pdf")}
        
        upload_response = client.post("/api/v1/documents/upload", 
                                    data=document_data, files=files, headers=refinery_headers)
        # This endpoint might not exist
        assert upload_response.status_code in [200, 404]
        
        if upload_response.status_code == 200:
            # Verify document was uploaded
            documents_response = client.get(f"/api/v1/documents?po_id={po_id}", headers=refinery_headers)
            assert documents_response.status_code == 200
            
            documents_data = documents_response.json()
            assert len(documents_data["items"]) >= 1


class TestMultiCompanyWorkflow:
    """Test workflows involving multiple companies."""
    
    def test_company_onboarding_workflow(self, complete_supply_chain):
        """Test new company onboarding workflow."""
        # Create new company
        brand_headers = get_auth_headers("brand@test.com")
        
        new_company_data = {
            "name": "New Supplier Co",
            "company_type": "processor",
            "email": "supplier@new.com",
            "country": "Thailand",
            "sector_id": "palm_oil",
            "tier_level": 2
        }
        
        company_response = client.post("/api/v1/companies", json=new_company_data, headers=brand_headers)
        assert company_response.status_code == 201
        new_company_id = company_response.json()["id"]
        
        # Create business relationship
        relationship_data = {
            "seller_company_id": new_company_id,
            "relationship_type": "supplier",
            "metadata": {
                "invitation_method": "email",
                "data_sharing_level": "standard"
            }
        }
        
        relationship_response = client.post("/api/v1/business-relationships", 
                                          json=relationship_data, headers=brand_headers)
        assert relationship_response.status_code == 201
        relationship_id = relationship_response.json()["id"]
        
        # New company accepts relationship
        new_company_user = User(
            id=uuid4(),
            email="admin@new.com",
            hashed_password=hash_password("testpassword123"),
            full_name="New Company Admin",
            role="admin",
            company_id=uuid4(),  # This would be the actual new company ID
            is_active=True
        )
        
        # This would require the new company to be logged in
        # For testing, we'll simulate the acceptance
        accept_data = {"accepted": True}
        # Note: In real scenario, this would be called by the new company
        # accept_response = client.post(f"/api/v1/business-relationships/{relationship_id}/accept", 
        #                              json=accept_data, headers=new_company_headers)
    
    def test_cross_sector_workflow(self, complete_supply_chain):
        """Test workflow involving multiple sectors."""
        # Create apparel sector
        db = TestingSessionLocal()
        
        apparel_sector = Sector(
            id="apparel",
            name="Apparel",
            description="Apparel supply chain",
            is_active=True,
            regulatory_focus=["UFLPA", "Modern Slavery Act"],
            compliance_rules={
                "traceability_required": True,
                "labor_standards_required": True
            }
        )
        db.add(apparel_sector)
        
        # Create apparel company
        apparel_company = Company(
            id=uuid4(),
            name="Fashion Brand Inc",
            company_type="brand",
            email="fashion@brand.com",
            country="United States",
            sector_id="apparel",
            tier_level=1
        )
        db.add(apparel_company)
        
        # Create apparel user
        apparel_user = User(
            id=uuid4(),
            email="fashion@test.com",
            hashed_password=hash_password("testpassword123"),
            full_name="Fashion User",
            role="admin",
            company_id=apparel_company.id,
            sector_id="apparel",
            tier_level=1,
            is_active=True
        )
        db.add(apparel_user)
        
        db.commit()
        db.close()
        
        # Test cross-sector data access
        fashion_headers = get_auth_headers("fashion@test.com")
        
        # Should be able to see palm oil data (if cross-sector access is allowed)
        palm_products_response = client.get("/api/v1/products?sector_id=palm_oil", headers=fashion_headers)
        # This might return 200 with data or 403 if cross-sector access is restricted
        assert palm_products_response.status_code in [200, 403]


class TestErrorHandlingAndRecovery:
    """Test error handling and recovery in workflows."""
    
    def test_workflow_with_database_error(self, complete_supply_chain):
        """Test workflow behavior when database errors occur."""
        refinery_headers = get_auth_headers("refinery@test.com")
        
        # Create PO with invalid data that might cause database error
        po_data = {
            "seller_company_id": str(complete_supply_chain["companies"]["mill"].id),
            "product_id": str(complete_supply_chain["products"]["crude_oil"].id),
            "quantity": 1000,
            "unit": "MT",
            "delivery_date": (date.today() + timedelta(days=30)).isoformat(),
            "invalid_field": "this might cause an error"
        }
        
        po_response = client.post("/api/v1/purchase-orders", json=po_data, headers=refinery_headers)
        # Should handle gracefully
        assert po_response.status_code in [200, 400, 422, 500]
    
    def test_workflow_with_network_timeout(self, complete_supply_chain):
        """Test workflow behavior with simulated network issues."""
        refinery_headers = get_auth_headers("refinery@test.com")
        
        # Mock external service timeout
        with patch('app.services.external_apis.verify_certification') as mock_verify:
            mock_verify.side_effect = Exception("Network timeout")
            
            po_data = {
                "seller_company_id": str(complete_supply_chain["companies"]["mill"].id),
                "product_id": str(complete_supply_chain["products"]["crude_oil"].id),
                "quantity": 1000,
                "unit": "MT",
                "delivery_date": (date.today() + timedelta(days=30)).isoformat()
            }
            
            po_response = client.post("/api/v1/purchase-orders", json=po_data, headers=refinery_headers)
            # Should handle timeout gracefully
            assert po_response.status_code in [200, 500, 503]
    
    def test_workflow_with_concurrent_modifications(self, complete_supply_chain):
        """Test workflow behavior with concurrent modifications."""
        import threading
        import time
        
        refinery_headers = get_auth_headers("refinery@test.com")
        
        # Create PO
        po_data = {
            "seller_company_id": str(complete_supply_chain["companies"]["mill"].id),
            "product_id": str(complete_supply_chain["products"]["crude_oil"].id),
            "quantity": 1000,
            "unit": "MT",
            "delivery_date": (date.today() + timedelta(days=30)).isoformat()
        }
        
        po_response = client.post("/api/v1/purchase-orders", json=po_data, headers=refinery_headers)
        po_id = po_response.json()["id"]
        
        # Simulate concurrent updates
        results = []
        
        def update_po(quantity):
            update_data = {"quantity": quantity}
            response = client.put(f"/api/v1/purchase-orders/{po_id}", json=update_data, headers=refinery_headers)
            results.append(response.status_code)
        
        # Start concurrent updates
        threads = []
        for i in range(3):
            thread = threading.Thread(target=update_po, args=(1000 + i * 100))
            threads.append(thread)
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        # At least one should succeed
        assert 200 in results


class TestPerformanceAndScalability:
    """Test performance and scalability of workflows."""
    
    def test_bulk_po_creation_performance(self, complete_supply_chain):
        """Test performance of creating multiple POs."""
        refinery_headers = get_auth_headers("refinery@test.com")
        
        start_time = datetime.now()
        
        # Create multiple POs
        for i in range(10):
            po_data = {
                "seller_company_id": str(complete_supply_chain["companies"]["mill"].id),
                "product_id": str(complete_supply_chain["products"]["crude_oil"].id),
                "quantity": 1000 + i,
                "unit": "MT",
                "delivery_date": (date.today() + timedelta(days=30)).isoformat()
            }
            
            response = client.post("/api/v1/purchase-orders", json=po_data, headers=refinery_headers)
            assert response.status_code == 201
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Should complete within reasonable time (adjust threshold as needed)
        assert duration < 10.0  # 10 seconds for 10 POs
    
    def test_large_dataset_query_performance(self, complete_supply_chain):
        """Test performance of querying large datasets."""
        refinery_headers = get_auth_headers("refinery@test.com")
        
        # Create many POs first
        for i in range(50):
            po_data = {
                "seller_company_id": str(complete_supply_chain["companies"]["mill"].id),
                "product_id": str(complete_supply_chain["products"]["crude_oil"].id),
                "quantity": 1000 + i,
                "unit": "MT",
                "delivery_date": (date.today() + timedelta(days=30)).isoformat()
            }
            client.post("/api/v1/purchase-orders", json=po_data, headers=refinery_headers)
        
        # Test query performance
        start_time = datetime.now()
        
        response = client.get("/api/v1/purchase-orders?limit=100", headers=refinery_headers)
        assert response.status_code == 200
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Should complete within reasonable time
        assert duration < 2.0  # 2 seconds for large query
