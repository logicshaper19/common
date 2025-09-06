"""
Invitation lifecycle tracking service.

This module handles the complete lifecycle of supplier invitations,
from creation through acceptance, expiration, and cascade propagation.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.models.supplier_invitation import SupplierInvitation
from app.models.company import Company
from app.core.logging import get_logger
from ..models.enums import InvitationStatus, OnboardingStage
from ..services.query_service import AnalyticsQueryService

logger = get_logger(__name__)


class InvitationTracker:
    """Handles invitation tracking and lifecycle management."""
    
    def __init__(self, db: Session, query_service: AnalyticsQueryService):
        self.db = db
        self.query_service = query_service
    
    def create_invitation(
        self,
        inviting_company_id: int,
        invited_company_name: str,
        invited_company_email: str,
        invitation_message: Optional[str] = None,
        parent_invitation_id: Optional[int] = None
    ) -> SupplierInvitation:
        """
        Create a new supplier invitation with viral tracking.
        
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
            "Creating supplier invitation",
            inviting_company_id=inviting_company_id,
            invited_company_name=invited_company_name,
            parent_invitation_id=parent_invitation_id
        )
        
        # Check for existing invitation to prevent duplicates
        existing = self._find_existing_invitation(
            inviting_company_id, invited_company_email
        )
        
        if existing and existing.status == InvitationStatus.PENDING:
            logger.warning(
                "Invitation already exists and is pending",
                existing_invitation_id=existing.id
            )
            return existing
        
        # Create new invitation
        invitation = SupplierInvitation(
            inviting_company_id=inviting_company_id,
            invited_company_name=invited_company_name,
            invited_company_email=invited_company_email,
            invitation_message=invitation_message,
            parent_invitation_id=parent_invitation_id,
            status=InvitationStatus.PENDING.value,
            created_at=datetime.utcnow()
        )
        
        self.db.add(invitation)
        self.db.commit()
        self.db.refresh(invitation)
        
        logger.info(
            "Supplier invitation created successfully",
            invitation_id=invitation.id,
            inviting_company_id=inviting_company_id
        )
        
        return invitation
    
    def accept_invitation(
        self,
        invitation_id: int,
        accepting_company_id: int
    ) -> bool:
        """
        Mark invitation as accepted and trigger cascade updates.
        
        Args:
            invitation_id: ID of invitation being accepted
            accepting_company_id: ID of company accepting invitation
            
        Returns:
            True if acceptance was successful
        """
        logger.info(
            "Processing invitation acceptance",
            invitation_id=invitation_id,
            accepting_company_id=accepting_company_id
        )
        
        invitation = self.db.query(SupplierInvitation).filter(
            SupplierInvitation.id == invitation_id
        ).first()
        
        if not invitation:
            logger.error("Invitation not found", invitation_id=invitation_id)
            return False
        
        if invitation.status != InvitationStatus.PENDING.value:
            logger.warning(
                "Invitation is not in pending status",
                invitation_id=invitation_id,
                current_status=invitation.status
            )
            return False
        
        # Update invitation status
        invitation.status = InvitationStatus.ACCEPTED.value
        invitation.accepted_at = datetime.utcnow()
        invitation.accepting_company_id = accepting_company_id
        
        self.db.commit()
        
        logger.info(
            "Invitation accepted successfully",
            invitation_id=invitation_id,
            accepting_company_id=accepting_company_id
        )
        
        return True
    
    def expire_old_invitations(self, days_old: int = 30) -> int:
        """
        Expire invitations that are older than specified days.
        
        Args:
            days_old: Number of days after which to expire invitations
            
        Returns:
            Number of invitations expired
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)
        
        expired_count = self.db.query(SupplierInvitation).filter(
            and_(
                SupplierInvitation.status == InvitationStatus.PENDING.value,
                SupplierInvitation.created_at < cutoff_date
            )
        ).update({
            "status": InvitationStatus.EXPIRED.value,
            "updated_at": datetime.utcnow()
        })
        
        self.db.commit()
        
        logger.info(
            "Expired old invitations",
            expired_count=expired_count,
            cutoff_date=cutoff_date
        )
        
        return expired_count
    
    def find_parent_invitation(
        self,
        company_id: int
    ) -> Optional[SupplierInvitation]:
        """
        Find the parent invitation that led to this company joining.
        
        Args:
            company_id: ID of company to find parent for
            
        Returns:
            Parent invitation if found
        """
        return self.db.query(SupplierInvitation).filter(
            and_(
                SupplierInvitation.accepting_company_id == company_id,
                SupplierInvitation.status == InvitationStatus.ACCEPTED.value
            )
        ).first()
    
    def update_invitation_status(
        self,
        invitation_id: int,
        new_status: InvitationStatus,
        notes: Optional[str] = None
    ) -> bool:
        """
        Update invitation status with optional notes.
        
        Args:
            invitation_id: ID of invitation to update
            new_status: New status to set
            notes: Optional notes about the status change
            
        Returns:
            True if update was successful
        """
        invitation = self.db.query(SupplierInvitation).filter(
            SupplierInvitation.id == invitation_id
        ).first()
        
        if not invitation:
            logger.error("Invitation not found for status update", invitation_id=invitation_id)
            return False
        
        old_status = invitation.status
        invitation.status = new_status.value
        invitation.updated_at = datetime.utcnow()
        
        if notes:
            invitation.notes = notes
        
        self.db.commit()
        
        logger.info(
            "Invitation status updated",
            invitation_id=invitation_id,
            old_status=old_status,
            new_status=new_status.value
        )
        
        return True
    
    def get_invitation_chain(
        self,
        invitation_id: int,
        max_depth: int = 10
    ) -> List[SupplierInvitation]:
        """
        Get the complete invitation chain starting from a root invitation.
        
        Args:
            invitation_id: Starting invitation ID
            max_depth: Maximum depth to traverse
            
        Returns:
            List of invitations in the chain
        """
        chain = []
        current_id = invitation_id
        depth = 0
        
        while current_id and depth < max_depth:
            invitation = self.db.query(SupplierInvitation).filter(
                SupplierInvitation.id == current_id
            ).first()
            
            if not invitation:
                break
            
            chain.append(invitation)
            current_id = invitation.parent_invitation_id
            depth += 1
        
        return list(reversed(chain))  # Return root-first order
    
    def get_invitation_descendants(
        self,
        invitation_id: int,
        max_depth: int = 10
    ) -> List[SupplierInvitation]:
        """
        Get all descendant invitations from a parent invitation.
        
        Args:
            invitation_id: Parent invitation ID
            max_depth: Maximum depth to traverse
            
        Returns:
            List of descendant invitations
        """
        descendants = []
        current_level = [invitation_id]
        depth = 0
        
        while current_level and depth < max_depth:
            next_level = []
            
            for parent_id in current_level:
                children = self.db.query(SupplierInvitation).filter(
                    SupplierInvitation.parent_invitation_id == parent_id
                ).all()
                
                descendants.extend(children)
                next_level.extend([child.id for child in children])
            
            current_level = next_level
            depth += 1
        
        return descendants
    
    def _find_existing_invitation(
        self,
        inviting_company_id: int,
        invited_company_email: str
    ) -> Optional[SupplierInvitation]:
        """Find existing invitation between companies."""
        return self.db.query(SupplierInvitation).filter(
            and_(
                SupplierInvitation.inviting_company_id == inviting_company_id,
                SupplierInvitation.invited_company_email == invited_company_email
            )
        ).order_by(SupplierInvitation.created_at.desc()).first()
    
    def get_invitation_metrics(
        self,
        company_id: Optional[int] = None,
        days_back: int = 30
    ) -> Dict[str, Any]:
        """
        Get invitation metrics for analysis.
        
        Args:
            company_id: Optional company filter
            days_back: Number of days to analyze
            
        Returns:
            Dictionary with invitation metrics
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days_back)
        
        query = self.db.query(SupplierInvitation).filter(
            SupplierInvitation.created_at >= cutoff_date
        )
        
        if company_id:
            query = query.filter(SupplierInvitation.inviting_company_id == company_id)
        
        invitations = query.all()
        
        # Calculate metrics
        total_sent = len(invitations)
        total_accepted = len([inv for inv in invitations if inv.status == InvitationStatus.ACCEPTED.value])
        total_pending = len([inv for inv in invitations if inv.status == InvitationStatus.PENDING.value])
        total_expired = len([inv for inv in invitations if inv.status == InvitationStatus.EXPIRED.value])
        
        conversion_rate = total_accepted / total_sent if total_sent > 0 else 0
        
        # Calculate average response time for accepted invitations
        response_times = []
        for inv in invitations:
            if inv.status == InvitationStatus.ACCEPTED.value and inv.accepted_at:
                response_time = (inv.accepted_at - inv.created_at).total_seconds() / 3600  # hours
                response_times.append(response_time)
        
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        
        return {
            "total_sent": total_sent,
            "total_accepted": total_accepted,
            "total_pending": total_pending,
            "total_expired": total_expired,
            "conversion_rate": conversion_rate,
            "average_response_time_hours": avg_response_time,
            "analysis_period_days": days_back
        }
