"""Purchase order traceability endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from uuid import UUID
from typing import Dict, Any

from app.core.auth import get_current_user_sync
from app.models.user import User
from app.schemas.purchase_order import (
    TraceabilityRequest,
    TraceabilityResponse,
    DiscrepancyResponse
)
from ..dependencies import get_po_service, validate_po_access
from app.services.purchase_order import PurchaseOrderService
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()

@router.post("/trace", response_model=TraceabilityResponse)
def trace_supply_chain(
    request: TraceabilityRequest,
    po_service: PurchaseOrderService = Depends(get_po_service),
    current_user: User = Depends(get_current_user_sync)
):
    """Trace the supply chain for a purchase order."""
    # First check if user has access to the root purchase order
    root_po = po_service.get_purchase_order_with_details(str(request.purchase_order_id))
    if not root_po:
        raise HTTPException(status_code=404, detail="Purchase order not found")

    # Check access permissions
    if (current_user.company_id != root_po.buyer_company["id"] and
        current_user.company_id != root_po.seller_company["id"]):
        raise HTTPException(
            status_code=403,
            detail="You can only trace purchase orders for your own company"
        )

    traceability_result = po_service.trace_supply_chain(request)

    logger.info(
        "Supply chain traced",
        root_po_id=str(request.purchase_order_id),
        depth=request.depth,
        total_nodes=traceability_result.total_nodes,
        user_id=str(current_user.id),
        company_id=str(current_user.company_id)
    )

    return traceability_result

@router.get("/{po_id}/chain")
def get_po_chain(
    po_id: UUID,
    po_service: PurchaseOrderService = Depends(get_po_service),
    current_user: User = Depends(get_current_user_sync),
    _: None = Depends(validate_po_access)
):
    """Get the complete supply chain for a purchase order."""
    from app.services.po_chaining import POChainingService

    chaining_service = POChainingService(po_service.db)

    try:
        chain_data = chaining_service.get_po_chain(str(po_id))

        # Filter chain data based on user permissions
        # For now, return full chain - in production, filter based on user role
        return {
            "success": True,
            "chain": chain_data
        }

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(
            "Failed to get PO chain",
            po_id=str(po_id),
            error=str(e)
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get supply chain: {str(e)}"
        )

@router.get("/{po_id}/discrepancies", response_model=DiscrepancyResponse)
def get_purchase_order_discrepancies(
    po_id: UUID,
    po_service: PurchaseOrderService = Depends(get_po_service),
    current_user: User = Depends(get_current_user_sync),
    _: None = Depends(validate_po_access)
):
    """Get discrepancy details for a purchase order awaiting buyer approval."""
    import json
    from app.services.discrepancy_detection import DiscrepancyDetectionService
    from app.schemas.purchase_order import DiscrepancyDetail, PurchaseOrderStatus

    discrepancy_service = DiscrepancyDetectionService()

    # Get the PO
    po = po_service.get_purchase_order_by_id(str(po_id))
    if not po:
        raise HTTPException(status_code=404, detail="Purchase order not found")

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