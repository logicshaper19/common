"""
Tests for purchase order functionality.
"""
import pytest
from datetime import date, timedelta
from decimal import Decimal
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import Base, get_db
from app.models.user import User
from app.models.company import Company
from app.models.product import Product
from app.models.purchase_order import PurchaseOrder
from app.services.product import ProductService
from app.services.purchase_order import PurchaseOrderService
from app.schemas.purchase_order import PurchaseOrderCreate, PurchaseOrderStatus
from app.core.security import hash_password
from uuid import uuid4

# Create test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_purchase_orders.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
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
    # Drop all tables and recreate them
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture
def db():
    """Get database session for testing."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_auth_headers(user_email: str, password: str) -> dict:
    """Get authentication headers for a user."""
    response = client.post(
        "/auth/login",
        json={"email": user_email, "password": password}
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def buyer_company(db: Session):
    """Create a buyer company for testing."""
    company = Company(
        id=uuid4(),
        name="Buyer Corp",
        company_type="brand",
        email="buyer@company.com"
    )
    db.add(company)
    db.commit()
    db.refresh(company)
    return company


@pytest.fixture
def seller_company(db: Session):
    """Create a seller company for testing."""
    company = Company(
        id=uuid4(),
        name="Seller Corp",
        company_type="processor",
        email="seller@company.com"
    )
    db.add(company)
    db.commit()
    db.refresh(company)
    return company


@pytest.fixture
def buyer_user(db: Session, buyer_company: Company):
    """Create a buyer user for testing."""
    user = User(
        id=uuid4(),
        email="buyer@example.com",
        hashed_password=hash_password("buyerpassword123"),
        full_name="Buyer User",
        role="buyer",
        company_id=buyer_company.id,
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def seller_user(db: Session, seller_company: Company):
    """Create a seller user for testing."""
    user = User(
        id=uuid4(),
        email="seller@example.com",
        hashed_password=hash_password("sellerpassword123"),
        full_name="Seller User",
        role="supplier",
        company_id=seller_company.id,
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def test_product(db: Session):
    """Create a test product."""
    product = Product(
        id=uuid4(),
        common_product_id="TEST-001",
        name="Test Product",
        description="A test product",
        category="processed",
        can_have_composition=True,
        material_breakdown={"component_a": 60.0, "component_b": 40.0},
        default_unit="KGM",
        hs_code="1234.56.78"
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


def test_create_purchase_order(buyer_user, seller_user, test_product, buyer_company, seller_company):
    """Test creating a purchase order."""
    headers = get_auth_headers("buyer@example.com", "buyerpassword123")
    
    tomorrow = date.today() + timedelta(days=1)
    
    po_data = {
        "buyer_company_id": str(buyer_company.id),
        "seller_company_id": str(seller_company.id),
        "product_id": str(test_product.id),
        "quantity": "100.500",
        "unit_price": "25.75",
        "unit": "KGM",
        "delivery_date": tomorrow.isoformat(),
        "delivery_location": "123 Main St, City, Country",
        "composition": {
            "component_a": 60.0,
            "component_b": 40.0
        },
        "notes": "Test purchase order"
    }
    
    response = client.post("/purchase-orders/", json=po_data, headers=headers)
    assert response.status_code == 200
    
    data = response.json()
    assert data["buyer_company_id"] == str(buyer_company.id)
    assert data["seller_company_id"] == str(seller_company.id)
    assert data["product_id"] == str(test_product.id)
    assert Decimal(data["quantity"]) == Decimal("100.500")
    assert Decimal(data["unit_price"]) == Decimal("25.75")
    assert Decimal(data["total_amount"]) == Decimal("2587.88")  # 100.500 * 25.75 rounded to 2 decimal places
    assert data["status"] == "draft"
    assert data["composition"]["component_a"] == 60.0
    assert data["po_number"].startswith("PO-")


def test_create_purchase_order_invalid_composition(buyer_user, seller_user, test_product, buyer_company, seller_company):
    """Test creating a purchase order with invalid composition."""
    headers = get_auth_headers("buyer@example.com", "buyerpassword123")
    
    tomorrow = date.today() + timedelta(days=1)
    
    po_data = {
        "buyer_company_id": str(buyer_company.id),
        "seller_company_id": str(seller_company.id),
        "product_id": str(test_product.id),
        "quantity": "100.0",
        "unit_price": "25.0",
        "unit": "KGM",
        "delivery_date": tomorrow.isoformat(),
        "delivery_location": "123 Main St, City, Country",
        "composition": {
            "invalid_component": 100.0  # Invalid - unknown material
        }
    }
    
    response = client.post("/purchase-orders/", json=po_data, headers=headers)
    assert response.status_code == 400
    assert "Invalid composition" in response.json()["detail"]


def test_create_purchase_order_unauthorized_company(buyer_user, seller_user, test_product, seller_company):
    """Test creating a purchase order for unauthorized company."""
    headers = get_auth_headers("buyer@example.com", "buyerpassword123")
    
    # Create another company that the buyer user doesn't belong to
    from app.models.company import Company
    from app.core.database import get_db
    
    db = next(get_db())
    other_company = Company(
        id=uuid4(),
        name="Other Corp",
        company_type="brand",
        email="other-unique@company.com"
    )
    db.add(other_company)
    db.commit()
    db.refresh(other_company)
    
    tomorrow = date.today() + timedelta(days=1)
    
    po_data = {
        "buyer_company_id": str(other_company.id),  # User doesn't belong to this company
        "seller_company_id": str(seller_company.id),
        "product_id": str(test_product.id),
        "quantity": "100.0",
        "unit_price": "25.0",
        "unit": "KGM",
        "delivery_date": tomorrow.isoformat(),
        "delivery_location": "123 Main St, City, Country"
    }
    
    response = client.post("/purchase-orders/", json=po_data, headers=headers)
    assert response.status_code == 403
    assert "You can only create purchase orders for your own company" in response.json()["detail"]


def test_list_purchase_orders(buyer_user, seller_user, test_product, buyer_company, seller_company):
    """Test listing purchase orders."""
    # Create a purchase order first
    headers = get_auth_headers("buyer@example.com", "buyerpassword123")
    
    tomorrow = date.today() + timedelta(days=1)
    
    po_data = {
        "buyer_company_id": str(buyer_company.id),
        "seller_company_id": str(seller_company.id),
        "product_id": str(test_product.id),
        "quantity": "100.0",
        "unit_price": "25.0",
        "unit": "KGM",
        "delivery_date": tomorrow.isoformat(),
        "delivery_location": "123 Main St, City, Country"
    }
    
    create_response = client.post("/purchase-orders/", json=po_data, headers=headers)
    assert create_response.status_code == 200
    
    # List purchase orders
    response = client.get("/purchase-orders/", headers=headers)
    assert response.status_code == 200
    
    data = response.json()
    assert data["total"] >= 1
    assert len(data["purchase_orders"]) >= 1
    assert data["page"] == 1
    assert data["per_page"] == 20
    
    # Check that the purchase order has detailed information
    po = data["purchase_orders"][0]
    assert "buyer_company" in po
    assert "seller_company" in po
    assert "product" in po
    assert po["buyer_company"]["name"] == "Buyer Corp"
    assert po["seller_company"]["name"] == "Seller Corp"
    assert po["product"]["name"] == "Test Product"


def test_get_purchase_order_by_id(buyer_user, seller_user, test_product, buyer_company, seller_company):
    """Test getting a purchase order by ID."""
    # Create a purchase order first
    headers = get_auth_headers("buyer@example.com", "buyerpassword123")
    
    tomorrow = date.today() + timedelta(days=1)
    
    po_data = {
        "buyer_company_id": str(buyer_company.id),
        "seller_company_id": str(seller_company.id),
        "product_id": str(test_product.id),
        "quantity": "100.0",
        "unit_price": "25.0",
        "unit": "KGM",
        "delivery_date": tomorrow.isoformat(),
        "delivery_location": "123 Main St, City, Country"
    }
    
    create_response = client.post("/purchase-orders/", json=po_data, headers=headers)
    assert create_response.status_code == 200
    po_id = create_response.json()["id"]
    
    # Get the purchase order
    response = client.get(f"/purchase-orders/{po_id}", headers=headers)
    assert response.status_code == 200
    
    data = response.json()
    assert data["id"] == po_id
    assert data["buyer_company"]["name"] == "Buyer Corp"
    assert data["seller_company"]["name"] == "Seller Corp"
    assert data["product"]["name"] == "Test Product"


def test_update_purchase_order(buyer_user, seller_user, test_product, buyer_company, seller_company):
    """Test updating a purchase order."""
    # Create a purchase order first
    headers = get_auth_headers("buyer@example.com", "buyerpassword123")
    
    tomorrow = date.today() + timedelta(days=1)
    
    po_data = {
        "buyer_company_id": str(buyer_company.id),
        "seller_company_id": str(seller_company.id),
        "product_id": str(test_product.id),
        "quantity": "100.0",
        "unit_price": "25.0",
        "unit": "KGM",
        "delivery_date": tomorrow.isoformat(),
        "delivery_location": "123 Main St, City, Country"
    }
    
    create_response = client.post("/purchase-orders/", json=po_data, headers=headers)
    assert create_response.status_code == 200
    po_id = create_response.json()["id"]
    
    # Update the purchase order
    update_data = {
        "quantity": "150.0",
        "unit_price": "30.0",
        "status": "confirmed",
        "notes": "Updated purchase order"
    }
    
    response = client.put(f"/purchase-orders/{po_id}", json=update_data, headers=headers)
    assert response.status_code == 200
    
    data = response.json()
    assert Decimal(data["quantity"]) == Decimal("150.0")
    assert Decimal(data["unit_price"]) == Decimal("30.0")
    assert Decimal(data["total_amount"]) == Decimal("150.0") * Decimal("30.0")
    assert data["status"] == "confirmed"
    assert data["notes"] == "Updated purchase order"


def test_delete_purchase_order(buyer_user, seller_user, test_product, buyer_company, seller_company):
    """Test deleting a purchase order."""
    # Create a purchase order first
    headers = get_auth_headers("buyer@example.com", "buyerpassword123")

    tomorrow = date.today() + timedelta(days=1)

    po_data = {
        "buyer_company_id": str(buyer_company.id),
        "seller_company_id": str(seller_company.id),
        "product_id": str(test_product.id),
        "quantity": "100.0",
        "unit_price": "25.0",
        "unit": "KGM",
        "delivery_date": tomorrow.isoformat(),
        "delivery_location": "123 Main St, City, Country"
    }

    create_response = client.post("/purchase-orders/", json=po_data, headers=headers)
    assert create_response.status_code == 200
    po_id = create_response.json()["id"]

    # Delete the purchase order
    response = client.delete(f"/purchase-orders/{po_id}", headers=headers)
    assert response.status_code == 200
    assert response.json()["message"] == "Purchase order deleted successfully"

    # Verify it's deleted
    get_response = client.get(f"/purchase-orders/{po_id}", headers=headers)
    assert get_response.status_code == 404


def test_delete_purchase_order_non_draft(buyer_user, seller_user, test_product, buyer_company, seller_company):
    """Test deleting a non-draft purchase order (should fail)."""
    # Create and confirm a purchase order first
    headers = get_auth_headers("buyer@example.com", "buyerpassword123")

    tomorrow = date.today() + timedelta(days=1)

    po_data = {
        "buyer_company_id": str(buyer_company.id),
        "seller_company_id": str(seller_company.id),
        "product_id": str(test_product.id),
        "quantity": "100.0",
        "unit_price": "25.0",
        "unit": "KGM",
        "delivery_date": tomorrow.isoformat(),
        "delivery_location": "123 Main St, City, Country"
    }

    create_response = client.post("/purchase-orders/", json=po_data, headers=headers)
    assert create_response.status_code == 200
    po_id = create_response.json()["id"]

    # Update to confirmed status
    update_response = client.put(f"/purchase-orders/{po_id}", json={"status": "confirmed"}, headers=headers)
    assert update_response.status_code == 200

    # Try to delete (should fail)
    response = client.delete(f"/purchase-orders/{po_id}", headers=headers)
    assert response.status_code == 400
    assert "Only draft purchase orders can be deleted" in response.json()["detail"]


def test_purchase_order_filtering(buyer_user, seller_user, test_product, buyer_company, seller_company):
    """Test purchase order filtering."""
    headers = get_auth_headers("buyer@example.com", "buyerpassword123")

    tomorrow = date.today() + timedelta(days=1)
    next_week = date.today() + timedelta(days=7)

    # Create multiple purchase orders
    po_data_1 = {
        "buyer_company_id": str(buyer_company.id),
        "seller_company_id": str(seller_company.id),
        "product_id": str(test_product.id),
        "quantity": "100.0",
        "unit_price": "25.0",
        "unit": "KGM",
        "delivery_date": tomorrow.isoformat(),
        "delivery_location": "Location A",
        "notes": "First order"
    }

    po_data_2 = {
        "buyer_company_id": str(buyer_company.id),
        "seller_company_id": str(seller_company.id),
        "product_id": str(test_product.id),
        "quantity": "200.0",
        "unit_price": "30.0",
        "unit": "KGM",
        "delivery_date": next_week.isoformat(),
        "delivery_location": "Location B",
        "notes": "Second order"
    }

    # Create the orders
    response1 = client.post("/purchase-orders/", json=po_data_1, headers=headers)
    assert response1.status_code == 200
    po_id_1 = response1.json()["id"]

    response2 = client.post("/purchase-orders/", json=po_data_2, headers=headers)
    assert response2.status_code == 200
    po_id_2 = response2.json()["id"]

    # Update first order to confirmed
    client.put(f"/purchase-orders/{po_id_1}", json={"status": "confirmed"}, headers=headers)

    # Test filtering by status
    response = client.get("/purchase-orders/?status=confirmed", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    confirmed_orders = [po for po in data["purchase_orders"] if po["status"] == "confirmed"]
    assert len(confirmed_orders) >= 1

    # Test filtering by delivery date
    response = client.get(f"/purchase-orders/?delivery_date_from={tomorrow.isoformat()}&delivery_date_to={tomorrow.isoformat()}", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1

    # Test search functionality
    response = client.get("/purchase-orders/?search=First", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    found_orders = [po for po in data["purchase_orders"] if "First" in (po["notes"] or "")]
    assert len(found_orders) >= 1


def test_trace_supply_chain_basic(buyer_user, seller_user, test_product, buyer_company, seller_company):
    """Test basic supply chain tracing."""
    headers = get_auth_headers("buyer@example.com", "buyerpassword123")

    tomorrow = date.today() + timedelta(days=1)

    # Create a purchase order
    po_data = {
        "buyer_company_id": str(buyer_company.id),
        "seller_company_id": str(seller_company.id),
        "product_id": str(test_product.id),
        "quantity": "100.0",
        "unit_price": "25.0",
        "unit": "KGM",
        "delivery_date": tomorrow.isoformat(),
        "delivery_location": "123 Main St, City, Country",
        "origin_data": {
            "coordinates": {"lat": 1.234, "lng": 103.567},
            "certifications": ["RSPO", "Organic"]
        }
    }

    create_response = client.post("/purchase-orders/", json=po_data, headers=headers)
    assert create_response.status_code == 200
    po_id = create_response.json()["id"]

    # Trace the supply chain
    trace_request = {
        "purchase_order_id": po_id,
        "depth": 3
    }

    response = client.post("/purchase-orders/trace", json=trace_request, headers=headers)
    assert response.status_code == 200

    data = response.json()
    assert data["root_purchase_order"]["purchase_order_id"] == po_id
    assert data["root_purchase_order"]["product_name"] == "Test Product"
    assert data["root_purchase_order"]["company_name"] == "Seller Corp"
    assert data["root_purchase_order"]["level"] == 0
    assert data["total_nodes"] == 1  # Only root node since no input materials
    assert data["max_depth_reached"] == 0


def test_access_control_seller_can_see_orders(buyer_user, seller_user, test_product, buyer_company, seller_company):
    """Test that seller can also see and update purchase orders."""
    # Create order as buyer
    buyer_headers = get_auth_headers("buyer@example.com", "buyerpassword123")

    tomorrow = date.today() + timedelta(days=1)

    po_data = {
        "buyer_company_id": str(buyer_company.id),
        "seller_company_id": str(seller_company.id),
        "product_id": str(test_product.id),
        "quantity": "100.0",
        "unit_price": "25.0",
        "unit": "KGM",
        "delivery_date": tomorrow.isoformat(),
        "delivery_location": "123 Main St, City, Country"
    }

    create_response = client.post("/purchase-orders/", json=po_data, headers=buyer_headers)
    assert create_response.status_code == 200
    po_id = create_response.json()["id"]

    # Seller should be able to see the order
    seller_headers = get_auth_headers("seller@example.com", "sellerpassword123")

    response = client.get(f"/purchase-orders/{po_id}", headers=seller_headers)
    assert response.status_code == 200

    # Seller should be able to update the order
    update_response = client.put(f"/purchase-orders/{po_id}", json={"status": "confirmed"}, headers=seller_headers)
    assert update_response.status_code == 200
    assert update_response.json()["status"] == "confirmed"

    # Seller should see the order in their list
    list_response = client.get("/purchase-orders/", headers=seller_headers)
    assert list_response.status_code == 200
    assert list_response.json()["total"] >= 1
