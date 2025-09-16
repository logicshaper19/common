"""
Tests for enhanced origin data capture and validation.
"""
import pytest
from decimal import Decimal
from datetime import date, timedelta
from uuid import uuid4
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from app.core.database import Base
from app.services.origin_data import OriginDataValidationService, PalmOilRegion, CertificationBody
from app.models.company import Company
from app.models.product import Product
from app.models.purchase_order import PurchaseOrder
from app.schemas.origin_data import (
    EnhancedGeographicCoordinates,
    EnhancedOriginDataCapture,
    FarmInformation,
    QualityParameters,
    ComplianceStatus
)

# Use PostgreSQL test configuration from conftest.py
# No need for custom database setup


@pytest.fixture
def sample_companies(db_session: Session):
    """Create sample companies for testing."""
    companies = {}
    
    # Create originator company
    companies["originator"] = Company(
        id=uuid4(),
        name="Palm Plantation Co",
        company_type="originator",
        email="plantation@example.com"
    )
    
    # Create processor company
    companies["processor"] = Company(
        id=uuid4(),
        name="Palm Processing Ltd",
        company_type="processor",
        email="processor@example.com"
    )
    
    for company in companies.values():
        db_session.add(company)
    
    db_session.commit()
    
    for company in companies.values():
        db_session.refresh(company)
    
    return companies


@pytest.fixture
def sample_products(db_session: Session):
    """Create sample products for testing."""
    products = {}
    
    # Fresh Fruit Bunches (raw material)
    products["ffb"] = Product(
        id=uuid4(),
        common_product_id="FFB-001",
        name="Fresh Fruit Bunches (FFB)",
        description="Fresh palm fruit bunches harvested from oil palm trees",
        category="raw_material",
        can_have_composition=False,
        material_breakdown=None,
        default_unit="KGM",
        hs_code="1207.10.00",
        origin_data_requirements={
            "required_fields": ["geographic_coordinates", "certifications"],
            "required_certifications": ["RSPO"],
            "quality_parameters": {
                "oil_content_percentage": {"min": 18, "max": 26},
                "moisture_content_percentage": {"max": 25}
            }
        }
    )
    
    for product in products.values():
        db_session.add(product)
    
    db_session.commit()
    
    for product in products.values():
        db_session.refresh(product)
    
    return products


class TestGeographicCoordinateValidation:
    """Test geographic coordinate validation."""
    
    def test_validate_coordinates_southeast_asia(self, db_session):
        """Test coordinate validation for Southeast Asia region."""
        origin_service = OriginDataValidationService(db_session)
        
        # Coordinates in Malaysia (Southeast Asia)
        coords = EnhancedGeographicCoordinates(
            latitude=2.5,
            longitude=101.5,
            accuracy_meters=10.0,
            elevation_meters=50.0
        )
        
        validation_result = origin_service._validate_geographic_coordinates(coords)
        
        assert validation_result["is_valid"]
        assert validation_result["detected_region"] == PalmOilRegion.SOUTHEAST_ASIA.value
        assert validation_result["accuracy_level"] == "very_good"
        assert len(validation_result["errors"]) == 0
        assert "Southeast Asia" in validation_result["suggestions"][0]
    
    def test_validate_coordinates_west_africa(self, db_session):
        """Test coordinate validation for West Africa region."""
        origin_service = OriginDataValidationService(db_session)
        
        # Coordinates in Nigeria (West Africa)
        coords = EnhancedGeographicCoordinates(
            latitude=6.5,
            longitude=3.4,
            accuracy_meters=25.0
        )
        
        validation_result = origin_service._validate_geographic_coordinates(coords)
        
        assert validation_result["is_valid"]
        assert validation_result["detected_region"] == PalmOilRegion.WEST_AFRICA.value
        assert validation_result["accuracy_level"] == "good"
        assert len(validation_result["errors"]) == 0
    
    def test_validate_coordinates_outside_palm_regions(self, db_session):
        """Test coordinate validation outside palm oil regions."""
        origin_service = OriginDataValidationService(db_session)
        
        # Coordinates in Europe (outside palm oil regions)
        coords = EnhancedGeographicCoordinates(
            latitude=52.5,
            longitude=13.4,
            accuracy_meters=5.0
        )
        
        validation_result = origin_service._validate_geographic_coordinates(coords)
        
        assert validation_result["is_valid"]  # Valid coordinates, but warning
        assert validation_result["detected_region"] is None
        assert validation_result["accuracy_level"] == "excellent"
        assert len(validation_result["warnings"]) > 0
        assert "outside known palm oil producing regions" in validation_result["warnings"][0]
    
    def test_validate_coordinates_poor_accuracy(self, db_session):
        """Test coordinate validation with poor GPS accuracy."""
        origin_service = OriginDataValidationService(db_session)
        
        # Coordinates with poor accuracy
        coords = EnhancedGeographicCoordinates(
            latitude=2.5,
            longitude=101.5,
            accuracy_meters=150.0
        )
        
        validation_result = origin_service._validate_geographic_coordinates(coords)
        
        assert validation_result["is_valid"]
        assert validation_result["accuracy_level"] == "very_low"
        assert len(validation_result["warnings"]) > 0
        assert "GPS accuracy is low" in validation_result["warnings"][0]


class TestCertificationValidation:
    """Test certification validation."""
    
    def test_validate_recognized_certifications(self, db_session, sample_products):
        """Test validation of recognized certifications."""
        origin_service = OriginDataValidationService(db_session)
        
        certifications = ["RSPO", "NDPE", "ISPO"]
        product = sample_products["ffb"]
        detected_region = PalmOilRegion.SOUTHEAST_ASIA
        
        validation_result = origin_service._validate_certifications_comprehensive(
            certifications, product, detected_region
        )
        
        assert validation_result["is_valid"]
        assert validation_result["recognized_certifications"] == certifications
        assert validation_result["unrecognized_certifications"] == []
        assert validation_result["quality_score"] == 1.0  # 3 high-value certs
        assert len(validation_result["errors"]) == 0
    
    def test_validate_unrecognized_certifications(self, db_session, sample_products):
        """Test validation with unrecognized certifications."""
        origin_service = OriginDataValidationService(db_session)
        
        certifications = ["RSPO", "CUSTOM_CERT", "UNKNOWN_STANDARD"]
        product = sample_products["ffb"]
        detected_region = PalmOilRegion.SOUTHEAST_ASIA
        
        validation_result = origin_service._validate_certifications_comprehensive(
            certifications, product, detected_region
        )
        
        assert validation_result["is_valid"]
        assert validation_result["recognized_certifications"] == ["RSPO"]
        assert set(validation_result["unrecognized_certifications"]) == {"CUSTOM_CERT", "UNKNOWN_STANDARD"}
        assert len(validation_result["warnings"]) == 2  # Two unrecognized certs
    
    def test_validate_missing_required_certifications(self, db_session, sample_products):
        """Test validation with missing required certifications."""
        origin_service = OriginDataValidationService(db_session)
        
        certifications = ["NDPE"]  # Missing RSPO which is required for product
        product = sample_products["ffb"]
        detected_region = PalmOilRegion.SOUTHEAST_ASIA
        
        validation_result = origin_service._validate_certifications_comprehensive(
            certifications, product, detected_region
        )
        
        assert not validation_result["is_valid"]
        assert len(validation_result["errors"]) > 0
        assert any("RSPO" in error for error in validation_result["errors"])
    
    def test_validate_no_certifications(self, db_session, sample_products):
        """Test validation with no certifications."""
        origin_service = OriginDataValidationService(db_session)
        
        certifications = []
        product = sample_products["ffb"]
        detected_region = PalmOilRegion.SOUTHEAST_ASIA
        
        validation_result = origin_service._validate_certifications_comprehensive(
            certifications, product, detected_region
        )
        
        assert not validation_result["is_valid"]  # Required certifications missing
        assert validation_result["quality_score"] == 0.0
        assert len(validation_result["suggestions"]) > 0


class TestHarvestDateValidation:
    """Test harvest date validation."""
    
    def test_validate_fresh_harvest_date(self, db_session, sample_products):
        """Test validation of fresh harvest date."""
        origin_service = OriginDataValidationService(db_session)
        
        harvest_date = date.today() - timedelta(days=7)  # 1 week old
        product = sample_products["ffb"]
        
        validation_result = origin_service._validate_harvest_date_comprehensive(
            harvest_date, product
        )
        
        assert validation_result["is_valid"]
        assert validation_result["days_old"] == 7
        assert validation_result["freshness_level"] == "very_fresh"
        assert len(validation_result["errors"]) == 0
        assert "Fresh harvest" in validation_result["suggestions"][0]
    
    def test_validate_old_harvest_date(self, db_session, sample_products):
        """Test validation of old harvest date."""
        origin_service = OriginDataValidationService(db_session)
        
        harvest_date = date.today() - timedelta(days=400)  # Over 1 year old
        product = sample_products["ffb"]
        
        validation_result = origin_service._validate_harvest_date_comprehensive(
            harvest_date, product
        )
        
        assert validation_result["is_valid"]
        assert validation_result["days_old"] == 400
        assert validation_result["freshness_level"] == "very_old"
        assert len(validation_result["warnings"]) > 0
        assert "more than 1 year old" in validation_result["warnings"][0]
    
    def test_validate_future_harvest_date(self, db_session, sample_products):
        """Test validation of future harvest date."""
        origin_service = OriginDataValidationService(db_session)
        
        harvest_date = date.today() + timedelta(days=1)  # Future date
        product = sample_products["ffb"]
        
        validation_result = origin_service._validate_harvest_date_comprehensive(
            harvest_date, product
        )
        
        assert not validation_result["is_valid"]
        assert len(validation_result["errors"]) > 0
        assert "cannot be in the future" in validation_result["errors"][0]


class TestComprehensiveOriginDataValidation:
    """Test comprehensive origin data validation."""
    
    def test_validate_excellent_origin_data(self, db_session, sample_companies, sample_products):
        """Test validation of excellent quality origin data."""
        origin_service = OriginDataValidationService(db_session)
        
        # Create excellent origin data
        origin_data = EnhancedOriginDataCapture(
            geographic_coordinates=EnhancedGeographicCoordinates(
                latitude=2.5,
                longitude=101.5,
                accuracy_meters=5.0,
                elevation_meters=50.0
            ),
            certifications=["RSPO", "NDPE", "ISPO", "Rainforest Alliance"],
            harvest_date=date.today() - timedelta(days=7),
            farm_information=FarmInformation(
                farm_id="FARM-PREMIUM-001",
                farm_name="Premium Palm Plantation",
                farm_size_hectares=500.0,
                owner_name="John Doe",
                established_year=2010
            ),
            batch_number="BATCH-2025-001",
            quality_parameters=QualityParameters(
                oil_content_percentage=22.5,
                moisture_content_percentage=18.0,
                free_fatty_acid_percentage=2.1
            )
        )
        
        validation_result = origin_service.validate_comprehensive_origin_data(
            origin_data,
            sample_products["ffb"].id
        )
        
        assert validation_result.is_valid
        assert validation_result.quality_score >= 0.8
        assert validation_result.compliance_status in ["fully_compliant", "substantially_compliant"]
        assert len(validation_result.errors) == 0
        assert validation_result.coordinate_validation["detected_region"] == PalmOilRegion.SOUTHEAST_ASIA.value
    
    def test_validate_poor_origin_data(self, db_session, sample_companies, sample_products):
        """Test validation of poor quality origin data."""
        origin_service = OriginDataValidationService(db_session)
        
        # Create poor quality origin data
        origin_data = EnhancedOriginDataCapture(
            geographic_coordinates=EnhancedGeographicCoordinates(
                latitude=52.5,  # Outside palm oil regions
                longitude=13.4,
                accuracy_meters=200.0  # Poor accuracy
            ),
            certifications=[],  # No certifications
            harvest_date=date.today() - timedelta(days=500)  # Very old
        )
        
        validation_result = origin_service.validate_comprehensive_origin_data(
            origin_data,
            sample_products["ffb"].id
        )
        
        assert not validation_result.is_valid  # Missing required certifications
        assert validation_result.quality_score < 0.5
        assert validation_result.compliance_status == "non_compliant"
        assert len(validation_result.errors) > 0
        assert len(validation_result.warnings) > 0
    
    def test_validate_minimal_compliant_origin_data(self, db_session, sample_companies, sample_products):
        """Test validation of minimally compliant origin data."""
        origin_service = OriginDataValidationService(db_session)
        
        # Create minimally compliant origin data
        origin_data = EnhancedOriginDataCapture(
            geographic_coordinates=EnhancedGeographicCoordinates(
                latitude=2.5,
                longitude=101.5,
                accuracy_meters=50.0
            ),
            certifications=["RSPO"],  # Only required certification
            harvest_date=date.today() - timedelta(days=90)
        )
        
        validation_result = origin_service.validate_comprehensive_origin_data(
            origin_data,
            sample_products["ffb"].id
        )
        
        assert validation_result.is_valid
        assert 0.4 <= validation_result.quality_score <= 1.0
        assert validation_result.compliance_status in ["substantially_compliant", "partially_compliant", "minimally_compliant"]
        assert len(validation_result.errors) == 0
        assert len(validation_result.suggestions) > 0  # Should suggest improvements
