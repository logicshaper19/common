"""
Team invitation API endpoints.
"""
from datetime import datetime, timezone, timedelta
from typing import Optional
import uuid
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.models.company import Company
from app.models.team_invitation import TeamInvitation, InvitationStatus
from app.schemas.team_invitation import (
    TeamInvitationCreate, TeamInvitationResponse, TeamInvitationAccept,
    TeamInvitationList, TeamMemberList, BulkInvitationCreate, BulkInvitationResponse
)
from app.services.team_invitation import TeamInvitationService
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.post("/invitations", response_model=TeamInvitationResponse)
async def create_team_invitation(
    invitation_data: TeamInvitationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new team invitation.
    
    Allows users to invite others to join their company.
    Only active users can send invitations.
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only active users can send invitations"
        )
    
    service = TeamInvitationService(db)
    
    try:
        invitation = service.create_invitation(
            invitation_data=invitation_data,
            company_id=current_user.company_id,
            invited_by_user_id=current_user.id
        )
        
        logger.info(
            "Team invitation created via API",
            invitation_id=str(invitation.id),
            invited_by=str(current_user.id),
            email=invitation_data.email
        )
        
        return invitation
        
    except Exception as e:
        logger.error(
            "Failed to create team invitation",
            error=str(e),
            invited_by=str(current_user.id),
            email=invitation_data.email
        )
        raise


@router.get("/invitations", response_model=TeamInvitationList)
async def get_team_invitations(
    status_filter: Optional[str] = Query(None, description="Filter by invitation status"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get team invitations for the current user's company.
    
    Returns paginated list of invitations with details.
    """
    service = TeamInvitationService(db)
    
    invitations = service.get_company_invitations(
        company_id=current_user.company_id,
        status_filter=status_filter,
        limit=limit,
        offset=offset
    )
    
    return invitations


@router.get("/members", response_model=TeamMemberList)
async def get_team_members(
    limit: int = Query(50, ge=1, le=100, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get team members for the current user's company.
    
    Returns paginated list of active team members.
    """
    service = TeamInvitationService(db)
    
    members = service.get_company_members(
        company_id=current_user.company_id,
        limit=limit,
        offset=offset
    )
    
    return members


@router.post("/invitations/{invitation_id}/cancel")
async def cancel_team_invitation(
    invitation_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Cancel a pending team invitation.
    
    Only users from the same company can cancel invitations.
    """
    service = TeamInvitationService(db)
    
    try:
        from uuid import UUID
        invitation_uuid = UUID(invitation_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid invitation ID format"
        )
    
    success = service.cancel_invitation(
        invitation_id=invitation_uuid,
        user_id=current_user.id
    )
    
    if success:
        return {"message": "Invitation cancelled successfully"}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cancel invitation"
        )


@router.delete("/invitations/{invitation_id}")
async def delete_team_invitation(
    invitation_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a team invitation (same as cancel but with DELETE method)
    """
    try:
        service = TeamInvitationService(db)
        invitation = service.cancel_invitation(invitation_id, current_user.company_id)

        return {"message": "Invitation deleted successfully"}

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to delete invitation {invitation_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete invitation"
        )


@router.post("/invitations/{invitation_id}/resend", response_model=TeamInvitationResponse)
async def resend_team_invitation(
    invitation_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Resend a team invitation by creating a new one with extended expiry
    """
    try:
        service = TeamInvitationService(db)

        # Get the existing invitation
        invitation = db.query(TeamInvitation).filter(
            TeamInvitation.id == invitation_id,
            TeamInvitation.company_id == current_user.company_id
        ).first()

        if not invitation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invitation not found"
            )

        if invitation.status != InvitationStatus.PENDING.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Can only resend pending invitations"
            )

        # Update the invitation with new expiry and token
        invitation.expires_at = datetime.now(timezone.utc) + timedelta(days=7)
        invitation.invitation_token = str(uuid.uuid4())

        db.commit()
        db.refresh(invitation)

        # Get additional data for response
        invited_by = db.query(User).filter(User.id == invitation.invited_by_user_id).first()
        company = db.query(Company).filter(Company.id == invitation.company_id).first()

        return TeamInvitationResponse(
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
            invited_by_name=invited_by.full_name if invited_by else None,
            invited_by_email=invited_by.email if invited_by else None,
            company_name=company.name if company else None
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to resend invitation {invitation_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to resend invitation"
        )


@router.post("/invitations/accept", response_model=dict)
async def accept_team_invitation(
    accept_data: TeamInvitationAccept,
    db: Session = Depends(get_db)
):
    """
    Accept a team invitation and create user account.
    
    This is a public endpoint that doesn't require authentication
    since the user doesn't exist yet.
    """
    service = TeamInvitationService(db)
    
    try:
        user, invitation = service.accept_invitation(accept_data)
        
        logger.info(
            "Team invitation accepted via API",
            user_id=str(user.id),
            invitation_id=str(invitation.id),
            email=user.email
        )
        
        return {
            "message": "Invitation accepted successfully",
            "user_id": str(user.id),
            "email": user.email,
            "company_id": str(user.company_id)
        }
        
    except Exception as e:
        logger.error(
            "Failed to accept team invitation",
            error=str(e),
            token=accept_data.invitation_token
        )
        raise


@router.get("/invitations/token/{token}")
async def get_invitation_details(
    token: str,
    db: Session = Depends(get_db)
):
    """
    Get invitation details by token.
    
    This is a public endpoint used to display invitation details
    before the user accepts it.
    """
    service = TeamInvitationService(db)
    
    invitation = service.get_invitation_by_token(token)
    
    if not invitation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invitation not found"
        )
    
    # Get company and inviter details
    from app.models.company import Company
    company = db.query(Company).filter(Company.id == invitation.company_id).first()
    inviter = db.query(User).filter(User.id == invitation.invited_by_user_id).first()
    
    return {
        "email": invitation.email,
        "full_name": invitation.full_name,
        "role": invitation.role,
        "company_name": company.name if company else "Unknown",
        "invited_by_name": inviter.full_name if inviter else "Unknown",
        "message": invitation.message,
        "created_at": invitation.created_at,
        "expires_at": invitation.expires_at,
        "is_expired": invitation.is_expired,
        "can_accept": invitation.can_be_accepted()
    }


@router.post("/invitations/bulk", response_model=BulkInvitationResponse)
async def create_bulk_invitations(
    bulk_data: BulkInvitationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create multiple team invitations at once.
    
    Useful for inviting multiple team members simultaneously.
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only active users can send invitations"
        )
    
    service = TeamInvitationService(db)
    successful = []
    failed = []
    
    for invitation_data in bulk_data.invitations:
        try:
            invitation = service.create_invitation(
                invitation_data=invitation_data,
                company_id=current_user.company_id,
                invited_by_user_id=current_user.id
            )
            successful.append(invitation)
            
        except Exception as e:
            failed.append({
                "email": invitation_data.email,
                "error": str(e)
            })
    
    logger.info(
        "Bulk team invitations processed",
        total_requested=len(bulk_data.invitations),
        successful=len(successful),
        failed=len(failed),
        invited_by=str(current_user.id)
    )
    
    return BulkInvitationResponse(
        successful=successful,
        failed=failed,
        total_sent=len(successful),
        total_failed=len(failed)
    )
