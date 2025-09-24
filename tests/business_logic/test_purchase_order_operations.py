"""
Tests for Purchase Order Business Logic Operations

These tests demonstrate how easy it is to test pure business logic functions:
- No HTTP concerns
- No database complexity
- Fast execution
- Clear assertions
- Easy to maintain
"""
import pytest
from datetime import datetime
from uuid import uuid4, UUID

from app.business_logic.purchase_order_operations import (
    confirm_purchase_order_business_logic,
    approve_purchase_order_business_logic,
    create_purchase_order_business_logic,
    cancel_purchase_order_business_logic,
    update_purchase_order_business_logic,
    ConfirmationRequest,
    PurchaseOrderStatus
)
from app.business_logic.exceptions import (
    AuthorizationError,
    ValidationError,
    StateTransitionError
)


class MockPurchaseOrder:
    """Mock PurchaseOrder for testing."""
    def __init__(self, **kwargs):
        self.id = kwargs.get('id', uuid4())
        self.buyer_company_id = kwargs.get('buyer_company_id', uuid4())
        self.seller_company_id = kwargs.get('seller_company_id', uuid4())
        self.product_id = kwargs.get('product_id', uuid4())
        self.quantity = kwargs.get('quantity', 100.0)
        self.unit = kwargs.get('unit', 'kg')
        self.price_per_unit = kwargs.get('price_per_unit', 10.0)
        self.total_amount = kwargs.get('total_amount', 1000.0)
        self.status = kwargs.get('status', PurchaseOrderStatus.PENDING_CONFIRMATION)
        self.confirmed_quantity = kwargs.get('confirmed_quantity', None)
        self.confirmed_at = kwargs.get('confirmed_at', None)
        self.confirmed_by_user_id = kwargs.get('confirmed_by_user_id', None)
        self.has_discrepancy = kwargs.get('has_discrepancy', False)
        self.discrepancy_reason = kwargs.get('discrepancy_reason', None)
        self.buyer_approved_at = kwargs.get('buyer_approved_at', None)
        self.buyer_approval_user_id = kwargs.get('buyer_approval_user_id', None)
        self.cancelled_at = kwargs.get('cancelled_at', None)
        self.cancelled_by_user_id = kwargs.get('cancelled_by_user_id', None)
        self.cancellation_reason = kwargs.get('cancellation_reason', None)
        self.updated_at = kwargs.get('updated_at', None)


class MockUser:
    """Mock User for testing."""
    def __init__(self, **kwargs):
        self.id = kwargs.get('id', uuid4())
        self.company_id = kwargs.get('company_id', uuid4())


class MockSession:
    """Mock database session for testing."""
    pass


def test_confirm_purchase_order_business_logic_success():
    """Test successful PO confirmation."""
    
    # Arrange
    seller_company_id = uuid4()
    user = MockUser(company_id=seller_company_id)
    po = MockPurchaseOrder(
        seller_company_id=seller_company_id,
        status=PurchaseOrderStatus.PENDING_CONFIRMATION,
        quantity=100.0
    )
    confirmation = ConfirmationRequest(quantity=100.0)
    db = MockSession()
    
    # Act
    result = confirm_purchase_order_business_logic(po, confirmation, user, db)
    
    # Assert
    assert result.status == PurchaseOrderStatus.CONFIRMED
    assert result.confirmed_quantity == 100.0
    assert result.confirmed_by_user_id == user.id
    assert result.confirmed_at is not None
    assert result.has_discrepancy == False


def test_confirm_purchase_order_business_logic_with_discrepancy():
    """Test PO confirmation with quantity discrepancy."""
    
    # Arrange
    seller_company_id = uuid4()
    user = MockUser(company_id=seller_company_id)
    po = MockPurchaseOrder(
        seller_company_id=seller_company_id,
        status=PurchaseOrderStatus.PENDING_CONFIRMATION,
        quantity=100.0
    )
    confirmation = ConfirmationRequest(
        quantity=80.0,
        discrepancy_reason="Shortage due to weather"
    )
    db = MockSession()
    
    # Act
    result = confirm_purchase_order_business_logic(po, confirmation, user, db)
    
    # Assert
    assert result.status == PurchaseOrderStatus.PENDING_BUYER_APPROVAL
    assert result.confirmed_quantity == 80.0
    assert result.has_discrepancy == True
    assert result.discrepancy_reason == "Shortage due to weather"


def test_confirm_purchase_order_business_logic_authorization_error():
    """Test PO confirmation with wrong user company."""
    
    # Arrange
    seller_company_id = uuid4()
    wrong_company_id = uuid4()
    user = MockUser(company_id=wrong_company_id)
    po = MockPurchaseOrder(
        seller_company_id=seller_company_id,
        status=PurchaseOrderStatus.PENDING_CONFIRMATION
    )
    confirmation = ConfirmationRequest(quantity=100.0)
    db = MockSession()
    
    # Act & Assert
    with pytest.raises(AuthorizationError) as exc_info:
        confirm_purchase_order_business_logic(po, confirmation, user, db)
    
    assert "Only seller can confirm purchase order" in str(exc_info.value)


def test_confirm_purchase_order_business_logic_state_transition_error():
    """Test PO confirmation with wrong status."""
    
    # Arrange
    seller_company_id = uuid4()
    user = MockUser(company_id=seller_company_id)
    po = MockPurchaseOrder(
        seller_company_id=seller_company_id,
        status=PurchaseOrderStatus.CONFIRMED  # Wrong status
    )
    confirmation = ConfirmationRequest(quantity=100.0)
    db = MockSession()
    
    # Act & Assert
    with pytest.raises(StateTransitionError) as exc_info:
        confirm_purchase_order_business_logic(po, confirmation, user, db)
    
    assert "Cannot confirm PO in status: confirmed" in str(exc_info.value)


def test_confirm_purchase_order_business_logic_validation_error():
    """Test PO confirmation with invalid quantity."""
    
    # Arrange
    seller_company_id = uuid4()
    user = MockUser(company_id=seller_company_id)
    po = MockPurchaseOrder(
        seller_company_id=seller_company_id,
        status=PurchaseOrderStatus.PENDING_CONFIRMATION
    )
    confirmation = ConfirmationRequest(quantity=0.0)  # Invalid quantity
    db = MockSession()
    
    # Act & Assert
    with pytest.raises(ValidationError) as exc_info:
        confirm_purchase_order_business_logic(po, confirmation, user, db)
    
    assert "Confirmed quantity must be greater than zero" in str(exc_info.value)


def test_approve_purchase_order_business_logic_success():
    """Test successful PO approval."""
    
    # Arrange
    buyer_company_id = uuid4()
    user = MockUser(company_id=buyer_company_id)
    po = MockPurchaseOrder(
        buyer_company_id=buyer_company_id,
        status=PurchaseOrderStatus.PENDING_BUYER_APPROVAL,
        has_discrepancy=True
    )
    db = MockSession()
    
    # Act
    result = approve_purchase_order_business_logic(po, user, db)
    
    # Assert
    assert result.status == PurchaseOrderStatus.APPROVED
    assert result.buyer_approved_at is not None
    assert result.buyer_approval_user_id == user.id
    assert result.has_discrepancy == False


def test_approve_purchase_order_business_logic_authorization_error():
    """Test PO approval with wrong user company."""
    
    # Arrange
    buyer_company_id = uuid4()
    wrong_company_id = uuid4()
    user = MockUser(company_id=wrong_company_id)
    po = MockPurchaseOrder(
        buyer_company_id=buyer_company_id,
        status=PurchaseOrderStatus.PENDING_BUYER_APPROVAL,
        has_discrepancy=True
    )
    db = MockSession()
    
    # Act & Assert
    with pytest.raises(AuthorizationError) as exc_info:
        approve_purchase_order_business_logic(po, user, db)
    
    assert "Only buyer can approve purchase order" in str(exc_info.value)


def test_create_purchase_order_business_logic_success():
    """Test successful PO creation."""
    
    # Arrange
    buyer_company_id = uuid4()
    seller_company_id = uuid4()
    product_id = uuid4()
    user = MockUser(company_id=buyer_company_id)
    db = MockSession()
    
    # Act
    result = create_purchase_order_business_logic(
        buyer_company_id=buyer_company_id,
        seller_company_id=seller_company_id,
        product_id=product_id,
        quantity=100.0,
        unit="kg",
        price_per_unit=10.0,
        current_user=user,
        db=db
    )
    
    # Assert
    assert result.buyer_company_id == buyer_company_id
    assert result.seller_company_id == seller_company_id
    assert result.product_id == product_id
    assert result.quantity == 100.0
    assert result.unit == "kg"
    assert result.price_per_unit == 10.0
    assert result.total_amount == 1000.0
    assert result.status == PurchaseOrderStatus.PENDING_CONFIRMATION
    assert result.created_at is not None


def test_create_purchase_order_business_logic_authorization_error():
    """Test PO creation with wrong user company."""
    
    # Arrange
    buyer_company_id = uuid4()
    wrong_company_id = uuid4()
    seller_company_id = uuid4()
    product_id = uuid4()
    user = MockUser(company_id=wrong_company_id)
    db = MockSession()
    
    # Act & Assert
    with pytest.raises(AuthorizationError) as exc_info:
        create_purchase_order_business_logic(
            buyer_company_id=buyer_company_id,
            seller_company_id=seller_company_id,
            product_id=product_id,
            quantity=100.0,
            unit="kg",
            price_per_unit=10.0,
            current_user=user,
            db=db
        )
    
    assert "User can only create POs for their own company" in str(exc_info.value)


def test_create_purchase_order_business_logic_validation_errors():
    """Test PO creation with validation errors."""
    
    # Arrange
    buyer_company_id = uuid4()
    seller_company_id = uuid4()
    product_id = uuid4()
    user = MockUser(company_id=buyer_company_id)
    db = MockSession()
    
    # Test invalid quantity
    with pytest.raises(ValidationError) as exc_info:
        create_purchase_order_business_logic(
            buyer_company_id=buyer_company_id,
            seller_company_id=seller_company_id,
            product_id=product_id,
            quantity=0.0,  # Invalid
            unit="kg",
            price_per_unit=10.0,
            current_user=user,
            db=db
        )
    assert "Quantity must be greater than zero" in str(exc_info.value)
    
    # Test invalid price
    with pytest.raises(ValidationError) as exc_info:
        create_purchase_order_business_logic(
            buyer_company_id=buyer_company_id,
            seller_company_id=seller_company_id,
            product_id=product_id,
            quantity=100.0,
            unit="kg",
            price_per_unit=0.0,  # Invalid
            current_user=user,
            db=db
        )
    assert "Price per unit must be greater than zero" in str(exc_info.value)
    
    # Test invalid unit
    with pytest.raises(ValidationError) as exc_info:
        create_purchase_order_business_logic(
            buyer_company_id=buyer_company_id,
            seller_company_id=seller_company_id,
            product_id=product_id,
            quantity=100.0,
            unit="",  # Invalid
            price_per_unit=10.0,
            current_user=user,
            db=db
        )
    assert "Unit is required" in str(exc_info.value)


def test_cancel_purchase_order_business_logic_success():
    """Test successful PO cancellation."""
    
    # Arrange
    buyer_company_id = uuid4()
    user = MockUser(company_id=buyer_company_id)
    po = MockPurchaseOrder(
        buyer_company_id=buyer_company_id,
        status=PurchaseOrderStatus.PENDING_CONFIRMATION
    )
    db = MockSession()
    
    # Act
    result = cancel_purchase_order_business_logic(po, user, db, "Customer request")
    
    # Assert
    assert result.status == PurchaseOrderStatus.CANCELLED
    assert result.cancelled_at is not None
    assert result.cancelled_by_user_id == user.id
    assert result.cancellation_reason == "Customer request"


def test_cancel_purchase_order_business_logic_authorization_error():
    """Test PO cancellation with wrong user company."""
    
    # Arrange
    buyer_company_id = uuid4()
    wrong_company_id = uuid4()
    user = MockUser(company_id=wrong_company_id)
    po = MockPurchaseOrder(
        buyer_company_id=buyer_company_id,
        status=PurchaseOrderStatus.PENDING_CONFIRMATION
    )
    db = MockSession()
    
    # Act & Assert
    with pytest.raises(AuthorizationError) as exc_info:
        cancel_purchase_order_business_logic(po, user, db)
    
    assert "Only buyer or seller can cancel purchase order" in str(exc_info.value)


def test_cancel_purchase_order_business_logic_state_transition_error():
    """Test PO cancellation with wrong status."""
    
    # Arrange
    buyer_company_id = uuid4()
    user = MockUser(company_id=buyer_company_id)
    po = MockPurchaseOrder(
        buyer_company_id=buyer_company_id,
        status=PurchaseOrderStatus.DELIVERED  # Cannot cancel delivered PO
    )
    db = MockSession()
    
    # Act & Assert
    with pytest.raises(StateTransitionError) as exc_info:
        cancel_purchase_order_business_logic(po, user, db)
    
    assert "Cannot cancel PO in status: delivered" in str(exc_info.value)


def test_update_purchase_order_business_logic_success():
    """Test successful PO update."""
    
    # Arrange
    buyer_company_id = uuid4()
    user = MockUser(company_id=buyer_company_id)
    po = MockPurchaseOrder(
        buyer_company_id=buyer_company_id,
        status=PurchaseOrderStatus.DRAFT,
        quantity=100.0,
        price_per_unit=10.0,
        total_amount=1000.0
    )
    updates = {
        'quantity': 150.0,
        'price_per_unit': 12.0
    }
    db = MockSession()
    
    # Act
    result = update_purchase_order_business_logic(po, updates, user, db)
    
    # Assert
    assert result.quantity == 150.0
    assert result.price_per_unit == 12.0
    assert result.total_amount == 1800.0  # 150 * 12
    assert result.updated_at is not None


def test_update_purchase_order_business_logic_authorization_error():
    """Test PO update with wrong user company."""
    
    # Arrange
    buyer_company_id = uuid4()
    wrong_company_id = uuid4()
    user = MockUser(company_id=wrong_company_id)
    po = MockPurchaseOrder(
        buyer_company_id=buyer_company_id,
        status=PurchaseOrderStatus.DRAFT
    )
    updates = {'quantity': 150.0}
    db = MockSession()
    
    # Act & Assert
    with pytest.raises(AuthorizationError) as exc_info:
        update_purchase_order_business_logic(po, updates, user, db)
    
    assert "Only buyer can update purchase order" in str(exc_info.value)


def test_update_purchase_order_business_logic_state_transition_error():
    """Test PO update with wrong status."""
    
    # Arrange
    buyer_company_id = uuid4()
    user = MockUser(company_id=buyer_company_id)
    po = MockPurchaseOrder(
        buyer_company_id=buyer_company_id,
        status=PurchaseOrderStatus.CONFIRMED  # Cannot update confirmed PO
    )
    updates = {'quantity': 150.0}
    db = MockSession()
    
    # Act & Assert
    with pytest.raises(StateTransitionError) as exc_info:
        update_purchase_order_business_logic(po, updates, user, db)
    
    assert "Cannot update PO in status: confirmed" in str(exc_info.value)
