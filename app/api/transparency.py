"""
API endpoints for transparency metrics and dashboard data.
"""
from typing import List, Optional, Dict, Any
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.models.purchase_order import PurchaseOrder
from app.services.deterministic_transparency import TransparencyGap, DeterministicTransparencyService
from app.core.logging import get_logger
from datetime import datetime, timedelta

logger = get_logger(__name__)

router = APIRouter(prefix="/transparency", tags=["transparency"])


async def get_recent_improvements(company_id: UUID, db: Session) -> List[Dict[str, Any]]:
    """Get recent transparency improvements for a company (last 30 days)."""
    try:
        from app.models.purchase_order import PurchaseOrder
        from app.models.batch import Batch
        from sqlalchemy import and_, or_

        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        improvements = []

        # Recent PO confirmations
        recent_confirmations = db.query(PurchaseOrder).filter(
            and_(
                or_(
                    PurchaseOrder.buyer_company_id == company_id,
                    PurchaseOrder.seller_company_id == company_id
                ),
                PurchaseOrder.seller_confirmed_at >= thirty_days_ago,
                PurchaseOrder.status == 'confirmed'
            )
        ).order_by(PurchaseOrder.seller_confirmed_at.desc()).limit(5).all()

        for po in recent_confirmations:
            improvements.append({
                "type": "po_confirmation",
                "title": f"Purchase Order {po.po_number} Confirmed",
                "description": f"Seller confirmed order for {po.quantity} {po.unit}",
                "date": po.seller_confirmed_at.isoformat() if po.seller_confirmed_at else None,
                "impact": "Improved supply chain visibility",
                "transparency_improvement": "+5%"
            })

        # Recent batch linkages (if batch model exists)
        try:
            recent_batches = db.query(Batch).filter(
                and_(
                    Batch.company_id == company_id,
                    Batch.created_at >= thirty_days_ago,
                    Batch.source_purchase_order_id.isnot(None)
                )
            ).order_by(Batch.created_at.desc()).limit(3).all()

            for batch in recent_batches:
                improvements.append({
                    "type": "batch_linkage",
                    "title": f"Batch {batch.batch_id} Linked to PO",
                    "description": f"Linked {batch.quantity} {batch.unit} batch to purchase order",
                    "date": batch.created_at.isoformat() if batch.created_at else None,
                    "impact": "Enhanced traceability",
                    "transparency_improvement": "+8%"
                })
        except Exception:
            # Batch model might not exist yet
            pass

        # Sort by date and return most recent
        improvements.sort(key=lambda x: x.get('date', ''), reverse=True)
        return improvements[:5]

    except Exception as e:
        logger.error(f"Failed to get recent improvements: {e}")
        return []


# Response Models
class TransparencyMetrics(BaseModel):
    """Company transparency metrics response."""
    ttm_score: float = Field(..., description="Time to Mill transparency score")
    ttp_score: float = Field(..., description="Time to Plantation transparency score")
    overall_score: float = Field(..., description="Overall transparency score")
    confidence_level: float = Field(..., description="Confidence level of the scores")
    traced_percentage: float = Field(..., description="Percentage of supply chain traced")
    untraced_percentage: float = Field(..., description="Percentage of supply chain untraced")
    last_updated: str = Field(..., description="Last update timestamp")


class GapAnalysisItem(BaseModel):
    """Individual gap analysis item."""
    gap_id: str
    category: str
    severity: str
    description: str
    recommendation: str
    impact_score: float
    implementation_effort: str


class MultiClientDashboard(BaseModel):
    """Multi-client dashboard for consultants."""
    consultant_id: str
    clients: List[Dict[str, Any]]
    summary_metrics: Dict[str, Any]
    generated_at: str


class CompanyTransparencySummary(BaseModel):
    """Company transparency summary."""
    company_id: str
    company_name: str
    transparency_metrics: TransparencyMetrics
    recent_improvements: List[Dict[str, Any]]
    key_gaps: List[GapAnalysisItem]


@router.get("/{company_id}", response_model=TransparencyMetrics)
async def get_transparency_metrics(
    company_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> TransparencyMetrics:
    """
    Get transparency metrics for a company.

    SINGLE SOURCE OF TRUTH: Uses deterministic transparency based on explicit user-created links.
    No fallbacks, no algorithmic guessing, 100% auditable.
    """
    try:
        # Check if user has access to this company's data
        if (current_user.company_id != company_id and
            current_user.role not in ["admin", "super_admin"]):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to company transparency data"
            )

        # SINGLE SOURCE OF TRUTH: Deterministic transparency calculation
        deterministic_service = DeterministicTransparencyService(db)
        deterministic_metrics = deterministic_service.get_company_transparency_metrics(
            company_id=company_id,
            refresh_data=False  # Use cached materialized view for performance
        )

        # Simple, auditable percentages - no complex scoring
        mill_percentage = deterministic_metrics.transparency_to_mill_percentage
        plantation_percentage = deterministic_metrics.transparency_to_plantation_percentage
        overall_percentage = (mill_percentage + plantation_percentage) / 2

        logger.info(
            "Deterministic transparency calculated (SINGLE SOURCE OF TRUTH)",
            company_id=str(company_id),
            mill_percentage=mill_percentage,
            plantation_percentage=plantation_percentage,
            overall_percentage=overall_percentage,
            total_volume=float(deterministic_metrics.total_volume),
            traced_pos=deterministic_metrics.traced_purchase_orders,
            total_pos=deterministic_metrics.total_purchase_orders
        )

        return TransparencyMetrics(
            ttm_score=mill_percentage / 100.0,  # Convert percentage to 0-1 scale for compatibility
            ttp_score=plantation_percentage / 100.0,  # Convert percentage to 0-1 scale for compatibility
            overall_score=overall_percentage / 100.0,  # Convert percentage to 0-1 scale for compatibility
            confidence_level=1.0,  # Always 100% confidence - based on explicit user actions
            traced_percentage=overall_percentage,
            untraced_percentage=100.0 - overall_percentage,
            last_updated=deterministic_metrics.calculation_timestamp.isoformat()
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get transparency metrics", company_id=str(company_id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get transparency metrics: {str(e)}"
        )


@router.get("/po/{po_id}")
async def get_supply_chain_visualization(
    po_id: str,
    include_gap_analysis: bool = Query(True, description="Include gap analysis"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get supply chain visualization for a purchase order.

    This endpoint delegates to the transparency visualization service.
    """
    try:
        # Convert string to UUID if needed
        try:
            po_uuid = UUID(po_id)
        except ValueError:
            # Handle mock PO IDs like 'po-001'
            if po_id.startswith('po-'):
                # For demo purposes, return mock data
                return {
                    "company_id": str(current_user.company_id),
                    "root_po_id": po_id,
                    "nodes": [],
                    "edges": [],
                    "total_levels": 0,
                    "max_width": 0,
                    "layout_algorithm": "hierarchical",
                    "overall_ttm_score": 0.0,
                    "overall_ttp_score": 0.0,
                    "overall_confidence": 0.0,
                    "traced_percentage": 0.0,
                    "untraced_percentage": 100.0,
                    "gap_analysis": [],
                    "generated_at": "2024-01-01T00:00:00Z",
                    "calculation_time_ms": 0
                }
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid purchase order ID format"
                )

        visualization_service = TransparencyVisualizationService(db)

        # Generate visualization
        visualization = visualization_service.generate_supply_chain_visualization(
            po_id=po_uuid,
            include_gap_analysis=include_gap_analysis
        )

        logger.info(
            "Supply chain visualization generated",
            po_id=po_id,
            user_id=str(current_user.id)
        )

        return visualization

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get supply chain visualization", po_id=po_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get supply chain visualization: {str(e)}"
        )


@router.get("/{company_id}/gaps", response_model=List[GapAnalysisItem])
async def get_gap_analysis(
    company_id: UUID,
    include_recommendations: bool = Query(True, description="Include improvement recommendations"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> List[GapAnalysisItem]:
    """
    Get transparency gaps and improvement recommendations for a company.
    """
    try:
        # Convert UUID to string format for database comparison
        company_id_str = str(company_id).replace('-', '')

        # Check if user has access to this company's data
        if (current_user.company_id and str(current_user.company_id).replace('-', '') != company_id_str) and current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to company data"
            )

        # Get purchase orders for the company (try both UUID formats)
        pos = db.query(PurchaseOrder).filter(
            (PurchaseOrder.buyer_company_id == str(company_id)) |
            (PurchaseOrder.buyer_company_id == company_id_str)
        ).limit(10).all()  # Limit for performance

        if not pos:
            return []  # Return empty list if no POs found

        # Generate realistic sample gaps based on actual purchase order data
        all_gaps = []

        # Analyze transparency scores to identify gaps
        low_ttm_pos = [po for po in pos if (po.transparency_to_mill or 0) < 0.7]
        low_ttp_pos = [po for po in pos if (po.transparency_to_plantation or 0) < 0.6]
        unconfirmed_pos = [po for po in pos if po.status != "confirmed"]

        # Critical gap: Missing plantation traceability
        if low_ttp_pos:
            all_gaps.append(GapAnalysisItem(
                gap_id="gap-plantation-trace",
                category="incomplete_data",
                severity="critical",
                description=f"{len(low_ttp_pos)} purchase orders lack plantation-level transparency data",
                recommendation="Establish direct plantation partnerships and implement blockchain tracking",
                impact_score=15.2,
                implementation_effort="high"
            ))

        # High priority gap: Low mill transparency
        if low_ttm_pos:
            all_gaps.append(GapAnalysisItem(
                gap_id="gap-mill-transparency",
                category="low_transparency",
                severity="high",
                description=f"{len(low_ttm_pos)} orders have time-to-mill transparency below 70%",
                recommendation="Implement supplier tracking systems and conduct regular audits",
                impact_score=8.5,
                implementation_effort="medium"
            ))

        # Medium priority gap: Unconfirmed orders
        if unconfirmed_pos:
            all_gaps.append(GapAnalysisItem(
                gap_id="gap-unconfirmed-orders",
                category="unconfirmed_order",
                severity="medium",
                description=f"{len(unconfirmed_pos)} purchase orders awaiting supplier confirmation",
                recommendation="Follow up with suppliers and implement automated confirmation system",
                impact_score=6.8,
                implementation_effort="low"
            ))

        logger.info(
            "Gap analysis completed",
            company_id=str(company_id),
            gaps_found=len(all_gaps),
            user_id=str(current_user.id)
        )

        return all_gaps

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get gap analysis", company_id=str(company_id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get gap analysis: {str(e)}"
        )


@router.get("/consultant/{consultant_id}/dashboard", response_model=MultiClientDashboard)
async def get_multi_client_dashboard(
    consultant_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> MultiClientDashboard:
    """
    Get multi-client dashboard for consultants.
    """
    try:
        # Check if user is a consultant and has access
        if current_user.role != "consultant" and str(current_user.id) != str(consultant_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to consultant dashboard"
            )

        # For now, return mock data
        # TODO: Implement actual multi-client dashboard logic
        return MultiClientDashboard(
            consultant_id=str(consultant_id),
            clients=[],
            summary_metrics={
                "total_clients": 0,
                "average_transparency": 0.0,
                "total_pos": 0
            },
            generated_at="2024-01-01T00:00:00Z"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get multi-client dashboard", consultant_id=str(consultant_id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get multi-client dashboard: {str(e)}"
        )


@router.post("/recalculate")
async def recalculate_transparency(
    request: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Trigger transparency recalculation for a company.
    """
    try:
        company_id = request.get("company_id")
        if not company_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="company_id is required"
            )

        company_uuid = UUID(company_id)
        company_id_str = str(company_uuid).replace('-', '')

        # Check if user has access to this company's data
        if (current_user.company_id and str(current_user.company_id).replace('-', '') != company_id_str) and current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to company data"
            )

        # Get purchase orders for the company (try both UUID formats)
        pos = db.query(PurchaseOrder).filter(
            (PurchaseOrder.buyer_company_id == str(company_uuid)) |
            (PurchaseOrder.buyer_company_id == company_id_str)
        ).all()

        transparency_engine = TransparencyCalculationEngine(db)

        # Recalculate transparency for all POs
        recalculated_count = 0
        for po in pos:
            try:
                transparency_engine.calculate_transparency_scores(
                    po_id=po.id,
                    use_cache=False  # Force recalculation by disabling cache
                )
                recalculated_count += 1
            except Exception as e:
                logger.warning(f"Failed to recalculate transparency for PO {po.id}: {str(e)}")
                continue

        logger.info(
            "Transparency recalculation completed",
            company_id=company_id,
            recalculated_count=recalculated_count,
            total_pos=len(pos),
            user_id=str(current_user.id)
        )

        return {
            "success": True,
            "message": f"Recalculated transparency for {recalculated_count} purchase orders",
            "recalculated_count": recalculated_count,
            "total_pos": len(pos)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to recalculate transparency", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to recalculate transparency: {str(e)}"
        )


@router.get("/{company_id}/summary", response_model=CompanyTransparencySummary)
async def get_company_transparency_summary(
    company_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> CompanyTransparencySummary:
    """
    Get comprehensive transparency summary for a company.
    """
    try:
        # Convert UUID to string format for database comparison
        company_id_str = str(company_id).replace('-', '')

        # Check if user has access to this company's data
        if (current_user.company_id and str(current_user.company_id).replace('-', '') != company_id_str) and current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to company data"
            )

        # Get transparency metrics
        metrics = await get_transparency_metrics(company_id, db, current_user)

        # Get gap analysis
        gaps = await get_gap_analysis(company_id, True, db, current_user)

        # Get company name
        from app.models.company import Company
        company = db.query(Company).filter(Company.id == company_id).first()
        company_name = company.name if company else "Unknown Company"

        # Get recent improvements (last 30 days)
        recent_improvements = await get_recent_improvements(company_id, db)

        return CompanyTransparencySummary(
            company_id=str(company_id),
            company_name=company_name,
            transparency_metrics=metrics,
            recent_improvements=recent_improvements,
            key_gaps=gaps[:5]  # Top 5 gaps
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get company transparency summary", company_id=str(company_id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get company transparency summary: {str(e)}"
        )


@router.get("/v2/companies/{company_id}/recent-improvements")
async def get_recent_improvements(
    company_id: UUID,
    days: int = 30,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get recent transparency improvements for a company."""

    try:
        # Check access permissions
        if not await _can_access_company_data(current_user, company_id, db):
            raise HTTPException(status_code=403, detail="Access denied")

        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)

        # Get current transparency metrics
        current_metrics = await _get_transparency_metrics(company_id, db)

        # Get historical transparency metrics
        historical_metrics = await _get_historical_transparency_metrics(
            company_id, start_date, db
        )

        # Calculate improvements
        improvements = _calculate_improvements(current_metrics, historical_metrics)

        # Get recent actions that contributed to improvements
        recent_actions = await _get_recent_improvement_actions(company_id, start_date, db)

        return {
            "success": True,
            "period_days": days,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "improvements": improvements,
            "recent_actions": recent_actions,
            "summary": {
                "total_improvements": len(improvements),
                "best_improvement": max(improvements, key=lambda x: x.get("change_percentage", 0)) if improvements else None
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get recent improvements", company_id=str(company_id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get recent improvements: {str(e)}"
        )


async def _can_access_company_data(current_user: User, company_id: UUID, db: Session) -> bool:
    """Check if user can access company data."""
    # Admin users can access any company
    if current_user.role == "admin":
        return True

    # Users can access their own company data
    if current_user.company_id == company_id:
        return True

    # Check if user has explicit permission through business relationships
    # This would be implemented based on business relationship permissions
    return False


async def _get_transparency_metrics(company_id: UUID, db: Session) -> Dict[str, Any]:
    """Get current transparency metrics for a company."""

    # Get all purchase orders for the company
    pos = db.query(PurchaseOrder).filter(
        PurchaseOrder.buyer_company_id == company_id
    ).all()

    if not pos:
        return {
            "transparency_to_mill_percentage": 0.0,
            "transparency_to_plantation_percentage": 0.0,
            "total_purchase_orders": 0,
            "traced_purchase_orders": 0,
            "total_volume": 0.0,
            "traced_volume": 0.0
        }

    total_pos = len(pos)
    traced_pos = 0
    total_volume = 0.0
    traced_volume = 0.0
    mill_transparency_sum = 0.0
    plantation_transparency_sum = 0.0

    for po in pos:
        total_volume += float(po.quantity or 0)

        # Check if PO has transparency data
        if hasattr(po, 'transparency_score') and po.transparency_score:
            traced_pos += 1
            traced_volume += float(po.quantity or 0)

            # Add to transparency sums for averaging
            mill_transparency_sum += po.transparency_score.get('mill_percentage', 0)
            plantation_transparency_sum += po.transparency_score.get('plantation_percentage', 0)

    # Calculate averages
    mill_percentage = mill_transparency_sum / total_pos if total_pos > 0 else 0.0
    plantation_percentage = plantation_transparency_sum / total_pos if total_pos > 0 else 0.0

    return {
        "transparency_to_mill_percentage": mill_percentage,
        "transparency_to_plantation_percentage": plantation_percentage,
        "total_purchase_orders": total_pos,
        "traced_purchase_orders": traced_pos,
        "total_volume": total_volume,
        "traced_volume": traced_volume
    }


async def _get_historical_transparency_metrics(
    company_id: UUID,
    date: datetime,
    db: Session
) -> Optional[Dict[str, Any]]:
    """Get transparency metrics from a specific historical date."""

    # For now, we'll calculate historical metrics from PO data
    # In a production system, you'd want to store daily snapshots
    return await _calculate_historical_metrics(company_id, date, db)


async def _calculate_historical_metrics(
    company_id: UUID,
    date: datetime,
    db: Session
) -> Dict[str, Any]:
    """Calculate historical transparency metrics from PO data."""

    # Get purchase orders that existed at the historical date
    pos = db.query(PurchaseOrder).filter(
        PurchaseOrder.buyer_company_id == company_id,
        PurchaseOrder.created_at <= date
    ).all()

    if not pos:
        return {
            "transparency_to_mill_percentage": 0.0,
            "transparency_to_plantation_percentage": 0.0,
            "total_purchase_orders": 0,
            "traced_purchase_orders": 0,
            "total_volume": 0.0,
            "traced_volume": 0.0
        }

    # Calculate metrics as of that date
    total_pos = len(pos)
    traced_pos = sum(1 for po in pos if hasattr(po, 'transparency_score') and po.transparency_score)
    total_volume = sum(float(po.quantity or 0) for po in pos)
    traced_volume = sum(float(po.quantity or 0) for po in pos if hasattr(po, 'transparency_score') and po.transparency_score)

    # Calculate average transparency percentages
    mill_sum = sum(po.transparency_score.get('mill_percentage', 0) for po in pos if hasattr(po, 'transparency_score') and po.transparency_score)
    plantation_sum = sum(po.transparency_score.get('plantation_percentage', 0) for po in pos if hasattr(po, 'transparency_score') and po.transparency_score)

    mill_percentage = mill_sum / traced_pos if traced_pos > 0 else 0.0
    plantation_percentage = plantation_sum / traced_pos if traced_pos > 0 else 0.0

    return {
        "transparency_to_mill_percentage": mill_percentage,
        "transparency_to_plantation_percentage": plantation_percentage,
        "total_purchase_orders": total_pos,
        "traced_purchase_orders": traced_pos,
        "total_volume": total_volume,
        "traced_volume": traced_volume
    }


def _calculate_improvements(
    current: Dict[str, Any],
    historical: Optional[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """Calculate improvements between current and historical metrics."""

    if not historical:
        return []

    improvements = []

    # Mill transparency improvement
    mill_current = current.get("transparency_to_mill_percentage", 0)
    mill_historical = historical.get("transparency_to_mill_percentage", 0)
    mill_change = mill_current - mill_historical

    if mill_change > 0:
        improvements.append({
            "metric": "mill_transparency",
            "label": "Mill Transparency",
            "current_value": round(mill_current, 2),
            "previous_value": round(mill_historical, 2),
            "change": round(mill_change, 2),
            "change_percentage": round((mill_change / mill_historical * 100) if mill_historical > 0 else 0, 2),
            "trend": "improving",
            "unit": "%"
        })

    # Plantation transparency improvement
    plantation_current = current.get("transparency_to_plantation_percentage", 0)
    plantation_historical = historical.get("transparency_to_plantation_percentage", 0)
    plantation_change = plantation_current - plantation_historical

    if plantation_change > 0:
        improvements.append({
            "metric": "plantation_transparency",
            "label": "Plantation Transparency",
            "current_value": round(plantation_current, 2),
            "previous_value": round(plantation_historical, 2),
            "change": round(plantation_change, 2),
            "change_percentage": round((plantation_change / plantation_historical * 100) if plantation_historical > 0 else 0, 2),
            "trend": "improving",
            "unit": "%"
        })

    # PO tracing improvement
    traced_current = current.get("traced_purchase_orders", 0)
    traced_historical = historical.get("traced_purchase_orders", 0)
    traced_change = traced_current - traced_historical

    if traced_change > 0:
        improvements.append({
            "metric": "traced_orders",
            "label": "Traced Purchase Orders",
            "current_value": traced_current,
            "previous_value": traced_historical,
            "change": traced_change,
            "change_percentage": round((traced_change / traced_historical * 100) if traced_historical > 0 else 0, 2),
            "trend": "improving",
            "unit": "orders"
        })

    return improvements


async def _get_recent_improvement_actions(
    company_id: UUID,
    start_date: datetime,
    db: Session
) -> List[Dict[str, Any]]:
    """Get recent actions that contributed to transparency improvements."""

    actions = []

    # Get recent gap actions that were resolved
    from app.models.gap_action import GapAction
    recent_gap_actions = db.query(GapAction).filter(
        GapAction.company_id == company_id,
        GapAction.created_at >= start_date,
        GapAction.status == 'resolved'
    ).all()

    for action in recent_gap_actions:
        actions.append({
            "type": "gap_resolution",
            "description": f"Resolved transparency gap: {action.action_type}",
            "date": action.resolved_at.isoformat() if action.resolved_at else action.created_at.isoformat(),
            "impact": "Improved supply chain visibility"
        })

    # Get recent document uploads
    from app.models.document import Document
    recent_documents = db.query(Document).filter(
        Document.company_id == company_id,
        Document.created_at >= start_date,
        Document.validation_status == 'valid'
    ).limit(10).all()

    for doc in recent_documents:
        actions.append({
            "type": "document_upload",
            "description": f"Uploaded {doc.document_type}: {doc.file_name}",
            "date": doc.created_at.isoformat(),
            "impact": "Enhanced traceability documentation"
        })

    # Sort by date (most recent first)
    actions.sort(key=lambda x: x["date"], reverse=True)

    return actions[:10]  # Return top 10 recent actions


@router.get("/v2/companies/{company_id}/transparency-dashboard")
async def get_transparency_dashboard(
    company_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get comprehensive transparency dashboard data for a company."""

    try:
        # Check access permissions
        if not await _can_access_company_data(current_user, company_id, db):
            raise HTTPException(status_code=403, detail="Access denied")

        # Get current transparency metrics
        current_metrics = await _get_transparency_metrics(company_id, db)

        # Get recent improvements (last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_improvements = await _get_recent_improvement_actions(company_id, thirty_days_ago, db)

        # Get transparency gaps
        transparency_gaps = await _get_transparency_gaps(company_id, db)

        # Get supply chain visibility stats
        supply_chain_stats = await _get_supply_chain_stats(company_id, db)

        # Get compliance status
        compliance_status = await _get_compliance_status(company_id, db)

        # Calculate overall transparency score
        transparency_score = _calculate_transparency_score(current_metrics, transparency_gaps)

        return {
            "success": True,
            "company_id": str(company_id),
            "generated_at": datetime.utcnow().isoformat(),
            "transparency_score": transparency_score,
            "metrics": current_metrics,
            "recent_improvements": recent_improvements[:5],  # Top 5 recent improvements
            "transparency_gaps": transparency_gaps[:10],  # Top 10 gaps
            "supply_chain_stats": supply_chain_stats,
            "compliance_status": compliance_status,
            "summary": {
                "total_purchase_orders": current_metrics.get("total_purchase_orders", 0),
                "transparency_to_mill_percentage": current_metrics.get("transparency_to_mill_percentage", 0),
                "transparency_to_plantation_percentage": current_metrics.get("transparency_to_plantation_percentage", 0),
                "total_gaps": len(transparency_gaps),
                "critical_gaps": len([gap for gap in transparency_gaps if gap.get("severity") == "critical"]),
                "recent_improvements_count": len(recent_improvements)
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get transparency dashboard", company_id=str(company_id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get transparency dashboard: {str(e)}"
        )


async def _get_transparency_gaps(company_id: UUID, db: Session) -> List[Dict[str, Any]]:
    """Get transparency gaps for a company."""
    try:
        # Get purchase orders with missing data
        pos = db.query(PurchaseOrder).filter(
            PurchaseOrder.buyer_company_id == company_id
        ).all()

        gaps = []
        for po in pos:
            # Check for missing traceability data
            if not po.seller_confirmed_at:
                gaps.append({
                    "type": "missing_confirmation",
                    "severity": "high",
                    "description": f"Purchase Order {po.po_number} not confirmed by seller",
                    "po_id": str(po.id),
                    "po_number": po.po_number,
                    "created_at": po.created_at.isoformat() if po.created_at else None
                })

            # Check for missing origin data
            if not po.origin_data:
                gaps.append({
                    "type": "missing_origin_data",
                    "severity": "medium",
                    "description": f"Purchase Order {po.po_number} missing origin data",
                    "po_id": str(po.id),
                    "po_number": po.po_number,
                    "created_at": po.created_at.isoformat() if po.created_at else None
                })

        return gaps

    except Exception as e:
        logger.error(f"Error getting transparency gaps: {str(e)}")
        return []


async def _get_supply_chain_stats(company_id: UUID, db: Session) -> Dict[str, Any]:
    """Get supply chain visibility statistics."""
    try:
        # Get purchase orders
        pos = db.query(PurchaseOrder).filter(
            PurchaseOrder.buyer_company_id == company_id
        ).all()

        total_pos = len(pos)
        confirmed_pos = len([po for po in pos if po.seller_confirmed_at])

        # Get unique suppliers
        supplier_ids = set(po.seller_company_id for po in pos if po.seller_company_id)

        return {
            "total_purchase_orders": total_pos,
            "confirmed_purchase_orders": confirmed_pos,
            "confirmation_rate": (confirmed_pos / total_pos * 100) if total_pos > 0 else 0,
            "unique_suppliers": len(supplier_ids),
            "average_confirmation_time_days": 0,  # Would calculate from actual data
            "supply_chain_depth": {
                "tier_1_suppliers": len(supplier_ids),
                "tier_2_suppliers": 0,  # Would calculate from relationship data
                "tier_3_suppliers": 0
            }
        }

    except Exception as e:
        logger.error(f"Error getting supply chain stats: {str(e)}")
        return {
            "total_purchase_orders": 0,
            "confirmed_purchase_orders": 0,
            "confirmation_rate": 0,
            "unique_suppliers": 0,
            "average_confirmation_time_days": 0,
            "supply_chain_depth": {
                "tier_1_suppliers": 0,
                "tier_2_suppliers": 0,
                "tier_3_suppliers": 0
            }
        }


async def _get_compliance_status(company_id: UUID, db: Session) -> Dict[str, Any]:
    """Get compliance status for regulations like EUDR, UFLPA."""
    try:
        # This would integrate with compliance service
        # For now, return mock data based on transparency metrics

        return {
            "eudr_compliance": {
                "status": "compliant",
                "score": 85,
                "last_assessment": datetime.utcnow().isoformat(),
                "requirements_met": 8,
                "total_requirements": 10
            },
            "uflpa_compliance": {
                "status": "under_review",
                "score": 75,
                "last_assessment": datetime.utcnow().isoformat(),
                "requirements_met": 6,
                "total_requirements": 8
            },
            "overall_compliance_score": 80
        }

    except Exception as e:
        logger.error(f"Error getting compliance status: {str(e)}")
        return {
            "eudr_compliance": {"status": "unknown", "score": 0},
            "uflpa_compliance": {"status": "unknown", "score": 0},
            "overall_compliance_score": 0
        }


def _calculate_transparency_score(metrics: Dict[str, Any], gaps: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate overall transparency score."""
    try:
        # Base score from transparency percentages
        mill_transparency = metrics.get("transparency_to_mill_percentage", 0)
        plantation_transparency = metrics.get("transparency_to_plantation_percentage", 0)

        # Calculate base score (average of mill and plantation transparency)
        base_score = (mill_transparency + plantation_transparency) / 2

        # Deduct points for gaps
        critical_gaps = len([gap for gap in gaps if gap.get("severity") == "critical"])
        high_gaps = len([gap for gap in gaps if gap.get("severity") == "high"])
        medium_gaps = len([gap for gap in gaps if gap.get("severity") == "medium"])

        # Penalty calculation
        penalty = (critical_gaps * 10) + (high_gaps * 5) + (medium_gaps * 2)
        final_score = max(0, base_score - penalty)

        # Determine grade
        if final_score >= 90:
            grade = "A"
        elif final_score >= 80:
            grade = "B"
        elif final_score >= 70:
            grade = "C"
        elif final_score >= 60:
            grade = "D"
        else:
            grade = "F"

        return {
            "score": round(final_score, 1),
            "grade": grade,
            "mill_transparency": round(mill_transparency, 1),
            "plantation_transparency": round(plantation_transparency, 1),
            "gaps_penalty": penalty,
            "breakdown": {
                "base_score": round(base_score, 1),
                "critical_gaps": critical_gaps,
                "high_gaps": high_gaps,
                "medium_gaps": medium_gaps,
                "total_penalty": penalty
            }
        }

    except Exception as e:
        logger.error(f"Error calculating transparency score: {str(e)}")
        return {
            "score": 0,
            "grade": "F",
            "mill_transparency": 0,
            "plantation_transparency": 0,
            "gaps_penalty": 0,
            "breakdown": {
                "base_score": 0,
                "critical_gaps": 0,
                "high_gaps": 0,
                "medium_gaps": 0,
                "total_penalty": 0
            }
        }
