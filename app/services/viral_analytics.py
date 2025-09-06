"""
Viral onboarding analytics service for the Common supply chain platform.
"""
from typing import Optional, List, Dict, Any, Tuple
from uuid import UUID
from datetime import datetime, timedelta
from decimal import Decimal
from dataclasses import dataclass, field
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc, asc

from app.models.viral_analytics import (
    SupplierInvitation,
    OnboardingProgress,
    NetworkGrowthMetric,
    ViralCascadeNode,
    InvitationStatus,
    OnboardingStage
)
from app.models.company import Company
from app.models.user import User
from app.models.business_relationship import BusinessRelationship
from app.models.purchase_order import PurchaseOrder
from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class CascadeMetrics:
    """Viral cascade metrics for analytics."""
    total_invitations_sent: int = 0
    total_invitations_accepted: int = 0
    acceptance_rate: float = 0.0
    total_companies_onboarded: int = 0
    onboarding_levels: Dict[int, int] = field(default_factory=dict)
    top_inviters: List[Dict[str, Any]] = field(default_factory=list)
    recent_onboardings: List[Dict[str, Any]] = field(default_factory=list)
    network_growth_rate: float = 0.0
    viral_coefficient: float = 0.0
    average_cascade_depth: float = 0.0


@dataclass
class NetworkEffectMetrics:
    """Network effect metrics for viral analysis."""
    total_nodes: int = 0
    total_edges: int = 0
    network_density: float = 0.0
    clustering_coefficient: float = 0.0
    average_path_length: float = 0.0
    viral_champions: List[Dict[str, Any]] = field(default_factory=list)
    growth_hotspots: List[Dict[str, Any]] = field(default_factory=list)
    conversion_funnel: Dict[str, Any] = field(default_factory=dict)


@dataclass
class OnboardingChainVisualization:
    """Onboarding chain visualization data."""
    nodes: List[Dict[str, Any]] = field(default_factory=list)
    edges: List[Dict[str, Any]] = field(default_factory=list)
    levels: Dict[int, List[Dict[str, Any]]] = field(default_factory=dict)
    root_companies: List[Dict[str, Any]] = field(default_factory=list)
    metrics: CascadeMetrics = field(default_factory=CascadeMetrics)


class ViralAnalyticsService:
    """
    Service for viral onboarding analytics and network effect measurement.
    
    Features:
    - Onboarding cascade tracking and analytics
    - Network effect metrics calculation
    - Onboarding chain visualization
    - Viral adoption reporting dashboard data
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def track_supplier_invitation(
        self,
        inviting_company_id: UUID,
        inviting_user_id: UUID,
        invited_email: str,
        invited_company_name: Optional[str] = None,
        invitation_source: str = "dashboard",
        invitation_context: Optional[Dict[str, Any]] = None
    ) -> SupplierInvitation:
        """
        Track a new supplier invitation for viral analytics.
        
        Args:
            inviting_company_id: Company sending the invitation
            inviting_user_id: User sending the invitation
            invited_email: Email of the invited supplier
            invited_company_name: Name of the invited company
            invitation_source: Source of the invitation
            invitation_context: Additional context for analytics
            
        Returns:
            Created SupplierInvitation record
        """
        try:
            # Determine invitation level and parent
            parent_invitation = self._find_parent_invitation(inviting_company_id)
            invitation_level = 1 if not parent_invitation else parent_invitation.invitation_level + 1
            root_inviter_company_id = (
                parent_invitation.root_inviter_company_id if parent_invitation
                else inviting_company_id
            )
            
            # Create invitation record
            invitation = SupplierInvitation(
                inviting_company_id=inviting_company_id,
                inviting_user_id=inviting_user_id,
                invited_email=invited_email,
                invited_company_name=invited_company_name,
                parent_invitation_id=parent_invitation.id if parent_invitation else None,
                invitation_level=invitation_level,
                root_inviter_company_id=root_inviter_company_id,
                invitation_source=invitation_source,
                invitation_context=invitation_context or {},
                expires_at=datetime.utcnow() + timedelta(days=30)  # 30-day expiry
            )
            
            self.db.add(invitation)
            self.db.commit()
            self.db.refresh(invitation)
            
            # Update cascade node metrics
            self._update_cascade_node_metrics(inviting_company_id)
            
            logger.info(
                "Supplier invitation tracked",
                invitation_id=str(invitation.id),
                inviting_company_id=str(inviting_company_id),
                invited_email=invited_email,
                invitation_level=invitation_level
            )
            
            return invitation
            
        except Exception as e:
            logger.error(
                "Failed to track supplier invitation",
                inviting_company_id=str(inviting_company_id),
                invited_email=invited_email,
                error=str(e)
            )
            raise
    
    def track_invitation_acceptance(
        self,
        invitation_id: UUID,
        registered_company_id: UUID,
        business_relationship_id: UUID
    ) -> OnboardingProgress:
        """
        Track invitation acceptance and create onboarding progress.
        
        Args:
            invitation_id: ID of the accepted invitation
            registered_company_id: ID of the newly registered company
            business_relationship_id: ID of the created business relationship
            
        Returns:
            Created OnboardingProgress record
        """
        try:
            # Update invitation status
            invitation = self.db.query(SupplierInvitation).filter(
                SupplierInvitation.id == invitation_id
            ).first()
            
            if not invitation:
                raise ValueError(f"Invitation {invitation_id} not found")
            
            invitation.status = InvitationStatus.ACCEPTED.value
            invitation.accepted_at = datetime.utcnow()
            invitation.registered_company_id = registered_company_id
            invitation.business_relationship_id = business_relationship_id
            
            # Create onboarding progress
            onboarding_progress = OnboardingProgress(
                company_id=registered_company_id,
                invitation_id=invitation_id,
                current_stage=OnboardingStage.REGISTERED.value,
                invited_at=invitation.created_at,
                registered_at=datetime.utcnow(),
                stages_completed=[{
                    "stage": OnboardingStage.INVITED.value,
                    "completed_at": invitation.created_at.isoformat()
                }, {
                    "stage": OnboardingStage.REGISTERED.value,
                    "completed_at": datetime.utcnow().isoformat()
                }]
            )
            
            # Calculate time to register
            time_diff = datetime.utcnow() - invitation.created_at
            onboarding_progress.time_to_register_hours = time_diff.total_seconds() / 3600
            
            self.db.add(onboarding_progress)
            self.db.commit()
            self.db.refresh(onboarding_progress)
            
            # Update cascade node
            self._create_or_update_cascade_node(
                company_id=registered_company_id,
                parent_company_id=invitation.inviting_company_id,
                root_company_id=invitation.root_inviter_company_id,
                cascade_level=invitation.invitation_level
            )
            
            # Update parent company viral metrics
            self._update_viral_metrics(invitation.inviting_company_id)
            
            logger.info(
                "Invitation acceptance tracked",
                invitation_id=str(invitation_id),
                registered_company_id=str(registered_company_id),
                time_to_register_hours=onboarding_progress.time_to_register_hours
            )
            
            return onboarding_progress
            
        except Exception as e:
            logger.error(
                "Failed to track invitation acceptance",
                invitation_id=str(invitation_id),
                error=str(e)
            )
            raise
    
    def update_onboarding_stage(
        self,
        company_id: UUID,
        new_stage: OnboardingStage,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Update onboarding stage for a company.
        
        Args:
            company_id: Company ID
            new_stage: New onboarding stage
            metadata: Additional metadata for the stage
        """
        try:
            progress = self.db.query(OnboardingProgress).filter(
                OnboardingProgress.company_id == company_id
            ).first()
            
            if not progress:
                # Create progress record if it doesn't exist
                progress = OnboardingProgress(
                    company_id=company_id,
                    current_stage=new_stage.value,
                    stages_completed=[]
                )
                self.db.add(progress)
            
            # Update stage if it's a progression
            current_stage_order = self._get_stage_order(progress.current_stage)
            new_stage_order = self._get_stage_order(new_stage.value)
            
            if new_stage_order > current_stage_order:
                progress.current_stage = new_stage.value
                
                # Add to completed stages
                stage_completion = {
                    "stage": new_stage.value,
                    "completed_at": datetime.utcnow().isoformat()
                }
                if metadata:
                    stage_completion["metadata"] = metadata
                
                if not progress.stages_completed:
                    progress.stages_completed = []
                progress.stages_completed.append(stage_completion)
                
                # Update specific stage timestamps
                now = datetime.utcnow()
                if new_stage == OnboardingStage.PROFILE_COMPLETED:
                    progress.profile_completed_at = now
                elif new_stage == OnboardingStage.FIRST_PO_CREATED:
                    progress.first_po_created_at = now
                    if progress.registered_at:
                        time_diff = now - progress.registered_at
                        progress.time_to_first_po_hours = time_diff.total_seconds() / 3600
                elif new_stage == OnboardingStage.FIRST_PO_CONFIRMED:
                    progress.first_po_confirmed_at = now
                elif new_stage == OnboardingStage.ACTIVE_USER:
                    progress.became_active_at = now
                    if progress.registered_at:
                        time_diff = now - progress.registered_at
                        progress.time_to_active_hours = time_diff.total_seconds() / 3600
            
            self.db.commit()
            
            logger.info(
                "Onboarding stage updated",
                company_id=str(company_id),
                new_stage=new_stage.value,
                previous_stage=progress.current_stage
            )
            
        except Exception as e:
            logger.error(
                "Failed to update onboarding stage",
                company_id=str(company_id),
                new_stage=new_stage.value,
                error=str(e)
            )
            raise
    
    def calculate_cascade_metrics(
        self,
        root_company_id: Optional[UUID] = None,
        time_period_days: int = 30
    ) -> CascadeMetrics:
        """
        Calculate viral cascade metrics.
        
        Args:
            root_company_id: Calculate metrics for specific root company
            time_period_days: Time period for metrics calculation
            
        Returns:
            Comprehensive cascade metrics
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=time_period_days)
            
            # Base query
            base_query = self.db.query(SupplierInvitation)
            if root_company_id:
                base_query = base_query.filter(
                    SupplierInvitation.root_inviter_company_id == root_company_id
                )
            
            # Total invitations
            total_invitations = base_query.filter(
                SupplierInvitation.created_at >= cutoff_date
            ).count()
            
            # Accepted invitations
            accepted_invitations = base_query.filter(
                and_(
                    SupplierInvitation.status == InvitationStatus.ACCEPTED.value,
                    SupplierInvitation.accepted_at >= cutoff_date
                )
            ).count()
            
            # Acceptance rate
            acceptance_rate = (
                (accepted_invitations / total_invitations * 100)
                if total_invitations > 0 else 0.0
            )
            
            # Companies onboarded
            companies_onboarded = base_query.filter(
                and_(
                    SupplierInvitation.status == InvitationStatus.ACCEPTED.value,
                    SupplierInvitation.accepted_at >= cutoff_date,
                    SupplierInvitation.registered_company_id.isnot(None)
                )
            ).count()
            
            # Onboarding levels
            level_stats = self.db.query(
                SupplierInvitation.invitation_level,
                func.count(SupplierInvitation.id)
            ).filter(
                and_(
                    SupplierInvitation.status == InvitationStatus.ACCEPTED.value,
                    SupplierInvitation.accepted_at >= cutoff_date
                )
            ).group_by(SupplierInvitation.invitation_level).all()
            
            onboarding_levels = {level: count for level, count in level_stats}
            
            # Top inviters
            top_inviters = self._get_top_inviters(cutoff_date, limit=10)
            
            # Recent onboardings
            recent_onboardings = self._get_recent_onboardings(limit=20)
            
            # Network growth rate
            network_growth_rate = self._calculate_network_growth_rate(time_period_days)
            
            # Viral coefficient
            viral_coefficient = self._calculate_viral_coefficient(time_period_days)
            
            # Average cascade depth
            avg_depth = self.db.query(func.avg(SupplierInvitation.invitation_level)).filter(
                SupplierInvitation.accepted_at >= cutoff_date
            ).scalar() or 0.0
            
            return CascadeMetrics(
                total_invitations_sent=total_invitations,
                total_invitations_accepted=accepted_invitations,
                acceptance_rate=acceptance_rate,
                total_companies_onboarded=companies_onboarded,
                onboarding_levels=onboarding_levels,
                top_inviters=top_inviters,
                recent_onboardings=recent_onboardings,
                network_growth_rate=network_growth_rate,
                viral_coefficient=viral_coefficient,
                average_cascade_depth=float(avg_depth)
            )
            
        except Exception as e:
            logger.error(
                "Failed to calculate cascade metrics",
                root_company_id=str(root_company_id) if root_company_id else None,
                error=str(e)
            )
            raise

    def _get_stage_order(self, stage: str) -> int:
        """Get the order of an onboarding stage."""
        stage_order = {
            OnboardingStage.INVITED.value: 0,
            OnboardingStage.REGISTERED.value: 1,
            OnboardingStage.PROFILE_COMPLETED.value: 2,
            OnboardingStage.FIRST_PO_CREATED.value: 3,
            OnboardingStage.FIRST_PO_CONFIRMED.value: 4,
            OnboardingStage.ACTIVE_USER.value: 5
        }
        return stage_order.get(stage, 0)

    def _create_or_update_cascade_node(
        self,
        company_id: UUID,
        parent_company_id: Optional[UUID],
        root_company_id: UUID,
        cascade_level: int
    ):
        """Create or update a viral cascade node."""
        try:
            node = self.db.query(ViralCascadeNode).filter(
                ViralCascadeNode.company_id == company_id
            ).first()

            if not node:
                # Count position in level
                position_in_level = self.db.query(ViralCascadeNode).filter(
                    and_(
                        ViralCascadeNode.root_company_id == root_company_id,
                        ViralCascadeNode.cascade_level == cascade_level
                    )
                ).count()

                node = ViralCascadeNode(
                    company_id=company_id,
                    parent_company_id=parent_company_id,
                    root_company_id=root_company_id,
                    cascade_level=cascade_level,
                    position_in_level=position_in_level,
                    joined_at=datetime.utcnow()
                )
                self.db.add(node)

            self.db.commit()

        except Exception as e:
            logger.error(
                "Failed to create/update cascade node",
                company_id=str(company_id),
                error=str(e)
            )

    def _update_viral_metrics(self, company_id: UUID):
        """Update viral metrics for a company."""
        try:
            progress = self.db.query(OnboardingProgress).filter(
                OnboardingProgress.company_id == company_id
            ).first()

            if not progress:
                return

            # Count suppliers invited and onboarded
            suppliers_invited = self.db.query(SupplierInvitation).filter(
                SupplierInvitation.inviting_company_id == company_id
            ).count()

            suppliers_onboarded = self.db.query(SupplierInvitation).filter(
                and_(
                    SupplierInvitation.inviting_company_id == company_id,
                    SupplierInvitation.status == InvitationStatus.ACCEPTED.value
                )
            ).count()

            # Update metrics
            progress.suppliers_invited = suppliers_invited
            progress.suppliers_onboarded = suppliers_onboarded
            progress.viral_coefficient = float(suppliers_onboarded)  # Simple viral coefficient

            self.db.commit()

        except Exception as e:
            logger.error(
                "Failed to update viral metrics",
                company_id=str(company_id),
                error=str(e)
            )

    def _get_top_inviters(self, cutoff_date: datetime, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top companies by invitations sent."""
        try:
            results = self.db.query(
                SupplierInvitation.inviting_company_id,
                Company.name,
                func.count(SupplierInvitation.id).label('invitations_sent'),
                func.count(
                    func.nullif(SupplierInvitation.status != InvitationStatus.ACCEPTED.value, True)
                ).label('invitations_accepted')
            ).join(
                Company, Company.id == SupplierInvitation.inviting_company_id
            ).filter(
                SupplierInvitation.created_at >= cutoff_date
            ).group_by(
                SupplierInvitation.inviting_company_id, Company.name
            ).order_by(
                desc('invitations_sent')
            ).limit(limit).all()

            return [
                {
                    "company_id": str(result.inviting_company_id),
                    "company_name": result.name,
                    "invitations_sent": result.invitations_sent,
                    "invitations_accepted": result.invitations_accepted,
                    "conversion_rate": (
                        (result.invitations_accepted / result.invitations_sent * 100)
                        if result.invitations_sent > 0 else 0.0
                    )
                }
                for result in results
            ]

        except Exception as e:
            logger.error("Failed to get top inviters", error=str(e))
            return []

    def _get_recent_onboardings(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent company onboardings."""
        try:
            results = self.db.query(
                SupplierInvitation,
                Company
            ).join(
                Company, Company.id == SupplierInvitation.registered_company_id
            ).filter(
                SupplierInvitation.status == InvitationStatus.ACCEPTED.value
            ).order_by(
                desc(SupplierInvitation.accepted_at)
            ).limit(limit).all()

            return [
                {
                    "company_id": str(company.id),
                    "company_name": company.name,
                    "company_type": company.company_type,
                    "invited_by_company_id": str(invitation.inviting_company_id),
                    "invitation_level": invitation.invitation_level,
                    "accepted_at": invitation.accepted_at.isoformat(),
                    "time_to_accept_hours": (
                        (invitation.accepted_at - invitation.created_at).total_seconds() / 3600
                        if invitation.accepted_at and invitation.created_at else None
                    )
                }
                for invitation, company in results
            ]

        except Exception as e:
            logger.error("Failed to get recent onboardings", error=str(e))
            return []

    def _calculate_network_growth_rate(self, time_period_days: int) -> float:
        """Calculate network growth rate."""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=time_period_days)

            # Companies at start of period
            companies_start = self.db.query(Company).filter(
                Company.created_at < cutoff_date
            ).count()

            # Companies at end of period
            companies_end = self.db.query(Company).count()

            # Growth rate
            if companies_start > 0:
                growth_rate = ((companies_end - companies_start) / companies_start) * 100
            else:
                growth_rate = 0.0

            return growth_rate

        except Exception as e:
            logger.error("Failed to calculate network growth rate", error=str(e))
            return 0.0

    def _calculate_viral_coefficient(self, time_period_days: int) -> float:
        """Calculate viral coefficient."""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=time_period_days)

            # Average invitations per new user
            new_companies = self.db.query(Company).filter(
                Company.created_at >= cutoff_date
            ).count()

            total_invitations = self.db.query(SupplierInvitation).filter(
                SupplierInvitation.created_at >= cutoff_date
            ).count()

            if new_companies > 0:
                viral_coefficient = total_invitations / new_companies
            else:
                viral_coefficient = 0.0

            return viral_coefficient

        except Exception as e:
            logger.error("Failed to calculate viral coefficient", error=str(e))
            return 0.0

    def _get_viral_champions(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get viral champions (top performing companies)."""
        try:
            results = self.db.query(
                ViralCascadeNode,
                Company
            ).join(
                Company, Company.id == ViralCascadeNode.company_id
            ).filter(
                ViralCascadeNode.is_viral_champion == True
            ).order_by(
                desc(ViralCascadeNode.downstream_viral_coefficient),
                desc(ViralCascadeNode.total_downstream_companies)
            ).limit(limit).all()

            return [
                {
                    "company_id": str(company.id),
                    "company_name": company.name,
                    "company_type": company.company_type,
                    "cascade_level": node.cascade_level,
                    "direct_invitations": node.direct_invitations_sent,
                    "direct_conversions": node.direct_invitations_accepted,
                    "conversion_rate": node.direct_conversion_rate,
                    "downstream_companies": node.total_downstream_companies,
                    "viral_coefficient": node.downstream_viral_coefficient
                }
                for node, company in results
            ]

        except Exception as e:
            logger.error("Failed to get viral champions", error=str(e))
            return []

    def _get_growth_hotspots(self, cutoff_date: datetime, limit: int = 10) -> List[Dict[str, Any]]:
        """Get growth hotspots (regions/segments with high growth)."""
        try:
            # Growth by company type
            type_growth = self.db.query(
                Company.company_type,
                func.count(Company.id).label('new_companies')
            ).filter(
                Company.created_at >= cutoff_date
            ).group_by(
                Company.company_type
            ).order_by(
                desc('new_companies')
            ).limit(limit).all()

            return [
                {
                    "segment": result.company_type,
                    "new_companies": result.new_companies,
                    "growth_type": "company_type"
                }
                for result in type_growth
            ]

        except Exception as e:
            logger.error("Failed to get growth hotspots", error=str(e))
            return []

    def _calculate_conversion_funnel(self, cutoff_date: datetime) -> Dict[str, Any]:
        """Calculate conversion funnel metrics."""
        try:
            # Invitations sent
            invitations_sent = self.db.query(SupplierInvitation).filter(
                SupplierInvitation.created_at >= cutoff_date
            ).count()

            # Invitations accepted (registered)
            invitations_accepted = self.db.query(SupplierInvitation).filter(
                and_(
                    SupplierInvitation.created_at >= cutoff_date,
                    SupplierInvitation.status == InvitationStatus.ACCEPTED.value
                )
            ).count()

            # Profile completed
            profiles_completed = self.db.query(OnboardingProgress).filter(
                and_(
                    OnboardingProgress.registered_at >= cutoff_date,
                    OnboardingProgress.profile_completed_at.isnot(None)
                )
            ).count()

            # First PO created
            first_pos_created = self.db.query(OnboardingProgress).filter(
                and_(
                    OnboardingProgress.registered_at >= cutoff_date,
                    OnboardingProgress.first_po_created_at.isnot(None)
                )
            ).count()

            # Active users
            active_users = self.db.query(OnboardingProgress).filter(
                and_(
                    OnboardingProgress.registered_at >= cutoff_date,
                    OnboardingProgress.became_active_at.isnot(None)
                )
            ).count()

            return {
                "invitations_sent": invitations_sent,
                "invitations_accepted": invitations_accepted,
                "profiles_completed": profiles_completed,
                "first_pos_created": first_pos_created,
                "active_users": active_users,
                "acceptance_rate": (
                    (invitations_accepted / invitations_sent * 100)
                    if invitations_sent > 0 else 0.0
                ),
                "profile_completion_rate": (
                    (profiles_completed / invitations_accepted * 100)
                    if invitations_accepted > 0 else 0.0
                ),
                "first_po_rate": (
                    (first_pos_created / invitations_accepted * 100)
                    if invitations_accepted > 0 else 0.0
                ),
                "activation_rate": (
                    (active_users / invitations_accepted * 100)
                    if invitations_accepted > 0 else 0.0
                )
            }

        except Exception as e:
            logger.error("Failed to calculate conversion funnel", error=str(e))
            return {}

    def _find_parent_invitation(self, company_id: UUID) -> Optional[SupplierInvitation]:
        """Find the parent invitation for a company."""
        # Look for invitation that resulted in this company's registration
        return self.db.query(SupplierInvitation).filter(
            and_(
                SupplierInvitation.registered_company_id == company_id,
                SupplierInvitation.status == InvitationStatus.ACCEPTED.value
            )
        ).first()

    def _update_cascade_node_metrics(self, company_id: UUID):
        """Update cascade node metrics for a company."""
        try:
            node = self.db.query(ViralCascadeNode).filter(
                ViralCascadeNode.company_id == company_id
            ).first()

            if not node:
                # Create node if it doesn't exist
                node = ViralCascadeNode(
                    company_id=company_id,
                    cascade_level=0,  # Will be updated when we have more info
                    position_in_level=0,
                    joined_at=datetime.utcnow()
                )
                self.db.add(node)
                self.db.commit()
                self.db.refresh(node)

            # Count direct invitations
            invitations_sent = self.db.query(SupplierInvitation).filter(
                SupplierInvitation.inviting_company_id == company_id
            ).count()

            invitations_accepted = self.db.query(SupplierInvitation).filter(
                and_(
                    SupplierInvitation.inviting_company_id == company_id,
                    SupplierInvitation.status == InvitationStatus.ACCEPTED.value
                )
            ).count()

            # Update metrics
            node.direct_invitations_sent = invitations_sent
            node.direct_invitations_accepted = invitations_accepted
            node.direct_conversion_rate = (
                (invitations_accepted / invitations_sent)
                if invitations_sent > 0 else 0.0
            )

            # Update viral champion status
            node.is_viral_champion = (
                invitations_accepted >= 5 and node.direct_conversion_rate >= 0.5
            )

            self.db.commit()

        except Exception as e:
            logger.error(
                "Failed to update cascade node metrics",
                company_id=str(company_id),
                error=str(e)
            )

    def calculate_network_effect_metrics(
        self,
        time_period_days: int = 90
    ) -> NetworkEffectMetrics:
        """
        Calculate network effect metrics for viral analysis.

        Args:
            time_period_days: Time period for analysis

        Returns:
            Comprehensive network effect metrics
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=time_period_days)

            # Total nodes (companies)
            total_nodes = self.db.query(Company).count()

            # Total edges (business relationships)
            total_edges = self.db.query(BusinessRelationship).filter(
                BusinessRelationship.status == "active"
            ).count()

            # Network density
            max_possible_edges = total_nodes * (total_nodes - 1) / 2
            network_density = (
                total_edges / max_possible_edges if max_possible_edges > 0 else 0.0
            )

            # Viral champions (top performers)
            viral_champions = self._get_viral_champions(limit=10)

            # Growth hotspots
            growth_hotspots = self._get_growth_hotspots(cutoff_date, limit=10)

            # Conversion funnel
            conversion_funnel = self._calculate_conversion_funnel(cutoff_date)

            return NetworkEffectMetrics(
                total_nodes=total_nodes,
                total_edges=total_edges,
                network_density=network_density,
                viral_champions=viral_champions,
                growth_hotspots=growth_hotspots,
                conversion_funnel=conversion_funnel
            )

        except Exception as e:
            logger.error("Failed to calculate network effect metrics", error=str(e))
            raise

    def generate_onboarding_chain_visualization(
        self,
        root_company_id: Optional[UUID] = None,
        max_depth: int = 5
    ) -> OnboardingChainVisualization:
        """
        Generate onboarding chain visualization data.

        Args:
            root_company_id: Root company for visualization
            max_depth: Maximum depth to visualize

        Returns:
            Visualization data with nodes and edges
        """
        try:
            # Get cascade nodes
            query = self.db.query(ViralCascadeNode).filter(
                ViralCascadeNode.cascade_level <= max_depth
            )

            if root_company_id:
                query = query.filter(
                    ViralCascadeNode.root_company_id == root_company_id
                )

            cascade_nodes = query.all()

            # Build visualization data
            nodes = []
            edges = []
            levels = {}

            for node in cascade_nodes:
                # Node data
                node_data = {
                    "id": str(node.company_id),
                    "company_name": node.company.name if node.company else "Unknown",
                    "company_type": node.company.company_type if node.company else "unknown",
                    "level": node.cascade_level,
                    "position": node.position_in_level,
                    "invitations_sent": node.direct_invitations_sent,
                    "invitations_accepted": node.direct_invitations_accepted,
                    "conversion_rate": node.direct_conversion_rate,
                    "downstream_companies": node.total_downstream_companies,
                    "viral_coefficient": node.downstream_viral_coefficient,
                    "is_viral_champion": node.is_viral_champion,
                    "node_size": node.node_size,
                    "node_color": node.node_color or "#cccccc",
                    "joined_at": node.joined_at.isoformat() if node.joined_at else None
                }
                nodes.append(node_data)

                # Group by level
                if node.cascade_level not in levels:
                    levels[node.cascade_level] = []
                levels[node.cascade_level].append(node_data)

                # Edge data (connection to parent)
                if node.parent_company_id:
                    edge_data = {
                        "id": f"{node.parent_company_id}_{node.company_id}",
                        "source": str(node.parent_company_id),
                        "target": str(node.company_id),
                        "relationship_type": "invitation",
                        "weight": node.direct_conversion_rate
                    }
                    edges.append(edge_data)

            # Get root companies
            root_companies = []
            if not root_company_id:
                root_nodes = [node for node in nodes if node["level"] == 0]
                root_companies = [
                    {
                        "company_id": node["id"],
                        "company_name": node["company_name"],
                        "total_downstream": node["downstream_companies"]
                    }
                    for node in root_nodes
                ]

            # Calculate metrics
            metrics = self.calculate_cascade_metrics(root_company_id)

            return OnboardingChainVisualization(
                nodes=nodes,
                edges=edges,
                levels=levels,
                root_companies=root_companies,
                metrics=metrics
            )

        except Exception as e:
            logger.error(
                "Failed to generate onboarding chain visualization",
                root_company_id=str(root_company_id) if root_company_id else None,
                error=str(e)
            )
            raise
