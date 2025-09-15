"""
Purchase order API endpoints.
"""
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from math import ceil
from datetime import date

from app.core.database import get_db
from app.core.auth import get_current_user_sync
from app.models.user import User
from app.services.purchase_order import create_purchase_order_service, PurchaseOrderService
from app.core.permissions import (
    require_po_creation_permission,
    require_po_confirmation_permission,
    get_permission_checker,
    PermissionChecker
)
from app.services.po_chaining import POChainingService
from app.schemas.purchase_order import (
    PurchaseOrderCreate,
    PurchaseOrderUpdate,
    PurchaseOrderResponse,
    PurchaseOrderWithDetails,
    PurchaseOrderListResponse,
    PurchaseOrderFilter,
    TraceabilityRequest,
    TraceabilityResponse,
    PurchaseOrderStatus,
    SellerConfirmation,
    PurchaseOrderConfirmation,
    BuyerApprovalRequest,
    DiscrepancyResponse,
    DiscrepancyDetail,
    PurchaseOrderHistoryEntry,
    ProposeChangesRequest,
    ApproveChangesRequest,
    AmendmentResponse,
    AmendmentStatus
)
from app.core.logging import get_logger
from app.core.data_access_middleware import require_po_access, filter_response_data, AccessType
# from app.core.rate_limiting import rate_limit, RateLimitType
from app.models.data_access import DataCategory, AccessType
from app.core.response_wrapper import standardize_response, standardize_list_response, ResponseBuilder
from app.core.response_models import StandardResponse, PaginatedResponse
from app.models.purchase_order import PurchaseOrder
from app.schemas.batch import BatchCreate, BatchType
from app.models.batch import Batch

logger = get_logger(__name__)

router = APIRouter(prefix="/purchase-orders", tags=["purchase-orders"])


@router.post("/", response_model=PurchaseOrderResponse)
@require_po_creation_permission
# # @rate_limit(RateLimitType.STANDARD)  # Temporarily disabled for testing
async def create_purchase_order(
    purchase_order: PurchaseOrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_sync)
):
    """
    Create a new purchase order.
    
    Only users from the buyer or seller company can create the purchase order.
    """
    try:
        logger.info(
            "Creating purchase order via API",
            user_id=str(current_user.id),
            company_id=str(current_user.company_id),
            buyer_company_id=str(purchase_order.buyer_company_id),
            seller_company_id=str(purchase_order.seller_company_id),
            product_id=str(purchase_order.product_id)
        )
        
        purchase_order_service = create_purchase_order_service(db)
        
        created_po = purchase_order_service.create_purchase_order(
            purchase_order, 
            current_user.company_id
        )
        
        logger.info(
            "Purchase order created via API",
            po_id=str(created_po.id),
            user_id=str(current_user.id),
            company_id=str(current_user.company_id)
        )
        
        return created_po
        
    except Exception as e:
        logger.error(
            "Error creating purchase order via API",
            error=str(e),
            error_type=type(e).__name__,
            user_id=str(current_user.id),
            company_id=str(current_user.company_id),
            buyer_company_id=str(purchase_order.buyer_company_id),
            seller_company_id=str(purchase_order.seller_company_id),
            product_id=str(purchase_order.product_id),
            exc_info=True
        )
        raise


@router.get("/", response_model=PurchaseOrderListResponse)
def list_purchase_orders(
    buyer_company_id: str = Query(None, description="Filter by buyer company ID"),
    seller_company_id: str = Query(None, description="Filter by seller company ID"),
    product_id: str = Query(None, description="Filter by product ID"),
    status: str = Query(None, description="Filter by status (comma-separated for multiple)"),
    delivery_date_from: str = Query(None, description="Filter by delivery date from (YYYY-MM-DD)"),
    delivery_date_to: str = Query(None, description="Filter by delivery date to (YYYY-MM-DD)"),
    search: str = Query(None, description="Search in PO number, notes, or delivery location"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_sync)
):
    """
    List purchase orders with filtering and pagination.
    
    Users can only see purchase orders where their company is the buyer or seller.
    """
    from datetime import datetime
    from uuid import UUID
    
    # Parse date filters
    delivery_date_from_parsed = None
    delivery_date_to_parsed = None
    
    if delivery_date_from:
        try:
            delivery_date_from_parsed = datetime.strptime(delivery_date_from, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid delivery_date_from format. Use YYYY-MM-DD"
            )
    
    if delivery_date_to:
        try:
            delivery_date_to_parsed = datetime.strptime(delivery_date_to, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid delivery_date_to format. Use YYYY-MM-DD"
            )
    
    # Parse UUID filters
    buyer_company_id_parsed = None
    seller_company_id_parsed = None
    product_id_parsed = None
    
    if buyer_company_id:
        if buyer_company_id == "current":
            # Special case: use current user's company ID
            buyer_company_id_parsed = current_user.company_id
        else:
            try:
                buyer_company_id_parsed = UUID(buyer_company_id)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid buyer_company_id format"
                )
    
    if seller_company_id:
        if seller_company_id == "current":
            # Special case: use current user's company ID
            seller_company_id_parsed = current_user.company_id
        else:
            try:
                seller_company_id_parsed = UUID(seller_company_id)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid seller_company_id format"
                )
    
    if product_id:
        try:
            product_id_parsed = UUID(product_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid product_id format"
            )
    
    # Parse status filter (comma-separated values)
    status_list = None
    if status:
        status_values = [s.strip() for s in status.split(',')]
        try:
            status_list = [PurchaseOrderStatus(s) for s in status_values]
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status value: {str(e)}"
            )
    
    # Create filter object
    filters = PurchaseOrderFilter(
        buyer_company_id=buyer_company_id_parsed,
        seller_company_id=seller_company_id_parsed,
        product_id=product_id_parsed,
        status=status_list,
        delivery_date_from=delivery_date_from_parsed,
        delivery_date_to=delivery_date_to_parsed,
        search=search,
        page=page,
        per_page=per_page
    )
    
    purchase_order_service = PurchaseOrderService(db)
    purchase_orders, total_count = purchase_order_service.list_purchase_orders_with_details(
        filters,
        current_user.company_id
    )
    
    total_pages = ceil(total_count / per_page)
    
    logger.info(
        "Purchase orders listed",
        user_id=str(current_user.id),
        company_id=str(current_user.company_id),
        page=page,
        per_page=per_page,
        total_count=total_count
    )
    
    return PurchaseOrderListResponse(
        purchase_orders=purchase_orders,
        total=total_count,
        page=page,
        per_page=per_page,
        total_pages=total_pages
    )


@router.get("/{purchase_order_id}", response_model=PurchaseOrderWithDetails)
@require_po_access(AccessType.READ)
@filter_response_data(
    data_category=DataCategory.PURCHASE_ORDER,
    entity_type="purchase_order",
    target_company_field="seller_company_id"
)
def get_purchase_order(
    purchase_order_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_sync)
):
    """
    Get a specific purchase order by ID.
    
    Users can only access purchase orders where their company is the buyer or seller.
    """
    purchase_order_service = PurchaseOrderService(db)
    
    purchase_order = purchase_order_service.get_purchase_order_with_details(purchase_order_id)
    if not purchase_order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Purchase order not found"
        )
    
    # Check access permissions (admins and processors may view all POs)
    if current_user.role != 'admin':
        # Check if user is from a processor company
        from app.models.company import Company
        user_company = db.query(Company).filter(Company.id == current_user.company_id).first()
        
        if not (user_company and user_company.company_type == "processor"):
            # Non-processor companies can only see POs where they are buyer or seller
            if (current_user.company_id != purchase_order.buyer_company["id"] and
                current_user.company_id != purchase_order.seller_company["id"]):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You can only access purchase orders for your own company"
                )

    logger.info(
        "Purchase order retrieved",
        po_id=purchase_order_id,
        user_id=str(current_user.id),
        company_id=str(current_user.company_id)
    )
    
    return purchase_order


@router.put("/{purchase_order_id}", response_model=PurchaseOrderResponse)
@require_po_access(AccessType.WRITE)
def update_purchase_order(
    purchase_order_id: str,
    purchase_order_update: PurchaseOrderUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_sync)
):
    """
    Update a purchase order.
    
    Both buyer and seller companies can update the purchase order.
    """
    purchase_order_service = PurchaseOrderService(db)
    
    updated_po = purchase_order_service.update_purchase_order(
        purchase_order_id,
        purchase_order_update,
        current_user.company_id
    )
    
    logger.info(
        "Purchase order updated via API",
        po_id=purchase_order_id,
        user_id=str(current_user.id),
        company_id=str(current_user.company_id)
    )
    
    return updated_po


@router.post("/{purchase_order_id}/seller-confirm", response_model=PurchaseOrderResponse)
@require_po_access(AccessType.WRITE)
def seller_confirm_purchase_order(
    purchase_order_id: str,
    confirmation: SellerConfirmation,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_sync)
):
    """
    Seller confirmation of purchase order with discrepancy detection.

    Only the seller company can confirm the purchase order.
    If discrepancies are detected, the PO status is set to AWAITING_BUYER_APPROVAL.
    If no discrepancies, the PO is confirmed immediately.
    """
    from datetime import datetime
    from app.services.discrepancy_detection import DiscrepancyDetectionService
    # from app.services.po_history import POHistoryService

    purchase_order_service = PurchaseOrderService(db)
    discrepancy_service = DiscrepancyDetectionService()
    # history_service = POHistoryService(db)

    # Get the PO to verify seller access
    po = purchase_order_service.get_purchase_order_by_id(purchase_order_id)
    if not po:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Purchase order not found"
        )

    # Verify user is from seller company
    if current_user.company_id != po.seller_company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the seller company can confirm this purchase order"
        )

    # Store original values if not already stored
    if po.original_quantity is None:
        po.original_quantity = po.quantity
        po.original_unit_price = po.unit_price
        po.original_delivery_date = po.delivery_date
        po.original_delivery_location = po.delivery_location

    # Detect discrepancies
    discrepancies = discrepancy_service.detect_discrepancies(po, confirmation)

    # Store seller confirmation data
    po.seller_confirmed_data = confirmation.model_dump()
    po.seller_confirmed_at = datetime.utcnow()

    if discrepancies:
        # Has discrepancies - require buyer approval
        po.status = PurchaseOrderStatus.AWAITING_BUYER_APPROVAL.value
        po.discrepancy_reason = discrepancy_service.create_discrepancy_reason(discrepancies)

        # Log history entry
        # history_service.log_seller_confirmation_with_discrepancies(
        #     purchase_order_id=po.id,
        #     user_id=current_user.id,
        #     company_id=current_user.company_id,
        #     po_number=po.po_number,
        #     discrepancies=[d.model_dump() for d in discrepancies]
        # )

        logger.info(
            "Purchase order confirmation requires buyer approval",
            po_id=purchase_order_id,
            user_id=str(current_user.id),
            company_id=str(current_user.company_id),
            discrepancies_count=len(discrepancies)
        )
    else:
        # No discrepancies - confirm immediately
        _confirm_po(po, confirmation, db, current_user, None)

        logger.info(
            "Purchase order confirmed by seller with no discrepancies",
            po_id=purchase_order_id,
            user_id=str(current_user.id),
            company_id=str(current_user.company_id),
            confirmed_quantity=str(confirmation.confirmed_quantity)
        )

    db.commit()
    db.refresh(po)

    # Convert to response format
    return purchase_order_service.get_purchase_order_with_details(purchase_order_id)


@router.post("/{purchase_order_id}/confirm", response_model=Dict[str, Any])
@require_po_confirmation_permission
@require_po_access(AccessType.WRITE)
def confirm_purchase_order(
    purchase_order_id: str,
    confirmation: PurchaseOrderConfirmation,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_sync)
):
    """
    Confirm a purchase order and automatically create child POs if needed.
    
    This endpoint handles the complete PO confirmation workflow:
    1. Confirms the received PO
    2. Automatically creates child POs to suppliers (if applicable)
    3. Updates fulfillment status and chain visibility
    """
    from datetime import datetime

    # Initialize services
    purchase_order_service = PurchaseOrderService(db)
    chaining_service = POChainingService(db)

    # Get the purchase order
    po = purchase_order_service.get_purchase_order(purchase_order_id)
    if not po:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Purchase order not found"
        )

    # Verify user is from seller company
    if current_user.company_id != po.seller_company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the seller company can confirm this purchase order"
        )

    # Check if PO is in a confirmable state
    if po.status not in [PurchaseOrderStatus.PENDING.value, PurchaseOrderStatus.AWAITING_CONFIRMATION.value]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Purchase order cannot be confirmed in current status: {po.status}"
        )

    # Prepare confirmation data
    confirmation_data = {
        "confirmed_at": datetime.utcnow(),
        "confirmed_quantity": confirmation.confirmed_quantity,
        "confirmed_unit_price": confirmation.confirmed_unit_price,
        "confirmed_delivery_date": confirmation.delivery_date,
        "confirmed_delivery_location": confirmation.delivery_location,
        "seller_notes": confirmation.notes
    }

    # Use chaining service to confirm PO and create child POs
    try:
        result = chaining_service.confirm_po_and_create_children(
            po_id=po.id,
            confirmation_data=confirmation_data,
            confirming_user_id=current_user.id
        )
        
        logger.info(
            "Purchase order confirmed with chaining",
            po_id=purchase_order_id,
            user_id=str(current_user.id),
            company_id=str(current_user.company_id),
            child_pos_created=len(result.get("child_pos_created", []))
        )
        
        return {
            "message": "Purchase order confirmed successfully",
            "po_id": purchase_order_id,
            "status": "confirmed",
            "child_pos_created": result.get("child_pos_created", []),
            "fulfillment_status": result.get("fulfillment_status"),
            "fulfillment_percentage": result.get("fulfillment_percentage")
        }
        
    except Exception as e:
        logger.error(
            "Failed to confirm PO with chaining",
            po_id=purchase_order_id,
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to confirm purchase order: {str(e)}"
        )


@router.get("/{purchase_order_id}/chain", response_model=Dict[str, Any])
def get_po_chain(
    purchase_order_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_sync)
):
    """
    Get the complete supply chain for a purchase order.
    
    Shows upstream chain (parents) and downstream chain (children)
    with appropriate visibility based on user's role and company.
    """
    chaining_service = POChainingService(db)
    
    try:
        chain_data = chaining_service.get_po_chain(purchase_order_id)
        
        # Filter chain data based on user permissions
        # For now, return full chain - in production, filter based on user role
        return {
            "success": True,
            "chain": chain_data
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(
            "Failed to get PO chain",
            po_id=purchase_order_id,
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get supply chain: {str(e)}"
        )


@router.post("/{purchase_order_id}/buyer-approve", response_model=PurchaseOrderResponse)
@require_po_access(AccessType.WRITE)
def buyer_approve_discrepancies(
    purchase_order_id: str,
    approval: BuyerApprovalRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_sync)
):
    """
    Buyer approval or rejection of seller confirmation discrepancies.

    Only the buyer company can approve/reject discrepancies.
    If approved, the PO is confirmed with the seller's values.
    If rejected, the PO status returns to PENDING for seller revision.
    """
    from datetime import datetime
    # from app.services.po_history import POHistoryService

    purchase_order_service = PurchaseOrderService(db)
    # history_service = POHistoryService(db)

    # Get the PO
    po = purchase_order_service.get_purchase_order_by_id(purchase_order_id)
    if not po:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Purchase order not found"
        )

    # Verify user is from buyer company
    if current_user.company_id != po.buyer_company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the buyer company can approve discrepancies"
        )

    # Verify PO is awaiting approval
    if po.status != PurchaseOrderStatus.AWAITING_BUYER_APPROVAL.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Purchase order is not awaiting buyer approval"
        )

    if approval.approve:
        # Buyer approved - apply seller's confirmation data and confirm PO
        seller_data = po.seller_confirmed_data

        # Create a SellerConfirmation object from stored data
        confirmation = SellerConfirmation(
            confirmed_quantity=seller_data.get('confirmed_quantity'),
            confirmed_unit_price=seller_data.get('confirmed_unit_price'),
            confirmed_delivery_date=seller_data.get('confirmed_delivery_date'),
            confirmed_delivery_location=seller_data.get('confirmed_delivery_location'),
            seller_notes=seller_data.get('seller_notes')
        )

        # Set buyer approval fields
        po.buyer_approved_at = datetime.utcnow()
        po.buyer_approval_user_id = current_user.id

        # Log approval
        # history_service.log_buyer_approval(
        #     purchase_order_id=po.id,
        #     user_id=current_user.id,
        #     company_id=current_user.company_id,
        #     po_number=po.po_number,
        #     approved=True,
        #     buyer_notes=approval.buyer_notes
        # )

        # Confirm the PO (this will create the batch automatically)
        _confirm_po(po, confirmation, db, current_user, None)

        logger.info(
            "Buyer approved discrepancies and confirmed PO",
            po_id=purchase_order_id,
            user_id=str(current_user.id),
            company_id=str(current_user.company_id)
        )
    else:
        # Buyer rejected - return to pending for seller revision
        po.status = PurchaseOrderStatus.PENDING.value
        po.discrepancy_reason = None
        po.seller_confirmed_data = None
        po.seller_confirmed_at = None

        # Log rejection
        # history_service.log_buyer_approval(
        #     purchase_order_id=po.id,
        #     user_id=current_user.id,
        #     company_id=current_user.company_id,
        #     po_number=po.po_number,
        #     approved=False,
        #     buyer_notes=approval.buyer_notes
        # )

        logger.info(
            "Buyer rejected discrepancies, PO returned to pending",
            po_id=purchase_order_id,
            user_id=str(current_user.id),
            company_id=str(current_user.company_id)
        )

    db.commit()
    db.refresh(po)

    return purchase_order_service.get_purchase_order_with_details(purchase_order_id)


@router.get("/{purchase_order_id}/discrepancies", response_model=DiscrepancyResponse)
@require_po_access(AccessType.READ)
def get_purchase_order_discrepancies(
    purchase_order_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_sync)
):
    """
    Get discrepancy details for a purchase order awaiting buyer approval.

    Returns the original vs confirmed values and discrepancy analysis.
    """
    import json
    from app.services.discrepancy_detection import DiscrepancyDetectionService

    purchase_order_service = PurchaseOrderService(db)
    discrepancy_service = DiscrepancyDetectionService()

    # Get the PO
    po = purchase_order_service.get_purchase_order_by_id(purchase_order_id)
    if not po:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Purchase order not found"
        )

    # Check if PO has discrepancies
    has_discrepancies = po.status == PurchaseOrderStatus.AWAITING_BUYER_APPROVAL.value

    if not has_discrepancies:
        return DiscrepancyResponse(
            has_discrepancies=False,
            discrepancies=[],
            requires_approval=False,
            seller_confirmation_data={}
        )

    # Parse discrepancy reason
    discrepancy_data = json.loads(po.discrepancy_reason) if po.discrepancy_reason else {}
    discrepancies = [
        DiscrepancyDetail(**d) for d in discrepancy_data.get("discrepancies", [])
    ]

    return DiscrepancyResponse(
        has_discrepancies=True,
        discrepancies=discrepancies,
        requires_approval=True,
        seller_confirmation_data=po.seller_confirmed_data or {}
    )


@router.get("/{purchase_order_id}/history", response_model=List[PurchaseOrderHistoryEntry])
@require_po_access(AccessType.READ)
def get_purchase_order_history(
    purchase_order_id: str,
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_sync)
):
    """
    Get the history/audit trail for a purchase order.

    Returns all actions performed on the purchase order in chronological order.
    """
    # from app.services.po_history import POHistoryService

    purchase_order_service = PurchaseOrderService(db)
    # history_service = POHistoryService(db)

    # Verify PO exists and user has access
    po = purchase_order_service.get_purchase_order_by_id(purchase_order_id)
    if not po:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Purchase order not found"
        )

    # Get history entries
    # history_entries = history_service.get_po_history(
    #     purchase_order_id=po.id,
    #     limit=limit
    # )

    # return history_entries
    return []  # Temporary return empty list


@router.delete("/{purchase_order_id}")
def delete_purchase_order(
    purchase_order_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_sync)
):
    """
    Delete a purchase order.
    
    Only the buyer company can delete draft purchase orders.
    """
    purchase_order_service = PurchaseOrderService(db)
    
    purchase_order_service.delete_purchase_order(
        purchase_order_id,
        current_user.company_id
    )
    
    logger.info(
        "Purchase order deleted via API",
        po_id=purchase_order_id,
        user_id=str(current_user.id),
        company_id=str(current_user.company_id)
    )
    
    return {"message": "Purchase order deleted successfully"}


@router.post("/trace", response_model=TraceabilityResponse)
# @rate_limit(RateLimitType.HEAVY)
def trace_supply_chain(
    request: TraceabilityRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_sync)
):
    """
    Trace the supply chain for a purchase order.
    
    Returns the complete traceability chain showing input materials and their sources.
    """
    purchase_order_service = PurchaseOrderService(db)
    
    # First check if user has access to the root purchase order
    root_po = purchase_order_service.get_purchase_order_with_details(str(request.purchase_order_id))
    if not root_po:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Purchase order not found"
        )
    
    # Check access permissions
    if (current_user.company_id != root_po.buyer_company["id"] and 
        current_user.company_id != root_po.seller_company["id"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only trace purchase orders for your own company"
        )
    
    traceability_result = purchase_order_service.trace_supply_chain(request)
    
    logger.info(
        "Supply chain traced",
        root_po_id=str(request.purchase_order_id),
        depth=request.depth,
        total_nodes=traceability_result.total_nodes,
        user_id=str(current_user.id),
        company_id=str(current_user.company_id)
    )
    
    return traceability_result


# Phase 1 MVP Amendment Endpoints

@router.put("/{po_id}/propose-changes", response_model=AmendmentResponse)
# @rate_limit(RateLimitType.STANDARD)
def propose_po_changes(
    po_id: str,
    proposal: ProposeChangesRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_sync)
):
    """
    Phase 1 MVP: Propose changes to a purchase order.

    Only sellers can propose changes to PENDING purchase orders.
    This is the core of the Phase 1 amendment workflow.
    """
    purchase_order_service = PurchaseOrderService(db)

    # Get the purchase order
    po = purchase_order_service.get_purchase_order(po_id)
    if not po:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Purchase order not found"
        )

    # Validate seller permissions
    if current_user.company_id != po.seller_company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the seller can propose changes to this purchase order"
        )

    # Validate PO status
    if po.status != PurchaseOrderStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only propose changes to PENDING purchase orders"
        )

    # Validate no existing pending amendment
    if po.amendment_status == AmendmentStatus.PROPOSED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="There is already a pending amendment for this purchase order"
        )

    # Apply the proposal
    result = purchase_order_service.propose_changes(po_id, proposal, current_user)

    logger.info(
        "Amendment proposed",
        po_id=po_id,
        proposed_quantity=str(proposal.proposed_quantity),
        original_quantity=str(po.quantity),
        seller_id=str(current_user.id),
        company_id=str(current_user.company_id)
    )

    return result


@router.put("/{po_id}/approve-changes", response_model=AmendmentResponse)
# @rate_limit(RateLimitType.STANDARD)
def approve_po_changes(
    po_id: str,
    approval: ApproveChangesRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_sync)
):
    """
    Phase 1 MVP: Approve or reject proposed changes to a purchase order.

    Only buyers can approve/reject amendments to purchase orders.
    """
    purchase_order_service = PurchaseOrderService(db)

    # Get the purchase order
    po = purchase_order_service.get_purchase_order(po_id)
    if not po:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Purchase order not found"
        )

    # Validate buyer permissions
    if current_user.company_id != po.buyer_company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the buyer can approve changes to this purchase order"
        )

    # Validate there's a pending amendment
    if po.amendment_status != AmendmentStatus.PROPOSED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No pending amendment to approve or reject"
        )

    # Apply the approval/rejection
    result = purchase_order_service.approve_changes(po_id, approval, current_user)

    action = "approved" if approval.approve else "rejected"
    logger.info(
        f"Amendment {action}",
        po_id=po_id,
        approved=approval.approve,
        buyer_id=str(current_user.id),
        company_id=str(current_user.company_id)
    )

    return result


def _confirm_po(
    po: "PurchaseOrder",
    confirmation: SellerConfirmation,
    db: Session,
    current_user: User,
    history_service: Optional[Any] = None
) -> None:
    """
    Core function to confirm a Purchase Order and create automatic batch.

    This function implements the critical transition from PO to Batch:
    1. Updates PO with confirmed values
    2. Sets status to CONFIRMED
    3. Creates deterministic batch automatically
    4. Links batch back to PO for full traceability

    Args:
        po: Purchase Order to confirm
        confirmation: Seller's confirmation data
        db: Database session
        current_user: User performing the confirmation
        history_service: Service for logging history
    """
    from datetime import datetime
    from decimal import Decimal
    from uuid import UUID
    from app.services.batch import BatchTrackingService
    from app.models.batch import Batch

    # 1. UPDATE PO WITH CONFIRMED VALUES
    po.confirmed_quantity = confirmation.confirmed_quantity
    po.confirmed_unit_price = confirmation.confirmed_unit_price
    po.confirmed_delivery_date = confirmation.confirmed_delivery_date
    po.confirmed_delivery_location = confirmation.confirmed_delivery_location
    po.seller_notes = confirmation.seller_notes
    po.status = PurchaseOrderStatus.CONFIRMED.value
    po.confirmed_at = datetime.utcnow()
    
    # 1.5. HANDLE COMMERCIAL CHAIN LINKING (NEW)
    if confirmation.is_drop_shipment and confirmation.parent_po_id:
        # This PO is fulfilling another PO (commercial chain)
        try:
            parent_po_uuid = UUID(confirmation.parent_po_id)
            parent_po = db.query(PurchaseOrder).filter(PurchaseOrder.id == parent_po_uuid).first()
            
            if parent_po:
                po.parent_po_id = parent_po_uuid
                po.supply_chain_level = parent_po.supply_chain_level + 1
                po.is_chain_initiated = False  # This is not the chain initiator
                
                logger.info(
                    "Commercial chain link established",
                    po_id=str(po.id),
                    parent_po_id=confirmation.parent_po_id,
                    supply_chain_level=po.supply_chain_level
                )
            else:
                logger.warning(
                    "Parent PO not found for commercial linking",
                    po_id=str(po.id),
                    parent_po_id=confirmation.parent_po_id
                )
        except ValueError:
            logger.warning(
                "Invalid parent PO ID format",
                po_id=str(po.id),
                parent_po_id=confirmation.parent_po_id
            )
    else:
        # This PO is initiating a new commercial chain
        po.is_chain_initiated = True
        po.supply_chain_level = 1

    # 2. LOG CONFIRMATION IN HISTORY
    # history_service.log_po_confirmed(
    #     purchase_order_id=po.id,
    #     user_id=current_user.id,
    #     company_id=current_user.company_id,
    #     po_number=po.po_number
    # )

    # 3. HANDLE BATCH CREATION - NEW CORRECTED FLOW
    batch_service = BatchTrackingService(db)

    try:
        if confirmation.selected_batches:
            # NEW FLOW: Use multiple selected harvest batches
            logger.info(
                "Using multiple selected harvest batches for PO confirmation",
                po_id=str(po.id),
                po_number=po.po_number,
                selected_batch_count=len(confirmation.selected_batches)
            )
            
            # Validate all selected batches
            harvest_batches = []
            total_quantity = Decimal('0')
            
            for batch_selection in confirmation.selected_batches:
                # Get the harvest batch
                harvest_batch = db.query(Batch).filter(Batch.id == batch_selection.batch_id).first()
                
                if not harvest_batch:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Selected harvest batch {batch_selection.batch_id} not found"
                    )
                
                # Verify the batch belongs to the seller
                if harvest_batch.company_id != po.seller_company_id:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Selected batch {batch_selection.batch_id} does not belong to seller company"
                    )
                
                # Verify it's a harvest batch
                if harvest_batch.batch_type != 'harvest':
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Selected batch {batch_selection.batch_id} is not a harvest batch"
                    )
                
                # Verify quantity doesn't exceed available
                if batch_selection.quantity_to_use > harvest_batch.quantity:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Requested quantity {batch_selection.quantity_to_use} exceeds available quantity {harvest_batch.quantity} for batch {batch_selection.batch_id}"
                    )
                
                harvest_batches.append((harvest_batch, batch_selection.quantity_to_use))
                total_quantity += batch_selection.quantity_to_use
            
            # Verify total quantity matches confirmed quantity
            if abs(total_quantity - confirmation.confirmed_quantity) > Decimal('0.001'):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Total selected quantity {total_quantity} does not match confirmed quantity {confirmation.confirmed_quantity}"
                )
            
            # Create PO batch that references all harvest batches
            po_batch_id = f"PO-{po.po_number}-BATCH-1"
            
            # Check if PO batch already exists
            existing_po_batch = db.query(Batch).filter(Batch.batch_id == po_batch_id).first()
            
            if existing_po_batch:
                logger.warning(
                    "PO batch already exists - skipping creation",
                    po_id=str(po.id),
                    batch_id=po_batch_id
                )
                po_batch = existing_po_batch
            else:
                # Use the first harvest batch as the primary source for metadata
                primary_harvest_batch = harvest_batches[0][0]
                
                # Create PO batch with reference to all harvest batches
                po_batch_data = BatchCreate(
                    batch_id=po_batch_id,
                    batch_type=BatchType.PROCESSING,  # PO batch is processing type
                    product_id=po.product_id,
                    quantity=confirmation.confirmed_quantity,
                    unit=po.unit,
                    production_date=date.today(),
                    expiry_date=None,
                    location_name=primary_harvest_batch.location_name,
                    location_coordinates=primary_harvest_batch.location_coordinates,
                    facility_code=primary_harvest_batch.facility_code,
                    quality_metrics=primary_harvest_batch.quality_metrics,
                    transformation_id=None,
                    parent_batch_ids=[batch[0].id for batch in harvest_batches],  # Link to all harvest batches
                    origin_data=primary_harvest_batch.origin_data,  # Inherit origin data from primary batch
                    certifications=primary_harvest_batch.certifications,  # Inherit certifications from primary batch
                    batch_metadata={
                        "created_from_po": True,
                        "purchase_order_id": str(po.id),
                        "source_harvest_batch_ids": [str(batch[0].id) for batch in harvest_batches],
                        "source_harvest_batch_numbers": [batch[0].batch_id for batch in harvest_batches],
                        "auto_created": True,
                        "creation_source": "purchase_order_confirmation_with_multiple_harvest_batches"
                    }
                )
                
                po_batch = batch_service.create_batch(
                    batch_data=po_batch_data,
                    company_id=po.seller_company_id,
                    user_id=current_user.id
                )
            
            # Create SALE relationships between each harvest batch and the PO batch
            from app.schemas.batch import BatchRelationshipCreate, RelationshipType
            
            for harvest_batch, quantity_used in harvest_batches:
                relationship_data = BatchRelationshipCreate(
                    parent_batch_id=harvest_batch.id,  # The harvest batch (seller's inventory)
                    child_batch_id=po_batch.id,       # The PO batch (buyer's new batch)
                    relationship_type=RelationshipType.SALE,
                    quantity_contribution=quantity_used,
                    percentage_contribution=(quantity_used / confirmation.confirmed_quantity) * Decimal('100.0'),
                    transformation_process="Commercial Sale",
                    transformation_date=datetime.utcnow(),
                    yield_percentage=Decimal('100.0'),
                    quality_impact=None
                )
                
                # Create the relationship using the batch service
                relationship = batch_service.create_batch_relationship(
                    relationship_data=relationship_data,
                    company_id=po.seller_company_id,
                    user_id=current_user.id
                )
                
                logger.info(
                    "SALE relationship created between harvest batch and PO batch",
                    po_id=str(po.id),
                    po_batch_id=str(po_batch.id),
                    harvest_batch_id=str(harvest_batch.id),
                    harvest_batch_number=harvest_batch.batch_id,
                    quantity_used=float(quantity_used),
                    relationship_id=str(relationship.id)
                )
            
            logger.info(
                "PO batch created with SALE relationships to multiple harvest batches",
                po_id=str(po.id),
                po_batch_id=str(po_batch.id),
                harvest_batch_count=len(harvest_batches),
                total_quantity=float(total_quantity)
            )
            
        elif confirmation.batch_id:
            # LEGACY FLOW: Use single selected harvest batch (deprecated)
            logger.warning(
                "Using legacy single batch selection - consider migrating to selected_batches",
                po_id=str(po.id),
                po_number=po.po_number,
                selected_batch_id=confirmation.batch_id
            )
            
            # Get the selected harvest batch
            harvest_batch = db.query(Batch).filter(Batch.id == confirmation.batch_id).first()
            
            if not harvest_batch:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Selected harvest batch not found"
                )
            
            # Verify the batch belongs to the seller
            if harvest_batch.company_id != po.seller_company_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Selected batch does not belong to seller company"
                )
            
            # Verify it's a harvest batch
            if harvest_batch.batch_type != 'harvest':
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Selected batch is not a harvest batch"
                )
            
            # Create PO batch that references the harvest batch
            po_batch_id = f"PO-{po.po_number}-BATCH-1"
            
            # Check if PO batch already exists
            existing_po_batch = db.query(Batch).filter(Batch.batch_id == po_batch_id).first()
            
            if existing_po_batch:
                logger.warning(
                    "PO batch already exists - skipping creation",
                    po_id=str(po.id),
                    batch_id=po_batch_id
                )
            else:
                # Create PO batch with reference to harvest batch
                po_batch_data = BatchCreate(
                    batch_id=po_batch_id,
                    batch_type=BatchType.PROCESSING,  # PO batch is processing type
                    product_id=po.product_id,
                    quantity=confirmation.confirmed_quantity,
                    unit=po.unit,
                    production_date=date.today(),
                    expiry_date=None,
                    location_name=harvest_batch.location_name,
                    location_coordinates=harvest_batch.location_coordinates,
                    facility_code=harvest_batch.facility_code,
                    quality_metrics=harvest_batch.quality_metrics,
                    transformation_id=None,
                    parent_batch_ids=[harvest_batch.id],  # Link to harvest batch
                    origin_data=harvest_batch.origin_data,  # Inherit origin data
                    certifications=harvest_batch.certifications,  # Inherit certifications
                    batch_metadata={
                        "created_from_po": True,
                        "purchase_order_id": str(po.id),
                        "source_harvest_batch_id": str(harvest_batch.id),
                        "source_harvest_batch_number": harvest_batch.batch_id,
                        "auto_created": True,
                        "creation_source": "purchase_order_confirmation_with_harvest_batch"
                    }
                )
                
                po_batch = batch_service.create_batch(
                    batch_data=po_batch_data,
                    company_id=po.seller_company_id,
                    user_id=current_user.id
                )
                
                # Create SALE relationship between harvest batch and PO batch
                from app.schemas.batch import BatchRelationshipCreate, RelationshipType
                from app.models.batch import BatchRelationship
                
                relationship_data = BatchRelationshipCreate(
                    parent_batch_id=harvest_batch.id,  # The harvest batch (seller's inventory)
                    child_batch_id=po_batch.id,       # The PO batch (buyer's new batch)
                    relationship_type=RelationshipType.SALE,
                    quantity_contribution=confirmation.confirmed_quantity,
                    percentage_contribution=Decimal('100.0'),  # 100% of PO batch comes from this harvest batch
                    transformation_process="Commercial Sale",
                    transformation_date=datetime.utcnow(),
                    yield_percentage=Decimal('100.0'),
                    quality_impact=None
                )
                
                # Create the relationship using the batch service
                relationship = batch_service.create_batch_relationship(
                    relationship_data=relationship_data,
                    company_id=po.seller_company_id,
                    user_id=current_user.id
                )
                
                logger.info(
                    "PO batch created with SALE relationship to harvest batch",
                    po_id=str(po.id),
                    po_batch_id=str(po_batch.id),
                    harvest_batch_id=str(harvest_batch.id),
                    harvest_batch_number=harvest_batch.batch_id,
                    relationship_id=str(relationship.id),
                    relationship_type="SALE"
                )
        
        elif confirmation.origin_data:
            # LEGACY FLOW: Create batch with origin data (deprecated)
            logger.warning(
                "Using legacy origin data flow - consider migrating to harvest batch selection",
                po_id=str(po.id),
                po_number=po.po_number
            )
            
            # Create batch with origin data (existing logic)
            batch = batch_service.create_batch_from_purchase_order(
                purchase_order_id=po.id,
                po_number=po.po_number,
                seller_company_id=po.seller_company_id,
                product_id=po.product_id,
                confirmed_quantity=confirmation.confirmed_quantity,
                user_id=current_user.id
            )
            
            # Update batch with origin data
            if confirmation.origin_data:
                batch.origin_data = confirmation.origin_data
                db.commit()
                db.refresh(batch)
        
        else:
            # DEFAULT FLOW: Create batch without origin data
            logger.info(
                "Creating PO batch without origin data",
                po_id=str(po.id),
                po_number=po.po_number
            )
            
            batch = batch_service.create_batch_from_purchase_order(
                purchase_order_id=po.id,
                po_number=po.po_number,
                seller_company_id=po.seller_company_id,
                product_id=po.product_id,
                confirmed_quantity=confirmation.confirmed_quantity,
                user_id=current_user.id
            )

        # 4. LOG BATCH CREATION IN AUDIT TRAIL
        # history_service.log_batch_created(
        #     purchase_order_id=po.id,
        #     user_id=current_user.id,
        #     company_id=current_user.company_id,
        #     po_number=po.po_number,
        #     batch_id=batch.batch_id
        # )

        logger.info(
            "PO confirmed and batch automatically created",
            po_id=str(po.id),
            po_number=po.po_number,
            batch_id=str(batch.id),
            batch_number=batch.batch_id,
            confirmed_quantity=str(confirmation.confirmed_quantity),
            seller_company_id=str(po.seller_company_id)
        )

    except Exception as e:
        logger.error(
            "Failed to create batch for confirmed PO - PO confirmation will proceed",
            po_id=str(po.id),
            po_number=po.po_number,
            error=str(e)
        )
        # IMPORTANT: Don't fail PO confirmation if batch creation fails
        # The PO confirmation is the source of truth, batch creation is a convenience
