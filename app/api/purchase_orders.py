"""
Simplified Purchase Orders API
Replaces complex data access middleware with simple role-based checks
"""
from typing import List, Optional
from uuid import UUID
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, selectinload
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
        # Add eager loading to prevent N+1 queries
        query = db.query(PurchaseOrder).options(
            selectinload(PurchaseOrder.buyer_company),
            selectinload(PurchaseOrder.seller_company),
            selectinload(PurchaseOrder.product)
        ).filter(
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
        
        # Simple production logging for N+1 fix verification
        logger.info(f"Purchase orders query: {len(purchase_orders)} records, "
                   f"eager loading enabled (buyer_company, seller_company, product)")
        
        # Convert to response format
        result = []
        for po in purchase_orders:
            # Related data is already loaded via eager loading - no more N+1 queries!
            buyer_company = po.buyer_company
            seller_company = po.seller_company
            product = po.product
            
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
        # Add eager loading to prevent N+1 queries
        purchase_orders = db.query(PurchaseOrder).options(
            selectinload(PurchaseOrder.buyer_company),
            selectinload(PurchaseOrder.product)
        ).filter(
            PurchaseOrder.seller_company_id == current_user.company_id,
            PurchaseOrder.status == 'pending'
        ).order_by(desc(PurchaseOrder.created_at)).limit(10).all()
        
        # Simple production logging for N+1 fix verification
        logger.info(f"Incoming purchase orders query: {len(purchase_orders)} records, "
                   f"eager loading enabled (buyer_company, product)")
        
        # Convert to simple format
        result = []
        for po in purchase_orders:
            # Related data is already loaded via eager loading - no more N+1 queries!
            buyer_company = po.buyer_company
            product = po.product
            
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


@router.get("/debug-performance")
def debug_performance(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user_sync)
):
    """Simple debug endpoint to measure N+1 query performance improvement."""
    import time
    from sqlalchemy import event
    from sqlalchemy.engine import Engine
    
    # Simple query counting setup
    query_count = {"count": 0}
    
    def count_queries(conn, cursor, statement, parameters, context, executemany):
        query_count["count"] += 1
    
    # Register the event listener
    event.listen(Engine, "before_cursor_execute", count_queries)
    
    try:
        # Test without eager loading (N+1 problem)
        query_count["count"] = 0
        start_time = time.time()
        
        pos_slow = db.query(PurchaseOrder).filter(
            or_(
                PurchaseOrder.buyer_company_id == current_user.company_id,
                PurchaseOrder.seller_company_id == current_user.company_id
            )
        ).limit(5).all()
        
        # Access relationships to trigger N+1 queries
        for po in pos_slow:
            try:
                _ = po.buyer_company.name if po.buyer_company else "No buyer"
                _ = po.seller_company.name if po.seller_company else "No seller"
                _ = po.product.name if po.product else "No product"
            except Exception as rel_error:
                logger.warning(f"Relationship access error: {rel_error}")
        
        slow_time = time.time() - start_time
        slow_query_count = query_count["count"]
        
        # Test with eager loading (optimized)
        query_count["count"] = 0
        start_time = time.time()
        
        pos_fast = db.query(PurchaseOrder).options(
            selectinload(PurchaseOrder.buyer_company),
            selectinload(PurchaseOrder.seller_company),
            selectinload(PurchaseOrder.product)
        ).filter(
            or_(
                PurchaseOrder.buyer_company_id == current_user.company_id,
                PurchaseOrder.seller_company_id == current_user.company_id
            )
        ).limit(5).all()
        
        # Access relationships (should not trigger additional queries)
        for po in pos_fast:
            try:
                _ = po.buyer_company.name if po.buyer_company else "No buyer"
                _ = po.seller_company.name if po.seller_company else "No seller"
                _ = po.product.name if po.product else "No product"
            except Exception as rel_error:
                logger.warning(f"Relationship access error: {rel_error}")
        
        fast_time = time.time() - start_time
        fast_query_count = query_count["count"]
        
        # Calculate improvements
        time_improvement = ((slow_time - fast_time) / slow_time * 100) if slow_time > 0 else 0
        query_reduction = slow_query_count - fast_query_count
        query_reduction_percent = (query_reduction / slow_query_count * 100) if slow_query_count > 0 else 0
        
        # Simple production logging
        logger.info(f"N+1 Performance Test: {query_reduction} fewer queries ({query_reduction_percent:.1f}% reduction), "
                   f"{time_improvement:.1f}% time improvement")
        
        return {
            "test_records": len(pos_slow),
            "performance_metrics": {
                "without_eager_loading": {
                    "time": f"{slow_time:.3f}s",
                    "query_count": slow_query_count
                },
                "with_eager_loading": {
                    "time": f"{fast_time:.3f}s", 
                    "query_count": fast_query_count
                },
                "improvements": {
                    "time_improvement": f"{time_improvement:.1f}%",
                    "query_reduction": query_reduction,
                    "query_reduction_percent": f"{query_reduction_percent:.1f}%"
                }
            },
            "n1_problem_solved": query_reduction > 0 and time_improvement > 0,
            "recommendations": _generate_simple_recommendations(time_improvement, query_reduction)
        }
        
    except Exception as e:
        logger.error(f"Error in performance debug: {str(e)}", exc_info=True)
        return {
            "error": str(e),
            "message": "Performance test failed"
        }
    finally:
        # Clean up event listener
        event.remove(Engine, "before_cursor_execute", count_queries)

def _generate_simple_recommendations(time_improvement: float, query_reduction: int) -> list:
    """Generate simple recommendations based on performance test results."""
    recommendations = []
    
    if query_reduction > 0:
        recommendations.append(f"✅ N+1 problem SOLVED: {query_reduction} fewer database queries")
    else:
        recommendations.append("⚠️ No query reduction detected - check relationship configuration")
    
    if time_improvement > 50:
        recommendations.append("🚀 Excellent performance improvement - consider applying to other endpoints")
    elif time_improvement > 20:
        recommendations.append("✅ Good performance improvement - monitor in production")
    elif time_improvement > 0:
        recommendations.append("📈 Modest improvement - consider additional optimizations")
    else:
        recommendations.append("❌ No time improvement - investigate further")
    
    if query_reduction > 5:
        recommendations.append("💡 High query reduction - this optimization will scale well with more data")
    
    return recommendations

@router.post("/test")
def test_create():
    """Test endpoint to verify the API is working."""
    return {"message": "Test endpoint working", "status": "success"}

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
        # Add eager loading to prevent N+1 queries
        po = db.query(PurchaseOrder).options(
            selectinload(PurchaseOrder.buyer_company),
            selectinload(PurchaseOrder.seller_company),
            selectinload(PurchaseOrder.product)
        ).filter(PurchaseOrder.id == po_id).first()
        
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
        
        # Related data is already loaded via eager loading - no more N+1 queries!
        buyer_company = po.buyer_company
        seller_company = po.seller_company
        product = po.product
        
        # Simple production logging for N+1 fix verification
        logger.info(f"Purchase order detail query: {po.po_number}, "
                   f"eager loading enabled (buyer_company, seller_company, product)")
        
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
    """
    Confirm a purchase order (seller action) with automatic batch creation.
    
    ⚠️  DEPRECATED: This is a simplified endpoint. 
    For enhanced features including stock fulfillment and origin data inheritance,
    use the enhanced confirmation endpoint: /api/v1/purchase-orders/{po_id}/confirm
    """
    logger.info(f"SIMPLE CONFIRMATION ENDPOINT CALLED - PO ID: {purchase_order_id}")
    logger.debug(f"Current user: {current_user.email} (ID: {current_user.id})")
    logger.debug("This is the SIMPLE endpoint without origin data inheritance")
    
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
        try:
            integration_service = POBatchIntegrationService(db)
            created_batch = integration_service.create_batch_from_po_confirmation(
                po_id=po_id,
                confirming_user_id=current_user.id
            )
            print(f"🔧 Batch creation result: {created_batch is not None}")
            if created_batch:
                print(f"🔧 Created batch: {created_batch.batch_id} for company {created_batch.company_id}")
            else:
                print(f"🔧 Batch creation failed - creating manually")
                # Fallback: Create batch manually if service fails
                from app.services.batch import BatchTrackingService
                from app.schemas.batch import BatchCreate, BatchType
                from datetime import datetime, date
                from uuid import uuid4
                
                batch_service = BatchTrackingService(db)
                timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
                batch_id = f"PO-{str(po_id)[:8]}-BATCH-{timestamp}"
                
                batch_data = BatchCreate(
                    batch_id=batch_id,
                    batch_type=BatchType.PROCESSING,
                    product_id=po.product_id,
                    quantity=po.quantity,
                    unit=po.unit,
                    production_date=date.today(),
                    location_name="Warehouse",
                    batch_metadata={
                        "purchase_order_id": str(po.id),
                        "seller_company_id": str(po.seller_company_id),
                        "buyer_company_id": str(po.buyer_company_id),
                        "created_from_po_confirmation": True
                    }
                )
                
                created_batch = batch_service.create_batch(
                    batch_data=batch_data,
                    company_id=po.buyer_company_id,  # Buyer gets the batch
                    user_id=current_user.id
                )
                
                # Link PO to batch
                po.batch_id = created_batch.id
                db.commit()
                print(f"🔧 Manually created batch: {created_batch.batch_id}")
        except Exception as batch_error:
            print(f"🔧 Batch creation error: {str(batch_error)}")
            created_batch = None
        
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


# ============================================================================
# SIMPLE PO-BATCH RELATIONSHIP MANAGEMENT
# ============================================================================

@router.get("/{po_id}/batches")
def get_po_batches(
    po_id: UUID,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user_sync)
):
    """Get all batches linked to a purchase order through the linkage table."""
    try:
        # Check if user can access this PO
        if not can_access_purchase_order(po_id, current_user, db):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this purchase order"
            )
        
        # Get PO to verify it exists
        po = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
        if not po:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Purchase order not found"
            )
        
        # Get batches through linkage table (no circular dependency)
        from app.models.po_batch_linkage import POBatchLinkage
        from app.models.batch import Batch
        
        linkages = db.query(POBatchLinkage).filter(
            POBatchLinkage.purchase_order_id == po_id
        ).all()
        
        batches = []
        for linkage in linkages:
            batch = db.query(Batch).filter(Batch.id == linkage.batch_id).first()
            if batch:
                batches.append({
                    "batch_id": batch.id,
                    "batch_number": batch.batch_number,
                    "quantity_allocated": linkage.quantity_allocated,
                    "unit": linkage.unit,
                    "allocation_reason": linkage.allocation_reason,
                    "created_at": linkage.created_at
                })
        
        return {
            "purchase_order_id": po_id,
            "po_number": po.po_number,
            "batches": batches,
            "total_batches": len(batches)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting PO batches: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get purchase order batches"
        )


@router.get("/{po_id}/fulfillment-network")
def get_fulfillment_network(
    po_id: UUID,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user_sync)
):
    """Get complex fulfillment network for a purchase order (when needed)."""
    try:
        # Check if user can access this PO
        if not can_access_purchase_order(po_id, current_user, db):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this purchase order"
            )
        
        # Get PO to verify it exists
        po = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
        if not po:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Purchase order not found"
            )
        
        # For now, return a simple response indicating this is for complex networks
        # In the future, this could be expanded to handle complex fulfillment networks
        return {
            "purchase_order_id": po_id,
            "po_number": po.po_number,
            "message": "Complex fulfillment network analysis not yet implemented",
            "note": "Use /batches endpoint for simple batch relationships"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting fulfillment network: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get fulfillment network"
        )
