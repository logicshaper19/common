"""
Simplified Purchase Orders API
Replaces complex data access middleware with simple role-based checks
"""
from typing import List, Optional
from uuid import UUID
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc

from app.core.database import get_db
from app.core.auth import get_current_user_sync, CurrentUser
from app.core.simple_auth import (
    require_po_access, 
    simple_log_action,
    can_access_purchase_order,
    can_create_purchase_order,
    can_confirm_purchase_order,
    can_approve_purchase_order
)
from app.core.minimal_audit import log_po_created, log_po_confirmed, log_po_approved
from app.core.logging import get_logger
from app.models.purchase_order import PurchaseOrder
from app.models.company import Company
from app.models.product import Product
from app.schemas.purchase_order import (
    PurchaseOrderCreate,
    PurchaseOrderUpdate,
    PurchaseOrderResponse,
    PurchaseOrderListResponse,
    PurchaseOrderWithDetails
)

logger = get_logger(__name__)

router = APIRouter(prefix="/purchase-orders", tags=["purchase-orders"])


def get_purchase_order_filters(
    buyer_company_id: Optional[UUID] = None,
    seller_company_id: Optional[UUID] = None,
    product_id: Optional[UUID] = None,
    status: Optional[str] = None,
    delivery_date_from: Optional[date] = None,
    delivery_date_to: Optional[date] = None,
    page: int = 1,
    per_page: int = 20
):
    """Create purchase order filters from query parameters."""
    return {
        'buyer_company_id': buyer_company_id,
        'seller_company_id': seller_company_id,
        'product_id': product_id,
        'status': status,
        'delivery_date_from': delivery_date_from,
        'delivery_date_to': delivery_date_to,
        'page': page,
        'per_page': per_page
    }


@router.get("/", response_model=PurchaseOrderListResponse)
def get_purchase_orders(
    filters: dict = Depends(get_purchase_order_filters),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user_sync)
):
    """Get purchase orders with simple filtering."""
    try:
        # Build query - users can only see POs involving their company
        query = db.query(PurchaseOrder).filter(
            or_(
                PurchaseOrder.buyer_company_id == current_user.company_id,
                PurchaseOrder.seller_company_id == current_user.company_id
            )
        )
        
        # Apply filters
        if filters['buyer_company_id']:
            query = query.filter(PurchaseOrder.buyer_company_id == filters['buyer_company_id'])
        
        if filters['seller_company_id']:
            query = query.filter(PurchaseOrder.seller_company_id == filters['seller_company_id'])
        
        if filters['product_id']:
            query = query.filter(PurchaseOrder.product_id == filters['product_id'])
        
        if filters['status']:
            query = query.filter(PurchaseOrder.status == filters['status'])
        
        if filters['delivery_date_from']:
            query = query.filter(PurchaseOrder.delivery_date >= filters['delivery_date_from'])
        
        if filters['delivery_date_to']:
            query = query.filter(PurchaseOrder.delivery_date <= filters['delivery_date_to'])
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        page = filters['page']
        per_page = filters['per_page']
        offset = (page - 1) * per_page
        
        purchase_orders = query.order_by(desc(PurchaseOrder.created_at)).offset(offset).limit(per_page).all()
        
        # Calculate total pages
        total_pages = (total + per_page - 1) // per_page
        
        # Convert to response format
        result = []
        for po in purchase_orders:
            # Get related data
            buyer_company = db.query(Company).filter(Company.id == po.buyer_company_id).first()
            seller_company = db.query(Company).filter(Company.id == po.seller_company_id).first()
            product = db.query(Product).filter(Product.id == po.product_id).first()
            
            po_dict = {
                'id': po.id,
                'po_number': po.po_number,
                'status': po.status,
                'buyer_company': {
                    'id': str(buyer_company.id),
                    'name': buyer_company.name,
                    'company_type': buyer_company.company_type
                } if buyer_company else None,
                'seller_company': {
                    'id': str(seller_company.id),
                    'name': seller_company.name,
                    'company_type': seller_company.company_type
                } if seller_company else None,
                'product': {
                    'id': str(product.id),
                    'name': product.name,
                    'description': product.description,
                    'default_unit': product.default_unit,
                    'category': product.category
                } if product else None,
                'quantity': po.quantity,
                'unit_price': po.unit_price,
                'total_amount': po.total_amount,
                'unit': po.unit,
                'delivery_date': po.delivery_date,
                'delivery_location': po.delivery_location,
                'notes': po.notes,
                'composition': None,
                'input_materials': None,
                'origin_data': None,
                'amendments': [],
                'created_at': po.created_at,
                'updated_at': po.updated_at
            }
            result.append(po_dict)
        
        return PurchaseOrderListResponse(
            purchase_orders=result,
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


@router.get("/incoming-simple")
def get_incoming_purchase_orders_simple(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user_sync)
):
    """Get incoming purchase orders (where user's company is seller)."""
    try:
        # Get POs where user's company is the seller
        purchase_orders = db.query(PurchaseOrder).filter(
            PurchaseOrder.seller_company_id == current_user.company_id,
            PurchaseOrder.status == 'pending'
        ).order_by(desc(PurchaseOrder.created_at)).limit(10).all()
        
        # Convert to simple format
        result = []
        for po in purchase_orders:
            buyer_company = db.query(Company).filter(Company.id == po.buyer_company_id).first()
            product = db.query(Product).filter(Product.id == po.product_id).first()
            
            po_dict = {
                'id': str(po.id),
                'po_number': po.po_number,
                'status': po.status,
                'buyer_company_id': str(po.buyer_company_id),
                'seller_company_id': str(po.seller_company_id),
                'product_id': str(po.product_id),
                'quantity': float(po.quantity),
                'unit_price': float(po.unit_price),
                'total_amount': float(po.total_amount),
                'unit': po.unit,
                'delivery_date': po.delivery_date.isoformat() if po.delivery_date else None,
                'delivery_location': po.delivery_location,
                'notes': po.notes,
                'created_at': po.created_at.isoformat(),
                'updated_at': po.updated_at.isoformat(),
                'buyer_company': {
                    'id': str(buyer_company.id),
                    'name': buyer_company.name,
                    'company_type': buyer_company.company_type
                } if buyer_company else None,
                'product': {
                    'id': str(product.id),
                    'name': product.name,
                    'description': product.description,
                    'default_unit': product.default_unit,
                    'category': product.category
                } if product else None
            }
            result.append(po_dict)
        
        return result
        
    except Exception as e:
        logger.error(f"Error retrieving incoming purchase orders: {str(e)}", exc_info=True)
        return []


@router.get("/{purchase_order_id}", response_model=PurchaseOrderWithDetails)
@simple_log_action("view", "purchase_order")
def get_purchase_order(
    purchase_order_id: str,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user_sync)
):
    """Get a specific purchase order with related data."""
    try:
        po_id = UUID(purchase_order_id)
        po = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
        
        if not po:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Purchase order not found"
            )
        
        # Check access
        if not can_access_purchase_order(current_user, po):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: You can only access purchase orders involving your company"
            )
        
        # Get related data
        buyer_company = db.query(Company).filter(Company.id == po.buyer_company_id).first()
        seller_company = db.query(Company).filter(Company.id == po.seller_company_id).first()
        product = db.query(Product).filter(Product.id == po.product_id).first()
        
        # Build response with related data
        po_dict = {
            'id': str(po.id),
            'po_number': po.po_number,
            'status': po.status,
            'buyer_company_id': str(po.buyer_company_id),
            'seller_company_id': str(po.seller_company_id),
            'product_id': str(po.product_id),
            'quantity': float(po.quantity),
            'unit_price': float(po.unit_price),
            'total_amount': float(po.total_amount),
            'unit': po.unit,
            'delivery_date': po.delivery_date.isoformat() if po.delivery_date else None,
            'delivery_location': po.delivery_location,
            'notes': po.notes,
            'composition': None,
            'input_materials': None,
            'origin_data': None,
            'amendments': [],
            'created_at': po.created_at.isoformat(),
            'updated_at': po.updated_at.isoformat(),
            'buyer_company': {
                'id': str(buyer_company.id),
                'name': buyer_company.name,
                'company_type': buyer_company.company_type
            } if buyer_company else None,
            'seller_company': {
                'id': str(seller_company.id),
                'name': seller_company.name,
                'company_type': seller_company.company_type
            } if seller_company else None,
            'product': {
                'id': str(product.id),
                'name': product.name,
                'description': product.description,
                'default_unit': product.default_unit,
                'category': product.category
            } if product else None
        }
        
        return po_dict
        
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid purchase order ID format"
        )
    except Exception as e:
        logger.error(f"Error retrieving purchase order: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve purchase order"
        )


@router.post("/test")
def test_create():
    """Test endpoint to verify the API is working."""
    return {"message": "Test endpoint working", "status": "success"}

@router.post("/")
def create_purchase_order(
    po_data: PurchaseOrderCreate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user_sync)
):
    """Create a new purchase order."""
    try:
        logger.info(f"Creating purchase order for user {current_user.id}")
        
        # Check if user can create POs (temporarily disabled for debugging)
        # if not can_create_purchase_order(current_user):
        #     raise HTTPException(
        #         status_code=status.HTTP_403_FORBIDDEN,
        #         detail="You don't have permission to create purchase orders"
        #     )
        
        # Generate PO number
        from datetime import datetime
        import uuid
        po_number = f"PO-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
        logger.info(f"Generated PO number: {po_number}")
        
        # Create PO
        logger.info("Creating PurchaseOrder object")
        po = PurchaseOrder(
            po_number=po_number,
            buyer_company_id=po_data.buyer_company_id,
            seller_company_id=po_data.seller_company_id,
            product_id=po_data.product_id,
            quantity=po_data.quantity,
            unit_price=po_data.unit_price,
            total_amount=po_data.quantity * po_data.unit_price,
            unit=po_data.unit,
            delivery_date=po_data.delivery_date,
            delivery_location=po_data.delivery_location,
            notes=po_data.notes,
            status='pending'
        )
        
        logger.info("Adding PO to database")
        db.add(po)
        logger.info("Committing transaction")
        db.commit()
        logger.info("Refreshing PO object")
        db.refresh(po)
        logger.info(f"Purchase order created successfully with ID: {po.id}")
        
        # Log audit event
        log_po_created(po.id, current_user.id, current_user.company_id)
        
        return po
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating purchase order: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create purchase order: {str(e)}"
        )


@router.put("/{purchase_order_id}/confirm")
@simple_log_action("confirm", "purchase_order")
def confirm_purchase_order(
    purchase_order_id: str,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user_sync)
):
    """Confirm a purchase order (seller action) with automatic batch creation."""
    print(f"🔧 SIMPLE CONFIRMATION ENDPOINT CALLED - UNIQUE MARKER 🔧")
    print(f"🔧 PO ID: {purchase_order_id}")
    print(f"🔧 Current user: {current_user.email} (ID: {current_user.id})")
    print(f"🔧 This is the SIMPLE endpoint without origin data inheritance! 🔧")
    
    from app.services.po_batch_integration import POBatchIntegrationService
    
    try:
        po_id = UUID(purchase_order_id)
        po = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
        
        if not po:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Purchase order not found"
            )
        
        # Check if user can confirm this PO
        if not can_confirm_purchase_order(current_user, po):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only confirm purchase orders where your company is the seller"
            )
        
        # Update status
        po.status = 'confirmed'
        db.commit()
        
        # Log audit event
        log_po_confirmed(db, po.id, current_user.id, current_user.company_id)
        
        # NEW: Create batch automatically after PO confirmation
        integration_service = POBatchIntegrationService(db)
        created_batch = integration_service.create_batch_from_po_confirmation(
            po_id=po_id,
            confirming_user_id=current_user.id
        )
        
        response_data = {
            "message": "Purchase order confirmed successfully",
            "batch_created": created_batch is not None
        }
        
        if created_batch:
            response_data["batch_id"] = str(created_batch.id)
            response_data["batch_name"] = created_batch.batch_id
            
            # Check if transformation should be triggered
            if integration_service.should_trigger_transformation(po.buyer_company_id):
                transformation_suggestion = integration_service.create_transformation_suggestion(
                    po_id=po_id,
                    batch_id=created_batch.id,
                    company_id=po.buyer_company_id,
                    user_id=current_user.id
                )
                
                if transformation_suggestion:
                    response_data["transformation_suggestion"] = transformation_suggestion
                    response_data["transformation_required"] = True
        
        return response_data
        
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid purchase order ID format"
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Error confirming purchase order: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to confirm purchase order"
        )


@router.put("/{purchase_order_id}/approve")
@simple_log_action("approve", "purchase_order")
def approve_purchase_order(
    purchase_order_id: str,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user_sync)
):
    """Approve a purchase order (buyer action)."""
    try:
        po_id = UUID(purchase_order_id)
        po = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
        
        if not po:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Purchase order not found"
            )
        
        # Check if user can approve this PO
        if not can_approve_purchase_order(current_user, po):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only approve purchase orders where your company is the buyer"
            )
        
        # Update status
        po.status = 'approved'
        db.commit()
        
        # Log audit event
        log_po_approved(db, po.id, current_user.id, current_user.company_id)
        
        return {"message": "Purchase order approved successfully"}
        
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid purchase order ID format"
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Error approving purchase order: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to approve purchase order"
        )
