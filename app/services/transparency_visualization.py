"""
Transparency visualization and gap analysis service for the Common supply chain platform.
"""
from typing import Optional, List, Dict, Any, Set, Tuple
from uuid import UUID
from datetime import datetime
from decimal import Decimal
from dataclasses import dataclass, field
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func

from app.models.purchase_order import PurchaseOrder
from app.models.company import Company
from app.models.product import Product
from app.services.transparency_engine import TransparencyCalculationEngine, TransparencyResult, TransparencyNode
from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class VisualizationNode:
    """Node for supply chain visualization."""
    id: str
    po_id: UUID
    po_number: str
    company_id: UUID
    company_name: str
    company_type: str
    product_name: str
    quantity: float
    unit: str
    
    # Position and layout
    level: int
    position_x: float = 0.0
    position_y: float = 0.0
    
    # Transparency metrics
    ttm_score: float = 0.0
    ttp_score: float = 0.0
    confidence_level: float = 0.0
    traced_percentage: float = 0.0
    
    # Visual properties
    node_color: str = "#cccccc"
    node_size: int = 50
    border_color: str = "#666666"
    border_width: int = 2
    
    # Data completeness
    has_origin_data: bool = False
    has_geographic_coordinates: bool = False
    has_certifications: bool = False
    missing_data_fields: List[str] = field(default_factory=list)
    
    # Gap analysis
    is_gap: bool = False
    gap_type: str = ""
    gap_severity: str = ""  # "low", "medium", "high", "critical"
    improvement_potential: float = 0.0


@dataclass
class VisualizationEdge:
    """Edge for supply chain visualization."""
    id: str
    source_node_id: str
    target_node_id: str
    
    # Relationship properties
    relationship_type: str = "input_material"
    quantity_flow: float = 0.0
    unit: str = ""
    
    # Visual properties
    edge_color: str = "#999999"
    edge_width: int = 2
    edge_style: str = "solid"  # "solid", "dashed", "dotted"
    
    # Transparency flow
    transparency_flow: float = 0.0
    confidence_flow: float = 0.0
    
    # Gap indicators
    is_missing_link: bool = False
    is_weak_link: bool = False
    improvement_priority: str = "low"


@dataclass
class GapAnalysisResult:
    """Result of gap analysis for transparency improvement."""
    company_id: UUID
    total_gaps: int
    critical_gaps: int
    high_priority_gaps: int
    medium_priority_gaps: int
    low_priority_gaps: int
    
    # Gap categories
    missing_origin_data_gaps: int = 0
    missing_input_material_gaps: int = 0
    missing_certification_gaps: int = 0
    missing_geographic_data_gaps: int = 0
    unconfirmed_po_gaps: int = 0
    
    # Improvement potential
    current_ttm_score: float = 0.0
    current_ttp_score: float = 0.0
    potential_ttm_score: float = 0.0
    potential_ttp_score: float = 0.0
    
    # Detailed gaps
    gap_details: List[Dict[str, Any]] = field(default_factory=list)
    improvement_recommendations: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class SupplyChainVisualization:
    """Complete supply chain visualization data."""
    company_id: UUID
    root_po_id: UUID
    
    # Graph structure
    nodes: List[VisualizationNode] = field(default_factory=list)
    edges: List[VisualizationEdge] = field(default_factory=list)
    
    # Layout properties
    total_levels: int = 0
    max_width: int = 0
    layout_algorithm: str = "hierarchical"
    
    # Transparency metrics
    overall_ttm_score: float = 0.0
    overall_ttp_score: float = 0.0
    overall_confidence: float = 0.0
    traced_percentage: float = 0.0
    untraced_percentage: float = 0.0
    
    # Gap analysis
    gap_analysis: Optional[GapAnalysisResult] = None
    
    # Metadata
    generated_at: datetime = field(default_factory=datetime.utcnow)
    calculation_time_ms: int = 0


class TransparencyVisualizationService:
    """
    Service for generating supply chain visualizations and gap analysis.
    
    Features:
    - Supply chain path visualization generation
    - Gap analysis logic to identify missing traceability links
    - Transparency improvement recommendation engine
    - Partial traceability calculation (traced vs untraced percentages)
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.transparency_engine = TransparencyCalculationEngine(db)
        
        # Visualization configuration
        self.NODE_COLORS = {
            "originator": "#4CAF50",      # Green
            "processor": "#2196F3",       # Blue
            "brand": "#FF9800",           # Orange
            "supplier": "#9C27B0",        # Purple
            "unknown": "#757575"          # Gray
        }
        
        self.GAP_COLORS = {
            "critical": "#F44336",        # Red
            "high": "#FF5722",           # Deep Orange
            "medium": "#FF9800",         # Orange
            "low": "#FFC107"             # Amber
        }
        
        # Gap analysis thresholds
        self.TRANSPARENCY_THRESHOLDS = {
            "critical": 0.3,
            "high": 0.5,
            "medium": 0.7,
            "good": 0.85
        }
    
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
            max_depth: Maximum depth for visualization
            
        Returns:
            Complete supply chain visualization
        """
        start_time = datetime.utcnow()
        
        logger.info(
            "Generating supply chain visualization",
            po_id=str(po_id),
            include_gap_analysis=include_gap_analysis
        )
        
        try:
            # Get transparency calculation result
            transparency_result = self.transparency_engine.calculate_transparency(
                po_id=po_id,
                include_detailed_analysis=True
            )
            
            # Get root PO for company context
            root_po = self.db.query(PurchaseOrder).filter(
                PurchaseOrder.id == po_id
            ).first()
            
            if not root_po:
                raise ValueError(f"Purchase order {po_id} not found")
            
            # Generate visualization nodes and edges
            nodes = self._generate_visualization_nodes(transparency_result)
            edges = self._generate_visualization_edges(transparency_result)
            
            # Apply layout algorithm
            self._apply_hierarchical_layout(nodes, edges)
            
            # Create visualization object
            visualization = SupplyChainVisualization(
                company_id=root_po.buyer_company_id,
                root_po_id=po_id,
                nodes=nodes,
                edges=edges,
                total_levels=max((node.level for node in nodes), default=0) + 1,
                max_width=self._calculate_max_width(nodes),
                overall_ttm_score=transparency_result.ttm_score,
                overall_ttp_score=transparency_result.ttp_score,
                overall_confidence=transparency_result.confidence_level,
                traced_percentage=transparency_result.traced_percentage,
                untraced_percentage=transparency_result.untraced_percentage
            )
            
            # Add gap analysis if requested
            if include_gap_analysis:
                visualization.gap_analysis = self.analyze_transparency_gaps(
                    transparency_result, root_po.buyer_company_id
                )
                
                # Update nodes with gap information
                self._apply_gap_analysis_to_nodes(visualization.nodes, visualization.gap_analysis)
            
            # Calculate generation time
            end_time = datetime.utcnow()
            visualization.calculation_time_ms = int((end_time - start_time).total_seconds() * 1000)
            
            logger.info(
                "Supply chain visualization generated",
                po_id=str(po_id),
                nodes_count=len(nodes),
                edges_count=len(edges),
                calculation_time_ms=visualization.calculation_time_ms
            )
            
            return visualization
            
        except Exception as e:
            logger.error(
                "Failed to generate supply chain visualization",
                po_id=str(po_id),
                error=str(e)
            )
            raise
    
    def analyze_transparency_gaps(
        self,
        transparency_result: TransparencyResult,
        company_id: UUID
    ) -> GapAnalysisResult:
        """
        Analyze transparency gaps and generate improvement recommendations.
        
        Args:
            transparency_result: Transparency calculation result
            company_id: Company ID for context
            
        Returns:
            Comprehensive gap analysis result
        """
        try:
            logger.info(
                "Analyzing transparency gaps",
                company_id=str(company_id),
                ttm_score=transparency_result.ttm_score,
                ttp_score=transparency_result.ttp_score
            )
            
            # Initialize gap counters
            gap_counts = {
                "critical": 0,
                "high": 0,
                "medium": 0,
                "low": 0
            }
            
            category_gaps = {
                "missing_origin_data": 0,
                "missing_input_material": 0,
                "missing_certification": 0,
                "missing_geographic_data": 0,
                "unconfirmed_po": 0,
                "low_transparency": 0
            }
            
            gap_details = []
            
            # Analyze each node for gaps
            for node in transparency_result.node_details:
                node_gaps = self._analyze_node_gaps(node)
                
                for gap in node_gaps:
                    gap_counts[gap["severity"]] += 1
                    category_gaps[gap["category"]] += 1
                    gap_details.append(gap)
            
            # Calculate improvement potential
            potential_ttm, potential_ttp = self._calculate_improvement_potential(
                transparency_result, gap_details
            )
            
            # Generate improvement recommendations
            recommendations = self._generate_improvement_recommendations(
                transparency_result, gap_details
            )
            
            return GapAnalysisResult(
                company_id=company_id,
                total_gaps=sum(gap_counts.values()),
                critical_gaps=gap_counts["critical"],
                high_priority_gaps=gap_counts["high"],
                medium_priority_gaps=gap_counts["medium"],
                low_priority_gaps=gap_counts["low"],
                missing_origin_data_gaps=category_gaps["missing_origin_data"],
                missing_input_material_gaps=category_gaps["missing_input_material"],
                missing_certification_gaps=category_gaps["missing_certification"],
                missing_geographic_data_gaps=category_gaps["missing_geographic_data"],
                unconfirmed_po_gaps=category_gaps["unconfirmed_po"],
                current_ttm_score=transparency_result.ttm_score,
                current_ttp_score=transparency_result.ttp_score,
                potential_ttm_score=potential_ttm,
                potential_ttp_score=potential_ttp,
                gap_details=gap_details,
                improvement_recommendations=recommendations
            )
            
        except Exception as e:
            logger.error(
                "Failed to analyze transparency gaps",
                company_id=str(company_id),
                error=str(e)
            )
            raise

    def _generate_visualization_nodes(
        self,
        transparency_result: TransparencyResult
    ) -> List[VisualizationNode]:
        """Generate visualization nodes from transparency result."""
        nodes = []

        for i, node_detail in enumerate(transparency_result.node_details):
            # Get company information
            company = self.db.query(Company).filter(
                Company.id == node_detail.company_id
            ).first()

            # Get product information
            product = self.db.query(Product).filter(
                Product.id == node_detail.product_id
            ).first()

            # Determine node color based on company type and transparency
            node_color = self._get_node_color(node_detail)
            node_size = self._get_node_size(node_detail)

            # Identify missing data fields
            missing_fields = []
            if not node_detail.has_origin_data:
                missing_fields.append("origin_data")
            if not node_detail.has_geographic_coordinates:
                missing_fields.append("geographic_coordinates")
            if not node_detail.has_certifications:
                missing_fields.append("certifications")
            if not node_detail.input_materials:
                missing_fields.append("input_materials")

            visualization_node = VisualizationNode(
                id=f"node_{i}",
                po_id=node_detail.po_id,
                po_number=node_detail.po_number,
                company_id=node_detail.company_id,
                company_name=company.name if company else "Unknown Company",
                company_type=node_detail.company_type,
                product_name=product.name if product else "Unknown Product",
                quantity=float(node_detail.quantity),
                unit=node_detail.unit,
                level=node_detail.depth,
                ttm_score=node_detail.base_ttm_score,
                ttp_score=node_detail.base_ttp_score,
                confidence_level=node_detail.confidence_level,
                traced_percentage=self._calculate_node_traced_percentage(node_detail),
                node_color=node_color,
                node_size=node_size,
                has_origin_data=node_detail.has_origin_data,
                has_geographic_coordinates=node_detail.has_geographic_coordinates,
                has_certifications=node_detail.has_certifications,
                missing_data_fields=missing_fields
            )

            nodes.append(visualization_node)

        return nodes

    def _generate_visualization_edges(
        self,
        transparency_result: TransparencyResult
    ) -> List[VisualizationEdge]:
        """Generate visualization edges from transparency result."""
        edges = []
        edge_counter = 0

        # Create a mapping of PO IDs to node indices
        po_to_node = {
            node.po_id: i for i, node in enumerate(transparency_result.node_details)
        }

        for i, node_detail in enumerate(transparency_result.node_details):
            for input_material in node_detail.input_materials:
                input_po_id = input_material.get("po_id")
                if input_po_id and input_po_id in po_to_node:
                    source_index = po_to_node[input_po_id]
                    target_index = i

                    # Determine edge properties
                    edge_color = self._get_edge_color(input_material)
                    edge_width = self._get_edge_width(input_material)
                    edge_style = self._get_edge_style(input_material)

                    edge = VisualizationEdge(
                        id=f"edge_{edge_counter}",
                        source_node_id=f"node_{source_index}",
                        target_node_id=f"node_{target_index}",
                        quantity_flow=float(input_material.get("quantity", 0)),
                        unit=input_material.get("unit", ""),
                        edge_color=edge_color,
                        edge_width=edge_width,
                        edge_style=edge_style,
                        transparency_flow=input_material.get("transparency_contribution", 0.0),
                        confidence_flow=input_material.get("confidence_level", 0.0)
                    )

                    edges.append(edge)
                    edge_counter += 1

        return edges

    def _apply_hierarchical_layout(
        self,
        nodes: List[VisualizationNode],
        edges: List[VisualizationEdge]
    ):
        """Apply hierarchical layout algorithm to position nodes."""
        if not nodes:
            return

        # Group nodes by level
        levels = {}
        for node in nodes:
            if node.level not in levels:
                levels[node.level] = []
            levels[node.level].append(node)

        # Position nodes within each level
        level_height = 150
        node_spacing = 120

        for level, level_nodes in levels.items():
            y_position = level * level_height
            total_width = len(level_nodes) * node_spacing
            start_x = -total_width / 2

            for i, node in enumerate(level_nodes):
                node.position_x = start_x + (i * node_spacing)
                node.position_y = y_position

    def _calculate_max_width(self, nodes: List[VisualizationNode]) -> int:
        """Calculate maximum width of the visualization."""
        if not nodes:
            return 0

        levels = {}
        for node in nodes:
            if node.level not in levels:
                levels[node.level] = 0
            levels[node.level] += 1

        return max(levels.values()) if levels else 0

    def _get_node_color(self, node_detail: TransparencyNode) -> str:
        """Get node color based on company type and transparency score."""
        base_color = self.NODE_COLORS.get(node_detail.company_type, self.NODE_COLORS["unknown"])

        # Adjust color intensity based on transparency score
        avg_score = (node_detail.base_ttm_score + node_detail.base_ttp_score) / 2

        if avg_score < self.TRANSPARENCY_THRESHOLDS["critical"]:
            return self.GAP_COLORS["critical"]
        elif avg_score < self.TRANSPARENCY_THRESHOLDS["high"]:
            return self.GAP_COLORS["high"]
        elif avg_score < self.TRANSPARENCY_THRESHOLDS["medium"]:
            return self.GAP_COLORS["medium"]
        else:
            return base_color

    def _get_node_size(self, node_detail: TransparencyNode) -> int:
        """Get node size based on quantity and importance."""
        base_size = 50

        # Scale based on quantity (logarithmic scaling)
        quantity = float(node_detail.quantity) if node_detail.quantity else 1.0
        size_multiplier = min(2.0, max(0.5, (quantity / 1000.0) ** 0.3))

        return int(base_size * size_multiplier)

    def _get_edge_color(self, input_material: Dict[str, Any]) -> str:
        """Get edge color based on transparency flow."""
        transparency = input_material.get("transparency_contribution", 0.0)

        if transparency >= 0.8:
            return "#4CAF50"  # Green - high transparency
        elif transparency >= 0.6:
            return "#FFC107"  # Amber - medium transparency
        elif transparency >= 0.3:
            return "#FF9800"  # Orange - low transparency
        else:
            return "#F44336"  # Red - very low transparency

    def _get_edge_width(self, input_material: Dict[str, Any]) -> int:
        """Get edge width based on quantity flow."""
        quantity = float(input_material.get("quantity", 0))

        if quantity >= 1000:
            return 4
        elif quantity >= 100:
            return 3
        elif quantity >= 10:
            return 2
        else:
            return 1

    def _get_edge_style(self, input_material: Dict[str, Any]) -> str:
        """Get edge style based on confidence level."""
        confidence = input_material.get("confidence_level", 0.0)

        if confidence >= 0.8:
            return "solid"
        elif confidence >= 0.5:
            return "dashed"
        else:
            return "dotted"

    def _calculate_node_traced_percentage(self, node_detail: TransparencyNode) -> float:
        """Calculate traced percentage for a single node."""
        factors = []

        if node_detail.has_origin_data:
            factors.append(1.0)
        if node_detail.has_geographic_coordinates:
            factors.append(1.0)
        if node_detail.has_certifications:
            factors.append(1.0)
        if node_detail.input_materials:
            factors.append(1.0)

        if not factors:
            return 0.0

        return (sum(factors) / 4.0) * 100.0

    def _apply_gap_analysis_to_nodes(
        self,
        nodes: List[VisualizationNode],
        gap_analysis: GapAnalysisResult
    ):
        """Apply gap analysis results to visualization nodes."""
        # Create a mapping of PO IDs to gap details
        po_gaps = {}
        for gap in gap_analysis.gap_details:
            po_id = gap.get("po_id")
            if po_id:
                if po_id not in po_gaps:
                    po_gaps[po_id] = []
                po_gaps[po_id].append(gap)

        # Update nodes with gap information
        for node in nodes:
            node_gaps = po_gaps.get(str(node.po_id), [])

            if node_gaps:
                # Find highest severity gap
                severities = ["critical", "high", "medium", "low"]
                highest_severity = "low"

                for gap in node_gaps:
                    gap_severity = gap.get("severity", "low")
                    if severities.index(gap_severity) < severities.index(highest_severity):
                        highest_severity = gap_severity

                node.is_gap = True
                node.gap_severity = highest_severity
                node.gap_type = node_gaps[0].get("category", "unknown")
                node.improvement_potential = sum(gap.get("impact", 0.0) for gap in node_gaps)

                # Update node color to reflect gap severity
                node.node_color = self.GAP_COLORS[highest_severity]
                node.border_color = self.GAP_COLORS[highest_severity]
                node.border_width = 3

    def _analyze_node_gaps(self, node: TransparencyNode) -> List[Dict[str, Any]]:
        """Analyze gaps for a single transparency node."""
        gaps = []

        # Check for missing origin data
        if not node.has_origin_data:
            severity = self._determine_gap_severity(node, "origin_data")
            gaps.append({
                "po_id": str(node.po_id),
                "category": "missing_origin_data",
                "severity": severity,
                "description": f"Missing origin data for {node.po_number}",
                "impact": self._calculate_gap_impact(node, "origin_data"),
                "recommendation": "Add origin data including harvest date, farm identification, and geographic coordinates"
            })

        # Check for missing geographic coordinates
        if not node.has_geographic_coordinates:
            severity = self._determine_gap_severity(node, "geographic_coordinates")
            gaps.append({
                "po_id": str(node.po_id),
                "category": "missing_geographic_data",
                "severity": severity,
                "description": f"Missing geographic coordinates for {node.po_number}",
                "impact": self._calculate_gap_impact(node, "geographic_coordinates"),
                "recommendation": "Add latitude and longitude coordinates for the production location"
            })

        # Check for missing certifications
        if not node.has_certifications:
            severity = self._determine_gap_severity(node, "certifications")
            gaps.append({
                "po_id": str(node.po_id),
                "category": "missing_certification",
                "severity": severity,
                "description": f"Missing certifications for {node.po_number}",
                "impact": self._calculate_gap_impact(node, "certifications"),
                "recommendation": "Add relevant certifications (RSPO, NDPE, etc.) to improve transparency"
            })

        # Check for missing input materials
        if not node.input_materials and node.company_type in ["processor", "brand"]:
            severity = self._determine_gap_severity(node, "input_materials")
            gaps.append({
                "po_id": str(node.po_id),
                "category": "missing_input_material",
                "severity": severity,
                "description": f"Missing input material links for {node.po_number}",
                "impact": self._calculate_gap_impact(node, "input_materials"),
                "recommendation": "Link input materials to establish supply chain traceability"
            })

        # Check for low transparency scores
        avg_score = (node.base_ttm_score + node.base_ttp_score) / 2
        if avg_score < self.TRANSPARENCY_THRESHOLDS["medium"]:
            severity = "high" if avg_score < self.TRANSPARENCY_THRESHOLDS["critical"] else "medium"
            gaps.append({
                "po_id": str(node.po_id),
                "category": "low_transparency",
                "severity": severity,
                "description": f"Low transparency score ({avg_score:.2f}) for {node.po_number}",
                "impact": 1.0 - avg_score,
                "recommendation": "Improve data completeness and add missing transparency information"
            })

        return gaps

    def _determine_gap_severity(self, node: TransparencyNode, gap_type: str) -> str:
        """Determine the severity of a gap based on node context."""
        # Base severity on company type and position in supply chain
        if node.company_type == "originator":
            # Originators are critical for transparency
            if gap_type in ["origin_data", "geographic_coordinates"]:
                return "critical"
            else:
                return "high"
        elif node.company_type == "processor":
            # Processors are important for traceability
            if gap_type == "input_materials":
                return "high"
            else:
                return "medium"
        else:
            # Other company types
            return "medium" if gap_type in ["origin_data", "input_materials"] else "low"

    def _calculate_gap_impact(self, node: TransparencyNode, gap_type: str) -> float:
        """Calculate the potential impact of fixing a gap."""
        # Impact weights by gap type
        impact_weights = {
            "origin_data": 0.3,
            "geographic_coordinates": 0.25,
            "certifications": 0.2,
            "input_materials": 0.35
        }

        base_impact = impact_weights.get(gap_type, 0.1)

        # Adjust impact based on company type
        if node.company_type == "originator":
            base_impact *= 1.5
        elif node.company_type == "processor":
            base_impact *= 1.2

        # Adjust impact based on current transparency level
        avg_score = (node.base_ttm_score + node.base_ttp_score) / 2
        if avg_score < 0.3:
            base_impact *= 1.3
        elif avg_score < 0.5:
            base_impact *= 1.1

        return min(base_impact, 1.0)

    def _calculate_improvement_potential(
        self,
        transparency_result: TransparencyResult,
        gap_details: List[Dict[str, Any]]
    ) -> Tuple[float, float]:
        """Calculate potential TTM and TTP scores after gap improvements."""
        current_ttm = transparency_result.ttm_score
        current_ttp = transparency_result.ttp_score

        # Calculate potential improvement from fixing gaps
        ttm_improvement = 0.0
        ttp_improvement = 0.0

        for gap in gap_details:
            impact = gap.get("impact", 0.0)
            category = gap.get("category", "")

            # Different gap types affect TTM and TTP differently
            if category in ["missing_origin_data", "missing_geographic_data"]:
                ttp_improvement += impact * 0.8
                ttm_improvement += impact * 0.4
            elif category == "missing_certification":
                ttp_improvement += impact * 0.6
                ttm_improvement += impact * 0.3
            elif category == "missing_input_material":
                ttm_improvement += impact * 0.7
                ttp_improvement += impact * 0.5
            else:
                ttm_improvement += impact * 0.5
                ttp_improvement += impact * 0.5

        # Apply diminishing returns
        ttm_improvement = ttm_improvement * 0.7  # 70% efficiency
        ttp_improvement = ttp_improvement * 0.7  # 70% efficiency

        potential_ttm = min(current_ttm + ttm_improvement, 1.0)
        potential_ttp = min(current_ttp + ttp_improvement, 1.0)

        return potential_ttm, potential_ttp

    def _generate_improvement_recommendations(
        self,
        transparency_result: TransparencyResult,
        gap_details: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Generate actionable improvement recommendations."""
        recommendations = []

        # Group gaps by category
        gap_categories = {}
        for gap in gap_details:
            category = gap.get("category", "unknown")
            if category not in gap_categories:
                gap_categories[category] = []
            gap_categories[category].append(gap)

        # Generate recommendations for each category
        for category, gaps in gap_categories.items():
            if category == "missing_origin_data":
                recommendations.append({
                    "category": "origin_data",
                    "priority": "high",
                    "title": "Add Origin Data",
                    "description": f"Add origin data for {len(gaps)} purchase orders to improve plantation-level transparency",
                    "expected_ttm_impact": sum(gap.get("impact", 0) * 0.4 for gap in gaps),
                    "expected_ttp_impact": sum(gap.get("impact", 0) * 0.8 for gap in gaps),
                    "implementation_effort": "medium",
                    "timeline": "2-4 weeks",
                    "actions": [
                        "Contact suppliers to provide harvest dates",
                        "Collect farm identification information",
                        "Verify geographic coordinates",
                        "Update purchase order records"
                    ]
                })

            elif category == "missing_input_material":
                recommendations.append({
                    "category": "input_materials",
                    "priority": "high",
                    "title": "Link Input Materials",
                    "description": f"Link input materials for {len(gaps)} purchase orders to establish supply chain traceability",
                    "expected_ttm_impact": sum(gap.get("impact", 0) * 0.7 for gap in gaps),
                    "expected_ttp_impact": sum(gap.get("impact", 0) * 0.5 for gap in gaps),
                    "implementation_effort": "high",
                    "timeline": "4-8 weeks",
                    "actions": [
                        "Identify input material sources",
                        "Establish supplier relationships",
                        "Create purchase order linkages",
                        "Verify material composition data"
                    ]
                })

            elif category == "missing_certification":
                recommendations.append({
                    "category": "certifications",
                    "priority": "medium",
                    "title": "Add Certifications",
                    "description": f"Add certifications for {len(gaps)} purchase orders to improve credibility",
                    "expected_ttm_impact": sum(gap.get("impact", 0) * 0.3 for gap in gaps),
                    "expected_ttp_impact": sum(gap.get("impact", 0) * 0.6 for gap in gaps),
                    "implementation_effort": "low",
                    "timeline": "1-2 weeks",
                    "actions": [
                        "Collect certification documents",
                        "Verify certification validity",
                        "Upload certification records",
                        "Link certifications to purchase orders"
                    ]
                })

            elif category == "missing_geographic_data":
                recommendations.append({
                    "category": "geographic_data",
                    "priority": "medium",
                    "title": "Add Geographic Coordinates",
                    "description": f"Add geographic coordinates for {len(gaps)} purchase orders",
                    "expected_ttm_impact": sum(gap.get("impact", 0) * 0.4 for gap in gaps),
                    "expected_ttp_impact": sum(gap.get("impact", 0) * 0.8 for gap in gaps),
                    "implementation_effort": "low",
                    "timeline": "1-2 weeks",
                    "actions": [
                        "Collect GPS coordinates from suppliers",
                        "Verify location accuracy",
                        "Update purchase order records",
                        "Validate geographic boundaries"
                    ]
                })

        # Add strategic recommendations based on overall transparency
        if transparency_result.ttm_score < 0.5:
            recommendations.append({
                "category": "strategic",
                "priority": "high",
                "title": "Improve Mill-Level Transparency",
                "description": "Focus on improving transparency to mill (TTM) through better input material tracking",
                "expected_ttm_impact": 0.3,
                "expected_ttp_impact": 0.1,
                "implementation_effort": "high",
                "timeline": "3-6 months",
                "actions": [
                    "Implement supplier onboarding program",
                    "Establish input material tracking systems",
                    "Create supplier transparency requirements",
                    "Regular transparency audits"
                ]
            })

        if transparency_result.ttp_score < 0.5:
            recommendations.append({
                "category": "strategic",
                "priority": "high",
                "title": "Improve Plantation-Level Transparency",
                "description": "Focus on improving transparency to plantation (TTP) through origin data collection",
                "expected_ttm_impact": 0.1,
                "expected_ttp_impact": 0.4,
                "implementation_effort": "high",
                "timeline": "3-6 months",
                "actions": [
                    "Establish direct relationships with originators",
                    "Implement origin data collection systems",
                    "Create plantation mapping programs",
                    "Regular origin verification audits"
                ]
            })

        # Sort recommendations by priority and impact
        priority_order = {"high": 0, "medium": 1, "low": 2}
        recommendations.sort(
            key=lambda x: (
                priority_order.get(x.get("priority", "low"), 2),
                -(x.get("expected_ttm_impact", 0) + x.get("expected_ttp_impact", 0))
            )
        )

        return recommendations
