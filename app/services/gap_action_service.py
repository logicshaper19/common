"""
Gap Action Service
Business logic for managing transparency gap actions
"""
from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.models.gap_action import GapAction
from app.models.company import Company
from app.models.user import User
from app.schemas.gap_action import GapActionRequest, GapActionUpdate, GapActionResponse
from app.core.logging import get_logger

logger = get_logger(__name__)


class GapActionService:
    """Service for managing gap actions."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_gap_action(
        self,
        company_id: UUID,
        gap_id: str,
        action_request: GapActionRequest,
        created_by_user_id: UUID
    ) -> GapAction:
        """
        Create a new gap action.
        
        Args:
            company_id: ID of the company creating the action
            gap_id: Identifier of the gap being addressed
            action_request: Action details
            created_by_user_id: ID of the user creating the action
            
        Returns:
            Created GapAction instance
        """
        # Validate action type
        valid_action_types = ["request_data", "contact_supplier", "mark_resolved"]
        if action_request.action_type not in valid_action_types:
            raise ValueError(f"Invalid action type. Must be one of: {valid_action_types}")
        
        # Create gap action
        gap_action = GapAction(
            gap_id=gap_id,
            company_id=company_id,
            action_type=action_request.action_type,
            target_company_id=action_request.target_company_id,
            message=action_request.message,
            created_by_user_id=created_by_user_id,
            status="pending"
        )
        
        self.db.add(gap_action)
        self.db.commit()
        self.db.refresh(gap_action)
        
        logger.info(
            f"Gap action created: {gap_action.id} for gap {gap_id} by user {created_by_user_id}"
        )
        
        return gap_action
    
    def get_gap_actions(
        self,
        company_id: UUID,
        status: Optional[str] = None,
        gap_id: Optional[str] = None,
        limit: int = 50
    ) -> List[GapAction]:
        """
        Get gap actions for a company.
        
        Args:
            company_id: ID of the company
            status: Optional status filter
            gap_id: Optional gap ID filter
            limit: Maximum number of actions to return
            
        Returns:
            List of GapAction instances
        """
        query = self.db.query(GapAction).filter(GapAction.company_id == company_id)
        
        if status:
            query = query.filter(GapAction.status == status)
        
        if gap_id:
            query = query.filter(GapAction.gap_id == gap_id)
        
        actions = query.order_by(GapAction.created_at.desc()).limit(limit).all()
        
        return actions
    
    def update_gap_action(
        self,
        action_id: UUID,
        company_id: UUID,
        update_request: GapActionUpdate,
        updated_by_user_id: UUID
    ) -> GapAction:
        """
        Update a gap action.
        
        Args:
            action_id: ID of the action to update
            company_id: ID of the company (for authorization)
            update_request: Update details
            updated_by_user_id: ID of the user making the update
            
        Returns:
            Updated GapAction instance
        """
        # Get the action
        action = self.db.query(GapAction).filter(
            and_(
                GapAction.id == action_id,
                GapAction.company_id == company_id
            )
        ).first()
        
        if not action:
            raise ValueError("Gap action not found or access denied")
        
        # Validate status
        valid_statuses = ["pending", "in_progress", "resolved", "cancelled"]
        if update_request.status not in valid_statuses:
            raise ValueError(f"Invalid status. Must be one of: {valid_statuses}")
        
        # Update action
        action.status = update_request.status
        
        if update_request.resolution_notes:
            action.resolution_notes = update_request.resolution_notes
        
        # If marking as resolved, set resolution fields
        if update_request.status == "resolved":
            action.mark_resolved(updated_by_user_id, update_request.resolution_notes)
        
        self.db.commit()
        self.db.refresh(action)
        
        logger.info(
            f"Gap action updated: {action_id} status changed to {update_request.status}"
        )
        
        return action
    
    def get_gap_action_by_id(self, action_id: UUID, company_id: UUID) -> Optional[GapAction]:
        """
        Get a specific gap action by ID.
        
        Args:
            action_id: ID of the action
            company_id: ID of the company (for authorization)
            
        Returns:
            GapAction instance or None if not found
        """
        return self.db.query(GapAction).filter(
            and_(
                GapAction.id == action_id,
                GapAction.company_id == company_id
            )
        ).first()
    
    def to_response(self, gap_action: GapAction) -> GapActionResponse:
        """
        Convert GapAction model to response schema.
        
        Args:
            gap_action: GapAction instance
            
        Returns:
            GapActionResponse instance
        """
        # Get related data
        created_by_name = "Unknown"
        if gap_action.created_by:
            created_by_name = gap_action.created_by.full_name or gap_action.created_by.email
        
        resolved_by_name = None
        if gap_action.resolved_by:
            resolved_by_name = gap_action.resolved_by.full_name or gap_action.resolved_by.email
        
        target_company_name = None
        if gap_action.target_company:
            target_company_name = gap_action.target_company.name
        
        return GapActionResponse(
            id=gap_action.id,
            gap_id=gap_action.gap_id,
            company_id=gap_action.company_id,
            action_type=gap_action.action_type,
            target_company_id=gap_action.target_company_id,
            target_company_name=target_company_name,
            message=gap_action.message,
            status=gap_action.status,
            created_by_user_id=gap_action.created_by_user_id,
            created_by_name=created_by_name,
            created_at=gap_action.created_at,
            resolved_by_user_id=gap_action.resolved_by_user_id,
            resolved_by_name=resolved_by_name,
            resolved_at=gap_action.resolved_at,
            resolution_notes=gap_action.resolution_notes
        )
