"""
Purchase Orders CRUD Operations
Handles basic create, read, update, delete operations
"""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc

from app.core.database import get_db
from app.core.auth import get_current_user_sync, CurrentUser
from app.core.data_access_middleware import require_po_access, AccessType
from app.core.logging import get_logger
from app.core.po_error_handling import (
    POErrorHandler, 
    validate_uuid, 
    validate_po_state, 
    validate_company_access,
    handle_database_operation
)
from app.models.purchase_order import PurchaseOrder
from app.models.company import Company
from app.models.product import Product
from app.schemas.purchase_order import (
    PurchaseOrderCreate,
    PurchaseOrderUpdate,
    PurchaseOrderResponse,
    PurchaseOrderListResponse,
    PurchaseOrderFilter
)

logger = get_logger(__name__)

router = APIRouter(prefix="/purchase-orders", tags=["purchase-orders-crud"])


@router.get("/", response_model=PurchaseOrderListResponse)
def get_purchase_orders(
    filters: PurchaseOrderFilter = Depends(),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user_sync)
):
    """
    Get purchase orders with filtering and pagination.
    """
    try:
        # Build query
        query = db.query(PurchaseOrder)
        
        # Apply filters
        if filters.buyer_company_id:
            query = query.filter(PurchaseOrder.buyer_company_id == filters.buyer_company_id)
        
        if filters.seller_company_id:
            query = query.filter(PurchaseOrder.seller_company_id == filters.seller_company_id)
        
        if filters.product_id:
            query = query.filter(PurchaseOrder.product_id == filters.product_id)
        
        if filters.status:
            query = query.filter(PurchaseOrder.status == filters.status)
        
        if filters.delivery_date_from:
            query = query.filter(PurchaseOrder.delivery_date >= filters.delivery_date_from)
        
        if filters.delivery_date_to:
            query = query.filter(PurchaseOrder.delivery_date <= filters.delivery_date_to)
        
        # Apply company isolation - users can only see POs where their company is involved
        query = query.filter(
            or_(
                PurchaseOrder.buyer_company_id == current_user.company_id,
                PurchaseOrder.seller_company_id == current_user.company_id
            )
        )
        
        # Get total count before pagination
        total = query.count()
        
        # Apply pagination
        page = filters.page or 1
        per_page = filters.per_page or 20
        offset = (page - 1) * per_page
        
        purchase_orders = query.order_by(desc(PurchaseOrder.created_at)).offset(offset).limit(per_page).all()
        
        # Calculate total pages
        total_pages = (total + per_page - 1) // per_page
        
        logger.info(
            "Retrieved purchase orders",
            user_id=str(current_user.id),
            company_id=str(current_user.company_id),
            total=total,
            page=page,
            per_page=per_page
        )
        
        return PurchaseOrderListResponse(
            purchase_orders=purchase_orders,
            total=total,
            page=page,
            per_page=per_page,
            total_pages=total_pages
        )
        
    except Exception as e:
        logger.error(f"Error retrieving purchase orders: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve purchase orders"
        )


@router.get("/{purchase_order_id}", response_model=PurchaseOrderResponse)
@require_po_access(AccessType.READ)
def get_purchase_order(
    purchase_order_id: str,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user_sync)
):
    """
    Get a specific purchase order by ID.
    """
    try:
        po_id = validate_uuid(purchase_order_id, "purchase order ID")
        purchase_order = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
        
        if not purchase_order:
            raise POErrorHandler.handle_not_found_error("Purchase order", purchase_order_id)
        
        logger.info(
            "Retrieved purchase order",
            user_id=str(current_user.id),
            po_id=purchase_order_id
        )
        
        return purchase_order
        
    except HTTPException:
        raise
    except Exception as e:
        raise POErrorHandler.handle_generic_error(e, "retrieve purchase order")


@router.post("/", response_model=PurchaseOrderResponse)
def create_purchase_order(
    po_data: PurchaseOrderCreate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user_sync)
):
    """
    Create a new purchase order.
    """
    try:
        # Validate that the buyer company exists
        buyer_company = db.query(Company).filter(Company.id == po_data.buyer_company_id).first()
        if not buyer_company:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Buyer company not found"
            )
        
        # Validate that the seller company exists
        seller_company = db.query(Company).filter(Company.id == po_data.seller_company_id).first()
        if not seller_company:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Seller company not found"
            )
        
        # Validate that the product exists
        product = db.query(Product).filter(Product.id == po_data.product_id).first()
        if not product:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Product not found"
            )
        
        # Create purchase order
        purchase_order = PurchaseOrder(
            po_number=po_data.po_number,
            buyer_company_id=po_data.buyer_company_id,
            seller_company_id=po_data.seller_company_id,
            product_id=po_data.product_id,
            quantity=po_data.quantity,
            unit_price=po_data.unit_price,
            total_amount=po_data.quantity * po_data.unit_price,
            unit=po_data.unit,
            delivery_date=po_data.delivery_date,
            delivery_location=po_data.delivery_location,
            status='pending',
            notes=po_data.notes
        )
        
        db.add(purchase_order)
        db.commit()
        db.refresh(purchase_order)
        
        logger.info(
            "Created purchase order",
            user_id=str(current_user.id),
            po_id=str(purchase_order.id),
            po_number=purchase_order.po_number
        )
        
        return purchase_order
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating purchase order: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create purchase order"
        )


@router.put("/{purchase_order_id}", response_model=PurchaseOrderResponse)
@require_po_access(AccessType.WRITE)
def update_purchase_order(
    purchase_order_id: str,
    po_data: PurchaseOrderUpdate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user_sync)
):
    """
    Update a purchase order.
    """
    try:
        po_id = UUID(purchase_order_id)
        purchase_order = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
        
        if not purchase_order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Purchase order not found"
            )
        
        # Check if PO can be updated (not in final states)
        if purchase_order.status in ['delivered', 'cancelled']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot update purchase order in final state"
            )
        
        # Update fields
        update_data = po_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(purchase_order, field, value)
        
        # Recalculate total if quantity or unit_price changed
        if 'quantity' in update_data or 'unit_price' in update_data:
            purchase_order.total_amount = purchase_order.quantity * purchase_order.unit_price
        
        db.commit()
        db.refresh(purchase_order)
        
        logger.info(
            "Updated purchase order",
            user_id=str(current_user.id),
            po_id=purchase_order_id
        )
        
        return purchase_order
        
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid purchase order ID format"
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating purchase order {purchase_order_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update purchase order"
        )


@router.delete("/{purchase_order_id}")
@require_po_access(AccessType.WRITE)
def delete_purchase_order(
    purchase_order_id: str,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user_sync)
):
    """
    Delete a purchase order.
    """
    try:
        po_id = UUID(purchase_order_id)
        purchase_order = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
        
        if not purchase_order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Purchase order not found"
            )
        
        # Check if PO can be deleted (only in draft or pending states)
        if purchase_order.status not in ['draft', 'pending']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete purchase order in current state"
            )
        
        db.delete(purchase_order)
        db.commit()
        
        logger.info(
            "Deleted purchase order",
            user_id=str(current_user.id),
            po_id=purchase_order_id
        )
        
        return {"message": "Purchase order deleted successfully"}
        
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid purchase order ID format"
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting purchase order {purchase_order_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete purchase order"
        )
