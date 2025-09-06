"""
Data classes for cascade and network metrics.

This module contains structured data classes for viral analytics metrics,
providing type safety and clear interfaces for metric data.
"""

from dataclasses import dataclass
from typing import Dict, List, Any, Optional
from datetime import datetime
from .enums import ViralMetricType, AnalyticsTimeframe


@dataclass
class CascadeMetrics:
    """Comprehensive metrics for a viral cascade."""
    
    # Basic cascade structure
    total_nodes: int
    total_invitations: int
    total_accepted: int
    max_depth: int
    max_width: int
    
    # Conversion metrics
    invitation_conversion_rate: float
    onboarding_completion_rate: float
    viral_coefficient: float
    
    # Network metrics
    network_density: float
    average_cascade_depth: float
    cascade_completion_rate: float
    
    # Time-based metrics
    average_invitation_response_time_hours: float
    average_onboarding_completion_time_days: float
    viral_velocity: float  # invitations per day
    
    # Quality metrics
    active_supplier_conversion_rate: float
    first_order_conversion_rate: float
    
    # Metadata
    calculation_timestamp: datetime
    timeframe: AnalyticsTimeframe
    company_id: Optional[int] = None
    
    def __post_init__(self):
        """Validate metrics after initialization."""
        if not 0 <= self.invitation_conversion_rate <= 1:
            raise ValueError("Invitation conversion rate must be between 0 and 1")
        
        if not 0 <= self.onboarding_completion_rate <= 1:
            raise ValueError("Onboarding completion rate must be between 0 and 1")
        
        if self.viral_coefficient < 0:
            raise ValueError("Viral coefficient cannot be negative")
    
    @property
    def is_viral(self) -> bool:
        """Check if cascade shows viral growth (coefficient > 1)."""
        return self.viral_coefficient > 1.0
    
    @property
    def growth_efficiency(self) -> float:
        """Calculate overall growth efficiency score."""
        return (
            self.viral_coefficient * 0.4 +
            self.invitation_conversion_rate * 0.3 +
            self.onboarding_completion_rate * 0.3
        )
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary of key metrics."""
        return {
            "total_network_size": self.total_nodes,
            "viral_coefficient": self.viral_coefficient,
            "is_viral": self.is_viral,
            "conversion_rate": self.invitation_conversion_rate,
            "completion_rate": self.onboarding_completion_rate,
            "growth_efficiency": self.growth_efficiency,
            "network_depth": self.max_depth,
            "network_width": self.max_width
        }


@dataclass
class NetworkEffectMetrics:
    """Metrics focused on network effects and viral spread."""
    
    # Network structure
    total_companies: int
    total_connections: int
    connected_components: int
    largest_component_size: int
    
    # Viral spread metrics
    viral_coefficient_by_generation: Dict[int, float]
    adoption_rate_by_generation: Dict[int, float]
    cascade_survival_rate: float  # % of cascades that reach depth > 2
    
    # Network health
    network_clustering_coefficient: float
    average_path_length: float
    network_diameter: int
    
    # Growth patterns
    daily_growth_rate: float
    weekly_growth_rate: float
    monthly_growth_rate: float
    
    # Quality indicators
    high_value_node_percentage: float  # % of nodes with high activity
    network_stability_score: float     # Resistance to node removal
    
    # Metadata
    calculation_timestamp: datetime
    timeframe: AnalyticsTimeframe
    
    @property
    def network_density(self) -> float:
        """Calculate network density."""
        if self.total_companies <= 1:
            return 0.0
        
        max_connections = self.total_companies * (self.total_companies - 1)
        return self.total_connections / max_connections if max_connections > 0 else 0.0
    
    @property
    def is_healthy_network(self) -> bool:
        """Determine if network shows healthy growth patterns."""
        return (
            self.cascade_survival_rate > 0.3 and
            self.network_clustering_coefficient > 0.1 and
            self.daily_growth_rate > 0.01
        )
    
    def get_generation_summary(self, max_generations: int = 5) -> List[Dict[str, Any]]:
        """Get summary of metrics by generation."""
        summary = []
        
        for gen in range(1, min(max_generations + 1, len(self.viral_coefficient_by_generation) + 1)):
            viral_coeff = self.viral_coefficient_by_generation.get(gen, 0.0)
            adoption_rate = self.adoption_rate_by_generation.get(gen, 0.0)
            
            summary.append({
                "generation": gen,
                "viral_coefficient": viral_coeff,
                "adoption_rate": adoption_rate,
                "is_growing": viral_coeff > 1.0,
                "efficiency": viral_coeff * adoption_rate
            })
        
        return summary


@dataclass
class CompanyViralMetrics:
    """Viral metrics specific to a single company."""
    
    company_id: int
    company_name: str
    
    # Direct metrics
    total_invitations_sent: int
    total_invitations_accepted: int
    total_suppliers_onboarded: int
    
    # Cascade metrics
    cascade_depth: int
    cascade_width: int
    total_cascade_nodes: int
    
    # Performance metrics
    invitation_conversion_rate: float
    onboarding_success_rate: float
    viral_coefficient: float
    
    # Ranking metrics
    rank_by_invitations: int
    rank_by_conversions: int
    rank_by_viral_coefficient: int
    percentile_ranking: float
    
    # Time metrics
    average_response_time_hours: float
    average_onboarding_time_days: float
    
    # Quality metrics
    active_supplier_rate: float
    repeat_order_rate: float
    
    # Metadata
    calculation_timestamp: datetime
    timeframe: AnalyticsTimeframe
    
    @property
    def is_viral_champion(self) -> bool:
        """Check if company qualifies as viral champion."""
        return (
            self.viral_coefficient > 1.5 and
            self.invitation_conversion_rate > 0.3 and
            self.total_invitations_sent >= 10
        )
    
    @property
    def performance_score(self) -> float:
        """Calculate overall performance score (0-100)."""
        score = (
            min(self.viral_coefficient / 2.0, 1.0) * 30 +  # Viral coefficient (max 30 points)
            self.invitation_conversion_rate * 25 +          # Conversion rate (max 25 points)
            self.onboarding_success_rate * 20 +             # Onboarding success (max 20 points)
            self.active_supplier_rate * 15 +                # Active suppliers (max 15 points)
            min(self.cascade_depth / 5.0, 1.0) * 10         # Network depth (max 10 points)
        )
        return min(score * 100, 100.0)
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary for dashboard display."""
        return {
            "company_id": self.company_id,
            "company_name": self.company_name,
            "viral_coefficient": self.viral_coefficient,
            "conversion_rate": self.invitation_conversion_rate,
            "total_network_size": self.total_cascade_nodes,
            "performance_score": self.performance_score,
            "is_viral_champion": self.is_viral_champion,
            "ranking_percentile": self.percentile_ranking
        }
