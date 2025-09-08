"""
Main confirmation service orchestrator.

This service coordinates the various confirmation strategies, validation services,
and document requirements to provide a clean interface for confirmation operations.
"""
from typing import Optional, List, Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.purchase_order import PurchaseOrder
from app.schemas.purchase_order import PurchaseOrderStatus
from app.schemas.confirmation import (
    ConfirmationInterfaceResponse,
    PurchaseOrderConfirmation,
    ConfirmationResponse
)
from app.services.purchase_order import PurchaseOrderService
from app.core.logging import get_logger

from .domain.models import ConfirmationContext, ValidationResult
from .domain.enums import ConfirmationInterfaceType
from .strategies.context import ConfirmationStrategyContext
from .validation import CoordinatesValidator, CertificationsValidator, InputMaterialsValidator
from .documents import DocumentRequirementsService

logger = get_logger(__name__)


class ConfirmationService:
    """
    Main confirmation service that orchestrates the confirmation process.
    
    This service provides a clean interface for:
    - Determining confirmation interface type
    - Validating confirmation data
    - Processing confirmations
    - Managing document requirements
    """
    
    def __init__(self, db: Session):
        """Initialize confirmation service with dependencies."""
        self.db = db
        self.po_service = PurchaseOrderService(db)
        
        # Initialize strategy context
        self.strategy_context = ConfirmationStrategyContext()
        
        # Initialize validators
        self.coordinates_validator = CoordinatesValidator(db)
        self.certifications_validator = CertificationsValidator(db)
        self.input_materials_validator = InputMaterialsValidator(db)
        
        # Initialize document service
        self.document_service = DocumentRequirementsService(db)
    
    def determine_confirmation_interface(
        self, 
        purchase_order_id: UUID,
        current_user_company_id: UUID
    ) -> ConfirmationInterfaceResponse:
        """
        Determine which confirmation interface to show.
        
        Args:
            purchase_order_id: Purchase order UUID
            current_user_company_id: Current user's company ID
            
        Returns:
            Confirmation interface configuration
            
        Raises:
            HTTPException: If PO not found or access denied
        """
        # Get purchase order with details
        po = self.po_service.get_purchase_order_with_details(str(purchase_order_id))
        if not po:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Purchase order not found"
            )
        
        # Check seller access
        if current_user_company_id != po.seller_company["id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the seller company can confirm purchase orders"
            )
        
        # Check confirmable status
        if po.status not in [PurchaseOrderStatus.DRAFT, PurchaseOrderStatus.PENDING]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Purchase order cannot be confirmed in {po.status} status"
            )
        
        # Create confirmation context
        context = ConfirmationContext(
            purchase_order_id=purchase_order_id,
            current_user_company_id=current_user_company_id,
            seller_company_type=po.seller_company["company_type"],
            product_category=po.product["category"],
            product_can_have_composition=po.product.get("can_have_composition", False)
        )
        
        # Get interface configuration using strategy
        interface_config = self.strategy_context.get_interface_config(context, po.product)
        
        # Get document requirements
        document_requirements = self.document_service.get_requirements_for_context(context)
        
        logger.info(
            "Confirmation interface determined",
            po_id=str(purchase_order_id),
            interface_type=context.interface_type.value,
            seller_company_type=context.seller_company_type,
            product_category=context.product_category
        )
        
        return ConfirmationInterfaceResponse(
            interface_type=context.interface_type,
            purchase_order_id=purchase_order_id,
            seller_company_type=context.seller_company_type,
            product_category=context.product_category,
            product_can_have_composition=context.product_can_have_composition,
            required_fields=interface_config.required_fields,
            optional_fields=interface_config.optional_fields,
            validation_rules=interface_config.validation_rules,
            interface_config=interface_config.ui_config,
            document_requirements=[
                {
                    "name": req.name,
                    "description": req.description,
                    "file_types": req.file_types,
                    "is_required": req.is_required,
                    "max_size_mb": req.max_size_mb
                }
                for req in document_requirements
            ]
        )
    
    async def confirm_purchase_order(
        self,
        purchase_order_id: UUID,
        confirmation_data: PurchaseOrderConfirmation,
        current_user_company_id: UUID
    ) -> ConfirmationResponse:
        """
        Confirm a purchase order with validation.
        
        Args:
            purchase_order_id: Purchase order UUID
            confirmation_data: Confirmation data
            current_user_company_id: Current user's company ID
            
        Returns:
            Confirmation response
            
        Raises:
            HTTPException: If validation fails or access denied
        """
        # Get confirmation context
        interface_response = self.determine_confirmation_interface(
            purchase_order_id, current_user_company_id
        )
        
        context = ConfirmationContext(
            purchase_order_id=purchase_order_id,
            current_user_company_id=current_user_company_id,
            seller_company_type=interface_response.seller_company_type,
            product_category=interface_response.product_category,
            product_can_have_composition=interface_response.product_can_have_composition,
            interface_type=interface_response.interface_type
        )
        
        # Validate confirmation data
        validation_results = await self._validate_confirmation_data(
            confirmation_data, context
        )
        
        # Check for validation errors
        errors = [result.message for result in validation_results if not result.is_valid]
        if errors:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Confirmation validation failed: {'; '.join(errors)}"
            )
        
        # Validate document requirements
        document_validation = await self._validate_document_requirements(
            context, confirmation_data
        )
        
        if not document_validation["all_required_uploaded"]:
            missing_docs = [doc["name"] for doc in document_validation["missing_documents"]]
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Required documents missing: {', '.join(missing_docs)}"
            )
        
        # Process confirmation using strategy
        confirmation_dict = confirmation_data.model_dump()
        update_data = self.strategy_context.process_confirmation(confirmation_dict, context)
        
        # Update purchase order
        po = self.po_service.get_purchase_order_by_id(str(purchase_order_id))
        if not po:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Purchase order not found"
            )
        
        # Apply updates
        for field, value in update_data.items():
            setattr(po, field, value)
        
        self.db.commit()
        self.db.refresh(po)
        
        # Get next steps
        next_steps = self.strategy_context.get_next_steps(context)
        
        logger.info(
            "Purchase order confirmed",
            po_id=str(purchase_order_id),
            interface_type=context.interface_type.value,
            user_company_id=str(current_user_company_id)
        )
        
        return ConfirmationResponse(
            success=True,
            message="Purchase order confirmed successfully",
            purchase_order_id=purchase_order_id,
            confirmed_status=po.status,
            next_steps=next_steps,
            validation_results=[
                {
                    "field": result.field,
                    "message": result.message,
                    "severity": result.severity.value,
                    "is_valid": result.is_valid
                }
                for result in validation_results
            ]
        )
    
    async def _validate_confirmation_data(
        self,
        confirmation_data: PurchaseOrderConfirmation,
        context: ConfirmationContext
    ) -> List[ValidationResult]:
        """Validate confirmation data using appropriate validators."""
        results = []
        
        # Convert to dict for validation
        data_dict = confirmation_data.model_dump()
        
        # Use strategy for validation
        strategy_results = self.strategy_context.validate_confirmation_data(data_dict, context)
        results.extend(strategy_results)
        
        # Additional specific validations
        if context.interface_type == ConfirmationInterfaceType.ORIGIN_DATA_INTERFACE:
            if confirmation_data.origin_data:
                origin_dict = confirmation_data.origin_data.model_dump()
                
                # Validate coordinates
                if "geographic_coordinates" in origin_dict:
                    coord_results = self.coordinates_validator.validate(
                        origin_dict["geographic_coordinates"]
                    )
                    results.extend(coord_results)
                
                # Validate certifications
                if "certifications" in origin_dict:
                    cert_results = self.certifications_validator.validate(
                        origin_dict["certifications"],
                        {
                            "product_category": context.product_category,
                            "company_type": context.seller_company_type
                        }
                    )
                    results.extend(cert_results)
        
        elif context.interface_type == ConfirmationInterfaceType.TRANSFORMATION_INTERFACE:
            if confirmation_data.transformation_data:
                transform_dict = confirmation_data.transformation_data.model_dump()
                
                # Validate input materials
                if "input_materials" in transform_dict:
                    material_results = self.input_materials_validator.validate(
                        transform_dict["input_materials"],
                        {"current_user_company_id": context.current_user_company_id}
                    )
                    results.extend(material_results)
        
        return results
    
    async def _validate_document_requirements(
        self,
        context: ConfirmationContext,
        confirmation_data: PurchaseOrderConfirmation
    ) -> Dict[str, Any]:
        """Validate document requirements."""
        # In a real implementation, this would check uploaded documents
        # For now, we'll return a placeholder validation
        
        return {
            "all_required_uploaded": True,
            "missing_documents": [],
            "invalid_documents": [],
            "valid_documents": []
        }
