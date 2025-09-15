"""
Simple audit logging service.
Replaces the over-engineered 6-class audit system.
"""
from datetime import datetime
from typing import Dict, Any, Optional
from uuid import UUID
from sqlalchemy.orm import Session

from app.core.logging import get_logger

logger = get_logger(__name__)


class SimpleAuditService:
    """Simple audit logging for purchase order events."""

    def __init__(self, db: Session):
        self.db = db

    def log_po_event(
        self,
        po_id: UUID,
        action: str,
        user_id: UUID,
        company_id: UUID,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Log a purchase order event.
        Simple structured logging instead of complex database audit.
        """
        event_data = {
            "event_type": "purchase_order_event",
            "po_id": str(po_id),
            "action": action,
            "user_id": str(user_id),
            "company_id": str(company_id),
            "timestamp": datetime.utcnow().isoformat(),
            "details": details or {}
        }

        # Simple structured logging
        logger.info("Purchase order event", **event_data)

    def log_po_creation(self, po_id: UUID, user_id: UUID, company_id: UUID):
        """Log purchase order creation."""
        self.log_po_event(po_id, "created", user_id, company_id)

    def log_po_update(self, po_id: UUID, user_id: UUID, company_id: UUID,
                      changes: Optional[Dict[str, Any]] = None):
        """Log purchase order update."""
        self.log_po_event(po_id, "updated", user_id, company_id, {"changes": changes})

    def log_po_confirmation(self, po_id: UUID, user_id: UUID, company_id: UUID):
        """Log purchase order confirmation."""
        self.log_po_event(po_id, "confirmed", user_id, company_id)

    def log_po_amendment(self, po_id: UUID, user_id: UUID, company_id: UUID,
                        amendment_type: str):
        """Log purchase order amendment."""
        self.log_po_event(po_id, "amended", user_id, company_id,
                         {"amendment_type": amendment_type})

    def log_access_attempt(self, po_id: UUID, user_id: UUID, company_id: UUID,
                          success: bool, reason: Optional[str] = None):
        """Log access attempt."""
        details = {"success": success}
        if reason:
            details["reason"] = reason

        self.log_po_event(po_id, "access_attempt", user_id, company_id, details)