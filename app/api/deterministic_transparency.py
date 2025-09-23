"""
Deterministic Transparency API Endpoints

Fast, auditable transparency metrics based on explicit user-created links.
Replaces complex scoring algorithms with binary traced/not-traced states.
"""

from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.services.deterministic_transparency import (
    DeterministicTransparencyService,
    TransparencyMetrics,
    TransparencyGap,
    SupplyChainTrace
)
from app.services.gap_action_service import GapActionService
from app.schemas.gap_action import (
    GapActionRequest,
    GapActionUpdate,
    GapActionResponse,
    GapActionListResponse,
    GapActionCreateResponse
)
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/transparency/v2", tags=["deterministic-transparency"])


class TransparencyResponse(BaseModel):
    """Response model for company transparency metrics."""
    success: bool
    data: TransparencyMetrics
    message: str = "Transparency metrics calculated successfully"
    calculation_method: str = "deterministic_materialized_view"


class TransparencyGapsResponse(BaseModel):
    """Response model for transparency gaps analysis."""
    success: bool
    data: List[TransparencyGap]
    total_gaps: int
    message: str = "Transparency gaps identified successfully"


class SupplyChainTraceResponse(BaseModel):
    """Response model for supply chain trace."""
    success: bool
    data: Optional[SupplyChainTrace]
    message: str


class RefreshRequest(BaseModel):
    """Request model for refreshing transparency data."""
    force_refresh: bool = Field(default=True, description="Force refresh of materialized view")


@router.get("/companies/{company_id}/metrics", response_model=TransparencyResponse)
def get_company_transparency_metrics(
    company_id: UUID,
    refresh: bool = Query(default=False, description="Refresh materialized view before calculation"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get deterministic transparency metrics for a company.
    
    Returns binary traced/not-traced percentages based on explicit data relationships:
    - Transparency to Mill: % of volume traced to mills or processing facilities
    - Transparency to Plantation: % of volume traced to plantation growers
    
    **Key Benefits:**
    - Sub-second response times using materialized views
    - 100% auditable - every calculation traceable through explicit data
    - No algorithmic "guessing" - only verifiable user-created relationships
    
    **Calculation Method:**
    ```
    transparency_percentage = (traced_volume / total_volume) * 100
    ```
    
    Where traced_volume is determined by following explicit batch relationships
    from confirmed purchase orders to companies of specific types.
    """
    try:
        # Check access permissions
        if (current_user.company_id != company_id and 
            current_user.role not in ["admin", "super_admin"]):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to company transparency data"
            )
        
        # Calculate deterministic metrics
        service = DeterministicTransparencyService(db)
        metrics = service.get_company_transparency_metrics(
            company_id=company_id,
            refresh_data=refresh
        )
        
        logger.info(
            f"Deterministic transparency calculated for company {company_id}: "
            f"Mill={metrics.transparency_to_mill_percentage:.1f}%, "
            f"Plantation={metrics.transparency_to_plantation_percentage:.1f}%"
        )
        
        return TransparencyResponse(
            success=True,
            data=metrics
        )
        
    except Exception as e:
        logger.error(f"Error calculating transparency metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to calculate transparency metrics: {str(e)}"
        )


@router.get("/companies/{company_id}/gaps", response_model=TransparencyGapsResponse)
def get_transparency_gaps(
    company_id: UUID,
    gap_type: Optional[str] = Query(
        default=None, 
        description="Filter by gap type: 'mill', 'plantation', or None for all gaps"
    ),
    limit: int = Query(default=50, ge=1, le=200, description="Maximum number of gaps to return"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get transparency gaps requiring attention.
    
    Identifies specific purchase orders that cannot be traced to mills or plantations,
    providing actionable information for supply chain teams.
    
    **Gap Types:**
    - `mill`: Purchase orders not traced to mills or processing facilities
    - `plantation`: Purchase orders not traced to plantation growers
    - `None`: All transparency gaps
    
    **Response includes:**
    - Specific PO details (number, quantity, supplier)
    - Gap type and severity
    - Last known company type in the trace
    - Trace depth achieved
    
    This enables targeted outreach to suppliers for missing traceability data.
    """
    try:
        # Check access permissions
        if (current_user.company_id != company_id and 
            current_user.role not in ["admin", "super_admin"]):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to company transparency data"
            )
        
        # Validate gap_type parameter
        if gap_type and gap_type not in ["mill", "plantation"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="gap_type must be 'mill', 'plantation', or None"
            )
        
        # Get transparency gaps
        service = DeterministicTransparencyService(db)
        gaps = service.get_transparency_gaps(
            company_id=company_id,
            gap_type=gap_type,
            limit=limit
        )
        
        logger.info(
            f"Found {len(gaps)} transparency gaps for company {company_id} "
            f"(type: {gap_type or 'all'})"
        )
        
        return TransparencyGapsResponse(
            success=True,
            data=gaps,
            total_gaps=len(gaps)
        )
        
    except Exception as e:
        logger.error(f"Error getting transparency gaps: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get transparency gaps: {str(e)}"
        )


@router.get("/purchase-orders/{po_id}/trace", response_model=SupplyChainTraceResponse)
def get_supply_chain_trace(
    po_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get complete supply chain trace for a purchase order.
    
    Shows the full path from the purchase order through all batch relationships
    to the deepest traceable origin, with deterministic transparency status.
    
    **Trace Information:**
    - Complete trace path with company names
    - Trace depth achieved
    - Origin company type (mill, plantation, etc.)
    - Binary transparency flags (traced to mill/plantation)
    - All companies in the trace path
    
    **Audit Trail:**
    Every step in the trace is based on explicit user-created batch relationships,
    making the entire calculation fully auditable and verifiable.
    """
    try:
        # Get supply chain trace
        service = DeterministicTransparencyService(db)
        trace = service.get_supply_chain_trace(po_id)
        
        if not trace:
            return SupplyChainTraceResponse(
                success=False,
                data=None,
                message="No supply chain trace found for this purchase order"
            )
        
        # Check access permissions (user must have access to the PO's buyer company)
        from app.models.purchase_order import PurchaseOrder
        po = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
        
        if not po:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Purchase order not found"
            )
        
        # Use universal access control for traceability
        from app.services.universal_access_control import UniversalAccessControl, AccessLevel
        
        access_control = UniversalAccessControl(db)
        decision = access_control.can_access_traceability(current_user, po, AccessLevel.READ)
        
        if not decision.allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied: {decision.reason}"
            )
        
        # Log the access attempt for audit trail
        access_control.log_access_attempt(current_user, "traceability", po_id, decision)
        
        logger.info(
            f"Supply chain trace retrieved for PO {po_id}: "
            f"depth={trace.trace_depth}, mill={trace.is_traced_to_mill}, "
            f"plantation={trace.is_traced_to_plantation}"
        )
        
        return SupplyChainTraceResponse(
            success=True,
            data=trace,
            message="Supply chain trace retrieved successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting supply chain trace: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get supply chain trace: {str(e)}"
        )


@router.post("/refresh")
def refresh_transparency_data(
    request: RefreshRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Refresh transparency materialized view.
    
    Triggers a refresh of the supply chain traceability materialized view
    to ensure all transparency calculations reflect the latest data.
    
    **When to use:**
    - After bulk data imports
    - After significant batch relationship changes
    - When real-time accuracy is critical
    
    **Note:** The materialized view is automatically refreshed when key data changes,
    so manual refresh is typically not needed for normal operations.
    """
    try:
        # Only admins can trigger manual refresh
        if current_user.role not in ["admin", "super_admin"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only administrators can refresh transparency data"
            )
        
        if request.force_refresh:
            service = DeterministicTransparencyService(db)
            service._refresh_materialized_view()
            
            logger.info(f"Transparency data refreshed by user {current_user.id}")
            
            return {
                "success": True,
                "message": "Transparency data refreshed successfully",
                "refreshed_at": service.db.execute(
                    "SELECT CURRENT_TIMESTAMP"
                ).scalar().isoformat()
            }
        else:
            return {
                "success": True,
                "message": "Refresh skipped (force_refresh=False)"
            }
        
    except Exception as e:
        logger.error(f"Error refreshing transparency data: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to refresh transparency data: {str(e)}"
        )


@router.get("/purchase-orders/{po_id}/audit", response_model=dict)
def get_transparency_audit_trail(
    po_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get complete audit trail for transparency calculation.
    
    Returns all data used in determining transparency status for a purchase order,
    enabling full auditability and verification of calculations.
    
    **Audit Information:**
    - All batch relationships used in calculation
    - Company types at each step
    - Trace path with timestamps
    - Calculation method and timestamp
    - Data sources for each transparency determination
    
    **Use Cases:**
    - Compliance audits
    - Transparency verification
    - Debugging trace issues
    - Customer transparency reports
    """
    try:
        # Check access permissions
        from app.models.purchase_order import PurchaseOrder
        po = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
        
        if not po:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Purchase order not found"
            )
        
        if (current_user.company_id != po.buyer_company_id and 
            current_user.role not in ["admin", "super_admin"]):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to purchase order audit data"
            )
        
        # Get audit trail
        service = DeterministicTransparencyService(db)
        audit_trail = service.get_transparency_audit_trail(po_id)
        
        logger.info(f"Transparency audit trail retrieved for PO {po_id}")
        
        return {
            "success": True,
            "data": audit_trail,
            "message": "Transparency audit trail retrieved successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting transparency audit trail: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get transparency audit trail: {str(e)}"
        )


# Gap Actions Endpoints

@router.post("/companies/{company_id}/gaps/{gap_id}/actions", response_model=GapActionCreateResponse)
def create_gap_action(
    company_id: UUID,
    gap_id: str,
    action: GapActionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create an action to resolve a transparency gap.

    This endpoint allows users to create actionable items for resolving transparency gaps,
    such as requesting data from suppliers, contacting suppliers directly, or marking
    gaps as resolved through offline processes.

    **Action Types:**
    - `request_data`: Formal request for additional traceability data
    - `contact_supplier`: Direct communication with supplier
    - `mark_resolved`: Mark gap as resolved through other means

    **Permissions:**
    - User must belong to the specified company
    - Only company members can create actions for their gaps
    """
    try:
        # Verify user belongs to the company
        if current_user.company_id != company_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: User does not belong to this company"
            )

        # Create gap action
        gap_action_service = GapActionService(db)
        gap_action = gap_action_service.create_gap_action(
            company_id=company_id,
            gap_id=gap_id,
            action_request=action,
            created_by_user_id=current_user.id
        )

        logger.info(
            f"Gap action created for company {company_id}, gap {gap_id} "
            f"by user {current_user.id}"
        )

        return GapActionCreateResponse(
            success=True,
            action_id=gap_action.id,
            message=f"Gap action '{action.action_type}' created successfully"
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error creating gap action: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create gap action: {str(e)}"
        )


@router.get("/companies/{company_id}/gap-actions", response_model=GapActionListResponse)
def get_gap_actions(
    company_id: UUID,
    status: Optional[str] = Query(None, description="Filter by action status"),
    gap_id: Optional[str] = Query(None, description="Filter by specific gap ID"),
    limit: int = Query(50, ge=1, le=200, description="Maximum number of actions to return"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get gap actions for a company.

    Returns all gap actions created by the company, with optional filtering
    by status or specific gap ID.

    **Status Values:**
    - `pending`: Action created but not yet started
    - `in_progress`: Action is being worked on
    - `resolved`: Action has been completed
    - `cancelled`: Action was cancelled

    **Permissions:**
    - User must belong to the specified company
    - Users can only see actions for their own company
    """
    try:
        # Verify user belongs to the company
        if current_user.company_id != company_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: User does not belong to this company"
            )

        # Get gap actions
        gap_action_service = GapActionService(db)
        actions = gap_action_service.get_gap_actions(
            company_id=company_id,
            status=status,
            gap_id=gap_id,
            limit=limit
        )

        # Convert to response format
        action_responses = [
            gap_action_service.to_response(action) for action in actions
        ]

        logger.info(
            f"Retrieved {len(actions)} gap actions for company {company_id} "
            f"(status: {status or 'all'}, gap_id: {gap_id or 'all'})"
        )

        return GapActionListResponse(
            success=True,
            actions=action_responses,
            total_count=len(action_responses),
            message="Gap actions retrieved successfully"
        )

    except Exception as e:
        logger.error(f"Error getting gap actions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get gap actions: {str(e)}"
        )


@router.put("/companies/{company_id}/gap-actions/{action_id}")
def update_gap_action(
    company_id: UUID,
    action_id: UUID,
    update: GapActionUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update gap action status.

    Allows updating the status and resolution notes of a gap action.
    Typically used to mark actions as in progress, resolved, or cancelled.

    **Status Transitions:**
    - `pending` → `in_progress`, `resolved`, `cancelled`
    - `in_progress` → `resolved`, `cancelled`
    - `resolved` and `cancelled` are final states

    **Permissions:**
    - User must belong to the specified company
    - Users can only update actions for their own company
    """
    try:
        # Verify user belongs to the company
        if current_user.company_id != company_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: User does not belong to this company"
            )

        # Update gap action
        gap_action_service = GapActionService(db)
        updated_action = gap_action_service.update_gap_action(
            action_id=action_id,
            company_id=company_id,
            update_request=update,
            updated_by_user_id=current_user.id
        )

        logger.info(
            f"Gap action {action_id} updated to status '{update.status}' "
            f"by user {current_user.id}"
        )

        return {
            "success": True,
            "message": f"Gap action updated to '{update.status}' successfully",
            "action": gap_action_service.to_response(updated_action)
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error updating gap action: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update gap action: {str(e)}"
        )
