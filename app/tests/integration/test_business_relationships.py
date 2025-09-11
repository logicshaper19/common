"""
Tests for business relationship management system.
"""
import pytest
from uuid import uuid4
from datetime import datetime, date
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from app.core.database import Base
from app.services.business_relationship import BusinessRelationshipService
from app.models.company import Company
from app.models.user import User
from app.models.business_relationship import BusinessRelationship
from app.models.product import Product
from app.models.purchase_order import PurchaseOrder
from app.models.batch import Batch, BatchTransaction, BatchRelationship
from app.schemas.business_relationship import (
    SupplierInvitationRequest,
    BusinessRelationshipCreate,
    BusinessRelationshipUpdate,
    DataSharingPermissions,
    RelationshipType,
    RelationshipStatus
)

# Create test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_business_relationships.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
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
def sample_companies(db_session: Session):
    """Create sample companies for testing."""
    companies = {}
    
    # Create buyer company
    companies["buyer"] = Company(
        id=uuid4(),
        name="Palm Processing Ltd",
        company_type="processor",
        email="processor@example.com"
    )
    
    # Create seller company
    companies["seller"] = Company(
        id=uuid4(),
        name="Palm Plantation Co",
        company_type="originator",
        email="plantation@example.com"
    )
    
    # Create partner company
    companies["partner"] = Company(
        id=uuid4(),
        name="Palm Trading Corp",
        company_type="brand",
        email="trading@example.com"
    )
    
    for company in companies.values():
        db_session.add(company)
    
    db_session.commit()
    
    for company in companies.values():
        db_session.refresh(company)
    
    return companies


@pytest.fixture
def sample_users(db_session: Session, sample_companies):
    """Create sample users for testing."""
    users = {}
    
    # Create buyer user
    users["buyer"] = User(
        id=uuid4(),
        email="buyer@example.com",
        hashed_password="hashed_password",
        full_name="Buyer User",
        role="buyer",
        company_id=sample_companies["buyer"].id
    )
    
    # Create seller user
    users["seller"] = User(
        id=uuid4(),
        email="seller@example.com",
        hashed_password="hashed_password",
        full_name="Seller User",
        role="seller",
        company_id=sample_companies["seller"].id
    )
    
    for user in users.values():
        db_session.add(user)
    
    db_session.commit()
    
    for user in users.values():
        db_session.refresh(user)
    
    return users


class TestSupplierInvitation:
    """Test supplier invitation functionality."""
    
    async def test_invite_new_supplier(self, db_session, sample_companies, sample_users):
        """Test inviting a completely new supplier."""
        relationship_service = BusinessRelationshipService(db_session)

        invitation_request = SupplierInvitationRequest(
            supplier_email="newsupplier@example.com",
            supplier_name="New Supplier Co",
            company_type="originator",
            relationship_type=RelationshipType.SUPPLIER,
            invitation_message="Welcome to our supply chain!"
        )

        result = await relationship_service.invite_supplier(
            invitation_request,
            sample_companies["buyer"].id,
            sample_users["buyer"].id
        )
        
        assert result["invitation_sent"] is True
        assert result["status"] == "pending"
        assert "company_id" in result
        assert "relationship_id" in result
        
        # Verify company was created
        new_company = db_session.query(Company).filter(
            Company.email == "newsupplier@example.com"
        ).first()
        assert new_company is not None
        assert new_company.name == "New Supplier Co"
        
        # Verify relationship was created
        relationship = db_session.query(BusinessRelationship).filter(
            BusinessRelationship.id == result["relationship_id"]
        ).first()
        assert relationship is not None
        assert relationship.status == RelationshipStatus.PENDING.value
        assert relationship.buyer_company_id == sample_companies["buyer"].id
        assert relationship.seller_company_id == new_company.id
    
    async def test_invite_existing_supplier(self, db_session, sample_companies, sample_users):
        """Test inviting an existing supplier company."""
        relationship_service = BusinessRelationshipService(db_session)

        invitation_request = SupplierInvitationRequest(
            supplier_email=sample_companies["seller"].email,
            supplier_name=sample_companies["seller"].name,
            company_type=sample_companies["seller"].company_type,
            relationship_type=RelationshipType.SUPPLIER
        )

        result = await relationship_service.invite_supplier(
            invitation_request,
            sample_companies["buyer"].id,
            sample_users["buyer"].id
        )
        
        assert result["relationship_established"] is True
        assert result["status"] == "active"
        assert result["company_id"] == sample_companies["seller"].id
        
        # Verify relationship was created
        relationship = db_session.query(BusinessRelationship).filter(
            BusinessRelationship.id == result["relationship_id"]
        ).first()
        assert relationship is not None
        assert relationship.status == RelationshipStatus.ACTIVE.value
        assert relationship.buyer_company_id == sample_companies["buyer"].id
        assert relationship.seller_company_id == sample_companies["seller"].id
    
    async def test_invite_duplicate_supplier(self, db_session, sample_companies, sample_users):
        """Test inviting a supplier that already has a relationship."""
        relationship_service = BusinessRelationshipService(db_session)

        # Create existing relationship
        existing_relationship = BusinessRelationship(
            id=uuid4(),
            buyer_company_id=sample_companies["buyer"].id,
            seller_company_id=sample_companies["seller"].id,
            relationship_type=RelationshipType.SUPPLIER.value,
            status=RelationshipStatus.ACTIVE.value,
            data_sharing_permissions={}
        )
        db_session.add(existing_relationship)
        db_session.commit()

        invitation_request = SupplierInvitationRequest(
            supplier_email=sample_companies["seller"].email,
            supplier_name=sample_companies["seller"].name,
            company_type=sample_companies["seller"].company_type,
            relationship_type=RelationshipType.SUPPLIER
        )

        with pytest.raises(Exception) as exc_info:
            await relationship_service.invite_supplier(
                invitation_request,
                sample_companies["buyer"].id,
                sample_users["buyer"].id
            )
        
        assert "already exists" in str(exc_info.value)


class TestBusinessRelationshipManagement:
    """Test business relationship management functionality."""
    
    def test_establish_relationship(self, db_session, sample_companies, sample_users):
        """Test establishing a new business relationship."""
        relationship_service = BusinessRelationshipService(db_session)
        
        relationship_data = BusinessRelationshipCreate(
            buyer_company_id=sample_companies["buyer"].id,
            seller_company_id=sample_companies["seller"].id,
            relationship_type=RelationshipType.SUPPLIER,
            data_sharing_permissions=DataSharingPermissions(
                operational_data=True,
                commercial_data=False,
                traceability_data=True,
                quality_data=True,
                location_data=False
            )
        )
        
        relationship = relationship_service.establish_relationship(
            relationship_data,
            sample_users["buyer"].id
        )
        
        assert relationship.buyer_company_id == sample_companies["buyer"].id
        assert relationship.seller_company_id == sample_companies["seller"].id
        assert relationship.relationship_type == RelationshipType.SUPPLIER.value
        assert relationship.status == RelationshipStatus.ACTIVE.value
        assert relationship.data_sharing_permissions["operational_data"] is True
        assert relationship.data_sharing_permissions["commercial_data"] is False
    
    def test_update_relationship_status(self, db_session, sample_companies, sample_users):
        """Test updating relationship status."""
        relationship_service = BusinessRelationshipService(db_session)
        
        # Create relationship
        relationship = BusinessRelationship(
            id=uuid4(),
            buyer_company_id=sample_companies["buyer"].id,
            seller_company_id=sample_companies["seller"].id,
            relationship_type=RelationshipType.SUPPLIER.value,
            status=RelationshipStatus.ACTIVE.value,
            data_sharing_permissions={}
        )
        db_session.add(relationship)
        db_session.commit()
        db_session.refresh(relationship)
        
        # Update to suspended
        update_data = BusinessRelationshipUpdate(
            status=RelationshipStatus.SUSPENDED
        )
        
        updated_relationship = relationship_service.update_relationship(
            relationship.id,
            update_data,
            sample_users["buyer"].id,
            sample_companies["buyer"].id
        )
        
        assert updated_relationship.status == RelationshipStatus.SUSPENDED.value
    
    def test_update_data_sharing_permissions(self, db_session, sample_companies, sample_users):
        """Test updating data sharing permissions."""
        relationship_service = BusinessRelationshipService(db_session)
        
        # Create relationship
        relationship = BusinessRelationship(
            id=uuid4(),
            buyer_company_id=sample_companies["buyer"].id,
            seller_company_id=sample_companies["seller"].id,
            relationship_type=RelationshipType.SUPPLIER.value,
            status=RelationshipStatus.ACTIVE.value,
            data_sharing_permissions={
                "operational_data": True,
                "commercial_data": False,
                "traceability_data": True,
                "quality_data": True,
                "location_data": False
            }
        )
        db_session.add(relationship)
        db_session.commit()
        db_session.refresh(relationship)
        
        # Update permissions
        new_permissions = DataSharingPermissions(
            operational_data=True,
            commercial_data=True,  # Changed to True
            traceability_data=True,
            quality_data=True,
            location_data=True  # Changed to True
        )
        
        update_data = BusinessRelationshipUpdate(
            data_sharing_permissions=new_permissions
        )
        
        updated_relationship = relationship_service.update_relationship(
            relationship.id,
            update_data,
            sample_users["buyer"].id,
            sample_companies["buyer"].id
        )
        
        assert updated_relationship.data_sharing_permissions["commercial_data"] is True
        assert updated_relationship.data_sharing_permissions["location_data"] is True
    
    def test_get_company_relationships(self, db_session, sample_companies, sample_users):
        """Test getting relationships for a company."""
        relationship_service = BusinessRelationshipService(db_session)
        
        # Create multiple relationships
        relationships = []
        for i in range(3):
            rel = BusinessRelationship(
                id=uuid4(),
                buyer_company_id=sample_companies["buyer"].id,
                seller_company_id=sample_companies["seller"].id if i == 0 else uuid4(),
                relationship_type=RelationshipType.SUPPLIER.value,
                status=RelationshipStatus.ACTIVE.value,
                data_sharing_permissions={}
            )
            relationships.append(rel)
            db_session.add(rel)
        
        db_session.commit()
        
        # Get relationships
        company_relationships, total_count = relationship_service.get_company_relationships(
            sample_companies["buyer"].id
        )
        
        assert total_count == 3
        assert len(company_relationships) == 3
        
        # Test filtering by status
        filtered_relationships, filtered_count = relationship_service.get_company_relationships(
            sample_companies["buyer"].id,
            status=RelationshipStatus.ACTIVE
        )
        
        assert filtered_count == 3
        assert all(rel.status == RelationshipStatus.ACTIVE.value for rel in filtered_relationships)
    
    def test_get_company_suppliers(self, db_session, sample_companies, sample_users):
        """Test getting suppliers for a company."""
        relationship_service = BusinessRelationshipService(db_session)
        
        # Create relationship
        relationship = BusinessRelationship(
            id=uuid4(),
            buyer_company_id=sample_companies["buyer"].id,
            seller_company_id=sample_companies["seller"].id,
            relationship_type=RelationshipType.SUPPLIER.value,
            status=RelationshipStatus.ACTIVE.value,
            data_sharing_permissions={}
        )
        db_session.add(relationship)
        db_session.commit()
        
        # Get suppliers
        suppliers, total_count = relationship_service.get_company_suppliers(
            sample_companies["buyer"].id
        )
        
        assert total_count == 1
        assert len(suppliers) == 1
        
        supplier = suppliers[0]
        assert supplier["company_id"] == sample_companies["seller"].id
        assert supplier["company_name"] == sample_companies["seller"].name
        assert supplier["relationship_status"] == RelationshipStatus.ACTIVE.value
        assert supplier["total_purchase_orders"] == 0  # No POs created yet
        assert supplier["active_purchase_orders"] == 0
