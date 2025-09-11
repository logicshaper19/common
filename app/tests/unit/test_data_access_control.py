"""
Tests for data access control and permissions system.
"""
import pytest
from unittest.mock import Mock, patch
from uuid import uuid4
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base
from app.services.data_access_control import DataAccessControlService
from app.models.data_access import (
    DataAccessPermission,
    AccessAttempt,
    DataClassification,
    DataCategory,
    DataSensitivityLevel,
    AccessType,
    AccessResult
)
from app.models.user import User
from app.models.company import Company
from app.models.purchase_order import PurchaseOrder
from app.models.product import Product
from app.models.business_relationship import BusinessRelationship

# Create test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_data_access.db"
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
def sample_companies(db_session):
    """Create sample companies for testing."""
    companies = {}
    
    companies["buyer"] = Company(
        id=uuid4(),
        name="Buyer Company",
        company_type="brand",
        email="buyer@example.com"
    )
    
    companies["seller"] = Company(
        id=uuid4(),
        name="Seller Company",
        company_type="processor",
        email="seller@example.com"
    )
    
    companies["third_party"] = Company(
        id=uuid4(),
        name="Third Party Company",
        company_type="supplier",
        email="third@example.com"
    )
    
    for company in companies.values():
        db_session.add(company)
    
    db_session.commit()
    
    for company in companies.values():
        db_session.refresh(company)
    
    return companies


@pytest.fixture
def sample_users(db_session, sample_companies):
    """Create sample users for testing."""
    users = {}
    
    users["buyer_user"] = User(
        id=uuid4(),
        email="buyer.user@example.com",
        hashed_password="hashed_password",
        full_name="Buyer User",
        role="buyer",
        is_active=True,
        company_id=sample_companies["buyer"].id
    )
    
    users["seller_user"] = User(
        id=uuid4(),
        email="seller.user@example.com",
        hashed_password="hashed_password",
        full_name="Seller User",
        role="seller",
        is_active=True,
        company_id=sample_companies["seller"].id
    )
    
    users["third_party_user"] = User(
        id=uuid4(),
        email="third.user@example.com",
        hashed_password="hashed_password",
        full_name="Third Party User",
        role="supplier",
        is_active=True,
        company_id=sample_companies["third_party"].id
    )
    
    for user in users.values():
        db_session.add(user)
    
    db_session.commit()
    
    for user in users.values():
        db_session.refresh(user)
    
    return users


@pytest.fixture
def sample_business_relationship(db_session, sample_companies):
    """Create a sample business relationship."""
    relationship = BusinessRelationship(
        id=uuid4(),
        buyer_company_id=sample_companies["buyer"].id,
        seller_company_id=sample_companies["seller"].id,
        relationship_type="supplier",
        status="active",
        data_sharing_permissions={
            "operational_data": True,
            "traceability_data": True,
            "quality_data": True,
            "location_data": False,
            "commercial_data": False
        }
    )
    
    db_session.add(relationship)
    db_session.commit()
    db_session.refresh(relationship)
    
    return relationship


@pytest.fixture
def sample_product(db_session):
    """Create a sample product for testing."""
    product = Product(
        id=uuid4(),
        common_product_id="TEST-001",
        name="Test Product",
        description="Test product for data access control",
        category="raw_material",
        can_have_composition=False,
        default_unit="KGM"
    )
    db_session.add(product)
    db_session.commit()
    db_session.refresh(product)
    return product


@pytest.fixture
def sample_po(db_session, sample_companies, sample_product):
    """Create a sample purchase order for testing."""
    po = PurchaseOrder(
        id=uuid4(),
        po_number="PO-ACCESS-TEST-001",
        buyer_company_id=sample_companies["buyer"].id,
        seller_company_id=sample_companies["seller"].id,
        product_id=sample_product.id,
        quantity=Decimal("1000.0"),
        unit="KGM",
        unit_price=Decimal("800.00"),
        total_amount=Decimal("800000.00"),
        delivery_date=datetime.utcnow().date(),
        delivery_location="Test Location",
        status="pending"
    )
    db_session.add(po)
    db_session.commit()
    db_session.refresh(po)
    return po


class TestDataAccessControlService:
    """Test data access control service functionality."""
    
    def test_own_company_data_access(self, db_session, sample_companies, sample_users, sample_po):
        """Test that users can always access their own company's data."""
        access_control = DataAccessControlService(db_session)
        buyer_user = sample_users["buyer_user"]
        
        # Buyer accessing their own PO data
        access_result, permission, denial_reason = access_control.check_access_permission(
            requesting_user_id=buyer_user.id,
            requesting_company_id=buyer_user.company_id,
            target_company_id=buyer_user.company_id,  # Same company
            data_category=DataCategory.PURCHASE_ORDER,
            access_type=AccessType.READ,
            entity_type="purchase_order",
            entity_id=sample_po.id
        )
        
        assert access_result == AccessResult.GRANTED
        assert permission is None  # No explicit permission needed for own data
        assert denial_reason is None
    
    def test_cross_company_access_without_permission(self, db_session, sample_companies, sample_users, sample_po):
        """Test that cross-company access is denied without permission."""
        access_control = DataAccessControlService(db_session)
        third_party_user = sample_users["third_party_user"]
        
        # Third party trying to access buyer's PO data
        access_result, permission, denial_reason = access_control.check_access_permission(
            requesting_user_id=third_party_user.id,
            requesting_company_id=third_party_user.company_id,
            target_company_id=sample_companies["buyer"].id,
            data_category=DataCategory.PURCHASE_ORDER,
            access_type=AccessType.READ,
            entity_type="purchase_order",
            entity_id=sample_po.id
        )
        
        assert access_result == AccessResult.DENIED
        assert permission is None
        assert denial_reason is not None
    
    def test_relationship_based_access(self, db_session, sample_companies, sample_users, sample_po, sample_business_relationship):
        """Test access based on business relationship permissions."""
        access_control = DataAccessControlService(db_session)
        seller_user = sample_users["seller_user"]
        
        # Seller accessing buyer's operational data (allowed by relationship)
        access_result, permission, denial_reason = access_control.check_access_permission(
            requesting_user_id=seller_user.id,
            requesting_company_id=seller_user.company_id,
            target_company_id=sample_companies["buyer"].id,
            data_category=DataCategory.PURCHASE_ORDER,
            access_type=AccessType.READ,
            entity_type="purchase_order",
            entity_id=sample_po.id,
            sensitivity_level=DataSensitivityLevel.OPERATIONAL
        )
        
        assert access_result == AccessResult.GRANTED
        assert denial_reason is None
    
    def test_explicit_permission_grant(self, db_session, sample_companies, sample_users, sample_business_relationship):
        """Test granting explicit data access permission."""
        access_control = DataAccessControlService(db_session)
        buyer_user = sample_users["buyer_user"]
        
        # Grant permission for commercial data access
        permission = access_control.grant_permission(
            grantor_company_id=sample_companies["buyer"].id,
            grantee_company_id=sample_companies["seller"].id,
            data_category=DataCategory.PURCHASE_ORDER,
            sensitivity_level=DataSensitivityLevel.COMMERCIAL,
            access_types=[AccessType.READ],
            granted_by_user_id=buyer_user.id,
            justification="Need access for pricing negotiations"
        )
        
        assert permission.id is not None
        assert permission.grantor_company_id == sample_companies["buyer"].id
        assert permission.grantee_company_id == sample_companies["seller"].id
        assert permission.data_category == DataCategory.PURCHASE_ORDER
        assert permission.sensitivity_level == DataSensitivityLevel.COMMERCIAL
        assert AccessType.READ.value in permission.access_types
        assert permission.is_active
        assert permission.justification == "Need access for pricing negotiations"
    
    def test_permission_revocation(self, db_session, sample_companies, sample_users, sample_business_relationship):
        """Test revoking data access permission."""
        access_control = DataAccessControlService(db_session)
        buyer_user = sample_users["buyer_user"]
        
        # Grant permission first
        permission = access_control.grant_permission(
            grantor_company_id=sample_companies["buyer"].id,
            grantee_company_id=sample_companies["seller"].id,
            data_category=DataCategory.PURCHASE_ORDER,
            sensitivity_level=DataSensitivityLevel.OPERATIONAL,
            access_types=[AccessType.READ],
            granted_by_user_id=buyer_user.id,
            justification="Test permission"
        )
        
        assert permission.is_active
        
        # Revoke permission
        success = access_control.revoke_permission(
            permission_id=permission.id,
            revoked_by_user_id=buyer_user.id,
            revoked_by_company_id=sample_companies["buyer"].id,
            reason="No longer needed"
        )
        
        assert success
        
        # Refresh and check
        db_session.refresh(permission)
        assert not permission.is_active
        assert permission.revoked_at is not None
        assert permission.revoked_by_user_id == buyer_user.id
    
    def test_sensitive_data_filtering(self, db_session, sample_companies, sample_users, sample_business_relationship):
        """Test filtering of sensitive data based on permissions."""
        access_control = DataAccessControlService(db_session)
        
        # Sample PO data with mixed sensitivity levels
        po_data = {
            "po_number": "PO-001",  # Public
            "quantity": 1000,       # Operational
            "unit": "KGM",         # Operational
            "unit_price": 800.00,  # Commercial
            "total_amount": 800000.00,  # Commercial
            "delivery_date": "2024-01-01",  # Operational
            "notes": "Special handling required"  # Public
        }
        
        # Filter data for cross-company access
        filtered_data, filtered_fields = access_control.filter_sensitive_data(
            data=po_data,
            requesting_company_id=sample_companies["seller"].id,
            target_company_id=sample_companies["buyer"].id,
            data_category=DataCategory.PURCHASE_ORDER,
            entity_type="purchase_order"
        )
        
        # Commercial data should be filtered
        assert "unit_price" in filtered_fields
        assert "total_amount" in filtered_fields
        assert filtered_data["unit_price"] == "[COMMERCIAL_DATA_FILTERED]"
        assert filtered_data["total_amount"] == "[COMMERCIAL_DATA_FILTERED]"
        
        # Operational and public data should remain
        assert filtered_data["po_number"] == "PO-001"
        assert filtered_data["quantity"] == 1000
        assert filtered_data["unit"] == "KGM"
        assert filtered_data["delivery_date"] == "2024-01-01"
        assert filtered_data["notes"] == "Special handling required"
    
    def test_access_attempt_logging(self, db_session, sample_companies, sample_users, sample_po):
        """Test that access attempts are properly logged."""
        access_control = DataAccessControlService(db_session)
        third_party_user = sample_users["third_party_user"]
        
        # Attempt unauthorized access
        access_control.check_access_permission(
            requesting_user_id=third_party_user.id,
            requesting_company_id=third_party_user.company_id,
            target_company_id=sample_companies["buyer"].id,
            data_category=DataCategory.PURCHASE_ORDER,
            access_type=AccessType.READ,
            entity_type="purchase_order",
            entity_id=sample_po.id
        )
        
        # Check that access attempt was logged
        access_attempts = db_session.query(AccessAttempt).filter(
            AccessAttempt.requesting_user_id == third_party_user.id
        ).all()
        
        assert len(access_attempts) == 1
        
        attempt = access_attempts[0]
        assert attempt.requesting_company_id == third_party_user.company_id
        assert attempt.target_company_id == sample_companies["buyer"].id
        assert attempt.data_category == DataCategory.PURCHASE_ORDER
        assert attempt.access_type == AccessType.READ
        assert attempt.entity_type == "purchase_order"
        assert attempt.entity_id == sample_po.id
        assert attempt.access_result == AccessResult.DENIED
        assert attempt.denial_reason is not None
    
    def test_data_classification_rules(self, db_session):
        """Test automatic data classification based on field patterns."""
        access_control = DataAccessControlService(db_session)
        
        # Create classification rules
        commercial_rule = DataClassification(
            id=uuid4(),
            entity_type="purchase_order",
            field_pattern=r".*price.*|.*cost.*|.*amount.*",
            data_category=DataCategory.PURCHASE_ORDER,
            sensitivity_level=DataSensitivityLevel.COMMERCIAL,
            rule_name="Commercial Data Rule",
            description="Classify price-related fields as commercial",
            is_active=True,
            priority=100
        )
        
        operational_rule = DataClassification(
            id=uuid4(),
            entity_type="purchase_order",
            field_pattern=r".*quantity.*|.*date.*|.*status.*",
            data_category=DataCategory.PURCHASE_ORDER,
            sensitivity_level=DataSensitivityLevel.OPERATIONAL,
            rule_name="Operational Data Rule",
            description="Classify operational fields",
            is_active=True,
            priority=90
        )
        
        db_session.add(commercial_rule)
        db_session.add(operational_rule)
        db_session.commit()
        
        # Test field classification
        classifications = access_control._get_data_classifications("purchase_order")
        assert len(classifications) == 2
        
        # Test specific field classification
        price_sensitivity = access_control._classify_field_sensitivity(
            "unit_price", 800.00, "purchase_order", classifications
        )
        assert price_sensitivity == DataSensitivityLevel.COMMERCIAL
        
        quantity_sensitivity = access_control._classify_field_sensitivity(
            "quantity", 1000, "purchase_order", classifications
        )
        assert quantity_sensitivity == DataSensitivityLevel.OPERATIONAL
