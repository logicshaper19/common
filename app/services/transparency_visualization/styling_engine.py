"""
Visual styling engine for transparency visualizations.

This service handles all visual styling logic, making it easy to:
- Change color schemes without touching business logic
- A/B test different visual approaches
- Maintain consistent styling across the application
"""
from typing import Dict, Any, Tuple
from sqlalchemy.orm import Session

from app.services.transparency_engine.domain.models import TransparencyNode
from app.core.logging import get_logger
from .models.visualization_models import VisualizationNode, VisualizationEdge

logger = get_logger(__name__)


class VisualizationStylingEngine:
    """
    Handles visual styling and theming for transparency visualizations.
    
    This service is responsible for:
    - Node color and size calculations
    - Edge styling based on transparency flow
    - Gap highlighting and visual indicators
    - Consistent theming across visualizations
    """
    
    def __init__(self, db: Session):
        self.db = db
        
        # Color schemes
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
        
        self.TRANSPARENCY_COLORS = {
            "excellent": "#4CAF50",      # Green (0.9+)
            "good": "#8BC34A",          # Light Green (0.7-0.9)
            "fair": "#FFC107",          # Amber (0.5-0.7)
            "poor": "#FF9800",          # Orange (0.3-0.5)
            "critical": "#F44336"       # Red (<0.3)
        }
        
        # Size configurations
        self.NODE_SIZE_RANGES = {
            "min": 30,
            "max": 100,
            "default": 50
        }
        
        self.EDGE_WIDTH_RANGES = {
            "min": 1,
            "max": 8,
            "default": 2
        }
    
    def apply_node_styling(self, node: VisualizationNode, node_detail: TransparencyNode) -> None:
        """
        Apply visual styling to a visualization node.
        
        Args:
            node: Visualization node to style
            node_detail: Source transparency node data
        """
        # Set node color based on company type and transparency
        node.node_color = self._get_node_color(node_detail)
        
        # Set node size based on quantity and importance
        node.node_size = self._get_node_size(node_detail)
        
        # Set border styling
        node.border_color = self._get_border_color(node_detail)
        node.border_width = self._get_border_width(node_detail)
        
        # Apply gap highlighting if applicable
        if node.is_gap:
            self._apply_gap_highlighting(node)
    
    def apply_edge_styling(self, edge: VisualizationEdge, input_material: Dict[str, Any]) -> None:
        """
        Apply visual styling to a visualization edge.
        
        Args:
            edge: Visualization edge to style
            input_material: Source input material data
        """
        # Set edge color based on transparency flow
        edge.edge_color = self._get_edge_color(input_material)
        
        # Set edge width based on quantity flow
        edge.edge_width = self._get_edge_width(input_material)
        
        # Set edge style based on confidence
        edge.edge_style = self._get_edge_style(input_material)
    
    def _get_node_color(self, node_detail: TransparencyNode) -> str:
        """Get node color based on company type and transparency score."""
        # Base color from company type
        base_color = self.NODE_COLORS.get(node_detail.company_type, self.NODE_COLORS["unknown"])
        
        # If transparency is very low, use gap color
        min_transparency = min(node_detail.ttm_score, node_detail.ttp_score)
        if min_transparency < 0.3:
            return self.GAP_COLORS["critical"]
        elif min_transparency < 0.5:
            return self.GAP_COLORS["high"]
        
        return base_color
    
    def _get_node_size(self, node_detail: TransparencyNode) -> int:
        """Get node size based on quantity and importance."""
        # Base size from quantity (normalized)
        quantity_factor = min(node_detail.quantity / 1000.0, 1.0)
        size_range = self.NODE_SIZE_RANGES["max"] - self.NODE_SIZE_RANGES["min"]
        base_size = self.NODE_SIZE_RANGES["min"] + (quantity_factor * size_range)
        
        # Adjust for transparency importance
        transparency_factor = (node_detail.ttm_score + node_detail.ttp_score) / 2.0
        size_multiplier = 0.7 + (transparency_factor * 0.3)  # 0.7 to 1.0
        
        return int(base_size * size_multiplier)
    
    def _get_border_color(self, node_detail: TransparencyNode) -> str:
        """Get border color based on confidence level."""
        if node_detail.confidence_level >= 0.8:
            return "#4CAF50"  # Green for high confidence
        elif node_detail.confidence_level >= 0.6:
            return "#FFC107"  # Amber for medium confidence
        else:
            return "#F44336"  # Red for low confidence
    
    def _get_border_width(self, node_detail: TransparencyNode) -> int:
        """Get border width based on data completeness."""
        completeness_score = self._calculate_data_completeness(node_detail)
        
        if completeness_score >= 0.8:
            return 2  # Normal border
        elif completeness_score >= 0.6:
            return 3  # Thicker border for attention
        else:
            return 4  # Very thick border for critical issues
    
    def _get_edge_color(self, input_material: Dict[str, Any]) -> str:
        """Get edge color based on transparency flow."""
        transparency_flow = input_material.get("transparency_flow", 0.0)
        
        if transparency_flow >= 0.8:
            return self.TRANSPARENCY_COLORS["excellent"]
        elif transparency_flow >= 0.6:
            return self.TRANSPARENCY_COLORS["good"]
        elif transparency_flow >= 0.4:
            return self.TRANSPARENCY_COLORS["fair"]
        elif transparency_flow >= 0.2:
            return self.TRANSPARENCY_COLORS["poor"]
        else:
            return self.TRANSPARENCY_COLORS["critical"]
    
    def _get_edge_width(self, input_material: Dict[str, Any]) -> int:
        """Get edge width based on quantity flow."""
        quantity_flow = input_material.get("quantity_flow", 0.0)
        
        # Normalize quantity to width range
        if quantity_flow <= 0:
            return self.EDGE_WIDTH_RANGES["min"]
        
        # Use logarithmic scaling for better visual distribution
        import math
        log_quantity = math.log10(max(quantity_flow, 1))
        max_log = 4  # Assume max quantity is 10^4
        
        normalized = min(log_quantity / max_log, 1.0)
        width_range = self.EDGE_WIDTH_RANGES["max"] - self.EDGE_WIDTH_RANGES["min"]
        
        return int(self.EDGE_WIDTH_RANGES["min"] + (normalized * width_range))
    
    def _get_edge_style(self, input_material: Dict[str, Any]) -> str:
        """Get edge style based on confidence and data quality."""
        confidence = input_material.get("confidence_flow", 0.0)
        is_verified = input_material.get("is_verified", False)
        
        if confidence >= 0.8 and is_verified:
            return "solid"
        elif confidence >= 0.6:
            return "dashed"
        else:
            return "dotted"
    
    def _apply_gap_highlighting(self, node: VisualizationNode) -> None:
        """Apply special highlighting for nodes with gaps."""
        if node.gap_severity == "critical":
            node.node_color = self.GAP_COLORS["critical"]
            node.border_color = "#D32F2F"  # Darker red
            node.border_width = 4
        elif node.gap_severity == "high":
            node.node_color = self.GAP_COLORS["high"]
            node.border_color = "#E64A19"  # Darker orange
            node.border_width = 3
        elif node.gap_severity == "medium":
            node.node_color = self.GAP_COLORS["medium"]
            node.border_color = "#F57C00"  # Darker amber
            node.border_width = 3
        else:  # low
            node.node_color = self.GAP_COLORS["low"]
            node.border_color = "#FFA000"  # Darker yellow
            node.border_width = 2
    
    def _calculate_data_completeness(self, node_detail: TransparencyNode) -> float:
        """Calculate data completeness score for a node."""
        completeness_factors = []
        
        # Check for origin data
        if hasattr(node_detail, 'origin_data') and node_detail.origin_data:
            completeness_factors.append(1.0)
        else:
            completeness_factors.append(0.0)
        
        # Check for input materials
        if hasattr(node_detail, 'input_materials') and node_detail.input_materials:
            completeness_factors.append(1.0)
        else:
            completeness_factors.append(0.0)
        
        # Check for certifications
        if hasattr(node_detail, 'certifications') and node_detail.certifications:
            completeness_factors.append(1.0)
        else:
            completeness_factors.append(0.0)
        
        # Check for geographic data
        if hasattr(node_detail, 'geographic_coordinates') and node_detail.geographic_coordinates:
            completeness_factors.append(1.0)
        else:
            completeness_factors.append(0.0)
        
        # Check confidence level
        completeness_factors.append(node_detail.confidence_level)
        
        return sum(completeness_factors) / len(completeness_factors)
    
    def get_color_for_transparency_score(self, score: float) -> str:
        """Get color for a given transparency score."""
        if score >= 0.9:
            return self.TRANSPARENCY_COLORS["excellent"]
        elif score >= 0.7:
            return self.TRANSPARENCY_COLORS["good"]
        elif score >= 0.5:
            return self.TRANSPARENCY_COLORS["fair"]
        elif score >= 0.3:
            return self.TRANSPARENCY_COLORS["poor"]
        else:
            return self.TRANSPARENCY_COLORS["critical"]
    
    def get_size_for_quantity(self, quantity: float, max_quantity: float = 1000.0) -> int:
        """Get node size for a given quantity."""
        if quantity <= 0:
            return self.NODE_SIZE_RANGES["min"]
        
        # Normalize quantity
        normalized = min(quantity / max_quantity, 1.0)
        
        # Calculate size
        size_range = self.NODE_SIZE_RANGES["max"] - self.NODE_SIZE_RANGES["min"]
        return int(self.NODE_SIZE_RANGES["min"] + (normalized * size_range))

