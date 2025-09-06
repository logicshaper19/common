"""
Viral Analytics Service - Modular Architecture

This package provides a modular, testable, and maintainable architecture for
viral analytics, replacing the monolithic ViralAnalyticsService.

The architecture follows domain-driven design principles with clear separation
of concerns:

- trackers/: Invitation and onboarding lifecycle management
- calculators/: Metrics calculation engines
- analyzers/: Network and cascade analysis
- generators/: Visualization data preparation
- models/: Domain models and data structures

Usage:
    from app.services.viral_analytics import create_viral_analytics_service
    
    # Create service with dependency injection
    service = create_viral_analytics_service(db)
    
    # Track invitation
    invitation = service.track_supplier_invitation(...)
    
    # Calculate metrics
    metrics = service.calculate_cascade_metrics(...)
"""

from sqlalchemy.orm import Session
from typing import Optional

from .analytics_service import ViralAnalyticsOrchestrator
from .trackers.invitation_tracker import InvitationTracker
from .trackers.onboarding_tracker import OnboardingTracker
from .calculators.metrics_calculator import MetricsCalculator
from .analyzers.network_analyzer import NetworkAnalyzer
from .analyzers.cascade_manager import CascadeNodeManager
from .generators.visualization_generator import VisualizationGenerator
from .services.query_service import AnalyticsQueryService


def create_viral_analytics_service(db: Session) -> ViralAnalyticsOrchestrator:
    """
    Factory function to create viral analytics service with dependencies.
    
    Args:
        db: Database session
        
    Returns:
        Configured ViralAnalyticsOrchestrator instance
    """
    
    # Create specialized services
    query_service = AnalyticsQueryService(db)
    invitation_tracker = InvitationTracker(db, query_service)
    onboarding_tracker = OnboardingTracker(db, query_service)
    cascade_manager = CascadeNodeManager(db, query_service)
    metrics_calculator = MetricsCalculator(db, query_service)
    network_analyzer = NetworkAnalyzer(db, query_service)
    visualization_generator = VisualizationGenerator(db, query_service)
    
    # Create main orchestrator
    return ViralAnalyticsOrchestrator(
        db=db,
        invitation_tracker=invitation_tracker,
        onboarding_tracker=onboarding_tracker,
        cascade_manager=cascade_manager,
        metrics_calculator=metrics_calculator,
        network_analyzer=network_analyzer,
        visualization_generator=visualization_generator
    )


# Backward compatibility wrapper
class ViralAnalyticsService:
    """
    Legacy wrapper for backward compatibility.
    
    This class maintains the same interface as the original monolithic service
    while delegating to the new modular architecture internally.
    """
    
    def __init__(self, db: Session):
        self._orchestrator = create_viral_analytics_service(db)
    
    def track_supplier_invitation(self, *args, **kwargs):
        """Delegate to new orchestrator."""
        return self._orchestrator.track_supplier_invitation(*args, **kwargs)
    
    def track_invitation_acceptance(self, *args, **kwargs):
        """Delegate to new orchestrator."""
        return self._orchestrator.track_invitation_acceptance(*args, **kwargs)
    
    def update_onboarding_stage(self, *args, **kwargs):
        """Delegate to new orchestrator."""
        return self._orchestrator.update_onboarding_stage(*args, **kwargs)
    
    def calculate_cascade_metrics(self, *args, **kwargs):
        """Delegate to new orchestrator."""
        return self._orchestrator.calculate_cascade_metrics(*args, **kwargs)
    
    def calculate_network_effect_metrics(self, *args, **kwargs):
        """Delegate to new orchestrator."""
        return self._orchestrator.calculate_network_effect_metrics(*args, **kwargs)
    
    def generate_onboarding_chain_visualization(self, *args, **kwargs):
        """Delegate to new orchestrator."""
        return self._orchestrator.generate_onboarding_chain_visualization(*args, **kwargs)
    
    def get_viral_adoption_dashboard_data(self, *args, **kwargs):
        """Delegate to new orchestrator."""
        return self._orchestrator.get_viral_adoption_dashboard_data(*args, **kwargs)


__all__ = [
    "create_viral_analytics_service",
    "ViralAnalyticsService",  # For backward compatibility
    "ViralAnalyticsOrchestrator",
]
