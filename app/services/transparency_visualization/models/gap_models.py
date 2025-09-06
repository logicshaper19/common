"""
Models for gap analysis and improvement recommendations.
"""
from typing import List, Dict, Any, Optional
from uuid import UUID
from dataclasses import dataclass, field
from enum import Enum


class GapType(Enum):
    """Types of transparency gaps."""
    MISSING_ORIGIN_DATA = "missing_origin_data"
    MISSING_INPUT_MATERIAL = "missing_input_material"
    LOW_CONFIDENCE = "low_confidence"
    INCOMPLETE_CERTIFICATIONS = "incomplete_certifications"
    MISSING_GEOGRAPHIC_DATA = "missing_geographic_data"
    WEAK_TRACEABILITY_LINK = "weak_traceability_link"


class GapSeverity(Enum):
    """Severity levels for gaps."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RecommendationPriority(Enum):
    """Priority levels for recommendations."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class GapAnalysis:
    """Individual gap analysis result."""
    gap_id: str
    node_id: str
    gap_type: GapType
    severity: GapSeverity
    description: str
    impact_score: float
    improvement_potential: float
    affected_metrics: List[str] = field(default_factory=list)
    suggested_actions: List[str] = field(default_factory=list)


@dataclass
class ImprovementRecommendation:
    """Actionable improvement recommendation."""
    recommendation_id: str
    category: str
    priority: RecommendationPriority
    title: str
    description: str
    expected_ttm_impact: float
    expected_ttp_impact: float
    implementation_effort: str  # "low", "medium", "high"
    timeline: str
    actions: List[str] = field(default_factory=list)
    affected_gaps: List[str] = field(default_factory=list)
    estimated_cost: Optional[str] = None
    success_metrics: List[str] = field(default_factory=list)

