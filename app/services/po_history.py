"""
Service for managing purchase order history and audit trail.
"""
import json
from typing import Dict, Any, Optional, List
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.purchase_order import PurchaseOrderHistory
from app.models.user import User
from app.core.logging import get_logger

logger = get_logger(__name__)


class POHistoryService:
    """Service for managing purchase order history and audit trail."""
    
    def __init__(self, db: Session):
        """Initialize the PO history service."""
        self.db = db
    
    def add_history_entry(
        self,
        purchase_order_id: UUID,
        action_type: str,
        action_description: str,
        user_id: UUID,
        company_id: UUID,
        changes_data: Optional[Dict[str, Any]] = None
    ) -> PurchaseOrderHistory:
        """
        Add a new history entry for a purchase order.
        
        Args:
            purchase_order_id: UUID of the purchase order
            action_type: Type of action (created, seller_confirmed, etc.)
            action_description: Human-readable description
            user_id: UUID of the user who performed the action
            company_id: UUID of the company the user belongs to
            changes_data: Optional dictionary of change details
            
        Returns:
            Created history entry
        """
        history_entry = PurchaseOrderHistory(
            purchase_order_id=purchase_order_id,
            action_type=action_type,
            action_description=action_description,
            user_id=user_id,
            company_id=company_id,
            changes_data=changes_data or {}
        )
        
        self.db.add(history_entry)
        self.db.flush()  # Get the ID without committing
        
        logger.info(
            "PO history entry added",
            po_id=str(purchase_order_id),
            action_type=action_type,
            user_id=str(user_id),
            company_id=str(company_id)
        )
        
        return history_entry
    
    def log_po_created(
        self,
        purchase_order_id: UUID,
        user_id: UUID,
        company_id: UUID,
        po_number: str
    ) -> PurchaseOrderHistory:
        """Log purchase order creation."""
        return self.add_history_entry(
            purchase_order_id=purchase_order_id,
            action_type="created",
            action_description=f"Purchase order {po_number} created",
            user_id=user_id,
            company_id=company_id
        )
    
    def log_seller_confirmation_with_discrepancies(
        self,
        purchase_order_id: UUID,
        user_id: UUID,
        company_id: UUID,
        po_number: str,
        discrepancies: List[Dict[str, Any]]
    ) -> PurchaseOrderHistory:
        """Log seller confirmation that has discrepancies requiring approval."""
        discrepancy_summary = ", ".join([
            f"{d['field']}: {d['original']} → {d['confirmed']}"
            for d in discrepancies
        ])
        
        return self.add_history_entry(
            purchase_order_id=purchase_order_id,
            action_type="seller_confirmed_with_discrepancies",
            action_description=f"Seller confirmed {po_number} with changes: {discrepancy_summary}",
            user_id=user_id,
            company_id=company_id,
            changes_data={"discrepancies": discrepancies}
        )
    
    def log_seller_confirmation_no_discrepancies(
        self,
        purchase_order_id: UUID,
        user_id: UUID,
        company_id: UUID,
        po_number: str
    ) -> PurchaseOrderHistory:
        """Log seller confirmation with no discrepancies."""
        return self.add_history_entry(
            purchase_order_id=purchase_order_id,
            action_type="seller_confirmed",
            action_description=f"Seller confirmed {po_number} with no changes",
            user_id=user_id,
            company_id=company_id
        )
    
    def log_buyer_approval(
        self,
        purchase_order_id: UUID,
        user_id: UUID,
        company_id: UUID,
        po_number: str,
        approved: bool,
        buyer_notes: Optional[str] = None
    ) -> PurchaseOrderHistory:
        """Log buyer approval or rejection of discrepancies."""
        action = "approved" if approved else "rejected"
        description = f"Buyer {action} changes to {po_number}"
        
        if buyer_notes:
            description += f" - {buyer_notes}"
        
        return self.add_history_entry(
            purchase_order_id=purchase_order_id,
            action_type=f"buyer_{action}",
            action_description=description,
            user_id=user_id,
            company_id=company_id,
            changes_data={"approved": approved, "buyer_notes": buyer_notes}
        )
    
    def log_po_confirmed(
        self,
        purchase_order_id: UUID,
        user_id: UUID,
        company_id: UUID,
        po_number: str
    ) -> PurchaseOrderHistory:
        """Log purchase order confirmation."""
        return self.add_history_entry(
            purchase_order_id=purchase_order_id,
            action_type="confirmed",
            action_description=f"Purchase order {po_number} confirmed and ready for fulfillment",
            user_id=user_id,
            company_id=company_id
        )
    
    def log_batch_created(
        self,
        purchase_order_id: UUID,
        user_id: UUID,
        company_id: UUID,
        po_number: str,
        batch_id: str
    ) -> PurchaseOrderHistory:
        """Log automatic batch creation."""
        return self.add_history_entry(
            purchase_order_id=purchase_order_id,
            action_type="batch_created",
            action_description=f"Batch {batch_id} automatically created for {po_number}",
            user_id=user_id,
            company_id=company_id,
            changes_data={"batch_id": batch_id}
        )
    
    def get_po_history(
        self,
        purchase_order_id: UUID,
        limit: Optional[int] = None
    ) -> List[PurchaseOrderHistory]:
        """
        Get history entries for a purchase order.
        
        Args:
            purchase_order_id: UUID of the purchase order
            limit: Optional limit on number of entries to return
            
        Returns:
            List of history entries ordered by creation time (newest first)
        """
        query = self.db.query(PurchaseOrderHistory).filter(
            PurchaseOrderHistory.purchase_order_id == purchase_order_id
        ).order_by(PurchaseOrderHistory.created_at.desc())
        
        if limit:
            query = query.limit(limit)
        
        return query.all()
