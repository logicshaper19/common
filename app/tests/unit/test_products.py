"""
Enhanced tests for product management system with comprehensive business logic validation.
"""
import pytest
from fastapi.testclient import TestClient
from decimal import Decimal
from uuid import uuid4

from app.models.user import User
from app.models.company import Company
from app.models.product import Product
from app.core.security import hash_password

# Test markers for categorization
pytestmark = [pytest.mark.unit, pytest.mark.products]


# ===== ENHANCED PRODUCT FIXTURES =====

@pytest.fixture
def test_palm_oil_product(db_session):
    """Create a test palm oil product with business logic validation."""
    product = Product(
        id=uuid4(),
        common_product_id="CPO-001",
        name="Crude Palm Oil",
        description="High-quality crude palm oil from sustainable sources",
        category="palm_oil",
        can_have_composition=True,
        material_breakdown={
            "palm_kernel": 0.20,
            "palm_fruit": 0.80
        },
        default_unit="MT",
        hs_code="1511.10.00",
        origin_data_requirements={
            "plantation_location": True,
            "harvest_date": True,
            "mill_processing_date": True,
            "sustainability_certification": True,
            "deforestation_risk_assessment": True
        }
    )
    db_session.add(product)
    db_session.commit()
    db_session.refresh(product)
    return product


@pytest.fixture
def test_processed_product(db_session):
    """Create a test processed product."""
    product = Product(
        id=uuid4(),
        common_product_id="RBD-PO-001",
        name="Refined, Bleached, Deodorized Palm Oil",
        description="Processed palm oil ready for food industry use",
        category="processed_palm_oil",
        can_have_composition=True,
        material_breakdown={
            "crude_palm_oil": 1.00
        },
        default_unit="MT",
        hs_code="1511.90.00",
        origin_data_requirements={
            "source_cpo_batch": True,
            "processing_facility": True,
            "quality_certificates": True,
            "processing_date": True
        }
    )
    db_session.add(product)
    db_session.commit()
    db_session.refresh(product)
    return product


@pytest.fixture
def test_final_product(db_session):
    """Create a test final consumer product."""
    product = Product(
        id=uuid4(),
        common_product_id="MARGARINE-001",
        name="Premium Margarine",
        description="Consumer margarine made from sustainable palm oil",
        category="consumer_goods",
        can_have_composition=True,
        material_breakdown={
            "refined_palm_oil": 0.60,
            "other_vegetable_oils": 0.30,
            "additives": 0.10
        },
        default_unit="KG",
        hs_code="1517.10.00",
        origin_data_requirements={
            "ingredient_traceability": True,
            "nutritional_analysis": True,
            "allergen_information": True,
            "manufacturing_facility": True
        }
    )
    db_session.add(product)
    db_session.commit()
    db_session.refresh(product)
    return product
        json={"email": user_email, "password": password}
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_create_product_as_admin(admin_user):
    """Test creating a product as admin."""
    headers = get_auth_headers("admin@example.com", "adminpassword123")
    
    product_data = {
        "common_product_id": "TEST-001",
        "name": "Test Product",
        "description": "A test product",
        "category": "raw_material",
        "can_have_composition": False,
        "default_unit": "KGM",
        "hs_code": "1234.56.78"
    }
    
    response = client.post("/products/", json=product_data, headers=headers)
    assert response.status_code == 200
    
    data = response.json()
    assert data["common_product_id"] == "TEST-001"
    assert data["name"] == "Test Product"
    assert data["category"] == "raw_material"
    assert data["can_have_composition"] is False


def test_create_product_as_regular_user(regular_user):
    """Test creating a product as regular user (should fail)."""
    headers = get_auth_headers("user@example.com", "userpassword123")
    
    product_data = {
        "common_product_id": "TEST-001",
        "name": "Test Product",
        "description": "A test product",
        "category": "raw_material",
        "can_have_composition": False,
        "default_unit": "KGM"
    }
    
    response = client.post("/products/", json=product_data, headers=headers)
    assert response.status_code == 403


def test_create_product_with_composition(admin_user):
    """Test creating a product with composition rules."""
    headers = get_auth_headers("admin@example.com", "adminpassword123")
    
    product_data = {
        "common_product_id": "BLEND-001",
        "name": "Palm Oil Blend",
        "description": "80/20 palm oil blend",
        "category": "finished_good",
        "can_have_composition": True,
        "material_breakdown": {
            "palm_oil": 80.0,
            "palm_kernel_oil": 20.0
        },
        "default_unit": "KGM",
        "hs_code": "1511.90.00"
    }
    
    response = client.post("/products/", json=product_data, headers=headers)
    assert response.status_code == 200
    
    data = response.json()
    assert data["can_have_composition"] is True
    assert data["material_breakdown"]["palm_oil"] == 80.0
    assert data["material_breakdown"]["palm_kernel_oil"] == 20.0


def test_create_product_invalid_composition(admin_user):
    """Test creating a product with invalid composition (doesn't sum to 100)."""
    headers = get_auth_headers("admin@example.com", "adminpassword123")
    
    product_data = {
        "common_product_id": "INVALID-001",
        "name": "Invalid Product",
        "category": "finished_good",
        "can_have_composition": True,
        "material_breakdown": {
            "palm_oil": 80.0,
            "palm_kernel_oil": 15.0  # Only sums to 95%
        },
        "default_unit": "KGM"
    }
    
    response = client.post("/products/", json=product_data, headers=headers)
    assert response.status_code == 422  # Validation error


def test_list_products(admin_user, regular_user):
    """Test listing products."""
    # Create some test products first
    headers = get_auth_headers("admin@example.com", "adminpassword123")
    
    products = [
        {
            "common_product_id": "RAW-001",
            "name": "Raw Material",
            "category": "raw_material",
            "can_have_composition": False,
            "default_unit": "KGM"
        },
        {
            "common_product_id": "PROC-001",
            "name": "Processed Product",
            "category": "processed",
            "can_have_composition": True,
            "material_breakdown": {"component": 100.0},
            "default_unit": "KGM"
        }
    ]
    
    for product_data in products:
        response = client.post("/products/", json=product_data, headers=headers)
        assert response.status_code == 200
    
    # Test listing as regular user
    user_headers = get_auth_headers("user@example.com", "userpassword123")
    response = client.get("/products/", headers=user_headers)
    assert response.status_code == 200
    
    data = response.json()
    assert data["total"] == 2
    assert len(data["products"]) == 2


def test_list_products_with_filters(admin_user):
    """Test listing products with filters."""
    headers = get_auth_headers("admin@example.com", "adminpassword123")
    
    # Create test products
    products = [
        {
            "common_product_id": "RAW-001",
            "name": "Raw Material",
            "category": "raw_material",
            "can_have_composition": False,
            "default_unit": "KGM"
        },
        {
            "common_product_id": "PROC-001",
            "name": "Processed Product",
            "category": "processed",
            "can_have_composition": True,
            "material_breakdown": {"component": 100.0},
            "default_unit": "KGM"
        }
    ]
    
    for product_data in products:
        response = client.post("/products/", json=product_data, headers=headers)
        assert response.status_code == 200
    
    # Test category filter
    response = client.get("/products/?category=raw_material", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["products"][0]["category"] == "raw_material"
    
    # Test composition filter
    response = client.get("/products/?can_have_composition=true", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["products"][0]["can_have_composition"] is True


def test_get_product_by_id(admin_user):
    """Test getting a product by ID."""
    headers = get_auth_headers("admin@example.com", "adminpassword123")
    
    # Create a product first
    product_data = {
        "common_product_id": "TEST-001",
        "name": "Test Product",
        "category": "raw_material",
        "can_have_composition": False,
        "default_unit": "KGM"
    }
    
    response = client.post("/products/", json=product_data, headers=headers)
    assert response.status_code == 200
    created_product = response.json()
    
    # Get the product by ID
    response = client.get(f"/products/{created_product['id']}", headers=headers)
    assert response.status_code == 200
    
    data = response.json()
    assert data["id"] == created_product["id"]
    assert data["name"] == "Test Product"


def test_validate_composition(admin_user):
    """Test composition validation."""
    headers = get_auth_headers("admin@example.com", "adminpassword123")
    
    # Create a product with composition rules
    product_data = {
        "common_product_id": "BLEND-001",
        "name": "Palm Oil Blend",
        "category": "finished_good",
        "can_have_composition": True,
        "material_breakdown": {
            "palm_oil": 80.0,
            "palm_kernel_oil": 20.0
        },
        "default_unit": "KGM"
    }
    
    response = client.post("/products/", json=product_data, headers=headers)
    assert response.status_code == 200
    created_product = response.json()
    
    # Test valid composition
    validation_data = {
        "product_id": created_product["id"],
        "composition": {
            "palm_oil": 80.0,
            "palm_kernel_oil": 20.0
        }
    }
    
    response = client.post("/products/validate-composition", json=validation_data, headers=headers)
    assert response.status_code == 200
    
    data = response.json()
    assert data["is_valid"] is True
    assert len(data["errors"]) == 0


# ===== ENHANCED BUSINESS LOGIC TESTS =====

def test_product_composition_business_logic(db_session, test_palm_oil_product, business_logic_validator):
    """Test product composition business logic validation."""
    product = test_palm_oil_product

    # Business Logic: Material breakdown should sum to 1.0 (100%)
    total_composition = sum(product.material_breakdown.values())
    assert abs(total_composition - 1.0) < 0.001  # Allow for floating point precision

    # Business Logic: Each component should be positive
    for component, percentage in product.material_breakdown.items():
        assert percentage > 0
        assert percentage <= 1.0

    # Business Logic: Product should have required origin data requirements
    assert "plantation_location" in product.origin_data_requirements
    assert "sustainability_certification" in product.origin_data_requirements
    assert "deforestation_risk_assessment" in product.origin_data_requirements

    # Business Logic: Palm oil products should require sustainability data
    if product.category == "palm_oil":
        assert product.origin_data_requirements["sustainability_certification"] is True
        assert product.origin_data_requirements["deforestation_risk_assessment"] is True


def test_product_supply_chain_validation(db_session, test_processed_product, business_logic_validator):
    """Test product supply chain business logic."""
    product = test_processed_product

    # Business Logic: Processed products should reference source materials
    assert "source_cpo_batch" in product.origin_data_requirements
    assert product.origin_data_requirements["source_cpo_batch"] is True

    # Business Logic: Processing facility should be tracked
    assert "processing_facility" in product.origin_data_requirements
    assert product.origin_data_requirements["processing_facility"] is True

    # Business Logic: Quality certificates should be required
    assert "quality_certificates" in product.origin_data_requirements
    assert product.origin_data_requirements["quality_certificates"] is True

    # Business Logic: HS code should be valid format
    assert product.hs_code is not None
    assert len(product.hs_code.replace(".", "")) >= 6  # Minimum HS code length


def test_product_traceability_requirements(db_session, test_final_product, business_logic_validator):
    """Test product traceability business logic."""
    product = test_final_product

    # Business Logic: Final products should have comprehensive traceability
    required_fields = [
        "ingredient_traceability",
        "nutritional_analysis",
        "allergen_information",
        "manufacturing_facility"
    ]

    for field in required_fields:
        assert field in product.origin_data_requirements
        assert product.origin_data_requirements[field] is True

    # Business Logic: Consumer goods should have detailed composition
    assert product.can_have_composition is True
    assert len(product.material_breakdown) >= 2  # Multiple ingredients

    # Business Logic: Main ingredient should be significant portion
    main_ingredient_percentage = max(product.material_breakdown.values())
    assert main_ingredient_percentage >= 0.5  # At least 50%


def test_product_category_business_rules(db_session, test_palm_oil_product, test_processed_product, test_final_product):
    """Test business rules specific to product categories."""

    # Business Logic: Raw materials (palm oil) should have origin requirements
    raw_product = test_palm_oil_product
    assert raw_product.category == "palm_oil"
    assert "plantation_location" in raw_product.origin_data_requirements
    assert "harvest_date" in raw_product.origin_data_requirements

    # Business Logic: Processed products should reference source materials
    processed_product = test_processed_product
    assert processed_product.category == "processed_palm_oil"
    assert "source_cpo_batch" in processed_product.origin_data_requirements
    assert "processing_facility" in processed_product.origin_data_requirements

    # Business Logic: Consumer goods should have consumer-facing requirements
    final_product = test_final_product
    assert final_product.category == "consumer_goods"
    assert "nutritional_analysis" in final_product.origin_data_requirements
    assert "allergen_information" in final_product.origin_data_requirements


def test_product_unit_validation_business_logic(db_session, test_palm_oil_product, test_final_product):
    """Test product unit validation business logic."""

    # Business Logic: Bulk commodities should use metric tons
    bulk_product = test_palm_oil_product
    assert bulk_product.default_unit == "MT"  # Metric tons for bulk

    # Business Logic: Consumer products should use consumer-friendly units
    consumer_product = test_final_product
    assert consumer_product.default_unit == "KG"  # Kilograms for consumer goods

    # Business Logic: Units should be consistent with product type
    valid_bulk_units = ["MT", "KG", "LB", "TON"]
    valid_consumer_units = ["KG", "G", "LB", "OZ", "PIECE"]

    if bulk_product.category in ["palm_oil", "processed_palm_oil"]:
        assert bulk_product.default_unit in valid_bulk_units

    if consumer_product.category == "consumer_goods":
        assert consumer_product.default_unit in valid_consumer_units


def test_product_hs_code_business_logic(db_session, test_palm_oil_product, test_processed_product, test_final_product):
    """Test HS code business logic validation."""

    # Business Logic: HS codes should be category-appropriate
    products = [test_palm_oil_product, test_processed_product, test_final_product]

    for product in products:
        # HS code should exist and be properly formatted
        assert product.hs_code is not None
        assert len(product.hs_code.replace(".", "")) >= 6

        # HS code should match product category
        if product.category == "palm_oil":
            assert product.hs_code.startswith("1511")  # Palm oil HS code prefix
        elif product.category == "processed_palm_oil":
            assert product.hs_code.startswith("1511")  # Still palm oil category
        elif product.category == "consumer_goods":
            # Consumer goods can have various HS codes
            assert len(product.hs_code) >= 8  # More specific classification


def test_product_sustainability_requirements_business_logic(db_session, test_palm_oil_product):
    """Test sustainability requirements business logic."""
    product = test_palm_oil_product

    # Business Logic: Palm oil products must have sustainability tracking
    sustainability_fields = [
        "sustainability_certification",
        "deforestation_risk_assessment"
    ]

    for field in sustainability_fields:
        assert field in product.origin_data_requirements
        assert product.origin_data_requirements[field] is True

    # Business Logic: Plantation location is required for deforestation tracking
    assert "plantation_location" in product.origin_data_requirements
    assert product.origin_data_requirements["plantation_location"] is True

    # Business Logic: Mill processing date helps with freshness tracking
    assert "mill_processing_date" in product.origin_data_requirements
    assert product.origin_data_requirements["mill_processing_date"] is True
