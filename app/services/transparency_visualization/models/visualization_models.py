"""
Core visualization models for supply chain transparency.
"""
from typing import List, Dict, Any, Optional
from uuid import UUID
from dataclasses import dataclass, field


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
    
    # Gap details
    gap_details: List[Dict[str, Any]] = field(default_factory=list)
    
    # Improvement metrics
    overall_improvement_potential: float = 0.0
    ttm_improvement_potential: float = 0.0
    ttp_improvement_potential: float = 0.0
    
    # Recommendations
    recommendations: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class SupplyChainVisualization:
    """Complete supply chain visualization result."""
    root_po_id: UUID
    nodes: List[VisualizationNode]
    edges: List[VisualizationEdge]
    
    # Overall metrics
    total_nodes: int
    total_edges: int
    overall_transparency_score: float
    traced_percentage: float
    
    # Gap analysis
    gap_analysis: Optional[GapAnalysisResult] = None
    
    # Layout information
    layout_type: str = "hierarchical"
    max_depth: int = 0
    max_width: int = 0
    
    # Metadata
    generated_at: str = ""
    calculation_time_ms: int = 0

