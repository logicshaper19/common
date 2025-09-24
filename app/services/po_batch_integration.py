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
import importlib.util
import os
spec = importlib.util.spec_from_file_location("transformation_module", os.path.join(os.path.dirname(__file__), "transformation.py"))
transformation_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(transformation_module)
from app.core.logging import get_logger
from app.core.unified_po_config import get_config, format_batch_id, format_event_id, format_facility_id, get_transformation_type, is_processor_type
from app.services.transformation_templates import TransformationTemplateEngine

logger = get_logger(__name__)


class POBatchIntegrationService:
    """Service for integrating PO confirmations with batch creation and transformations."""
    
    def __init__(self, db: Session):
        self.db = db
        self.batch_service = BatchTrackingService(db)
        self.transformation_service = transformation_module.TransformationService(db)
        self.config = get_config()
        self.template_engine = TransformationTemplateEngine()
    
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
            
            # Create batch creation event for provenance tracking
            from app.services.batch_creation_service import BatchCreationService
            creation_service = BatchCreationService(self.db)
            creation_service.create_batch_creation_event(
                batch_id=batch.id,
                source_purchase_order_id=po.id,
                creation_type='po_confirmation',
                creation_context={
                    "creation_source": "po_confirmation",
                    "po_number": po.po_number,
                    "seller_company_id": str(po.seller_company_id),
                    "buyer_company_id": str(po.buyer_company_id),
                    "confirmed_quantity": float(po.quantity),
                    "confirmed_unit_price": float(po.unit_price),
                    "system_version": "1.0"
                },
                created_by_user_id=confirming_user_id
            )
            
            # Link PO to batch for allocation tracking
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
        Create a comprehensive transformation suggestion with role-specific data.
        
        Args:
            po_id: ID of the confirmed PO
            batch_id: ID of the created batch
            company_id: ID of the processing company
            user_id: ID of the user
            
        Returns:
            Comprehensive transformation suggestion with role-specific data
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
            
            # Prepare input batch data for template
            input_batch_data = {
                "batch_id": str(batch_id),
                "quantity": float(batch.quantity),
                "unit": batch.unit,
                "product_name": batch.product.name,
                "quality_grade": batch.quality_grade or "A"
            }
            
            # Create comprehensive transformation template
            template = self.template_engine.get_transformation_template(
                transformation_type=transformation_type,
                company_type=company.company_type,
                input_batch_data=input_batch_data,
                facility_id=format_facility_id(company.company_type)
            )
            
            # Create event ID using configuration
            event_date = datetime.utcnow().strftime(self.config.DATE_FORMAT)
            event_id = format_event_id(
                transformation_type.value.upper(),
                event_date,
                str(po_id)
            )
            
            # Create output batch suggestion
            output_batch_suggestion = self.template_engine.create_output_batch_suggestion(
                transformation_type=transformation_type,
                input_batch_data=input_batch_data
            )
            
            # Create actual output batch if suggestion is valid
            output_batch_id = None
            if output_batch_suggestion and output_batch_suggestion.get("batch_id"):
                output_batch_id = self._create_output_batch_from_suggestion(
                    output_batch_suggestion=output_batch_suggestion,
                    company_id=company_id,
                    user_id=user_id,
                    po_id=po_id
                )
            
            # Build comprehensive suggestion
            suggestion = {
                # Basic transformation event data
                "event_id": event_id,
                "transformation_type": transformation_type,
                "company_id": company_id,
                "facility_id": template["facility_id"],
                "input_batches": [BatchReference(
                    batch_id=str(batch_id),
                    quantity=float(batch.quantity),
                    unit=batch.unit
                )],
                "output_batches": [BatchReference(
                    batch_id=str(output_batch_id) if output_batch_id else output_batch_suggestion["batch_id"],
                    quantity=output_batch_suggestion["quantity"],
                    unit=output_batch_suggestion["unit"]
                )] if output_batch_suggestion else [],
                "process_description": template["process_description"],
                "start_time": template["start_time"],
                "location_name": company.name,
                "location_coordinates": template["location_coordinates"],
                "weather_conditions": template["weather_conditions"],
                
                # Quality and process data
                "quality_metrics": template["quality_metrics"],
                "process_parameters": template["process_parameters"],
                "efficiency_metrics": template["efficiency_metrics"],
                
                # Compliance and certifications
                "certifications": template["certifications"],
                "compliance_data": template["compliance_data"],
                
                # Status and metadata
                "status": template["status"],
                "validation_status": template["validation_status"],
                "suggested": True,
                "source_po_id": str(po_id),
                
                # Role-specific data (pre-filled templates)
                "role_specific_data": self._extract_role_specific_data(template, transformation_type),
                
                # Output batch suggestion
                "output_batch_suggestion": output_batch_suggestion,
                
                # Additional metadata
                "event_metadata": {
                    "created_from_po_confirmation": True,
                    "po_id": str(po_id),
                    "input_batch_id": str(batch_id),
                    "suggestion_timestamp": datetime.utcnow().isoformat(),
                    "template_version": "1.0"
                }
            }
            
            logger.info(
                f"Created comprehensive transformation suggestion for {company.name}",
                company_id=str(company_id),
                transformation_type=transformation_type.value,
                po_id=str(po_id),
                has_role_specific_data=bool(suggestion.get("role_specific_data"))
            )
            
            return suggestion
            
        except Exception as e:
            logger.error(f"Failed to create transformation suggestion: {str(e)}", exc_info=True)
            return None
    
    def _extract_role_specific_data(self, template: Dict[str, Any], transformation_type: TransformationType) -> Dict[str, Any]:
        """Extract role-specific data from template based on transformation type."""
        if transformation_type == TransformationType.HARVEST:
            return template.get("plantation_data", {})
        elif transformation_type == TransformationType.MILLING:
            return template.get("mill_data", {})
        elif transformation_type == TransformationType.REFINING:
            return template.get("refinery_data", {})
        elif transformation_type == TransformationType.MANUFACTURING:
            return template.get("manufacturer_data", {})
        return {}
    
    def _create_output_batch_from_suggestion(
        self,
        output_batch_suggestion: Dict[str, Any],
        company_id: UUID,
        user_id: UUID,
        po_id: UUID
    ) -> Optional[UUID]:
        """Create an actual output batch from a suggestion."""
        try:
            from app.schemas.batch import BatchCreate, BatchType
            from app.models.product import Product
            
            # Get a default product for the output batch
            # In a real implementation, this would be determined by the transformation type
            product = self.db.query(Product).filter(
                Product.company_id == company_id
            ).first()
            
            if not product:
                logger.warning(f"No product found for company {company_id}, skipping output batch creation")
                return None
            
            # Create batch data from suggestion
            batch_data = BatchCreate(
                batch_id=output_batch_suggestion["batch_id"],
                batch_type=BatchType.PROCESSING,  # Output from transformation
                product_id=product.id,
                quantity=output_batch_suggestion["quantity"],
                unit=output_batch_suggestion["unit"],
                production_date=output_batch_suggestion.get("production_date"),
                expiry_date=output_batch_suggestion.get("expiry_date"),
                location_name=output_batch_suggestion.get("location_name", "Processing Facility"),
                quality_grade=output_batch_suggestion.get("quality_grade", "A"),
                batch_metadata=output_batch_suggestion.get("batch_metadata", {})
            )
            
            # Create the batch using the batch service
            batch = self.batch_service.create_batch(
                batch_data=batch_data,
                company_id=company_id,
                user_id=user_id
            )
            
            if batch:
                logger.info(
                    f"Created output batch {batch.batch_id} from transformation suggestion",
                    batch_id=str(batch.id),
                    company_id=str(company_id),
                    po_id=str(po_id)
                )
                return batch.id
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to create output batch from suggestion: {str(e)}", exc_info=True)
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
