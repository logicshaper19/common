"""
Delivery API endpoints for purchase orders.
Simple endpoints that work with existing PurchaseOrder model fields.
"""
from typing import Optional
from uuid import UUID
from datetime import datetime
from enum import Enum
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.core.auth import get_current_user_sync, CurrentUser
from app.core.simple_auth import can_access_purchase_order
from app.core.logging import get_logger
from app.models.purchase_order import PurchaseOrder

logger = get_logger(__name__)

router = APIRouter(prefix="/purchase-orders", tags=["deliveries"])

# Delivery status enum for validation
class DeliveryStatus(str, Enum):
    PENDING = "pending"
    IN_TRANSIT = "in_transit"
    DELIVERED = "delivered"
    FAILED = "failed"

# Helper function to get PO with auth check
def get_po_with_auth_check(po_id: UUID, current_user: CurrentUser, db: Session) -> PurchaseOrder:
    """Get purchase order with authentication check."""
    po = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
    if not po:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Purchase order not found"
        )
    
    if not can_access_purchase_order(current_user, po):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Access denied: You can only access purchase orders involving your company"
        )
    
    return po

# Valid status transitions
VALID_TRANSITIONS = {
    DeliveryStatus.PENDING: [DeliveryStatus.IN_TRANSIT, DeliveryStatus.FAILED],
    DeliveryStatus.IN_TRANSIT: [DeliveryStatus.DELIVERED, DeliveryStatus.FAILED],
    DeliveryStatus.FAILED: [DeliveryStatus.IN_TRANSIT],  # Can retry from failed
    DeliveryStatus.DELIVERED: []  # Final state, no transitions allowed
}

def validate_status_transition(current_status: str, new_status: DeliveryStatus) -> bool:
    """Validate if the status transition is allowed."""
    if not current_status:
        current_status = DeliveryStatus.PENDING
    
    try:
        current_enum = DeliveryStatus(current_status)
        return new_status in VALID_TRANSITIONS.get(current_enum, [])
    except ValueError:
        # If current status is invalid, allow any transition
        return True

def parse_delivery_note(line: str) -> tuple[str, str]:
    """Safely parse delivery note with timestamp."""
    bracket_pos = line.find(']')
    if bracket_pos > 0:
        timestamp_str = line[1:bracket_pos]
        note = line[bracket_pos + 1:].strip()
        return timestamp_str, note
    else:
        # Handle malformed line
        return "Unknown", line.strip()

# Simple schemas
class DeliveryStatusUpdate(BaseModel):
    status: DeliveryStatus
    notes: Optional[str] = None

class DeliveryResponse(BaseModel):
    delivery_date: str
    delivery_location: str
    delivery_status: str
    delivered_at: Optional[str] = None
    delivery_notes: Optional[str] = None
    delivery_confirmed_by: Optional[str] = None
    
    class Config:
        from_attributes = True

@router.get("/{po_id}/delivery", response_model=DeliveryResponse)
def get_delivery(
    po_id: UUID,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user_sync)
):
    """Get delivery information for a purchase order."""
    try:
        po = get_po_with_auth_check(po_id, current_user, db)
        
        return DeliveryResponse(
            delivery_date=str(po.delivery_date) if po.delivery_date else "",
            delivery_location=po.delivery_location or "",
            delivery_status=po.delivery_status or "pending",
            delivered_at=po.delivered_at.isoformat() if po.delivered_at else None,
            delivery_notes=po.delivery_notes,
            delivery_confirmed_by=str(po.delivery_confirmed_by) if po.delivery_confirmed_by else None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving delivery info: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve delivery information"
        )

@router.patch("/{po_id}/delivery", response_model=DeliveryResponse)
def update_delivery(
    po_id: UUID,
    update: DeliveryStatusUpdate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user_sync)
):
    """Update delivery status for a purchase order."""
    try:
        po = get_po_with_auth_check(po_id, current_user, db)
        
        # Validate status transition
        if not validate_status_transition(po.delivery_status, update.status):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid status transition. Please check the current status and try again."
            )
        
        # Update delivery status
        po.delivery_status = update.status.value
        
        # Handle delivered status
        if update.status == DeliveryStatus.DELIVERED:
            po.delivered_at = datetime.utcnow()
            po.delivery_confirmed_by = current_user.id
            # Update main PO status if appropriate
            if po.status in ["confirmed", "shipped"]:
                po.status = "delivered"
        
        # Add notes with timestamp
        if update.notes:
            timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M")
            new_note = f"[{timestamp}] {update.notes}"
            po.delivery_notes = f"{po.delivery_notes or ''}\n{new_note}".strip()
        
        db.commit()
        db.refresh(po)
        
        logger.info(f"Delivery status updated for PO {po.po_number}: {update.status}")
        
        return DeliveryResponse(
            delivery_date=str(po.delivery_date) if po.delivery_date else "",
            delivery_location=po.delivery_location or "",
            delivery_status=po.delivery_status,
            delivered_at=po.delivered_at.isoformat() if po.delivered_at else None,
            delivery_notes=po.delivery_notes,
            delivery_confirmed_by=str(po.delivery_confirmed_by) if po.delivery_confirmed_by else None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating delivery status: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update delivery status"
        )

@router.get("/{po_id}/delivery/history")
def get_delivery_history(
    po_id: UUID,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user_sync)
):
    """Get delivery history and notes for a purchase order."""
    try:
        po = get_po_with_auth_check(po_id, current_user, db)
        
        # Parse delivery notes into history entries
        history = []
        if po.delivery_notes:
            for line in po.delivery_notes.split('\n'):
                if line.strip() and line.startswith('['):
                    # Parse timestamp and note safely
                    timestamp_str, note = parse_delivery_note(line)
                    history.append({
                        "timestamp": timestamp_str,
                        "note": note
                    })
        
        return {
            "po_id": str(po_id),
            "po_number": po.po_number,
            "current_status": po.delivery_status,
            "delivered_at": po.delivered_at.isoformat() if po.delivered_at else None,
            "delivery_confirmed_by": str(po.delivery_confirmed_by) if po.delivery_confirmed_by else None,
            "history": history
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving delivery history: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve delivery history"
        )
