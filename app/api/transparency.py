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
from app.services.transparency_engine import TransparencyCalculationEngine
from app.services.transparency_visualization import TransparencyVisualizationService
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
    
    Returns TTM/TTP scores, overall transparency, and confidence levels.
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
            # Return default metrics if no POs found
            return TransparencyMetrics(
                ttm_score=0.0,
                ttp_score=0.0,
                overall_score=0.0,
                confidence_level=0.0,
                traced_percentage=0.0,
                untraced_percentage=100.0,
                last_updated="2024-01-01T00:00:00Z"
            )

        transparency_engine = TransparencyCalculationEngine(db)

        # Calculate average metrics across all POs
        total_ttm = 0.0
        total_ttp = 0.0
        total_confidence = 0.0
        total_traced = 0.0
        valid_calculations = 0

        for po in pos:
            try:
                # Try to use the transparency engine first
                result = transparency_engine.calculate_transparency_scores(
                    po_id=po.id,
                    use_cache=True
                )
                total_ttm += result.ttm_score
                total_ttp += result.ttp_score
                total_confidence += result.confidence_level
                total_traced += result.traced_percentage
                valid_calculations += 1
            except Exception as e:
                logger.warning(f"Transparency engine failed for PO {po.id}: {str(e)}, falling back to stored values")
                # Fallback to stored transparency values
                try:
                    ttm_score = float(po.transparency_to_mill or 0.0)
                    ttp_score = float(po.transparency_to_plantation or 0.0)

                    if ttm_score > 0 or ttp_score > 0:  # Only use if we have actual data
                        total_ttm += ttm_score
                        total_ttp += ttp_score
                        # Estimate confidence and traced percentage from scores
                        avg_score = (ttm_score + ttp_score) / 2
                        total_confidence += min(avg_score * 1.2, 1.0)
                        total_traced += avg_score * 100.0
                        valid_calculations += 1
                except Exception as fallback_error:
                    logger.warning(f"Fallback also failed for PO {po.id}: {str(fallback_error)}")
                    continue

        if valid_calculations == 0:
            # Return default metrics if no valid calculations
            return TransparencyMetrics(
                ttm_score=0.0,
                ttp_score=0.0,
                overall_score=0.0,
                confidence_level=0.0,
                traced_percentage=0.0,
                untraced_percentage=100.0,
                last_updated="2024-01-01T00:00:00Z"
            )

        # Calculate averages
        avg_ttm = total_ttm / valid_calculations
        avg_ttp = total_ttp / valid_calculations
        avg_confidence = total_confidence / valid_calculations
        avg_traced = total_traced / valid_calculations
        overall_score = (avg_ttm + avg_ttp) / 2

        logger.info(
            "Transparency metrics calculated",
            company_id=str(company_id),
            ttm_score=avg_ttm,
            ttp_score=avg_ttp,
            overall_score=overall_score,
            user_id=str(current_user.id)
        )

        return TransparencyMetrics(
            ttm_score=avg_ttm,
            ttp_score=avg_ttp,
            overall_score=overall_score,
            confidence_level=avg_confidence,
            traced_percentage=avg_traced,
            untraced_percentage=100.0 - avg_traced,
            last_updated="2024-01-01T00:00:00Z"
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
