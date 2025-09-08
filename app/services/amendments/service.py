"""
Amendment service for managing purchase order amendments.
"""
from typing import Optional, List, Tuple, Dict, Any
from uuid import UUID, uuid4
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session

from app.models.amendment import Amendment
from app.models.purchase_order import PurchaseOrder
from app.schemas.amendment import (
    AmendmentCreate, 
    AmendmentUpdate, 
    AmendmentApproval,
    AmendmentFilter,
    ReceivedQuantityAdjustment,
    ProposeChangesRequest
)
from app.services.amendments.repository import AmendmentRepository
from app.services.amendments.validators import AmendmentValidator
from app.services.amendments.impact_assessor import AmendmentImpactAssessor
from app.services.amendments.number_generator import AmendmentNumberGenerator
from app.services.amendments.exceptions import (
    AmendmentError,
    AmendmentNotFoundError,
    AmendmentValidationError,
    AmendmentPermissionError,
    AmendmentStatusError
)
from app.services.purchase_order import PurchaseOrderService
from app.core.logging import get_logger

logger = get_logger(__name__)


class AmendmentService:
    """Main service for amendment operations."""
    
    def __init__(self, db: Session):
        self.db = db
        self.repository = AmendmentRepository(db)
        self.validator = AmendmentValidator(db)
        self.impact_assessor = AmendmentImpactAssessor()
        self.number_generator = AmendmentNumberGenerator(db)
        self.po_service = PurchaseOrderService(db)
    
    def create_amendment(
        self, 
        amendment_data: AmendmentCreate,
        current_user_company_id: UUID
    ) -> Amendment:
        """
        Create a new amendment.
        
        Args:
            amendment_data: Amendment creation data
            current_user_company_id: Current user's company ID
            
        Returns:
            Created amendment
            
        Raises:
            AmendmentValidationError: If validation fails
            AmendmentError: If creation fails
        """
        logger.info(
            "Creating amendment",
            po_id=str(amendment_data.purchase_order_id),
            amendment_type=amendment_data.amendment_type.value,
            company_id=str(current_user_company_id)
        )
        
        try:
            # Get the purchase order
            purchase_order = self.po_service.get_purchase_order_by_id(
                str(amendment_data.purchase_order_id)
            )
            if not purchase_order:
                raise AmendmentValidationError("Purchase order not found")
            
            # Validate amendment creation
            self.validator.validate_amendment_creation(
                amendment_data, 
                purchase_order, 
                current_user_company_id
            )
            
            # Generate amendment number
            amendment_number = self.number_generator.generate(purchase_order.po_number)
            
            # Determine approval requirements
            approval_company_id = self._determine_approval_company(
                purchase_order, 
                current_user_company_id
            )
            
            # Calculate expiration
            expires_at = None
            if amendment_data.expires_in_hours:
                expires_at = datetime.now(timezone.utc) + timedelta(
                    hours=amendment_data.expires_in_hours
                )
            
            # Assess impact
            impact_assessment = self.impact_assessor.assess_amendment_impact(
                amendment_data, 
                purchase_order
            )
            
            # Prepare amendment data
            creation_data = {
                'id': uuid4(),
                'purchase_order_id': amendment_data.purchase_order_id,
                'amendment_number': amendment_number,
                'amendment_type': amendment_data.amendment_type.value,
                'status': 'pending',
                'reason': amendment_data.reason.value,
                'priority': amendment_data.priority.value,
                'changes': [change.dict() for change in amendment_data.changes],
                'proposed_by_company_id': current_user_company_id,
                'requires_approval_from_company_id': approval_company_id,
                'proposed_at': datetime.now(timezone.utc),
                'expires_at': expires_at,
                'notes': amendment_data.notes,
                'supporting_documents': amendment_data.supporting_documents,
                'impact_assessment': impact_assessment.dict() if impact_assessment else None,
                'requires_erp_sync': False,  # Phase 1: Manual sync
            }
            
            # Create amendment
            amendment = self.repository.create(creation_data)
            
            logger.info(
                "Amendment created successfully",
                amendment_id=str(amendment.id),
                amendment_number=amendment_number,
                po_id=str(amendment_data.purchase_order_id)
            )
            
            return amendment
            
        except AmendmentValidationError:
            raise
        except Exception as e:
            logger.error("Failed to create amendment", error=str(e))
            raise AmendmentError(f"Failed to create amendment: {str(e)}")
    
    def get_amendment_by_id(self, amendment_id: str) -> Optional[Amendment]:
        """
        Get amendment by ID.
        
        Args:
            amendment_id: Amendment UUID string
            
        Returns:
            Amendment or None
        """
        try:
            uuid_obj = UUID(amendment_id)
            return self.repository.get_by_id(uuid_obj)
        except ValueError:
            return None
    
    def update_amendment(
        self,
        amendment_id: str,
        update_data: AmendmentUpdate,
        current_user_company_id: UUID
    ) -> Amendment:
        """
        Update an amendment.
        
        Args:
            amendment_id: Amendment UUID string
            update_data: Update data
            current_user_company_id: Current user's company ID
            
        Returns:
            Updated amendment
            
        Raises:
            AmendmentNotFoundError: If amendment not found
            AmendmentPermissionError: If user lacks permission
            AmendmentStatusError: If amendment cannot be updated
        """
        amendment = self.get_amendment_by_id(amendment_id)
        if not amendment:
            raise AmendmentNotFoundError(f"Amendment {amendment_id} not found")
        
        # Validate update permissions
        self.validator.validate_amendment_update(
            amendment, 
            current_user_company_id
        )
        
        # Prepare update data
        update_dict = {}
        if update_data.priority is not None:
            update_dict['priority'] = update_data.priority.value
        if update_data.notes is not None:
            update_dict['notes'] = update_data.notes
        if update_data.supporting_documents is not None:
            update_dict['supporting_documents'] = update_data.supporting_documents
        if update_data.expires_in_hours is not None:
            update_dict['expires_at'] = datetime.now(timezone.utc) + timedelta(
                hours=update_data.expires_in_hours
            )
        
        return self.repository.update(amendment, update_dict)
    
    def approve_amendment(
        self,
        amendment_id: str,
        approval_data: AmendmentApproval,
        current_user_company_id: UUID
    ) -> Amendment:
        """
        Approve or reject an amendment.
        
        Args:
            amendment_id: Amendment UUID string
            approval_data: Approval data
            current_user_company_id: Current user's company ID
            
        Returns:
            Updated amendment
            
        Raises:
            AmendmentNotFoundError: If amendment not found
            AmendmentPermissionError: If user lacks permission
            AmendmentStatusError: If amendment cannot be approved
        """
        amendment = self.get_amendment_by_id(amendment_id)
        if not amendment:
            raise AmendmentNotFoundError(f"Amendment {amendment_id} not found")
        
        # Validate approval permissions
        self.validator.validate_amendment_approval(
            amendment, 
            current_user_company_id
        )
        
        # Update amendment status
        update_data = {
            'status': 'approved' if approval_data.approved else 'rejected',
            'approval_notes': approval_data.approval_notes,
            'approved_at': datetime.now(timezone.utc)
        }
        
        amendment = self.repository.update(amendment, update_data)
        
        # If approved, apply the amendment
        if approval_data.approved:
            self._apply_amendment(amendment)
        
        logger.info(
            "Amendment approval processed",
            amendment_id=str(amendment.id),
            approved=approval_data.approved,
            company_id=str(current_user_company_id)
        )
        
        return amendment
    
    def list_amendments(
        self,
        filters: AmendmentFilter,
        current_user_company_id: UUID
    ) -> Tuple[List[Amendment], int]:
        """
        List amendments with filters and pagination.
        
        Args:
            filters: Filter criteria
            current_user_company_id: Current user's company ID
            
        Returns:
            Tuple of (amendments list, total count)
        """
        return self.repository.list_with_filters(filters, current_user_company_id)
    
    def _determine_approval_company(
        self, 
        purchase_order: PurchaseOrder, 
        proposing_company_id: UUID
    ) -> UUID:
        """Determine which company needs to approve the amendment."""
        if proposing_company_id == purchase_order.buyer_company_id:
            return purchase_order.seller_company_id
        else:
            return purchase_order.buyer_company_id
    
    def _apply_amendment(self, amendment: Amendment) -> None:
        """Apply an approved amendment to the purchase order."""
        logger.info(
            "Applying amendment to purchase order",
            amendment_id=str(amendment.id),
            po_id=str(amendment.purchase_order_id)
        )
        
        try:
            # Get the purchase order
            purchase_order = self.po_service.get_purchase_order_by_id(
                str(amendment.purchase_order_id)
            )
            if not purchase_order:
                raise AmendmentError("Purchase order not found")
            
            # Apply changes based on amendment type
            changes_applied = []
            for change in amendment.changes:
                if isinstance(change, dict):
                    field_name = change.get('field_name')
                    new_value = change.get('new_value')
                    
                    if hasattr(purchase_order, field_name):
                        old_value = getattr(purchase_order, field_name)
                        setattr(purchase_order, field_name, new_value)
                        changes_applied.append(f"{field_name}: {old_value} → {new_value}")
            
            # Update amendment status
            self.repository.update(amendment, {
                'status': 'applied',
                'applied_at': datetime.now(timezone.utc)
            })
            
            # Commit changes
            self.db.commit()
            
            logger.info(
                "Amendment applied successfully",
                amendment_id=str(amendment.id),
                changes_applied=changes_applied
            )
            
        except Exception as e:
            self.db.rollback()
            logger.error(
                "Failed to apply amendment",
                amendment_id=str(amendment.id),
                error=str(e)
            )
            raise AmendmentError(f"Failed to apply amendment: {str(e)}")

    # Phase 1 specific methods for quick operations
    def adjust_received_quantity(
        self,
        purchase_order_id: str,
        adjustment_data: ReceivedQuantityAdjustment,
        current_user_company_id: UUID
    ) -> Amendment:
        """
        Quick adjustment of received quantity (Phase 1 post-confirmation).

        Args:
            purchase_order_id: Purchase order UUID string
            adjustment_data: Quantity adjustment data
            current_user_company_id: Current user's company ID

        Returns:
            Created amendment
        """
        from app.services.amendments.domain.enums import AmendmentType, AmendmentPriority
        from app.schemas.amendment import AmendmentChangeCreate
        from app.schemas.purchase_order import PurchaseOrderStatus

        logger.info(
            "Adjusting received quantity",
            po_id=purchase_order_id,
            quantity_received=str(adjustment_data.quantity_received),
            company_id=str(current_user_company_id)
        )

        # Get purchase order
        purchase_order = self.po_service.get_purchase_order_by_id(purchase_order_id)
        if not purchase_order:
            raise AmendmentValidationError("Purchase order not found")

        # Validate this is a post-confirmation adjustment
        if purchase_order.status not in ['shipped', 'delivered']:
            raise AmendmentStatusError(
                "Received quantity can only be adjusted for shipped or delivered orders"
            )

        # Only buyer can adjust received quantity
        if current_user_company_id != purchase_order.buyer_company_id:
            raise AmendmentPermissionError(
                "Only the buyer can adjust received quantity"
            )

        # Create amendment for the adjustment
        amendment_create = AmendmentCreate(
            purchase_order_id=UUID(purchase_order_id),
            amendment_type=AmendmentType.RECEIVED_QUANTITY_ADJUSTMENT,
            reason=adjustment_data.reason,
            priority=AmendmentPriority.HIGH,  # Quantity adjustments are high priority
            changes=[
                AmendmentChangeCreate(
                    field_name="quantity_received",
                    old_value=purchase_order.quantity_received,
                    new_value=adjustment_data.quantity_received,
                    reason="Actual quantity received differs from ordered quantity"
                )
            ],
            notes=adjustment_data.notes,
            expires_in_hours=None  # No expiration for quantity adjustments
        )

        # Create and auto-approve the amendment (buyer's adjustment)
        amendment = self.create_amendment(amendment_create, current_user_company_id)

        # Auto-approve since this is a buyer's quantity adjustment
        approval = AmendmentApproval(
            approved=True,
            approval_notes="Auto-approved quantity adjustment by buyer"
        )

        amendment = self.approve_amendment(
            str(amendment.id),
            approval,
            current_user_company_id
        )

        logger.info(
            "Received quantity adjusted successfully",
            amendment_id=str(amendment.id),
            po_id=purchase_order_id,
            new_quantity=str(adjustment_data.quantity_received)
        )

        return amendment

    def propose_changes(
        self,
        purchase_order_id: str,
        changes_data: ProposeChangesRequest,
        current_user_company_id: UUID
    ) -> Amendment:
        """
        Propose changes to a purchase order (Phase 1 pre-confirmation).

        Args:
            purchase_order_id: Purchase order UUID string
            changes_data: Proposed changes data
            current_user_company_id: Current user's company ID

        Returns:
            Created amendment
        """
        from app.services.amendments.domain.enums import AmendmentType
        from app.schemas.amendment import AmendmentChangeCreate

        logger.info(
            "Proposing changes to purchase order",
            po_id=purchase_order_id,
            company_id=str(current_user_company_id)
        )

        # Get purchase order
        purchase_order = self.po_service.get_purchase_order_by_id(purchase_order_id)
        if not purchase_order:
            raise AmendmentValidationError("Purchase order not found")

        # Validate this is a pre-confirmation change
        if purchase_order.status not in ['draft', 'pending']:
            raise AmendmentStatusError(
                "Changes can only be proposed for draft or pending orders"
            )

        # Build list of changes
        changes = []

        if changes_data.quantity is not None:
            changes.append(AmendmentChangeCreate(
                field_name="quantity",
                old_value=purchase_order.quantity,
                new_value=changes_data.quantity,
                reason="Quantity adjustment requested"
            ))

        if changes_data.unit_price is not None:
            changes.append(AmendmentChangeCreate(
                field_name="unit_price",
                old_value=purchase_order.unit_price,
                new_value=changes_data.unit_price,
                reason="Price adjustment requested"
            ))

        if changes_data.delivery_date is not None:
            changes.append(AmendmentChangeCreate(
                field_name="delivery_date",
                old_value=purchase_order.delivery_date,
                new_value=changes_data.delivery_date,
                reason="Delivery date change requested"
            ))

        if changes_data.delivery_location is not None:
            changes.append(AmendmentChangeCreate(
                field_name="delivery_location",
                old_value=purchase_order.delivery_location,
                new_value=changes_data.delivery_location,
                reason="Delivery location change requested"
            ))

        if changes_data.composition is not None:
            changes.append(AmendmentChangeCreate(
                field_name="composition",
                old_value=purchase_order.composition,
                new_value=changes_data.composition,
                reason="Composition change requested"
            ))

        if not changes:
            raise AmendmentValidationError("At least one change must be specified")

        # Determine amendment type based on primary change
        amendment_type = AmendmentType.QUANTITY_CHANGE
        if changes_data.unit_price is not None:
            amendment_type = AmendmentType.PRICE_CHANGE
        elif changes_data.delivery_date is not None:
            amendment_type = AmendmentType.DELIVERY_DATE_CHANGE
        elif changes_data.delivery_location is not None:
            amendment_type = AmendmentType.DELIVERY_LOCATION_CHANGE
        elif changes_data.composition is not None:
            amendment_type = AmendmentType.COMPOSITION_CHANGE

        # Create amendment
        amendment_create = AmendmentCreate(
            purchase_order_id=UUID(purchase_order_id),
            amendment_type=amendment_type,
            reason=changes_data.reason,
            priority=changes_data.priority,
            changes=changes,
            notes=changes_data.notes,
            expires_in_hours=changes_data.expires_in_hours
        )

        amendment = self.create_amendment(amendment_create, current_user_company_id)

        logger.info(
            "Changes proposed successfully",
            amendment_id=str(amendment.id),
            po_id=purchase_order_id,
            change_count=len(changes)
        )

        return amendment
