"""
API endpoints for transparency visualization and gap analysis.
"""
from typing import List, Optional, Dict, Any
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.services.transparency_visualization import (
    TransparencyVisualizationService,
    SupplyChainVisualization,
    GapAnalysisResult,
    VisualizationNode,
    VisualizationEdge
)
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/transparency-visualization", tags=["transparency-visualization"])


# Response Models
class VisualizationNodeResponse(BaseModel):
    """Response model for visualization nodes."""
    id: str
    po_id: str
    po_number: str
    company_id: str
    company_name: str
    company_type: str
    product_name: str
    quantity: float
    unit: str
    level: int
    position_x: float
    position_y: float
    ttm_score: float
    ttp_score: float
    confidence_level: float
    traced_percentage: float
    node_color: str
    node_size: int
    border_color: str
    border_width: int
    has_origin_data: bool
    has_geographic_coordinates: bool
    has_certifications: bool
    missing_data_fields: List[str]
    is_gap: bool
    gap_type: str
    gap_severity: str
    improvement_potential: float
    
    class Config:
        from_attributes = True


class VisualizationEdgeResponse(BaseModel):
    """Response model for visualization edges."""
    id: str
    source_node_id: str
    target_node_id: str
    relationship_type: str
    quantity_flow: float
    unit: str
    edge_color: str
    edge_width: int
    edge_style: str
    transparency_flow: float
    confidence_flow: float
    is_missing_link: bool
    is_weak_link: bool
    improvement_priority: str
    
    class Config:
        from_attributes = True


class GapDetailResponse(BaseModel):
    """Response model for gap details."""
    po_id: str
    category: str
    severity: str
    description: str
    impact: float
    recommendation: str


class ImprovementRecommendationResponse(BaseModel):
    """Response model for improvement recommendations."""
    category: str
    priority: str
    title: str
    description: str
    expected_ttm_impact: float
    expected_ttp_impact: float
    implementation_effort: str
    timeline: str
    actions: List[str]


class GapAnalysisResponse(BaseModel):
    """Response model for gap analysis."""
    company_id: str
    total_gaps: int
    critical_gaps: int
    high_priority_gaps: int
    medium_priority_gaps: int
    low_priority_gaps: int
    missing_origin_data_gaps: int
    missing_input_material_gaps: int
    missing_certification_gaps: int
    missing_geographic_data_gaps: int
    unconfirmed_po_gaps: int
    current_ttm_score: float
    current_ttp_score: float
    potential_ttm_score: float
    potential_ttp_score: float
    gap_details: List[GapDetailResponse]
    improvement_recommendations: List[ImprovementRecommendationResponse]
    
    class Config:
        from_attributes = True


class SupplyChainVisualizationResponse(BaseModel):
    """Response model for supply chain visualization."""
    company_id: str
    root_po_id: str
    nodes: List[VisualizationNodeResponse]
    edges: List[VisualizationEdgeResponse]
    total_levels: int
    max_width: int
    layout_algorithm: str
    overall_ttm_score: float
    overall_ttp_score: float
    overall_confidence: float
    traced_percentage: float
    untraced_percentage: float
    gap_analysis: Optional[GapAnalysisResponse] = None
    generated_at: str
    calculation_time_ms: int
    
    class Config:
        from_attributes = True


class PartialTraceabilityResponse(BaseModel):
    """Response model for partial traceability calculation."""
    company_id: str
    total_purchase_orders: int
    traced_purchase_orders: int
    untraced_purchase_orders: int
    traced_percentage: float
    untraced_percentage: float
    traced_volume: float
    untraced_volume: float
    volume_unit: str
    traceability_by_product: Dict[str, Dict[str, float]]
    traceability_by_supplier: Dict[str, Dict[str, float]]
    improvement_opportunities: List[str]


@router.get("/supply-chain/{po_id}", response_model=SupplyChainVisualizationResponse)
async def get_supply_chain_visualization(
    po_id: UUID,
    include_gap_analysis: bool = Query(True, description="Include gap analysis in visualization"),
    max_depth: Optional[int] = Query(None, description="Maximum depth for visualization"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> SupplyChainVisualizationResponse:
    """
    Generate supply chain visualization for a purchase order.
    
    Creates a comprehensive visual representation of the supply chain
    including nodes, edges, transparency scores, and gap analysis.
    """
    try:
        visualization_service = TransparencyVisualizationService(db)
        
        # Generate visualization
        visualization = visualization_service.generate_supply_chain_visualization(
            po_id=po_id,
            include_gap_analysis=include_gap_analysis,
            max_depth=max_depth
        )
        
        # Convert to response format
        nodes_response = [
            VisualizationNodeResponse(
                id=node.id,
                po_id=str(node.po_id),
                po_number=node.po_number,
                company_id=str(node.company_id),
                company_name=node.company_name,
                company_type=node.company_type,
                product_name=node.product_name,
                quantity=node.quantity,
                unit=node.unit,
                level=node.level,
                position_x=node.position_x,
                position_y=node.position_y,
                ttm_score=node.ttm_score,
                ttp_score=node.ttp_score,
                confidence_level=node.confidence_level,
                traced_percentage=node.traced_percentage,
                node_color=node.node_color,
                node_size=node.node_size,
                border_color=node.border_color,
                border_width=node.border_width,
                has_origin_data=node.has_origin_data,
                has_geographic_coordinates=node.has_geographic_coordinates,
                has_certifications=node.has_certifications,
                missing_data_fields=node.missing_data_fields,
                is_gap=node.is_gap,
                gap_type=node.gap_type,
                gap_severity=node.gap_severity,
                improvement_potential=node.improvement_potential
            )
            for node in visualization.nodes
        ]
        
        edges_response = [
            VisualizationEdgeResponse(
                id=edge.id,
                source_node_id=edge.source_node_id,
                target_node_id=edge.target_node_id,
                relationship_type=edge.relationship_type,
                quantity_flow=edge.quantity_flow,
                unit=edge.unit,
                edge_color=edge.edge_color,
                edge_width=edge.edge_width,
                edge_style=edge.edge_style,
                transparency_flow=edge.transparency_flow,
                confidence_flow=edge.confidence_flow,
                is_missing_link=edge.is_missing_link,
                is_weak_link=edge.is_weak_link,
                improvement_priority=edge.improvement_priority
            )
            for edge in visualization.edges
        ]
        
        gap_analysis_response = None
        if visualization.gap_analysis:
            gap_analysis_response = GapAnalysisResponse(
                company_id=str(visualization.gap_analysis.company_id),
                total_gaps=visualization.gap_analysis.total_gaps,
                critical_gaps=visualization.gap_analysis.critical_gaps,
                high_priority_gaps=visualization.gap_analysis.high_priority_gaps,
                medium_priority_gaps=visualization.gap_analysis.medium_priority_gaps,
                low_priority_gaps=visualization.gap_analysis.low_priority_gaps,
                missing_origin_data_gaps=visualization.gap_analysis.missing_origin_data_gaps,
                missing_input_material_gaps=visualization.gap_analysis.missing_input_material_gaps,
                missing_certification_gaps=visualization.gap_analysis.missing_certification_gaps,
                missing_geographic_data_gaps=visualization.gap_analysis.missing_geographic_data_gaps,
                unconfirmed_po_gaps=visualization.gap_analysis.unconfirmed_po_gaps,
                current_ttm_score=visualization.gap_analysis.current_ttm_score,
                current_ttp_score=visualization.gap_analysis.current_ttp_score,
                potential_ttm_score=visualization.gap_analysis.potential_ttm_score,
                potential_ttp_score=visualization.gap_analysis.potential_ttp_score,
                gap_details=[
                    GapDetailResponse(
                        po_id=gap["po_id"],
                        category=gap["category"],
                        severity=gap["severity"],
                        description=gap["description"],
                        impact=gap["impact"],
                        recommendation=gap["recommendation"]
                    )
                    for gap in visualization.gap_analysis.gap_details
                ],
                improvement_recommendations=[
                    ImprovementRecommendationResponse(
                        category=rec["category"],
                        priority=rec["priority"],
                        title=rec["title"],
                        description=rec["description"],
                        expected_ttm_impact=rec["expected_ttm_impact"],
                        expected_ttp_impact=rec["expected_ttp_impact"],
                        implementation_effort=rec["implementation_effort"],
                        timeline=rec["timeline"],
                        actions=rec["actions"]
                    )
                    for rec in visualization.gap_analysis.improvement_recommendations
                ]
            )
        
        return SupplyChainVisualizationResponse(
            company_id=str(visualization.company_id),
            root_po_id=str(visualization.root_po_id),
            nodes=nodes_response,
            edges=edges_response,
            total_levels=visualization.total_levels,
            max_width=visualization.max_width,
            layout_algorithm=visualization.layout_algorithm,
            overall_ttm_score=visualization.overall_ttm_score,
            overall_ttp_score=visualization.overall_ttp_score,
            overall_confidence=visualization.overall_confidence,
            traced_percentage=visualization.traced_percentage,
            untraced_percentage=visualization.untraced_percentage,
            gap_analysis=gap_analysis_response,
            generated_at=visualization.generated_at.isoformat(),
            calculation_time_ms=visualization.calculation_time_ms
        )
        
    except Exception as e:
        logger.error("Failed to generate supply chain visualization", po_id=str(po_id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate visualization: {str(e)}"
        )


@router.get("/gaps/{company_id}", response_model=GapAnalysisResponse)
async def get_transparency_gaps(
    company_id: UUID,
    include_recommendations: bool = Query(True, description="Include improvement recommendations"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> GapAnalysisResponse:
    """
    Get transparency gaps and improvement recommendations for a company.

    Analyzes all purchase orders for the company to identify transparency
    gaps and provide actionable improvement recommendations.
    """
    try:
        from app.models.purchase_order import PurchaseOrder
        from app.services.transparency_engine import TransparencyCalculationEngine

        # Check if user has access to this company's data
        if current_user.company_id != company_id and current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to company data"
            )

        # Get all purchase orders for the company
        pos = db.query(PurchaseOrder).filter(
            PurchaseOrder.buyer_company_id == company_id
        ).limit(50).all()  # Limit for performance

        if not pos:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No purchase orders found for company"
            )

        visualization_service = TransparencyVisualizationService(db)
        transparency_engine = TransparencyCalculationEngine(db)

        # Analyze gaps across all POs
        all_gaps = []
        all_recommendations = []
        total_ttm = 0.0
        total_ttp = 0.0

        for po in pos:
            try:
                # Calculate transparency for this PO
                result = transparency_engine.calculate_transparency(
                    po_id=po.id,
                    include_detailed_analysis=True
                )

                # Analyze gaps
                gap_analysis = visualization_service.analyze_transparency_gaps(
                    result, company_id
                )

                all_gaps.extend(gap_analysis.gap_details)
                if include_recommendations:
                    all_recommendations.extend(gap_analysis.improvement_recommendations)

                total_ttm += result.ttm_score
                total_ttp += result.ttp_score

            except Exception as e:
                logger.warning(f"Failed to analyze PO {po.id}: {str(e)}")
                continue

        # Aggregate results
        avg_ttm = total_ttm / len(pos) if pos else 0.0
        avg_ttp = total_ttp / len(pos) if pos else 0.0

        # Count gaps by category and severity
        gap_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        category_counts = {
            "missing_origin_data": 0,
            "missing_input_material": 0,
            "missing_certification": 0,
            "missing_geographic_data": 0,
            "unconfirmed_po": 0
        }

        for gap in all_gaps:
            gap_counts[gap.get("severity", "low")] += 1
            category_counts[gap.get("category", "unknown")] += 1

        # Calculate improvement potential
        potential_ttm = min(avg_ttm + 0.3, 1.0)  # Simplified calculation
        potential_ttp = min(avg_ttp + 0.3, 1.0)

        # Deduplicate recommendations
        unique_recommendations = []
        seen_categories = set()
        for rec in all_recommendations:
            if rec["category"] not in seen_categories:
                unique_recommendations.append(rec)
                seen_categories.add(rec["category"])

        return GapAnalysisResponse(
            company_id=str(company_id),
            total_gaps=len(all_gaps),
            critical_gaps=gap_counts["critical"],
            high_priority_gaps=gap_counts["high"],
            medium_priority_gaps=gap_counts["medium"],
            low_priority_gaps=gap_counts["low"],
            missing_origin_data_gaps=category_counts["missing_origin_data"],
            missing_input_material_gaps=category_counts["missing_input_material"],
            missing_certification_gaps=category_counts["missing_certification"],
            missing_geographic_data_gaps=category_counts["missing_geographic_data"],
            unconfirmed_po_gaps=category_counts["unconfirmed_po"],
            current_ttm_score=avg_ttm,
            current_ttp_score=avg_ttp,
            potential_ttm_score=potential_ttm,
            potential_ttp_score=potential_ttp,
            gap_details=[
                GapDetailResponse(
                    po_id=gap["po_id"],
                    category=gap["category"],
                    severity=gap["severity"],
                    description=gap["description"],
                    impact=gap["impact"],
                    recommendation=gap["recommendation"]
                )
                for gap in all_gaps[:100]  # Limit for performance
            ],
            improvement_recommendations=[
                ImprovementRecommendationResponse(
                    category=rec["category"],
                    priority=rec["priority"],
                    title=rec["title"],
                    description=rec["description"],
                    expected_ttm_impact=rec["expected_ttm_impact"],
                    expected_ttp_impact=rec["expected_ttp_impact"],
                    implementation_effort=rec["implementation_effort"],
                    timeline=rec["timeline"],
                    actions=rec["actions"]
                )
                for rec in unique_recommendations
            ]
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to analyze transparency gaps", company_id=str(company_id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze gaps: {str(e)}"
        )


@router.get("/partial-traceability/{company_id}", response_model=PartialTraceabilityResponse)
async def get_partial_traceability(
    company_id: UUID,
    include_breakdown: bool = Query(True, description="Include breakdown by product and supplier"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> PartialTraceabilityResponse:
    """
    Calculate partial traceability showing traced vs untraced percentages.

    Provides comprehensive analysis of what percentage of materials
    can be traced through the supply chain.
    """
    try:
        from app.models.purchase_order import PurchaseOrder
        from app.models.product import Product
        from app.models.company import Company
        from sqlalchemy import func, case, or_

        # Check access permissions
        if current_user.company_id != company_id and current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to company data"
            )

        # Get all purchase orders for the company
        pos_query = db.query(PurchaseOrder).filter(
            PurchaseOrder.buyer_company_id == company_id
        )

        total_pos = pos_query.count()

        if total_pos == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No purchase orders found for company"
            )

        # Calculate traced vs untraced
        traced_pos = pos_query.filter(
            or_(
                PurchaseOrder.transparency_to_mill.isnot(None),
                PurchaseOrder.transparency_to_plantation.isnot(None)
            )
        ).count()

        untraced_pos = total_pos - traced_pos
        traced_percentage = (traced_pos / total_pos) * 100 if total_pos > 0 else 0.0
        untraced_percentage = 100.0 - traced_percentage

        # Calculate volume-based traceability
        total_volume_result = db.query(func.sum(PurchaseOrder.quantity)).filter(
            PurchaseOrder.buyer_company_id == company_id
        ).scalar() or 0.0

        traced_volume_result = db.query(func.sum(PurchaseOrder.quantity)).filter(
            PurchaseOrder.buyer_company_id == company_id,
            or_(
                PurchaseOrder.transparency_to_mill.isnot(None),
                PurchaseOrder.transparency_to_plantation.isnot(None)
            )
        ).scalar() or 0.0

        traced_volume = float(traced_volume_result)
        total_volume = float(total_volume_result)
        untraced_volume = total_volume - traced_volume

        # Breakdown by product and supplier if requested
        traceability_by_product = {}
        traceability_by_supplier = {}

        if include_breakdown:
            # Product breakdown
            product_stats = db.query(
                Product.name,
                func.count(PurchaseOrder.id).label('total_pos'),
                func.count(
                    case(
                        (or_(
                            PurchaseOrder.transparency_to_mill.isnot(None),
                            PurchaseOrder.transparency_to_plantation.isnot(None)
                        ), PurchaseOrder.id)
                    )
                ).label('traced_pos'),
                func.sum(PurchaseOrder.quantity).label('total_volume'),
                func.sum(
                    case(
                        (or_(
                            PurchaseOrder.transparency_to_mill.isnot(None),
                            PurchaseOrder.transparency_to_plantation.isnot(None)
                        ), PurchaseOrder.quantity)
                    )
                ).label('traced_volume')
            ).join(
                PurchaseOrder, Product.id == PurchaseOrder.product_id
            ).filter(
                PurchaseOrder.buyer_company_id == company_id
            ).group_by(Product.name).all()

            for stat in product_stats:
                traced_pct = (stat.traced_pos / stat.total_pos * 100) if stat.total_pos > 0 else 0.0
                traced_vol_pct = (float(stat.traced_volume or 0) / float(stat.total_volume or 1) * 100) if stat.total_volume else 0.0

                traceability_by_product[stat.name] = {
                    "traced_percentage": traced_pct,
                    "traced_volume_percentage": traced_vol_pct,
                    "total_orders": stat.total_pos,
                    "traced_orders": stat.traced_pos
                }

            # Supplier breakdown
            supplier_stats = db.query(
                Company.name,
                func.count(PurchaseOrder.id).label('total_pos'),
                func.count(
                    case(
                        (or_(
                            PurchaseOrder.transparency_to_mill.isnot(None),
                            PurchaseOrder.transparency_to_plantation.isnot(None)
                        ), PurchaseOrder.id)
                    )
                ).label('traced_pos'),
                func.sum(PurchaseOrder.quantity).label('total_volume'),
                func.sum(
                    case(
                        (or_(
                            PurchaseOrder.transparency_to_mill.isnot(None),
                            PurchaseOrder.transparency_to_plantation.isnot(None)
                        ), PurchaseOrder.quantity)
                    )
                ).label('traced_volume')
            ).join(
                PurchaseOrder, Company.id == PurchaseOrder.seller_company_id
            ).filter(
                PurchaseOrder.buyer_company_id == company_id
            ).group_by(Company.name).all()

            for stat in supplier_stats:
                traced_pct = (stat.traced_pos / stat.total_pos * 100) if stat.total_pos > 0 else 0.0
                traced_vol_pct = (float(stat.traced_volume or 0) / float(stat.total_volume or 1) * 100) if stat.total_volume else 0.0

                traceability_by_supplier[stat.name] = {
                    "traced_percentage": traced_pct,
                    "traced_volume_percentage": traced_vol_pct,
                    "total_orders": stat.total_pos,
                    "traced_orders": stat.traced_pos
                }

        # Generate improvement opportunities
        improvement_opportunities = []

        if traced_percentage < 50:
            improvement_opportunities.append("Focus on basic traceability implementation across all suppliers")
        if traced_percentage < 80:
            improvement_opportunities.append("Prioritize high-volume suppliers for traceability improvements")

        # Add product-specific opportunities
        for product, stats in traceability_by_product.items():
            if stats["traced_percentage"] < 60:
                improvement_opportunities.append(f"Improve traceability for {product} supply chain")

        # Add supplier-specific opportunities
        low_trace_suppliers = [
            supplier for supplier, stats in traceability_by_supplier.items()
            if stats["traced_percentage"] < 50
        ]
        if low_trace_suppliers:
            improvement_opportunities.append(f"Work with suppliers: {', '.join(low_trace_suppliers[:3])}")

        return PartialTraceabilityResponse(
            company_id=str(company_id),
            total_purchase_orders=total_pos,
            traced_purchase_orders=traced_pos,
            untraced_purchase_orders=untraced_pos,
            traced_percentage=traced_percentage,
            untraced_percentage=untraced_percentage,
            traced_volume=traced_volume,
            untraced_volume=untraced_volume,
            volume_unit="KGM",  # Default unit
            traceability_by_product=traceability_by_product,
            traceability_by_supplier=traceability_by_supplier,
            improvement_opportunities=improvement_opportunities
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to calculate partial traceability", company_id=str(company_id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to calculate traceability: {str(e)}"
        )
