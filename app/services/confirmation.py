"""
Purchase order confirmation service with dual interface logic.
"""
from typing import Optional, List, Dict, Any, Tuple
from uuid import UUID
from datetime import datetime
from decimal import Decimal
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.purchase_order import PurchaseOrder
from app.models.product import Product
from app.models.company import Company
from app.schemas.confirmation import (
    ConfirmationInterfaceType,
    ConfirmationInterfaceResponse,
    PurchaseOrderConfirmation,
    ConfirmationResponse,
    InputMaterialValidationRequest,
    InputMaterialValidationResponse,
    OriginDataValidationRequest,
    OriginDataValidationResponse
)
from app.schemas.product import CompositionValidation
from app.schemas.purchase_order import PurchaseOrderStatus
from app.services.purchase_order import PurchaseOrderService
from app.services.product import ProductService
from app.core.logging import get_logger

logger = get_logger(__name__)


class ConfirmationService:
    """Service for purchase order confirmation with dual interface logic."""
    
    def __init__(self, db: Session):
        self.db = db
        self.po_service = PurchaseOrderService(db)
        self.product_service = ProductService(db)
    
    def determine_confirmation_interface(
        self, 
        purchase_order_id: UUID,
        current_user_company_id: UUID
    ) -> ConfirmationInterfaceResponse:
        """
        Determine which confirmation interface to show based on company type and product category.
        
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
        
        # Check if user is the seller (only sellers can confirm)
        if current_user_company_id != po.seller_company["id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the seller company can confirm purchase orders"
            )
        
        # Check if PO is in confirmable status
        if po.status not in [PurchaseOrderStatus.DRAFT, PurchaseOrderStatus.PENDING]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Purchase order cannot be confirmed in {po.status} status"
            )
        
        # Get seller company and product details
        seller_company_type = po.seller_company["company_type"]
        product_category = po.product["category"]
        product_can_have_composition = po.product.get("can_have_composition", False)
        
        # Determine interface type based on business logic
        interface_type = self._determine_interface_type(
            seller_company_type, 
            product_category, 
            product_can_have_composition
        )
        
        # Get interface configuration
        interface_config = self._get_interface_config(
            interface_type, 
            po.product, 
            seller_company_type
        )
        
        logger.info(
            "Confirmation interface determined",
            po_id=str(purchase_order_id),
            interface_type=interface_type.value,
            seller_company_type=seller_company_type,
            product_category=product_category
        )
        
        return ConfirmationInterfaceResponse(
            interface_type=interface_type,
            purchase_order_id=purchase_order_id,
            seller_company_type=seller_company_type,
            product_category=product_category,
            product_can_have_composition=product_can_have_composition,
            required_fields=interface_config["required_fields"],
            optional_fields=interface_config["optional_fields"],
            validation_rules=interface_config["validation_rules"],
            interface_config=interface_config["config"]
        )
    
    def _determine_interface_type(
        self, 
        seller_company_type: str, 
        product_category: str,
        product_can_have_composition: bool
    ) -> ConfirmationInterfaceType:
        """
        Determine interface type based on business rules.
        
        Business Logic:
        1. If seller is 'originator' OR product is 'raw_material' → Origin Data Interface
        2. If seller is 'processor' OR product can_have_composition → Transformation Interface  
        3. Otherwise → Simple Confirmation Interface
        """
        if seller_company_type == 'originator' or product_category == 'raw_material':
            return ConfirmationInterfaceType.ORIGIN_DATA_INTERFACE
        elif seller_company_type == 'processor' or product_can_have_composition:
            return ConfirmationInterfaceType.TRANSFORMATION_INTERFACE
        else:
            return ConfirmationInterfaceType.SIMPLE_CONFIRMATION_INTERFACE
    
    def _get_interface_config(
        self, 
        interface_type: ConfirmationInterfaceType,
        product: Dict[str, Any],
        seller_company_type: str
    ) -> Dict[str, Any]:
        """Get configuration for the specific interface type."""
        
        if interface_type == ConfirmationInterfaceType.ORIGIN_DATA_INTERFACE:
            return {
                "required_fields": [
                    "geographic_coordinates",
                    "certifications"
                ],
                "optional_fields": [
                    "harvest_date",
                    "farm_identification", 
                    "batch_number",
                    "quality_parameters"
                ],
                "validation_rules": {
                    "coordinates_required": True,
                    "certifications_min": 0,
                    "harvest_date_max_age_days": 365,
                    "quality_parameters_schema": product.get("origin_data_requirements", {})
                },
                "config": {
                    "show_map_picker": True,
                    "show_certification_selector": True,
                    "show_harvest_date": product.get("category") == "raw_material",
                    "show_quality_parameters": True,
                    "certification_options": [
                        "RSPO", "NDPE", "ISPO", "MSPO", "RTRS", "ISCC", 
                        "SAN", "UTZ", "Rainforest Alliance", "Organic", 
                        "Fair Trade", "Non-GMO", "Sustainable", "Traceable"
                    ]
                }
            }
        
        elif interface_type == ConfirmationInterfaceType.TRANSFORMATION_INTERFACE:
            return {
                "required_fields": [
                    "input_materials",
                    "transformation_process"
                ],
                "optional_fields": [
                    "facility_location",
                    "processing_date",
                    "yield_percentage",
                    "quality_parameters"
                ],
                "validation_rules": {
                    "input_materials_min": 1,
                    "percentage_sum_tolerance": 0.01,
                    "quantity_validation": True,
                    "composition_validation": product.get("can_have_composition", False)
                },
                "config": {
                    "show_input_material_selector": True,
                    "show_composition_editor": product.get("can_have_composition", False),
                    "show_process_description": True,
                    "show_facility_info": True,
                    "material_breakdown_rules": product.get("material_breakdown", {}),
                    "default_unit": product.get("default_unit", "KGM")
                }
            }
        
        else:  # SIMPLE_CONFIRMATION_INTERFACE
            return {
                "required_fields": [
                    "confirmed_quantity"
                ],
                "optional_fields": [
                    "confirmation_notes"
                ],
                "validation_rules": {
                    "quantity_validation": True,
                    "max_quantity_variance": 0.1  # 10% variance allowed
                },
                "config": {
                    "show_quantity_editor": True,
                    "show_notes_field": True,
                    "default_unit": product.get("default_unit", "KGM")
                }
            }
    
    def validate_input_materials(
        self, 
        request: InputMaterialValidationRequest,
        current_user_company_id: UUID
    ) -> InputMaterialValidationResponse:
        """
        Validate input materials for transformation interface.
        
        Args:
            request: Input material validation request
            current_user_company_id: Current user's company ID
            
        Returns:
            Validation response with results
        """
        errors = []
        warnings = []
        validation_results = []
        total_quantity_available = Decimal('0')
        total_quantity_requested = Decimal('0')
        
        # Get the target purchase order
        target_po = self.po_service.get_purchase_order_by_id(str(request.purchase_order_id))
        if not target_po:
            errors.append("Target purchase order not found")
            return InputMaterialValidationResponse(
                is_valid=False,
                validation_results=[],
                total_quantity_available=Decimal('0'),
                total_quantity_requested=Decimal('0'),
                errors=errors,
                warnings=warnings
            )
        
        # Validate each input material
        for input_material in request.input_materials:
            result = self._validate_single_input_material(
                input_material, 
                current_user_company_id,
                target_po
            )
            validation_results.append(result)
            
            if result["is_valid"]:
                total_quantity_available += result["available_quantity"]
            else:
                errors.extend(result["errors"])
            
            total_quantity_requested += input_material.quantity_used
            warnings.extend(result.get("warnings", []))
        
        # Check if total percentages sum to 100%
        total_percentage = sum(material.percentage_contribution for material in request.input_materials)
        if abs(total_percentage - 100.0) > 0.01:
            errors.append(f"Input material percentages must sum to 100%, got {total_percentage}%")
        
        is_valid = len(errors) == 0
        
        logger.info(
            "Input materials validated",
            po_id=str(request.purchase_order_id),
            is_valid=is_valid,
            total_materials=len(request.input_materials),
            errors_count=len(errors),
            warnings_count=len(warnings)
        )
        
        return InputMaterialValidationResponse(
            is_valid=is_valid,
            validation_results=validation_results,
            total_quantity_available=total_quantity_available,
            total_quantity_requested=total_quantity_requested,
            errors=errors,
            warnings=warnings
        )
    
    def _validate_single_input_material(
        self, 
        input_material, 
        current_user_company_id: UUID,
        target_po: PurchaseOrder
    ) -> Dict[str, Any]:
        """Validate a single input material."""
        errors = []
        warnings = []
        
        # Get source purchase order
        source_po = self.po_service.get_purchase_order_by_id(str(input_material.source_po_id))
        if not source_po:
            return {
                "source_po_id": str(input_material.source_po_id),
                "is_valid": False,
                "errors": ["Source purchase order not found"],
                "warnings": [],
                "available_quantity": Decimal('0')
            }
        
        # Check if source PO belongs to current company (as buyer)
        if source_po.buyer_company_id != current_user_company_id:
            errors.append("Source purchase order does not belong to your company")
        
        # Check if source PO is confirmed/delivered
        if source_po.status not in ['confirmed', 'in_transit', 'delivered']:
            warnings.append(f"Source PO is in {source_po.status} status, not yet confirmed")
        
        # Check available quantity (simplified - in real system would track usage)
        available_quantity = source_po.quantity
        if input_material.quantity_used > available_quantity:
            errors.append(f"Requested quantity {input_material.quantity_used} exceeds available {available_quantity}")
        
        return {
            "source_po_id": str(input_material.source_po_id),
            "is_valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "available_quantity": available_quantity,
            "source_po_number": source_po.po_number,
            "source_product": source_po.product_id
        }

    def validate_origin_data(
        self,
        request: OriginDataValidationRequest,
        current_user_company_id: UUID
    ) -> OriginDataValidationResponse:
        """
        Validate origin data for origin data interface.

        Args:
            request: Origin data validation request
            current_user_company_id: Current user's company ID

        Returns:
            Validation response with results
        """
        errors = []
        warnings = []
        suggestions = []

        # Get the purchase order
        po = self.po_service.get_purchase_order_by_id(str(request.purchase_order_id))
        if not po:
            errors.append("Purchase order not found")
            return OriginDataValidationResponse(
                is_valid=False,
                validation_results={},
                compliance_status={},
                errors=errors,
                warnings=warnings,
                suggestions=suggestions
            )

        # Validate geographic coordinates
        coords = request.origin_data.geographic_coordinates
        coord_validation = self._validate_coordinates(coords)

        # Validate certifications
        cert_validation = self._validate_certifications(
            request.origin_data.certifications,
            po.product_id
        )

        # Validate harvest date if provided
        harvest_validation = {}
        if request.origin_data.harvest_date:
            harvest_validation = self._validate_harvest_date(
                request.origin_data.harvest_date,
                po.product_id
            )

        # Compile validation results
        validation_results = {
            "coordinates": coord_validation,
            "certifications": cert_validation,
            "harvest_date": harvest_validation
        }

        # Determine compliance status
        compliance_status = self._determine_compliance_status(validation_results)

        # Collect all errors and warnings
        for validation in validation_results.values():
            errors.extend(validation.get("errors", []))
            warnings.extend(validation.get("warnings", []))
            suggestions.extend(validation.get("suggestions", []))

        is_valid = len(errors) == 0

        logger.info(
            "Origin data validated",
            po_id=str(request.purchase_order_id),
            is_valid=is_valid,
            compliance_status=compliance_status,
            errors_count=len(errors),
            warnings_count=len(warnings)
        )

        return OriginDataValidationResponse(
            is_valid=is_valid,
            validation_results=validation_results,
            compliance_status=compliance_status,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions
        )

    def confirm_purchase_order(
        self,
        purchase_order_id: UUID,
        confirmation_data: PurchaseOrderConfirmation,
        current_user_company_id: UUID
    ) -> ConfirmationResponse:
        """
        Confirm a purchase order with the appropriate interface data.

        Args:
            purchase_order_id: Purchase order UUID
            confirmation_data: Confirmation data
            current_user_company_id: Current user's company ID

        Returns:
            Confirmation response

        Raises:
            HTTPException: If validation fails or access denied
        """
        # Get interface type first
        interface_response = self.determine_confirmation_interface(
            purchase_order_id,
            current_user_company_id
        )

        # Validate confirmation data based on interface type
        validation_results = self._validate_confirmation_data(
            confirmation_data,
            interface_response.interface_type,
            purchase_order_id,
            current_user_company_id
        )

        if not validation_results["is_valid"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Confirmation validation failed: {', '.join(validation_results['errors'])}"
            )

        # Get the purchase order
        po = self.po_service.get_purchase_order_by_id(str(purchase_order_id))
        if not po:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Purchase order not found"
            )

        try:
            # Update purchase order with confirmation data
            update_data = {
                "status": PurchaseOrderStatus.CONFIRMED.value
            }

            # Add confirmed quantity if provided
            if confirmation_data.confirmed_quantity:
                update_data["quantity"] = confirmation_data.confirmed_quantity
                # Recalculate total amount
                update_data["total_amount"] = confirmation_data.confirmed_quantity * po.unit_price

            # Add confirmed composition if provided
            if confirmation_data.confirmed_composition:
                update_data["composition"] = confirmation_data.confirmed_composition

            # Add interface-specific data
            if confirmation_data.origin_data:
                origin_dict = confirmation_data.origin_data.model_dump()
                # Convert date objects to strings for JSON serialization
                if "harvest_date" in origin_dict and origin_dict["harvest_date"]:
                    origin_dict["harvest_date"] = origin_dict["harvest_date"].isoformat()
                update_data["origin_data"] = origin_dict

            if confirmation_data.transformation_data:
                transformation_dict = confirmation_data.transformation_data.model_dump()
                # Convert UUIDs and Decimals to strings in input materials for JSON serialization
                input_materials = transformation_dict["input_materials"]
                for material in input_materials:
                    if "source_po_id" in material:
                        material["source_po_id"] = str(material["source_po_id"])
                    if "quantity_used" in material and isinstance(material["quantity_used"], Decimal):
                        material["quantity_used"] = float(material["quantity_used"])
                update_data["input_materials"] = input_materials
                # Store additional transformation data in origin_data field for now
                # In a real system, you might want a separate transformation_data field
                existing_origin = po.origin_data or {}
                existing_origin.update({
                    "transformation_process": transformation_dict.get("transformation_process"),
                    "facility_location": transformation_dict.get("facility_location"),
                    "processing_date": transformation_dict.get("processing_date").isoformat() if transformation_dict.get("processing_date") else None,
                    "yield_percentage": transformation_dict.get("yield_percentage"),
                    "quality_parameters": transformation_dict.get("quality_parameters")
                })
                update_data["origin_data"] = existing_origin

            # Add confirmation notes
            if confirmation_data.confirmation_notes:
                existing_notes = po.notes or ""
                update_data["notes"] = f"{existing_notes}\n\nConfirmation: {confirmation_data.confirmation_notes}".strip()

            # Update the purchase order
            for field, value in update_data.items():
                setattr(po, field, value)

            self.db.commit()
            self.db.refresh(po)

            # Determine next steps
            next_steps = self._determine_next_steps(interface_response.interface_type, po)

            logger.info(
                "Purchase order confirmed successfully",
                po_id=str(purchase_order_id),
                interface_type=interface_response.interface_type.value,
                confirmed_quantity=float(confirmation_data.confirmed_quantity) if confirmation_data.confirmed_quantity else None
            )

            return ConfirmationResponse(
                purchase_order_id=purchase_order_id,
                confirmation_status="confirmed",
                interface_type=interface_response.interface_type,
                confirmed_at=datetime.utcnow(),
                transparency_score_updated=False,  # Would be True after implementing transparency calculation
                validation_results=validation_results,
                next_steps=next_steps
            )

        except Exception as e:
            self.db.rollback()
            logger.error("Failed to confirm purchase order", po_id=str(purchase_order_id), error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to confirm purchase order"
            )

    def _validate_coordinates(self, coords) -> Dict[str, Any]:
        """Validate geographic coordinates."""
        errors = []
        warnings = []
        suggestions = []

        # Basic validation is handled by Pydantic, but we can add business logic
        if coords.accuracy_meters and coords.accuracy_meters > 100:
            warnings.append("GPS accuracy is low (>100m), consider improving location precision")

        # Check if coordinates are in reasonable ranges for palm oil regions
        # Palm oil is primarily grown in tropical regions
        if not (-30 <= coords.latitude <= 30):
            warnings.append("Coordinates are outside typical palm oil growing regions")

        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "suggestions": suggestions
        }

    def _validate_certifications(self, certifications: List[str], product_id: UUID) -> Dict[str, Any]:
        """Validate certifications."""
        errors = []
        warnings = []
        suggestions = []

        # Get product to check requirements
        product = self.product_service.get_product_by_id(str(product_id))
        if product and product.origin_data_requirements:
            required_certs = product.origin_data_requirements.get("required_certifications", [])
            for req_cert in required_certs:
                if req_cert not in certifications:
                    warnings.append(f"Missing recommended certification: {req_cert}")

        # Suggest common certifications if none provided
        if not certifications:
            suggestions.append("Consider adding certifications like RSPO, NDPE, or ISPO for better traceability")

        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "suggestions": suggestions
        }

    def _validate_harvest_date(self, harvest_date, product_id: UUID) -> Dict[str, Any]:
        """Validate harvest date."""
        errors = []
        warnings = []
        suggestions = []

        # Check if harvest date is not in the future
        if harvest_date > datetime.now().date():
            errors.append("Harvest date cannot be in the future")

        # Check if harvest date is not too old (configurable)
        days_old = (datetime.now().date() - harvest_date).days
        if days_old > 365:
            warnings.append(f"Harvest date is {days_old} days old, which may affect product quality")

        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "suggestions": suggestions
        }

    def _determine_compliance_status(self, validation_results: Dict[str, Any]) -> Dict[str, str]:
        """Determine compliance status based on validation results."""
        compliance = {}

        # Geographic compliance
        coord_result = validation_results.get("coordinates", {})
        if coord_result.get("is_valid", False):
            compliance["geographic"] = "compliant"
        else:
            compliance["geographic"] = "non_compliant"

        # Certification compliance
        cert_result = validation_results.get("certifications", {})
        if cert_result.get("warnings"):
            compliance["certification"] = "partial"
        elif cert_result.get("is_valid", False):
            compliance["certification"] = "compliant"
        else:
            compliance["certification"] = "non_compliant"

        # Overall compliance
        if all(status == "compliant" for status in compliance.values()):
            compliance["overall"] = "fully_compliant"
        elif any(status == "non_compliant" for status in compliance.values()):
            compliance["overall"] = "non_compliant"
        else:
            compliance["overall"] = "partially_compliant"

        return compliance

    def _validate_confirmation_data(
        self,
        confirmation_data: PurchaseOrderConfirmation,
        interface_type: ConfirmationInterfaceType,
        purchase_order_id: UUID,
        current_user_company_id: UUID
    ) -> Dict[str, Any]:
        """Validate confirmation data based on interface type."""
        errors = []
        warnings = []

        # Validate based on interface type
        if interface_type == ConfirmationInterfaceType.ORIGIN_DATA_INTERFACE:
            if not confirmation_data.origin_data:
                errors.append("Origin data is required for this interface")
            else:
                # Validate origin data
                origin_request = OriginDataValidationRequest(
                    purchase_order_id=purchase_order_id,
                    origin_data=confirmation_data.origin_data
                )
                origin_validation = self.validate_origin_data(origin_request, current_user_company_id)
                if not origin_validation.is_valid:
                    errors.extend(origin_validation.errors)
                warnings.extend(origin_validation.warnings)

        elif interface_type == ConfirmationInterfaceType.TRANSFORMATION_INTERFACE:
            if not confirmation_data.transformation_data:
                errors.append("Transformation data is required for this interface")
            else:
                # Validate input materials
                input_request = InputMaterialValidationRequest(
                    purchase_order_id=purchase_order_id,
                    input_materials=confirmation_data.transformation_data.input_materials
                )
                input_validation = self.validate_input_materials(input_request, current_user_company_id)
                if not input_validation.is_valid:
                    errors.extend(input_validation.errors)
                warnings.extend(input_validation.warnings)

        # Validate confirmed composition if provided
        if confirmation_data.confirmed_composition:
            # Get product to check composition rules
            po = self.po_service.get_purchase_order_by_id(str(purchase_order_id))
            if po and po.product_id:
                product = self.product_service.get_product_by_id(str(po.product_id))
                if product and product.can_have_composition:
                    composition_validation_request = CompositionValidation(
                        product_id=po.product_id,
                        composition=confirmation_data.confirmed_composition
                    )
                    composition_validation = self.product_service.validate_composition(composition_validation_request)
                    if not composition_validation.is_valid:
                        errors.extend(composition_validation.errors)
                    warnings.extend(composition_validation.warnings)

        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }

    def _determine_next_steps(self, interface_type: ConfirmationInterfaceType, po: PurchaseOrder) -> List[str]:
        """Determine next steps after confirmation."""
        next_steps = []

        if interface_type == ConfirmationInterfaceType.ORIGIN_DATA_INTERFACE:
            next_steps.extend([
                "Origin data has been captured and validated",
                "Purchase order is now confirmed and ready for shipment",
                "Buyer will be notified of confirmation"
            ])

        elif interface_type == ConfirmationInterfaceType.TRANSFORMATION_INTERFACE:
            next_steps.extend([
                "Input materials have been linked to this purchase order",
                "Transformation data has been recorded",
                "Supply chain traceability has been updated",
                "Purchase order is now confirmed and ready for shipment"
            ])

        else:  # Simple confirmation
            next_steps.extend([
                "Purchase order has been confirmed",
                "Ready for shipment preparation",
                "Buyer will be notified of confirmation"
            ])

        # Common next steps
        next_steps.extend([
            "Update delivery schedule if needed",
            "Prepare shipping documentation",
            "Monitor transparency score updates"
        ])

        return next_steps
