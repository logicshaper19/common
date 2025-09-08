"""
Amendment API endpoints.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from math import ceil

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.services.amendments.service import AmendmentService
from app.schemas.amendment import (
    AmendmentCreate,
    AmendmentUpdate,
    AmendmentResponse,
    AmendmentListResponse,
    AmendmentFilter,
    AmendmentApproval,
    ReceivedQuantityAdjustment,
    ProposeChangesRequest
)
from app.services.amendments.exceptions import (
    AmendmentError,
    AmendmentNotFoundError,
    AmendmentValidationError,
    AmendmentPermissionError,
    AmendmentStatusError,
    get_http_status_for_amendment_exception
)
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/amendments", tags=["amendments"])


@router.post("/", response_model=AmendmentResponse)
def create_amendment(
    amendment: AmendmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new amendment.
    
    Creates an amendment request for a purchase order. The amendment will be
    sent to the counterparty for approval.
    """
    try:
        amendment_service = AmendmentService(db)
        
        created_amendment = amendment_service.create_amendment(
            amendment, 
            current_user.company_id
        )
        
        logger.info(
            "Amendment created via API",
            amendment_id=str(created_amendment.id),
            user_id=str(current_user.id),
            company_id=str(current_user.company_id)
        )
        
        return created_amendment
        
    except (AmendmentValidationError, AmendmentPermissionError, AmendmentStatusError) as e:
        status_code = get_http_status_for_amendment_exception(e)
        raise HTTPException(status_code=status_code, detail=str(e))
    except AmendmentError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/", response_model=AmendmentListResponse)
def list_amendments(
    purchase_order_id: str = Query(None, description="Filter by purchase order ID"),
    amendment_type: str = Query(None, description="Filter by amendment type"),
    status_filter: str = Query(None, alias="status", description="Filter by status"),
    priority: str = Query(None, description="Filter by priority"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List amendments with filtering and pagination.
    
    Returns amendments that the current user's company is involved in
    (either as proposer or approver).
    """
    try:
        amendment_service = AmendmentService(db)
        
        # Build filter
        filters = AmendmentFilter(
            purchase_order_id=purchase_order_id,
            amendment_type=amendment_type,
            status=status_filter,
            priority=priority,
            page=page,
            per_page=per_page
        )
        
        amendments, total = amendment_service.list_amendments(
            filters,
            current_user.company_id
        )
        
        # Convert to summary responses
        amendment_summaries = []
        for amendment in amendments:
            summary = {
                'id': amendment.id,
                'amendment_number': amendment.amendment_number,
                'amendment_type': amendment.amendment_type,
                'status': amendment.status,
                'priority': amendment.priority,
                'proposed_by_company_id': amendment.proposed_by_company_id,
                'proposed_at': amendment.proposed_at,
                'expires_at': amendment.expires_at,
                'change_count': len(amendment.changes) if amendment.changes else 0,
                'primary_change_description': amendment.get_primary_change_description(),
                'impact_level': None,
                'financial_impact': None
            }
            
            # Add impact assessment if available
            if amendment.impact_assessment:
                if isinstance(amendment.impact_assessment, dict):
                    summary['impact_level'] = amendment.impact_assessment.get('impact_level')
                    summary['financial_impact'] = amendment.impact_assessment.get('financial_impact')
            
            amendment_summaries.append(summary)
        
        total_pages = ceil(total / per_page)
        
        return AmendmentListResponse(
            amendments=amendment_summaries,
            total=total,
            page=page,
            per_page=per_page,
            total_pages=total_pages
        )
        
    except AmendmentError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/{amendment_id}", response_model=AmendmentResponse)
def get_amendment(
    amendment_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get amendment by ID.
    
    Returns detailed information about a specific amendment.
    """
    try:
        amendment_service = AmendmentService(db)
        
        amendment = amendment_service.get_amendment_by_id(amendment_id)
        if not amendment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Amendment {amendment_id} not found"
            )
        
        # Check access permissions
        if current_user.company_id not in [
            amendment.proposed_by_company_id,
            amendment.requires_approval_from_company_id
        ]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        return amendment
        
    except HTTPException:
        raise
    except AmendmentError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.put("/{amendment_id}", response_model=AmendmentResponse)
def update_amendment(
    amendment_id: str,
    amendment_update: AmendmentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update an amendment.
    
    Only the proposing company can update pending amendments.
    """
    try:
        amendment_service = AmendmentService(db)
        
        updated_amendment = amendment_service.update_amendment(
            amendment_id,
            amendment_update,
            current_user.company_id
        )
        
        logger.info(
            "Amendment updated via API",
            amendment_id=amendment_id,
            user_id=str(current_user.id),
            company_id=str(current_user.company_id)
        )
        
        return updated_amendment
        
    except AmendmentNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Amendment {amendment_id} not found"
        )
    except (AmendmentPermissionError, AmendmentStatusError) as e:
        status_code = get_http_status_for_amendment_exception(e)
        raise HTTPException(status_code=status_code, detail=str(e))
    except AmendmentError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/{amendment_id}/approve", response_model=AmendmentResponse)
def approve_amendment(
    amendment_id: str,
    approval: AmendmentApproval,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Approve or reject an amendment.
    
    Only the company that needs to approve the amendment can use this endpoint.
    If approved, the amendment will be automatically applied to the purchase order.
    """
    try:
        amendment_service = AmendmentService(db)
        
        approved_amendment = amendment_service.approve_amendment(
            amendment_id,
            approval,
            current_user.company_id
        )
        
        logger.info(
            "Amendment approval processed via API",
            amendment_id=amendment_id,
            approved=approval.approved,
            user_id=str(current_user.id),
            company_id=str(current_user.company_id)
        )
        
        return approved_amendment
        
    except AmendmentNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Amendment {amendment_id} not found"
        )
    except (AmendmentPermissionError, AmendmentStatusError) as e:
        status_code = get_http_status_for_amendment_exception(e)
        raise HTTPException(status_code=status_code, detail=str(e))
    except AmendmentError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# Phase 1 specific endpoints for quick operations

@router.post("/purchase-orders/{purchase_order_id}/adjust-received-quantity", response_model=AmendmentResponse)
def adjust_received_quantity(
    purchase_order_id: str,
    adjustment: ReceivedQuantityAdjustment,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Adjust received quantity for a purchase order (Phase 1 post-confirmation).
    
    This is a quick operation for buyers to adjust the actual quantity received
    when it differs from the ordered quantity. The amendment is auto-approved
    and immediately applied.
    """
    try:
        amendment_service = AmendmentService(db)
        
        amendment = amendment_service.adjust_received_quantity(
            purchase_order_id,
            adjustment,
            current_user.company_id
        )
        
        logger.info(
            "Received quantity adjusted via API",
            po_id=purchase_order_id,
            amendment_id=str(amendment.id),
            user_id=str(current_user.id),
            company_id=str(current_user.company_id)
        )
        
        return amendment
        
    except (AmendmentValidationError, AmendmentPermissionError, AmendmentStatusError) as e:
        status_code = get_http_status_for_amendment_exception(e)
        raise HTTPException(status_code=status_code, detail=str(e))
    except AmendmentError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/purchase-orders/{purchase_order_id}/propose-changes", response_model=AmendmentResponse)
def propose_changes(
    purchase_order_id: str,
    changes: ProposeChangesRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Propose changes to a purchase order (Phase 1 pre-confirmation).

    This endpoint allows proposing multiple changes to a purchase order
    before it's confirmed. The changes will be sent to the counterparty
    for approval.
    """
    try:
        amendment_service = AmendmentService(db)

        amendment = amendment_service.propose_changes(
            purchase_order_id,
            changes,
            current_user.company_id
        )

        logger.info(
            "Changes proposed via API",
            po_id=purchase_order_id,
            amendment_id=str(amendment.id),
            user_id=str(current_user.id),
            company_id=str(current_user.company_id)
        )

        return amendment

    except (AmendmentValidationError, AmendmentPermissionError, AmendmentStatusError) as e:
        status_code = get_http_status_for_amendment_exception(e)
        raise HTTPException(status_code=status_code, detail=str(e))
    except AmendmentError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
