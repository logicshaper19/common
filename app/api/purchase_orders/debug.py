"""
Purchase Orders Debug Endpoints
Simple endpoints for debugging and testing
"""
from typing import List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth import get_current_user_sync, CurrentUser
from app.core.logging import get_logger
from app.models.purchase_order import PurchaseOrder
from app.models.company import Company
from app.models.product import Product

logger = get_logger(__name__)

router = APIRouter(prefix="/purchase-orders", tags=["purchase-orders-debug"])


@router.get("/test-simple")
def test_simple():
    """Simple test endpoint without any decorators or dependencies."""
    return {"message": "API is working!", "data": []}


@router.get("/test-auth-simple")
def test_auth_simple(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user_sync)
):
    """Simple test endpoint with authentication but no data access middleware."""
    return {
        "message": "Authentication working!",
        "user_id": str(current_user.id),
        "user_email": current_user.email,
        "company_id": str(current_user.company_id)
    }


@router.get("/test-no-auth")
def test_no_auth():
    """Simple test endpoint without any authentication or middleware."""
    return {"message": "No auth endpoint working!"}


@router.get("/debug-auth")
def debug_auth(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user_sync)
):
    """Debug endpoint to check authentication and user data."""
    return {
        "message": "Authentication working!",
        "user_id": str(current_user.id),
        "user_email": current_user.email,
        "company_id": str(current_user.company_id),
        "company_name": current_user.company.name if current_user.company else None,
        "is_active": current_user.is_active,
        "role": current_user.role
    }


@router.get("/incoming-simple-working")
def get_incoming_purchase_orders_working(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user_sync)
):
    """
    Working version of incoming purchase orders - bypasses data access middleware.
    """
    try:
        # Debug logging
        logger.info(f"Getting incoming POs for user {current_user.email}, company_id: {current_user.company_id}")
        
        # Very simple query - just get the POs first
        purchase_orders = db.query(PurchaseOrder).filter(
            PurchaseOrder.seller_company_id == current_user.company_id,
            PurchaseOrder.status == 'pending'
        ).order_by(PurchaseOrder.created_at.desc()).limit(10).all()
        
        logger.info(f"Found {len(purchase_orders)} purchase orders")
        
        # Convert to response format
        result = []
        for po in purchase_orders:
            # Get related data separately to avoid complex joins
            buyer_company = db.query(Company).filter(Company.id == po.buyer_company_id).first()
            seller_company = db.query(Company).filter(Company.id == po.seller_company_id).first()
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
            result.append(po_dict)
        
        return result
        
    except Exception as e:
        logger.error(f"Error in get_incoming_purchase_orders_working: {str(e)}", exc_info=True)
        return []


@router.get("/incoming-direct", include_in_schema=False)
def get_incoming_purchase_orders_direct(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user_sync)
):
    """
    Direct endpoint for incoming purchase orders - bypasses complex middleware.
    """
    try:
        # Simple query - get POs where current user's company is the seller
        purchase_orders = db.query(PurchaseOrder).filter(
            PurchaseOrder.seller_company_id == current_user.company_id,
            PurchaseOrder.status == 'pending'
        ).order_by(PurchaseOrder.created_at.desc()).limit(20).all()
        
        # Convert to simple response format
        result = []
        for po in purchase_orders:
            # Get related data with simple queries
            buyer_company = db.query(Company).filter(Company.id == po.buyer_company_id).first()
            product = db.query(Product).filter(Product.id == po.product_id).first()
            
            po_data = {
                'id': str(po.id),
                'po_number': po.po_number,
                'status': po.status,
                'quantity': float(po.quantity),
                'unit_price': float(po.unit_price),
                'total_amount': float(po.total_amount),
                'unit': po.unit,
                'delivery_date': po.delivery_date.isoformat() if po.delivery_date else None,
                'delivery_location': po.delivery_location,
                'notes': po.notes,
                'created_at': po.created_at.isoformat(),
                'buyer_company': {
                    'id': str(buyer_company.id),
                    'name': buyer_company.name,
                    'company_type': buyer_company.company_type
                } if buyer_company else None,
                'product': {
                    'id': str(product.id),
                    'name': product.name,
                    'description': product.description,
                    'category': product.category
                } if product else None
            }
            result.append(po_data)
        
        return {
            "success": True,
            "data": result,
            "count": len(result)
        }
        
    except Exception as e:
        logger.error(f"Error in get_incoming_purchase_orders_direct: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "data": []
        }


@router.post("/{po_id}/accept-simple")
def accept_purchase_order_simple(
    po_id: str,
    acceptance_data: dict,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user_sync)
):
    """
    Simple accept purchase order endpoint - bypasses complex middleware.
    """
    try:
        # Get the purchase order
        po = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
        if not po:
            return {"success": False, "error": "Purchase order not found"}
        
        # Check if user's company is the seller
        if po.seller_company_id != current_user.company_id:
            return {"success": False, "error": "Not authorized to accept this purchase order"}
        
        # Update the purchase order status
        po.status = 'accepted'
        po.seller_notes = acceptance_data.get('notes', '')
        po.seller_confirmed_at = datetime.utcnow()
        
        db.commit()
        
        return {
            "success": True,
            "message": "Purchase order accepted successfully",
            "po_id": po_id
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error accepting purchase order {po_id}: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@router.post("/{po_id}/reject-simple")
def reject_purchase_order_simple(
    po_id: str,
    rejection_data: dict,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user_sync)
):
    """
    Simple reject purchase order endpoint - bypasses complex middleware.
    """
    try:
        # Get the purchase order
        po = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
        if not po:
            return {"success": False, "error": "Purchase order not found"}
        
        # Check if user's company is the seller
        if po.seller_company_id != current_user.company_id:
            return {"success": False, "error": "Not authorized to reject this purchase order"}
        
        # Update the purchase order status
        po.status = 'rejected'
        po.seller_notes = rejection_data.get('reason', '')
        po.seller_confirmed_at = datetime.utcnow()
        
        db.commit()
        
        return {
            "success": True,
            "message": "Purchase order rejected successfully",
            "po_id": po_id
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error rejecting purchase order {po_id}: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }
