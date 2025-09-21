"""
PO-Batch Integration Service for Unified PO Model implementation.

This service handles:
1. Automatic batch creation when POs are confirmed
2. Transformation trigger logic for processors
3. Chain building through batch relationships
"""
from datetime import datetime, date
from typing import Optional, Dict, Any, List
from uuid import UUID, uuid4
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.models.purchase_order import PurchaseOrder
from app.models.batch import Batch, BatchRelationship
from app.models.transformation import TransformationEvent, TransformationType
from app.models.company import Company
from app.models.product import Product
from app.schemas.batch import BatchCreate, BatchType, BatchStatus
from app.schemas.transformation import TransformationEventCreate, BatchReference
from app.services.batch import BatchTrackingService
from app.services.transformation import TransformationService
from app.core.logging import get_logger
from app.core.unified_po_config import get_config, format_batch_id, format_event_id, format_facility_id, get_transformation_type, is_processor_type

logger = get_logger(__name__)


class POBatchIntegrationService:
    """Service for integrating PO confirmations with batch creation and transformations."""
    
    def __init__(self, db: Session):
        self.db = db
        self.batch_service = BatchTrackingService(db)
        self.transformation_service = TransformationService(db)
        self.config = get_config()
    
    def create_batch_from_po_confirmation(
        self,
        po_id: UUID,
        confirming_user_id: UUID
    ) -> Optional[Batch]:
        """
        Create a batch automatically when a PO is confirmed.
        
        Args:
            po_id: ID of the confirmed purchase order
            confirming_user_id: ID of the user confirming the PO
            
        Returns:
            Created batch or None if creation failed
        """
        try:
            # Get the confirmed PO
            po = self.db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
            if not po or po.status != 'confirmed':
                logger.warning(f"PO {po_id} not found or not confirmed")
                return None
            
            # Get buyer company (who will own the batch)
            buyer_company = self.db.query(Company).filter(Company.id == po.buyer_company_id).first()
            if not buyer_company:
                logger.error(f"Buyer company {po.buyer_company_id} not found")
                return None
            
            # Get product
            product = self.db.query(Product).filter(Product.id == po.product_id).first()
            if not product:
                logger.error(f"Product {po.product_id} not found")
                return None
            
            # Generate deterministic batch ID using configuration
            timestamp = datetime.utcnow().strftime(self.config.TIMESTAMP_FORMAT)
            batch_id = format_batch_id(str(po.id), timestamp)
            
            # Create batch data
            batch_data = BatchCreate(
                batch_id=batch_id,
                batch_type=BatchType.PROCESSING,  # Using default from config
                product_id=po.product_id,
                quantity=po.quantity,
                unit=po.unit,
                production_date=date.today(),
                location_name=buyer_company.name,
                batch_metadata={
                    self.config.BATCH_METADATA_KEYS["purchase_order_id"]: str(po.id),
                    self.config.BATCH_METADATA_KEYS["seller_company_id"]: str(po.seller_company_id),
                    self.config.BATCH_METADATA_KEYS["buyer_company_id"]: str(po.buyer_company_id),
                    self.config.BATCH_METADATA_KEYS["created_from_po_confirmation"]: True
                }
            )
            
            # Create the batch
            batch = self.batch_service.create_batch(
                batch_data=batch_data,
                company_id=po.buyer_company_id,
                user_id=confirming_user_id
            )
            
            # Link PO to batch
            po.batch_id = batch.id
            self.db.commit()
            
            logger.info(
                f"Created batch {batch.batch_id} from PO {po.id}",
                batch_id=batch.batch_id,
                po_id=str(po.id),
                buyer_company_id=str(po.buyer_company_id)
            )
            
            return batch
            
        except Exception as e:
            logger.error(f"Failed to create batch from PO {po_id}: {str(e)}", exc_info=True)
            self.db.rollback()
            return None
    
    def should_trigger_transformation(self, company_id: UUID) -> bool:
        """
        Check if a company should trigger transformation after PO confirmation.
        
        Args:
            company_id: ID of the company
            
        Returns:
            True if transformation should be triggered
        """
        company = self.db.query(Company).filter(Company.id == company_id).first()
        if not company:
            return False
        
        # Trigger transformation for processors using configuration
        return is_processor_type(company.company_type)
    
    def create_transformation_suggestion(
        self,
        po_id: UUID,
        batch_id: UUID,
        company_id: UUID,
        user_id: UUID
    ) -> Optional[Dict[str, Any]]:
        """
        Create a transformation suggestion for processors.
        
        Args:
            po_id: ID of the confirmed PO
            batch_id: ID of the created batch
            company_id: ID of the processing company
            user_id: ID of the user
            
        Returns:
            Transformation suggestion data or None
        """
        try:
            # Get company to determine transformation type
            company = self.db.query(Company).filter(Company.id == company_id).first()
            if not company:
                return None
            
            # Determine transformation type based on company type using configuration
            transformation_type = get_transformation_type(company.company_type)
            if not transformation_type:
                return None
            
            # Get PO and batch details
            po = self.db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
            batch = self.db.query(Batch).filter(Batch.id == batch_id).first()
            
            if not po or not batch:
                return None
            
            # Create transformation suggestion using configuration
            event_date = datetime.utcnow().strftime(self.config.DATE_FORMAT)
            event_id = format_event_id(
                transformation_type.value.upper(),
                event_date,
                str(po_id)
            )
            facility_id = format_facility_id(company.company_type)
            
            suggestion = {
                "event_id": event_id,
                "transformation_type": transformation_type,
                "company_id": company_id,
                "facility_id": facility_id,
                "input_batches": [BatchReference(
                    batch_id=str(batch_id),
                    quantity=float(batch.quantity),
                    unit=batch.unit
                )],
                "process_description": f"Process {batch.product.name} from {po.seller_company.name}",
                "start_time": datetime.utcnow(),
                "location_name": company.name,
                "suggested": True,
                "source_po_id": str(po_id)
            }
            
            logger.info(
                f"Created transformation suggestion for {company.name}",
                company_id=str(company_id),
                transformation_type=transformation_type.value,
                po_id=str(po_id)
            )
            
            return suggestion
            
        except Exception as e:
            logger.error(f"Failed to create transformation suggestion: {str(e)}", exc_info=True)
            return None
    
    def create_batch_relationship(
        self,
        parent_batch_id: UUID,
        child_batch_id: UUID,
        relationship_type: str,
        po_id: UUID,
        user_id: UUID
    ) -> Optional[BatchRelationship]:
        """
        Create a relationship between batches to build the traceability chain.
        
        Args:
            parent_batch_id: ID of the parent batch (seller's batch)
            child_batch_id: ID of the child batch (buyer's batch)
            relationship_type: Type of relationship (e.g., 'sale', 'transformation')
            po_id: ID of the purchase order
            user_id: ID of the user creating the relationship
            
        Returns:
            Created batch relationship or None
        """
        try:
            # Check if relationship already exists
            existing = self.db.query(BatchRelationship).filter(
                and_(
                    BatchRelationship.parent_batch_id == parent_batch_id,
                    BatchRelationship.child_batch_id == child_batch_id,
                    BatchRelationship.relationship_type == relationship_type
                )
            ).first()
            
            if existing:
                logger.info(f"Batch relationship already exists: {parent_batch_id} -> {child_batch_id}")
                return existing
            
            # Create new relationship using configuration
            relationship = BatchRelationship(
                id=uuid4(),
                parent_batch_id=parent_batch_id,
                child_batch_id=child_batch_id,
                relationship_type=relationship_type or self.config.DEFAULT_RELATIONSHIP_TYPE,
                po_id=po_id,
                created_by_user_id=user_id,
                created_at=datetime.utcnow()
            )
            
            self.db.add(relationship)
            self.db.commit()
            
            logger.info(
                f"Created batch relationship: {parent_batch_id} -> {child_batch_id}",
                relationship_type=relationship_type,
                po_id=str(po_id)
            )
            
            return relationship
            
        except Exception as e:
            logger.error(f"Failed to create batch relationship: {str(e)}", exc_info=True)
            self.db.rollback()
            return None
    
    def get_traceability_chain(self, batch_id: UUID) -> List[Dict[str, Any]]:
        """
        Get the full traceability chain for a batch.
        
        Args:
            batch_id: ID of the batch to trace
            
        Returns:
            List of chain nodes showing the full traceability path
        """
        try:
            chain = []
            current_batch_id = batch_id
            
            while current_batch_id:
                # Get current batch
                batch = self.db.query(Batch).filter(Batch.id == current_batch_id).first()
                if not batch:
                    break
                
                # Get the PO that created this batch
                po = self.db.query(PurchaseOrder).filter(PurchaseOrder.batch_id == current_batch_id).first()
                
                # Get the parent batch (if any)
                relationship = self.db.query(BatchRelationship).filter(
                    BatchRelationship.child_batch_id == current_batch_id
                ).first()
                
                chain_node = {
                    "batch_id": str(current_batch_id),
                    "batch_name": batch.batch_id,
                    "company_name": batch.company.name if batch.company else "Unknown",
                    "product_name": batch.product.name if batch.product else "Unknown",
                    "quantity": float(batch.quantity),
                    "unit": batch.unit,
                    "production_date": batch.production_date.isoformat() if batch.production_date else None,
                    "po_id": str(po.id) if po else None,
                    "parent_batch_id": str(relationship.parent_batch_id) if relationship else None
                }
                
                chain.append(chain_node)
                
                # Move to parent batch
                current_batch_id = relationship.parent_batch_id if relationship else None
            
            return chain
            
        except Exception as e:
            logger.error(f"Failed to get traceability chain for batch {batch_id}: {str(e)}", exc_info=True)
            return []
