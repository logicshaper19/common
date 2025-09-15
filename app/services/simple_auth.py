"""
Simple authentication and authorization service.
Replaces the over-engineered data access control system.
"""
from typing import Optional
from uuid import UUID
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models.purchase_order import PurchaseOrder
from app.models.user import User
from app.core.logging import get_logger

logger = get_logger(__name__)


class SimpleAuthService:
    """Simple authentication service for purchase order access."""

    def __init__(self, db: Session):
        self.db = db

    def check_po_access(self, user: User, po_id: UUID) -> bool:
        """
        Simple access check: users can access POs where their company
        is either buyer or seller.
        """
        po = self.db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()

        if not po:
            return False

        # Simple rule: access if user's company is buyer or seller
        return (user.company_id == po.buyer_company_id or
                user.company_id == po.seller_company_id)

    def require_po_access(self, user: User, po_id: UUID) -> PurchaseOrder:
        """Check access and return PO, or raise 403."""
        po = self.db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()

        if not po:
            raise HTTPException(status_code=404, detail="Purchase order not found")

        if not (user.company_id == po.buyer_company_id or
                user.company_id == po.seller_company_id):
            raise HTTPException(status_code=403, detail="Access denied")

        return po

    def filter_pos_by_access(self, user: User, query):
        """Filter query to only include accessible POs."""
        return query.filter(
            (PurchaseOrder.buyer_company_id == user.company_id) |
            (PurchaseOrder.seller_company_id == user.company_id)
        )