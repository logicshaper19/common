"""
Batch Ownership Service for managing ownership transfers with liability tracking.
Handles the complex business logic of ownership vs liability during supply chain transactions.
"""
from datetime import datetime
from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from app.models.batch import Batch
from app.core.logging import get_logger

logger = get_logger(__name__)


class BatchOwnershipService:
    """Service for managing batch ownership transfers with proper liability tracking."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def transfer_ownership_with_seller_liability(
        self, 
        batch_id: UUID, 
        new_company_id: UUID, 
        seller_company_id: UUID,
        po_id: UUID,
        reason: str = "purchase_order_confirmation"
    ) -> bool:
        """
        Transfer batch ownership for traceability while maintaining seller liability until delivery.
        
        Business Logic:
        - Legal ownership transfers to buyer for traceability purposes
        - Seller remains liable for loss/damage until physical delivery
        - This is documented in batch metadata for liability tracking
        
        Args:
            batch_id: ID of the batch to transfer
            new_company_id: ID of the buyer company (new owner)
            seller_company_id: ID of the seller company (remains liable)
            po_id: ID of the purchase order triggering the transfer
            reason: Reason for the ownership transfer
            
        Returns:
            bool: True if transfer successful, False otherwise
        """
        try:
            batch = self.db.query(Batch).filter(Batch.id == batch_id).first()
            if not batch:
                logger.error(f"Batch not found: {batch_id}")
                return False
            
            old_company_id = batch.company_id
            
            # Transfer ownership for traceability
            batch.company_id = new_company_id
            batch.status = 'allocated'
            batch.updated_at = datetime.utcnow()
            
            # Document seller liability in metadata
            if not batch.batch_metadata:
                batch.batch_metadata = {}
            
            batch.batch_metadata.update({
                'ownership_transfer': {
                    'transferred_at': datetime.utcnow().isoformat(),
                    'legal_owner': str(new_company_id),
                    'physical_custodian': str(seller_company_id),
                    'liability_holder': str(seller_company_id),
                    'purchase_order_id': str(po_id),
                    'liability_note': 'Seller remains liable for loss/damage until delivery confirmation',
                    'transfer_reason': reason
                }
            })
            
            logger.info(
                f"Batch ownership transferred with seller liability: {batch.batch_id} "
                f"from {old_company_id} to {new_company_id}, seller liable until delivery"
            )
            return True
            
        except Exception as e:
            logger.error(f"Failed to transfer batch ownership: {e}")
            return False

    def complete_delivery_transfer(self, batch_id: UUID) -> bool:
        """
        Complete liability transfer when delivery is confirmed.
        
        Args:
            batch_id: ID of the batch to complete delivery for
            
        Returns:
            bool: True if delivery completion successful, False otherwise
        """
        try:
            batch = self.db.query(Batch).filter(Batch.id == batch_id).first()
            if not batch:
                logger.error(f"Batch not found for delivery completion: {batch_id}")
                return False
            
            batch.status = 'delivered'
            batch.updated_at = datetime.utcnow()
            
            # Update liability metadata
            if batch.batch_metadata and 'ownership_transfer' in batch.batch_metadata:
                batch.batch_metadata['ownership_transfer'].update({
                    'delivery_confirmed_at': datetime.utcnow().isoformat(),
                    'liability_holder': batch.batch_metadata['ownership_transfer']['legal_owner'],
                    'liability_note': 'Full ownership and liability transferred to buyer upon delivery'
                })
            
            logger.info(f"Delivery completed for batch: {batch.batch_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to complete delivery transfer: {e}")
            return False

    def get_liability_info(self, batch_id: UUID) -> Optional[dict]:
        """
        Get liability information for a batch.
        
        Args:
            batch_id: ID of the batch to get liability info for
            
        Returns:
            dict: Liability information or None if not found
        """
        try:
            batch = self.db.query(Batch).filter(Batch.id == batch_id).first()
            if not batch or not batch.batch_metadata:
                return None
            
            ownership_transfer = batch.batch_metadata.get('ownership_transfer')
            if not ownership_transfer:
                return None
            
            return {
                'batch_id': str(batch_id),
                'current_owner': str(batch.company_id),
                'liability_holder': ownership_transfer.get('liability_holder'),
                'physical_custodian': ownership_transfer.get('physical_custodian'),
                'transferred_at': ownership_transfer.get('transferred_at'),
                'delivery_confirmed_at': ownership_transfer.get('delivery_confirmed_at'),
                'liability_note': ownership_transfer.get('liability_note'),
                'purchase_order_id': ownership_transfer.get('purchase_order_id')
            }
            
        except Exception as e:
            logger.error(f"Failed to get liability info for batch {batch_id}: {e}")
            return None

    def transfer_multiple_batches(
        self, 
        batch_ids: List[UUID], 
        new_company_id: UUID, 
        seller_company_id: UUID,
        po_id: UUID,
        reason: str = "purchase_order_confirmation"
    ) -> dict:
        """
        Transfer ownership for multiple batches with seller liability.
        
        Args:
            batch_ids: List of batch IDs to transfer
            new_company_id: ID of the buyer company
            seller_company_id: ID of the seller company
            po_id: ID of the purchase order
            reason: Reason for the transfer
            
        Returns:
            dict: Results of the transfer operation
        """
        results = {
            'successful_transfers': [],
            'failed_transfers': [],
            'total_batches': len(batch_ids)
        }
        
        for batch_id in batch_ids:
            success = self.transfer_ownership_with_seller_liability(
                batch_id=batch_id,
                new_company_id=new_company_id,
                seller_company_id=seller_company_id,
                po_id=po_id,
                reason=reason
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

    def simple_ownership_transfer_with_liability_note(
        self, 
        batch_id: UUID, 
        new_company_id: UUID, 
        seller_company_id: UUID,
        po_id: UUID
    ) -> bool:
        """
        Simple ownership transfer with minimal liability tracking.
        This is a lightweight version for cases where full metadata tracking isn't needed.
        
        Args:
            batch_id: ID of the batch to transfer
            new_company_id: ID of the buyer company
            seller_company_id: ID of the seller company
            po_id: ID of the purchase order
            
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
            batch.batch_metadata['purchase_order_id'] = str(po_id)
            
            logger.info(
                f"Simple ownership transfer: {batch.batch_id} from {old_company_id} to {new_company_id}"
            )
            return True
            
        except Exception as e:
            logger.error(f"Failed simple ownership transfer: {e}")
            return False
