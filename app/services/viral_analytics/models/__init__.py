"""
Domain models and data structures for viral analytics.

This module contains all data classes, enums, and domain models used
throughout the viral analytics system.
"""

from .cascade_metrics import CascadeMetrics, NetworkEffectMetrics
from .visualization_data import OnboardingChainVisualization, NetworkGraphData
from .enums import OnboardingStage, InvitationStatus, ViralMetricType

__all__ = [
    "CascadeMetrics",
    "NetworkEffectMetrics", 
    "OnboardingChainVisualization",
    "NetworkGraphData",
    "OnboardingStage",
    "InvitationStatus",
    "ViralMetricType",
]
