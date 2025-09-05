"""
Traceability and transparency calculation schemas.
"""
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field
from enum import Enum


class TransparencyLevel(str, Enum):
    """Transparency levels for scoring."""
    MILL = "mill"
    PLANTATION = "plantation"


class TransparencyScoreRequest(BaseModel):
    """Request schema for transparency score calculation."""
    purchase_order_id: UUID
    force_recalculation: bool = Field(False, description="Force recalculation even if recent scores exist")


class TransparencyFactorsResponse(BaseModel):
    """Response schema for transparency factors analysis."""
    has_origin_data: bool
    has_geographic_coordinates: bool
    has_certifications: bool
    certification_count: int
    has_harvest_date: bool
    has_farm_identification: bool
    has_input_materials: bool
    input_material_count: int
    company_type_score: float
    product_category_score: float
    data_completeness_score: float
    certification_quality_score: float


class TraceabilityMetricsResponse(BaseModel):
    """Response schema for traceability metrics."""
    purchase_order_id: UUID
    total_nodes: int
    max_depth_reached: int
    mill_nodes: int
    plantation_nodes: int
    origin_data_nodes: int
    certified_nodes: int
    geographic_data_nodes: int
    input_material_links: int
    transparency_to_mill: float = Field(..., ge=0.0, le=1.0, description="TTM score (0.0 to 1.0)")
    transparency_to_plantation: float = Field(..., ge=0.0, le=1.0, description="TTP score (0.0 to 1.0)")
    calculation_timestamp: datetime
    score_interpretation: Dict[str, str]


class BulkTransparencyUpdateRequest(BaseModel):
    """Request schema for bulk transparency score updates."""
    company_id: Optional[UUID] = Field(None, description="Optional company ID to filter by")
    max_age_hours: int = Field(24, ge=1, le=168, description="Only update scores older than this many hours")
    force_update: bool = Field(False, description="Force update all scores regardless of age")


class BulkUpdateResult(BaseModel):
    """Result schema for individual purchase order in bulk update."""
    po_id: str
    po_number: str
    ttm_score: Optional[float] = None
    ttp_score: Optional[float] = None
    status: str  # "updated", "error", "skipped"
    error: Optional[str] = None


class BulkTransparencyUpdateResponse(BaseModel):
    """Response schema for bulk transparency score updates."""
    total_processed: int
    updated_count: int
    error_count: int
    skipped_count: int = 0
    results: List[BulkUpdateResult]
    timestamp: str
    summary: Dict[str, Any]


class TransparencyAnalyticsRequest(BaseModel):
    """Request schema for transparency analytics."""
    company_id: UUID
    include_detailed_breakdown: bool = Field(False, description="Include detailed breakdown by product/supplier")
    date_range_days: int = Field(90, ge=1, le=365, description="Number of days to include in analysis")


class TransparencyDistribution(BaseModel):
    """Transparency score distribution."""
    high_transparency: int = Field(..., description="Count of POs with TTP >= 0.8")
    medium_transparency: int = Field(..., description="Count of POs with 0.5 <= TTP < 0.8")
    low_transparency: int = Field(..., description="Count of POs with TTP < 0.5")


class TransparencyAnalyticsResponse(BaseModel):
    """Response schema for transparency analytics."""
    company_id: UUID
    total_purchase_orders: int
    average_ttm_score: float
    average_ttp_score: float
    transparency_distribution: TransparencyDistribution
    improvement_opportunities: List[str]
    last_updated: str
    trends: Optional[Dict[str, Any]] = None
    detailed_breakdown: Optional[Dict[str, Any]] = None


class SupplyChainNodeAnalysis(BaseModel):
    """Analysis of a single supply chain node."""
    purchase_order_id: UUID
    po_number: str
    level: int
    company_name: str
    company_type: str
    product_name: str
    product_category: str
    quantity: Decimal
    percentage_contribution: Optional[float] = None
    transparency_factors: TransparencyFactorsResponse
    contribution_weight: float
    node_transparency_score: float


class EnhancedTraceabilityResponse(BaseModel):
    """Enhanced traceability response with transparency analysis."""
    root_purchase_order: SupplyChainNodeAnalysis
    supply_chain: List[SupplyChainNodeAnalysis]
    traceability_metrics: TraceabilityMetricsResponse
    transparency_insights: Dict[str, Any]
    recommendations: List[str]


class TransparencyScoreUpdateEvent(BaseModel):
    """Event schema for transparency score updates."""
    purchase_order_id: UUID
    previous_ttm_score: Optional[float]
    new_ttm_score: float
    previous_ttp_score: Optional[float]
    new_ttp_score: float
    score_change_ttm: float
    score_change_ttp: float
    updated_at: datetime
    trigger: str  # "manual", "automatic", "confirmation", "bulk_update"


class TransparencyTrendData(BaseModel):
    """Transparency trend data over time."""
    date: str
    average_ttm: float
    average_ttp: float
    total_pos: int
    high_transparency_count: int


class TransparencyTrendsResponse(BaseModel):
    """Response schema for transparency trends."""
    company_id: UUID
    date_range_days: int
    trend_data: List[TransparencyTrendData]
    overall_trend_ttm: str  # "improving", "declining", "stable"
    overall_trend_ttp: str  # "improving", "declining", "stable"
    trend_analysis: Dict[str, Any]


class TransparencyBenchmarkRequest(BaseModel):
    """Request schema for transparency benchmarking."""
    company_id: UUID
    benchmark_against: str = Field("industry", description="Benchmark against 'industry', 'sector', or 'region'")
    include_peer_comparison: bool = Field(False, description="Include anonymous peer comparison")


class TransparencyBenchmarkResponse(BaseModel):
    """Response schema for transparency benchmarking."""
    company_id: UUID
    company_ttm_score: float
    company_ttp_score: float
    benchmark_ttm_score: float
    benchmark_ttp_score: float
    percentile_ranking_ttm: float
    percentile_ranking_ttp: float
    performance_vs_benchmark: Dict[str, str]
    improvement_potential: Dict[str, float]
    best_practices: List[str]


class TransparencyImprovementPlan(BaseModel):
    """Transparency improvement plan."""
    priority: str  # "high", "medium", "low"
    category: str  # "origin_data", "certifications", "input_materials", etc.
    description: str
    expected_impact_ttm: float
    expected_impact_ttp: float
    implementation_effort: str  # "low", "medium", "high"
    timeline_weeks: int


class EnhancedTransparencyNode(BaseModel):
    """Enhanced transparency node for detailed analysis."""
    po_id: UUID
    po_number: str
    company_id: UUID
    company_type: str
    product_id: UUID
    product_category: str
    quantity: Decimal
    unit: str

    # Transparency factors
    has_origin_data: bool
    has_geographic_coordinates: bool
    has_certifications: bool
    certification_count: int
    high_value_cert_count: int
    data_completeness_score: float

    # Calculated scores
    base_ttm_score: float
    base_ttp_score: float
    weighted_ttm_score: float
    weighted_ttp_score: float
    confidence_level: float

    # Graph metadata
    depth: int
    is_circular: bool
    degradation_factor: float
    visited_at: datetime


class EnhancedTransparencyPath(BaseModel):
    """Enhanced transparency path through supply chain."""
    nodes: List[EnhancedTransparencyNode]
    total_weight: float
    path_ttm_score: float
    path_ttp_score: float
    path_confidence: float
    has_cycles: bool
    cycle_break_points: List[UUID]


class EnhancedTransparencyResult(BaseModel):
    """Enhanced transparency calculation result."""
    po_id: UUID
    ttm_score: float
    ttp_score: float
    confidence_level: float
    traced_percentage: float
    untraced_percentage: float

    # Graph analysis
    total_nodes: int
    max_depth: int
    circular_references: List[UUID]
    degradation_applied: float

    # Detailed breakdown
    paths: List[EnhancedTransparencyPath]
    node_details: List[EnhancedTransparencyNode]
    calculation_metadata: Dict[str, Any]

    # Timestamps
    calculated_at: datetime
    calculation_duration_ms: float


class TransparencyCalculationRequest(BaseModel):
    """Request for enhanced transparency calculation."""
    purchase_order_id: UUID
    force_recalculation: bool = Field(False, description="Force recalculation even if cached")
    include_detailed_analysis: bool = Field(True, description="Include detailed path and node analysis")
    max_depth: Optional[int] = Field(None, description="Maximum depth for graph traversal")


class TransparencyImprovementSuggestion(BaseModel):
    """Transparency improvement suggestion."""
    category: str
    priority: str  # "high", "medium", "low"
    description: str
    expected_impact: float
    implementation_effort: str  # "low", "medium", "high"


class CircularReferenceAnalysis(BaseModel):
    """Analysis of circular references in supply chain."""
    detected_cycles: List[List[UUID]]
    cycle_break_points: List[UUID]
    affected_transparency_score: float
    resolution_suggestions: List[str]


class TransparencyImprovementResponse(BaseModel):
    """Response schema for transparency improvement recommendations."""
    company_id: UUID
    current_ttm_score: float
    current_ttp_score: float
    potential_ttm_score: float
    potential_ttp_score: float
    improvement_plans: List[TransparencyImprovementPlan]
    quick_wins: List[str]
    long_term_strategies: List[str]


class TransparencyAuditRequest(BaseModel):
    """Request schema for transparency audit."""
    purchase_order_id: UUID
    audit_depth: int = Field(5, ge=1, le=10, description="Depth of supply chain to audit")
    include_recommendations: bool = Field(True, description="Include improvement recommendations")


class TransparencyAuditFinding(BaseModel):
    """Individual finding in transparency audit."""
    level: int
    purchase_order_id: UUID
    finding_type: str  # "missing_data", "low_quality", "opportunity", "compliance"
    severity: str  # "critical", "high", "medium", "low"
    description: str
    recommendation: str
    impact_on_transparency: str


class TransparencyAuditResponse(BaseModel):
    """Response schema for transparency audit."""
    purchase_order_id: UUID
    audit_timestamp: datetime
    overall_transparency_grade: str  # "A", "B", "C", "D", "F"
    audit_findings: List[TransparencyAuditFinding]
    compliance_status: Dict[str, str]
    data_quality_score: float
    recommendations_summary: List[str]
    next_audit_recommended: datetime
