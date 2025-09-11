"""
Enhanced comprehensive tests for purchase order business logic.
Tests complex domain rules, state transitions, and business relationships.
"""
import pytest
from datetime import datetime, timedelta, date
from decimal import Decimal
from uuid import uuid4
from unittest.mock import patch, Mock

from app.models.user import User
from app.models.company import Company
from app.models.product import Product
from app.models.purchase_order import PurchaseOrder
from app.models.business_relationship import BusinessRelationship
from app.schemas.purchase_order import PurchaseOrderStatus, PurchaseOrderCreate
from app.core.security import hash_password

# Mark all tests in this file as integration tests
pytestmark = [pytest.mark.integration, pytest.mark.api, pytest.mark.database]


@pytest.fixture
def supply_chain_companies(db_session):
    """Create a complete supply chain with business relationships."""
    # Create companies representing different tiers
    brand = Company(
        id=uuid4(),
        name="Global Brand Corp",
        company_type="brand",
        email="procurement@globalbrand.com",
        tier_level=1
    )
    
    processor = Company(
        id=uuid4(),
        name="Palm Processing Ltd",
        company_type="processor", 
        email="sales@palmprocessing.com",
        tier_level=2
    )
    
    mill = Company(
        id=uuid4(),
        name="Sustainable Mill Co",
        company_type="mill",
        email="operations@sustainablemill.com",
        tier_level=4
    )
    
    plantation = Company(
        id=uuid4(),
        name="Eco Plantation",
        company_type="plantation",
        email="harvest@ecoplantation.com",
        tier_level=7
    )
    
    db_session.add_all([brand, processor, mill, plantation])
    db_session.commit()
    
    # Create business relationships
    brand_processor_rel = BusinessRelationship(
        id=uuid4(),
        buyer_company_id=brand.id,
        seller_company_id=processor.id,
        relationship_type="supplier",
        status="active",
        established_date=date.today() - timedelta(days=365)
    )
    
    processor_mill_rel = BusinessRelationship(
        id=uuid4(),
        buyer_company_id=processor.id,
        seller_company_id=mill.id,
        relationship_type="supplier",
        status="active",
        established_date=date.today() - timedelta(days=180)
    )
    
    mill_plantation_rel = BusinessRelationship(
        id=uuid4(),
        buyer_company_id=mill.id,
        seller_company_id=plantation.id,
        relationship_type="supplier",
        status="active",
        established_date=date.today() - timedelta(days=90)
    )
    
    db_session.add_all([brand_processor_rel, processor_mill_rel, mill_plantation_rel])
    db_session.commit()
    
    return {
        "brand": brand,
        "processor": processor,
        "mill": mill,
        "plantation": plantation,
        "relationships": [brand_processor_rel, processor_mill_rel, mill_plantation_rel]
    }


@pytest.fixture
def palm_oil_products(db_session):
    """Create palm oil supply chain products with composition rules."""
    # Raw material from plantation
    ffb = Product(
        id=uuid4(),
        common_product_id="FFB-001",
        name="Fresh Fruit Bunches",
        description="Raw palm fruit bunches from plantation",
        category="raw_material",
        can_have_composition=False,
        default_unit="KGM",
        hs_code="1207.10.00",
        origin_data_requirements={"plantation_id": True, "harvest_date": True}
    )
    
    # Processed at mill
    cpo = Product(
        id=uuid4(),
        common_product_id="CPO-001", 
        name="Crude Palm Oil",
        description="Crude palm oil extracted from FFB",
        category="processed",
        can_have_composition=True,
        material_breakdown={"ffb": 100.0},
        default_unit="KGM",
        hs_code="1511.10.00",
        origin_data_requirements={"mill_id": True, "extraction_date": True}
    )
    
    # Refined at processor
    rbd_po = Product(
        id=uuid4(),
        common_product_id="RBD-PO-001",
        name="Refined Bleached Deodorized Palm Oil",
        description="Refined palm oil ready for food use",
        category="finished_good",
        can_have_composition=True,
        material_breakdown={"cpo": 100.0},
        default_unit="KGM",
        hs_code="1511.90.11"
    )
    
    # Blended product
    palm_blend = Product(
        id=uuid4(),
        common_product_id="BLEND-001",
        name="80/20 Palm Oil Blend",
        description="80% RBD Palm Oil, 20% Palm Kernel Oil",
        category="finished_good", 
        can_have_composition=True,
        material_breakdown={"rbd_palm_oil": 80.0, "palm_kernel_oil": 20.0},
        default_unit="KGM",
        hs_code="1511.90.19"
    )
    
    db_session.add_all([ffb, cpo, rbd_po, palm_blend])
    db_session.commit()
    
    return {
        "ffb": ffb,
        "cpo": cpo, 
        "rbd_po": rbd_po,
        "palm_blend": palm_blend
    }


@pytest.fixture
def supply_chain_users(db_session, supply_chain_companies):
    """Create users for each company in the supply chain."""
    companies = supply_chain_companies
    
    brand_buyer = User(
        id=uuid4(),
        email="buyer@globalbrand.com",
        hashed_password=hash_password("brandpass123"),
        full_name="Brand Procurement Manager",
        role="buyer",
        company_id=companies["brand"].id,
        is_active=True
    )
    
    processor_seller = User(
        id=uuid4(),
        email="sales@palmprocessing.com", 
        hashed_password=hash_password("processorpass123"),
        full_name="Processor Sales Manager",
        role="seller",
        company_id=companies["processor"].id,
        is_active=True
    )
    
    mill_operator = User(
        id=uuid4(),
        email="ops@sustainablemill.com",
        hashed_password=hash_password("millpass123"),
        full_name="Mill Operations Manager",
        role="seller",
        company_id=companies["mill"].id,
        is_active=True
    )
    
    plantation_manager = User(
        id=uuid4(),
        email="manager@ecoplantation.com",
        hashed_password=hash_password("plantationpass123"),
        full_name="Plantation Manager",
        role="seller", 
        company_id=companies["plantation"].id,
        is_active=True
    )
    
    db_session.add_all([brand_buyer, processor_seller, mill_operator, plantation_manager])
    db_session.commit()
    
    return {
        "brand_buyer": brand_buyer,
        "processor_seller": processor_seller,
        "mill_operator": mill_operator,
        "plantation_manager": plantation_manager
    }


def test_purchase_order_creation_with_business_rules(
    client, db_session, supply_chain_companies, palm_oil_products, supply_chain_users
):
    """Test PO creation with comprehensive business rule validation."""
    companies = supply_chain_companies
    products = palm_oil_products
    users = supply_chain_users
    
    # Get auth headers for brand buyer
    login_response = client.post("/auth/login", json={
        "email": "buyer@globalbrand.com",
        "password": "brandpass123"
    })
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create valid PO from brand to processor
    po_data = {
        "buyer_company_id": str(companies["brand"].id),
        "seller_company_id": str(companies["processor"].id),
        "product_id": str(products["rbd_po"].id),
        "quantity": "1000.000",
        "unit_price": "1250.50",
        "unit": "KGM",
        "delivery_date": (date.today() + timedelta(days=30)).isoformat(),
        "delivery_location": "Brand Warehouse, Port of Rotterdam",
        "composition": {"cpo": 100.0},
        "origin_data": {
            "sustainability_certification": "RSPO",
            "traceability_level": "mill"
        },
        "notes": "Require RSPO certified palm oil with mill-level traceability"
    }
    
    response = client.post("/purchase-orders/", json=po_data, headers=headers)
    assert response.status_code == 201
    
    po_response = response.json()
    
    # Validate business logic in response
    assert po_response["status"] == PurchaseOrderStatus.DRAFT.value
    assert Decimal(po_response["quantity"]) == Decimal("1000.000")
    assert Decimal(po_response["unit_price"]) == Decimal("1250.50")
    assert Decimal(po_response["total_amount"]) == Decimal("1250500.00")
    assert po_response["unit"] == "KGM"
    
    # Validate PO number generation follows business rules
    assert po_response["po_number"].startswith("PO-")
    assert len(po_response["po_number"]) >= 10
    
    # Validate composition matches product requirements
    assert po_response["composition"]["cpo"] == 100.0
    
    # Validate database state
    po = db_session.query(PurchaseOrder).filter(
        PurchaseOrder.id == po_response["id"]
    ).first()
    assert po is not None
    assert po.buyer_company_id == companies["brand"].id
    assert po.seller_company_id == companies["processor"].id
    assert po.product_id == products["rbd_po"].id
    assert po.status == PurchaseOrderStatus.DRAFT.value
    
    # Validate business relationship exists
    relationship = db_session.query(BusinessRelationship).filter(
        BusinessRelationship.buyer_company_id == companies["brand"].id,
        BusinessRelationship.seller_company_id == companies["processor"].id
    ).first()
    assert relationship is not None
    assert relationship.status == "active"


def test_purchase_order_invalid_business_relationship(
    client, db_session, supply_chain_companies, palm_oil_products, supply_chain_users
):
    """Test PO creation fails when no business relationship exists."""
    companies = supply_chain_companies
    products = palm_oil_products
    
    # Get auth headers for brand buyer
    login_response = client.post("/auth/login", json={
        "email": "buyer@globalbrand.com", 
        "password": "brandpass123"
    })
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Try to create PO directly from brand to mill (no direct relationship)
    po_data = {
        "buyer_company_id": str(companies["brand"].id),
        "seller_company_id": str(companies["mill"].id),  # No direct relationship
        "product_id": str(products["cpo"].id),
        "quantity": "500.000",
        "unit_price": "1100.00",
        "unit": "KGM",
        "delivery_date": (date.today() + timedelta(days=45)).isoformat(),
        "delivery_location": "Brand Warehouse"
    }
    
    response = client.post("/purchase-orders/", json=po_data, headers=headers)
    assert response.status_code == 400
    
    error_data = response.json()
    assert "business relationship" in error_data["detail"].lower()
    
    # Validate no PO was created
    po_count = db_session.query(PurchaseOrder).filter(
        PurchaseOrder.buyer_company_id == companies["brand"].id,
        PurchaseOrder.seller_company_id == companies["mill"].id
    ).count()
    assert po_count == 0


def test_purchase_order_composition_validation(
    client, db_session, supply_chain_companies, palm_oil_products, supply_chain_users
):
    """Test PO composition validation against product rules."""
    companies = supply_chain_companies
    products = palm_oil_products
    
    # Get auth headers
    login_response = client.post("/auth/login", json={
        "email": "buyer@globalbrand.com",
        "password": "brandpass123"
    })
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test invalid composition (doesn't sum to 100%)
    po_data = {
        "buyer_company_id": str(companies["brand"].id),
        "seller_company_id": str(companies["processor"].id),
        "product_id": str(products["palm_blend"].id),
        "quantity": "1000.000",
        "unit_price": "1200.00",
        "unit": "KGM",
        "delivery_date": (date.today() + timedelta(days=30)).isoformat(),
        "delivery_location": "Brand Warehouse",
        "composition": {
            "rbd_palm_oil": 80.0,
            "palm_kernel_oil": 15.0  # Only sums to 95%
        }
    }
    
    response = client.post("/purchase-orders/", json=po_data, headers=headers)
    assert response.status_code == 422
    
    error_data = response.json()
    assert "composition" in str(error_data).lower()
    
    # Test composition with wrong materials
    po_data["composition"] = {
        "wrong_material": 50.0,
        "another_wrong": 50.0
    }
    
    response = client.post("/purchase-orders/", json=po_data, headers=headers)
    assert response.status_code == 422
    
    # Test valid composition
    po_data["composition"] = {
        "rbd_palm_oil": 80.0,
        "palm_kernel_oil": 20.0
    }
    
    response = client.post("/purchase-orders/", json=po_data, headers=headers)
    assert response.status_code == 201
    
    po_response = response.json()
    assert po_response["composition"]["rbd_palm_oil"] == 80.0
    assert po_response["composition"]["palm_kernel_oil"] == 20.0


def test_purchase_order_status_transitions(
    client, db_session, supply_chain_companies, palm_oil_products, supply_chain_users
):
    """Test PO status transitions follow business rules."""
    companies = supply_chain_companies
    products = palm_oil_products

    # Create PO as brand buyer
    login_response = client.post("/auth/login", json={
        "email": "buyer@globalbrand.com",
        "password": "brandpass123"
    })
    token = login_response.json()["access_token"]
    buyer_headers = {"Authorization": f"Bearer {token}"}

    po_data = {
        "buyer_company_id": str(companies["brand"].id),
        "seller_company_id": str(companies["processor"].id),
        "product_id": str(products["rbd_po"].id),
        "quantity": "1000.000",
        "unit_price": "1250.50",
        "unit": "KGM",
        "delivery_date": (date.today() + timedelta(days=30)).isoformat(),
        "delivery_location": "Brand Warehouse"
    }

    response = client.post("/purchase-orders/", json=po_data, headers=buyer_headers)
    assert response.status_code == 201
    po_id = response.json()["id"]

    # Test transition from DRAFT to PENDING
    response = client.patch(
        f"/purchase-orders/{po_id}/status",
        json={"status": "pending"},
        headers=buyer_headers
    )
    assert response.status_code == 200
    assert response.json()["status"] == "pending"

    # Test invalid transition (PENDING to DELIVERED - skipping CONFIRMED)
    response = client.patch(
        f"/purchase-orders/{po_id}/status",
        json={"status": "delivered"},
        headers=buyer_headers
    )
    assert response.status_code == 400
    error_data = response.json()
    assert "invalid transition" in error_data["detail"].lower()

    # Get seller auth headers
    seller_login = client.post("/auth/login", json={
        "email": "sales@palmprocessing.com",
        "password": "processorpass123"
    })
    seller_token = seller_login.json()["access_token"]
    seller_headers = {"Authorization": f"Bearer {seller_token}"}

    # Seller confirms PO
    confirmation_data = {
        "confirmed_quantity": "1000.000",
        "confirmed_unit_price": "1250.50",
        "confirmed_delivery_date": (date.today() + timedelta(days=28)).isoformat(),
        "seller_notes": "Confirmed - can deliver 2 days earlier"
    }

    response = client.post(
        f"/purchase-orders/{po_id}/confirm",
        json=confirmation_data,
        headers=seller_headers
    )
    assert response.status_code == 200

    # Validate status changed to CONFIRMED
    po_response = response.json()
    assert po_response["status"] == "confirmed"
    assert po_response["confirmed_quantity"] == "1000.000"
    assert po_response["seller_notes"] == "Confirmed - can deliver 2 days earlier"

    # Test valid transition to IN_TRANSIT
    response = client.patch(
        f"/purchase-orders/{po_id}/status",
        json={"status": "in_transit"},
        headers=seller_headers
    )
    assert response.status_code == 200
    assert response.json()["status"] == "in_transit"


def test_purchase_order_discrepancy_handling(
    client, db_session, supply_chain_companies, palm_oil_products, supply_chain_users
):
    """Test PO discrepancy handling and buyer approval workflow."""
    companies = supply_chain_companies
    products = palm_oil_products

    # Create and submit PO
    buyer_login = client.post("/auth/login", json={
        "email": "buyer@globalbrand.com",
        "password": "brandpass123"
    })
    buyer_headers = {"Authorization": f"Bearer {buyer_login.json()['access_token']}"}

    po_data = {
        "buyer_company_id": str(companies["brand"].id),
        "seller_company_id": str(companies["processor"].id),
        "product_id": str(products["rbd_po"].id),
        "quantity": "1000.000",
        "unit_price": "1250.50",
        "unit": "KGM",
        "delivery_date": (date.today() + timedelta(days=30)).isoformat(),
        "delivery_location": "Brand Warehouse"
    }

    response = client.post("/purchase-orders/", json=po_data, headers=buyer_headers)
    po_id = response.json()["id"]

    # Submit PO
    client.patch(f"/purchase-orders/{po_id}/status",
                json={"status": "pending"}, headers=buyer_headers)

    # Seller confirms with discrepancies
    seller_login = client.post("/auth/login", json={
        "email": "sales@palmprocessing.com",
        "password": "processorpass123"
    })
    seller_headers = {"Authorization": f"Bearer {seller_login.json()['access_token']}"}

    confirmation_data = {
        "confirmed_quantity": "950.000",  # 50kg less than requested
        "confirmed_unit_price": "1275.00",  # $24.50 higher per kg
        "confirmed_delivery_date": (date.today() + timedelta(days=35)).isoformat(),  # 5 days later
        "seller_notes": "Can only provide 950kg due to inventory constraints"
    }

    response = client.post(
        f"/purchase-orders/{po_id}/confirm",
        json=confirmation_data,
        headers=seller_headers
    )
    assert response.status_code == 200

    po_response = response.json()
    # Should be awaiting buyer approval due to discrepancies
    assert po_response["status"] == "awaiting_buyer_approval"

    # Validate discrepancy details
    assert "discrepancies" in po_response
    discrepancies = po_response["discrepancies"]
    assert len(discrepancies) == 3  # quantity, price, delivery_date

    quantity_discrepancy = next(d for d in discrepancies if d["field"] == "quantity")
    assert quantity_discrepancy["original_value"] == "1000.000"
    assert quantity_discrepancy["confirmed_value"] == "950.000"
    assert quantity_discrepancy["impact"] == "decrease"

    # Buyer approves discrepancies
    approval_data = {
        "approve": True,
        "buyer_notes": "Acceptable - urgent need for this product"
    }

    response = client.post(
        f"/purchase-orders/{po_id}/approve-discrepancies",
        json=approval_data,
        headers=buyer_headers
    )
    assert response.status_code == 200

    final_po = response.json()
    assert final_po["status"] == "confirmed"
    assert final_po["quantity"] == "950.000"  # Updated to confirmed quantity
    assert final_po["unit_price"] == "1275.00"  # Updated to confirmed price
    assert final_po["buyer_approved_at"] is not None


def test_purchase_order_financial_calculations(
    client, db_session, supply_chain_companies, palm_oil_products, supply_chain_users
):
    """Test PO financial calculations and business rules."""
    companies = supply_chain_companies
    products = palm_oil_products

    buyer_login = client.post("/auth/login", json={
        "email": "buyer@globalbrand.com",
        "password": "brandpass123"
    })
    buyer_headers = {"Authorization": f"Bearer {buyer_login.json()['access_token']}"}

    # Test with high precision decimals
    po_data = {
        "buyer_company_id": str(companies["brand"].id),
        "seller_company_id": str(companies["processor"].id),
        "product_id": str(products["rbd_po"].id),
        "quantity": "1234.567",  # 3 decimal places
        "unit_price": "1250.89",  # 2 decimal places
        "unit": "KGM",
        "delivery_date": (date.today() + timedelta(days=30)).isoformat(),
        "delivery_location": "Brand Warehouse"
    }

    response = client.post("/purchase-orders/", json=po_data, headers=buyer_headers)
    assert response.status_code == 201

    po_response = response.json()

    # Validate precise financial calculations
    expected_total = Decimal("1234.567") * Decimal("1250.89")
    assert Decimal(po_response["total_amount"]) == expected_total.quantize(Decimal('0.01'))

    # Test business rule: unreasonably large quantities should be flagged
    large_po_data = po_data.copy()
    large_po_data["quantity"] = "10000000.000"  # 10 million kg

    response = client.post("/purchase-orders/", json=large_po_data, headers=buyer_headers)
    assert response.status_code == 422
    error_data = response.json()
    assert "unreasonably large" in str(error_data).lower()

    # Test business rule: unreasonably high prices should be flagged
    expensive_po_data = po_data.copy()
    expensive_po_data["unit_price"] = "500000.00"  # $500k per kg

    response = client.post("/purchase-orders/", json=expensive_po_data, headers=buyer_headers)
    assert response.status_code == 422
    error_data = response.json()
    assert "unreasonably high" in str(error_data).lower()


def test_purchase_order_traceability_requirements(
    client, db_session, supply_chain_companies, palm_oil_products, supply_chain_users
):
    """Test PO traceability and origin data requirements."""
    companies = supply_chain_companies
    products = palm_oil_products

    buyer_login = client.post("/auth/login", json={
        "email": "buyer@globalbrand.com",
        "password": "brandpass123"
    })
    buyer_headers = {"Authorization": f"Bearer {buyer_login.json()['access_token']}"}

    # Test PO for product requiring origin data
    po_data = {
        "buyer_company_id": str(companies["brand"].id),
        "seller_company_id": str(companies["processor"].id),
        "product_id": str(products["cpo"].id),  # Requires mill_id and extraction_date
        "quantity": "1000.000",
        "unit_price": "1100.00",
        "unit": "KGM",
        "delivery_date": (date.today() + timedelta(days=30)).isoformat(),
        "delivery_location": "Brand Warehouse",
        "origin_data": {
            "mill_id": str(companies["mill"].id),
            "extraction_date": "2024-01-15",
            "sustainability_certification": "RSPO",
            "deforestation_free": True
        }
    }

    response = client.post("/purchase-orders/", json=po_data, headers=buyer_headers)
    assert response.status_code == 201

    po_response = response.json()
    assert po_response["origin_data"]["mill_id"] == str(companies["mill"].id)
    assert po_response["origin_data"]["sustainability_certification"] == "RSPO"

    # Test PO missing required origin data
    incomplete_po_data = po_data.copy()
    incomplete_po_data["origin_data"] = {
        "sustainability_certification": "RSPO"
        # Missing required mill_id and extraction_date
    }

    response = client.post("/purchase-orders/", json=incomplete_po_data, headers=buyer_headers)
    assert response.status_code == 422
    error_data = response.json()
    assert "mill_id" in str(error_data).lower() or "extraction_date" in str(error_data).lower()


def test_purchase_order_access_control(
    client, db_session, supply_chain_companies, palm_oil_products, supply_chain_users
):
    """Test PO access control and authorization rules."""
    companies = supply_chain_companies
    products = palm_oil_products

    # Create PO as brand buyer
    buyer_login = client.post("/auth/login", json={
        "email": "buyer@globalbrand.com",
        "password": "brandpass123"
    })
    buyer_headers = {"Authorization": f"Bearer {buyer_login.json()['access_token']}"}

    po_data = {
        "buyer_company_id": str(companies["brand"].id),
        "seller_company_id": str(companies["processor"].id),
        "product_id": str(products["rbd_po"].id),
        "quantity": "1000.000",
        "unit_price": "1250.50",
        "unit": "KGM",
        "delivery_date": (date.today() + timedelta(days=30)).isoformat(),
        "delivery_location": "Brand Warehouse"
    }

    response = client.post("/purchase-orders/", json=po_data, headers=buyer_headers)
    assert response.status_code == 201
    po_id = response.json()["id"]

    # Test unauthorized company cannot access PO
    mill_login = client.post("/auth/login", json={
        "email": "ops@sustainablemill.com",
        "password": "millpass123"
    })
    mill_headers = {"Authorization": f"Bearer {mill_login.json()['access_token']}"}

    response = client.get(f"/purchase-orders/{po_id}", headers=mill_headers)
    assert response.status_code == 403

    # Test seller can access PO
    seller_login = client.post("/auth/login", json={
        "email": "sales@palmprocessing.com",
        "password": "processorpass123"
    })
    seller_headers = {"Authorization": f"Bearer {seller_login.json()['access_token']}"}

    response = client.get(f"/purchase-orders/{po_id}", headers=seller_headers)
    assert response.status_code == 200

    # Test unauthorized user cannot modify PO
    response = client.patch(
        f"/purchase-orders/{po_id}/status",
        json={"status": "cancelled"},
        headers=mill_headers
    )
    assert response.status_code == 403

    # Test buyer can modify their own PO
    response = client.patch(
        f"/purchase-orders/{po_id}/status",
        json={"status": "pending"},
        headers=buyer_headers
    )
    assert response.status_code == 200
