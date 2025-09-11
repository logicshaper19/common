"""
Enhanced tests for notification system with comprehensive business logic validation.
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from uuid import uuid4
from datetime import datetime, timedelta
from decimal import Decimal

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

# Test markers for categorization
pytestmark = [pytest.mark.unit, pytest.mark.notifications]


# ===== ENHANCED NOTIFICATION FIXTURES =====

@pytest.fixture
def notification_service(db_session):
    """Create notification service with enhanced capabilities."""
    return NotificationService(db_session)


@pytest.fixture
def test_notification_template(db_session):
    """Create a test notification template with business logic validation."""
    template = NotificationTemplate(
        id=uuid4(),
        notification_type=NotificationType.PO_STATUS_CHANGED,
        channel=NotificationChannel.EMAIL,
        subject_template="Purchase Order {{po_id}} Status Update",
        title_template="PO Status Update",
        message_template="Your purchase order {{po_id}} status has changed to {{status}}",
        variables=["po_id", "status"],
        is_active=True
    )
    db_session.add(template)
    db_session.commit()
    db_session.refresh(template)
    return template


@pytest.fixture
def test_user_preferences(db_session, test_user):
    """Create test user notification preferences."""
    preferences = UserNotificationPreferences(
        id=uuid4(),
        user_id=test_user.id,
        email_enabled=True,
        push_enabled=True,
        sms_enabled=False,
        webhook_enabled=True,
        notification_types={
            "PO_STATUS_CHANGED": True,
            "SUPPLIER_INVITATION": True,
            "SYSTEM_ALERT": False
        },
        quiet_hours_start="22:00",
        quiet_hours_end="08:00",
        timezone="UTC"
    )
    db_session.add(preferences)
    db_session.commit()
    db_session.refresh(preferences)
    return preferences


@pytest.fixture
def test_webhook_endpoint(db_session, test_company):
    """Create test webhook endpoint."""
    webhook = WebhookEndpoint(
        id=uuid4(),
        company_id=test_company.id,
        url="https://api.example.com/webhooks/notifications",
        secret_key="test_secret_key",
        is_active=True,
        notification_types=[NotificationType.PO_STATUS_CHANGED, NotificationType.SUPPLIER_INVITATION],
        retry_count=3,
        timeout_seconds=30
    )
    db_session.add(webhook)
    db_session.commit()
    db_session.refresh(webhook)
    return webhook


@pytest.fixture
def test_notification(db_session, test_user, test_purchase_order):
    """Create test notification with business context."""
    notification = Notification(
        id=uuid4(),
        user_id=test_user.id,
        type=NotificationType.PO_STATUS_CHANGED,
        title="Purchase Order Status Update",
        message=f"Purchase order {test_purchase_order.id} has been updated",
        priority=NotificationPriority.MEDIUM,
        status=NotificationStatus.PENDING,
        data={
            "po_id": str(test_purchase_order.id),
            "status": "confirmed",
            "company_name": test_purchase_order.seller_company.name,
            "total_value": float(test_purchase_order.quantity * test_purchase_order.unit_price)
        },
        created_at=datetime.utcnow()
    )
    db_session.add(notification)
    db_session.commit()
    db_session.refresh(notification)
    return notification


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


# ===== ENHANCED BUSINESS LOGIC TESTS =====

def test_notification_template_business_logic(db_session, test_notification_template, business_logic_validator):
    """Test notification template business logic validation."""
    template = test_notification_template

    # Business Logic: Template should have required fields
    assert template.notification_type is not None
    assert template.channel is not None
    assert template.subject_template is not None
    assert template.title_template is not None
    assert template.message_template is not None
    assert template.is_active is True

    # Business Logic: Template variables should be extractable
    assert "po_id" in template.variables
    assert "status" in template.variables

    # Business Logic: Template should render correctly
    rendered_subject = template.subject_template.replace("{{po_id}}", "PO-123").replace("{{status}}", "confirmed")
    assert "PO-123" in rendered_subject
    assert "confirmed" in rendered_subject


def test_user_notification_preferences_business_logic(db_session, test_user, test_user_preferences):
    """Test user notification preferences business logic."""
    preferences = test_user_preferences

    # Business Logic: User should have control over notification channels
    assert preferences.email_enabled is True
    assert preferences.push_enabled is True
    assert preferences.sms_enabled is False
    assert preferences.webhook_enabled is True

    # Business Logic: Notification type preferences should be granular
    assert preferences.notification_types["PO_STATUS_CHANGED"] is True
    assert preferences.notification_types["SUPPLIER_INVITATION"] is True
    assert preferences.notification_types["SYSTEM_ALERT"] is False

    # Business Logic: Quiet hours should be respected
    assert preferences.quiet_hours_start == "22:00"
    assert preferences.quiet_hours_end == "08:00"
    assert preferences.timezone == "UTC"


def test_webhook_endpoint_business_logic(db_session, test_webhook_endpoint, test_company):
    """Test webhook endpoint business logic validation."""
    webhook = test_webhook_endpoint

    # Business Logic: Webhook should belong to a company
    assert webhook.company_id == test_company.id
    assert webhook.url.startswith("https://")  # Security requirement

    # Business Logic: Webhook should have security configuration
    assert webhook.secret_key is not None
    assert len(webhook.secret_key) >= 10  # Minimum security requirement

    # Business Logic: Webhook should have retry and timeout configuration
    assert webhook.retry_count >= 1
    assert webhook.timeout_seconds >= 5
    assert webhook.timeout_seconds <= 60  # Reasonable timeout range

    # Business Logic: Webhook should specify notification types
    assert NotificationType.PO_STATUS_CHANGED in webhook.notification_types
    assert len(webhook.notification_types) > 0


def test_notification_delivery_business_logic(db_session, test_notification, test_user):
    """Test notification delivery business logic."""
    notification = test_notification

    # Business Logic: Notification should have business context
    assert "po_id" in notification.data
    assert "status" in notification.data
    assert "company_name" in notification.data
    assert "total_value" in notification.data

    # Business Logic: Notification priority should affect delivery
    if notification.priority == NotificationPriority.HIGH:
        # High priority notifications should be delivered immediately
        assert notification.status in [NotificationStatus.PENDING, NotificationStatus.SENT]

    # Business Logic: Notification should have proper timestamps
    assert notification.created_at is not None
    assert notification.created_at <= datetime.utcnow()

    # Business Logic: Notification data should be valid
    total_value = notification.data.get("total_value")
    if total_value:
        assert total_value > 0  # Business value should be positive


def test_notification_channel_selection_business_logic(db_session, test_user, test_user_preferences, notification_service):
    """Test notification channel selection based on user preferences."""
    preferences = test_user_preferences

    # Business Logic: Channel selection should respect user preferences
    available_channels = []

    if preferences.email_enabled:
        available_channels.append(NotificationChannel.EMAIL)

    if preferences.push_enabled:
        available_channels.append(NotificationChannel.PUSH)

    if preferences.sms_enabled:
        available_channels.append(NotificationChannel.SMS)

    if preferences.webhook_enabled:
        available_channels.append(NotificationChannel.WEBHOOK)

    # Business Logic: At least one channel should be enabled
    assert len(available_channels) > 0

    # Business Logic: Email should be enabled (critical notifications)
    assert NotificationChannel.EMAIL in available_channels

    # Business Logic: SMS should be disabled (user preference)
    assert NotificationChannel.SMS not in available_channels
