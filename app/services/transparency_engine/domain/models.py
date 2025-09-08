"""
Domain models for transparency calculation engine.
"""
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime
from decimal import Decimal
from dataclasses import dataclass, field as dataclass_field

from .enums import TransparencyLevel, ConfidenceLevel, CertificationTier


@dataclass
class TransparencyNode:
    """Represents a node in the transparency calculation graph."""
    po_id: UUID
    po_number: str
    company_id: UUID
    company_type: str
    product_id: UUID
    product_category: str
    quantity: Decimal
    unit: str
    
    # Transparency factors
    has_origin_data: bool = False
    has_geographic_coordinates: bool = False
    has_certifications: bool = False
    certification_count: int = 0
    high_value_cert_count: int = 0
    data_completeness_score: float = 0.0
    
    # Input materials
    input_materials: List[Dict[str, Any]] = dataclass_field(default_factory=list)
    
    # Calculated scores
    base_ttm_score: float = 0.0
    base_ttp_score: float = 0.0
    weighted_ttm_score: float = 0.0
    weighted_ttp_score: float = 0.0
    confidence_level: float = 0.0
    
    # Graph traversal metadata
    depth: int = 0
    visited_at: Optional[datetime] = None
    is_circular: bool = False
    degradation_factor: float = 1.0
    
    @property
    def transparency_level(self) -> TransparencyLevel:
        """Get transparency level based on combined score."""
        combined_score = (self.weighted_ttm_score + self.weighted_ttp_score) / 2
        
        if combined_score >= 0.8:
            return TransparencyLevel.VERY_HIGH
        elif combined_score >= 0.6:
            return TransparencyLevel.HIGH
        elif combined_score >= 0.4:
            return TransparencyLevel.MEDIUM
        elif combined_score >= 0.2:
            return TransparencyLevel.LOW
        else:
            return TransparencyLevel.VERY_LOW
    
    @property
    def confidence_level_enum(self) -> ConfidenceLevel:
        """Get confidence level enum."""
        if self.confidence_level >= 0.8:
            return ConfidenceLevel.VERY_HIGH
        elif self.confidence_level >= 0.6:
            return ConfidenceLevel.HIGH
        elif self.confidence_level >= 0.4:
            return ConfidenceLevel.MEDIUM
        elif self.confidence_level >= 0.2:
            return ConfidenceLevel.LOW
        else:
            return ConfidenceLevel.VERY_LOW
    
    @property
    def certification_tier(self) -> CertificationTier:
        """Get certification tier based on certification counts."""
        if self.high_value_cert_count >= 3:
            return CertificationTier.ELITE
        elif self.high_value_cert_count >= 1:
            return CertificationTier.PREMIUM
        elif self.certification_count >= 2:
            return CertificationTier.STANDARD
        elif self.certification_count >= 1:
            return CertificationTier.BASIC
        else:
            return CertificationTier.BASIC


@dataclass
class TransparencyPath:
    """Represents a path through the supply chain graph."""
    nodes: List[TransparencyNode] = dataclass_field(default_factory=list)
    total_weight: float = 0.0
    path_ttm_score: float = 0.0
    path_ttp_score: float = 0.0
    path_confidence: float = 0.0
    has_cycles: bool = False
    cycle_break_points: List[UUID] = dataclass_field(default_factory=list)
    
    @property
    def path_length(self) -> int:
        """Get the length of the path."""
        return len(self.nodes)
    
    @property
    def average_score(self) -> float:
        """Get average transparency score for the path."""
        return (self.path_ttm_score + self.path_ttp_score) / 2
    
    @property
    def weakest_link(self) -> Optional[TransparencyNode]:
        """Find the weakest link in the transparency chain."""
        if not self.nodes:
            return None
        
        return min(
            self.nodes,
            key=lambda node: (node.weighted_ttm_score + node.weighted_ttp_score) / 2
        )


@dataclass
class TransparencyResult:
    """Complete transparency calculation result."""
    po_id: UUID
    ttm_score: float
    ttp_score: float
    confidence_level: float
    traced_percentage: float
    calculation_timestamp: datetime
    
    # Detailed breakdown
    total_nodes_analyzed: int = 0
    circular_references_detected: int = 0
    data_gaps_identified: int = 0
    
    # Path analysis
    primary_path: Optional[TransparencyPath] = None
    alternative_paths: List[TransparencyPath] = dataclass_field(default_factory=list)
    
    # Improvement opportunities
    improvement_potential: float = 0.0
    critical_gaps: List[str] = dataclass_field(default_factory=list)
    
    @property
    def combined_score(self) -> float:
        """Get combined transparency score."""
        return (self.ttm_score + self.ttp_score) / 2
    
    @property
    def transparency_level(self) -> TransparencyLevel:
        """Get overall transparency level."""
        combined = self.combined_score
        
        if combined >= 0.8:
            return TransparencyLevel.VERY_HIGH
        elif combined >= 0.6:
            return TransparencyLevel.HIGH
        elif combined >= 0.4:
            return TransparencyLevel.MEDIUM
        elif combined >= 0.2:
            return TransparencyLevel.LOW
        else:
            return TransparencyLevel.VERY_LOW
    
    @property
    def confidence_level_enum(self) -> ConfidenceLevel:
        """Get confidence level enum."""
        if self.confidence_level >= 0.8:
            return ConfidenceLevel.VERY_HIGH
        elif self.confidence_level >= 0.6:
            return ConfidenceLevel.HIGH
        elif self.confidence_level >= 0.4:
            return ConfidenceLevel.MEDIUM
        elif self.confidence_level >= 0.2:
            return ConfidenceLevel.LOW
        else:
            return ConfidenceLevel.VERY_LOW


@dataclass
class TransparencyMetrics:
    """Aggregated transparency metrics."""
    total_pos_analyzed: int = 0
    average_ttm_score: float = 0.0
    average_ttp_score: float = 0.0
    average_confidence: float = 0.0
    
    # Distribution
    transparency_distribution: Dict[TransparencyLevel, int] = dataclass_field(default_factory=dict)
    confidence_distribution: Dict[ConfidenceLevel, int] = dataclass_field(default_factory=dict)
    
    # Trends
    score_trend: List[Dict[str, Any]] = dataclass_field(default_factory=list)
    improvement_rate: float = 0.0
    
    # Quality indicators
    data_completeness_rate: float = 0.0
    certification_coverage: float = 0.0
    geographic_coverage: float = 0.0


@dataclass
class ImprovementSuggestion:
    """Transparency improvement suggestion."""
    category: str
    priority: str  # high, medium, low
    description: str
    impact_estimate: float  # Expected score improvement
    effort_estimate: str    # low, medium, high
    specific_actions: List[str] = dataclass_field(default_factory=list)
    
    # Context
    affected_nodes: List[UUID] = dataclass_field(default_factory=list)
    cost_benefit_ratio: Optional[float] = None
    implementation_timeline: Optional[str] = None
