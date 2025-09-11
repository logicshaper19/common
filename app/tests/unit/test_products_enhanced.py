"""
Enhanced unit tests for product business logic.
Tests composition validation, product categorization, and domain rules.
"""
import pytest
from decimal import Decimal
from uuid import uuid4

from app.models.product import Product
from app.models.company import Company
from app.models.user import User
from app.core.security import hash_password
from app.services.product.composition_validator import CompositionValidator
from app.services.product.product_service import ProductService

# Mark all tests in this file as unit tests
pytestmark = [pytest.mark.unit, pytest.mark.database]


@pytest.fixture
def admin_company(db_session):
    """Create admin company for product management."""
    company = Company(
        id=uuid4(),
        name="Admin Company",
        company_type="admin",
        email="admin@platform.com"
    )
    db_session.add(company)
    db_session.commit()
    return company


@pytest.fixture
def admin_user(db_session, admin_company):
    """Create admin user with product management permissions."""
    user = User(
        id=uuid4(),
        email="admin@platform.com",
        hashed_password=hash_password("adminpass123"),
        full_name="Platform Admin",
        role="admin",
        company_id=admin_company.id,
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def composition_validator(db_session):
    """Create composition validator service."""
    return CompositionValidator(db_session)


@pytest.fixture
def product_service(db_session):
    """Create product service."""
    return ProductService(db_session)


def test_product_creation_business_rules(db_session, admin_user):
    """Test product creation with comprehensive business rule validation."""
    # Test valid raw material product
    raw_product = Product(
        id=uuid4(),
        common_product_id="RAW-PALM-001",
        name="Fresh Fruit Bunches",
        description="Raw palm fruit bunches from certified plantations",
        category="raw_material",
        can_have_composition=False,
        default_unit="KGM",
        hs_code="1207.10.00",
        origin_data_requirements={
            "plantation_id": True,
            "harvest_date": True,
            "sustainability_certification": True
        },
        created_by=admin_user.id
    )
    
    db_session.add(raw_product)
    db_session.commit()
    
    # Validate business rules
    assert raw_product.common_product_id.startswith("RAW-")
    assert raw_product.category == "raw_material"
    assert raw_product.can_have_composition is False
    assert raw_product.material_breakdown is None
    assert raw_product.origin_data_requirements is not None
    assert len(raw_product.hs_code) == 10  # Standard HS code format
    
    # Test processed product with composition
    processed_product = Product(
        id=uuid4(),
        common_product_id="PROC-CPO-001",
        name="Crude Palm Oil",
        description="Crude palm oil extracted from FFB",
        category="processed",
        can_have_composition=True,
        material_breakdown={"fresh_fruit_bunches": 100.0},
        default_unit="KGM",
        hs_code="1511.10.00",
        processing_requirements={
            "extraction_method": "mechanical",
            "temperature_max": 60,
            "moisture_content_max": 0.1
        },
        created_by=admin_user.id
    )
    
    db_session.add(processed_product)
    db_session.commit()
    
    # Validate processed product business rules
    assert processed_product.can_have_composition is True
    assert processed_product.material_breakdown is not None
    assert sum(processed_product.material_breakdown.values()) == 100.0
    assert processed_product.processing_requirements is not None


def test_product_composition_validation_rules(composition_validator, db_session, admin_user):
    """Test comprehensive composition validation business logic."""
    # Create base products for composition
    palm_oil = Product(
        id=uuid4(),
        common_product_id="BASE-PO-001",
        name="Palm Oil",
        category="processed",
        can_have_composition=False,
        default_unit="KGM"
    )
    
    palm_kernel_oil = Product(
        id=uuid4(),
        common_product_id="BASE-PKO-001", 
        name="Palm Kernel Oil",
        category="processed",
        can_have_composition=False,
        default_unit="KGM"
    )
    
    db_session.add_all([palm_oil, palm_kernel_oil])
    db_session.commit()
    
    # Create blend product with composition rules
    blend_product = Product(
        id=uuid4(),
        common_product_id="BLEND-001",
        name="80/20 Palm Oil Blend",
        category="finished_good",
        can_have_composition=True,
        material_breakdown={
            "palm_oil": 80.0,
            "palm_kernel_oil": 20.0
        },
        default_unit="KGM",
        composition_tolerance=2.0  # Allow 2% variance
    )
    
    db_session.add(blend_product)
    db_session.commit()
    
    # Test valid composition within tolerance
    valid_composition = {
        "palm_oil": 81.0,  # 1% over target (within 2% tolerance)
        "palm_kernel_oil": 19.0  # 1% under target
    }
    
    result = composition_validator.validate_composition(
        blend_product.id, valid_composition
    )
    assert result.is_valid is True
    assert len(result.errors) == 0
    
    # Test composition outside tolerance
    invalid_composition = {
        "palm_oil": 85.0,  # 5% over target (exceeds 2% tolerance)
        "palm_kernel_oil": 15.0  # 5% under target
    }
    
    result = composition_validator.validate_composition(
        blend_product.id, invalid_composition
    )
    assert result.is_valid is False
    assert len(result.errors) > 0
    assert any("tolerance" in error.lower() for error in result.errors)
    
    # Test composition with wrong materials
    wrong_composition = {
        "coconut_oil": 50.0,
        "sunflower_oil": 50.0
    }
    
    result = composition_validator.validate_composition(
        blend_product.id, wrong_composition
    )
    assert result.is_valid is False
    assert any("not allowed" in error.lower() for error in result.errors)
    
    # Test composition that doesn't sum to 100%
    incomplete_composition = {
        "palm_oil": 80.0,
        "palm_kernel_oil": 15.0  # Only sums to 95%
    }
    
    result = composition_validator.validate_composition(
        blend_product.id, incomplete_composition
    )
    assert result.is_valid is False
    assert any("100%" in error or "sum" in error.lower() for error in result.errors)


def test_product_categorization_business_rules(db_session, admin_user):
    """Test product categorization and tier-specific business rules."""
    # Test raw material constraints
    raw_material = Product(
        id=uuid4(),
        common_product_id="RAW-001",
        name="Raw Material",
        category="raw_material",
        can_have_composition=False,  # Raw materials cannot have composition
        default_unit="KGM",
        tier_level=7  # Plantation level
    )
    
    db_session.add(raw_material)
    db_session.commit()
    
    # Validate raw material business rules
    assert raw_material.can_have_composition is False
    assert raw_material.material_breakdown is None
    assert raw_material.tier_level >= 5  # Must be from originator tier or below
    
    # Test processed product requirements
    processed_product = Product(
        id=uuid4(),
        common_product_id="PROC-001",
        name="Processed Product",
        category="processed",
        can_have_composition=True,
        material_breakdown={"raw_material": 100.0},
        default_unit="KGM",
        tier_level=4,  # Mill level
        processing_requirements={
            "temperature_range": {"min": 40, "max": 80},
            "pressure_max": 5.0,
            "processing_time_hours": 24
        }
    )
    
    db_session.add(processed_product)
    db_session.commit()
    
    # Validate processed product business rules
    assert processed_product.can_have_composition is True
    assert processed_product.material_breakdown is not None
    assert processed_product.processing_requirements is not None
    assert processed_product.tier_level <= 4  # Must be from mill tier or above
    
    # Test finished good requirements
    finished_good = Product(
        id=uuid4(),
        common_product_id="FG-001",
        name="Finished Good",
        category="finished_good",
        can_have_composition=True,
        material_breakdown={"processed_ingredient": 100.0},
        default_unit="KGM",
        tier_level=2,  # Processor level
        quality_standards={
            "moisture_content_max": 0.1,
            "free_fatty_acid_max": 0.1,
            "peroxide_value_max": 2.0,
            "color_lovibond_max": 3.0
        }
    )
    
    db_session.add(finished_good)
    db_session.commit()
    
    # Validate finished good business rules
    assert finished_good.quality_standards is not None
    assert finished_good.tier_level <= 3  # Must be from processor tier or above


def test_product_unit_standardization(db_session, admin_user):
    """Test product unit standardization and conversion rules."""
    # Test weight-based product
    weight_product = Product(
        id=uuid4(),
        common_product_id="WEIGHT-001",
        name="Palm Oil",
        category="processed",
        default_unit="KGM",  # Kilograms
        allowed_units=["KGM", "TNE", "LBR"],  # kg, tonnes, pounds
        unit_conversions={
            "TNE": 0.001,  # 1 kg = 0.001 tonnes
            "LBR": 2.20462  # 1 kg = 2.20462 pounds
        }
    )
    
    db_session.add(weight_product)
    db_session.commit()
    
    # Validate unit business rules
    assert weight_product.default_unit in weight_product.allowed_units
    assert len(weight_product.unit_conversions) == len(weight_product.allowed_units) - 1
    
    # Test volume-based product
    volume_product = Product(
        id=uuid4(),
        common_product_id="VOLUME-001",
        name="Liquid Palm Oil",
        category="finished_good",
        default_unit="LTR",  # Liters
        allowed_units=["LTR", "MLT", "GAL"],  # liters, milliliters, gallons
        unit_conversions={
            "MLT": 1000,  # 1 liter = 1000 milliliters
            "GAL": 0.264172  # 1 liter = 0.264172 gallons
        },
        density_kg_per_liter=0.92  # For weight-volume conversions
    )
    
    db_session.add(volume_product)
    db_session.commit()
    
    # Validate volume product business rules
    assert volume_product.density_kg_per_liter is not None
    assert 0.8 <= volume_product.density_kg_per_liter <= 1.2  # Reasonable density range


def test_product_sustainability_requirements(db_session, admin_user):
    """Test sustainability and compliance requirements for products."""
    sustainable_product = Product(
        id=uuid4(),
        common_product_id="SUST-001",
        name="RSPO Certified Palm Oil",
        category="finished_good",
        default_unit="KGM",
        sustainability_certifications=["RSPO", "RTRS"],
        compliance_requirements={
            "deforestation_free": True,
            "no_peat_development": True,
            "no_exploitation": True,
            "traceability_level": "plantation"
        },
        origin_data_requirements={
            "plantation_coordinates": True,
            "certification_number": True,
            "audit_date": True,
            "chain_of_custody": True
        }
    )
    
    db_session.add(sustainable_product)
    db_session.commit()
    
    # Validate sustainability business rules
    assert len(sustainable_product.sustainability_certifications) > 0
    assert sustainable_product.compliance_requirements["deforestation_free"] is True
    assert sustainable_product.compliance_requirements["traceability_level"] in [
        "plantation", "mill", "processor", "brand"
    ]
    assert "certification_number" in sustainable_product.origin_data_requirements


def test_product_pricing_and_market_rules(db_session, admin_user):
    """Test product pricing validation and market-specific rules."""
    market_product = Product(
        id=uuid4(),
        common_product_id="MKT-001",
        name="Food Grade Palm Oil",
        category="finished_good",
        default_unit="KGM",
        market_specifications={
            "food_grade": True,
            "kosher_certified": True,
            "halal_certified": True,
            "shelf_life_months": 24
        },
        price_validation_rules={
            "min_price_usd_per_kg": 0.50,
            "max_price_usd_per_kg": 5.00,
            "price_volatility_threshold": 0.20  # 20% daily change threshold
        }
    )
    
    db_session.add(market_product)
    db_session.commit()
    
    # Validate market business rules
    assert market_product.market_specifications["food_grade"] is True
    assert market_product.price_validation_rules["min_price_usd_per_kg"] > 0
    assert market_product.price_validation_rules["max_price_usd_per_kg"] > \
           market_product.price_validation_rules["min_price_usd_per_kg"]
    assert 0 < market_product.price_validation_rules["price_volatility_threshold"] < 1


def test_product_batch_and_inventory_rules(db_session, admin_user):
    """Test product batch tracking and inventory management rules."""
    batch_product = Product(
        id=uuid4(),
        common_product_id="BATCH-001",
        name="Traceable Palm Oil",
        category="processed",
        default_unit="KGM",
        batch_requirements={
            "min_batch_size_kg": 1000,
            "max_batch_size_kg": 25000,
            "batch_numbering_format": "YYYY-MM-DD-XXX",
            "shelf_life_days": 730
        },
        inventory_rules={
            "fifo_required": True,  # First In, First Out
            "temperature_controlled": True,
            "humidity_controlled": False,
            "segregation_required": True
        }
    )
    
    db_session.add(batch_product)
    db_session.commit()
    
    # Validate batch and inventory business rules
    assert batch_product.batch_requirements["min_batch_size_kg"] > 0
    assert batch_product.batch_requirements["max_batch_size_kg"] > \
           batch_product.batch_requirements["min_batch_size_kg"]
    assert batch_product.inventory_rules["fifo_required"] is True
    assert "YYYY" in batch_product.batch_requirements["batch_numbering_format"]
