"""
Thin Confirmation Endpoint

This endpoint demonstrates the thin endpoint pattern:
- Only HTTP concerns (authentication, validation, error handling)
- Delegates business logic to business logic functions
- Easy to test and maintain
"""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth import get_current_user_sync, CurrentUser
from app.core.logging import get_logger
from app.models.purchase_order import PurchaseOrder
from app.business_logic.purchase_order_operations import (
    confirm_purchase_order_business_logic,
    ConfirmationRequest,
    BusinessLogicError,
    ValidationError,
    AuthorizationError,
    StateTransitionError
)
from app.schemas.purchase_order import PurchaseOrderResponse

logger = get_logger(__name__)
router = APIRouter()


@router.post("/{po_id}/confirm", response_model=PurchaseOrderResponse)
async def confirm_purchase_order(
    po_id: UUID,
    confirmation_data: dict,
    current_user: CurrentUser = Depends(get_current_user_sync),
    db: Session = Depends(get_db)
):
    """
    Thin endpoint - just HTTP concerns and error handling.
    
    This endpoint:
    - Handles HTTP authentication
    - Validates input format
    - Delegates business logic to business logic functions
    - Handles HTTP error responses
    - Returns HTTP responses
    """
    
    # HTTP concern: Get entity
    po = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
    if not po:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Purchase order not found"
        )
    
    # HTTP concern: Validate input format
    try:
        quantity = float(confirmation_data.get('quantity', 0))
        discrepancy_reason = confirmation_data.get('discrepancy_reason')
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid quantity format"
        )
    
    # Create business logic request object
    confirmation = ConfirmationRequest(
        quantity=quantity,
        discrepancy_reason=discrepancy_reason
    )
    
    try:
        # Delegate to business logic function
        confirmed_po = confirm_purchase_order_business_logic(
            po, confirmation, current_user, db
        )
        
        # HTTP concern: Save changes
        db.add(confirmed_po)
        db.commit()
        db.refresh(confirmed_po)
        
        # HTTP concern: Return response
        return PurchaseOrderResponse.from_orm(confirmed_po)
        
    except AuthorizationError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except StateTransitionError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except BusinessLogicError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to confirm PO {po_id}: {str(e)}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post("/{po_id}/confirm-with-transparency", response_model=PurchaseOrderResponse)
async def confirm_purchase_order_with_transparency(
    po_id: UUID,
    confirmation_data: dict,
    current_user: CurrentUser = Depends(get_current_user_sync),
    db: Session = Depends(get_db)
):
    """
    Thin endpoint with service integration.
    
    This demonstrates how to integrate business logic functions
    with focused services for complex operations.
    """
    
    # HTTP concern: Get entity
    po = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
    if not po:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Purchase order not found"
        )
    
    # HTTP concern: Validate input format
    try:
        quantity = float(confirmation_data.get('quantity', 0))
        discrepancy_reason = confirmation_data.get('discrepancy_reason')
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid quantity format"
        )
    
    # Create business logic request object
    confirmation = ConfirmationRequest(
        quantity=quantity,
        discrepancy_reason=discrepancy_reason
    )
    
    try:
        # Use database transaction to ensure consistency
        with db.begin():  # This ensures atomic operation
            # Core business logic
            confirmed_po = confirm_purchase_order_business_logic(
                po, confirmation, current_user, db
            )
            
            # Save the PO changes
            db.add(confirmed_po)
            db.flush()  # Get the ID but don't commit yet
            
            # Only call complex services within the same transaction
            if confirmed_po.status == "confirmed":
                from app.services.transparency_calculation import TransparencyCalculationService
                transparency_service = TransparencyCalculationService(db)
                transparency_service.mark_for_recalculation(confirmed_po.id)
                # Note: Actual recalculation happens async to avoid long transactions
            
            # Transaction commits automatically on exit
        
        # Trigger async transparency recalculation outside transaction
        # if confirmed_po.status == "confirmed":
        #     transparency_calculation_job.delay(confirmed_po.id)
        
        return PurchaseOrderResponse.from_orm(confirmed_po)
        
    except AuthorizationError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except StateTransitionError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except BusinessLogicError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to confirm PO {po_id} with transparency: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )
