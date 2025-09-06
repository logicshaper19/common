"""
Onboarding progress tracking service.

This module manages onboarding stage tracking and progression throughout
the supplier journey, providing insights into conversion funnels.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, func

from app.models.onboarding_progress import OnboardingProgress
from app.models.supplier_invitation import SupplierInvitation
from app.models.company import Company
from app.core.logging import get_logger
from ..models.enums import OnboardingStage, InvitationStatus
from ..services.query_service import AnalyticsQueryService

logger = get_logger(__name__)


class OnboardingTracker:
    """Manages onboarding stage tracking and progression."""
    
    def __init__(self, db: Session, query_service: AnalyticsQueryService):
        self.db = db
        self.query_service = query_service
    
    def update_onboarding_stage(
        self,
        company_id: int,
        new_stage: OnboardingStage,
        completion_percentage: float = 0.0,
        notes: Optional[str] = None
    ) -> None:
        """
        Update onboarding stage for a company.
        
        Args:
            company_id: ID of company to update
            new_stage: New onboarding stage
            completion_percentage: Percentage completion of the stage
            notes: Optional notes about the stage update
        """
        logger.info(
            "Updating onboarding stage",
            company_id=company_id,
            new_stage=new_stage.value,
            completion_percentage=completion_percentage
        )
        
        # Get or create onboarding progress record
        progress = self.get_onboarding_progress(company_id)
        
        if not progress:
            # Create new progress record
            progress = OnboardingProgress(
                company_id=company_id,
                current_stage=new_stage.value,
                stage_completion_percentage=completion_percentage,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            self.db.add(progress)
        else:
            # Update existing record
            old_stage = progress.current_stage
            progress.current_stage = new_stage.value
            progress.stage_completion_percentage = completion_percentage
            progress.updated_at = datetime.utcnow()
            
            # Track stage progression
            if self._is_stage_progression(old_stage, new_stage.value):
                self._record_stage_milestone(progress, old_stage, new_stage.value)
        
        if notes:
            progress.notes = notes
        
        self.db.commit()
        
        logger.info(
            "Onboarding stage updated successfully",
            company_id=company_id,
            new_stage=new_stage.value
        )
    
    def get_onboarding_progress(
        self,
        company_id: int
    ) -> Optional[OnboardingProgress]:
        """
        Get current onboarding progress for a company.
        
        Args:
            company_id: ID of company
            
        Returns:
            OnboardingProgress instance if found
        """
        return self.db.query(OnboardingProgress).filter(
            OnboardingProgress.company_id == company_id
        ).first()
    
    def calculate_onboarding_metrics(
        self,
        company_id: Optional[int] = None,
        days_back: int = 30
    ) -> Dict[str, Any]:
        """
        Calculate comprehensive onboarding metrics.
        
        Args:
            company_id: Optional company filter
            days_back: Number of days to analyze
            
        Returns:
            Dictionary with onboarding metrics
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days_back)
        
        # Build base query
        query = self.db.query(OnboardingProgress).filter(
            OnboardingProgress.created_at >= cutoff_date
        )
        
        if company_id:
            # For specific company, get their invited companies' progress
            invited_companies = self.db.query(SupplierInvitation.accepting_company_id).filter(
                and_(
                    SupplierInvitation.inviting_company_id == company_id,
                    SupplierInvitation.status == InvitationStatus.ACCEPTED.value,
                    SupplierInvitation.accepting_company_id.isnot(None)
                )
            ).subquery()
            
            query = query.filter(OnboardingProgress.company_id.in_(invited_companies))
        
        progress_records = query.all()
        
        # Calculate stage distribution
        stage_counts = {}
        total_records = len(progress_records)
        
        for stage in OnboardingStage:
            count = len([p for p in progress_records if p.current_stage == stage.value])
            stage_counts[stage.value] = {
                "count": count,
                "percentage": count / total_records if total_records > 0 else 0
            }
        
        # Calculate conversion rates between stages
        conversion_rates = self._calculate_stage_conversion_rates(progress_records)
        
        # Calculate average completion times
        completion_times = self._calculate_completion_times(progress_records)
        
        # Calculate funnel metrics
        funnel_metrics = self._calculate_funnel_metrics(progress_records)
        
        return {
            "total_companies_onboarding": total_records,
            "stage_distribution": stage_counts,
            "conversion_rates": conversion_rates,
            "average_completion_times": completion_times,
            "funnel_metrics": funnel_metrics,
            "analysis_period_days": days_back
        }
    
    def get_stage_order(self, stage: str) -> int:
        """Get numeric order of onboarding stage."""
        return OnboardingStage.get_stage_order(stage)
    
    def track_milestone_completion(
        self,
        company_id: int,
        milestone: str,
        completion_data: Dict[str, Any]
    ) -> None:
        """
        Track completion of specific onboarding milestones.
        
        Args:
            company_id: ID of company
            milestone: Milestone identifier
            completion_data: Additional data about milestone completion
        """
        logger.info(
            "Tracking milestone completion",
            company_id=company_id,
            milestone=milestone
        )
        
        progress = self.get_onboarding_progress(company_id)
        if not progress:
            logger.warning(
                "No onboarding progress found for milestone tracking",
                company_id=company_id
            )
            return
        
        # Update milestone data
        if not progress.milestone_data:
            progress.milestone_data = {}
        
        progress.milestone_data[milestone] = {
            "completed_at": datetime.utcnow().isoformat(),
            "data": completion_data
        }
        
        progress.updated_at = datetime.utcnow()
        self.db.commit()
        
        logger.info(
            "Milestone completion tracked",
            company_id=company_id,
            milestone=milestone
        )
    
    def get_onboarding_funnel_data(
        self,
        company_id: Optional[int] = None,
        days_back: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Get onboarding funnel data for visualization.
        
        Args:
            company_id: Optional company filter
            days_back: Number of days to analyze
            
        Returns:
            List of funnel stage data
        """
        return self.query_service.get_onboarding_funnel_data(
            company_id=company_id,
            timeframe=self._days_to_timeframe(days_back)
        )
    
    def get_companies_by_stage(
        self,
        stage: OnboardingStage,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get companies currently in a specific onboarding stage.
        
        Args:
            stage: Onboarding stage to filter by
            limit: Maximum number of companies to return
            
        Returns:
            List of company data with progress information
        """
        results = self.db.query(
            OnboardingProgress,
            Company.name.label('company_name')
        ).join(
            Company, OnboardingProgress.company_id == Company.id
        ).filter(
            OnboardingProgress.current_stage == stage.value
        ).limit(limit).all()
        
        companies = []
        for progress, company_name in results:
            companies.append({
                "company_id": progress.company_id,
                "company_name": company_name,
                "current_stage": progress.current_stage,
                "completion_percentage": progress.stage_completion_percentage,
                "created_at": progress.created_at.isoformat(),
                "updated_at": progress.updated_at.isoformat(),
                "days_in_stage": (datetime.utcnow() - progress.updated_at).days
            })
        
        return companies
    
    def _is_stage_progression(self, old_stage: str, new_stage: str) -> bool:
        """Check if stage change represents forward progression."""
        old_order = OnboardingStage.get_stage_order(old_stage)
        new_order = OnboardingStage.get_stage_order(new_stage)
        return new_order > old_order
    
    def _record_stage_milestone(
        self,
        progress: OnboardingProgress,
        old_stage: str,
        new_stage: str
    ) -> None:
        """Record stage progression milestone."""
        if not progress.milestone_data:
            progress.milestone_data = {}
        
        milestone_key = f"stage_progression_{old_stage}_to_{new_stage}"
        progress.milestone_data[milestone_key] = {
            "completed_at": datetime.utcnow().isoformat(),
            "old_stage": old_stage,
            "new_stage": new_stage
        }
    
    def _calculate_stage_conversion_rates(
        self,
        progress_records: List[OnboardingProgress]
    ) -> Dict[str, float]:
        """Calculate conversion rates between onboarding stages."""
        stage_counts = {}
        
        # Count companies in each stage
        for record in progress_records:
            stage = record.current_stage
            stage_counts[stage] = stage_counts.get(stage, 0) + 1
        
        # Calculate conversion rates
        conversion_rates = {}
        stages = list(OnboardingStage)
        
        for i in range(len(stages) - 1):
            current_stage = stages[i]
            next_stage = stages[i + 1]
            
            current_count = stage_counts.get(current_stage.value, 0)
            next_count = stage_counts.get(next_stage.value, 0)
            
            # Calculate how many progressed from current to next or beyond
            progressed_count = sum(
                stage_counts.get(stage.value, 0)
                for stage in stages[i + 1:]
            )
            
            total_in_current = current_count + progressed_count
            conversion_rate = progressed_count / total_in_current if total_in_current > 0 else 0
            
            conversion_rates[f"{current_stage.value}_to_{next_stage.value}"] = conversion_rate
        
        return conversion_rates
    
    def _calculate_completion_times(
        self,
        progress_records: List[OnboardingProgress]
    ) -> Dict[str, float]:
        """Calculate average completion times for each stage."""
        completion_times = {}
        
        for stage in OnboardingStage:
            stage_records = [p for p in progress_records if p.current_stage == stage.value]
            
            if stage_records:
                times = []
                for record in stage_records:
                    time_in_stage = (datetime.utcnow() - record.updated_at).total_seconds() / 86400  # days
                    times.append(time_in_stage)
                
                completion_times[stage.value] = sum(times) / len(times)
            else:
                completion_times[stage.value] = 0
        
        return completion_times
    
    def _calculate_funnel_metrics(
        self,
        progress_records: List[OnboardingProgress]
    ) -> Dict[str, Any]:
        """Calculate overall funnel metrics."""
        if not progress_records:
            return {"drop_off_rate": 0, "completion_rate": 0, "average_time_to_complete": 0}
        
        total_started = len(progress_records)
        completed = len([p for p in progress_records if p.current_stage == OnboardingStage.ACTIVE_SUPPLIER.value])
        
        completion_rate = completed / total_started if total_started > 0 else 0
        drop_off_rate = 1 - completion_rate
        
        # Calculate average time to complete for completed companies
        completed_records = [p for p in progress_records if p.current_stage == OnboardingStage.ACTIVE_SUPPLIER.value]
        if completed_records:
            completion_times = [(p.updated_at - p.created_at).total_seconds() / 86400 for p in completed_records]
            avg_completion_time = sum(completion_times) / len(completion_times)
        else:
            avg_completion_time = 0
        
        return {
            "drop_off_rate": drop_off_rate,
            "completion_rate": completion_rate,
            "average_time_to_complete_days": avg_completion_time
        }
    
    def _days_to_timeframe(self, days: int):
        """Convert days to AnalyticsTimeframe enum."""
        from ..models.enums import AnalyticsTimeframe
        
        if days <= 7:
            return AnalyticsTimeframe.LAST_7_DAYS
        elif days <= 30:
            return AnalyticsTimeframe.LAST_30_DAYS
        elif days <= 90:
            return AnalyticsTimeframe.LAST_90_DAYS
        elif days <= 180:
            return AnalyticsTimeframe.LAST_6_MONTHS
        elif days <= 365:
            return AnalyticsTimeframe.LAST_YEAR
        else:
            return AnalyticsTimeframe.ALL_TIME
