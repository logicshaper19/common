"""
Tests for purchase order functionality using conftest.py fixtures.
"""
import pytest
from datetime import date, timedelta
from decimal import Decimal


def test_create_purchase_order(client, test_buyer_company, test_seller_company, test_product, auth_headers):
    """Test creating a purchase order."""
    # Create users for the companies
    from app.tests.fixtures.factories import UserFactory
    from app.core.database import get_db
    
    db = next(get_db())
    
    # Create buyer user
    buyer_user = UserFactory.create_user(
        company=test_buyer_company,
        role="buyer"
    )
    db.add(buyer_user)
    
    # Create seller user  
    seller_user = UserFactory.create_user(
        company=test_seller_company,
        role="seller"
    )
    db.add(seller_user)
    
    db.commit()
    
    headers = auth_headers(buyer_user.email)
    
    tomorrow = date.today() + timedelta(days=1)
    
    po_data = {
        "buyer_company_id": str(test_buyer_company.id),
        "seller_company_id": str(test_seller_company.id),
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
    
    response = client.post("/api/v1/purchase-orders/", json=po_data, headers=headers)
    assert response.status_code == 200
    
    data = response.json()
    assert data["buyer_company_id"] == str(test_buyer_company.id)
    assert data["seller_company_id"] == str(test_seller_company.id)
    assert data["product_id"] == str(test_product.id)
    assert Decimal(data["quantity"]) == Decimal("100.500")
    assert Decimal(data["unit_price"]) == Decimal("25.75")
    assert Decimal(data["total_amount"]) == Decimal("2587.88")  # 100.500 * 25.75 rounded to 2 decimal places
    assert data["status"] == "draft"
    assert data["composition"]["component_a"] == 60.0
    assert data["po_number"].startswith("PO-")


def test_create_purchase_order_invalid_composition(client, test_buyer_company, test_seller_company, test_product, auth_headers):
    """Test creating a purchase order with invalid composition."""
    from app.tests.fixtures.factories import UserFactory
    from app.core.database import get_db
    
    db = next(get_db())
    
    buyer_user = UserFactory.create_user(
        company=test_buyer_company,
        role="buyer"
    )
    db.add(buyer_user)
    db.commit()
    
    headers = auth_headers(buyer_user.email)
    
    tomorrow = date.today() + timedelta(days=1)
    
    po_data = {
        "buyer_company_id": str(test_buyer_company.id),
        "seller_company_id": str(test_seller_company.id),
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
    
    response = client.post("/api/v1/purchase-orders/", json=po_data, headers=headers)
    assert response.status_code == 400
    assert "Invalid composition" in response.json()["detail"]


def test_create_purchase_order_unauthorized_company(client, test_buyer_company, test_seller_company, test_product, auth_headers):
    """Test creating a purchase order for unauthorized company."""
    from app.tests.fixtures.factories import UserFactory, CompanyFactory
    from app.core.database import get_db
    
    db = next(get_db())
    
    buyer_user = UserFactory.create_user(
        company=test_buyer_company,
        role="buyer"
    )
    db.add(buyer_user)
    db.commit()
    
    headers = auth_headers(buyer_user.email)
    
    # Create another company that the buyer user doesn't belong to
    other_company = CompanyFactory.create_company(
        company_type="brand",
        name="Other Corp"
    )
    db.add(other_company)
    db.commit()
    
    tomorrow = date.today() + timedelta(days=1)
    
    po_data = {
        "buyer_company_id": str(other_company.id),  # User doesn't belong to this company
        "seller_company_id": str(test_seller_company.id),
        "product_id": str(test_product.id),
        "quantity": "100.0",
        "unit_price": "25.0",
        "unit": "KGM",
        "delivery_date": tomorrow.isoformat(),
        "delivery_location": "123 Main St, City, Country"
    }
    
    response = client.post("/api/v1/purchase-orders/", json=po_data, headers=headers)
    assert response.status_code == 403
    assert "You can only create purchase orders for your own company" in response.json()["detail"]


def test_list_purchase_orders(client, test_buyer_company, test_seller_company, test_product, auth_headers):
    """Test listing purchase orders."""
    from app.tests.fixtures.factories import UserFactory
    from app.core.database import get_db
    
    db = next(get_db())
    
    buyer_user = UserFactory.create_user(
        company=test_buyer_company,
        role="buyer"
    )
    db.add(buyer_user)
    db.commit()
    
    headers = auth_headers(buyer_user.email)
    
    tomorrow = date.today() + timedelta(days=1)
    
    po_data = {
        "buyer_company_id": str(test_buyer_company.id),
        "seller_company_id": str(test_seller_company.id),
        "product_id": str(test_product.id),
        "quantity": "100.0",
        "unit_price": "25.0",
        "unit": "KGM",
        "delivery_date": tomorrow.isoformat(),
        "delivery_location": "123 Main St, City, Country"
    }
    
    create_response = client.post("/api/v1/purchase-orders/", json=po_data, headers=headers)
    assert create_response.status_code == 200
    
    # List purchase orders
    response = client.get("/api/v1/purchase-orders/", headers=headers)
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
    assert po["buyer_company"]["name"] == test_buyer_company.name
    assert po["seller_company"]["name"] == test_seller_company.name
    assert po["product"]["name"] == test_product.name


def test_get_purchase_order_by_id(client, test_buyer_company, test_seller_company, test_product, auth_headers):
    """Test getting a purchase order by ID."""
    from app.tests.fixtures.factories import UserFactory
    from app.core.database import get_db
    
    db = next(get_db())
    
    buyer_user = UserFactory.create_user(
        company=test_buyer_company,
        role="buyer"
    )
    db.add(buyer_user)
    db.commit()
    
    headers = auth_headers(buyer_user.email)
    
    tomorrow = date.today() + timedelta(days=1)
    
    po_data = {
        "buyer_company_id": str(test_buyer_company.id),
        "seller_company_id": str(test_seller_company.id),
        "product_id": str(test_product.id),
        "quantity": "100.0",
        "unit_price": "25.0",
        "unit": "KGM",
        "delivery_date": tomorrow.isoformat(),
        "delivery_location": "123 Main St, City, Country"
    }
    
    create_response = client.post("/api/v1/purchase-orders/", json=po_data, headers=headers)
    assert create_response.status_code == 200
    po_id = create_response.json()["id"]
    
    # Get the purchase order
    response = client.get(f"/api/v1/purchase-orders/{po_id}", headers=headers)
    assert response.status_code == 200
    
    data = response.json()
    assert data["id"] == po_id
    assert data["buyer_company"]["name"] == test_buyer_company.name
    assert data["seller_company"]["name"] == test_seller_company.name
    assert data["product"]["name"] == test_product.name


def test_update_purchase_order(client, test_buyer_company, test_seller_company, test_product, auth_headers):
    """Test updating a purchase order."""
    from app.tests.fixtures.factories import UserFactory
    from app.core.database import get_db
    
    db = next(get_db())
    
    buyer_user = UserFactory.create_user(
        company=test_buyer_company,
        role="buyer"
    )
    db.add(buyer_user)
    db.commit()
    
    headers = auth_headers(buyer_user.email)
    
    tomorrow = date.today() + timedelta(days=1)
    
    po_data = {
        "buyer_company_id": str(test_buyer_company.id),
        "seller_company_id": str(test_seller_company.id),
        "product_id": str(test_product.id),
        "quantity": "100.0",
        "unit_price": "25.0",
        "unit": "KGM",
        "delivery_date": tomorrow.isoformat(),
        "delivery_location": "123 Main St, City, Country"
    }
    
    create_response = client.post("/api/v1/purchase-orders/", json=po_data, headers=headers)
    assert create_response.status_code == 200
    po_id = create_response.json()["id"]
    
    # Update the purchase order
    update_data = {
        "quantity": "150.0",
        "unit_price": "30.0",
        "status": "confirmed",
        "notes": "Updated purchase order"
    }
    
    response = client.put(f"/api/v1/purchase-orders/{po_id}", json=update_data, headers=headers)
    assert response.status_code == 200
    
    data = response.json()
    assert Decimal(data["quantity"]) == Decimal("150.0")
    assert Decimal(data["unit_price"]) == Decimal("30.0")
    assert Decimal(data["total_amount"]) == Decimal("150.0") * Decimal("30.0")
    assert data["status"] == "confirmed"
    assert data["notes"] == "Updated purchase order"


def test_delete_purchase_order(client, test_buyer_company, test_seller_company, test_product, auth_headers):
    """Test deleting a purchase order."""
    from app.tests.fixtures.factories import UserFactory
    from app.core.database import get_db
    
    db = next(get_db())
    
    buyer_user = UserFactory.create_user(
        company=test_buyer_company,
        role="buyer"
    )
    db.add(buyer_user)
    db.commit()
    
    headers = auth_headers(buyer_user.email)

    tomorrow = date.today() + timedelta(days=1)

    po_data = {
        "buyer_company_id": str(test_buyer_company.id),
        "seller_company_id": str(test_seller_company.id),
        "product_id": str(test_product.id),
        "quantity": "100.0",
        "unit_price": "25.0",
        "unit": "KGM",
        "delivery_date": tomorrow.isoformat(),
        "delivery_location": "123 Main St, City, Country"
    }

    create_response = client.post("/api/v1/purchase-orders/", json=po_data, headers=headers)
    assert create_response.status_code == 200
    po_id = create_response.json()["id"]

    # Delete the purchase order
    response = client.delete(f"/api/v1/purchase-orders/{po_id}", headers=headers)
    assert response.status_code == 200
    assert response.json()["message"] == "Purchase order deleted successfully"

    # Verify it's deleted
    get_response = client.get(f"/api/v1/purchase-orders/{po_id}", headers=headers)
    assert get_response.status_code == 404


def test_delete_purchase_order_non_draft(client, test_buyer_company, test_seller_company, test_product, auth_headers):
    """Test deleting a non-draft purchase order (should fail)."""
    from app.tests.fixtures.factories import UserFactory
    from app.core.database import get_db
    
    db = next(get_db())
    
    buyer_user = UserFactory.create_user(
        company=test_buyer_company,
        role="buyer"
    )
    db.add(buyer_user)
    db.commit()
    
    headers = auth_headers(buyer_user.email)

    tomorrow = date.today() + timedelta(days=1)

    po_data = {
        "buyer_company_id": str(test_buyer_company.id),
        "seller_company_id": str(test_seller_company.id),
        "product_id": str(test_product.id),
        "quantity": "100.0",
        "unit_price": "25.0",
        "unit": "KGM",
        "delivery_date": tomorrow.isoformat(),
        "delivery_location": "123 Main St, City, Country"
    }

    create_response = client.post("/api/v1/purchase-orders/", json=po_data, headers=headers)
    assert create_response.status_code == 200
    po_id = create_response.json()["id"]

    # Update to confirmed status
    update_response = client.put(f"/api/v1/purchase-orders/{po_id}", json={"status": "confirmed"}, headers=headers)
    assert update_response.status_code == 200

    # Try to delete (should fail)
    response = client.delete(f"/api/v1/purchase-orders/{po_id}", headers=headers)
    assert response.status_code == 400
    assert "Only draft purchase orders can be deleted" in response.json()["detail"]


def test_purchase_order_filtering(client, test_buyer_company, test_seller_company, test_product, auth_headers):
    """Test purchase order filtering."""
    from app.tests.fixtures.factories import UserFactory
    from app.core.database import get_db
    
    db = next(get_db())
    
    buyer_user = UserFactory.create_user(
        company=test_buyer_company,
        role="buyer"
    )
    db.add(buyer_user)
    db.commit()
    
    headers = auth_headers(buyer_user.email)

    tomorrow = date.today() + timedelta(days=1)
    next_week = date.today() + timedelta(days=7)

    # Create multiple purchase orders
    po_data_1 = {
        "buyer_company_id": str(test_buyer_company.id),
        "seller_company_id": str(test_seller_company.id),
        "product_id": str(test_product.id),
        "quantity": "100.0",
        "unit_price": "25.0",
        "unit": "KGM",
        "delivery_date": tomorrow.isoformat(),
        "delivery_location": "Location A",
        "notes": "First order"
    }

    po_data_2 = {
        "buyer_company_id": str(test_buyer_company.id),
        "seller_company_id": str(test_seller_company.id),
        "product_id": str(test_product.id),
        "quantity": "200.0",
        "unit_price": "30.0",
        "unit": "KGM",
        "delivery_date": next_week.isoformat(),
        "delivery_location": "Location B",
        "notes": "Second order"
    }

    # Create the orders
    response1 = client.post("/api/v1/purchase-orders/", json=po_data_1, headers=headers)
    assert response1.status_code == 200
    po_id_1 = response1.json()["id"]

    response2 = client.post("/api/v1/purchase-orders/", json=po_data_2, headers=headers)
    assert response2.status_code == 200
    po_id_2 = response2.json()["id"]

    # Update first order to confirmed
    client.put(f"/api/v1/purchase-orders/{po_id_1}", json={"status": "confirmed"}, headers=headers)

    # Test filtering by status
    response = client.get("/api/v1/purchase-orders/?status=confirmed", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    confirmed_orders = [po for po in data["purchase_orders"] if po["status"] == "confirmed"]
    assert len(confirmed_orders) >= 1

    # Test filtering by delivery date
    response = client.get(f"/api/v1/purchase-orders/?delivery_date_from={tomorrow.isoformat()}&delivery_date_to={tomorrow.isoformat()}", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1

    # Test search functionality
    response = client.get("/api/v1/purchase-orders/?search=First", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    found_orders = [po for po in data["purchase_orders"] if "First" in (po["notes"] or "")]
    assert len(found_orders) >= 1


def test_trace_supply_chain_basic(client, test_buyer_company, test_seller_company, test_product, auth_headers):
    """Test basic supply chain tracing."""
    from app.tests.fixtures.factories import UserFactory
    from app.core.database import get_db
    
    db = next(get_db())
    
    buyer_user = UserFactory.create_user(
        company=test_buyer_company,
        role="buyer"
    )
    db.add(buyer_user)
    db.commit()
    
    headers = auth_headers(buyer_user.email)

    tomorrow = date.today() + timedelta(days=1)

    # Create a purchase order
    po_data = {
        "buyer_company_id": str(test_buyer_company.id),
        "seller_company_id": str(test_seller_company.id),
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

    create_response = client.post("/api/v1/purchase-orders/", json=po_data, headers=headers)
    assert create_response.status_code == 200
    po_id = create_response.json()["id"]

    # Trace the supply chain
    trace_request = {
        "purchase_order_id": po_id,
        "depth": 3
    }

    response = client.post("/api/v1/purchase-orders/trace", json=trace_request, headers=headers)
    assert response.status_code == 200

    data = response.json()
    assert data["root_purchase_order"]["purchase_order_id"] == po_id
    assert data["root_purchase_order"]["product_name"] == test_product.name
    assert data["root_purchase_order"]["company_name"] == test_seller_company.name
    assert data["root_purchase_order"]["level"] == 0
    assert data["total_nodes"] == 1  # Only root node since no input materials
    assert data["max_depth_reached"] == 0


def test_access_control_seller_can_see_orders(client, test_buyer_company, test_seller_company, test_product, auth_headers):
    """Test that seller can also see and update purchase orders."""
    from app.tests.fixtures.factories import UserFactory
    from app.core.database import get_db
    
    db = next(get_db())
    
    # Create buyer user
    buyer_user = UserFactory.create_user(
        company=test_buyer_company,
        role="buyer"
    )
    db.add(buyer_user)
    
    # Create seller user
    seller_user = UserFactory.create_user(
        company=test_seller_company,
        role="seller"
    )
    db.add(seller_user)
    
    db.commit()
    
    # Create order as buyer
    buyer_headers = auth_headers(buyer_user.email)

    tomorrow = date.today() + timedelta(days=1)

    po_data = {
        "buyer_company_id": str(test_buyer_company.id),
        "seller_company_id": str(test_seller_company.id),
        "product_id": str(test_product.id),
        "quantity": "100.0",
        "unit_price": "25.0",
        "unit": "KGM",
        "delivery_date": tomorrow.isoformat(),
        "delivery_location": "123 Main St, City, Country"
    }

    create_response = client.post("/api/v1/purchase-orders/", json=po_data, headers=buyer_headers)
    assert create_response.status_code == 200
    po_id = create_response.json()["id"]

    # Seller should be able to see the order
    seller_headers = auth_headers(seller_user.email)

    response = client.get(f"/api/v1/purchase-orders/{po_id}", headers=seller_headers)
    assert response.status_code == 200

    # Seller should be able to update the order
    update_response = client.put(f"/api/v1/purchase-orders/{po_id}", json={"status": "confirmed"}, headers=seller_headers)
    assert update_response.status_code == 200
    assert update_response.json()["status"] == "confirmed"

    # Seller should see the order in their list
    list_response = client.get("/api/v1/purchase-orders/", headers=seller_headers)
    assert list_response.status_code == 200
    assert list_response.json()["total"] >= 1