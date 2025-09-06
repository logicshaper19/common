"""
Integration tests for audit logging with purchase order operations.
"""
import pytest
from unittest.mock import Mock, patch
from uuid import uuid4
from datetime import datetime
from decimal import Decimal
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base
from app.services.purchase_order import PurchaseOrderService
from app.services.audit_logger import AuditLogger
from app.models.audit_event import AuditEvent, AuditEventType
from app.models.user import User
from app.models.company import Company
from app.models.purchase_order import PurchaseOrder
from app.models.product import Product
from app.schemas.purchase_order import PurchaseOrderCreate, PurchaseOrderUpdate, PurchaseOrderStatus

# Create test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_audit_integration.db"
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
    
    for user in users.values():
        db_session.add(user)
    
    db_session.commit()
    
    for user in users.values():
        db_session.refresh(user)
    
    return users


@pytest.fixture
def sample_product(db_session):
    """Create a sample product for testing."""
    product = Product(
        id=uuid4(),
        common_product_id="TEST-001",
        name="Test Product",
        description="Test product for audit integration",
        category="raw_material",
        can_have_composition=False,
        default_unit="KGM"
    )
    db_session.add(product)
    db_session.commit()
    db_session.refresh(product)
    return product


class TestAuditIntegration:
    """Test audit logging integration with PO operations."""
    
    @patch('app.services.notifications.send_email_notification')
    @patch('app.services.notifications.send_webhook_notification')
    def test_po_creation_audit_trail(self, mock_webhook, mock_email, db_session, sample_companies, sample_users, sample_product):
        """Test that PO creation generates comprehensive audit trail."""
        # Mock notification tasks
        mock_email.delay.return_value = Mock(id="email-task-id")
        mock_webhook.delay.return_value = Mock(id="webhook-task-id")
        
        po_service = PurchaseOrderService(db_session)
        audit_logger = AuditLogger(db_session)
        
        buyer_company = sample_companies["buyer"]
        seller_company = sample_companies["seller"]
        product = sample_product
        
        # Create PO data
        po_data = PurchaseOrderCreate(
            buyer_company_id=buyer_company.id,
            seller_company_id=seller_company.id,
            product_id=product.id,
            quantity=Decimal("1000.0"),
            unit="KGM",
            unit_price=Decimal("800.00"),
            delivery_date=datetime.utcnow().date(),
            delivery_location="Test Location",
            notes="Test PO creation with audit"
        )
        
        # Create PO (this should trigger audit logging)
        po = po_service.create_purchase_order(po_data, buyer_company.id)
        
        # Verify PO was created
        assert po.id is not None
        assert po.po_number is not None
        
        # Verify audit event was created
        audit_events = audit_logger.query_audit_events(
            entity_type="purchase_order",
            entity_id=po.id
        )
        
        assert len(audit_events) == 1
        
        audit_event = audit_events[0]
        assert audit_event.event_type == AuditEventType.PO_CREATED
        assert audit_event.action == "create"
        assert audit_event.actor_company_id == buyer_company.id
        assert audit_event.entity_id == po.id
        assert audit_event.new_values is not None
        assert audit_event.old_values is None  # No old values for creation
        
        # Verify audit event contains PO details
        new_values = audit_event.new_values
        assert new_values["po_number"] == po.po_number
        assert new_values["buyer_company_id"] == str(buyer_company.id)
        assert new_values["seller_company_id"] == str(seller_company.id)
        assert new_values["product_id"] == str(product.id)
        assert new_values["quantity"] == 1000.0
        assert new_values["unit_price"] == 800.0
        assert new_values["total_amount"] == 800000.0
        assert new_values["notes"] == "Test PO creation with audit"
        
        # Verify business context
        assert audit_event.business_context is not None
        business_context = audit_event.business_context
        assert business_context["buyer_company_name"] == buyer_company.name
        assert business_context["seller_company_name"] == seller_company.name
        assert business_context["product_name"] == product.name
        assert business_context["workflow_stage"] == "creation"
    
    @patch('app.services.notifications.send_email_notification')
    @patch('app.services.notifications.send_webhook_notification')
    def test_po_update_audit_trail(self, mock_webhook, mock_email, db_session, sample_companies, sample_users, sample_product):
        """Test that PO updates generate comprehensive audit trail."""
        # Mock notification tasks
        mock_email.delay.return_value = Mock(id="email-task-id")
        mock_webhook.delay.return_value = Mock(id="webhook-task-id")
        
        po_service = PurchaseOrderService(db_session)
        audit_logger = AuditLogger(db_session)
        
        buyer_company = sample_companies["buyer"]
        seller_company = sample_companies["seller"]
        product = sample_product
        
        # Create initial PO
        po_data = PurchaseOrderCreate(
            buyer_company_id=buyer_company.id,
            seller_company_id=seller_company.id,
            product_id=product.id,
            quantity=Decimal("1000.0"),
            unit="KGM",
            unit_price=Decimal("800.00"),
            delivery_date=datetime.utcnow().date(),
            delivery_location="Test Location"
        )
        
        po = po_service.create_purchase_order(po_data, buyer_company.id)
        
        # Update the PO
        update_data = PurchaseOrderUpdate(
            quantity=Decimal("1500.0"),
            unit_price=Decimal("750.00"),
            notes="Updated PO with new quantity and price"
        )
        
        updated_po = po_service.update_purchase_order(
            str(po.id),
            update_data,
            buyer_company.id
        )
        
        # Verify PO was updated
        assert updated_po.quantity == Decimal("1500.0")
        assert updated_po.unit_price == Decimal("750.00")
        assert updated_po.total_amount == Decimal("1125000.00")  # 1500 * 750
        
        # Verify audit events were created (creation + update)
        audit_events = audit_logger.query_audit_events(
            entity_type="purchase_order",
            entity_id=po.id,
            order_desc=True
        )
        
        assert len(audit_events) == 2
        
        # Check update event (most recent)
        update_event = audit_events[0]
        assert update_event.event_type == AuditEventType.PO_UPDATED
        assert update_event.action == "update"
        assert update_event.actor_company_id == buyer_company.id
        
        # Verify old and new values
        old_values = update_event.old_values
        new_values = update_event.new_values
        
        assert old_values["quantity"] == 1000.0
        assert old_values["unit_price"] == 800.0
        assert old_values["total_amount"] == 800000.0
        
        assert new_values["quantity"] == 1500.0
        assert new_values["unit_price"] == 750.0
        assert new_values["total_amount"] == 1125000.0
        assert new_values["notes"] == "Updated PO with new quantity and price"
        
        # Verify changed fields
        assert "quantity" in update_event.changed_fields
        assert "unit_price" in update_event.changed_fields
        assert "total_amount" in update_event.changed_fields
        assert "notes" in update_event.changed_fields
        
        # Check creation event
        creation_event = audit_events[1]
        assert creation_event.event_type == AuditEventType.PO_CREATED
        assert creation_event.action == "create"
    
    def test_audit_trail_completeness(self, db_session, sample_companies, sample_users, sample_product):
        """Test that audit trail captures complete PO lifecycle."""
        audit_logger = AuditLogger(db_session)
        
        buyer_company = sample_companies["buyer"]
        product = sample_product
        
        # Create a PO manually to test audit trail retrieval
        po = PurchaseOrder(
            id=uuid4(),
            po_number="PO-AUDIT-TEST-001",
            buyer_company_id=buyer_company.id,
            seller_company_id=sample_companies["seller"].id,
            product_id=product.id,
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
        
        # Create audit events for PO lifecycle
        lifecycle_events = [
            (AuditEventType.PO_CREATED, "create", "PO created"),
            (AuditEventType.PO_UPDATED, "update", "PO details updated"),
            (AuditEventType.PO_CONFIRMED, "confirm", "PO confirmed by seller"),
            (AuditEventType.PO_STATUS_CHANGED, "status_change", "PO status changed to confirmed")
        ]
        
        for event_type, action, description in lifecycle_events:
            audit_logger.log_po_event(
                event_type=event_type,
                po_id=po.id,
                action=action,
                description=description,
                actor_company_id=buyer_company.id
            )
        
        # Get complete audit trail
        audit_trail = audit_logger.get_po_audit_trail(po.id)
        
        assert len(audit_trail) == 4
        
        # Verify events are in reverse chronological order
        assert audit_trail[0].event_type == AuditEventType.PO_STATUS_CHANGED
        assert audit_trail[1].event_type == AuditEventType.PO_CONFIRMED
        assert audit_trail[2].event_type == AuditEventType.PO_UPDATED
        assert audit_trail[3].event_type == AuditEventType.PO_CREATED
        
        # Verify all events are for the same PO
        for event in audit_trail:
            assert event.entity_id == po.id
            assert event.entity_type == "purchase_order"
            assert event.actor_company_id == buyer_company.id
    
    def test_audit_query_filtering(self, db_session, sample_companies, sample_users, sample_product):
        """Test comprehensive audit event querying and filtering."""
        audit_logger = AuditLogger(db_session)
        
        buyer_company = sample_companies["buyer"]
        seller_company = sample_companies["seller"]
        buyer_user = sample_users["buyer_user"]
        seller_user = sample_users["seller_user"]
        
        # Create multiple POs and audit events
        pos = []
        for i in range(3):
            po = PurchaseOrder(
                id=uuid4(),
                po_number=f"PO-FILTER-TEST-{i:03d}",
                buyer_company_id=buyer_company.id,
                seller_company_id=seller_company.id,
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
            pos.append(po)
        
        db_session.commit()
        
        # Create audit events for different actors and types
        for i, po in enumerate(pos):
            # Buyer creates PO
            audit_logger.log_po_event(
                event_type=AuditEventType.PO_CREATED,
                po_id=po.id,
                action="create",
                description=f"PO {po.po_number} created",
                actor_user_id=buyer_user.id,
                actor_company_id=buyer_company.id
            )
            
            # Seller confirms PO (only for first two POs)
            if i < 2:
                audit_logger.log_po_event(
                    event_type=AuditEventType.PO_CONFIRMED,
                    po_id=po.id,
                    action="confirm",
                    description=f"PO {po.po_number} confirmed",
                    actor_user_id=seller_user.id,
                    actor_company_id=seller_company.id
                )
        
        # Test filtering by entity type
        po_events = audit_logger.query_audit_events(entity_type="purchase_order")
        assert len(po_events) == 5  # 3 created + 2 confirmed
        
        # Test filtering by event type
        creation_events = audit_logger.query_audit_events(event_type=AuditEventType.PO_CREATED)
        assert len(creation_events) == 3
        
        confirmation_events = audit_logger.query_audit_events(event_type=AuditEventType.PO_CONFIRMED)
        assert len(confirmation_events) == 2
        
        # Test filtering by actor company
        buyer_events = audit_logger.query_audit_events(actor_company_id=buyer_company.id)
        assert len(buyer_events) == 3  # All creation events
        
        seller_events = audit_logger.query_audit_events(actor_company_id=seller_company.id)
        assert len(seller_events) == 2  # All confirmation events
        
        # Test filtering by actor user
        buyer_user_events = audit_logger.query_audit_events(actor_user_id=buyer_user.id)
        assert len(buyer_user_events) == 3
        
        seller_user_events = audit_logger.query_audit_events(actor_user_id=seller_user.id)
        assert len(seller_user_events) == 2
        
        # Test filtering by specific entity
        specific_po_events = audit_logger.query_audit_events(
            entity_type="purchase_order",
            entity_id=pos[0].id
        )
        assert len(specific_po_events) == 2  # Created + confirmed
        
        # Test pagination
        paginated_events = audit_logger.query_audit_events(limit=3, offset=0)
        assert len(paginated_events) == 3
        
        next_page_events = audit_logger.query_audit_events(limit=3, offset=3)
        assert len(next_page_events) == 2
