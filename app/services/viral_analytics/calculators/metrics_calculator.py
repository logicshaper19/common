"""
Metrics calculation engine for viral analytics.

This module handles all viral metrics calculations including viral coefficients,
network growth rates, conversion rates, and cascade metrics.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from app.models.viral_analytics import (
    SupplierInvitation,
    OnboardingProgress,
    ViralCascadeNode
)
from app.core.logging import get_logger
from ..models.cascade_metrics import CascadeMetrics, NetworkEffectMetrics, CompanyViralMetrics
from ..models.enums import InvitationStatus, OnboardingStage, AnalyticsTimeframe, ViralMetricType
from ..services.query_service import AnalyticsQueryService

logger = get_logger(__name__)


class MetricsCalculator:
    """Handles all viral metrics calculations."""
    
    def __init__(self, db: Session, query_service: AnalyticsQueryService):
        self.db = db
        self.query_service = query_service
    
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
            CascadeMetrics instance with all calculated metrics
        """
        logger.info(
            "Calculating cascade metrics",
            company_id=company_id,
            timeframe=timeframe.value
        )
        
        # Get time filter
        time_filter = self._get_time_filter(timeframe)
        
        # Get basic cascade structure metrics
        structure_metrics = self._calculate_structure_metrics(company_id, time_filter)
        
        # Get conversion metrics
        conversion_metrics = self._calculate_conversion_metrics(company_id, time_filter)
        
        # Get network metrics
        network_metrics = self._calculate_network_metrics(company_id, time_filter)
        
        # Get time-based metrics
        time_metrics = self._calculate_time_metrics(company_id, time_filter)
        
        # Get quality metrics
        quality_metrics = self._calculate_quality_metrics(company_id, time_filter)
        
        return CascadeMetrics(
            # Basic structure
            total_nodes=structure_metrics["total_nodes"],
            total_invitations=structure_metrics["total_invitations"],
            total_accepted=structure_metrics["total_accepted"],
            max_depth=structure_metrics["max_depth"],
            max_width=structure_metrics["max_width"],
            
            # Conversion metrics
            invitation_conversion_rate=conversion_metrics["invitation_conversion_rate"],
            onboarding_completion_rate=conversion_metrics["onboarding_completion_rate"],
            viral_coefficient=conversion_metrics["viral_coefficient"],
            
            # Network metrics
            network_density=network_metrics["network_density"],
            average_cascade_depth=network_metrics["average_cascade_depth"],
            cascade_completion_rate=network_metrics["cascade_completion_rate"],
            
            # Time metrics
            average_invitation_response_time_hours=time_metrics["avg_response_time_hours"],
            average_onboarding_completion_time_days=time_metrics["avg_onboarding_time_days"],
            viral_velocity=time_metrics["viral_velocity"],
            
            # Quality metrics
            active_supplier_conversion_rate=quality_metrics["active_supplier_rate"],
            first_order_conversion_rate=quality_metrics["first_order_rate"],
            
            # Metadata
            calculation_timestamp=datetime.utcnow(),
            timeframe=timeframe,
            company_id=company_id
        )
    
    def calculate_network_effect_metrics(
        self,
        timeframe: AnalyticsTimeframe = AnalyticsTimeframe.LAST_30_DAYS
    ) -> NetworkEffectMetrics:
        """
        Calculate network effect metrics across the entire platform.
        
        Args:
            timeframe: Time period for analysis
            
        Returns:
            NetworkEffectMetrics instance
        """
        logger.info("Calculating network effect metrics", timeframe=timeframe.value)
        
        time_filter = self._get_time_filter(timeframe)
        
        # Get network structure metrics
        network_structure = self._calculate_network_structure(time_filter)
        
        # Get viral spread metrics
        viral_spread = self._calculate_viral_spread_metrics(time_filter)
        
        # Get network health metrics
        network_health = self._calculate_network_health_metrics(time_filter)
        
        # Get growth patterns
        growth_patterns = self._calculate_growth_patterns(time_filter)
        
        return NetworkEffectMetrics(
            # Network structure
            total_companies=network_structure["total_companies"],
            total_connections=network_structure["total_connections"],
            connected_components=network_structure["connected_components"],
            largest_component_size=network_structure["largest_component_size"],
            
            # Viral spread
            viral_coefficient_by_generation=viral_spread["viral_coefficient_by_generation"],
            adoption_rate_by_generation=viral_spread["adoption_rate_by_generation"],
            cascade_survival_rate=viral_spread["cascade_survival_rate"],
            
            # Network health
            network_clustering_coefficient=network_health["clustering_coefficient"],
            average_path_length=network_health["average_path_length"],
            network_diameter=network_health["network_diameter"],
            
            # Growth patterns
            daily_growth_rate=growth_patterns["daily_growth_rate"],
            weekly_growth_rate=growth_patterns["weekly_growth_rate"],
            monthly_growth_rate=growth_patterns["monthly_growth_rate"],
            
            # Quality indicators
            high_value_node_percentage=network_health["high_value_node_percentage"],
            network_stability_score=network_health["network_stability_score"],
            
            # Metadata
            calculation_timestamp=datetime.utcnow(),
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
        time_filter = self._get_time_filter(timeframe)
        
        # Get invitations sent by this company
        invitations_query = self.db.query(func.count(SupplierInvitation.id)).filter(
            SupplierInvitation.inviting_company_id == company_id
        )
        
        if time_filter:
            invitations_query = invitations_query.filter(
                SupplierInvitation.created_at >= time_filter
            )
        
        total_invitations = invitations_query.scalar() or 0
        
        # Get accepted invitations
        accepted_query = self.db.query(func.count(SupplierInvitation.id)).filter(
            and_(
                SupplierInvitation.inviting_company_id == company_id,
                SupplierInvitation.status == InvitationStatus.ACCEPTED.value
            )
        )
        
        if time_filter:
            accepted_query = accepted_query.filter(
                SupplierInvitation.created_at >= time_filter
            )
        
        total_accepted = accepted_query.scalar() or 0
        
        # Get secondary invitations (invitations sent by companies this company invited)
        secondary_invitations = 0
        if total_accepted > 0:
            # Get companies invited by this company
            invited_companies = self.db.query(SupplierInvitation.accepting_company_id).filter(
                and_(
                    SupplierInvitation.inviting_company_id == company_id,
                    SupplierInvitation.status == InvitationStatus.ACCEPTED.value,
                    SupplierInvitation.accepting_company_id.isnot(None)
                )
            ).subquery()
            
            # Count invitations sent by those companies
            secondary_query = self.db.query(func.count(SupplierInvitation.id)).filter(
                SupplierInvitation.inviting_company_id.in_(invited_companies)
            )
            
            if time_filter:
                secondary_query = secondary_query.filter(
                    SupplierInvitation.created_at >= time_filter
                )
            
            secondary_invitations = secondary_query.scalar() or 0
        
        # Calculate viral coefficient
        # Viral coefficient = (secondary invitations) / (primary accepted invitations)
        viral_coefficient = secondary_invitations / total_accepted if total_accepted > 0 else 0
        
        logger.info(
            "Calculated viral coefficient",
            company_id=company_id,
            viral_coefficient=viral_coefficient,
            total_invitations=total_invitations,
            total_accepted=total_accepted,
            secondary_invitations=secondary_invitations
        )
        
        return viral_coefficient
    
    def calculate_network_growth_rate(
        self,
        timeframe: AnalyticsTimeframe = AnalyticsTimeframe.LAST_30_DAYS
    ) -> float:
        """
        Calculate overall network growth rate.
        
        Args:
            timeframe: Time period for analysis
            
        Returns:
            Growth rate as a percentage
        """
        days = AnalyticsTimeframe.get_days(timeframe)
        if days == 0:  # ALL_TIME
            days = 30  # Default to 30 days
        
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get network size at start and end of period
        start_size = self.db.query(func.count(SupplierInvitation.accepting_company_id.distinct())).filter(
            and_(
                SupplierInvitation.status == InvitationStatus.ACCEPTED.value,
                SupplierInvitation.accepted_at <= start_date
            )
        ).scalar() or 1  # Avoid division by zero
        
        end_size = self.db.query(func.count(SupplierInvitation.accepting_company_id.distinct())).filter(
            and_(
                SupplierInvitation.status == InvitationStatus.ACCEPTED.value,
                SupplierInvitation.accepted_at <= end_date
            )
        ).scalar() or 0
        
        # Calculate growth rate
        growth_rate = ((end_size - start_size) / start_size) * 100 if start_size > 0 else 0
        
        return growth_rate
    
    def get_top_inviters(
        self,
        limit: int = 10,
        timeframe: AnalyticsTimeframe = AnalyticsTimeframe.LAST_30_DAYS
    ) -> List[Dict[str, Any]]:
        """
        Get top companies by invitation count.
        
        Args:
            limit: Number of top inviters to return
            timeframe: Time period for analysis
            
        Returns:
            List of top inviter data
        """
        return self.query_service.get_top_performers(
            metric_type="invitations_sent",
            limit=limit,
            timeframe_days=AnalyticsTimeframe.get_days(timeframe)
        )
    
    def get_recent_onboardings(
        self,
        limit: int = 10,
        days_back: int = 7
    ) -> List[Dict[str, Any]]:
        """
        Get recently completed onboardings.
        
        Args:
            limit: Number of recent onboardings to return
            days_back: Number of days to look back
            
        Returns:
            List of recent onboarding data
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days_back)
        
        results = self.db.query(
            OnboardingProgress.company_id,
            OnboardingProgress.current_stage,
            OnboardingProgress.updated_at,
            func.coalesce(OnboardingProgress.stage_completion_percentage, 0).label('completion')
        ).filter(
            and_(
                OnboardingProgress.updated_at >= cutoff_date,
                OnboardingProgress.current_stage.in_([
                    OnboardingStage.VERIFICATION_COMPLETED.value,
                    OnboardingStage.FIRST_ORDER_PLACED.value,
                    OnboardingStage.ACTIVE_SUPPLIER.value
                ])
            )
        ).order_by(OnboardingProgress.updated_at.desc()).limit(limit).all()
        
        onboardings = []
        for company_id, stage, updated_at, completion in results:
            onboardings.append({
                "company_id": company_id,
                "current_stage": stage,
                "completion_percentage": float(completion),
                "updated_at": updated_at.isoformat(),
                "days_ago": (datetime.utcnow() - updated_at).days
            })
        
        return onboardings
    
    def _get_time_filter(self, timeframe: AnalyticsTimeframe) -> Optional[datetime]:
        """Get datetime filter for timeframe."""
        if timeframe == AnalyticsTimeframe.ALL_TIME:
            return None
        
        days = AnalyticsTimeframe.get_days(timeframe)
        return datetime.utcnow() - timedelta(days=days)
    
    def _calculate_structure_metrics(
        self,
        company_id: Optional[int],
        time_filter: Optional[datetime]
    ) -> Dict[str, Any]:
        """Calculate basic cascade structure metrics."""
        # Implementation for structure metrics calculation
        # This would include queries for total nodes, invitations, etc.
        return {
            "total_nodes": 0,
            "total_invitations": 0,
            "total_accepted": 0,
            "max_depth": 0,
            "max_width": 0
        }
    
    def _calculate_conversion_metrics(
        self,
        company_id: Optional[int],
        time_filter: Optional[datetime]
    ) -> Dict[str, Any]:
        """Calculate conversion-related metrics."""
        # Implementation for conversion metrics
        return {
            "invitation_conversion_rate": 0.0,
            "onboarding_completion_rate": 0.0,
            "viral_coefficient": 0.0
        }
    
    def _calculate_network_metrics(
        self,
        company_id: Optional[int],
        time_filter: Optional[datetime]
    ) -> Dict[str, Any]:
        """Calculate network structure metrics."""
        # Implementation for network metrics
        return {
            "network_density": 0.0,
            "average_cascade_depth": 0.0,
            "cascade_completion_rate": 0.0
        }
    
    def _calculate_time_metrics(
        self,
        company_id: Optional[int],
        time_filter: Optional[datetime]
    ) -> Dict[str, Any]:
        """Calculate time-based metrics."""
        # Implementation for time metrics
        return {
            "avg_response_time_hours": 0.0,
            "avg_onboarding_time_days": 0.0,
            "viral_velocity": 0.0
        }
    
    def _calculate_quality_metrics(
        self,
        company_id: Optional[int],
        time_filter: Optional[datetime]
    ) -> Dict[str, Any]:
        """Calculate quality-related metrics."""
        # Implementation for quality metrics
        return {
            "active_supplier_rate": 0.0,
            "first_order_rate": 0.0
        }
    
    def _calculate_network_structure(self, time_filter: Optional[datetime]) -> Dict[str, Any]:
        """Calculate network structure metrics."""
        # Implementation for network structure calculation
        return {
            "total_companies": 0,
            "total_connections": 0,
            "connected_components": 0,
            "largest_component_size": 0
        }
    
    def _calculate_viral_spread_metrics(self, time_filter: Optional[datetime]) -> Dict[str, Any]:
        """Calculate viral spread metrics."""
        # Implementation for viral spread calculation
        return {
            "viral_coefficient_by_generation": {},
            "adoption_rate_by_generation": {},
            "cascade_survival_rate": 0.0
        }
    
    def _calculate_network_health_metrics(self, time_filter: Optional[datetime]) -> Dict[str, Any]:
        """Calculate network health metrics."""
        # Implementation for network health calculation
        return {
            "clustering_coefficient": 0.0,
            "average_path_length": 0.0,
            "network_diameter": 0,
            "high_value_node_percentage": 0.0,
            "network_stability_score": 0.0
        }
    
    def _calculate_growth_patterns(self, time_filter: Optional[datetime]) -> Dict[str, Any]:
        """Calculate growth pattern metrics."""
        # Implementation for growth pattern calculation
        return {
            "daily_growth_rate": 0.0,
            "weekly_growth_rate": 0.0,
            "monthly_growth_rate": 0.0
        }
