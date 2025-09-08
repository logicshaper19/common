"""
Main orchestrator for transparency visualization.

This service coordinates all visualization components while maintaining
clean separation of concerns and high testability.
"""
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session

from app.services.transparency_engine import TransparencyCalculationEngine
from app.services.transparency_engine.domain.models import TransparencyResult
from app.core.logging import get_logger
from .models.visualization_models import SupplyChainVisualization, VisualizationNode, VisualizationEdge
from .models.gap_models import GapAnalysisResult
from .gap_analyzer import TransparencyGapAnalyzer
from .recommendation_engine import ImprovementRecommendationEngine
from .styling_engine import VisualizationStylingEngine

logger = get_logger(__name__)


class TransparencyVisualizationService:
    """
    Main orchestrator for transparency visualization.
    
    This service coordinates all visualization components:
    - Gap analysis
    - Recommendation generation
    - Visual styling
    - Graph construction
    
    The service maintains clean separation of concerns by delegating
    specific responsibilities to specialized engines.
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.transparency_engine = TransparencyCalculationEngine(db)
        
        # Initialize specialized engines
        self.gap_analyzer = TransparencyGapAnalyzer(db)
        self.recommendation_engine = ImprovementRecommendationEngine(db)
        self.styling_engine = VisualizationStylingEngine(db)
    
    def generate_supply_chain_visualization(
        self,
        po_id: UUID,
        include_gap_analysis: bool = True,
        max_depth: Optional[int] = None
    ) -> SupplyChainVisualization:
        """
        Generate comprehensive supply chain visualization with gap analysis.
        
        Args:
            po_id: Root purchase order ID
            include_gap_analysis: Whether to include gap analysis
            max_depth: Maximum depth for visualization (None for unlimited)
            
        Returns:
            Complete supply chain visualization
        """
        start_time = datetime.now()
        
        try:
            # Step 1: Get transparency data
            transparency_result = self._get_transparency_data(po_id, max_depth)
            
            # Step 2: Build visualization graph
            nodes, edges = self._build_visualization_graph(transparency_result)
            
            # Step 3: Apply visual styling
            self._apply_visual_styling(nodes, edges, transparency_result)
            
            # Step 4: Perform gap analysis if requested
            gap_analysis = None
            if include_gap_analysis:
                gap_analysis = self._perform_gap_analysis(transparency_result)
            
            # Step 5: Create final visualization
            visualization = self._create_visualization_result(
                po_id, nodes, edges, gap_analysis, transparency_result
            )
            
            # Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            visualization.calculation_time_ms = int(processing_time)
            
            logger.info(
                f"Generated visualization for PO {po_id}: "
                f"{len(nodes)} nodes, {len(edges)} edges, "
                f"{processing_time:.1f}ms"
            )
            
            return visualization
            
        except Exception as e:
            logger.error(f"Failed to generate visualization for PO {po_id}: {str(e)}")
            raise
    
    def _get_transparency_data(
        self, 
        po_id: UUID, 
        max_depth: Optional[int]
    ) -> TransparencyResult:
        """Get transparency calculation data."""
        return self.transparency_engine.calculate_transparency_for_po(
            po_id, max_depth=max_depth
        )
    
    def _build_visualization_graph(
        self, 
        transparency_result: TransparencyResult
    ) -> tuple[List[VisualizationNode], List[VisualizationEdge]]:
        """Build visualization nodes and edges from transparency data."""
        nodes = []
        edges = []
        
        # Create nodes from transparency data
        for node_detail in transparency_result.node_details:
            node = self._create_visualization_node(node_detail)
            nodes.append(node)
        
        # Create edges from material flows
        for node_detail in transparency_result.node_details:
            for input_material in node_detail.input_materials or []:
                edge = self._create_visualization_edge(node_detail, input_material)
                edges.append(edge)
        
        return nodes, edges
    
    def _create_visualization_node(self, node_detail) -> VisualizationNode:
        """Create a visualization node from transparency data."""
        return VisualizationNode(
            id=str(node_detail.po_id),
            po_id=node_detail.po_id,
            po_number=node_detail.po_number,
            company_id=node_detail.company_id,
            company_name=node_detail.company_name,
            company_type=node_detail.company_type,
            product_name=node_detail.product_name,
            quantity=node_detail.quantity,
            unit=node_detail.unit,
            level=node_detail.level,
            ttm_score=node_detail.ttm_score,
            ttp_score=node_detail.ttp_score,
            confidence_level=node_detail.confidence_level,
            traced_percentage=self._calculate_traced_percentage(node_detail),
            has_origin_data=bool(node_detail.origin_data),
            has_geographic_coordinates=bool(getattr(node_detail, 'geographic_coordinates', None)),
            has_certifications=bool(node_detail.certifications),
            missing_data_fields=self._identify_missing_data_fields(node_detail)
        )
    
    def _create_visualization_edge(self, node_detail, input_material: Dict[str, Any]) -> VisualizationEdge:
        """Create a visualization edge from input material data."""
        return VisualizationEdge(
            id=f"{input_material['source_po_id']}_{node_detail.po_id}",
            source_node_id=str(input_material['source_po_id']),
            target_node_id=str(node_detail.po_id),
            relationship_type="input_material",
            quantity_flow=input_material.get('quantity_used', 0.0),
            unit=input_material.get('unit', ''),
            transparency_flow=input_material.get('transparency_flow', 0.0),
            confidence_flow=input_material.get('confidence_flow', 0.0),
            is_missing_link=input_material.get('is_missing_link', False),
            is_weak_link=input_material.get('is_weak_link', False)
        )
    
    def _apply_visual_styling(
        self, 
        nodes: List[VisualizationNode], 
        edges: List[VisualizationEdge],
        transparency_result: TransparencyResult
    ) -> None:
        """Apply visual styling to nodes and edges."""
        # Create lookup for node details
        node_details_map = {
            node_detail.po_id: node_detail 
            for node_detail in transparency_result.node_details
        }
        
        # Style nodes
        for node in nodes:
            node_detail = node_details_map.get(node.po_id)
            if node_detail:
                self.styling_engine.apply_node_styling(node, node_detail)
        
        # Style edges
        for edge in edges:
            # Find corresponding input material data
            source_node_detail = node_details_map.get(UUID(edge.source_node_id))
            if source_node_detail:
                input_material = self._find_input_material(
                    source_node_detail, UUID(edge.target_node_id)
                )
                if input_material:
                    self.styling_engine.apply_edge_styling(edge, input_material)
    
    def _perform_gap_analysis(self, transparency_result: TransparencyResult) -> GapAnalysisResult:
        """Perform gap analysis using the gap analyzer."""
        # Analyze gaps
        gap_analyses = self.gap_analyzer.analyze_transparency_gaps(
            transparency_result.node_details
        )
        
        # Generate recommendations
        recommendations = self.recommendation_engine.generate_recommendations(gap_analyses)
        
        # Create gap analysis result
        return GapAnalysisResult(
            company_id=transparency_result.root_company_id,
            total_gaps=len(gap_analyses),
            critical_gaps=len([g for g in gap_analyses if g.severity.value == "critical"]),
            high_priority_gaps=len([g for g in gap_analyses if g.severity.value == "high"]),
            medium_priority_gaps=len([g for g in gap_analyses if g.severity.value == "medium"]),
            low_priority_gaps=len([g for g in gap_analyses if g.severity.value == "low"]),
            gap_details=[self._gap_analysis_to_dict(g) for g in gap_analyses],
            recommendations=[self._recommendation_to_dict(r) for r in recommendations],
            overall_improvement_potential=sum(g.improvement_potential[0] + g.improvement_potential[1] for g in gap_analyses) / 2,
            ttm_improvement_potential=sum(g.improvement_potential[0] for g in gap_analyses),
            ttp_improvement_potential=sum(g.improvement_potential[1] for g in gap_analyses)
        )
    
    def _create_visualization_result(
        self,
        po_id: UUID,
        nodes: List[VisualizationNode],
        edges: List[VisualizationEdge],
        gap_analysis: Optional[GapAnalysisResult],
        transparency_result: TransparencyResult
    ) -> SupplyChainVisualization:
        """Create the final visualization result."""
        return SupplyChainVisualization(
            root_po_id=po_id,
            nodes=nodes,
            edges=edges,
            total_nodes=len(nodes),
            total_edges=len(edges),
            overall_transparency_score=transparency_result.overall_transparency_score,
            traced_percentage=transparency_result.traced_percentage,
            gap_analysis=gap_analysis,
            layout_type="hierarchical",
            max_depth=max(node.level for node in nodes) if nodes else 0,
            max_width=self._calculate_max_width(nodes),
            generated_at=datetime.now().isoformat()
        )
    
    def _calculate_traced_percentage(self, node_detail) -> float:
        """Calculate traced percentage for a node."""
        if not node_detail.input_materials:
            return 0.0
        
        total_quantity = node_detail.quantity
        traced_quantity = sum(
            material.get('quantity_used', 0) 
            for material in node_detail.input_materials
        )
        
        return min(traced_quantity / total_quantity, 1.0) if total_quantity > 0 else 0.0
    
    def _identify_missing_data_fields(self, node_detail) -> List[str]:
        """Identify missing data fields for a node."""
        missing_fields = []
        
        if not node_detail.origin_data:
            missing_fields.append("origin_data")
        
        if not node_detail.input_materials:
            missing_fields.append("input_materials")
        
        if not node_detail.certifications:
            missing_fields.append("certifications")
        
        if not getattr(node_detail, 'geographic_coordinates', None):
            missing_fields.append("geographic_coordinates")
        
        return missing_fields
    
    def _find_input_material(self, source_node_detail, target_po_id: UUID) -> Optional[Dict[str, Any]]:
        """Find input material data for a specific target PO."""
        for input_material in source_node_detail.input_materials or []:
            if input_material.get('source_po_id') == target_po_id:
                return input_material
        return None
    
    def _calculate_max_width(self, nodes: List[VisualizationNode]) -> int:
        """Calculate maximum width of the visualization."""
        if not nodes:
            return 0
        
        level_counts = {}
        for node in nodes:
            level_counts[node.level] = level_counts.get(node.level, 0) + 1
        
        return max(level_counts.values()) if level_counts else 0
    
    def _gap_analysis_to_dict(self, gap_analysis) -> Dict[str, Any]:
        """Convert gap analysis to dictionary."""
        return {
            "gap_id": gap_analysis.gap_id,
            "node_id": gap_analysis.node_id,
            "gap_type": gap_analysis.gap_type.value,
            "severity": gap_analysis.severity.value,
            "description": gap_analysis.description,
            "impact_score": gap_analysis.impact_score,
            "improvement_potential": gap_analysis.improvement_potential,
            "affected_metrics": gap_analysis.affected_metrics,
            "suggested_actions": gap_analysis.suggested_actions
        }
    
    def _recommendation_to_dict(self, recommendation) -> Dict[str, Any]:
        """Convert recommendation to dictionary."""
        return {
            "recommendation_id": recommendation.recommendation_id,
            "category": recommendation.category,
            "priority": recommendation.priority.value,
            "title": recommendation.title,
            "description": recommendation.description,
            "expected_ttm_impact": recommendation.expected_ttm_impact,
            "expected_ttp_impact": recommendation.expected_ttp_impact,
            "implementation_effort": recommendation.implementation_effort,
            "timeline": recommendation.timeline,
            "actions": recommendation.actions,
            "affected_gaps": recommendation.affected_gaps,
            "success_metrics": recommendation.success_metrics
        }

