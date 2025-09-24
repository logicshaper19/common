"""
Thin ERP Sync Endpoint

This endpoint demonstrates the thin endpoint pattern for service integration:
- Only HTTP concerns (authentication, validation, error handling)
- Delegates complex operations to focused services
- Easy to test and maintain
"""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth import get_current_user_sync, CurrentUser
from app.core.logging import get_logger
from app.models.purchase_order import PurchaseOrder
from app.services.erp_integration import ERPIntegrationService

logger = get_logger(__name__)
router = APIRouter()


@router.post("/{po_id}/sync-to-erp")
async def sync_purchase_order_to_erp(
    po_id: UUID,
    erp_system: str = "SAP",
    current_user: CurrentUser = Depends(get_current_user_sync),
    db: Session = Depends(get_db)
):
    """
    Thin endpoint for ERP synchronization.
    
    This endpoint:
    - Handles HTTP authentication
    - Validates input format
    - Delegates complex ERP operations to focused service
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
    
    # HTTP concern: Validate user access
    if current_user.company_id not in [po.buyer_company_id, po.seller_company_id]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this purchase order"
        )
    
    # HTTP concern: Validate ERP system
    if erp_system not in ["SAP", "Oracle", "NetSuite"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported ERP system"
        )
    
    try:
        # Delegate to focused service
        erp_service = ERPIntegrationService(db, erp_system)
        result = erp_service.sync_purchase_order_to_erp(po_id)
        
        if result['success']:
            return {
                "message": "Purchase order successfully synced to ERP",
                "po_id": po_id,
                "erp_system": erp_system,
                "erp_po_id": result.get('erp_po_id'),
                "sync_timestamp": result['sync_timestamp']
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"ERP sync failed: {result['error']}"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to sync PO {po_id} to ERP: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/{po_id}/erp-sync-status")
async def get_erp_sync_status(
    po_id: UUID,
    erp_system: str = "SAP",
    current_user: CurrentUser = Depends(get_current_user_sync),
    db: Session = Depends(get_db)
):
    """
    Thin endpoint for ERP sync status checking.
    
    This endpoint:
    - Handles HTTP authentication
    - Validates input format
    - Delegates status checking to focused service
    - Returns HTTP responses
    """
    
    # HTTP concern: Get entity
    po = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
    if not po:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Purchase order not found"
        )
    
    # HTTP concern: Validate user access
    if current_user.company_id not in [po.buyer_company_id, po.seller_company_id]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this purchase order"
        )
    
    try:
        # Delegate to focused service
        erp_service = ERPIntegrationService(db, erp_system)
        status_info = erp_service.get_erp_sync_status(po_id)
        
        if 'error' in status_info:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Failed to get ERP status: {status_info['error']}"
            )
        
        return status_info
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get ERP sync status for PO {po_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/{po_id}/transparency-score")
async def get_transparency_score(
    po_id: UUID,
    current_user: CurrentUser = Depends(get_current_user_sync),
    db: Session = Depends(get_db)
):
    """
    Thin endpoint for transparency score calculation.
    
    This endpoint:
    - Handles HTTP authentication
    - Validates input format
    - Delegates complex calculations to focused service
    - Returns HTTP responses
    """
    
    # HTTP concern: Get entity
    po = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
    if not po:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Purchase order not found"
        )
    
    # HTTP concern: Validate user access
    if current_user.company_id not in [po.buyer_company_id, po.seller_company_id]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this purchase order"
        )
    
    try:
        # Delegate to focused service
        from app.services.transparency_calculation import TransparencyCalculationService
        transparency_service = TransparencyCalculationService(db)
        
        # Calculate transparency for the buyer company
        score = transparency_service.calculate_supply_chain_transparency(po.buyer_company_id)
        insights = transparency_service.get_transparency_insights(po.buyer_company_id)
        
        return {
            "po_id": po_id,
            "company_id": po.buyer_company_id,
            "transparency_score": {
                "overall": score.overall_score,
                "mill_percentage": score.mill_percentage,
                "plantation_percentage": score.plantation_percentage,
                "calculated_at": score.calculated_at.isoformat()
            },
            "insights": insights['insights'],
            "recommendations": insights['recommendations']
        }
        
    except Exception as e:
        logger.error(f"Failed to calculate transparency score for PO {po_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )
