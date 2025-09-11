"""
Tests for farm management API endpoints.
"""
import pytest
from uuid import uuid4
from datetime import datetime, date, timedelta
from decimal import Decimal
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import Base, get_db
from app.models.company import Company
from app.models.user import User
from app.models.product import Product
from app.models.location import Location
from app.models.batch import Batch
from app.models.batch_farm_contribution import BatchFarmContribution
from app.core.security import create_access_token

# Create test database
SQLALCHEMY_DATABASE_URL = "postgresql://postgres:password@localhost:5432/test_farm_api"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_pre_ping=True,
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


@pytest.fixture(autouse=True)
def clean_db():
    """Clean database before each test."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture
def client():
    """Get test client."""
    return TestClient(app)


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
def auth_headers(sample_user):
    """Get authentication headers for API requests."""
    token = create_access_token(data={"sub": sample_user.email})
    return {"Authorization": f"Bearer {token}"}


class TestFarmManagementAPI:
    """Test farm management API endpoints."""
    
    def test_get_company_capabilities_success(self, client, sample_company, sample_farm, auth_headers):
        """Test getting company capabilities successfully."""
        response = client.get(
            f"/farm-management/company/{sample_company.id}/capabilities",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["company_id"] == str(sample_company.id)
        assert data["has_farm_locations"] is True
        assert data["can_create_batches"] is True
        assert data["can_track_farm_contributions"] is True
        assert data["total_farms"] == 1
        assert data["farm_types"] == ["palm_plantation"]
        assert data["total_farm_area_hectares"] == 500.0
    
    def test_get_company_capabilities_company_not_found(self, client, auth_headers):
        """Test getting company capabilities for non-existent company."""
        fake_company_id = str(uuid4())
        response = client.get(
            f"/farm-management/company/{fake_company_id}/capabilities",
            headers=auth_headers
        )
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_get_company_farms_success(self, client, sample_company, sample_farm, auth_headers):
        """Test getting company farms successfully."""
        response = client.get(
            f"/farm-management/company/{sample_company.id}/farms",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["company_id"] == str(sample_company.id)
        assert data["total_farms"] == 1
        assert len(data["farms"]) == 1
        
        farm = data["farms"][0]
        assert farm["farm_id"] == str(sample_farm.id)
        assert farm["name"] == "Palm Plantation Alpha"
        assert farm["farm_type"] == "palm_plantation"
        assert farm["is_farm_location"] is True
        assert farm["compliance_status"] == "verified"
    
    def test_get_company_farms_company_not_found(self, client, auth_headers):
        """Test getting company farms for non-existent company."""
        fake_company_id = str(uuid4())
        response = client.get(
            f"/farm-management/company/{fake_company_id}/farms",
            headers=auth_headers
        )
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_create_batch_with_farm_contributions_success(self, client, sample_company, sample_user, sample_product, sample_farm, auth_headers):
        """Test creating batch with farm contributions successfully."""
        batch_request = {
            "batch_data": {
                "batch_id": "API-BATCH-001",
                "batch_type": "harvest",
                "product_id": str(sample_product.id),
                "quantity": 100.0,
                "unit": "MT",
                "production_date": date.today().isoformat(),
                "location_name": "Processing Facility Alpha"
            },
            "farm_contributions": [
                {
                    "location_id": str(sample_farm.id),
                    "quantity_contributed": 100.0,
                    "unit": "MT",
                    "contribution_percentage": 100.0,
                    "farm_data": {
                        "coordinates": {
                            "latitude": 3.1390,
                            "longitude": 101.6869
                        },
                        "certifications": sample_farm.certifications
                    },
                    "compliance_status": "verified"
                }
            ]
        }
        
        response = client.post(
            "/farm-management/batches",
            json=batch_request,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["batch_id"] is not None
        assert data["batch_number"] == "API-BATCH-001"
        assert data["total_quantity"] == 100.0
        assert data["farm_contributions"] == 1
        assert len(data["contributions"]) == 1
        assert data["contributions"][0]["farm_id"] == str(sample_farm.id)
        assert data["contributions"][0]["quantity_contributed"] == 100.0
        assert data["contributions"][0]["compliance_status"] == "verified"
    
    def test_create_batch_with_farm_contributions_validation_error(self, client, sample_company, sample_user, sample_product, sample_farm, auth_headers):
        """Test creating batch with invalid data."""
        batch_request = {
            "batch_data": {
                "batch_id": "API-BATCH-002",
                "batch_type": "harvest",
                "product_id": str(sample_product.id),
                "quantity": 100.0,
                "unit": "MT",
                "production_date": date.today().isoformat(),
                "location_name": "Processing Facility Alpha"
            },
            "farm_contributions": [
                {
                    "location_id": str(sample_farm.id),
                    "quantity_contributed": 80.0,  # Mismatch!
                    "unit": "MT",
                    "contribution_percentage": 80.0,
                    "farm_data": {},
                    "compliance_status": "verified"
                }
            ]
        }
        
        response = client.post(
            "/farm-management/batches",
            json=batch_request,
            headers=auth_headers
        )
        
        assert response.status_code == 400
        assert "does not match batch quantity" in response.json()["detail"]
    
    def test_get_batch_farm_traceability_success(self, client, sample_company, sample_user, sample_product, sample_farm, auth_headers, db_session):
        """Test getting batch farm traceability successfully."""
        # First create a batch with farm contributions
        batch = Batch(
            id=uuid4(),
            batch_id="TRACE-BATCH-001",
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
        
        # Test traceability endpoint
        response = client.get(
            f"/farm-management/batches/{batch.id}/traceability",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["batch_id"] == str(batch.id)
        assert data["batch_number"] == "TRACE-BATCH-001"
        assert data["total_quantity"] == 100.0
        assert data["farm_contributions"] == 1
        assert len(data["farms"]) == 1
        
        farm_info = data["farms"][0]
        assert farm_info["farm_id"] == str(sample_farm.id)
        assert farm_info["farm_name"] == "Palm Plantation Alpha"
        assert farm_info["quantity_contributed"] == 100.0
        assert farm_info["compliance_status"] == "verified"
        
        # Check regulatory compliance summary
        assert data["regulatory_compliance"]["eudr_ready"] is True
        assert data["regulatory_compliance"]["us_ready"] is True
        assert data["regulatory_compliance"]["total_farms"] == 1
        assert data["regulatory_compliance"]["verified_farms"] == 1
    
    def test_get_batch_farm_traceability_batch_not_found(self, client, auth_headers):
        """Test getting traceability for non-existent batch."""
        fake_batch_id = str(uuid4())
        response = client.get(
            f"/farm-management/batches/{fake_batch_id}/traceability",
            headers=auth_headers
        )
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_get_batch_compliance_status_success(self, client, sample_company, sample_user, sample_product, sample_farm, auth_headers, db_session):
        """Test getting batch compliance status successfully."""
        # First create a batch with farm contributions
        batch = Batch(
            id=uuid4(),
            batch_id="COMPLIANCE-BATCH-001",
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
        
        # Test compliance status endpoint
        response = client.get(
            f"/farm-management/batches/{batch.id}/compliance",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["batch_id"] == str(batch.id)
        assert data["batch_number"] == "COMPLIANCE-BATCH-001"
        assert "regulatory_compliance" in data
        assert len(data["farm_compliance_details"]) == 1
        
        farm_compliance = data["farm_compliance_details"][0]
        assert farm_compliance["farm_id"] == str(sample_farm.id)
        assert farm_compliance["farm_name"] == "Palm Plantation Alpha"
        assert farm_compliance["compliance_status"] == "verified"
        assert "coordinates" in farm_compliance
        assert "certifications" in farm_compliance
    
    def test_get_batch_compliance_status_batch_not_found(self, client, auth_headers):
        """Test getting compliance status for non-existent batch."""
        fake_batch_id = str(uuid4())
        response = client.get(
            f"/farm-management/batches/{fake_batch_id}/compliance",
            headers=auth_headers
        )
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_unauthorized_access(self, client, sample_company):
        """Test that endpoints require authentication."""
        # Test without auth headers
        response = client.get(f"/farm-management/company/{sample_company.id}/capabilities")
        assert response.status_code == 401
        
        response = client.get(f"/farm-management/company/{sample_company.id}/farms")
        assert response.status_code == 401
        
        response = client.post("/farm-management/batches", json={})
        assert response.status_code == 401
        
        fake_batch_id = str(uuid4())
        response = client.get(f"/farm-management/batches/{fake_batch_id}/traceability")
        assert response.status_code == 401
        
        response = client.get(f"/farm-management/batches/{fake_batch_id}/compliance")
        assert response.status_code == 401
