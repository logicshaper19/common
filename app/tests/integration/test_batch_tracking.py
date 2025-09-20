"""
Tests for batch tracking system.
"""
import pytest
from uuid import uuid4
from datetime import datetime, date, timedelta
from decimal import Decimal
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from app.core.database import Base
from app.services.batch import BatchTrackingService
from app.models.company import Company
from app.models.user import User
from app.models.product import Product
from app.models.batch import Batch, BatchTransaction, BatchRelationship
from app.models.purchase_order import PurchaseOrder
from app.schemas.batch import (
    BatchCreate,
    BatchUpdate,
    BatchTransactionCreate,
    BatchRelationshipCreate,
    BatchType,
    BatchStatus,
    TransactionType,
    RelationshipType,
    GeographicCoordinates,
    QualityMetrics
)

# Create test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_batch_tracking.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool)
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
        name="Palm Processing Ltd",
        company_type="processor",
        email="processor@example.com"
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
def sample_product(db_session: Session):
    """Create sample product for testing."""
    product = Product(
        id=uuid4(),
        common_product_id="FFB-001",
        name="Fresh Fruit Bunches",
        description="Fresh palm fruit bunches",
        category="raw_material",
        can_have_composition=False,
        default_unit="KGM",
        hs_code="1207.10.00"
    )
    
    db_session.add(product)
    db_session.commit()
    db_session.refresh(product)
    
    return product


class TestBatchCreation:
    """Test batch creation functionality."""
    
    def test_create_harvest_batch(self, db_session, sample_company, sample_user, sample_product):
        """Test creating a harvest batch."""
        batch_service = BatchTrackingService(db_session)
        
        batch_data = BatchCreate(
            batch_id="HARVEST-2025-001",
            batch_type=BatchType.HARVEST,
            product_id=sample_product.id,
            quantity=Decimal("1000.0"),
            unit="KGM",
            production_date=date.today(),
            location_name="Palm Plantation A",
            location_coordinates=GeographicCoordinates(
                latitude=2.5,
                longitude=101.5,
                accuracy_meters=10.0
            ),
            facility_code="FARM-001",
            quality_metrics=QualityMetrics(
                oil_content_percentage=22.5,
                moisture_content_percentage=18.0,
                ripeness_level="ripe"
            ),
            origin_data={
                "farm_id": "FARM-001",
                "harvest_method": "manual",
                "weather_conditions": "sunny"
            },
            certifications=["RSPO", "NDPE"]
        )
        
        batch = batch_service.create_batch(
            batch_data,
            sample_company.id,
            sample_user.id
        )
        
        assert batch.batch_id == "HARVEST-2025-001"
        assert batch.batch_type == BatchType.HARVEST.value
        assert batch.company_id == sample_company.id
        assert batch.product_id == sample_product.id
        assert batch.quantity == Decimal("1000.0")
        assert batch.unit == "KGM"
        assert batch.status == BatchStatus.ACTIVE.value
        assert batch.location_name == "Palm Plantation A"
        assert batch.location_coordinates["latitude"] == 2.5
        assert batch.quality_metrics["oil_content_percentage"] == 22.5
        assert "RSPO" in batch.certifications
        assert batch.origin_data["farm_id"] == "FARM-001"
    
    def test_create_processing_batch(self, db_session, sample_company, sample_user, sample_product):
        """Test creating a processing batch."""
        batch_service = BatchTrackingService(db_session)
        
        batch_data = BatchCreate(
            batch_id="PROCESS-2025-001",
            batch_type=BatchType.PROCESSING,
            product_id=sample_product.id,
            quantity=Decimal("800.0"),
            unit="KGM",
            production_date=date.today(),
            location_name="Processing Mill A",
            facility_code="MILL-001",
            processing_method="steam_sterilization",
            storage_conditions="ambient_temperature",
            transformation_id="TRANS-001",
            parent_batch_ids=[uuid4()],  # Reference to harvest batch
            quality_metrics=QualityMetrics(
                oil_content_percentage=24.0,
                moisture_content_percentage=15.0,
                free_fatty_acid_percentage=2.1
            )
        )
        
        batch = batch_service.create_batch(
            batch_data,
            sample_company.id,
            sample_user.id
        )
        
        assert batch.batch_id == "PROCESS-2025-001"
        assert batch.batch_type == BatchType.PROCESSING.value
        assert batch.processing_method == "steam_sterilization"
        assert batch.transformation_id == "TRANS-001"
        assert len(batch.parent_batch_ids) == 1
        assert batch.quality_metrics["free_fatty_acid_percentage"] == 2.1
    
    def test_create_transformation_batch(self, db_session, sample_company, sample_user, sample_product):
        """Test creating a transformation batch."""
        batch_service = BatchTrackingService(db_session)
        
        batch_data = BatchCreate(
            batch_id="REFINE-2025-001",
            batch_type=BatchType.TRANSFORMATION,
            product_id=sample_product.id,
            quantity=Decimal("600.0"),
            unit="KGM",
            production_date=date.today(),
            expiry_date=date.today() + timedelta(days=365),
            location_name="Refinery A",
            facility_code="REF-001",
            processing_method="refining_bleaching_deodorizing",
            transformation_id="REFINE-001",
            parent_batch_ids=[uuid4(), uuid4()],  # Multiple input batches
            quality_metrics=QualityMetrics(
                oil_content_percentage=99.5,
                moisture_content_percentage=0.1,
                free_fatty_acid_percentage=0.1,
                color_grade="Grade_A"
            ),
            certifications=["RSPO", "ISCC"]
        )
        
        batch = batch_service.create_batch(
            batch_data,
            sample_company.id,
            sample_user.id
        )
        
        assert batch.batch_id == "REFINE-2025-001"
        assert batch.batch_type == BatchType.TRANSFORMATION.value
        assert batch.expiry_date is not None
        assert batch.processing_method == "refining_bleaching_deodorizing"
        assert len(batch.parent_batch_ids) == 2
        assert batch.quality_metrics["oil_content_percentage"] == 99.5
        assert batch.quality_metrics["color_grade"] == "Grade_A"
    
    def test_create_duplicate_batch_id(self, db_session, sample_company, sample_user, sample_product):
        """Test creating batch with duplicate ID fails."""
        batch_service = BatchTrackingService(db_session)
        
        batch_data = BatchCreate(
            batch_id="DUPLICATE-001",
            batch_type=BatchType.HARVEST,
            product_id=sample_product.id,
            quantity=Decimal("1000.0"),
            unit="KGM",
            production_date=date.today()
        )
        
        # Create first batch
        batch_service.create_batch(
            batch_data,
            sample_company.id,
            sample_user.id
        )
        
        # Try to create duplicate
        with pytest.raises(Exception) as exc_info:
            batch_service.create_batch(
                batch_data,
                sample_company.id,
                sample_user.id
            )
        
        assert "already exists" in str(exc_info.value)


class TestBatchUpdates:
    """Test batch update functionality."""
    
    def test_update_batch_quantity(self, db_session, sample_company, sample_user, sample_product):
        """Test updating batch quantity."""
        batch_service = BatchTrackingService(db_session)
        
        # Create batch
        batch_data = BatchCreate(
            batch_id="UPDATE-001",
            batch_type=BatchType.HARVEST,
            product_id=sample_product.id,
            quantity=Decimal("1000.0"),
            unit="KGM",
            production_date=date.today()
        )
        
        batch = batch_service.create_batch(
            batch_data,
            sample_company.id,
            sample_user.id
        )
        
        # Update quantity
        update_data = BatchUpdate(
            quantity=Decimal("950.0")
        )
        
        updated_batch = batch_service.update_batch(
            batch.id,
            update_data,
            sample_company.id,
            sample_user.id
        )
        
        assert updated_batch.quantity == Decimal("950.0")
    
    def test_update_batch_status(self, db_session, sample_company, sample_user, sample_product):
        """Test updating batch status."""
        batch_service = BatchTrackingService(db_session)
        
        # Create batch
        batch_data = BatchCreate(
            batch_id="STATUS-001",
            batch_type=BatchType.HARVEST,
            product_id=sample_product.id,
            quantity=Decimal("1000.0"),
            unit="KGM",
            production_date=date.today()
        )
        
        batch = batch_service.create_batch(
            batch_data,
            sample_company.id,
            sample_user.id
        )
        
        # Update status
        update_data = BatchUpdate(
            status=BatchStatus.CONSUMED
        )
        
        updated_batch = batch_service.update_batch(
            batch.id,
            update_data,
            sample_company.id,
            sample_user.id
        )
        
        assert updated_batch.status == BatchStatus.CONSUMED.value
    
    def test_update_quality_metrics(self, db_session, sample_company, sample_user, sample_product):
        """Test updating batch quality metrics."""
        batch_service = BatchTrackingService(db_session)
        
        # Create batch
        batch_data = BatchCreate(
            batch_id="QUALITY-001",
            batch_type=BatchType.HARVEST,
            product_id=sample_product.id,
            quantity=Decimal("1000.0"),
            unit="KGM",
            production_date=date.today(),
            quality_metrics=QualityMetrics(
                oil_content_percentage=22.0,
                moisture_content_percentage=20.0
            )
        )
        
        batch = batch_service.create_batch(
            batch_data,
            sample_company.id,
            sample_user.id
        )
        
        # Update quality metrics
        new_quality_metrics = QualityMetrics(
            oil_content_percentage=23.5,
            moisture_content_percentage=18.0,
            ripeness_level="optimal"
        )
        
        update_data = BatchUpdate(
            quality_metrics=new_quality_metrics
        )
        
        updated_batch = batch_service.update_batch(
            batch.id,
            update_data,
            sample_company.id,
            sample_user.id
        )
        
        assert updated_batch.quality_metrics["oil_content_percentage"] == 23.5
        assert updated_batch.quality_metrics["moisture_content_percentage"] == 18.0
        assert updated_batch.quality_metrics["ripeness_level"] == "optimal"


class TestBatchTransactions:
    """Test batch transaction functionality."""
    
    def test_create_batch_transaction(self, db_session, sample_company, sample_user, sample_product):
        """Test creating a batch transaction."""
        batch_service = BatchTrackingService(db_session)
        
        # Create source and destination batches
        source_batch_data = BatchCreate(
            batch_id="SOURCE-001",
            batch_type=BatchType.HARVEST,
            product_id=sample_product.id,
            quantity=Decimal("1000.0"),
            unit="KGM",
            production_date=date.today()
        )
        
        source_batch = batch_service.create_batch(
            source_batch_data,
            sample_company.id,
            sample_user.id
        )
        
        dest_batch_data = BatchCreate(
            batch_id="DEST-001",
            batch_type=BatchType.PROCESSING,
            product_id=sample_product.id,
            quantity=Decimal("800.0"),
            unit="KGM",
            production_date=date.today()
        )
        
        dest_batch = batch_service.create_batch(
            dest_batch_data,
            sample_company.id,
            sample_user.id
        )
        
        # Create transaction
        transaction_data = BatchTransactionCreate(
            transaction_type=TransactionType.TRANSFORMATION,
            source_batch_id=source_batch.id,
            destination_batch_id=dest_batch.id,
            quantity_moved=Decimal("800.0"),
            unit="KGM",
            transaction_date=datetime.utcnow(),
            notes="Transformation from harvest to processing"
        )
        
        transaction = batch_service.create_batch_transaction(
            transaction_data,
            sample_company.id,
            sample_user.id
        )
        
        assert transaction.transaction_type == TransactionType.TRANSFORMATION.value
        assert transaction.source_batch_id == source_batch.id
        assert transaction.destination_batch_id == dest_batch.id
        assert transaction.quantity_moved == Decimal("800.0")
        assert transaction.company_id == sample_company.id
        assert transaction.created_by_user_id == sample_user.id


class TestBatchRelationships:
    """Test batch relationship functionality."""
    
    def test_create_batch_relationship(self, db_session, sample_company, sample_user, sample_product):
        """Test creating a batch relationship for traceability."""
        batch_service = BatchTrackingService(db_session)
        
        # Create parent and child batches
        parent_batch_data = BatchCreate(
            batch_id="PARENT-001",
            batch_type=BatchType.HARVEST,
            product_id=sample_product.id,
            quantity=Decimal("1000.0"),
            unit="KGM",
            production_date=date.today()
        )
        
        parent_batch = batch_service.create_batch(
            parent_batch_data,
            sample_company.id,
            sample_user.id
        )
        
        child_batch_data = BatchCreate(
            batch_id="CHILD-001",
            batch_type=BatchType.PROCESSING,
            product_id=sample_product.id,
            quantity=Decimal("800.0"),
            unit="KGM",
            production_date=date.today()
        )
        
        child_batch = batch_service.create_batch(
            child_batch_data,
            sample_company.id,
            sample_user.id
        )
        
        # Create relationship
        relationship_data = BatchRelationshipCreate(
            parent_batch_id=parent_batch.id,
            child_batch_id=child_batch.id,
            relationship_type=RelationshipType.TRANSFORMATION,
            quantity_contribution=Decimal("800.0"),
            percentage_contribution=Decimal("80.0"),
            transformation_process="steam_sterilization_pressing",
            transformation_date=datetime.utcnow(),
            yield_percentage=Decimal("80.0"),
            quality_impact={
                "oil_content_increase": 2.0,
                "moisture_reduction": 5.0
            }
        )
        
        relationship = batch_service.create_batch_relationship(
            relationship_data,
            sample_company.id,
            sample_user.id
        )
        
        assert relationship.parent_batch_id == parent_batch.id
        assert relationship.child_batch_id == child_batch.id
        assert relationship.relationship_type == RelationshipType.TRANSFORMATION.value
        assert relationship.quantity_contribution == Decimal("800.0")
        assert relationship.percentage_contribution == Decimal("80.0")
        assert relationship.yield_percentage == Decimal("80.0")
        assert relationship.quality_impact["oil_content_increase"] == 2.0
        assert relationship.created_by_user_id == sample_user.id
