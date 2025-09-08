"""
Amendment validation logic.
"""
from typing import Optional, List
from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.models.amendment import Amendment
from app.models.purchase_order import PurchaseOrder
from app.schemas.amendment import AmendmentCreate
from app.services.amendments.exceptions import (
    AmendmentValidationError,
    AmendmentPermissionError,
    AmendmentStatusError,
    AmendmentExpiredError
)
from app.core.logging import get_logger

logger = get_logger(__name__)


class AmendmentValidator:
    """Validates amendment operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def validate_amendment_creation(
        self,
        amendment_data: AmendmentCreate,
        purchase_order: PurchaseOrder,
        current_user_company_id: UUID
    ) -> None:
        """
        Validate amendment creation.
        
        Args:
            amendment_data: Amendment creation data
            purchase_order: Purchase order being amended
            current_user_company_id: Current user's company ID
            
        Raises:
            AmendmentValidationError: If validation fails
            AmendmentPermissionError: If user lacks permission
            AmendmentStatusError: If PO status doesn't allow amendments
        """
        # Validate user has permission to create amendments for this PO
        self._validate_amendment_permissions(purchase_order, current_user_company_id)
        
        # Validate PO status allows amendments
        self._validate_po_status_for_amendment(purchase_order, amendment_data.amendment_type)
        
        # Validate no conflicting pending amendments
        self._validate_no_conflicting_amendments(purchase_order, amendment_data)
        
        # Validate changes are valid
        self._validate_amendment_changes(amendment_data, purchase_order)
    
    def validate_amendment_update(
        self,
        amendment: Amendment,
        current_user_company_id: UUID
    ) -> None:
        """
        Validate amendment update.
        
        Args:
            amendment: Amendment to update
            current_user_company_id: Current user's company ID
            
        Raises:
            AmendmentPermissionError: If user lacks permission
            AmendmentStatusError: If amendment cannot be updated
            AmendmentExpiredError: If amendment has expired
        """
        # Check if amendment has expired
        if amendment.is_expired():
            raise AmendmentExpiredError(
                f"Amendment {amendment.amendment_number} has expired"
            )
        
        # Only the proposer can update pending amendments
        if amendment.proposed_by_company_id != current_user_company_id:
            raise AmendmentPermissionError(
                "Only the proposing company can update amendments"
            )
        
        # Can only update pending amendments
        if amendment.status != 'pending':
            raise AmendmentStatusError(
                f"Cannot update amendment in {amendment.status} status",
                current_status=amendment.status,
                allowed_statuses=['pending']
            )
    
    def validate_amendment_approval(
        self,
        amendment: Amendment,
        current_user_company_id: UUID
    ) -> None:
        """
        Validate amendment approval.
        
        Args:
            amendment: Amendment to approve
            current_user_company_id: Current user's company ID
            
        Raises:
            AmendmentPermissionError: If user lacks permission
            AmendmentStatusError: If amendment cannot be approved
            AmendmentExpiredError: If amendment has expired
        """
        # Check if amendment has expired
        if amendment.is_expired():
            raise AmendmentExpiredError(
                f"Amendment {amendment.amendment_number} has expired"
            )
        
        # Only the approval company can approve
        if amendment.requires_approval_from_company_id != current_user_company_id:
            raise AmendmentPermissionError(
                "Only the approval company can approve amendments"
            )
        
        # Can only approve pending amendments
        if amendment.status != 'pending':
            raise AmendmentStatusError(
                f"Cannot approve amendment in {amendment.status} status",
                current_status=amendment.status,
                allowed_statuses=['pending']
            )
    
    def _validate_amendment_permissions(
        self,
        purchase_order: PurchaseOrder,
        current_user_company_id: UUID
    ) -> None:
        """Validate user has permission to create amendments for this PO."""
        if current_user_company_id not in [
            purchase_order.buyer_company_id,
            purchase_order.seller_company_id
        ]:
            raise AmendmentPermissionError(
                "Only buyer or seller companies can create amendments"
            )
    
    def _validate_po_status_for_amendment(
        self,
        purchase_order: PurchaseOrder,
        amendment_type
    ) -> None:
        """Validate PO status allows the requested amendment type."""
        from app.services.amendments.domain.enums import AmendmentType
        
        # Pre-confirmation amendments
        pre_confirmation_types = [
            AmendmentType.QUANTITY_CHANGE,
            AmendmentType.PRICE_CHANGE,
            AmendmentType.DELIVERY_DATE_CHANGE,
            AmendmentType.DELIVERY_LOCATION_CHANGE,
            AmendmentType.COMPOSITION_CHANGE
        ]
        
        # Post-confirmation amendments
        post_confirmation_types = [
            AmendmentType.RECEIVED_QUANTITY_ADJUSTMENT,
            AmendmentType.DELIVERY_CONFIRMATION
        ]
        
        if amendment_type in pre_confirmation_types:
            if purchase_order.status not in ['draft', 'pending']:
                raise AmendmentStatusError(
                    f"Cannot create {amendment_type.value} amendment for PO in {purchase_order.status} status",
                    current_status=purchase_order.status,
                    allowed_statuses=['draft', 'pending']
                )
        
        elif amendment_type in post_confirmation_types:
            if purchase_order.status not in ['confirmed', 'in_transit', 'shipped', 'delivered']:
                raise AmendmentStatusError(
                    f"Cannot create {amendment_type.value} amendment for PO in {purchase_order.status} status",
                    current_status=purchase_order.status,
                    allowed_statuses=['confirmed', 'in_transit', 'shipped', 'delivered']
                )
    
    def _validate_no_conflicting_amendments(
        self,
        purchase_order: PurchaseOrder,
        amendment_data: AmendmentCreate
    ) -> None:
        """Validate no conflicting pending amendments exist."""
        from app.services.amendments.domain.enums import AmendmentType
        
        # Check for pending amendments of the same type
        existing_amendments = self.db.query(Amendment).filter(
            Amendment.purchase_order_id == purchase_order.id,
            Amendment.status == 'pending',
            Amendment.amendment_type == amendment_data.amendment_type.value
        ).all()
        
        if existing_amendments:
            raise AmendmentValidationError(
                f"A pending {amendment_data.amendment_type.value} amendment already exists for this purchase order"
            )
        
        # Special validation for quantity adjustments (only one at a time)
        if amendment_data.amendment_type == AmendmentType.RECEIVED_QUANTITY_ADJUSTMENT:
            any_pending = self.db.query(Amendment).filter(
                Amendment.purchase_order_id == purchase_order.id,
                Amendment.status == 'pending'
            ).first()
            
            if any_pending:
                raise AmendmentValidationError(
                    "Cannot create quantity adjustment while other amendments are pending"
                )
    
    def _validate_amendment_changes(
        self,
        amendment_data: AmendmentCreate,
        purchase_order: PurchaseOrder
    ) -> None:
        """Validate the proposed changes are valid."""
        for change in amendment_data.changes:
            field_name = change.field_name
            new_value = change.new_value
            
            # Validate field exists on purchase order
            if not hasattr(purchase_order, field_name):
                raise AmendmentValidationError(
                    f"Invalid field name: {field_name}"
                )
            
            # Validate specific field constraints
            if field_name == 'quantity' and new_value <= 0:
                raise AmendmentValidationError(
                    "Quantity must be greater than zero"
                )
            
            if field_name == 'unit_price' and new_value <= 0:
                raise AmendmentValidationError(
                    "Unit price must be greater than zero"
                )
            
            if field_name == 'quantity_received' and new_value < 0:
                raise AmendmentValidationError(
                    "Received quantity cannot be negative"
                )
            
            # Validate composition if applicable
            if field_name == 'composition' and new_value:
                if not isinstance(new_value, dict):
                    raise AmendmentValidationError(
                        "Composition must be a dictionary"
                    )
                
                total = sum(new_value.values())
                if not (99.0 <= total <= 101.0):
                    raise AmendmentValidationError(
                        "Composition percentages must sum to approximately 100%"
                    )
