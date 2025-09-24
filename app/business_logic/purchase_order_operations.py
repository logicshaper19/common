"""
Purchase Order Business Logic Operations

Pure business logic functions for purchase order operations.
These functions contain no HTTP concerns, no database complexity,
and are easy to test and reuse.
"""
from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.purchase_order import PurchaseOrder
from app.models.user import User
from app.business_logic.exceptions import (
    BusinessLogicError,
    ValidationError,
    AuthorizationError,
    StateTransitionError
)


class PurchaseOrderStatus:
    """Purchase Order status constants."""
    DRAFT = "draft"
    PENDING = "pending"
    PENDING_CONFIRMATION = "pending_confirmation"
    CONFIRMED = "confirmed"
    PENDING_BUYER_APPROVAL = "pending_buyer_approval"
    APPROVED = "approved"
    IN_TRANSIT = "in_transit"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class ConfirmationRequest:
    """Request object for PO confirmation."""
    def __init__(self, quantity: float, discrepancy_reason: Optional[str] = None):
        self.quantity = quantity
        self.discrepancy_reason = discrepancy_reason


def confirm_purchase_order_business_logic(
    po: PurchaseOrder,
    confirmation: ConfirmationRequest,
    current_user: User,
    db: Session
) -> PurchaseOrder:
    """
    Pure business logic function for confirming a purchase order.
    
    This function contains only business rules and state changes.
    No HTTP concerns, no database complexity - easy to test.
    """
    
    # Business validation
    if po.seller_company_id != current_user.company_id:
        raise AuthorizationError("Only seller can confirm purchase order")
    
    if po.status != PurchaseOrderStatus.PENDING_CONFIRMATION:
        raise StateTransitionError(f"Cannot confirm PO in status: {po.status}")
    
    if confirmation.quantity <= 0:
        raise ValidationError("Confirmed quantity must be greater than zero")
    
    # State changes
    po.status = PurchaseOrderStatus.CONFIRMED
    po.confirmed_quantity = confirmation.quantity
    po.confirmed_at = datetime.utcnow()
    po.confirmed_by_user_id = current_user.id
    
    # Handle discrepancies
    if po.quantity != confirmation.quantity:
        po.has_discrepancy = True
        po.discrepancy_reason = confirmation.discrepancy_reason
        po.status = PurchaseOrderStatus.PENDING_BUYER_APPROVAL
    
    return po


def approve_purchase_order_business_logic(
    po: PurchaseOrder,
    current_user: User,
    db: Session
) -> PurchaseOrder:
    """
    Pure business logic function for approving a purchase order.
    
    This handles buyer approval of seller confirmations with discrepancies.
    """
    
    # Business validation
    if po.buyer_company_id != current_user.company_id:
        raise AuthorizationError("Only buyer can approve purchase order")
    
    if po.status != PurchaseOrderStatus.PENDING_BUYER_APPROVAL:
        raise StateTransitionError(f"Cannot approve PO in status: {po.status}")
    
    if not po.has_discrepancy:
        raise ValidationError("PO has no discrepancy to approve")
    
    # State changes
    po.status = PurchaseOrderStatus.APPROVED
    po.buyer_approved_at = datetime.utcnow()
    po.buyer_approval_user_id = current_user.id
    po.has_discrepancy = False
    
    return po


def create_purchase_order_business_logic(
    buyer_company_id: UUID,
    seller_company_id: UUID,
    product_id: UUID,
    quantity: float,
    unit: str,
    price_per_unit: float,
    current_user: User,
    db: Session
) -> PurchaseOrder:
    """
    Pure business logic function for creating a purchase order.
    
    This handles the business rules for PO creation.
    """
    
    # Business validation
    if current_user.company_id != buyer_company_id:
        raise AuthorizationError("User can only create POs for their own company")
    
    if quantity <= 0:
        raise ValidationError("Quantity must be greater than zero")
    
    if price_per_unit <= 0:
        raise ValidationError("Price per unit must be greater than zero")
    
    if not unit or len(unit.strip()) == 0:
        raise ValidationError("Unit is required")
    
    # Create PO with business rules
    po = PurchaseOrder(
        buyer_company_id=buyer_company_id,
        seller_company_id=seller_company_id,
        product_id=product_id,
        quantity=quantity,
        unit=unit,
        price_per_unit=price_per_unit,
        total_amount=quantity * price_per_unit,
        status=PurchaseOrderStatus.PENDING_CONFIRMATION,
        created_at=datetime.utcnow()
    )
    
    return po


def cancel_purchase_order_business_logic(
    po: PurchaseOrder,
    current_user: User,
    db: Session,
    reason: Optional[str] = None
) -> PurchaseOrder:
    """
    Pure business logic function for cancelling a purchase order.
    
    This handles the business rules for PO cancellation.
    """
    
    # Business validation
    if po.buyer_company_id != current_user.company_id and po.seller_company_id != current_user.company_id:
        raise AuthorizationError("Only buyer or seller can cancel purchase order")
    
    if po.status in [PurchaseOrderStatus.DELIVERED, PurchaseOrderStatus.CANCELLED]:
        raise StateTransitionError(f"Cannot cancel PO in status: {po.status}")
    
    # State changes
    po.status = PurchaseOrderStatus.CANCELLED
    po.cancelled_at = datetime.utcnow()
    po.cancelled_by_user_id = current_user.id
    if reason:
        po.cancellation_reason = reason
    
    return po


def update_purchase_order_business_logic(
    po: PurchaseOrder,
    updates: dict,
    current_user: User,
    db: Session
) -> PurchaseOrder:
    """
    Pure business logic function for updating a purchase order.
    
    This handles the business rules for PO updates.
    """
    
    # Business validation
    if po.buyer_company_id != current_user.company_id:
        raise AuthorizationError("Only buyer can update purchase order")
    
    if po.status not in [PurchaseOrderStatus.DRAFT, PurchaseOrderStatus.PENDING]:
        raise StateTransitionError(f"Cannot update PO in status: {po.status}")
    
    # Apply updates with business rules
    if 'quantity' in updates:
        if updates['quantity'] <= 0:
            raise ValidationError("Quantity must be greater than zero")
        po.quantity = updates['quantity']
        po.total_amount = po.quantity * po.price_per_unit
    
    if 'price_per_unit' in updates:
        if updates['price_per_unit'] <= 0:
            raise ValidationError("Price per unit must be greater than zero")
        po.price_per_unit = updates['price_per_unit']
        po.total_amount = po.quantity * po.price_per_unit
    
    if 'unit' in updates:
        if not updates['unit'] or len(updates['unit'].strip()) == 0:
            raise ValidationError("Unit is required")
        po.unit = updates['unit']
    
    po.updated_at = datetime.utcnow()
    
    return po
