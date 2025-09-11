"""
End-to-end test scenarios covering complete user workflows.
"""
import pytest
import asyncio
from typing import Dict, Any, List
from datetime import datetime, timedelta
from decimal import Decimal
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.core.database import get_db
from app.core.security import create_access_token
from app.tests.factories import (
    SupplyChainScenarioFactory,
    CompanyFactory,
    UserFactory,
    ProductFactory,
    PurchaseOrderFactory,
    SupplyChainScenario
)
from app.models.company import Company
from app.models.user import User
from app.models.product import Product
from app.models.purchase_order import PurchaseOrder


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def db_session():
    """Get database session for testing."""
    return next(get_db())


@pytest.fixture
def simple_supply_chain(db_session: Session) -> SupplyChainScenario:
    """Create a simple supply chain scenario."""
    scenario = SupplyChainScenarioFactory.create_simple_scenario()
    
    # Add to database
    for company in scenario.companies:
        db_session.add(company)
    
    for user in scenario.users:
        db_session.add(user)
    
    for product in scenario.products:
        db_session.add(product)
    
    for relationship in scenario.relationships:
        db_session.add(relationship)
    
    db_session.commit()
    
    for po in scenario.purchase_orders:
        db_session.add(po)
    
    db_session.commit()
    
    return scenario


@pytest.fixture
def complex_supply_chain(db_session: Session) -> SupplyChainScenario:
    """Create a complex supply chain scenario."""
    scenario = SupplyChainScenarioFactory.create_complex_scenario()
    
    # Add to database
    for company in scenario.companies:
        db_session.add(company)
    
    for user in scenario.users:
        db_session.add(user)
    
    for product in scenario.products:
        db_session.add(product)
    
    for relationship in scenario.relationships:
        db_session.add(relationship)
    
    db_session.commit()
    
    for po in scenario.purchase_orders:
        db_session.add(po)
    
    db_session.commit()
    
    return scenario


def create_auth_headers(user: User) -> Dict[str, str]:
    """Create authentication headers for a user."""
    token = create_access_token(data={"sub": user.email})
    return {"Authorization": f"Bearer {token}"}


class TestCompleteUserWorkflows:
    """Test complete user workflows from start to finish."""
    
    def test_brand_buyer_complete_workflow(self, client: TestClient, simple_supply_chain: SupplyChainScenario):
        """Test complete workflow for a brand buyer creating and managing POs."""
        # Get brand company and user
        brand_company = next(c for c in simple_supply_chain.companies if c.company_type == "brand")
        brand_user = next(u for u in simple_supply_chain.users if u.company_id == brand_company.id)
        
        # Get processor company for PO creation
        processor_company = next(c for c in simple_supply_chain.companies if c.company_type == "processor")
        
        # Get a finished good product
        finished_product = next(p for p in simple_supply_chain.products if p.category == "finished_good")
        
        headers = create_auth_headers(brand_user)
        
        # Step 1: Login and verify authentication
        response = client.get("/api/v1/auth/me", headers=headers)
        assert response.status_code == 200
        user_data = response.json()
        assert user_data["email"] == brand_user.email
        
        # Step 2: View dashboard/company information
        response = client.get(f"/api/v1/companies/{brand_company.id}", headers=headers)
        assert response.status_code == 200
        company_data = response.json()
        assert company_data["name"] == brand_company.name
        
        # Step 3: Browse available products
        response = client.get("/api/v1/products", headers=headers)
        assert response.status_code == 200
        products_data = response.json()
        assert len(products_data) > 0
        
        # Step 4: Create a new purchase order
        po_data = {
            "buyer_company_id": str(brand_company.id),
            "seller_company_id": str(processor_company.id),
            "product_id": str(finished_product.id),
            "quantity": 1000,
            "unit": "PCS",
            "delivery_date": (datetime.now() + timedelta(days=30)).date().isoformat(),
            "notes": "Urgent order for new collection"
        }
        
        response = client.post("/api/v1/purchase-orders", json=po_data, headers=headers)
        assert response.status_code == 201
        created_po = response.json()
        assert created_po["status"] == "pending"
        assert created_po["quantity"] == 1000
        
        po_id = created_po["id"]
        
        # Step 5: View created PO
        response = client.get(f"/api/v1/purchase-orders/{po_id}", headers=headers)
        assert response.status_code == 200
        po_details = response.json()
        assert po_details["id"] == po_id
        
        # Step 6: View company's PO list
        response = client.get("/api/v1/purchase-orders", headers=headers)
        assert response.status_code == 200
        po_list = response.json()
        assert any(po["id"] == po_id for po in po_list)
        
        # Step 7: Update PO (if still in draft/pending)
        update_data = {
            "quantity": 1200,
            "notes": "Updated quantity for increased demand"
        }
        response = client.put(f"/api/v1/purchase-orders/{po_id}", json=update_data, headers=headers)
        assert response.status_code == 200
        updated_po = response.json()
        assert updated_po["quantity"] == 1200
        
        # Step 8: View audit trail
        response = client.get(f"/api/v1/audit/purchase-orders/{po_id}", headers=headers)
        assert response.status_code == 200
        audit_events = response.json()
        assert len(audit_events) >= 2  # Creation and update events
    
    def test_processor_confirmation_workflow(self, client: TestClient, simple_supply_chain: SupplyChainScenario):
        """Test processor workflow for confirming POs and linking input materials."""
        # Get processor company and user
        processor_company = next(c for c in simple_supply_chain.companies if c.company_type == "processor")
        processor_user = next(u for u in simple_supply_chain.users if u.company_id == processor_company.id)
        
        # Get an existing PO where processor is seller
        processor_po = next(
            po for po in simple_supply_chain.purchase_orders 
            if po.seller_company_id == processor_company.id
        )
        
        headers = create_auth_headers(processor_user)
        
        # Step 1: Login and view pending POs
        response = client.get("/api/v1/purchase-orders?status=pending", headers=headers)
        assert response.status_code == 200
        pending_pos = response.json()
        
        # Step 2: View specific PO details
        response = client.get(f"/api/v1/purchase-orders/{processor_po.id}", headers=headers)
        assert response.status_code == 200
        po_details = response.json()
        
        # Step 3: Get input materials (raw material POs)
        response = client.get("/api/v1/purchase-orders?buyer_company_id=" + str(processor_company.id), headers=headers)
        assert response.status_code == 200
        input_pos = response.json()
        
        # Step 4: Confirm PO with input materials
        if input_pos:
            input_materials = [
                {
                    "source_po_id": input_pos[0]["id"],
                    "quantity_used": 800,
                    "percentage_contribution": 80
                },
                {
                    "source_po_id": input_pos[1]["id"] if len(input_pos) > 1 else input_pos[0]["id"],
                    "quantity_used": 200,
                    "percentage_contribution": 20
                }
            ]
        else:
            input_materials = []
        
        confirmation_data = {
            "confirmed_quantity": float(processor_po.quantity),
            "input_materials": input_materials,
            "quality_notes": "All quality checks passed",
            "processing_notes": "Standard processing applied"
        }
        
        response = client.post(
            f"/api/v1/purchase-orders/{processor_po.id}/confirm",
            json=confirmation_data,
            headers=headers
        )
        assert response.status_code == 200
        confirmed_po = response.json()
        assert confirmed_po["status"] == "confirmed"
        
        # Step 5: View transparency calculation (if available)
        response = client.get(f"/api/v1/transparency/{processor_po.id}", headers=headers)
        # May return 200 with scores or 202 if still calculating
        assert response.status_code in [200, 202]
    
    def test_originator_origin_data_workflow(self, client: TestClient, simple_supply_chain: SupplyChainScenario):
        """Test originator workflow for adding origin data."""
        # Get originator company and user
        originator_company = next(c for c in simple_supply_chain.companies if c.company_type == "originator")
        originator_user = next(u for u in simple_supply_chain.users if u.company_id == originator_company.id)
        
        # Get an originator PO
        originator_po = next(
            po for po in simple_supply_chain.purchase_orders 
            if po.seller_company_id == originator_company.id
        )
        
        headers = create_auth_headers(originator_user)
        
        # Step 1: View POs requiring origin data
        response = client.get("/api/v1/purchase-orders?requires_origin_data=true", headers=headers)
        assert response.status_code == 200
        
        # Step 2: Add origin data to PO
        origin_data = {
            "coordinates": {
                "lat": 28.6139,
                "lng": 77.2090
            },
            "farm_name": "Sustainable Cotton Farm",
            "harvest_date": "2023-10-15",
            "certifications": ["Organic", "Fair Trade"],
            "farmer_info": {
                "name": "Farmer John",
                "farm_size_hectares": 50,
                "years_experience": 20
            },
            "quality_metrics": {
                "fiber_length": 28.5,
                "moisture_content": 8.2,
                "purity_percentage": 98.5
            }
        }
        
        response = client.post(
            f"/api/v1/purchase-orders/{originator_po.id}/origin-data",
            json=origin_data,
            headers=headers
        )
        assert response.status_code == 200
        
        # Step 3: Confirm PO with origin data
        confirmation_data = {
            "confirmed_quantity": float(originator_po.quantity),
            "origin_data": origin_data,
            "harvest_notes": "Excellent quality harvest",
            "certification_documents": ["cert1.pdf", "cert2.pdf"]
        }
        
        response = client.post(
            f"/api/v1/purchase-orders/{originator_po.id}/confirm",
            json=confirmation_data,
            headers=headers
        )
        assert response.status_code == 200
        
        # Step 4: View transparency score (should be 100% for origin)
        response = client.get(f"/api/v1/transparency/{originator_po.id}", headers=headers)
        assert response.status_code in [200, 202]
    
    def test_supply_chain_transparency_calculation(self, client: TestClient, complex_supply_chain: SupplyChainScenario):
        """Test end-to-end transparency calculation across supply chain."""
        # Get a brand user to view transparency
        brand_company = next(c for c in complex_supply_chain.companies if c.company_type == "brand")
        brand_user = next(u for u in complex_supply_chain.users if u.company_id == brand_company.id)
        
        headers = create_auth_headers(brand_user)
        
        # Step 1: View supply chain network
        response = client.get(f"/api/v1/companies/{brand_company.id}/supply-chain", headers=headers)
        assert response.status_code == 200
        supply_chain = response.json()
        assert "nodes" in supply_chain
        assert "edges" in supply_chain
        
        # Step 2: Get transparency scores for brand's POs
        response = client.get("/api/v1/purchase-orders", headers=headers)
        assert response.status_code == 200
        brand_pos = response.json()
        
        if brand_pos:
            po_id = brand_pos[0]["id"]
            
            # Step 3: View detailed transparency calculation
            response = client.get(f"/api/v1/transparency/{po_id}/detailed", headers=headers)
            assert response.status_code in [200, 202]
            
            if response.status_code == 200:
                transparency_data = response.json()
                assert "transparency_to_mill" in transparency_data
                assert "transparency_to_plantation" in transparency_data
                assert "supply_chain_paths" in transparency_data
        
        # Step 4: View transparency dashboard
        response = client.get(f"/api/v1/companies/{brand_company.id}/transparency-dashboard", headers=headers)
        assert response.status_code == 200
        dashboard = response.json()
        assert "average_transparency" in dashboard
        assert "transparency_distribution" in dashboard
    
    def test_business_relationship_establishment(self, client: TestClient, db_session: Session):
        """Test complete business relationship establishment workflow."""
        # Create two companies
        buyer_company = CompanyFactory.create_company("brand")
        seller_company = CompanyFactory.create_company("processor")
        
        db_session.add(buyer_company)
        db_session.add(seller_company)
        db_session.commit()
        
        # Create users
        buyer_user = UserFactory.create_user(buyer_company, role="admin")
        seller_user = UserFactory.create_user(seller_company, role="admin")
        
        db_session.add(buyer_user)
        db_session.add(seller_user)
        db_session.commit()
        
        buyer_headers = create_auth_headers(buyer_user)
        seller_headers = create_auth_headers(seller_user)
        
        # Step 1: Buyer invites seller
        invitation_data = {
            "seller_company_email": seller_company.email,
            "relationship_type": "supplier",
            "message": "We would like to establish a business relationship"
        }
        
        response = client.post(
            "/api/v1/business-relationships/invite",
            json=invitation_data,
            headers=buyer_headers
        )
        assert response.status_code == 201
        invitation = response.json()
        relationship_id = invitation["id"]
        
        # Step 2: Seller views pending invitations
        response = client.get("/api/v1/business-relationships/pending", headers=seller_headers)
        assert response.status_code == 200
        pending = response.json()
        assert any(rel["id"] == relationship_id for rel in pending)
        
        # Step 3: Seller accepts invitation
        response = client.post(
            f"/api/v1/business-relationships/{relationship_id}/accept",
            headers=seller_headers
        )
        assert response.status_code == 200
        
        # Step 4: Verify relationship is established
        response = client.get("/api/v1/business-relationships", headers=buyer_headers)
        assert response.status_code == 200
        relationships = response.json()
        established_rel = next(rel for rel in relationships if rel["id"] == relationship_id)
        assert established_rel["status"] == "active"
        
        # Step 5: Both parties can now create POs
        product = ProductFactory.create_product("processed")
        db_session.add(product)
        db_session.commit()
        
        po_data = {
            "buyer_company_id": str(buyer_company.id),
            "seller_company_id": str(seller_company.id),
            "product_id": str(product.id),
            "quantity": 500,
            "unit": "KGM",
            "delivery_date": (datetime.now() + timedelta(days=30)).date().isoformat()
        }
        
        response = client.post("/api/v1/purchase-orders", json=po_data, headers=buyer_headers)
        assert response.status_code == 201
    
    def test_error_handling_workflow(self, client: TestClient, simple_supply_chain: SupplyChainScenario):
        """Test error handling in various workflow scenarios."""
        brand_company = next(c for c in simple_supply_chain.companies if c.company_type == "brand")
        brand_user = next(u for u in simple_supply_chain.users if u.company_id == brand_company.id)
        
        headers = create_auth_headers(brand_user)
        
        # Test 1: Invalid PO creation (missing required fields)
        invalid_po_data = {
            "buyer_company_id": str(brand_company.id),
            # Missing seller_company_id, product_id, quantity
        }
        
        response = client.post("/api/v1/purchase-orders", json=invalid_po_data, headers=headers)
        assert response.status_code == 422
        error_data = response.json()
        assert "error" in error_data
        assert error_data["error"]["code"] == "VALIDATION_ERROR"
        
        # Test 2: Access to non-existent resource
        response = client.get(f"/api/v1/purchase-orders/{uuid4()}", headers=headers)
        assert response.status_code == 404
        error_data = response.json()
        assert error_data["error"]["code"] == "RESOURCE_NOT_FOUND"
        
        # Test 3: Unauthorized access (wrong company)
        other_company_po = next(
            po for po in simple_supply_chain.purchase_orders 
            if po.buyer_company_id != brand_company.id and po.seller_company_id != brand_company.id
        )
        
        response = client.get(f"/api/v1/purchase-orders/{other_company_po.id}", headers=headers)
        assert response.status_code == 403
        error_data = response.json()
        assert error_data["error"]["code"] == "INSUFFICIENT_PERMISSIONS"
        
        # Test 4: Invalid state transition
        confirmed_po = next(
            po for po in simple_supply_chain.purchase_orders 
            if po.status == "confirmed" and po.buyer_company_id == brand_company.id
        )
        
        if confirmed_po:
            response = client.delete(f"/api/v1/purchase-orders/{confirmed_po.id}", headers=headers)
            assert response.status_code == 422
            error_data = response.json()
            assert error_data["error"]["code"] == "INVALID_STATE_TRANSITION"
    
    def test_concurrent_operations_workflow(self, client: TestClient, simple_supply_chain: SupplyChainScenario):
        """Test handling of concurrent operations on the same resources."""
        brand_company = next(c for c in simple_supply_chain.companies if c.company_type == "brand")
        brand_user = next(u for u in simple_supply_chain.users if u.company_id == brand_company.id)
        
        # Create another user for the same company
        another_user = UserFactory.create_user(brand_company, role="buyer")
        
        headers1 = create_auth_headers(brand_user)
        headers2 = create_auth_headers(another_user)
        
        # Get a PO that can be modified
        modifiable_po = next(
            po for po in simple_supply_chain.purchase_orders 
            if po.status in ["draft", "pending"] and po.buyer_company_id == brand_company.id
        )
        
        if modifiable_po:
            # Simulate concurrent updates
            update_data1 = {"quantity": 1000, "notes": "Updated by user 1"}
            update_data2 = {"quantity": 1500, "notes": "Updated by user 2"}
            
            # Both users try to update simultaneously
            response1 = client.put(
                f"/api/v1/purchase-orders/{modifiable_po.id}",
                json=update_data1,
                headers=headers1
            )
            response2 = client.put(
                f"/api/v1/purchase-orders/{modifiable_po.id}",
                json=update_data2,
                headers=headers2
            )
            
            # One should succeed, the other might get a conflict or succeed with last-write-wins
            assert response1.status_code in [200, 409]
            assert response2.status_code in [200, 409]
            
            # Verify final state is consistent
            response = client.get(f"/api/v1/purchase-orders/{modifiable_po.id}", headers=headers1)
            assert response.status_code == 200
            final_po = response.json()
            assert final_po["quantity"] in [1000, 1500]  # One of the updates succeeded
