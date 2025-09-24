"""
Simple Batch Ownership Service - Safe, minimal implementation.
Focuses on core traceability without over-engineering.
"""
from datetime import datetime
from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from app.models.batch import Batch
from app.core.logging import get_logger

logger = get_logger(__name__)


class SimpleBatchOwnershipService:
    """Simple, safe batch ownership transfer service."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def transfer_batch_ownership(
        self, 
        batch_id: UUID, 
        new_company_id: UUID,
        po_id: Optional[UUID] = None
    ) -> bool:
        """
        Simple, safe batch ownership transfer.
        
        Args:
            batch_id: ID of the batch to transfer
            new_company_id: ID of the buyer company
            po_id: Optional purchase order ID for reference
            
        Returns:
            bool: True if transfer successful, False otherwise
        """
        try:
            batch = self.db.query(Batch).filter(Batch.id == batch_id).first()
            if not batch:
                logger.error(f"Batch not found: {batch_id}")
                return False
            
            old_company_id = batch.company_id
            
            # Simple ownership transfer
            batch.company_id = new_company_id
            batch.status = 'allocated'
            batch.updated_at = datetime.utcnow()
            
            # Minimal liability note
            if not batch.batch_metadata:
                batch.batch_metadata = {}
            batch.batch_metadata['seller_liable_until_delivery'] = True
            batch.batch_metadata['ownership_transferred_at'] = datetime.utcnow().isoformat()
            if po_id:
                batch.batch_metadata['purchase_order_id'] = str(po_id)
            
            logger.info(
                f"Batch ownership transferred: {batch.batch_id} from {old_company_id} to {new_company_id}"
            )
            return True
            
        except Exception as e:
            logger.error(f"Failed to transfer batch ownership: {e}")
            return False

    def transfer_multiple_batches(
        self, 
        batch_ids: List[UUID], 
        new_company_id: UUID,
        po_id: Optional[UUID] = None
    ) -> dict:
        """
        Transfer ownership for multiple batches.
        
        Args:
            batch_ids: List of batch IDs to transfer
            new_company_id: ID of the buyer company
            po_id: Optional purchase order ID for reference
            
        Returns:
            dict: Results of the transfer operation
        """
        results = {
            'successful_transfers': [],
            'failed_transfers': [],
            'total_batches': len(batch_ids)
        }
        
        for batch_id in batch_ids:
            success = self.transfer_batch_ownership(
                batch_id=batch_id,
                new_company_id=new_company_id,
                po_id=po_id
            )
            
            if success:
                results['successful_transfers'].append(str(batch_id))
            else:
                results['failed_transfers'].append(str(batch_id))
        
        logger.info(
            f"Batch transfer results: {len(results['successful_transfers'])} successful, "
            f"{len(results['failed_transfers'])} failed out of {results['total_batches']} total"
        )
        
        return results

    def complete_delivery(self, batch_id: UUID) -> bool:
        """
        Mark batch as delivered.
        
        Args:
            batch_id: ID of the batch to mark as delivered
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            batch = self.db.query(Batch).filter(Batch.id == batch_id).first()
            if not batch:
                logger.error(f"Batch not found: {batch_id}")
                return False
            
            batch.status = 'delivered'
            batch.updated_at = datetime.utcnow()
            
            # Update liability note
            if batch.batch_metadata:
                batch.batch_metadata['seller_liable_until_delivery'] = False
                batch.batch_metadata['delivery_completed_at'] = datetime.utcnow().isoformat()
            
            logger.info(f"Batch marked as delivered: {batch.batch_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to mark batch as delivered: {e}")
            return False
