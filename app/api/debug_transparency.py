"""
Debug transparency calculation endpoint.

ONLY FOR DEBUGGING: If the deterministic system shows a PO is not traced,
an admin can run the old complex engine to see if it can find a link
that the user-driven system might have missed. This is for investigation,
not for production scoring.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
from typing import Optional, Dict, Any

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/debug/transparency", tags=["debug-transparency"])


@router.get("/debug-discrepancy/{po_id}")
def debug_transparency_discrepancy(
    po_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    ONLY FOR DEBUGGING: If the deterministic system shows a PO is not traced,
    an admin can run the old complex engine to see if it can find a link
    that the user-driven system might have missed. This is for investigation,
    not for production scoring.
    
    Requires admin or super_admin role.
    """
    # Only allow admins to use debug endpoints
    if current_user.role not in ["admin", "super_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Debug endpoints require admin privileges"
        )
    
    try:
        # Import the complex engine only for debugging
        from app.services.transparency_engine.service import TransparencyCalculationEngine
        from app.services.transparency_engine.domain.enums import GraphTraversalMode, CycleHandlingStrategy
        
        # Initialize the complex engine for debugging
        transparency_engine = TransparencyCalculationEngine(
            db=db,
            max_depth=10,
            traversal_mode=GraphTraversalMode.DEPTH_FIRST,
            cycle_strategy=CycleHandlingStrategy.DEGRADATION
        )
        
        # Try to calculate using the complex engine
        legacy_result = transparency_engine.calculate_transparency_scores(
            po_id=po_id,
            use_cache=False  # Don't use cache for debugging
        )
        
        logger.info(
            "Legacy engine debug completed",
            po_id=str(po_id),
            ttm_score=legacy_result.final_ttm_score,
            ttp_score=legacy_result.final_ttp_score,
            confidence=legacy_result.confidence_level,
            total_nodes=legacy_result.total_nodes,
            cycles_detected=len(legacy_result.circular_references),
            user_id=str(current_user.id)
        )
        
        return {
            "po_id": str(po_id),
            "debug_timestamp": legacy_result.calculation_timestamp.isoformat(),
            "legacy_ttm_score": legacy_result.final_ttm_score,
            "legacy_ttp_score": legacy_result.final_ttp_score,
            "legacy_confidence": legacy_result.confidence_level,
            "total_nodes_analyzed": legacy_result.total_nodes,
            "circular_references": len(legacy_result.circular_references),
            "paths_found": len(legacy_result.paths),
            "debug_note": "This is for investigation only - not used for production scoring",
            "recommendation": "Compare with deterministic system results to identify discrepancies"
        }
        
    except Exception as e:
        logger.error(
            "Legacy engine debug failed",
            po_id=str(po_id),
            error=str(e),
            user_id=str(current_user.id)
        )
        return {
            "po_id": str(po_id),
            "debug_timestamp": None,
            "error": str(e),
            "debug_note": "Legacy engine failed - this is expected if complex engine is not available",
            "recommendation": "Use deterministic system as single source of truth"
        }


@router.get("/compare-systems/{po_id}")
def compare_transparency_systems(
    po_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Compare deterministic system vs legacy complex engine for a specific PO.
    
    This helps identify discrepancies between the two approaches.
    Requires admin or super_admin role.
    """
    # Only allow admins to use debug endpoints
    if current_user.role not in ["admin", "super_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Debug endpoints require admin privileges"
        )
    
    try:
        # Get deterministic result (primary system)
        from sqlalchemy import text
        
        deterministic_query = text("""
            SELECT
                SUM(CASE WHEN COALESCE(sct.is_traced_to_mill, FALSE) THEN po.quantity ELSE 0 END) / NULLIF(SUM(po.quantity), 0) * 100.0 AS ttm_percentage,
                SUM(CASE WHEN COALESCE(sct.is_traced_to_plantation, FALSE) THEN po.quantity ELSE 0 END) / NULLIF(SUM(po.quantity), 0) * 100.0 AS ttp_percentage
            FROM purchase_orders po
            LEFT JOIN supply_chain_traceability sct ON po.id = sct.po_id
            WHERE po.id = :po_id
            AND po.status = 'CONFIRMED'
        """)
        
        deterministic_result = db.execute(deterministic_query, {"po_id": str(po_id)}).fetchone()
        
        deterministic_ttm = float(deterministic_result.ttm_percentage) if deterministic_result and deterministic_result.ttm_percentage else 0.0
        deterministic_ttp = float(deterministic_result.ttp_percentage) if deterministic_result and deterministic_result.ttp_percentage else 0.0
        
        # Try to get legacy result
        legacy_result = None
        legacy_error = None
        
        try:
            from app.services.transparency_engine.service import TransparencyCalculationEngine
            from app.services.transparency_engine.domain.enums import GraphTraversalMode, CycleHandlingStrategy
            
            transparency_engine = TransparencyCalculationEngine(
                db=db,
                max_depth=10,
                traversal_mode=GraphTraversalMode.DEPTH_FIRST,
                cycle_strategy=CycleHandlingStrategy.DEGRADATION
            )
            
            legacy_result = transparency_engine.calculate_transparency_scores(
                po_id=po_id,
                use_cache=False
            )
        except Exception as e:
            legacy_error = str(e)
        
        # Calculate differences
        if legacy_result:
            ttm_difference = abs(deterministic_ttm - (legacy_result.final_ttm_score * 100))
            ttp_difference = abs(deterministic_ttp - (legacy_result.final_ttp_score * 100))
        else:
            ttm_difference = None
            ttp_difference = None
        
        return {
            "po_id": str(po_id),
            "deterministic_system": {
                "ttm_percentage": deterministic_ttm,
                "ttp_percentage": deterministic_ttp,
                "confidence": 1.0,  # Always 100% for deterministic
                "note": "Primary system - single source of truth"
            },
            "legacy_system": {
                "ttm_score": legacy_result.final_ttm_score if legacy_result else None,
                "ttp_score": legacy_result.final_ttp_score if legacy_result else None,
                "confidence": legacy_result.confidence_level if legacy_result else None,
                "error": legacy_error,
                "note": "Debug only - not used for production"
            },
            "differences": {
                "ttm_difference_percentage": ttm_difference,
                "ttp_difference_percentage": ttp_difference,
                "significant_difference": ttm_difference > 10 or ttp_difference > 10 if ttm_difference and ttp_difference else False
            },
            "recommendation": "Use deterministic system results for production scoring"
        }
        
    except Exception as e:
        logger.error(
            "Failed to compare transparency systems",
            po_id=str(po_id),
            error=str(e),
            user_id=str(current_user.id)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to compare systems: {str(e)}"
        )
