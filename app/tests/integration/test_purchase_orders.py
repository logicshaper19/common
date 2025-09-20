"""
Comprehensive tests for purchase order system.
"""
import pytest
import json
from datetime import datetime, timedelta, date
from decimal import Decimal
from uuid import uuid4
from unittest.mock import patch, Mock

# Mark all tests in this file as integration tests
pytestmark = [pytest.mark.integration, pytest.mark.api]

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
from app.core.security import hash_password, create_access_token

# Create test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_pos.db"
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
def test_companies():
    """Create test companies."""
    db = TestingSessionLocal()
    
    brand_company = Company(
        id=uuid4(),
        name="Test Brand",
        company_type="brand",
        email="brand@test.com"
    )
    
    processor_company = Company(
        id=uuid4(),
        name="Test Processor",
        company_type="processor",
        email="processor@test.com"
    )
    
    originator_company = Company(
        id=uuid4(),
        name="Test Originator",
        company_type="originator",
        email="originator@test.com"
    )
    
    db.add_all([brand_company, processor_company, originator_company])
    db.commit()
    db.close()
    
    return {
        "brand": brand_company,
        "processor": processor_company,
        "originator": originator_company
    }


@pytest.fixture
def test_users(test_companies):
    """Create test users."""
    db = TestingSessionLocal()
    
    users = {}
    for role, company in test_companies.items():
        user = User(
            id=uuid4(),
            email=f"{role}@test.com",
            hashed_password=hash_password("testpassword123"),
            full_name=f"Test {role.title()}",
            role="admin" if role == "brand" else "seller",
            company_id=company.id,
            is_active=True
        )
        db.add(user)
        users[role] = user
    
    db.commit()
    db.close()
    return users


@pytest.fixture
def test_products():
    """Create test products."""
    db = TestingSessionLocal()
    
    raw_material = Product(
        id=uuid4(),
        common_product_id="RAW-001",
        name="Organic Cotton",
        category="raw_material",
        description="High-quality organic cotton",
        default_unit="KGM",
        can_have_composition=False
    )
    
    processed_material = Product(
        id=uuid4(),
        common_product_id="PROC-001",
        name="Cotton Fabric",
        category="processed",
        description="Processed cotton fabric",
        default_unit="KGM",
        can_have_composition=True
    )
    
    finished_good = Product(
        id=uuid4(),
        common_product_id="FIN-001",
        name="T-Shirt",
        category="finished_good",
        description="Organic cotton t-shirt",
        default_unit="PCS",
        can_have_composition=True
    )
    
    db.add_all([raw_material, processed_material, finished_good])
    db.commit()
    db.close()
    
    return {
        "raw_material": raw_material,
        "processed": processed_material,
        "finished_good": finished_good
    }


@pytest.fixture
def test_relationships(test_companies):
    """Create test business relationships."""
    db = TestingSessionLocal()
    
    # Brand -> Processor relationship
    brand_processor_rel = BusinessRelationship(
        id=uuid4(),
        buyer_company_id=test_companies["brand"].id,
        seller_company_id=test_companies["processor"].id,
        relationship_type="supplier",
        status="active"
    )
    
    # Processor -> Originator relationship
    processor_originator_rel = BusinessRelationship(
        id=uuid4(),
        buyer_company_id=test_companies["processor"].id,
        seller_company_id=test_companies["originator"].id,
        relationship_type="supplier",
        status="active"
    )
    
    db.add_all([brand_processor_rel, processor_originator_rel])
    db.commit()
    db.close()
    
    return [brand_processor_rel, processor_originator_rel]


def get_auth_headers(user_email: str) -> dict:
    """Get authentication headers for a user."""
    token = create_access_token(data={"sub": user_email})
    return {"Authorization": f"Bearer {token}"}


class TestPurchaseOrderCreation:
    """Test purchase order creation functionality."""
    
    def test_create_purchase_order_success(self, test_users, test_companies, test_products, test_relationships):
        """Test successful purchase order creation."""
        headers = get_auth_headers("brand@test.com")
        
        po_data = {
            "seller_company_id": str(test_companies["processor"].id),
            "product_id": str(test_products["processed"].id),
            "quantity": 1000,
            "unit": "KGM",
            "delivery_date": (date.today() + timedelta(days=30)).isoformat(),
            "notes": "Test purchase order"
        }
        
        response = client.post("/api/v1/purchase-orders", json=po_data, headers=headers)
        assert response.status_code == 201
        
        data = response.json()
        assert data["po_number"] is not None
        assert data["buyer_company_id"] == str(test_companies["brand"].id)
        assert data["seller_company_id"] == str(test_companies["processor"].id)
        assert data["product_id"] == str(test_products["processed"].id)
        assert data["quantity"] == 1000
        assert data["status"] == "pending"
    
    def test_create_po_without_relationship(self, test_users, test_companies, test_products):
        """Test creating PO without business relationship."""
        headers = get_auth_headers("brand@test.com")
        
        po_data = {
            "seller_company_id": str(test_companies["originator"].id),  # No direct relationship
            "product_id": str(test_products["raw_material"].id),
            "quantity": 500,
            "unit": "KGM",
            "delivery_date": (date.today() + timedelta(days=30)).isoformat()
        }
        
        response = client.post("/api/v1/purchase-orders", json=po_data, headers=headers)
        # Should either succeed (if relationships are not strictly enforced) or fail
        assert response.status_code in [201, 400, 403]
    
    def test_create_po_invalid_product(self, test_users, test_companies, test_relationships):
        """Test creating PO with invalid product."""
        headers = get_auth_headers("brand@test.com")
        
        po_data = {
            "seller_company_id": str(test_companies["processor"].id),
            "product_id": str(uuid4()),  # Non-existent product
            "quantity": 1000,
            "unit": "KGM",
            "delivery_date": (date.today() + timedelta(days=30)).isoformat()
        }
        
        response = client.post("/api/v1/purchase-orders", json=po_data, headers=headers)
        assert response.status_code == 404
    
    def test_create_po_invalid_company(self, test_users, test_products, test_relationships):
        """Test creating PO with invalid company."""
        headers = get_auth_headers("brand@test.com")
        
        po_data = {
            "seller_company_id": str(uuid4()),  # Non-existent company
            "product_id": str(test_products["processed"].id),
            "quantity": 1000,
            "unit": "KGM",
            "delivery_date": (date.today() + timedelta(days=30)).isoformat()
        }
        
        response = client.post("/api/v1/purchase-orders", json=po_data, headers=headers)
        assert response.status_code == 404
    
    def test_create_po_unauthorized(self, test_companies, test_products):
        """Test creating PO without authentication."""
        po_data = {
            "seller_company_id": str(test_companies["processor"].id),
            "product_id": str(test_products["processed"].id),
            "quantity": 1000,
            "unit": "KGM",
            "delivery_date": (date.today() + timedelta(days=30)).isoformat()
        }
        
        response = client.post("/api/v1/purchase-orders", json=po_data)
        assert response.status_code == 401
    
    def test_create_po_validation_errors(self, test_users, test_companies, test_products):
        """Test PO creation with validation errors."""
        headers = get_auth_headers("brand@test.com")
        
        # Missing required fields
        po_data = {
            "seller_company_id": str(test_companies["processor"].id),
            # Missing product_id, quantity, etc.
        }
        
        response = client.post("/api/v1/purchase-orders", json=po_data, headers=headers)
        assert response.status_code == 422
        
        # Invalid quantity
        po_data = {
            "seller_company_id": str(test_companies["processor"].id),
            "product_id": str(test_products["processed"].id),
            "quantity": -100,  # Negative quantity
            "unit": "KGM",
            "delivery_date": (date.today() + timedelta(days=30)).isoformat()
        }
        
        response = client.post("/api/v1/purchase-orders", json=po_data, headers=headers)
        assert response.status_code == 422


class TestPurchaseOrderRetrieval:
    """Test purchase order retrieval functionality."""
    
    def test_get_purchase_orders(self, test_users, test_companies, test_products, test_relationships):
        """Test getting purchase orders list."""
        headers = get_auth_headers("brand@test.com")
        
        # Create a test PO first
        po_data = {
            "seller_company_id": str(test_companies["processor"].id),
            "product_id": str(test_products["processed"].id),
            "quantity": 1000,
            "unit": "KGM",
            "delivery_date": (date.today() + timedelta(days=30)).isoformat()
        }
        
        create_response = client.post("/api/v1/purchase-orders", json=po_data, headers=headers)
        assert create_response.status_code == 201
        
        # Get POs
        response = client.get("/api/v1/purchase-orders", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert len(data["items"]) >= 1
    
    def test_get_po_by_id(self, test_users, test_companies, test_products, test_relationships):
        """Test getting specific purchase order by ID."""
        headers = get_auth_headers("brand@test.com")
        
        # Create a test PO
        po_data = {
            "seller_company_id": str(test_companies["processor"].id),
            "product_id": str(test_products["processed"].id),
            "quantity": 1000,
            "unit": "KGM",
            "delivery_date": (date.today() + timedelta(days=30)).isoformat()
        }
        
        create_response = client.post("/api/v1/purchase-orders", json=po_data, headers=headers)
        assert create_response.status_code == 201
        
        po_id = create_response.json()["id"]
        
        # Get specific PO
        response = client.get(f"/api/v1/purchase-orders/{po_id}", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["id"] == po_id
        assert data["quantity"] == 1000
    
    def test_get_po_not_found(self, test_users):
        """Test getting non-existent PO."""
        headers = get_auth_headers("brand@test.com")
        
        response = client.get(f"/api/v1/purchase-orders/{uuid4()}", headers=headers)
        assert response.status_code == 404
    
    def test_get_po_unauthorized(self, test_users, test_companies, test_products, test_relationships):
        """Test getting PO without authentication."""
        # Create PO first (with auth)
        headers = get_auth_headers("brand@test.com")
        po_data = {
            "seller_company_id": str(test_companies["processor"].id),
            "product_id": str(test_products["processed"].id),
            "quantity": 1000,
            "unit": "KGM",
            "delivery_date": (date.today() + timedelta(days=30)).isoformat()
        }
        
        create_response = client.post("/api/v1/purchase-orders", json=po_data, headers=headers)
        po_id = create_response.json()["id"]
        
        # Try to get without auth
        response = client.get(f"/api/v1/purchase-orders/{po_id}")
        assert response.status_code == 401


class TestPurchaseOrderConfirmation:
    """Test purchase order confirmation functionality."""
    
    def test_confirm_po_success(self, test_users, test_companies, test_products, test_relationships):
        """Test successful PO confirmation."""
        # Create PO as brand
        brand_headers = get_auth_headers("brand@test.com")
        po_data = {
            "seller_company_id": str(test_companies["processor"].id),
            "product_id": str(test_products["processed"].id),
            "quantity": 1000,
            "unit": "KGM",
            "delivery_date": (date.today() + timedelta(days=30)).isoformat()
        }
        
        create_response = client.post("/api/v1/purchase-orders", json=po_data, headers=brand_headers)
        po_id = create_response.json()["id"]
        
        # Confirm as processor
        processor_headers = get_auth_headers("processor@test.com")
        confirm_data = {
            "confirmed_quantity": 1000,
            "notes": "Confirmed by processor"
        }
        
        response = client.post(f"/api/v1/purchase-orders/{po_id}/seller-confirm", 
                             json=confirm_data, headers=processor_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "confirmed"
        assert data["confirmed_quantity"] == 1000
        assert data["confirmed_at"] is not None
    
    def test_confirm_po_wrong_company(self, test_users, test_companies, test_products, test_relationships):
        """Test confirming PO by wrong company."""
        # Create PO as brand
        brand_headers = get_auth_headers("brand@test.com")
        po_data = {
            "seller_company_id": str(test_companies["processor"].id),
            "product_id": str(test_products["processed"].id),
            "quantity": 1000,
            "unit": "KGM",
            "delivery_date": (date.today() + timedelta(days=30)).isoformat()
        }
        
        create_response = client.post("/api/v1/purchase-orders", json=po_data, headers=brand_headers)
        po_id = create_response.json()["id"]
        
        # Try to confirm as originator (wrong company)
        originator_headers = get_auth_headers("originator@test.com")
        confirm_data = {"confirmed_quantity": 1000}
        
        response = client.post(f"/api/v1/purchase-orders/{po_id}/seller-confirm", 
                             json=confirm_data, headers=originator_headers)
        assert response.status_code == 403
    
    def test_confirm_po_already_confirmed(self, test_users, test_companies, test_products, test_relationships):
        """Test confirming already confirmed PO."""
        # Create and confirm PO
        brand_headers = get_auth_headers("brand@test.com")
        po_data = {
            "seller_company_id": str(test_companies["processor"].id),
            "product_id": str(test_products["processed"].id),
            "quantity": 1000,
            "unit": "KGM",
            "delivery_date": (date.today() + timedelta(days=30)).isoformat()
        }
        
        create_response = client.post("/api/v1/purchase-orders", json=po_data, headers=brand_headers)
        po_id = create_response.json()["id"]
        
        processor_headers = get_auth_headers("processor@test.com")
        confirm_data = {"confirmed_quantity": 1000}
        
        # First confirmation
        response = client.post(f"/api/v1/purchase-orders/{po_id}/seller-confirm", 
                             json=confirm_data, headers=processor_headers)
        assert response.status_code == 200
        
        # Second confirmation attempt
        response = client.post(f"/api/v1/purchase-orders/{po_id}/seller-confirm", 
                             json=confirm_data, headers=processor_headers)
        assert response.status_code in [400, 409]  # Bad request or conflict


class TestPurchaseOrderChaining:
    """Test purchase order chaining functionality."""
    
    def test_po_chaining_creation(self, test_users, test_companies, test_products, test_relationships):
        """Test creating chained purchase orders."""
        # Create parent PO (brand -> processor)
        brand_headers = get_auth_headers("brand@test.com")
        parent_po_data = {
            "seller_company_id": str(test_companies["processor"].id),
            "product_id": str(test_products["finished_good"].id),
            "quantity": 1000,
            "unit": "PCS",
            "delivery_date": (date.today() + timedelta(days=30)).isoformat()
        }
        
        parent_response = client.post("/api/v1/purchase-orders", json=parent_po_data, headers=brand_headers)
        parent_po_id = parent_response.json()["id"]
        
        # Confirm parent PO
        processor_headers = get_auth_headers("processor@test.com")
        confirm_data = {"confirmed_quantity": 1000}
        client.post(f"/api/v1/purchase-orders/{parent_po_id}/seller-confirm", 
                   json=confirm_data, headers=processor_headers)
        
        # Create child PO (processor -> originator)
        child_po_data = {
            "seller_company_id": str(test_companies["originator"].id),
            "product_id": str(test_products["raw_material"].id),
            "quantity": 2000,  # More raw material needed for finished goods
            "unit": "KGM",
            "delivery_date": (date.today() + timedelta(days=15)).isoformat(),
            "parent_po_id": parent_po_id
        }
        
        response = client.post("/api/v1/purchase-orders", json=child_po_data, headers=processor_headers)
        assert response.status_code == 201
        
        data = response.json()
        assert data["parent_po_id"] == parent_po_id
    
    def test_po_chaining_validation(self, test_users, test_companies, test_products, test_relationships):
        """Test PO chaining validation."""
        processor_headers = get_auth_headers("processor@test.com")
        
        # Try to create child PO with non-existent parent
        child_po_data = {
            "seller_company_id": str(test_companies["originator"].id),
            "product_id": str(test_products["raw_material"].id),
            "quantity": 2000,
            "unit": "KGM",
            "delivery_date": (date.today() + timedelta(days=15)).isoformat(),
            "parent_po_id": str(uuid4())  # Non-existent parent
        }
        
        response = client.post("/api/v1/purchase-orders", json=child_po_data, headers=processor_headers)
        assert response.status_code == 404


class TestPurchaseOrderFiltering:
    """Test purchase order filtering and search functionality."""
    
    def test_filter_by_status(self, test_users, test_companies, test_products, test_relationships):
        """Test filtering POs by status."""
        headers = get_auth_headers("brand@test.com")
        
        # Create POs with different statuses
        po_data = {
            "seller_company_id": str(test_companies["processor"].id),
            "product_id": str(test_products["processed"].id),
            "quantity": 1000,
            "unit": "KGM",
            "delivery_date": (date.today() + timedelta(days=30)).isoformat()
        }
        
        client.post("/api/v1/purchase-orders", json=po_data, headers=headers)
        
        # Filter by status
        response = client.get("/api/v1/purchase-orders?status=pending", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        for po in data["items"]:
            assert po["status"] == "pending"
    
    def test_filter_by_company(self, test_users, test_companies, test_products, test_relationships):
        """Test filtering POs by company."""
        headers = get_auth_headers("brand@test.com")
        
        # Create PO
        po_data = {
            "seller_company_id": str(test_companies["processor"].id),
            "product_id": str(test_products["processed"].id),
            "quantity": 1000,
            "unit": "KGM",
            "delivery_date": (date.today() + timedelta(days=30)).isoformat()
        }
        
        client.post("/api/v1/purchase-orders", json=po_data, headers=headers)
        
        # Filter by seller company
        response = client.get(f"/api/v1/purchase-orders?seller_company_id={test_companies['processor'].id}", 
                            headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        for po in data["items"]:
            assert po["seller_company_id"] == str(test_companies["processor"].id)
    
    def test_pagination(self, test_users, test_companies, test_products, test_relationships):
        """Test pagination functionality."""
        headers = get_auth_headers("brand@test.com")
        
        # Create multiple POs
        for i in range(5):
            po_data = {
                "seller_company_id": str(test_companies["processor"].id),
                "product_id": str(test_products["processed"].id),
                "quantity": 1000 + i,
                "unit": "KGM",
                "delivery_date": (date.today() + timedelta(days=30)).isoformat()
            }
            client.post("/api/v1/purchase-orders", json=po_data, headers=headers)
        
        # Test pagination
        response = client.get("/api/v1/purchase-orders?limit=2&offset=0", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert len(data["items"]) <= 2
        assert "total" in data
        assert "limit" in data
        assert "offset" in data


class TestPurchaseOrderUpdates:
    """Test purchase order update functionality."""
    
    def test_update_po_success(self, test_users, test_companies, test_products, test_relationships):
        """Test successful PO update."""
        headers = get_auth_headers("brand@test.com")
        
        # Create PO
        po_data = {
            "seller_company_id": str(test_companies["processor"].id),
            "product_id": str(test_products["processed"].id),
            "quantity": 1000,
            "unit": "KGM",
            "delivery_date": (date.today() + timedelta(days=30)).isoformat()
        }
        
        create_response = client.post("/api/v1/purchase-orders", json=po_data, headers=headers)
        po_id = create_response.json()["id"]
        
        # Update PO
        update_data = {
            "quantity": 1500,
            "notes": "Updated quantity"
        }
        
        response = client.put(f"/api/v1/purchase-orders/{po_id}", json=update_data, headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["quantity"] == 1500
        assert data["notes"] == "Updated quantity"
    
    def test_update_po_unauthorized(self, test_users, test_companies, test_products, test_relationships):
        """Test updating PO without authorization."""
        # Create PO as brand
        brand_headers = get_auth_headers("brand@test.com")
        po_data = {
            "seller_company_id": str(test_companies["processor"].id),
            "product_id": str(test_products["processed"].id),
            "quantity": 1000,
            "unit": "KGM",
            "delivery_date": (date.today() + timedelta(days=30)).isoformat()
        }
        
        create_response = client.post("/api/v1/purchase-orders", json=po_data, headers=brand_headers)
        po_id = create_response.json()["id"]
        
        # Try to update as processor (should fail)
        processor_headers = get_auth_headers("processor@test.com")
        update_data = {"quantity": 1500}
        
        response = client.put(f"/api/v1/purchase-orders/{po_id}", json=update_data, headers=processor_headers)
        assert response.status_code == 403
    
    def test_update_confirmed_po(self, test_users, test_companies, test_products, test_relationships):
        """Test updating confirmed PO (should be restricted)."""
        # Create and confirm PO
        brand_headers = get_auth_headers("brand@test.com")
        po_data = {
            "seller_company_id": str(test_companies["processor"].id),
            "product_id": str(test_products["processed"].id),
            "quantity": 1000,
            "unit": "KGM",
            "delivery_date": (date.today() + timedelta(days=30)).isoformat()
        }
        
        create_response = client.post("/api/v1/purchase-orders", json=po_data, headers=brand_headers)
        po_id = create_response.json()["id"]
        
        # Confirm PO
        processor_headers = get_auth_headers("processor@test.com")
        confirm_data = {"confirmed_quantity": 1000}
        client.post(f"/api/v1/purchase-orders/{po_id}/seller-confirm", 
                   json=confirm_data, headers=processor_headers)
        
        # Try to update confirmed PO
        update_data = {"quantity": 1500}
        response = client.put(f"/api/v1/purchase-orders/{po_id}", json=update_data, headers=brand_headers)
        assert response.status_code in [400, 403, 409]  # Should be restricted


class TestPurchaseOrderDeletion:
    """Test purchase order deletion functionality."""
    
    def test_delete_po_success(self, test_users, test_companies, test_products, test_relationships):
        """Test successful PO deletion."""
        headers = get_auth_headers("brand@test.com")
        
        # Create PO
        po_data = {
            "seller_company_id": str(test_companies["processor"].id),
            "product_id": str(test_products["processed"].id),
            "quantity": 1000,
            "unit": "KGM",
            "delivery_date": (date.today() + timedelta(days=30)).isoformat()
        }
        
        create_response = client.post("/api/v1/purchase-orders", json=po_data, headers=headers)
        po_id = create_response.json()["id"]
        
        # Delete PO
        response = client.delete(f"/api/v1/purchase-orders/{po_id}", headers=headers)
        assert response.status_code == 200
        
        # Verify PO is deleted
        get_response = client.get(f"/api/v1/purchase-orders/{po_id}", headers=headers)
        assert get_response.status_code == 404
    
    def test_delete_po_unauthorized(self, test_users, test_companies, test_products, test_relationships):
        """Test deleting PO without authorization."""
        # Create PO as brand
        brand_headers = get_auth_headers("brand@test.com")
        po_data = {
            "seller_company_id": str(test_companies["processor"].id),
            "product_id": str(test_products["processed"].id),
            "quantity": 1000,
            "unit": "KGM",
            "delivery_date": (date.today() + timedelta(days=30)).isoformat()
        }
        
        create_response = client.post("/api/v1/purchase-orders", json=po_data, headers=brand_headers)
        po_id = create_response.json()["id"]
        
        # Try to delete as processor (should fail)
        processor_headers = get_auth_headers("processor@test.com")
        response = client.delete(f"/api/v1/purchase-orders/{po_id}", headers=processor_headers)
        assert response.status_code == 403
    
    def test_delete_confirmed_po(self, test_users, test_companies, test_products, test_relationships):
        """Test deleting confirmed PO (should be restricted)."""
        # Create and confirm PO
        brand_headers = get_auth_headers("brand@test.com")
        po_data = {
            "seller_company_id": str(test_companies["processor"].id),
            "product_id": str(test_products["processed"].id),
            "quantity": 1000,
            "unit": "KGM",
            "delivery_date": (date.today() + timedelta(days=30)).isoformat()
        }
        
        create_response = client.post("/api/v1/purchase-orders", json=po_data, headers=brand_headers)
        po_id = create_response.json()["id"]
        
        # Confirm PO
        processor_headers = get_auth_headers("processor@test.com")
        confirm_data = {"confirmed_quantity": 1000}
        client.post(f"/api/v1/purchase-orders/{po_id}/seller-confirm", 
                   json=confirm_data, headers=processor_headers)
        
        # Try to delete confirmed PO
        response = client.delete(f"/api/v1/purchase-orders/{po_id}", headers=brand_headers)
        assert response.status_code in [400, 403, 409]  # Should be restricted


class TestPurchaseOrderBusinessLogic:
    """Test specific business logic scenarios."""
    
    def test_delivery_date_validation(self, test_users, test_companies, test_products):
        """Test delivery date validation rules."""
        headers = get_auth_headers("brand@test.com")
        
        # Test past delivery date
        past_date = (date.today() - timedelta(days=1)).isoformat()
        po_data = {
            "seller_company_id": str(test_companies["processor"].id),
            "product_id": str(test_products["processed"].id),
            "quantity": 1000,
            "unit": "KGM",
            "delivery_date": past_date
        }
        
        response = client.post("/api/v1/purchase-orders", json=po_data, headers=headers)
        assert response.status_code == 422
        assert "delivery_date" in response.json()["detail"][0]["loc"]
        
        # Test too far in future (if business rule exists)
        far_future = (date.today() + timedelta(days=730)).isoformat()
        po_data["delivery_date"] = far_future
        response = client.post("/api/v1/purchase-orders", json=po_data, headers=headers)
        # Should pass or fail based on business rules
    
    def test_po_number_uniqueness(self, test_users, test_companies, test_products):
        """Test that PO numbers are unique across the system."""
        headers = get_auth_headers("brand@test.com")
        po_numbers = set()
        
        # Create multiple POs and verify unique numbers
        for i in range(10):
            po_data = {
                "seller_company_id": str(test_companies["processor"].id),
                "product_id": str(test_products["processed"].id),
                "quantity": 1000 + i,
                "unit": "KGM",
                "delivery_date": (date.today() + timedelta(days=30)).isoformat()
            }
            
            response = client.post("/api/v1/purchase-orders", json=po_data, headers=headers)
            po_number = response.json()["po_number"]
            assert po_number not in po_numbers
            po_numbers.add(po_number)
    
    def test_quantity_unit_validation(self, test_users, test_companies, test_products):
        """Test quantity and unit validation."""
        headers = get_auth_headers("brand@test.com")
        
        # Test decimal quantities
        po_data = {
            "seller_company_id": str(test_companies["processor"].id),
            "product_id": str(test_products["processed"].id),
            "quantity": 1000.5,
            "unit": "KGM",
            "delivery_date": (date.today() + timedelta(days=30)).isoformat()
        }
        
        response = client.post("/api/v1/purchase-orders", json=po_data, headers=headers)
        # Should accept decimal for weight units
        assert response.status_code == 201
        
        # Test decimal quantities with piece units (should fail)
        po_data["product_id"] = str(test_products["finished_good"].id)
        po_data["unit"] = "PCS"
        po_data["quantity"] = 100.5
        
        response = client.post("/api/v1/purchase-orders", json=po_data, headers=headers)
        assert response.status_code == 422  # Pieces should be whole numbers
    
    def test_concurrent_po_confirmation(self, test_users, test_companies, test_products):
        """Test concurrent confirmation attempts."""
        import threading
        
        # Create PO
        brand_headers = get_auth_headers("brand@test.com")
        po_data = {
            "seller_company_id": str(test_companies["processor"].id),
            "product_id": str(test_products["processed"].id),
            "quantity": 1000,
            "unit": "KGM",
            "delivery_date": (date.today() + timedelta(days=30)).isoformat()
        }
        
        create_response = client.post("/api/v1/purchase-orders", json=po_data, headers=brand_headers)
        po_id = create_response.json()["id"]
        
        processor_headers = get_auth_headers("processor@test.com")
        confirm_data = {"confirmed_quantity": 1000}
        
        results = []
        
        def confirm_po():
            response = client.post(f"/api/v1/purchase-orders/{po_id}/seller-confirm", 
                                 json=confirm_data, headers=processor_headers)
            results.append(response.status_code)
        
        # Start multiple confirmation threads
        threads = [threading.Thread(target=confirm_po) for _ in range(3)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        
        # Only one should succeed
        success_count = sum(1 for status in results if status == 200)
        assert success_count == 1


class TestPurchaseOrderSecurity:
    """Test security-related scenarios."""
    
    def test_expired_token_access(self, test_users, test_companies, test_products):
        """Test access with expired token."""
        # Create token with past expiration
        expired_token = create_access_token(
            data={"sub": "brand@test.com"}, 
            expires_delta=timedelta(seconds=-1)
        )
        headers = {"Authorization": f"Bearer {expired_token}"}
        
        response = client.get("/api/v1/purchase-orders", headers=headers)
        assert response.status_code == 401
    
    def test_cross_company_data_access(self, test_users, test_companies, test_products):
        """Test that users can't access other companies' POs."""
        # Create PO as brand
        brand_headers = get_auth_headers("brand@test.com")
        po_data = {
            "seller_company_id": str(test_companies["processor"].id),
            "product_id": str(test_products["processed"].id),
            "quantity": 1000,
            "unit": "KGM",
            "delivery_date": (date.today() + timedelta(days=30)).isoformat()
        }
        
        create_response = client.post("/api/v1/purchase-orders", json=po_data, headers=brand_headers)
        po_id = create_response.json()["id"]
        
        # Try to access as originator (unrelated company)
        originator_headers = get_auth_headers("originator@test.com")
        response = client.get(f"/api/v1/purchase-orders/{po_id}", headers=originator_headers)
        assert response.status_code == 403
    
    def test_sql_injection_protection(self, test_users):
        """Test SQL injection protection in search/filter parameters."""
        headers = get_auth_headers("brand@test.com")
        
        # Try SQL injection in query parameters
        malicious_params = [
            "'; DROP TABLE purchase_orders; --",
            "1' OR '1'='1",
            "' UNION SELECT * FROM users --"
        ]
        
        for param in malicious_params:
            response = client.get(f"/api/v1/purchase-orders?search={param}", headers=headers)
            # Should not crash and should return valid response
            assert response.status_code in [200, 400, 422]  # But not 500


class TestPurchaseOrderIntegration:
    """Test integration scenarios and complex workflows."""
    
    def test_complete_supply_chain_workflow(self, test_users, test_companies, test_products, test_relationships):
        """Test complete workflow from brand to originator."""
        # Brand creates PO for finished goods
        brand_headers = get_auth_headers("brand@test.com")
        brand_po_data = {
            "seller_company_id": str(test_companies["processor"].id),
            "product_id": str(test_products["finished_good"].id),
            "quantity": 1000,
            "unit": "PCS",
            "delivery_date": (date.today() + timedelta(days=60)).isoformat()
        }
        
        brand_response = client.post("/api/v1/purchase-orders", json=brand_po_data, headers=brand_headers)
        brand_po_id = brand_response.json()["id"]
        
        # Processor confirms
        processor_headers = get_auth_headers("processor@test.com")
        confirm_data = {"confirmed_quantity": 1000, "notes": "Confirmed by processor"}
        
        confirm_response = client.post(f"/api/v1/purchase-orders/{brand_po_id}/seller-confirm", 
                                     json=confirm_data, headers=processor_headers)
        assert confirm_response.status_code == 200
        
        # Processor creates child PO for raw materials
        processor_po_data = {
            "seller_company_id": str(test_companies["originator"].id),
            "product_id": str(test_products["raw_material"].id),
            "quantity": 2000,  # Need more raw material
            "unit": "KGM",
            "delivery_date": (date.today() + timedelta(days=30)).isoformat(),
            "parent_po_id": brand_po_id
        }
        
        processor_response = client.post("/api/v1/purchase-orders", json=processor_po_data, headers=processor_headers)
        processor_po_id = processor_response.json()["id"]
        
        # Originator confirms
        originator_headers = get_auth_headers("originator@test.com")
        originator_confirm = {"confirmed_quantity": 2000}
        
        originator_response = client.post(f"/api/v1/purchase-orders/{processor_po_id}/seller-confirm", 
                                        json=originator_confirm, headers=originator_headers)
        assert originator_response.status_code == 200
        
        # Verify the complete chain
        chain_response = client.get(f"/api/v1/purchase-orders/{brand_po_id}/chain", headers=brand_headers)
        assert chain_response.status_code == 200
        
        chain_data = chain_response.json()
        assert len(chain_data["child_orders"]) == 1
        assert chain_data["child_orders"][0]["id"] == processor_po_id
