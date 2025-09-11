"""
Tests for farm management system and EUDR/US regulatory compliance.
"""
import pytest
from uuid import uuid4
from datetime import datetime, date, timedelta
from decimal import Decimal
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from app.core.database import Base
from app.services.farm_management import FarmManagementService
from app.services.farm_compliance import FarmComplianceService
from app.models.company import Company
from app.models.user import User
from app.models.product import Product
from app.models.location import Location
from app.models.batch import Batch
from app.models.batch_farm_contribution import BatchFarmContribution
from app.schemas.farm_management import (
    FarmContribution,
    BatchCreationRequest,
    FarmInfo
)

# Create test database
SQLALCHEMY_DATABASE_URL = "postgresql://postgres:password@localhost:5432/test_farm_management"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_pre_ping=True,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables
Base.metadata.create_all(bind=engine)


@pytest.fixture(autouse=True)
def clean_db():
    """Clean database before each test."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture
def db_session():
    """Get database session for testing."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def sample_company(db_session: Session):
    """Create sample company for testing."""
    company = Company(
        id=uuid4(),
        name="Palm Oil Cooperative",
        company_type="originator",
        email="coop@example.com",
        country="Malaysia"
    )
    
    db_session.add(company)
    db_session.commit()
    db_session.refresh(company)
    
    return company


@pytest.fixture
def sample_user(db_session: Session, sample_company):
    """Create sample user for testing."""
    user = User(
        id=uuid4(),
        email="user@example.com",
        hashed_password="hashed_password",
        full_name="Test User",
        role="user",
        company_id=sample_company.id
    )
    
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    
    return user


@pytest.fixture
def sample_product(db_session: Session, sample_company):
    """Create sample product for testing."""
    product = Product(
        id=uuid4(),
        name="Palm Oil",
        description="Sustainable palm oil",
        company_id=sample_company.id,
        unit="MT"
    )
    
    db_session.add(product)
    db_session.commit()
    db_session.refresh(product)
    
    return product


@pytest.fixture
def sample_farm(db_session: Session, sample_company, sample_user):
    """Create sample farm with EUDR compliance data."""
    farm = Location(
        id=uuid4(),
        name="Palm Plantation Alpha",
        location_type="farm",
        company_id=sample_company.id,
        is_farm_location=True,
        farm_type="palm_plantation",
        farm_size_hectares=Decimal("500.0"),
        latitude=Decimal("3.1390"),
        longitude=Decimal("101.6869"),
        accuracy_meters=Decimal("10.0"),
        country="Malaysia",
        established_year=2015,
        registration_number="FARM-001-2023",
        farm_owner_name="Ahmad Bin Hassan",
        specialization="sustainable_palm_oil",
        
        # EUDR Compliance Data
        deforestation_cutoff_date=date(2020, 12, 31),
        land_use_change_history={
            "2020-01-01": "forest",
            "2020-12-31": "plantation",
            "verification_date": "2023-01-15"
        },
        legal_land_tenure_docs={
            "land_title": "Title_001_2020.pdf",
            "lease_agreement": "Lease_001_2020.pdf",
            "verification_status": "verified"
        },
        due_diligence_statement={
            "statement_id": "DD-001-2023",
            "verification_date": "2023-01-15",
            "risk_level": "low"
        },
        risk_assessment_data={
            "deforestation_risk": "low",
            "assessment_date": "2023-01-15",
            "verification_source": "satellite_imagery"
        },
        compliance_status="verified",
        compliance_verification_date=datetime.utcnow(),
        compliance_verified_by_user_id=sample_user.id,
        
        # US Regulatory Compliance
        uflpa_compliance_data={
            "forced_labor_risk": "low",
            "assessment_date": "2023-01-15",
            "verification_status": "verified"
        },
        cbp_documentation={
            "document_id": "CBP-001-2023",
            "verification_date": "2023-01-15"
        },
        supply_chain_mapping={
            "suppliers": ["Supplier A", "Supplier B"],
            "verification_date": "2023-01-15"
        },
        us_risk_assessment={
            "overall_risk": "low",
            "assessment_date": "2023-01-15"
        },
        
        # Certifications
        certifications={
            "RSPO": {
                "certificate_number": "RSPO-001-2023",
                "valid_until": "2024-12-31",
                "status": "active"
            },
            "Organic": {
                "certificate_number": "ORG-001-2023",
                "valid_until": "2024-12-31",
                "status": "active"
            }
        },
        
        created_by_user_id=sample_user.id
    )
    
    db_session.add(farm)
    db_session.commit()
    db_session.refresh(farm)
    
    return farm


@pytest.fixture
def sample_farm_non_compliant(db_session: Session, sample_company, sample_user):
    """Create sample farm with missing compliance data."""
    farm = Location(
        id=uuid4(),
        name="Palm Plantation Beta",
        location_type="farm",
        company_id=sample_company.id,
        is_farm_location=True,
        farm_type="palm_plantation",
        farm_size_hectares=Decimal("300.0"),
        latitude=Decimal("3.1390"),
        longitude=Decimal("101.6869"),
        accuracy_meters=Decimal("50.0"),  # Lower accuracy
        country="Malaysia",
        compliance_status="pending",
        created_by_user_id=sample_user.id
    )
    
    db_session.add(farm)
    db_session.commit()
    db_session.refresh(farm)
    
    return farm


class TestFarmManagementService:
    """Test farm management service functionality."""
    
    def test_get_company_capabilities_with_farms(self, db_session: Session, sample_company, sample_farm):
        """Test getting company capabilities when company has farms."""
        service = FarmManagementService(db_session)
        
        capabilities = service.get_company_capabilities(sample_company.id)
        
        assert capabilities["company_id"] == str(sample_company.id)
        assert capabilities["has_farm_locations"] is True
        assert capabilities["can_create_batches"] is True
        assert capabilities["can_track_farm_contributions"] is True
        assert capabilities["total_farms"] == 1
        assert capabilities["farm_types"] == ["palm_plantation"]
        assert capabilities["total_farm_area_hectares"] == 500.0
    
    def test_get_company_capabilities_without_farms(self, db_session: Session, sample_company):
        """Test getting company capabilities when company has no farms."""
        service = FarmManagementService(db_session)
        
        capabilities = service.get_company_capabilities(sample_company.id)
        
        assert capabilities["company_id"] == str(sample_company.id)
        assert capabilities["has_farm_locations"] is False
        assert capabilities["can_create_batches"] is True  # Can still create batches
        assert capabilities["can_track_farm_contributions"] is False
        assert capabilities["total_farms"] == 0
        assert capabilities["farm_types"] == []
        assert capabilities["total_farm_area_hectares"] == 0.0
    
    def test_get_company_farms(self, db_session: Session, sample_company, sample_farm, sample_farm_non_compliant):
        """Test getting all farms for a company."""
        service = FarmManagementService(db_session)
        
        farms = service.get_company_farms(sample_company.id)
        
        assert len(farms) == 2
        farm_names = [farm["name"] for farm in farms]
        assert "Palm Plantation Alpha" in farm_names
        assert "Palm Plantation Beta" in farm_names
    
    def test_create_batch_with_farm_contributions(self, db_session: Session, sample_company, sample_user, sample_product, sample_farm):
        """Test creating a batch with farm contributions."""
        service = FarmManagementService(db_session)
        
        batch_data = {
            "batch_id": "BATCH-001-2023",
            "batch_type": "harvest",
            "product_id": str(sample_product.id),
            "quantity": 100.0,
            "unit": "MT",
            "production_date": date.today(),
            "location_name": "Processing Facility Alpha"
        }
        
        farm_contributions = [
            {
                "location_id": str(sample_farm.id),
                "quantity_contributed": 100.0,
                "unit": "MT",
                "contribution_percentage": 100.0,
                "farm_data": {
                    "coordinates": {
                        "latitude": float(sample_farm.latitude),
                        "longitude": float(sample_farm.longitude)
                    },
                    "certifications": sample_farm.certifications
                },
                "compliance_status": "verified"
            }
        ]
        
        result = service.create_batch_with_farm_contributions(
            batch_data=batch_data,
            farm_contributions=farm_contributions,
            company_id=sample_company.id,
            user_id=sample_user.id
        )
        
        assert result["batch_id"] is not None
        assert result["batch_number"] == "BATCH-001-2023"
        assert result["total_quantity"] == 100.0
        assert result["farm_contributions"] == 1
        assert len(result["contributions"]) == 1
        assert result["contributions"][0]["farm_id"] == str(sample_farm.id)
        assert result["contributions"][0]["quantity_contributed"] == 100.0
        assert result["contributions"][0]["compliance_status"] == "verified"
    
    def test_create_batch_with_multiple_farm_contributions(self, db_session: Session, sample_company, sample_user, sample_product, sample_farm, sample_farm_non_compliant):
        """Test creating a batch with multiple farm contributions."""
        service = FarmManagementService(db_session)
        
        batch_data = {
            "batch_id": "BATCH-002-2023",
            "batch_type": "harvest",
            "product_id": str(sample_product.id),
            "quantity": 200.0,
            "unit": "MT",
            "production_date": date.today(),
            "location_name": "Processing Facility Alpha"
        }
        
        farm_contributions = [
            {
                "location_id": str(sample_farm.id),
                "quantity_contributed": 120.0,
                "unit": "MT",
                "contribution_percentage": 60.0,
                "farm_data": {"coordinates": {"latitude": 3.1390, "longitude": 101.6869}},
                "compliance_status": "verified"
            },
            {
                "location_id": str(sample_farm_non_compliant.id),
                "quantity_contributed": 80.0,
                "unit": "MT",
                "contribution_percentage": 40.0,
                "farm_data": {"coordinates": {"latitude": 3.1390, "longitude": 101.6869}},
                "compliance_status": "pending"
            }
        ]
        
        result = service.create_batch_with_farm_contributions(
            batch_data=batch_data,
            farm_contributions=farm_contributions,
            company_id=sample_company.id,
            user_id=sample_user.id
        )
        
        assert result["batch_id"] is not None
        assert result["total_quantity"] == 200.0
        assert result["farm_contributions"] == 2
        assert len(result["contributions"]) == 2
        
        # Check individual contributions
        contrib_by_farm = {c["farm_id"]: c for c in result["contributions"]}
        assert contrib_by_farm[str(sample_farm.id)]["quantity_contributed"] == 120.0
        assert contrib_by_farm[str(sample_farm.id)]["contribution_percentage"] == 60.0
        assert contrib_by_farm[str(sample_farm_non_compliant.id)]["quantity_contributed"] == 80.0
        assert contrib_by_farm[str(sample_farm_non_compliant.id)]["contribution_percentage"] == 40.0
    
    def test_create_batch_quantity_mismatch_error(self, db_session: Session, sample_company, sample_user, sample_product, sample_farm):
        """Test error when farm contributions don't match batch quantity."""
        service = FarmManagementService(db_session)
        
        batch_data = {
            "batch_id": "BATCH-003-2023",
            "batch_type": "harvest",
            "product_id": str(sample_product.id),
            "quantity": 100.0,
            "unit": "MT",
            "production_date": date.today(),
            "location_name": "Processing Facility Alpha"
        }
        
        farm_contributions = [
            {
                "location_id": str(sample_farm.id),
                "quantity_contributed": 80.0,  # Mismatch!
                "unit": "MT",
                "contribution_percentage": 80.0,
                "farm_data": {},
                "compliance_status": "verified"
            }
        ]
        
        with pytest.raises(ValueError, match="Total farm contributions.*does not match batch quantity"):
            service.create_batch_with_farm_contributions(
                batch_data=batch_data,
                farm_contributions=farm_contributions,
                company_id=sample_company.id,
                user_id=sample_user.id
            )
    
    def test_get_batch_farm_traceability(self, db_session: Session, sample_company, sample_user, sample_product, sample_farm):
        """Test getting batch farm traceability information."""
        service = FarmManagementService(db_session)
        
        # First create a batch with farm contributions
        batch_data = {
            "batch_id": "BATCH-004-2023",
            "batch_type": "harvest",
            "product_id": str(sample_product.id),
            "quantity": 100.0,
            "unit": "MT",
            "production_date": date.today(),
            "location_name": "Processing Facility Alpha"
        }
        
        farm_contributions = [
            {
                "location_id": str(sample_farm.id),
                "quantity_contributed": 100.0,
                "unit": "MT",
                "contribution_percentage": 100.0,
                "farm_data": {"coordinates": {"latitude": 3.1390, "longitude": 101.6869}},
                "compliance_status": "verified"
            }
        ]
        
        batch_result = service.create_batch_with_farm_contributions(
            batch_data=batch_data,
            farm_contributions=farm_contributions,
            company_id=sample_company.id,
            user_id=sample_user.id
        )
        
        # Now test traceability
        traceability = service.get_batch_farm_traceability(batch_result["batch_id"])
        
        assert traceability["batch_id"] == batch_result["batch_id"]
        assert traceability["batch_number"] == "BATCH-004-2023"
        assert traceability["total_quantity"] == 100.0
        assert traceability["farm_contributions"] == 1
        assert len(traceability["farms"]) == 1
        
        farm_info = traceability["farms"][0]
        assert farm_info["farm_id"] == str(sample_farm.id)
        assert farm_info["farm_name"] == "Palm Plantation Alpha"
        assert farm_info["farm_type"] == "palm_plantation"
        assert farm_info["quantity_contributed"] == 100.0
        assert farm_info["contribution_percentage"] == 100.0
        assert farm_info["compliance_status"] == "verified"
        assert farm_info["coordinates"]["latitude"] == 3.1390
        assert farm_info["coordinates"]["longitude"] == 101.6869
        
        # Check regulatory compliance summary
        assert traceability["regulatory_compliance"]["eudr_ready"] is True
        assert traceability["regulatory_compliance"]["us_ready"] is True
        assert traceability["regulatory_compliance"]["total_farms"] == 1
        assert traceability["regulatory_compliance"]["verified_farms"] == 1
    
    def test_get_batch_farm_traceability_nonexistent_batch(self, db_session: Session):
        """Test error when getting traceability for non-existent batch."""
        service = FarmManagementService(db_session)
        
        with pytest.raises(ValueError, match="Batch.*not found"):
            service.get_batch_farm_traceability(uuid4())


class TestFarmComplianceService:
    """Test farm compliance verification service."""
    
    def test_verify_farm_eudr_compliance_complete(self, db_session: Session, sample_farm):
        """Test EUDR compliance verification for a complete farm."""
        service = FarmComplianceService(db_session)
        
        result = service.verify_farm_eudr_compliance(sample_farm.id)
        
        assert result["farm_id"] == str(sample_farm.id)
        assert result["farm_name"] == "Palm Plantation Alpha"
        assert result["eudr_compliance_status"] == "verified"
        assert result["overall_status"] == "verified"
        
        # Check individual EUDR checks
        eudr_checks = result["eudr_checks"]
        assert eudr_checks["geolocation_present"]["status"] == "pass"
        assert eudr_checks["deforestation_risk_low"]["status"] == "pass"
        assert eudr_checks["legal_docs_valid"]["status"] == "pass"
        assert eudr_checks["due_diligence_statement"]["status"] == "pass"
        assert eudr_checks["land_use_change_history"]["status"] == "pass"
    
    def test_verify_farm_eudr_compliance_incomplete(self, db_session: Session, sample_farm_non_compliant):
        """Test EUDR compliance verification for an incomplete farm."""
        service = FarmComplianceService(db_session)
        
        result = service.verify_farm_eudr_compliance(sample_farm_non_compliant.id)
        
        assert result["farm_id"] == str(sample_farm_non_compliant.id)
        assert result["eudr_compliance_status"] == "failed"
        assert result["overall_status"] == "failed"
        
        # Check individual EUDR checks (should fail)
        eudr_checks = result["eudr_checks"]
        assert eudr_checks["geolocation_present"]["status"] == "fail"  # Low accuracy
        assert eudr_checks["deforestation_risk_low"]["status"] == "fail"  # No risk data
        assert eudr_checks["legal_docs_valid"]["status"] == "fail"  # No legal docs
        assert eudr_checks["due_diligence_statement"]["status"] == "fail"  # No statement
        assert eudr_checks["land_use_change_history"]["status"] == "fail"  # No history
    
    def test_verify_farm_us_compliance_complete(self, db_session: Session, sample_farm):
        """Test US compliance verification for a complete farm."""
        service = FarmComplianceService(db_session)
        
        result = service.verify_farm_us_compliance(sample_farm.id)
        
        assert result["farm_id"] == str(sample_farm.id)
        assert result["farm_name"] == "Palm Plantation Alpha"
        assert result["us_compliance_status"] == "verified"
        assert result["overall_status"] == "verified"
        
        # Check individual US checks
        us_checks = result["us_checks"]
        assert us_checks["uflpa_compliance"]["status"] == "pass"
        assert us_checks["cbp_documentation"]["status"] == "pass"
        assert us_checks["supply_chain_mapping"]["status"] == "pass"
        assert us_checks["us_risk_assessment"]["status"] == "pass"
    
    def test_verify_farm_us_compliance_incomplete(self, db_session: Session, sample_farm_non_compliant):
        """Test US compliance verification for an incomplete farm."""
        service = FarmComplianceService(db_session)
        
        result = service.verify_farm_us_compliance(sample_farm_non_compliant.id)
        
        assert result["farm_id"] == str(sample_farm_non_compliant.id)
        assert result["us_compliance_status"] == "failed"
        assert result["overall_status"] == "failed"
        
        # Check individual US checks (should fail)
        us_checks = result["us_checks"]
        assert us_checks["uflpa_compliance"]["status"] == "fail"
        assert us_checks["cbp_documentation"]["status"] == "fail"
        assert us_checks["supply_chain_mapping"]["status"] == "fail"
        assert us_checks["us_risk_assessment"]["status"] == "fail"
    
    def test_get_farm_compliance_status(self, db_session: Session, sample_farm):
        """Test getting current compliance status for a farm."""
        service = FarmComplianceService(db_session)
        
        result = service.get_farm_compliance_status(sample_farm.id)
        
        assert result["farm_id"] == str(sample_farm.id)
        assert result["farm_name"] == "Palm Plantation Alpha"
        assert result["compliance_status"] == "verified"
        assert result["compliance_verification_date"] is not None
        assert result["exemption_reason"] is None
        
        # Check EUDR data
        assert result["eudr_data"]["deforestation_cutoff_date"] == "2020-12-31"
        assert result["eudr_data"]["land_use_change_history"] is not None
        assert result["eudr_data"]["legal_land_tenure_docs"] is not None
        assert result["eudr_data"]["due_diligence_statement"] is not None
        assert result["eudr_data"]["risk_assessment_data"] is not None
        
        # Check US data
        assert result["us_data"]["uflpa_compliance_data"] is not None
        assert result["us_data"]["cbp_documentation"] is not None
        assert result["us_data"]["supply_chain_mapping"] is not None
        assert result["us_data"]["us_risk_assessment"] is not None
    
    def test_verify_farm_compliance_nonexistent_farm(self, db_session: Session):
        """Test error when verifying compliance for non-existent farm."""
        service = FarmComplianceService(db_session)
        
        with pytest.raises(ValueError, match="Farm.*not found"):
            service.verify_farm_eudr_compliance(uuid4())
        
        with pytest.raises(ValueError, match="Farm.*not found"):
            service.verify_farm_us_compliance(uuid4())
        
        with pytest.raises(ValueError, match="Farm.*not found"):
            service.get_farm_compliance_status(uuid4())


class TestBatchFarmContributionModel:
    """Test batch farm contribution model functionality."""
    
    def test_batch_farm_contribution_creation(self, db_session: Session, sample_company, sample_user, sample_product, sample_farm):
        """Test creating batch farm contribution records."""
        # Create a batch first
        batch = Batch(
            id=uuid4(),
            batch_id="TEST-BATCH-001",
            batch_type="harvest",
            company_id=sample_company.id,
            product_id=sample_product.id,
            quantity=Decimal("100.0"),
            unit="MT",
            production_date=date.today(),
            created_by_user_id=sample_user.id
        )
        db_session.add(batch)
        db_session.commit()
        
        # Create farm contribution
        contribution = BatchFarmContribution(
            batch_id=batch.id,
            location_id=sample_farm.id,
            quantity_contributed=Decimal("100.0"),
            unit="MT",
            contribution_percentage=Decimal("100.0"),
            farm_data={
                "coordinates": {"latitude": 3.1390, "longitude": 101.6869},
                "certifications": sample_farm.certifications
            },
            compliance_status="verified"
        )
        
        db_session.add(contribution)
        db_session.commit()
        db_session.refresh(contribution)
        
        # Verify the contribution was created
        assert contribution.id is not None
        assert contribution.batch_id == batch.id
        assert contribution.location_id == sample_farm.id
        assert contribution.quantity_contributed == Decimal("100.0")
        assert contribution.contribution_percentage == Decimal("100.0")
        assert contribution.compliance_status == "verified"
        assert contribution.farm_data["coordinates"]["latitude"] == 3.1390
    
    def test_batch_farm_contribution_relationships(self, db_session: Session, sample_company, sample_user, sample_product, sample_farm):
        """Test batch farm contribution relationships."""
        # Create a batch first
        batch = Batch(
            id=uuid4(),
            batch_id="TEST-BATCH-002",
            batch_type="harvest",
            company_id=sample_company.id,
            product_id=sample_product.id,
            quantity=Decimal("100.0"),
            unit="MT",
            production_date=date.today(),
            created_by_user_id=sample_user.id
        )
        db_session.add(batch)
        db_session.commit()
        
        # Create farm contribution
        contribution = BatchFarmContribution(
            batch_id=batch.id,
            location_id=sample_farm.id,
            quantity_contributed=Decimal("100.0"),
            unit="MT",
            contribution_percentage=Decimal("100.0"),
            compliance_status="verified"
        )
        
        db_session.add(contribution)
        db_session.commit()
        db_session.refresh(contribution)
        
        # Test relationships
        assert contribution.batch.id == batch.id
        assert contribution.location.id == sample_farm.id
        assert contribution.batch.batch_id == "TEST-BATCH-002"
        assert contribution.location.name == "Palm Plantation Alpha"
    
    def test_batch_farm_contribution_unique_constraint(self, db_session: Session, sample_company, sample_user, sample_product, sample_farm):
        """Test that unique constraint prevents duplicate contributions."""
        # Create a batch first
        batch = Batch(
            id=uuid4(),
            batch_id="TEST-BATCH-003",
            batch_type="harvest",
            company_id=sample_company.id,
            product_id=sample_product.id,
            quantity=Decimal("100.0"),
            unit="MT",
            production_date=date.today(),
            created_by_user_id=sample_user.id
        )
        db_session.add(batch)
        db_session.commit()
        
        # Create first contribution
        contribution1 = BatchFarmContribution(
            batch_id=batch.id,
            location_id=sample_farm.id,
            quantity_contributed=Decimal("50.0"),
            unit="MT",
            contribution_percentage=Decimal("50.0"),
            compliance_status="verified"
        )
        db_session.add(contribution1)
        db_session.commit()
        
        # Try to create duplicate contribution
        contribution2 = BatchFarmContribution(
            batch_id=batch.id,
            location_id=sample_farm.id,  # Same farm
            quantity_contributed=Decimal("50.0"),
            unit="MT",
            contribution_percentage=Decimal("50.0"),
            compliance_status="verified"
        )
        db_session.add(contribution2)
        
        # Should raise integrity error
        with pytest.raises(Exception):  # SQLAlchemy will raise an integrity error
            db_session.commit()
