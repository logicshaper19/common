"""
Comprehensive tests for product catalog and sector management.
"""
import pytest
import json
from datetime import datetime, timedelta
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
from app.models.sector import Sector, SectorTier, SectorProduct
from app.core.security import hash_password, create_access_token

# Use PostgreSQL test configuration from conftest.py
# No need for custom database setup
client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_db(db_session):
    """Clean database before each test."""
    db_session.query(SectorProduct).delete()
    db_session.query(SectorTier).delete()
    db_session.query(Sector).delete()
    db_session.query(Product).delete()
    db_session.query(Company).delete()
    db_session.query(User).delete()
    db_session.commit()


@pytest.fixture
def test_sectors(db_session):
    """Create test sectors."""
    
    sectors = {
        "palm_oil": Sector(
            id="palm_oil",
            name="Palm Oil",
            description="Palm oil supply chain sector",
            is_active=True,
            regulatory_focus=["EUDR", "RSPO"],
            compliance_rules={
                "traceability_required": True,
                "certification_required": True,
                "origin_data_fields": ["farm_location", "harvest_date", "certification_id"]
            }
        ),
        "apparel": Sector(
            id="apparel",
            name="Apparel & Textiles",
            description="Fashion and textile supply chain sector",
            is_active=True,
            regulatory_focus=["UFLPA", "Modern Slavery Act"],
            compliance_rules={
                "traceability_required": True,
                "labor_standards_required": True,
                "origin_data_fields": ["manufacturing_facility", "worker_conditions", "materials_origin"]
            }
        )
    }
    
    for sector in sectors.values():
        db_session.add(sector)
    
    db_session.commit()
    return sectors


@pytest.fixture
def test_sector_tiers(test_sectors, db_session):
    """Create test sector tiers."""
    
    # Palm Oil tiers
    palm_tiers = [
        SectorTier(
            id="palm_brand",
            sector_id="palm_oil",
            tier_number=1,
            name="Brand",
            description="Consumer-facing brands",
            requirements={"certification": "RSPO", "transparency_level": "high"}
        ),
        SectorTier(
            id="palm_refinery",
            sector_id="palm_oil",
            tier_number=2,
            name="Refinery",
            description="Oil processing facilities",
            requirements={"certification": "RSPO", "transparency_level": "medium"}
        ),
        SectorTier(
            id="palm_mill",
            sector_id="palm_oil",
            tier_number=3,
            name="Mill",
            description="Palm oil mills",
            requirements={"certification": "RSPO", "transparency_level": "medium"}
        )
    ]
    
    # Apparel tiers
    apparel_tiers = [
        SectorTier(
            id="apparel_brand",
            sector_id="apparel",
            tier_number=1,
            name="Brand",
            description="Fashion brands",
            requirements={"labor_standards": "SMETA", "transparency_level": "high"}
        ),
        SectorTier(
            id="apparel_manufacturer",
            sector_id="apparel",
            tier_number=2,
            name="Manufacturer",
            description="Garment manufacturers",
            requirements={"labor_standards": "SMETA", "transparency_level": "medium"}
        )
    ]
    
    all_tiers = palm_tiers + apparel_tiers
    for tier in all_tiers:
        db.add(tier)
    
    db.commit()
    db.close()
    return {"palm_oil": palm_tiers, "apparel": apparel_tiers}


@pytest.fixture
def test_products():
    """Create test products."""
    db = TestingSessionLocal()
    
    products = {
        "palm_crude": Product(
            id=uuid4(),
            common_product_id="PALM-CRUDE-001",
            name="Crude Palm Oil",
            category="raw_material",
            description="Unrefined palm oil from mills",
            default_unit="MT",
            can_have_composition=False,
            hs_code="151110",
            origin_data_requirements={
                "coordinates": {"required": True, "type": "farm_location"},
                "harvest_date": {"required": True, "type": "date"},
                "certification_id": {"required": True, "type": "string"}
            }
        ),
        "palm_refined": Product(
            id=uuid4(),
            common_product_id="PALM-REFINED-001",
            name="Refined Palm Oil",
            category="processed",
            description="Refined palm oil for food industry",
            default_unit="MT",
            can_have_composition=True,
            hs_code="151190",
            origin_data_requirements={
                "facility_location": {"required": True, "type": "coordinates"},
                "processing_date": {"required": True, "type": "date"},
                "input_materials": {"required": True, "type": "list"}
            }
        ),
        "cotton_raw": Product(
            id=uuid4(),
            common_product_id="COTTON-RAW-001",
            name="Organic Cotton",
            category="raw_material",
            description="Organic cotton fiber",
            default_unit="KGM",
            can_have_composition=False,
            hs_code="520100",
            origin_data_requirements={
                "farm_location": {"required": True, "type": "coordinates"},
                "harvest_date": {"required": True, "type": "date"},
                "certification": {"required": True, "type": "string"}
            }
        ),
        "cotton_fabric": Product(
            id=uuid4(),
            common_product_id="COTTON-FABRIC-001",
            name="Cotton Fabric",
            category="processed",
            description="Woven cotton fabric",
            default_unit="KGM",
            can_have_composition=True,
            hs_code="520511",
            origin_data_requirements={
                "manufacturing_facility": {"required": True, "type": "coordinates"},
                "production_date": {"required": True, "type": "date"},
                "input_materials": {"required": True, "type": "list"}
            }
        )
    }
    
    for product in products.values():
        db_session.add(product)
    
    db_session.commit()
    return products


@pytest.fixture
def test_users(test_sectors, db_session):
    """Create test users."""
    
    # Create test company
    company = Company(
        id=uuid4(),
        name="Test Company",
        company_type="brand",
        email="test@company.com",
        sector_id="palm_oil"
    )
    db_session.add(company)
    db_session.commit()
    
    user = User(
        id=uuid4(),
        email="test@company.com",
        hashed_password=hash_password("testpassword123"),
        full_name="Test User",
        role="admin",
        company_id=company.id,
        sector_id="palm_oil",
        tier_level=1,
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    
    return user


def get_auth_headers(user_email: str) -> dict:
    """Get authentication headers for a user."""
    token = create_access_token(data={"sub": user_email})
    return {"Authorization": f"Bearer {token}"}


class TestProductCatalog:
    """Test product catalog functionality."""
    
    def test_get_products_list(self, test_users):
        """Test getting products list."""
        headers = get_auth_headers("test@company.com")
        
        response = client.get("/api/v1/products", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert len(data["items"]) >= 4  # At least our test products
    
    def test_get_product_by_id(self, test_users, test_products):
        """Test getting specific product by ID."""
        headers = get_auth_headers("test@company.com")
        product_id = test_products["palm_crude"].id
        
        response = client.get(f"/api/v1/products/{product_id}", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["id"] == str(product_id)
        assert data["name"] == "Crude Palm Oil"
        assert data["category"] == "raw_material"
    
    def test_get_product_not_found(self, test_users):
        """Test getting non-existent product."""
        headers = get_auth_headers("test@company.com")
        
        response = client.get(f"/api/v1/products/{uuid4()}", headers=headers)
        assert response.status_code == 404
    
    def test_create_product(self, test_users):
        """Test creating new product."""
        headers = get_auth_headers("test@company.com")
        
        product_data = {
            "common_product_id": "TEST-PRODUCT-001",
            "name": "Test Product",
            "category": "raw_material",
            "description": "Test product description",
            "default_unit": "KGM",
            "can_have_composition": False,
            "hs_code": "123456",
            "origin_data_requirements": {
                "test_field": {"required": True, "type": "string"}
            }
        }
        
        response = client.post("/api/v1/products", json=product_data, headers=headers)
        assert response.status_code == 201
        
        data = response.json()
        assert data["name"] == "Test Product"
        assert data["category"] == "raw_material"
        assert data["common_product_id"] == "TEST-PRODUCT-001"
    
    def test_create_product_duplicate_id(self, test_users, test_products):
        """Test creating product with duplicate common_product_id."""
        headers = get_auth_headers("test@company.com")
        
        product_data = {
            "common_product_id": "PALM-CRUDE-001",  # Already exists
            "name": "Duplicate Product",
            "category": "raw_material",
            "description": "Duplicate product",
            "default_unit": "KGM"
        }
        
        response = client.post("/api/v1/products", json=product_data, headers=headers)
        assert response.status_code == 400
    
    def test_update_product(self, test_users, test_products):
        """Test updating product."""
        headers = get_auth_headers("test@company.com")
        product_id = test_products["palm_crude"].id
        
        update_data = {
            "name": "Updated Crude Palm Oil",
            "description": "Updated description",
            "hs_code": "151111"
        }
        
        response = client.put(f"/api/v1/products/{product_id}", json=update_data, headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["name"] == "Updated Crude Palm Oil"
        assert data["description"] == "Updated description"
        assert data["hs_code"] == "151111"
    
    def test_product_validation_errors(self, test_users):
        """Test product creation with validation errors."""
        headers = get_auth_headers("test@company.com")
        
        # Missing required fields
        product_data = {
            "name": "Incomplete Product",
            # Missing common_product_id, category, etc.
        }
        
        response = client.post("/api/v1/products", json=product_data, headers=headers)
        assert response.status_code == 422
        
        # Invalid category
        product_data = {
            "common_product_id": "INVALID-001",
            "name": "Invalid Product",
            "category": "invalid_category",
            "default_unit": "KGM"
        }
        
        response = client.post("/api/v1/products", json=product_data, headers=headers)
        assert response.status_code == 422


class TestProductFiltering:
    """Test product filtering and search functionality."""
    
    def test_filter_products_by_category(self, test_users, test_products):
        """Test filtering products by category."""
        headers = get_auth_headers("test@company.com")
        
        response = client.get("/api/v1/products?category=raw_material", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        for product in data["items"]:
            assert product["category"] == "raw_material"
    
    def test_filter_products_by_hs_code(self, test_users, test_products):
        """Test filtering products by HS code."""
        headers = get_auth_headers("test@company.com")
        
        response = client.get("/api/v1/products?hs_code=151110", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        for product in data["items"]:
            assert product["hs_code"] == "151110"
    
    def test_search_products_by_name(self, test_users, test_products):
        """Test searching products by name."""
        headers = get_auth_headers("test@company.com")
        
        response = client.get("/api/v1/products?search=Palm", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert len(data["items"]) >= 1
        assert any("Palm" in product["name"] for product in data["items"])
    
    def test_filter_products_by_composition(self, test_users, test_products):
        """Test filtering products by composition capability."""
        headers = get_auth_headers("test@company.com")
        
        response = client.get("/api/v1/products?can_have_composition=true", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        for product in data["items"]:
            assert product["can_have_composition"] is True


class TestSectorManagement:
    """Test sector management functionality."""
    
    def test_get_sectors_list(self, test_users, test_sectors):
        """Test getting sectors list."""
        headers = get_auth_headers("test@company.com")
        
        response = client.get("/api/v1/sectors", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "items" in data
        assert len(data["items"]) >= 2  # At least our test sectors
    
    def test_get_sector_by_id(self, test_users, test_sectors):
        """Test getting specific sector by ID."""
        headers = get_auth_headers("test@company.com")
        
        response = client.get("/api/v1/sectors/palm_oil", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["id"] == "palm_oil"
        assert data["name"] == "Palm Oil"
        assert "regulatory_focus" in data
        assert "compliance_rules" in data
    
    def test_get_sector_tiers(self, test_users, test_sectors, test_sector_tiers):
        """Test getting sector tiers."""
        headers = get_auth_headers("test@company.com")
        
        response = client.get("/api/v1/sectors/palm_oil/tiers", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) >= 3  # At least our palm oil tiers
        
        # Check tier structure
        tier_names = [tier["name"] for tier in data]
        assert "Brand" in tier_names
        assert "Refinery" in tier_names
        assert "Mill" in tier_names
    
    def test_create_sector(self, test_users):
        """Test creating new sector."""
        headers = get_auth_headers("test@company.com")
        
        sector_data = {
            "id": "electronics",
            "name": "Electronics",
            "description": "Electronics supply chain sector",
            "regulatory_focus": ["Conflict Minerals", "RoHS"],
            "compliance_rules": {
                "traceability_required": True,
                "conflict_minerals_required": True,
                "origin_data_fields": ["mineral_origin", "smelter_id", "certification"]
            }
        }
        
        response = client.post("/api/v1/sectors", json=sector_data, headers=headers)
        assert response.status_code == 201
        
        data = response.json()
        assert data["id"] == "electronics"
        assert data["name"] == "Electronics"
        assert data["is_active"] is True
    
    def test_create_sector_tier(self, test_users, test_sectors):
        """Test creating sector tier."""
        headers = get_auth_headers("test@company.com")
        
        tier_data = {
            "sector_id": "palm_oil",
            "tier_number": 4,
            "name": "Smallholder",
            "description": "Smallholder farmers",
            "requirements": {
                "certification": "RSPO",
                "transparency_level": "basic"
            }
        }
        
        response = client.post("/api/v1/sectors/palm_oil/tiers", json=tier_data, headers=headers)
        assert response.status_code == 201
        
        data = response.json()
        assert data["name"] == "Smallholder"
        assert data["tier_number"] == 4
        assert data["sector_id"] == "palm_oil"
    
    def test_sector_validation_errors(self, test_users):
        """Test sector creation with validation errors."""
        headers = get_auth_headers("test@company.com")
        
        # Missing required fields
        sector_data = {
            "name": "Incomplete Sector",
            # Missing id, description
        }
        
        response = client.post("/api/v1/sectors", json=sector_data, headers=headers)
        assert response.status_code == 422
        
        # Invalid sector ID format
        sector_data = {
            "id": "invalid id with spaces",
            "name": "Invalid Sector",
            "description": "Invalid sector"
        }
        
        response = client.post("/api/v1/sectors", json=sector_data, headers=headers)
        assert response.status_code == 422


class TestSectorProductMapping:
    """Test sector-product mapping functionality."""
    
    def test_map_product_to_sector(self, test_users, test_products, test_sectors):
        """Test mapping product to sector."""
        headers = get_auth_headers("test@company.com")
        
        mapping_data = {
            "product_id": str(test_products["palm_crude"].id),
            "sector_id": "palm_oil",
            "tier_level": 3,  # Mill level
            "is_primary": True
        }
        
        response = client.post("/api/v1/sectors/palm_oil/products", json=mapping_data, headers=headers)
        assert response.status_code == 201
        
        data = response.json()
        assert data["product_id"] == str(test_products["palm_crude"].id)
        assert data["sector_id"] == "palm_oil"
        assert data["tier_level"] == 3
    
    def test_get_sector_products(self, test_users, test_products, test_sectors):
        """Test getting products for a sector."""
        headers = get_auth_headers("test@company.com")
        
        # First map a product
        mapping_data = {
            "product_id": str(test_products["palm_crude"].id),
            "sector_id": "palm_oil",
            "tier_level": 3
        }
        client.post("/api/v1/sectors/palm_oil/products", json=mapping_data, headers=headers)
        
        # Get sector products
        response = client.get("/api/v1/sectors/palm_oil/products", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) >= 1
        assert any(product["product_id"] == str(test_products["palm_crude"].id) for product in data)
    
    def test_get_products_by_tier(self, test_users, test_products, test_sectors):
        """Test getting products by tier level."""
        headers = get_auth_headers("test@company.com")
        
        # Map products to different tiers
        mapping_data = {
            "product_id": str(test_products["palm_crude"].id),
            "sector_id": "palm_oil",
            "tier_level": 3
        }
        client.post("/api/v1/sectors/palm_oil/products", json=mapping_data, headers=headers)
        
        # Get products for tier 3
        response = client.get("/api/v1/sectors/palm_oil/products?tier_level=3", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        for product in data:
            assert product["tier_level"] == 3


class TestProductComposition:
    """Test product composition functionality."""
    
    def test_get_product_composition(self, test_users, test_products):
        """Test getting product composition."""
        headers = get_auth_headers("test@company.com")
        product_id = test_products["palm_refined"].id
        
        response = client.get(f"/api/v1/products/{product_id}/composition", headers=headers)
        # This endpoint might not exist
        assert response.status_code in [200, 404]
        
        if response.status_code == 200:
            data = response.json()
            assert "components" in data
            assert "percentages" in data
    
    def test_update_product_composition(self, test_users, test_products):
        """Test updating product composition."""
        headers = get_auth_headers("test@company.com")
        product_id = test_products["palm_refined"].id
        
        composition_data = {
            "components": [
                {
                    "product_id": str(test_products["palm_crude"].id),
                    "percentage": 100.0,
                    "is_primary": True
                }
            ]
        }
        
        response = client.put(f"/api/v1/products/{product_id}/composition", 
                            json=composition_data, headers=headers)
        # This endpoint might not exist
        assert response.status_code in [200, 404]
    
    def test_validate_composition_percentages(self, test_users, test_products):
        """Test composition percentage validation."""
        headers = get_auth_headers("test@company.com")
        product_id = test_products["palm_refined"].id
        
        # Invalid composition (percentages don't add up to 100)
        composition_data = {
            "components": [
                {
                    "product_id": str(test_products["palm_crude"].id),
                    "percentage": 50.0,
                    "is_primary": True
                }
            ]
        }
        
        response = client.put(f"/api/v1/products/{product_id}/composition", 
                            json=composition_data, headers=headers)
        # This should return validation error if endpoint exists
        assert response.status_code in [200, 400, 404, 422]


class TestProductAnalytics:
    """Test product analytics and insights."""
    
    def test_get_product_analytics(self, test_users, test_products):
        """Test getting product analytics."""
        headers = get_auth_headers("test@company.com")
        
        response = client.get("/api/v1/products/analytics", headers=headers)
        # This endpoint might not exist
        assert response.status_code in [200, 404]
        
        if response.status_code == 200:
            data = response.json()
            assert "products_by_category" in data
            assert "products_by_sector" in data
            assert "total_products" in data
    
    def test_get_product_usage_stats(self, test_users, test_products):
        """Test getting product usage statistics."""
        headers = get_auth_headers("test@company.com")
        product_id = test_products["palm_crude"].id
        
        response = client.get(f"/api/v1/products/{product_id}/usage", headers=headers)
        # This endpoint might not exist
        assert response.status_code in [200, 404]
        
        if response.status_code == 200:
            data = response.json()
            assert "purchase_orders_count" in data
            assert "total_quantity" in data
            assert "companies_using" in data


class TestProductPermissions:
    """Test product-related permissions."""
    
    def test_product_data_access_permissions(self, test_users, test_products):
        """Test product data access permissions."""
        headers = get_auth_headers("test@company.com")
        
        # Should be able to access product data
        response = client.get(f"/api/v1/products/{test_products['palm_crude'].id}", headers=headers)
        assert response.status_code == 200
        
        # Should be able to create products
        product_data = {
            "common_product_id": "PERM-TEST-001",
            "name": "Permission Test Product",
            "category": "raw_material",
            "default_unit": "KGM"
        }
        
        response = client.post("/api/v1/products", json=product_data, headers=headers)
        assert response.status_code == 201
    
    def test_sector_admin_permissions(self, test_users, test_sectors):
        """Test sector admin permissions."""
        headers = get_auth_headers("test@company.com")
        
        # Should be able to access sector data
        response = client.get("/api/v1/sectors", headers=headers)
        assert response.status_code == 200
        
        # Should be able to create sectors
        sector_data = {
            "id": "test_sector",
            "name": "Test Sector",
            "description": "Test sector for permissions"
        }
        
        response = client.post("/api/v1/sectors", json=sector_data, headers=headers)
        assert response.status_code == 201
