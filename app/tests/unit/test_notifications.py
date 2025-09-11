"""
Tests for notification system.
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from uuid import uuid4
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base
from app.services.notifications import NotificationService
from app.services.notification_events import NotificationEventTrigger
from app.models.notification import (
    Notification,
    NotificationDelivery,
    UserNotificationPreferences,
    NotificationTemplate,
    WebhookEndpoint,
    NotificationType,
    NotificationChannel,
    NotificationPriority,
    NotificationStatus
)
from app.models.user import User
from app.models.company import Company
from app.models.purchase_order import PurchaseOrder
from app.models.product import Product

# Create test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_notifications.db"
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
        description="Test product for notifications",
        category="raw_material",
        can_have_composition=False,
        default_unit="KGM"
    )
    db_session.add(product)
    db_session.commit()
    db_session.refresh(product)
    return product


@pytest.fixture
def sample_po(db_session, sample_companies, sample_users, sample_product):
    """Create a sample purchase order for testing."""
    po = PurchaseOrder(
        id=uuid4(),
        po_number="PO-TEST-001",
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


class TestNotificationService:
    """Test notification service functionality."""
    
    @patch('app.services.notifications.send_email_notification')
    @patch('app.services.notifications.send_webhook_notification')
    def test_create_notification(self, mock_webhook, mock_email, db_session, sample_users):
        """Test creating a basic notification."""
        # Mock Celery tasks
        mock_email.delay.return_value = Mock(id="email-task-id")
        mock_webhook.delay.return_value = Mock(id="webhook-task-id")

        service = NotificationService(db_session)
        user = sample_users["buyer_user"]

        notification = service.create_notification(
            user_id=user.id,
            notification_type=NotificationType.SYSTEM_ALERT,
            title="Test Notification",
            message="This is a test notification",
            priority=NotificationPriority.NORMAL
        )
        
        assert notification.id is not None
        assert notification.user_id == user.id
        assert notification.company_id == user.company_id
        assert notification.notification_type == NotificationType.SYSTEM_ALERT
        assert notification.title == "Test Notification"
        assert notification.message == "This is a test notification"
        assert notification.priority == NotificationPriority.NORMAL
        assert not notification.is_read
        
        # Check that delivery records were created
        deliveries = db_session.query(NotificationDelivery).filter(
            NotificationDelivery.notification_id == notification.id
        ).all()
        
        # Should have in-app and email deliveries by default
        assert len(deliveries) >= 1
    
    @patch('app.services.notifications.send_email_notification')
    @patch('app.services.notifications.send_webhook_notification')
    def test_create_po_notification(self, mock_webhook, mock_email, db_session, sample_po, sample_users):
        """Test creating PO-related notifications."""
        # Mock Celery tasks
        mock_email.delay.return_value = Mock(id="email-task-id")
        mock_webhook.delay.return_value = Mock(id="webhook-task-id")

        service = NotificationService(db_session)

        notifications = service.create_po_notification(
            po_id=sample_po.id,
            notification_type=NotificationType.PO_CREATED,
            template_variables={
                "po_number": sample_po.po_number,
                "buyer_company": "Buyer Company",
                "seller_company": "Seller Company"
            }
        )
        
        # Should create notifications for seller company users
        assert len(notifications) >= 1
        
        notification = notifications[0]
        assert notification.notification_type == NotificationType.PO_CREATED
        assert notification.related_po_id == sample_po.id
        assert sample_po.po_number in notification.title or sample_po.po_number in notification.message
    
    @patch('app.services.notifications.send_email_notification')
    @patch('app.services.notifications.send_webhook_notification')
    def test_mark_as_read(self, mock_webhook, mock_email, db_session, sample_users):
        """Test marking notification as read."""
        # Mock Celery tasks
        mock_email.delay.return_value = Mock(id="email-task-id")
        mock_webhook.delay.return_value = Mock(id="webhook-task-id")

        service = NotificationService(db_session)
        user = sample_users["buyer_user"]

        # Create notification
        notification = service.create_notification(
            user_id=user.id,
            notification_type=NotificationType.SYSTEM_ALERT,
            title="Test Notification",
            message="This is a test notification"
        )
        
        assert not notification.is_read
        assert notification.read_at is None
        
        # Mark as read
        success = service.mark_as_read(notification.id, user.id)
        assert success
        
        # Refresh and check
        db_session.refresh(notification)
        assert notification.is_read
        assert notification.read_at is not None
    
    @patch('app.services.notifications.send_email_notification')
    @patch('app.services.notifications.send_webhook_notification')
    def test_get_user_notifications(self, mock_webhook, mock_email, db_session, sample_users):
        """Test getting user notifications."""
        # Mock Celery tasks
        mock_email.delay.return_value = Mock(id="email-task-id")
        mock_webhook.delay.return_value = Mock(id="webhook-task-id")

        service = NotificationService(db_session)
        user = sample_users["buyer_user"]

        # Create multiple notifications
        for i in range(5):
            service.create_notification(
                user_id=user.id,
                notification_type=NotificationType.SYSTEM_ALERT,
                title=f"Test Notification {i}",
                message=f"This is test notification {i}"
            )
        
        # Get all notifications
        notifications = service.get_user_notifications(user.id)
        assert len(notifications) == 5
        
        # Mark one as read
        service.mark_as_read(notifications[0].id, user.id)
        
        # Get only unread notifications
        unread_notifications = service.get_user_notifications(user.id, unread_only=True)
        assert len(unread_notifications) == 4
        
        # Test pagination
        paginated_notifications = service.get_user_notifications(user.id, limit=3)
        assert len(paginated_notifications) == 3


class TestNotificationEventTrigger:
    """Test notification event triggers."""
    
    @patch('app.services.notifications.send_email_notification')
    @patch('app.services.notifications.send_webhook_notification')
    def test_trigger_po_created(self, mock_webhook, mock_email, db_session, sample_po, sample_users):
        """Test PO created notification trigger."""
        # Mock Celery tasks
        mock_email.delay.return_value = Mock(id="email-task-id")
        mock_webhook.delay.return_value = Mock(id="webhook-task-id")

        trigger = NotificationEventTrigger(db_session)
        user = sample_users["buyer_user"]

        notification_ids = trigger.trigger_po_created(
            po_id=sample_po.id,
            created_by_user_id=user.id
        )
        
        assert len(notification_ids) >= 1
        
        # Check that notifications were created
        notifications = db_session.query(Notification).filter(
            Notification.related_po_id == sample_po.id,
            Notification.notification_type == NotificationType.PO_CREATED
        ).all()
        
        assert len(notifications) >= 1
        notification = notifications[0]
        assert sample_po.po_number in notification.title or sample_po.po_number in notification.message
    
    def test_trigger_po_status_changed(self, db_session, sample_po, sample_users):
        """Test PO status changed notification trigger."""
        trigger = NotificationEventTrigger(db_session)
        user = sample_users["buyer_user"]
        
        notification_ids = trigger.trigger_po_status_changed(
            po_id=sample_po.id,
            old_status="pending",
            new_status="confirmed",
            changed_by_user_id=user.id
        )
        
        assert len(notification_ids) >= 1
        
        # Check that notifications were created
        notifications = db_session.query(Notification).filter(
            Notification.related_po_id == sample_po.id,
            Notification.notification_type == NotificationType.PO_STATUS_CHANGED
        ).all()
        
        assert len(notifications) >= 1
        notification = notifications[0]
        assert "confirmed" in notification.message.lower()
    
    def test_trigger_transparency_updated(self, db_session, sample_po, sample_users):
        """Test transparency updated notification trigger."""
        trigger = NotificationEventTrigger(db_session)
        
        notification_ids = trigger.trigger_transparency_updated(
            po_id=sample_po.id,
            ttm_score=0.85,
            ttp_score=0.92,
            confidence_level=0.88
        )
        
        assert len(notification_ids) >= 1
        
        # Check that notifications were created
        notifications = db_session.query(Notification).filter(
            Notification.related_po_id == sample_po.id,
            Notification.notification_type == NotificationType.TRANSPARENCY_UPDATED
        ).all()
        
        assert len(notifications) >= 1
        notification = notifications[0]
        assert "transparency" in notification.title.lower() or "transparency" in notification.message.lower()


class TestUserNotificationPreferences:
    """Test user notification preferences."""
    
    def test_create_notification_preferences(self, db_session, sample_users):
        """Test creating notification preferences."""
        user = sample_users["buyer_user"]
        
        preferences = UserNotificationPreferences(
            user_id=user.id,
            notification_type=NotificationType.PO_CREATED,
            in_app_enabled=True,
            email_enabled=False,
            webhook_enabled=False,
            email_digest_frequency="daily",
            min_priority=NotificationPriority.NORMAL
        )
        
        db_session.add(preferences)
        db_session.commit()
        db_session.refresh(preferences)
        
        assert preferences.id is not None
        assert preferences.user_id == user.id
        assert preferences.notification_type == NotificationType.PO_CREATED
        assert preferences.in_app_enabled
        assert not preferences.email_enabled
        assert not preferences.webhook_enabled
        assert preferences.email_digest_frequency == "daily"
        assert preferences.min_priority == NotificationPriority.NORMAL


class TestWebhookEndpoint:
    """Test webhook endpoint functionality."""
    
    def test_create_webhook_endpoint(self, db_session, sample_companies):
        """Test creating webhook endpoint."""
        company = sample_companies["buyer"]
        
        webhook = WebhookEndpoint(
            id=uuid4(),
            company_id=company.id,
            name="Test Webhook",
            url="https://example.com/webhook",
            secret_key="test_secret",
            notification_types=[NotificationType.PO_CREATED.value, NotificationType.PO_CONFIRMED.value],
            timeout_seconds=30,
            max_retries=3,
            is_active=True
        )
        
        db_session.add(webhook)
        db_session.commit()
        db_session.refresh(webhook)
        
        assert webhook.id is not None
        assert webhook.company_id == company.id
        assert webhook.name == "Test Webhook"
        assert webhook.url == "https://example.com/webhook"
        assert webhook.secret_key == "test_secret"
        assert NotificationType.PO_CREATED.value in webhook.notification_types
        assert NotificationType.PO_CONFIRMED.value in webhook.notification_types
        assert webhook.timeout_seconds == 30
        assert webhook.max_retries == 3
        assert webhook.is_active


class TestNotificationDelivery:
    """Test notification delivery functionality."""
    
    @patch('app.services.notifications._send_email_via_resend')
    def test_email_delivery_success(self, mock_send_email, db_session, sample_users):
        """Test successful email delivery."""
        mock_send_email.return_value = {
            "message_id": "test_message_id",
            "status": "sent"
        }
        
        service = NotificationService(db_session)
        user = sample_users["buyer_user"]
        
        # Create notification with email channel
        notification = service.create_notification(
            user_id=user.id,
            notification_type=NotificationType.SYSTEM_ALERT,
            title="Test Email Notification",
            message="This is a test email notification",
            channels=[NotificationChannel.EMAIL]
        )
        
        # Check that delivery record was created
        delivery = db_session.query(NotificationDelivery).filter(
            NotificationDelivery.notification_id == notification.id,
            NotificationDelivery.channel == NotificationChannel.EMAIL
        ).first()
        
        assert delivery is not None
        assert delivery.status == NotificationStatus.PENDING
        assert delivery.attempt_count == 0
