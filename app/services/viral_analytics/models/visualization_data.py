"""
Data classes for visualization data structures.

This module contains structured data classes for preparing data for
viral analytics visualizations and dashboards.
"""

from dataclasses import dataclass
from typing import Dict, List, Any, Optional
from datetime import datetime
from .enums import OnboardingStage, CascadeNodeType


@dataclass
class OnboardingChainNode:
    """Single node in an onboarding chain visualization."""
    
    node_id: str
    company_name: str
    company_id: int
    
    # Position in chain
    level: int
    parent_id: Optional[str]
    children_ids: List[str]
    
    # Onboarding data
    current_stage: OnboardingStage
    stage_completion_percentage: float
    invitation_date: datetime
    acceptance_date: Optional[datetime]
    completion_date: Optional[datetime]
    
    # Metrics
    invitations_sent: int
    invitations_accepted: int
    conversion_rate: float
    
    # Visual properties
    node_type: CascadeNodeType
    is_viral_champion: bool
    performance_score: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.node_id,
            "company_name": self.company_name,
            "company_id": self.company_id,
            "level": self.level,
            "parent_id": self.parent_id,
            "children_ids": self.children_ids,
            "current_stage": self.current_stage.value,
            "stage_completion": self.stage_completion_percentage,
            "invitation_date": self.invitation_date.isoformat(),
            "acceptance_date": self.acceptance_date.isoformat() if self.acceptance_date else None,
            "completion_date": self.completion_date.isoformat() if self.completion_date else None,
            "invitations_sent": self.invitations_sent,
            "invitations_accepted": self.invitations_accepted,
            "conversion_rate": self.conversion_rate,
            "node_type": self.node_type.value,
            "is_viral_champion": self.is_viral_champion,
            "performance_score": self.performance_score
        }


@dataclass
class OnboardingChainVisualization:
    """Complete onboarding chain visualization data."""
    
    root_company_id: int
    root_company_name: str
    
    # Chain structure
    nodes: List[OnboardingChainNode]
    total_levels: int
    total_nodes: int
    
    # Chain metrics
    chain_viral_coefficient: float
    chain_conversion_rate: float
    chain_completion_rate: float
    
    # Visual layout data
    level_widths: Dict[int, int]  # Number of nodes per level
    max_width: int
    
    # Metadata
    generation_timestamp: datetime
    timeframe_days: int
    
    def get_nodes_by_level(self) -> Dict[int, List[OnboardingChainNode]]:
        """Group nodes by their level in the chain."""
        nodes_by_level = {}
        
        for node in self.nodes:
            level = node.level
            if level not in nodes_by_level:
                nodes_by_level[level] = []
            nodes_by_level[level].append(node)
        
        return nodes_by_level
    
    def get_viral_champions(self) -> List[OnboardingChainNode]:
        """Get all viral champion nodes in the chain."""
        return [node for node in self.nodes if node.is_viral_champion]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "root_company_id": self.root_company_id,
            "root_company_name": self.root_company_name,
            "nodes": [node.to_dict() for node in self.nodes],
            "total_levels": self.total_levels,
            "total_nodes": self.total_nodes,
            "chain_viral_coefficient": self.chain_viral_coefficient,
            "chain_conversion_rate": self.chain_conversion_rate,
            "chain_completion_rate": self.chain_completion_rate,
            "level_widths": self.level_widths,
            "max_width": self.max_width,
            "generation_timestamp": self.generation_timestamp.isoformat(),
            "timeframe_days": self.timeframe_days
        }


@dataclass
class NetworkGraphNode:
    """Node in network graph visualization."""
    
    id: str
    label: str
    company_id: int
    
    # Visual properties
    size: float  # Based on network influence
    color: str   # Based on performance tier
    shape: str   # Based on node type
    
    # Metrics for tooltips
    invitations_sent: int
    invitations_accepted: int
    viral_coefficient: float
    performance_score: float
    
    # Position (if pre-calculated)
    x: Optional[float] = None
    y: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for graph visualization."""
        return {
            "id": self.id,
            "label": self.label,
            "company_id": self.company_id,
            "size": self.size,
            "color": self.color,
            "shape": self.shape,
            "x": self.x,
            "y": self.y,
            "metrics": {
                "invitations_sent": self.invitations_sent,
                "invitations_accepted": self.invitations_accepted,
                "viral_coefficient": self.viral_coefficient,
                "performance_score": self.performance_score
            }
        }


@dataclass
class NetworkGraphEdge:
    """Edge in network graph visualization."""
    
    source: str
    target: str
    
    # Edge properties
    weight: float  # Strength of connection
    color: str     # Based on relationship type
    width: float   # Based on activity level
    
    # Metadata
    invitation_date: datetime
    acceptance_date: Optional[datetime]
    relationship_strength: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for graph visualization."""
        return {
            "source": self.source,
            "target": self.target,
            "weight": self.weight,
            "color": self.color,
            "width": self.width,
            "invitation_date": self.invitation_date.isoformat(),
            "acceptance_date": self.acceptance_date.isoformat() if self.acceptance_date else None,
            "relationship_strength": self.relationship_strength
        }


@dataclass
class NetworkGraphData:
    """Complete network graph visualization data."""
    
    nodes: List[NetworkGraphNode]
    edges: List[NetworkGraphEdge]
    
    # Graph metrics
    total_nodes: int
    total_edges: int
    network_density: float
    clustering_coefficient: float
    
    # Visual layout info
    layout_algorithm: str
    zoom_level: float
    center_node_id: Optional[str]
    
    # Metadata
    generation_timestamp: datetime
    timeframe_days: int
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "nodes": [node.to_dict() for node in self.nodes],
            "edges": [edge.to_dict() for edge in self.edges],
            "total_nodes": self.total_nodes,
            "total_edges": self.total_edges,
            "network_density": self.network_density,
            "clustering_coefficient": self.clustering_coefficient,
            "layout_algorithm": self.layout_algorithm,
            "zoom_level": self.zoom_level,
            "center_node_id": self.center_node_id,
            "generation_timestamp": self.generation_timestamp.isoformat(),
            "timeframe_days": self.timeframe_days
        }


@dataclass
class DashboardMetricsData:
    """Aggregated metrics data for dashboard display."""
    
    # Key performance indicators
    total_network_size: int
    total_invitations_sent: int
    total_invitations_accepted: int
    overall_viral_coefficient: float
    overall_conversion_rate: float
    
    # Growth metrics
    daily_growth_rate: float
    weekly_growth_rate: float
    monthly_growth_rate: float
    
    # Top performers
    top_viral_champions: List[Dict[str, Any]]
    fastest_growing_cascades: List[Dict[str, Any]]
    most_active_inviters: List[Dict[str, Any]]
    
    # Time series data
    growth_timeline: List[Dict[str, Any]]
    conversion_timeline: List[Dict[str, Any]]
    
    # Network health
    network_health_score: float
    cascade_survival_rate: float
    average_cascade_depth: float
    
    # Metadata
    generation_timestamp: datetime
    timeframe_days: int
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "kpis": {
                "total_network_size": self.total_network_size,
                "total_invitations_sent": self.total_invitations_sent,
                "total_invitations_accepted": self.total_invitations_accepted,
                "overall_viral_coefficient": self.overall_viral_coefficient,
                "overall_conversion_rate": self.overall_conversion_rate
            },
            "growth_metrics": {
                "daily_growth_rate": self.daily_growth_rate,
                "weekly_growth_rate": self.weekly_growth_rate,
                "monthly_growth_rate": self.monthly_growth_rate
            },
            "top_performers": {
                "viral_champions": self.top_viral_champions,
                "growing_cascades": self.fastest_growing_cascades,
                "active_inviters": self.most_active_inviters
            },
            "timelines": {
                "growth": self.growth_timeline,
                "conversion": self.conversion_timeline
            },
            "network_health": {
                "health_score": self.network_health_score,
                "cascade_survival_rate": self.cascade_survival_rate,
                "average_cascade_depth": self.average_cascade_depth
            },
            "metadata": {
                "generation_timestamp": self.generation_timestamp.isoformat(),
                "timeframe_days": self.timeframe_days
            }
        }
