"""
Optimized database query service for viral analytics.

This module provides efficient, reusable database queries for viral analytics,
addressing N+1 query problems and providing optimized data access patterns.
"""

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session, joinedload, selectinload
from sqlalchemy import func, and_, or_, desc, asc, text
from functools import lru_cache

from app.models.viral_analytics import (
    SupplierInvitation,
    OnboardingProgress,
    ViralCascadeNode
)
from app.models.company import Company
from ..models.enums import OnboardingStage, InvitationStatus, AnalyticsTimeframe


class AnalyticsQueryService:
    """Optimized database queries for viral analytics."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_invitation_stats(
        self, 
        company_id: Optional[int] = None,
        timeframe: AnalyticsTimeframe = AnalyticsTimeframe.LAST_30_DAYS
    ) -> Dict[str, int]:
        """
        Get invitation statistics with optimized queries.
        
        Args:
            company_id: Optional company filter
            timeframe: Time period for analysis
            
        Returns:
            Dictionary with invitation counts by status
        """
        query = self.db.query(
            SupplierInvitation.status,
            func.count(SupplierInvitation.id).label('count')
        )
        
        # Apply filters
        if company_id:
            query = query.filter(SupplierInvitation.inviting_company_id == company_id)
        
        if timeframe != AnalyticsTimeframe.ALL_TIME:
            days = AnalyticsTimeframe.get_days(timeframe)
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            query = query.filter(SupplierInvitation.created_at >= cutoff_date)
        
        # Group and execute
        results = query.group_by(SupplierInvitation.status).all()
        
        # Convert to dictionary
        stats = {status.value: 0 for status in InvitationStatus}
        for status, count in results:
            stats[status] = count
        
        return stats
    
    def get_onboarding_funnel_data(
        self,
        company_id: Optional[int] = None,
        timeframe: AnalyticsTimeframe = AnalyticsTimeframe.LAST_30_DAYS
    ) -> List[Dict[str, Any]]:
        """
        Get onboarding funnel data with stage progression.
        
        Args:
            company_id: Optional company filter
            timeframe: Time period for analysis
            
        Returns:
            List of stage data with counts and conversion rates
        """
        query = self.db.query(
            OnboardingProgress.current_stage,
            func.count(OnboardingProgress.id).label('count'),
            func.avg(OnboardingProgress.stage_completion_percentage).label('avg_completion')
        )
        
        # Apply filters
        if company_id:
            query = query.join(SupplierInvitation).filter(
                SupplierInvitation.inviting_company_id == company_id
            )
        
        if timeframe != AnalyticsTimeframe.ALL_TIME:
            days = AnalyticsTimeframe.get_days(timeframe)
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            query = query.filter(OnboardingProgress.created_at >= cutoff_date)
        
        # Group and order by stage
        results = query.group_by(OnboardingProgress.current_stage).all()
        
        # Convert to structured data
        funnel_data = []
        total_started = sum(count for _, count, _ in results)
        
        for stage, count, avg_completion in results:
            stage_order = OnboardingStage.get_stage_order(stage)
            conversion_rate = count / total_started if total_started > 0 else 0
            
            funnel_data.append({
                "stage": stage,
                "stage_order": stage_order,
                "count": count,
                "conversion_rate": conversion_rate,
                "avg_completion_percentage": float(avg_completion or 0),
                "drop_off_rate": 1 - conversion_rate
            })
        
        # Sort by stage order
        return sorted(funnel_data, key=lambda x: x["stage_order"])
    
    def get_cascade_hierarchy_data(
        self,
        root_company_id: int,
        max_depth: int = 10
    ) -> Dict[int, List[Dict[str, Any]]]:
        """
        Get cascade hierarchy data efficiently with single query.
        
        Args:
            root_company_id: Root company for cascade
            max_depth: Maximum depth to retrieve
            
        Returns:
            Dictionary mapping depth to list of node data
        """
        # Use recursive CTE for efficient hierarchy retrieval
        cte_query = text("""
            WITH RECURSIVE cascade_tree AS (
                -- Base case: root node
                SELECT 
                    vcn.id,
                    vcn.company_id,
                    c.name as company_name,
                    vcn.parent_cascade_node_id,
                    vcn.depth,
                    vcn.total_invitations_sent,
                    vcn.total_invitations_accepted,
                    vcn.viral_coefficient,
                    vcn.created_at,
                    0 as level
                FROM viral_cascade_nodes vcn
                JOIN companies c ON vcn.company_id = c.id
                WHERE vcn.company_id = :root_company_id
                
                UNION ALL
                
                -- Recursive case: children
                SELECT 
                    vcn.id,
                    vcn.company_id,
                    c.name as company_name,
                    vcn.parent_cascade_node_id,
                    vcn.depth,
                    vcn.total_invitations_sent,
                    vcn.total_invitations_accepted,
                    vcn.viral_coefficient,
                    vcn.created_at,
                    ct.level + 1
                FROM viral_cascade_nodes vcn
                JOIN companies c ON vcn.company_id = c.id
                JOIN cascade_tree ct ON vcn.parent_cascade_node_id = ct.id
                WHERE ct.level < :max_depth
            )
            SELECT * FROM cascade_tree ORDER BY level, created_at
        """)
        
        results = self.db.execute(
            cte_query, 
            {"root_company_id": root_company_id, "max_depth": max_depth}
        ).fetchall()
        
        # Group by level
        hierarchy = {}
        for row in results:
            level = row.level
            if level not in hierarchy:
                hierarchy[level] = []
            
            hierarchy[level].append({
                "id": row.id,
                "company_id": row.company_id,
                "company_name": row.company_name,
                "parent_id": row.parent_cascade_node_id,
                "depth": row.depth,
                "invitations_sent": row.total_invitations_sent,
                "invitations_accepted": row.total_invitations_accepted,
                "viral_coefficient": float(row.viral_coefficient or 0),
                "created_at": row.created_at,
                "level": level
            })
        
        return hierarchy
    
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
            Dictionary with comprehensive company stats
        """
        # Build time filter
        time_filter = None
        if timeframe != AnalyticsTimeframe.ALL_TIME:
            days = AnalyticsTimeframe.get_days(timeframe)
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            time_filter = cutoff_date
        
        # Get invitation stats
        invitation_query = self.db.query(
            func.count(SupplierInvitation.id).label('total_sent'),
            func.count(
                func.nullif(SupplierInvitation.status, InvitationStatus.PENDING.value)
            ).label('total_responded'),
            func.count(
                func.nullif(SupplierInvitation.status, InvitationStatus.ACCEPTED.value)
            ).label('total_accepted')
        ).filter(SupplierInvitation.inviting_company_id == company_id)
        
        if time_filter:
            invitation_query = invitation_query.filter(
                SupplierInvitation.created_at >= time_filter
            )
        
        inv_stats = invitation_query.first()
        
        # Get cascade node data
        cascade_node = self.db.query(ViralCascadeNode).filter(
            ViralCascadeNode.company_id == company_id
        ).first()
        
        # Get onboarding stats
        onboarding_query = self.db.query(
            func.count(OnboardingProgress.id).label('total_onboarding'),
            func.count(
                func.case(
                    [(OnboardingProgress.current_stage == OnboardingStage.ACTIVE_SUPPLIER.value, 1)]
                )
            ).label('completed_onboarding')
        ).join(SupplierInvitation).filter(
            SupplierInvitation.inviting_company_id == company_id
        )
        
        if time_filter:
            onboarding_query = onboarding_query.filter(
                OnboardingProgress.created_at >= time_filter
            )
        
        onb_stats = onboarding_query.first()
        
        # Calculate metrics
        total_sent = inv_stats.total_sent or 0
        total_accepted = inv_stats.total_accepted or 0
        total_onboarding = onb_stats.total_onboarding or 0
        completed_onboarding = onb_stats.completed_onboarding or 0
        
        conversion_rate = total_accepted / total_sent if total_sent > 0 else 0
        completion_rate = completed_onboarding / total_onboarding if total_onboarding > 0 else 0
        viral_coefficient = cascade_node.viral_coefficient if cascade_node else 0
        
        return {
            "company_id": company_id,
            "total_invitations_sent": total_sent,
            "total_invitations_accepted": total_accepted,
            "total_suppliers_onboarded": total_onboarding,
            "completed_onboarding": completed_onboarding,
            "invitation_conversion_rate": conversion_rate,
            "onboarding_completion_rate": completion_rate,
            "viral_coefficient": float(viral_coefficient or 0),
            "cascade_depth": cascade_node.depth if cascade_node else 0,
            "cascade_node_id": cascade_node.id if cascade_node else None
        }
    
    def get_time_series_data(
        self,
        metric_type: str,
        timeframe: AnalyticsTimeframe = AnalyticsTimeframe.LAST_30_DAYS,
        company_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get time series data for viral metrics.
        
        Args:
            metric_type: Type of metric ('invitations', 'acceptances', 'onboardings')
            timeframe: Time period for analysis
            company_id: Optional company filter
            
        Returns:
            List of time series data points
        """
        days = AnalyticsTimeframe.get_days(timeframe)
        if days == 0:  # ALL_TIME
            days = 365  # Default to 1 year for all time
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Choose appropriate model and date field
        if metric_type == "invitations":
            model = SupplierInvitation
            date_field = SupplierInvitation.created_at
            company_filter = SupplierInvitation.inviting_company_id == company_id
        elif metric_type == "acceptances":
            model = SupplierInvitation
            date_field = SupplierInvitation.accepted_at
            company_filter = SupplierInvitation.inviting_company_id == company_id
        elif metric_type == "onboardings":
            model = OnboardingProgress
            date_field = OnboardingProgress.created_at
            company_filter = True  # Handle via join
        else:
            raise ValueError(f"Unknown metric type: {metric_type}")
        
        # Build query
        query = self.db.query(
            func.date(date_field).label('date'),
            func.count(model.id).label('count')
        ).filter(date_field >= cutoff_date)
        
        # Apply company filter
        if company_id and metric_type == "onboardings":
            query = query.join(SupplierInvitation).filter(
                SupplierInvitation.inviting_company_id == company_id
            )
        elif company_id:
            query = query.filter(company_filter)
        
        # Group by date
        results = query.group_by(func.date(date_field)).order_by(func.date(date_field)).all()
        
        # Convert to time series format
        time_series = []
        for date_val, count in results:
            time_series.append({
                "date": date_val.isoformat(),
                "value": count,
                "metric_type": metric_type
            })
        
        return time_series
    
    @lru_cache(maxsize=100)
    def get_top_performers(
        self,
        metric_type: str,
        limit: int = 10,
        timeframe_days: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Get top performing companies with caching.
        
        Args:
            metric_type: Type of performance metric
            limit: Number of top performers to return
            timeframe_days: Days to look back
            
        Returns:
            List of top performer data
        """
        cutoff_date = datetime.utcnow() - timedelta(days=timeframe_days)
        
        if metric_type == "viral_coefficient":
            query = self.db.query(
                ViralCascadeNode.company_id,
                Company.name.label('company_name'),
                ViralCascadeNode.viral_coefficient
            ).join(Company).filter(
                ViralCascadeNode.updated_at >= cutoff_date
            ).order_by(desc(ViralCascadeNode.viral_coefficient)).limit(limit)
            
        elif metric_type == "invitations_sent":
            query = self.db.query(
                SupplierInvitation.inviting_company_id.label('company_id'),
                Company.name.label('company_name'),
                func.count(SupplierInvitation.id).label('invitations_sent')
            ).join(Company, SupplierInvitation.inviting_company_id == Company.id).filter(
                SupplierInvitation.created_at >= cutoff_date
            ).group_by(
                SupplierInvitation.inviting_company_id, Company.name
            ).order_by(desc(func.count(SupplierInvitation.id))).limit(limit)
            
        else:
            raise ValueError(f"Unknown metric type: {metric_type}")
        
        results = query.all()
        
        # Convert to standardized format
        performers = []
        for row in results:
            performer_data = {
                "company_id": row.company_id,
                "company_name": row.company_name,
                "metric_type": metric_type
            }
            
            if metric_type == "viral_coefficient":
                performer_data["value"] = float(row.viral_coefficient or 0)
            elif metric_type == "invitations_sent":
                performer_data["value"] = row.invitations_sent
            
            performers.append(performer_data)
        
        return performers
    
    def clear_cache(self):
        """Clear query cache."""
        self.get_top_performers.cache_clear()
