"""
Team invitation service layer for managing team invitations and user onboarding.
"""
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timedelta
from uuid import UUID, uuid4
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from fastapi import HTTPException, status

from app.models.user import User
from app.models.company import Company
from app.models.team_invitation import TeamInvitation, InvitationStatus
from app.schemas.team_invitation import (
    TeamInvitationCreate, TeamInvitationResponse, TeamInvitationWithDetails,
    TeamInvitationAccept, TeamInvitationList, TeamMemberResponse, TeamMemberList,
    TeamInvitationStats, BulkInvitationCreate, BulkInvitationResponse
)
from app.core.security import hash_password
from app.core.logging import get_logger
from app.core.config import settings

logger = get_logger(__name__)


class TeamInvitationService:
    """Service for managing team invitations and user onboarding."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_invitation(
        self,
        invitation_data: TeamInvitationCreate,
        company_id: UUID,
        invited_by_user_id: UUID
    ) -> TeamInvitationResponse:
        """
        Create a new team invitation.
        
        Args:
            invitation_data: Invitation details
            company_id: Company to invite user to
            invited_by_user_id: User sending the invitation
            
        Returns:
            Created invitation
            
        Raises:
            HTTPException: If invitation cannot be created
        """
        logger.info(
            "Creating team invitation",
            email=invitation_data.email,
            company_id=str(company_id),
            invited_by=str(invited_by_user_id)
        )
        
        # Check if user already exists in the company
        existing_user = self.db.query(User).filter(
            and_(
                User.email == invitation_data.email,
                User.company_id == company_id
            )
        ).first()
        
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"User with email {invitation_data.email} is already a member of this company"
            )
        
        # Check for existing pending invitation
        existing_invitation = self.db.query(TeamInvitation).filter(
            and_(
                TeamInvitation.email == invitation_data.email,
                TeamInvitation.company_id == company_id,
                TeamInvitation.status == InvitationStatus.PENDING.value
            )
        ).first()
        
        if existing_invitation and not existing_invitation.is_expired:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"A pending invitation already exists for {invitation_data.email}"
            )
        
        # Cancel existing pending invitation if expired
        if existing_invitation and existing_invitation.is_expired:
            existing_invitation.expire()
            self.db.commit()
        
        # Create new invitation
        invitation = TeamInvitation(
            email=invitation_data.email,
            full_name=invitation_data.full_name,
            role=invitation_data.role,
            company_id=company_id,
            invited_by_user_id=invited_by_user_id,
            message=invitation_data.message,
            expires_at=datetime.utcnow() + timedelta(days=7)
        )
        
        self.db.add(invitation)
        self.db.commit()
        self.db.refresh(invitation)
        
        logger.info(
            "Team invitation created successfully",
            invitation_id=str(invitation.id),
            email=invitation_data.email
        )
        
        # Convert to response schema
        response = TeamInvitationResponse(
            id=invitation.id,
            email=invitation.email,
            full_name=invitation.full_name,
            role=invitation.role,
            company_id=invitation.company_id,
            invited_by_user_id=invitation.invited_by_user_id,
            status=invitation.status,
            invitation_token=invitation.invitation_token,
            message=invitation.message,
            created_at=invitation.created_at,
            expires_at=invitation.expires_at,
            accepted_at=invitation.accepted_at,
            accepted_by_user_id=invitation.accepted_by_user_id,
            is_expired=invitation.is_expired,
            is_pending=invitation.is_pending
        )
        
        return response
    
    def get_invitation_by_token(self, token: str) -> Optional[TeamInvitation]:
        """Get invitation by token."""
        return self.db.query(TeamInvitation).filter(
            TeamInvitation.invitation_token == token
        ).first()
    
    def accept_invitation(
        self,
        accept_data: TeamInvitationAccept
    ) -> Tuple[User, TeamInvitation]:
        """
        Accept a team invitation and create user account.
        
        Args:
            accept_data: Invitation acceptance data
            
        Returns:
            Tuple of (created_user, invitation)
            
        Raises:
            HTTPException: If invitation cannot be accepted
        """
        logger.info(
            "Processing invitation acceptance",
            token=accept_data.invitation_token
        )
        
        # Find invitation
        invitation = self.get_invitation_by_token(accept_data.invitation_token)
        if not invitation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invitation not found"
            )
        
        # Validate invitation can be accepted
        if not invitation.can_be_accepted():
            if invitation.is_expired:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invitation has expired"
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invitation cannot be accepted (status: {invitation.status})"
                )
        
        # Check if user already exists with this email
        existing_user = self.db.query(User).filter(
            User.email == invitation.email
        ).first()
        
        if existing_user:
            # User exists, just add them to the company if not already a member
            if existing_user.company_id == invitation.company_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User is already a member of this company"
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User already exists with a different company. Please contact support."
                )
        
        # Create new user
        user = User(
            id=uuid4(),
            email=invitation.email,
            hashed_password=hash_password(accept_data.password),
            full_name=accept_data.full_name or invitation.full_name or invitation.email.split('@')[0],
            role=invitation.role,
            company_id=invitation.company_id,
            is_active=True
        )
        
        self.db.add(user)
        
        # Accept invitation
        invitation.accept(user.id)
        
        self.db.commit()
        self.db.refresh(user)
        
        logger.info(
            "Invitation accepted successfully",
            user_id=str(user.id),
            invitation_id=str(invitation.id),
            email=user.email
        )
        
        return user, invitation

    def get_company_invitations(
        self,
        company_id: UUID,
        status_filter: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> TeamInvitationList:
        """
        Get invitations for a company.

        Args:
            company_id: Company ID
            status_filter: Optional status filter
            limit: Maximum number of results
            offset: Offset for pagination

        Returns:
            List of invitations with details
        """
        query = self.db.query(TeamInvitation).filter(
            TeamInvitation.company_id == company_id
        )

        if status_filter:
            query = query.filter(TeamInvitation.status == status_filter)

        # Get total count
        total = query.count()

        # Get invitations with pagination
        invitations = query.order_by(
            TeamInvitation.created_at.desc()
        ).offset(offset).limit(limit).all()

        # Get additional details for each invitation
        invitation_details = []
        for invitation in invitations:
            invited_by = self.db.query(User).filter(
                User.id == invitation.invited_by_user_id
            ).first()

            company = self.db.query(Company).filter(
                Company.id == invitation.company_id
            ).first()

            detail = TeamInvitationWithDetails(
                id=invitation.id,
                email=invitation.email,
                full_name=invitation.full_name,
                role=invitation.role,
                company_id=invitation.company_id,
                invited_by_user_id=invitation.invited_by_user_id,
                status=invitation.status,
                invitation_token=invitation.invitation_token,
                message=invitation.message,
                created_at=invitation.created_at,
                expires_at=invitation.expires_at,
                accepted_at=invitation.accepted_at,
                accepted_by_user_id=invitation.accepted_by_user_id,
                is_expired=invitation.is_expired,
                is_pending=invitation.is_pending,
                invited_by_name=invited_by.full_name if invited_by else "Unknown",
                invited_by_email=invited_by.email if invited_by else "Unknown",
                company_name=company.name if company else "Unknown"
            )
            invitation_details.append(detail)

        # Calculate counts
        all_invitations = self.db.query(TeamInvitation).filter(
            TeamInvitation.company_id == company_id
        ).all()

        pending_count = sum(1 for inv in all_invitations if inv.is_pending)
        accepted_count = sum(1 for inv in all_invitations if inv.status == InvitationStatus.ACCEPTED.value)
        expired_count = sum(1 for inv in all_invitations if inv.is_expired)

        return TeamInvitationList(
            invitations=invitation_details,
            total=total,
            pending_count=pending_count,
            accepted_count=accepted_count,
            expired_count=expired_count
        )

    def get_company_members(
        self,
        company_id: UUID,
        limit: int = 50,
        offset: int = 0
    ) -> TeamMemberList:
        """
        Get team members for a company.

        Args:
            company_id: Company ID
            limit: Maximum number of results
            offset: Offset for pagination

        Returns:
            List of team members
        """
        query = self.db.query(User).filter(
            and_(
                User.company_id == company_id,
                User.is_active == True
            )
        )

        total = query.count()

        users = query.order_by(User.created_at.desc()).offset(offset).limit(limit).all()

        members = []
        for user in users:
            member = TeamMemberResponse(
                id=user.id,
                email=user.email,
                full_name=user.full_name,
                role=user.role,
                is_active=user.is_active,
                created_at=user.created_at,
                last_login=None  # TODO: Add last_login tracking
            )
            members.append(member)

        # Calculate counts
        all_users = self.db.query(User).filter(User.company_id == company_id).all()
        active_count = sum(1 for user in all_users if user.is_active)
        admin_count = sum(1 for user in all_users if user.role == 'admin' and user.is_active)

        return TeamMemberList(
            members=members,
            total=total,
            active_count=active_count,
            admin_count=admin_count
        )

    def cancel_invitation(self, invitation_id: UUID, user_id: UUID) -> bool:
        """
        Cancel a pending invitation.

        Args:
            invitation_id: Invitation ID
            user_id: User requesting cancellation

        Returns:
            True if cancelled successfully

        Raises:
            HTTPException: If invitation cannot be cancelled
        """
        invitation = self.db.query(TeamInvitation).filter(
            TeamInvitation.id == invitation_id
        ).first()

        if not invitation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invitation not found"
            )

        # Check if user has permission to cancel (must be from same company)
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user or user.company_id != invitation.company_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to cancel this invitation"
            )

        if invitation.status != InvitationStatus.PENDING.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only pending invitations can be cancelled"
            )

        invitation.cancel()
        self.db.commit()

        logger.info(
            "Invitation cancelled",
            invitation_id=str(invitation_id),
            cancelled_by=str(user_id)
        )

        return True
