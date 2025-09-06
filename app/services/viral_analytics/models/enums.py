"""
Enums and constants for viral analytics.

This module contains all enumeration types used throughout the viral
analytics system.
"""

from enum import Enum


class OnboardingStage(str, Enum):
    """Onboarding stages in the supplier journey."""
    INVITED = "invited"
    REGISTERED = "registered"
    PROFILE_COMPLETED = "profile_completed"
    DOCUMENTS_UPLOADED = "documents_uploaded"
    VERIFICATION_PENDING = "verification_pending"
    VERIFICATION_COMPLETED = "verification_completed"
    FIRST_ORDER_PLACED = "first_order_placed"
    ACTIVE_SUPPLIER = "active_supplier"
    
    @classmethod
    def get_stage_order(cls, stage: str) -> int:
        """Get numeric order of onboarding stage."""
        stage_order = {
            cls.INVITED: 1,
            cls.REGISTERED: 2,
            cls.PROFILE_COMPLETED: 3,
            cls.DOCUMENTS_UPLOADED: 4,
            cls.VERIFICATION_PENDING: 5,
            cls.VERIFICATION_COMPLETED: 6,
            cls.FIRST_ORDER_PLACED: 7,
            cls.ACTIVE_SUPPLIER: 8
        }
        return stage_order.get(stage, 0)
    
    @classmethod
    def get_completion_stages(cls) -> list['OnboardingStage']:
        """Get stages that represent completion milestones."""
        return [
            cls.REGISTERED,
            cls.PROFILE_COMPLETED,
            cls.VERIFICATION_COMPLETED,
            cls.FIRST_ORDER_PLACED,
            cls.ACTIVE_SUPPLIER
        ]


class InvitationStatus(str, Enum):
    """Status of supplier invitations."""
    PENDING = "pending"
    ACCEPTED = "accepted"
    EXPIRED = "expired"
    DECLINED = "declined"
    CANCELLED = "cancelled"
    
    @classmethod
    def get_active_statuses(cls) -> list['InvitationStatus']:
        """Get statuses that represent active invitations."""
        return [cls.PENDING, cls.ACCEPTED]
    
    @classmethod
    def get_completed_statuses(cls) -> list['InvitationStatus']:
        """Get statuses that represent completed invitations."""
        return [cls.ACCEPTED, cls.DECLINED, cls.CANCELLED]


class ViralMetricType(str, Enum):
    """Types of viral metrics that can be calculated."""
    VIRAL_COEFFICIENT = "viral_coefficient"
    NETWORK_GROWTH_RATE = "network_growth_rate"
    INVITATION_CONVERSION_RATE = "invitation_conversion_rate"
    ONBOARDING_COMPLETION_RATE = "onboarding_completion_rate"
    CASCADE_DEPTH = "cascade_depth"
    CASCADE_WIDTH = "cascade_width"
    NETWORK_DENSITY = "network_density"
    VIRAL_VELOCITY = "viral_velocity"
    
    @classmethod
    def get_primary_metrics(cls) -> list['ViralMetricType']:
        """Get primary viral metrics for dashboard display."""
        return [
            cls.VIRAL_COEFFICIENT,
            cls.NETWORK_GROWTH_RATE,
            cls.INVITATION_CONVERSION_RATE,
            cls.ONBOARDING_COMPLETION_RATE
        ]
    
    @classmethod
    def get_network_metrics(cls) -> list['ViralMetricType']:
        """Get network structure metrics."""
        return [
            cls.CASCADE_DEPTH,
            cls.CASCADE_WIDTH,
            cls.NETWORK_DENSITY,
            cls.VIRAL_VELOCITY
        ]


class CascadeNodeType(str, Enum):
    """Types of nodes in viral cascade."""
    ROOT = "root"           # Original inviter (no parent)
    BRANCH = "branch"       # Has both parent and children
    LEAF = "leaf"          # Has parent but no children
    ISOLATED = "isolated"   # No parent or children
    
    @classmethod
    def determine_node_type(cls, has_parent: bool, has_children: bool) -> 'CascadeNodeType':
        """Determine node type based on relationships."""
        if not has_parent and not has_children:
            return cls.ISOLATED
        elif not has_parent and has_children:
            return cls.ROOT
        elif has_parent and has_children:
            return cls.BRANCH
        else:  # has_parent and not has_children
            return cls.LEAF


class AnalyticsTimeframe(str, Enum):
    """Time frames for analytics calculations."""
    LAST_7_DAYS = "last_7_days"
    LAST_30_DAYS = "last_30_days"
    LAST_90_DAYS = "last_90_days"
    LAST_6_MONTHS = "last_6_months"
    LAST_YEAR = "last_year"
    ALL_TIME = "all_time"
    
    @classmethod
    def get_days(cls, timeframe: 'AnalyticsTimeframe') -> int:
        """Get number of days for timeframe."""
        timeframe_days = {
            cls.LAST_7_DAYS: 7,
            cls.LAST_30_DAYS: 30,
            cls.LAST_90_DAYS: 90,
            cls.LAST_6_MONTHS: 180,
            cls.LAST_YEAR: 365,
            cls.ALL_TIME: 0  # Special case for all time
        }
        return timeframe_days.get(timeframe, 30)


class ViralChampionTier(str, Enum):
    """Tiers for viral champions based on performance."""
    PLATINUM = "platinum"    # Top 1% of inviters
    GOLD = "gold"           # Top 5% of inviters
    SILVER = "silver"       # Top 15% of inviters
    BRONZE = "bronze"       # Top 30% of inviters
    STANDARD = "standard"   # Everyone else
    
    @classmethod
    def get_tier_thresholds(cls) -> dict['ViralChampionTier', float]:
        """Get percentile thresholds for each tier."""
        return {
            cls.PLATINUM: 0.99,
            cls.GOLD: 0.95,
            cls.SILVER: 0.85,
            cls.BRONZE: 0.70,
            cls.STANDARD: 0.0
        }
    
    @classmethod
    def determine_tier(cls, percentile: float) -> 'ViralChampionTier':
        """Determine tier based on percentile ranking."""
        thresholds = cls.get_tier_thresholds()
        
        for tier, threshold in thresholds.items():
            if percentile >= threshold:
                return tier
        
        return cls.STANDARD
