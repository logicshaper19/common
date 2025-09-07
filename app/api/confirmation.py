"""
Purchase order confirmation API endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
from datetime import datetime

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.services.confirmation import ConfirmationService
from app.schemas.confirmation import (
    ConfirmationInterfaceResponse,
    PurchaseOrderConfirmation,
    ConfirmationResponse,
    InputMaterialValidationRequest,
    InputMaterialValidationResponse,
    OriginDataValidationRequest,
    OriginDataValidationResponse
)
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/purchase-orders", tags=["confirmation"])


@router.get("/{purchase_order_id}/confirmation-interface", response_model=ConfirmationInterfaceResponse)
def get_confirmation_interface(
    purchase_order_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get the appropriate confirmation interface for a purchase order.
    
    Determines which interface to show based on:
    - Seller company type (originator, processor, brand)
    - Product category (raw_material, processed, finished_good)
    - Product composition capabilities
    
    Only the seller company can access the confirmation interface.
    """
    try:
        purchase_order_uuid = UUID(purchase_order_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid purchase order ID format"
        )
    
    confirmation_service = ConfirmationService(db)
    
    interface_response = confirmation_service.determine_confirmation_interface(
        purchase_order_uuid,
        current_user.company_id
    )
    
    logger.info(
        "Confirmation interface requested",
        po_id=purchase_order_id,
        interface_type=interface_response.interface_type.value,
        user_id=str(current_user.id),
        company_id=str(current_user.company_id)
    )
    
    return interface_response


@router.post("/{purchase_order_id}/confirm", response_model=ConfirmationResponse)
async def confirm_purchase_order(
    purchase_order_id: str,
    confirmation_data: PurchaseOrderConfirmation,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Confirm a purchase order with the appropriate interface data.
    
    The confirmation data should match the interface type:
    - Origin Data Interface: Requires origin_data with coordinates and certifications
    - Transformation Interface: Requires transformation_data with input materials
    - Simple Confirmation: Requires only basic confirmation details
    
    Only the seller company can confirm purchase orders.
    """
    try:
        purchase_order_uuid = UUID(purchase_order_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid purchase order ID format"
        )
    
    confirmation_service = ConfirmationService(db)
    
    confirmation_response = await confirmation_service.confirm_purchase_order(
        purchase_order_uuid,
        confirmation_data,
        current_user.company_id
    )
    
    logger.info(
        "Purchase order confirmed via API",
        po_id=purchase_order_id,
        interface_type=confirmation_response.interface_type.value,
        user_id=str(current_user.id),
        company_id=str(current_user.company_id)
    )
    
    return confirmation_response


@router.post("/validate-input-materials", response_model=InputMaterialValidationResponse)
def validate_input_materials(
    validation_request: InputMaterialValidationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Validate input materials for transformation interface.
    
    Checks:
    - Source purchase orders exist and belong to the company
    - Sufficient quantities are available
    - Percentage contributions sum to 100%
    - Source POs are in appropriate status
    
    This endpoint can be called before confirmation to validate the data.
    """
    confirmation_service = ConfirmationService(db)
    
    validation_response = confirmation_service.validate_input_materials(
        validation_request,
        current_user.company_id
    )
    
    logger.info(
        "Input materials validated",
        po_id=str(validation_request.purchase_order_id),
        is_valid=validation_response.is_valid,
        materials_count=len(validation_request.input_materials),
        user_id=str(current_user.id)
    )
    
    return validation_response


@router.post("/validate-origin-data", response_model=OriginDataValidationResponse)
def validate_origin_data(
    validation_request: OriginDataValidationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Validate origin data for origin data interface.
    
    Checks:
    - Geographic coordinates are valid and reasonable
    - Certifications are appropriate for the product
    - Harvest dates are realistic
    - Compliance with regional requirements
    
    This endpoint can be called before confirmation to validate the data.
    """
    confirmation_service = ConfirmationService(db)
    
    validation_response = confirmation_service.validate_origin_data(
        validation_request,
        current_user.company_id
    )
    
    logger.info(
        "Origin data validated",
        po_id=str(validation_request.purchase_order_id),
        is_valid=validation_response.is_valid,
        compliance_status=validation_response.compliance_status.get("overall", "unknown"),
        user_id=str(current_user.id)
    )
    
    return validation_response


@router.get("/{purchase_order_id}/confirmation-status")
def get_confirmation_status(
    purchase_order_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get the current confirmation status of a purchase order.
    
    Returns information about:
    - Whether the PO has been confirmed
    - What interface was used for confirmation
    - Validation results and compliance status
    - Next steps in the process
    """
    try:
        purchase_order_uuid = UUID(purchase_order_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid purchase order ID format"
        )
    
    confirmation_service = ConfirmationService(db)
    
    # Get the purchase order to check status
    po = confirmation_service.po_service.get_purchase_order_with_details(purchase_order_id)
    if not po:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Purchase order not found"
        )
    
    # Check access permissions
    if (current_user.company_id != po.buyer_company["id"] and 
        current_user.company_id != po.seller_company["id"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this purchase order"
        )
    
    # Determine what interface would be used
    if po.status in ["draft", "pending"]:
        interface_response = confirmation_service.determine_confirmation_interface(
            purchase_order_uuid,
            po.seller_company["id"]
        )
        interface_type = interface_response.interface_type.value
    else:
        # For confirmed POs, determine interface type from data
        if po.origin_data and "geographic_coordinates" in po.origin_data:
            interface_type = "origin_data_interface"
        elif po.input_materials:
            interface_type = "transformation_interface"
        else:
            interface_type = "simple_confirmation_interface"
    
    status_info = {
        "purchase_order_id": purchase_order_id,
        "current_status": po.status,
        "is_confirmed": po.status in ["confirmed", "in_transit", "delivered"],
        "interface_type": interface_type,
        "confirmation_data": {
            "has_origin_data": bool(po.origin_data),
            "has_input_materials": bool(po.input_materials),
            "has_composition": bool(po.composition),
            "confirmed_at": po.updated_at if po.status != "draft" else None
        },
        "next_actions": []
    }
    
    # Determine next actions based on status and user role
    if po.status == "draft" and current_user.company_id == po.seller_company["id"]:
        status_info["next_actions"].append("Confirm purchase order using appropriate interface")
    elif po.status == "confirmed" and current_user.company_id == po.seller_company["id"]:
        status_info["next_actions"].extend([
            "Prepare shipment",
            "Update delivery schedule",
            "Prepare shipping documentation"
        ])
    elif po.status == "confirmed" and current_user.company_id == po.buyer_company["id"]:
        status_info["next_actions"].extend([
            "Monitor shipment status",
            "Prepare for delivery",
            "Review transparency data"
        ])
    
    logger.info(
        "Confirmation status requested",
        po_id=purchase_order_id,
        status=po.status,
        interface_type=interface_type,
        user_id=str(current_user.id)
    )
    
    return status_info


@router.get("/{purchase_order_id}/document-requirements")
async def get_document_requirements(
    purchase_order_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get document requirements for a purchase order confirmation.

    Returns the list of required and optional documents based on:
    - Company type and tier level
    - Product sector and compliance requirements
    - Confirmation interface type
    """
    try:
        purchase_order_uuid = UUID(purchase_order_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid purchase order ID format"
        )

    confirmation_service = ConfirmationService(db)

    # Get interface type first
    interface_response = confirmation_service.determine_confirmation_interface(
        purchase_order_uuid,
        current_user.company_id
    )

    # Get document requirements
    requirements = confirmation_service.get_document_requirements_for_po(
        purchase_order_uuid,
        interface_response.interface_type,
        current_user.company_id
    )

    # Get current document validation status
    validation_status = await confirmation_service.validate_document_requirements_for_confirmation(
        purchase_order_uuid,
        interface_response.interface_type,
        current_user.company_id
    )

    return {
        "purchase_order_id": purchase_order_id,
        "interface_type": interface_response.interface_type.value,
        "requirements": requirements,
        "validation_status": validation_status,
        "can_confirm": validation_status["all_required_uploaded"]
    }


@router.get("/{purchase_order_id}/document-validation-status")
async def get_document_validation_status(
    purchase_order_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get current document validation status for a purchase order.

    Returns real-time status of document uploads and validation.
    """
    try:
        purchase_order_uuid = UUID(purchase_order_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid purchase order ID format"
        )

    confirmation_service = ConfirmationService(db)

    # Get interface type
    interface_response = confirmation_service.determine_confirmation_interface(
        purchase_order_uuid,
        current_user.company_id
    )

    # Get validation status
    validation_status = await confirmation_service.validate_document_requirements_for_confirmation(
        purchase_order_uuid,
        interface_response.interface_type,
        current_user.company_id
    )

    return {
        "purchase_order_id": purchase_order_id,
        "validation_status": validation_status,
        "can_confirm": validation_status["all_required_uploaded"],
        "last_updated": datetime.utcnow().isoformat()
    }
