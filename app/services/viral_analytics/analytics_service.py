"""
Main orchestrator for viral analytics.

This module coordinates the complete viral analytics process,
orchestrating multiple specialized services and providing a unified interface.
"""

from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import date
from sqlalchemy.orm import Session

from app.models.viral_analytics import SupplierInvitation, OnboardingProgress
from app.core.logging import get_logger
from .trackers.invitation_tracker import InvitationTracker
from .trackers.onboarding_tracker import OnboardingTracker
from .calculators.metrics_calculator import MetricsCalculator
from .analyzers.network_analyzer import NetworkAnalyzer
from .analyzers.cascade_manager import CascadeNodeManager
from .generators.visualization_generator import VisualizationGenerator
from .models.cascade_metrics import CascadeMetrics, NetworkEffectMetrics
from .models.visualization_data import OnboardingChainVisualization, DashboardMetricsData
from .models.enums import OnboardingStage, AnalyticsTimeframe

logger = get_logger(__name__)


class ViralAnalyticsOrchestrator:
    """Main orchestrator for viral analytics functionality."""
    
    def __init__(
        self,
        db: Session,
        invitation_tracker: InvitationTracker,
        onboarding_tracker: OnboardingTracker,
        cascade_manager: CascadeNodeManager,
        metrics_calculator: MetricsCalculator,
        network_analyzer: NetworkAnalyzer,
        visualization_generator: VisualizationGenerator
    ):
        self.db = db
        self.invitation_tracker = invitation_tracker
        self.onboarding_tracker = onboarding_tracker
        self.cascade_manager = cascade_manager
        self.metrics_calculator = metrics_calculator
        self.network_analyzer = network_analyzer
        self.visualization_generator = visualization_generator
    
    def track_supplier_invitation(
        self,
        inviting_company_id: int,
        invited_company_name: str,
        invited_company_email: str,
        invitation_message: Optional[str] = None,
        parent_invitation_id: Optional[int] = None
    ) -> SupplierInvitation:
        """
        Track a new supplier invitation with viral cascade management.
        
        Args:
            inviting_company_id: ID of company sending invitation
            invited_company_name: Name of company being invited
            invited_company_email: Email of company being invited
            invitation_message: Optional custom message
            parent_invitation_id: Optional parent invitation for cascade tracking
            
        Returns:
            Created SupplierInvitation instance
        """
        logger.info(
            "Tracking supplier invitation",
            inviting_company_id=inviting_company_id,
            invited_company_name=invited_company_name
        )
        
        # Create invitation
        invitation = self.invitation_tracker.create_invitation(
            inviting_company_id=inviting_company_id,
            invited_company_name=invited_company_name,
            invited_company_email=invited_company_email,
            invitation_message=invitation_message,
            parent_invitation_id=parent_invitation_id
        )
        
        # Update or create cascade node for inviting company
        parent_company_id = None
        if parent_invitation_id:
            parent_invitation = self.invitation_tracker.find_parent_invitation(inviting_company_id)
            if parent_invitation:
                parent_company_id = parent_invitation.inviting_company_id
        
        self.cascade_manager.create_or_update_cascade_node(
            company_id=inviting_company_id,
            parent_company_id=parent_company_id
        )
        
        # Update cascade metrics
        self.cascade_manager.update_cascade_node_metrics(inviting_company_id)
        
        logger.info(
            "Supplier invitation tracked successfully",
            invitation_id=invitation.id,
            inviting_company_id=inviting_company_id
        )
        
        return invitation
    
    def track_invitation_acceptance(
        self,
        invitation_id: int,
        accepting_company_id: int
    ) -> OnboardingProgress:
        """
        Track invitation acceptance and initialize onboarding.
        
        Args:
            invitation_id: ID of invitation being accepted
            accepting_company_id: ID of company accepting invitation
            
        Returns:
            Created OnboardingProgress instance
        """
        logger.info(
            "Tracking invitation acceptance",
            invitation_id=invitation_id,
            accepting_company_id=accepting_company_id
        )
        
        # Mark invitation as accepted
        success = self.invitation_tracker.accept_invitation(invitation_id, accepting_company_id)
        
        if not success:
            raise ValueError(f"Failed to accept invitation {invitation_id}")
        
        # Initialize onboarding progress
        self.onboarding_tracker.update_onboarding_stage(
            company_id=accepting_company_id,
            new_stage=OnboardingStage.REGISTERED,
            completion_percentage=10.0,
            notes="Invitation accepted, onboarding started"
        )
        
        # Create cascade node for accepting company
        invitation = self.db.query(SupplierInvitation).filter(
            SupplierInvitation.id == invitation_id
        ).first()
        
        if invitation:
            self.cascade_manager.create_or_update_cascade_node(
                company_id=accepting_company_id,
                parent_company_id=invitation.inviting_company_id
            )
            
            # Update metrics for both companies
            self.cascade_manager.update_cascade_node_metrics(invitation.inviting_company_id)
            self.cascade_manager.update_cascade_node_metrics(accepting_company_id)
        
        # Get onboarding progress
        progress = self.onboarding_tracker.get_onboarding_progress(accepting_company_id)
        
        logger.info(
            "Invitation acceptance tracked successfully",
            invitation_id=invitation_id,
            accepting_company_id=accepting_company_id
        )
        
        return progress
    
    def update_onboarding_stage(
        self,
        company_id: int,
        new_stage: OnboardingStage,
        completion_percentage: float = 0.0,
        notes: Optional[str] = None
    ) -> None:
        """
        Update onboarding stage and cascade metrics.
        
        Args:
            company_id: ID of company to update
            new_stage: New onboarding stage
            completion_percentage: Percentage completion of the stage
            notes: Optional notes about the stage update
        """
        logger.info(
            "Updating onboarding stage",
            company_id=company_id,
            new_stage=new_stage.value
        )
        
        # Update onboarding stage
        self.onboarding_tracker.update_onboarding_stage(
            company_id=company_id,
            new_stage=new_stage,
            completion_percentage=completion_percentage,
            notes=notes
        )
        
        # Update cascade metrics if this is a significant milestone
        if new_stage in OnboardingStage.get_completion_stages():
            self.cascade_manager.update_cascade_node_metrics(company_id)
        
        logger.info(
            "Onboarding stage updated successfully",
            company_id=company_id,
            new_stage=new_stage.value
        )
    
    def calculate_cascade_metrics(
        self,
        company_id: Optional[int] = None,
        timeframe: AnalyticsTimeframe = AnalyticsTimeframe.LAST_30_DAYS
    ) -> CascadeMetrics:
        """
        Calculate comprehensive cascade metrics.
        
        Args:
            company_id: Optional company filter for cascade root
            timeframe: Time period for analysis
            
        Returns:
            CascadeMetrics instance
        """
        logger.info(
            "Calculating cascade metrics",
            company_id=company_id,
            timeframe=timeframe.value
        )
        
        return self.metrics_calculator.calculate_cascade_metrics(
            company_id=company_id,
            timeframe=timeframe
        )
    
    def calculate_network_effect_metrics(
        self,
        timeframe: AnalyticsTimeframe = AnalyticsTimeframe.LAST_30_DAYS
    ) -> NetworkEffectMetrics:
        """
        Calculate network effect metrics across the platform.
        
        Args:
            timeframe: Time period for analysis
            
        Returns:
            NetworkEffectMetrics instance
        """
        logger.info("Calculating network effect metrics", timeframe=timeframe.value)
        
        return self.metrics_calculator.calculate_network_effect_metrics(timeframe=timeframe)
    
    def generate_onboarding_chain_visualization(
        self,
        root_company_id: int,
        max_depth: int = 5,
        timeframe_days: int = 90
    ) -> OnboardingChainVisualization:
        """
        Generate onboarding chain visualization data.
        
        Args:
            root_company_id: Root company for the chain
            max_depth: Maximum depth to visualize
            timeframe_days: Days to look back for data
            
        Returns:
            OnboardingChainVisualization instance
        """
        logger.info(
            "Generating onboarding chain visualization",
            root_company_id=root_company_id,
            max_depth=max_depth
        )
        
        return self.visualization_generator.generate_onboarding_chain_visualization(
            root_company_id=root_company_id,
            max_depth=max_depth,
            timeframe_days=timeframe_days
        )
    
    def get_viral_adoption_dashboard_data(
        self,
        timeframe: AnalyticsTimeframe = AnalyticsTimeframe.LAST_30_DAYS
    ) -> DashboardMetricsData:
        """
        Get comprehensive dashboard data for viral adoption metrics.
        
        Args:
            timeframe: Time period for metrics
            
        Returns:
            DashboardMetricsData instance
        """
        logger.info("Generating viral adoption dashboard data", timeframe=timeframe.value)
        
        return self.visualization_generator.prepare_metrics_dashboard_data(timeframe=timeframe)
    
    def get_viral_champions(
        self,
        limit: int = 20,
        timeframe: AnalyticsTimeframe = AnalyticsTimeframe.LAST_30_DAYS
    ) -> List[Dict[str, Any]]:
        """
        Get viral champions based on network performance.
        
        Args:
            limit: Maximum number of champions to return
            timeframe: Time period for analysis
            
        Returns:
            List of viral champion data
        """
        return self.network_analyzer.get_viral_champions(limit=limit, timeframe=timeframe)
    
    def get_growth_hotspots(
        self,
        limit: int = 10,
        timeframe: AnalyticsTimeframe = AnalyticsTimeframe.LAST_7_DAYS
    ) -> List[Dict[str, Any]]:
        """
        Get growth hotspots in the network.
        
        Args:
            limit: Maximum number of hotspots to return
            timeframe: Time period for analysis
            
        Returns:
            List of growth hotspot data
        """
        return self.network_analyzer.get_growth_hotspots(limit=limit, timeframe=timeframe)
    
    def analyze_network_structure(
        self,
        timeframe: AnalyticsTimeframe = AnalyticsTimeframe.LAST_30_DAYS
    ) -> Dict[str, Any]:
        """
        Analyze overall network structure and properties.
        
        Args:
            timeframe: Time period for analysis
            
        Returns:
            Network structure analysis
        """
        return self.network_analyzer.analyze_network_structure(timeframe=timeframe)
    
    def expire_old_invitations(self, days_old: int = 30) -> int:
        """
        Expire invitations that are older than specified days.
        
        Args:
            days_old: Number of days after which to expire invitations
            
        Returns:
            Number of invitations expired
        """
        return self.invitation_tracker.expire_old_invitations(days_old=days_old)
    
    def get_company_viral_stats(
        self,
        company_id: int,
        timeframe: AnalyticsTimeframe = AnalyticsTimeframe.LAST_30_DAYS
    ) -> Dict[str, Any]:
        """
        Get comprehensive viral statistics for a company.
        
        Args:
            company_id: Company ID
            timeframe: Time period for analysis
            
        Returns:
            Company viral statistics
        """
        return self.metrics_calculator.query_service.get_company_viral_stats(
            company_id=company_id,
            timeframe=timeframe
        )
    
    def calculate_viral_coefficient(
        self,
        company_id: int,
        timeframe: AnalyticsTimeframe = AnalyticsTimeframe.LAST_30_DAYS
    ) -> float:
        """
        Calculate viral coefficient for a specific company.
        
        Args:
            company_id: Company ID
            timeframe: Time period for analysis
            
        Returns:
            Viral coefficient value
        """
        return self.metrics_calculator.calculate_viral_coefficient(
            company_id=company_id,
            timeframe=timeframe
        )
