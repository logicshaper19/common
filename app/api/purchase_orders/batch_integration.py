"""
Purchase Orders Batch Integration
Handles integration with batch tracking and harvest management
"""
from typing import List, Optional
from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.core.database import get_db
from app.core.auth import get_current_user_sync, CurrentUser
from app.core.data_access_middleware import require_po_access, AccessType
from app.core.logging import get_logger
from app.models.purchase_order import PurchaseOrder
from app.models.batch import Batch
# Using Batch model for harvest batches - batch_type='harvest'
from app.schemas.purchase_order import (
    BatchConfirmationRequest,
    BatchConfirmationResponse
)

logger = get_logger(__name__)

router = APIRouter(prefix="/purchase-orders", tags=["purchase-orders-batch-integration"])


@router.post("/{purchase_order_id}/confirm-batches", response_model=BatchConfirmationResponse)
@require_po_access(AccessType.WRITE)
def confirm_purchase_order_batches(
    purchase_order_id: str,
    confirmation: BatchConfirmationRequest,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user_sync)
):
    """
    Confirm purchase order with specific harvest batches.
    """
    try:
        po_id = UUID(purchase_order_id)
        purchase_order = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
        
        if not purchase_order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Purchase order not found"
            )
        
        # Check if user's company is the seller
        if purchase_order.seller_company_id != current_user.company_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the seller can confirm batches for this purchase order"
            )
        
        # Check if PO is in correct state
        if purchase_order.status not in ['pending', 'confirmed']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Purchase order is not in a state that can be confirmed with batches"
            )
        
        # Validate harvest batches exist and belong to seller
        harvest_batches = []
        total_quantity = 0
        
        for batch_id in confirmation.harvest_batch_ids:
            harvest_batch = db.query(Batch).filter(
                and_(
                    Batch.id == batch_id,
                    Batch.company_id == current_user.company_id,
                    Batch.batch_type == 'harvest'
                )
            ).first()
            
            if not harvest_batch:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Harvest batch {batch_id} not found or not owned by your company"
                )
            
            # Check if batch is available (assuming there's a status field or we can check quantity > 0)
            if harvest_batch.quantity <= 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Harvest batch {batch_id} is not available for use"
                )
            
            harvest_batches.append(harvest_batch)
            total_quantity += float(harvest_batch.quantity)
        
        # Validate total quantity matches PO requirements
        if total_quantity < purchase_order.quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient harvest batch quantity. Required: {purchase_order.quantity}, Available: {total_quantity}"
            )
        
        # Create batches for the purchase order
        created_batches = []
        remaining_quantity = purchase_order.quantity
        
        for harvest_batch in harvest_batches:
            if remaining_quantity <= 0:
                break
            
            # Calculate how much of this harvest batch to use
            batch_quantity = min(remaining_quantity, harvest_batch.quantity)
            
            # Create a new batch for the purchase order
            batch = Batch(
                batch_id=f"PO-{purchase_order.po_number}-{len(created_batches) + 1}",
                batch_type='processing',  # This is a processing batch created from harvest
                product_id=purchase_order.product_id,
                quantity=batch_quantity,
                unit=purchase_order.unit,
                status='allocated',
                company_id=current_user.company_id,
                source_purchase_order_id=po_id,
                production_date=harvest_batch.production_date,
                created_by_user_id=current_user.id
            )
            
            db.add(batch)
            created_batches.append(batch)
            
            # Update harvest batch quantity
            harvest_batch.quantity -= batch_quantity
            # Note: Batch model doesn't have a status field, so we just update quantity
            
            remaining_quantity -= batch_quantity
        
        # Update purchase order status
        purchase_order.status = 'confirmed'
        purchase_order.seller_confirmed_at = datetime.utcnow()
        purchase_order.seller_notes = confirmation.notes
        purchase_order.confirmed_quantity = purchase_order.quantity
        purchase_order.confirmed_unit_price = purchase_order.unit_price
        purchase_order.confirmed_delivery_date = purchase_order.delivery_date
        purchase_order.confirmed_delivery_location = purchase_order.delivery_location
        
        db.commit()
        
        # Refresh batches to get their IDs
        for batch in created_batches:
            db.refresh(batch)
        
        logger.info(
            "Purchase order confirmed with batches",
            user_id=str(current_user.id),
            po_id=purchase_order_id,
            batch_count=len(created_batches),
            total_quantity=purchase_order.quantity
        )
        
        return BatchConfirmationResponse(
            success=True,
            message="Purchase order confirmed with batches successfully",
            purchase_order_id=purchase_order_id,
            batch_ids=[str(batch.id) for batch in created_batches],
            total_quantity=purchase_order.quantity,
            confirmed_at=purchase_order.seller_confirmed_at.isoformat()
        )
        
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid purchase order ID format"
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error confirming purchase order batches {purchase_order_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to confirm purchase order with batches"
        )


@router.get("/{purchase_order_id}/batches")
@require_po_access(AccessType.READ)
def get_purchase_order_batches(
    purchase_order_id: str,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user_sync)
):
    """
    Get all batches associated with a purchase order.
    """
    try:
        po_id = UUID(purchase_order_id)
        purchase_order = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
        
        if not purchase_order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Purchase order not found"
            )
        
        # Get batches for this purchase order
        batches = db.query(Batch).filter(Batch.purchase_order_id == po_id).all()
        
        logger.info(
            "Retrieved purchase order batches",
            user_id=str(current_user.id),
            po_id=purchase_order_id,
            batch_count=len(batches)
        )
        
        return {
            "purchase_order_id": purchase_order_id,
            "batches": [
                {
                    "id": str(batch.id),
                    "batch_number": batch.batch_number,
                    "quantity": float(batch.quantity),
                    "unit": batch.unit,
                    "status": batch.status,
                    "created_at": batch.created_at.isoformat(),
                    "source_harvest_batch_id": str(batch.source_harvest_batch_id) if batch.source_harvest_batch_id else None
                }
                for batch in batches
            ],
            "total_quantity": sum(float(batch.quantity) for batch in batches)
        }
        
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid purchase order ID format"
        )
    except Exception as e:
        logger.error(f"Error retrieving purchase order batches {purchase_order_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve purchase order batches"
        )


@router.get("/{purchase_order_id}/traceability")
@require_po_access(AccessType.READ)
def get_purchase_order_traceability(
    purchase_order_id: str,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user_sync)
):
    """
    Get traceability information for a purchase order.
    """
    try:
        po_id = UUID(purchase_order_id)
        purchase_order = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
        
        if not purchase_order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Purchase order not found"
            )
        
        # Get batches and their source harvest batches
        batches = db.query(Batch).filter(Batch.purchase_order_id == po_id).all()
        
        traceability_data = {
            "purchase_order": {
                "id": str(purchase_order.id),
                "po_number": purchase_order.po_number,
                "status": purchase_order.status,
                "quantity": float(purchase_order.quantity),
                "unit": purchase_order.unit,
                "created_at": purchase_order.created_at.isoformat()
            },
            "batches": [],
            "harvest_traceability": []
        }
        
        for batch in batches:
            batch_data = {
                "id": str(batch.id),
                "batch_id": batch.batch_id,
                "quantity": float(batch.quantity),
                "unit": batch.unit,
                "status": batch.status,
                "created_at": batch.created_at.isoformat()
            }
            
            # Get source harvest batch if available
            if batch.source_purchase_order_id:
                harvest_batch = db.query(Batch).filter(
                    Batch.id == batch.source_purchase_order_id
                ).first()
                
                if harvest_batch:
                    batch_data["source_harvest_batch"] = {
                        "id": str(harvest_batch.id),
                        "batch_id": harvest_batch.batch_id,
                        "production_date": harvest_batch.production_date.isoformat() if harvest_batch.production_date else None,
                        "location_name": harvest_batch.location_name,
                        "certifications": harvest_batch.certifications
                    }
            
            traceability_data["batches"].append(batch_data)
        
        logger.info(
            "Retrieved purchase order traceability",
            user_id=str(current_user.id),
            po_id=purchase_order_id,
            batch_count=len(batches)
        )
        
        return traceability_data
        
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid purchase order ID format"
        )
    except Exception as e:
        logger.error(f"Error retrieving purchase order traceability {purchase_order_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve purchase order traceability"
        )
