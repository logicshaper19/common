"""
Traceability and transparency calculation API endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from uuid import UUID
from typing import Optional

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.services.traceability import TraceabilityCalculationService
from app.services.purchase_order import PurchaseOrderService
from app.services.transparency_engine import TransparencyCalculationEngine
from app.schemas.traceability import (
    TransparencyScoreRequest,
    TraceabilityMetricsResponse,
    BulkTransparencyUpdateRequest,
    BulkTransparencyUpdateResponse,
    TransparencyAnalyticsRequest,
    TransparencyAnalyticsResponse,
    EnhancedTraceabilityResponse,
    TransparencyTrendsResponse,
    TransparencyBenchmarkRequest,
    TransparencyBenchmarkResponse,
    TransparencyImprovementResponse,
    TransparencyAuditRequest,
    TransparencyAuditResponse,
    EnhancedTransparencyResult,
    TransparencyCalculationRequest,
    TransparencyImprovementSuggestion,
    CircularReferenceAnalysis
)
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/traceability", tags=["traceability"])


@router.post("/calculate-transparency", response_model=TraceabilityMetricsResponse)
def calculate_transparency_scores(
    request: TransparencyScoreRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Calculate transparency scores (TTM and TTP) for a purchase order.
    
    Analyzes the complete supply chain to calculate:
    - Transparency to Mill (TTM): How well we can trace to processing facilities
    - Transparency to Plantation (TTP): How well we can trace to original sources
    
    Requires access to the purchase order (buyer or seller).
    """
    traceability_service = TraceabilityCalculationService(db)
    po_service = PurchaseOrderService(db)
    
    # Check access permissions
    po = po_service.get_purchase_order_with_details(str(request.purchase_order_id))
    if not po:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Purchase order not found"
        )
    
    if (current_user.company_id != po.buyer_company["id"] and 
        current_user.company_id != po.seller_company["id"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only calculate transparency for your own purchase orders"
        )
    
    try:
        # Calculate or retrieve transparency scores
        if request.force_recalculation:
            metrics = traceability_service.update_transparency_scores(request.purchase_order_id)
        else:
            # Check if recent scores exist
            if (po.transparency_to_mill is not None and 
                po.transparency_to_plantation is not None and
                po.transparency_calculated_at is not None):
                # Use existing scores if they're recent (less than 1 hour old)
                from datetime import datetime, timedelta
                if datetime.utcnow() - po.transparency_calculated_at < timedelta(hours=1):
                    metrics = traceability_service.calculate_transparency_scores(request.purchase_order_id)
                else:
                    metrics = traceability_service.update_transparency_scores(request.purchase_order_id)
            else:
                metrics = traceability_service.update_transparency_scores(request.purchase_order_id)
        
        # Create score interpretation
        score_interpretation = {
            "ttm_grade": _get_transparency_grade(metrics.transparency_to_mill),
            "ttp_grade": _get_transparency_grade(metrics.transparency_to_plantation),
            "ttm_description": _get_score_description(metrics.transparency_to_mill, "mill"),
            "ttp_description": _get_score_description(metrics.transparency_to_plantation, "plantation")
        }
        
        response = TraceabilityMetricsResponse(
            purchase_order_id=request.purchase_order_id,
            total_nodes=metrics.total_nodes,
            max_depth_reached=metrics.max_depth_reached,
            mill_nodes=metrics.mill_nodes,
            plantation_nodes=metrics.plantation_nodes,
            origin_data_nodes=metrics.origin_data_nodes,
            certified_nodes=metrics.certified_nodes,
            geographic_data_nodes=metrics.geographic_data_nodes,
            input_material_links=metrics.input_material_links,
            transparency_to_mill=metrics.transparency_to_mill,
            transparency_to_plantation=metrics.transparency_to_plantation,
            calculation_timestamp=metrics.calculation_timestamp,
            score_interpretation=score_interpretation
        )
        
        logger.info(
            "Transparency scores calculated",
            po_id=str(request.purchase_order_id),
            ttm_score=metrics.transparency_to_mill,
            ttp_score=metrics.transparency_to_plantation,
            user_id=str(current_user.id)
        )
        
        return response
        
    except Exception as e:
        logger.error(
            "Failed to calculate transparency scores",
            po_id=str(request.purchase_order_id),
            error=str(e),
            user_id=str(current_user.id)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to calculate transparency scores"
        )


@router.post("/bulk-update", response_model=BulkTransparencyUpdateResponse)
def bulk_update_transparency_scores(
    request: BulkTransparencyUpdateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Bulk update transparency scores for multiple purchase orders.
    
    Updates scores for purchase orders that:
    - Belong to the specified company (or current user's company if not specified)
    - Have scores older than the specified age threshold
    - Are in confirmed, in_transit, or delivered status
    
    This operation runs in the background for large datasets.
    """
    traceability_service = TraceabilityCalculationService(db)
    
    # Use current user's company if not specified
    company_id = request.company_id or current_user.company_id
    
    # Check if user has permission to update scores for the specified company
    if company_id != current_user.company_id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update transparency scores for your own company"
        )
    
    try:
        # Perform bulk update
        # When force_update is True, use a very large max_age to update all scores
        max_age = 8760 if request.force_update else request.max_age_hours  # 8760 hours = 1 year
        update_result = traceability_service.bulk_update_transparency_scores(
            company_id=company_id,
            max_age_hours=max_age
        )
        
        # Convert to response format
        results = []
        for result in update_result["results"]:
            results.append(BulkUpdateResult(
                po_id=result["po_id"],
                po_number=result["po_number"],
                ttm_score=result.get("ttm_score"),
                ttp_score=result.get("ttp_score"),
                status=result["status"],
                error=result.get("error")
            ))
        
        response = BulkTransparencyUpdateResponse(
            total_processed=update_result["total_processed"],
            updated_count=update_result["updated_count"],
            error_count=update_result["error_count"],
            results=results,
            timestamp=update_result["timestamp"],
            summary={
                "company_id": str(company_id),
                "max_age_hours": request.max_age_hours,
                "force_update": request.force_update,
                "success_rate": update_result["updated_count"] / max(update_result["total_processed"], 1)
            }
        )
        
        logger.info(
            "Bulk transparency update completed",
            company_id=str(company_id),
            total_processed=update_result["total_processed"],
            updated_count=update_result["updated_count"],
            user_id=str(current_user.id)
        )
        
        return response
        
    except Exception as e:
        logger.error(
            "Failed to perform bulk transparency update",
            company_id=str(company_id),
            error=str(e),
            user_id=str(current_user.id)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to perform bulk transparency update"
        )


@router.get("/analytics", response_model=TransparencyAnalyticsResponse)
def get_transparency_analytics(
    company_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get transparency analytics for a company.
    
    Provides insights into:
    - Average transparency scores
    - Score distribution
    - Improvement opportunities
    - Trends over time
    
    If no company_id is provided, uses current user's company.
    """
    traceability_service = TraceabilityCalculationService(db)
    
    # Use current user's company if not specified
    target_company_id = UUID(company_id) if company_id else current_user.company_id
    
    # Check permissions
    if target_company_id != current_user.company_id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view analytics for your own company"
        )
    
    try:
        analytics_data = traceability_service.get_transparency_analytics(target_company_id)
        
        response = TransparencyAnalyticsResponse(
            company_id=target_company_id,
            total_purchase_orders=analytics_data["total_purchase_orders"],
            average_ttm_score=analytics_data["average_ttm_score"],
            average_ttp_score=analytics_data["average_ttp_score"],
            transparency_distribution=analytics_data["transparency_distribution"],
            improvement_opportunities=analytics_data["improvement_opportunities"],
            last_updated=analytics_data["last_updated"]
        )
        
        logger.info(
            "Transparency analytics retrieved",
            company_id=str(target_company_id),
            total_pos=analytics_data["total_purchase_orders"],
            avg_ttp=analytics_data["average_ttp_score"],
            user_id=str(current_user.id)
        )
        
        return response
        
    except Exception as e:
        logger.error(
            "Failed to retrieve transparency analytics",
            company_id=str(target_company_id),
            error=str(e),
            user_id=str(current_user.id)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve transparency analytics"
        )


@router.post("/enhanced-transparency", response_model=EnhancedTransparencyResult)
def calculate_enhanced_transparency(
    request: TransparencyCalculationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Calculate enhanced transparency scores using the advanced calculation engine.

    This endpoint uses the enhanced transparency calculation engine that provides:
    - Recursive graph traversal with cycle detection
    - Degradation factor application for transformation steps
    - Confidence level calculation based on data completeness
    - Detailed path analysis and improvement suggestions
    - Circular reference detection and handling

    Returns comprehensive transparency analysis with detailed breakdown.
    """
    transparency_engine = TransparencyCalculationEngine(db)
    po_service = PurchaseOrderService(db)

    # Check access permissions
    po = po_service.get_purchase_order_with_details(str(request.purchase_order_id))
    if not po:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Purchase order not found"
        )

    if (current_user.company_id != po.buyer_company["id"] and
        current_user.company_id != po.seller_company["id"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only calculate transparency for your own purchase orders"
        )

    try:
        # Calculate enhanced transparency scores
        result = transparency_engine.calculate_transparency(
            po_id=request.purchase_order_id,
            force_recalculation=request.force_recalculation,
            include_detailed_analysis=request.include_detailed_analysis
        )

        logger.info(
            "Enhanced transparency calculation completed",
            po_id=str(request.purchase_order_id),
            ttm_score=result.ttm_score,
            ttp_score=result.ttp_score,
            confidence=result.confidence_level,
            total_nodes=result.total_nodes,
            cycles_detected=len(result.circular_references),
            user_id=str(current_user.id)
        )

        return result

    except Exception as e:
        logger.error(
            "Failed to calculate enhanced transparency scores",
            po_id=str(request.purchase_order_id),
            error=str(e),
            user_id=str(current_user.id)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to calculate enhanced transparency scores"
        )


@router.get("/circular-references/{po_id}", response_model=CircularReferenceAnalysis)
def analyze_circular_references(
    po_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Analyze circular references in the supply chain graph.

    Detects and analyzes circular references that may affect transparency calculations.
    Provides suggestions for resolving data integrity issues.
    """
    transparency_engine = TransparencyCalculationEngine(db)
    po_service = PurchaseOrderService(db)

    # Check access permissions
    po = po_service.get_purchase_order_with_details(str(po_id))
    if not po:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Purchase order not found"
        )

    if (current_user.company_id != po.buyer_company["id"] and
        current_user.company_id != po.seller_company["id"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only analyze circular references for your own purchase orders"
        )

    try:
        # Detect circular references
        circular_refs = transparency_engine.detect_circular_references(po_id)

        # Calculate impact on transparency
        result = transparency_engine.calculate_transparency(po_id, include_detailed_analysis=False)
        affected_score = 1.0 - result.ttm_score if circular_refs else 0.0

        # Generate resolution suggestions
        suggestions = []
        if circular_refs:
            suggestions.extend([
                "Review input material linkages for logical inconsistencies",
                "Verify purchase order dates to identify chronological issues",
                "Check for duplicate or incorrectly linked purchase orders",
                "Consider breaking cycles at the oldest purchase order in the chain"
            ])

        analysis = CircularReferenceAnalysis(
            detected_cycles=[circular_refs] if circular_refs else [],
            cycle_break_points=circular_refs[:1] if circular_refs else [],  # Suggest breaking at first detected
            affected_transparency_score=affected_score,
            resolution_suggestions=suggestions
        )

        logger.info(
            "Circular reference analysis completed",
            po_id=str(po_id),
            cycles_detected=len(circular_refs),
            affected_score=affected_score,
            user_id=str(current_user.id)
        )

        return analysis

    except Exception as e:
        logger.error(
            "Failed to analyze circular references",
            po_id=str(po_id),
            error=str(e),
            user_id=str(current_user.id)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to analyze circular references"
        )


@router.get("/improvement-suggestions/{po_id}")
def get_transparency_improvement_suggestions(
    po_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> List[TransparencyImprovementSuggestion]:
    """
    Get transparency improvement suggestions for a purchase order.

    Analyzes the current transparency state and provides actionable suggestions
    for improving transparency scores and data quality.
    """
    transparency_engine = TransparencyCalculationEngine(db)
    po_service = PurchaseOrderService(db)

    # Check access permissions
    po = po_service.get_purchase_order_with_details(str(po_id))
    if not po:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Purchase order not found"
        )

    if (current_user.company_id != po.buyer_company["id"] and
        current_user.company_id != po.seller_company["id"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only get improvement suggestions for your own purchase orders"
        )

    try:
        # Calculate transparency and get suggestions
        result = transparency_engine.calculate_transparency(po_id, include_detailed_analysis=False)
        suggestions = transparency_engine.get_transparency_improvement_suggestions(result)

        # Convert to response format
        response_suggestions = [
            TransparencyImprovementSuggestion(
                category=s["category"],
                priority=s["priority"],
                description=s["description"],
                expected_impact=s["expected_impact"],
                implementation_effort=s["implementation_effort"]
            )
            for s in suggestions
        ]

        logger.info(
            "Transparency improvement suggestions generated",
            po_id=str(po_id),
            suggestions_count=len(suggestions),
            user_id=str(current_user.id)
        )

        return response_suggestions

    except Exception as e:
        logger.error(
            "Failed to generate improvement suggestions",
            po_id=str(po_id),
            error=str(e),
            user_id=str(current_user.id)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate improvement suggestions"
        )


def _get_transparency_grade(score: float) -> str:
    """Convert transparency score to letter grade."""
    if score >= 0.9:
        return "A"
    elif score >= 0.8:
        return "B"
    elif score >= 0.7:
        return "C"
    elif score >= 0.6:
        return "D"
    else:
        return "F"


def _get_score_description(score: float, level: str) -> str:
    """Get human-readable description of transparency score."""
    if score >= 0.9:
        return f"Excellent transparency to {level} - comprehensive traceability data available"
    elif score >= 0.8:
        return f"Good transparency to {level} - most traceability data available"
    elif score >= 0.7:
        return f"Fair transparency to {level} - some traceability data available"
    elif score >= 0.6:
        return f"Limited transparency to {level} - minimal traceability data available"
    else:
        return f"Poor transparency to {level} - insufficient traceability data"
