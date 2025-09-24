"""
Service for managing batch creation events and provenance tracking.
"""
from typing import Optional, List, Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.batch_creation_event import BatchCreationEvent
from app.models.batch import Batch
from app.models.purchase_order import PurchaseOrder
from app.core.logging import get_logger

logger = get_logger(__name__)


class BatchCreationService:
    """Service for managing batch creation events and provenance tracking."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_batch_creation_event(
        self,
        batch_id: UUID,
        source_purchase_order_id: Optional[UUID] = None,
        creation_type: str = 'po_confirmation',
        creation_context: Optional[Dict[str, Any]] = None,
        created_by_user_id: Optional[UUID] = None
    ) -> BatchCreationEvent:
        """
        Create a batch creation event to track provenance.
        
        Args:
            batch_id: ID of the batch that was created
            source_purchase_order_id: ID of the PO that created this batch (if applicable)
            creation_type: Type of creation event ('po_confirmation', 'manual', 'transformation', etc.)
            creation_context: Additional context about the creation
            created_by_user_id: ID of the user who created the batch
            
        Returns:
            Created BatchCreationEvent
        """
        creation_event = BatchCreationEvent(
            batch_id=batch_id,
            source_purchase_order_id=source_purchase_order_id,
            creation_type=creation_type,
            creation_context=creation_context or {},
            created_by_user_id=created_by_user_id
        )
        
        self.db.add(creation_event)
        self.db.commit()
        self.db.refresh(creation_event)
        
        logger.info(
            "Batch creation event created",
            event_id=str(creation_event.id),
            batch_id=str(batch_id),
            source_po_id=str(source_purchase_order_id) if source_purchase_order_id else None,
            creation_type=creation_type
        )
        
        return creation_event
    
    def get_batch_creation_events(self, batch_id: UUID) -> List[BatchCreationEvent]:
        """
        Get all creation events for a specific batch.
        
        Args:
            batch_id: ID of the batch
            
        Returns:
            List of BatchCreationEvent objects
        """
        return self.db.query(BatchCreationEvent).filter(
            BatchCreationEvent.batch_id == batch_id
        ).order_by(BatchCreationEvent.created_at.desc()).all()
    
    def get_batches_created_from_po(self, purchase_order_id: UUID) -> List[Batch]:
        """
        Get all batches that were created from a specific purchase order.
        
        Args:
            purchase_order_id: ID of the purchase order
            
        Returns:
            List of Batch objects
        """
        return self.db.query(Batch).join(BatchCreationEvent).filter(
            BatchCreationEvent.source_purchase_order_id == purchase_order_id
        ).all()
    
    def get_source_purchase_order(self, batch_id: UUID) -> Optional[PurchaseOrder]:
        """
        Get the source purchase order that created a specific batch.
        
        Args:
            batch_id: ID of the batch
            
        Returns:
            PurchaseOrder object if found, None otherwise
        """
        creation_event = self.db.query(BatchCreationEvent).filter(
            and_(
                BatchCreationEvent.batch_id == batch_id,
                BatchCreationEvent.source_purchase_order_id.isnot(None)
            )
        ).first()
        
        if creation_event and creation_event.source_purchase_order:
            return creation_event.source_purchase_order
        
        return None
    
    def get_batch_provenance_info(self, batch_id: UUID) -> Optional[Dict[str, Any]]:
        """
        Get comprehensive provenance information for a batch.
        
        Args:
            batch_id: ID of the batch
            
        Returns:
            Dictionary with provenance information or None if not found
        """
        creation_event = self.db.query(BatchCreationEvent).filter(
            BatchCreationEvent.batch_id == batch_id
        ).first()
        
        if not creation_event:
            return None
        
        return {
            "batch_id": str(batch_id),
            "source_purchase_order_id": str(creation_event.source_purchase_order_id) if creation_event.source_purchase_order_id else None,
            "creation_type": creation_event.creation_type,
            "creation_context": creation_event.creation_context,
            "created_at": creation_event.created_at.isoformat() if creation_event.created_at else None,
            "created_by_user_id": str(creation_event.created_by_user_id) if creation_event.created_by_user_id else None,
            "source_po_number": creation_event.source_purchase_order.po_number if creation_event.source_purchase_order else None
        }
