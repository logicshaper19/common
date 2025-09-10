"""
Audit Service for Admin Override Actions
Provides comprehensive logging and notification for admin actions.
"""
from typing import Dict, Any, Optional
from uuid import UUID, uuid4
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.audit_event import AuditEvent
from app.models.user import User
from app.models.company import Company
from app.services.notification import NotificationService
from app.core.logging import get_logger

logger = get_logger(__name__)


class AuditService:
    """Service for logging admin override actions and maintaining audit trails."""
    
    def __init__(self, db: Session):
        self.db = db
        self.notification_service = NotificationService(db)
    
    async def log_admin_action(
        self,
        admin_user_id: UUID,
        action_type: str,
        target_resource_type: str,
        target_resource_id: str,
        target_company_id: Optional[UUID] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> UUID:
        """
        Log admin override actions for audit trail.
        
        Args:
            admin_user_id: ID of the admin user performing the action
            action_type: Type of action (e.g., 'document_access_override', 'document_deletion_override')
            target_resource_type: Type of resource being accessed (e.g., 'document', 'purchase_order')
            target_resource_id: ID of the target resource
            target_company_id: ID of the company that owns the resource
            details: Additional details about the action
            
        Returns:
            UUID of the created audit event
        """
        try:
            # Get admin user details
            admin_user = self.db.query(User).filter(User.id == admin_user_id).first()
            if not admin_user:
                raise ValueError(f"Admin user not found: {admin_user_id}")
            
            # Create audit event
            audit_event = AuditEvent(
                id=uuid4(),
                event_type="admin_override",
                user_id=admin_user_id,
                company_id=target_company_id,
                resource_type=target_resource_type,
                resource_id=target_resource_id,
                action=action_type,
                details={
                    **(details or {}),
                    "admin_user_email": admin_user.email,
                    "admin_user_name": admin_user.full_name,
                    "admin_company_id": str(admin_user.company_id) if admin_user.company_id else None,
                    "timestamp": datetime.utcnow().isoformat(),
                    "severity": "high"
                },
                severity="high",  # Admin overrides are always high severity
                timestamp=datetime.utcnow()
            )
            
            self.db.add(audit_event)
            self.db.commit()
            
            logger.info(
                "Admin action logged successfully",
                audit_event_id=str(audit_event.id),
                admin_user_id=str(admin_user_id),
                action_type=action_type,
                target_resource_type=target_resource_type,
                target_resource_id=target_resource_id
            )
            
            # Send notifications to affected company if applicable
            if target_company_id:
                await self._notify_company_of_admin_action(
                    target_company_id, action_type, details or {}, admin_user
                )
            
            return audit_event.id
            
        except Exception as e:
            self.db.rollback()
            logger.error(
                "Failed to log admin action",
                error=str(e),
                admin_user_id=str(admin_user_id),
                action_type=action_type
            )
            raise
    
    async def _notify_company_of_admin_action(
        self,
        company_id: UUID,
        action_type: str,
        details: Dict[str, Any],
        admin_user: User
    ):
        """
        Notify company users of admin actions on their resources.
        
        Args:
            company_id: ID of the affected company
            action_type: Type of admin action performed
            details: Details about the action
            admin_user: Admin user who performed the action
        """
        try:
            # Get company details
            company = self.db.query(Company).filter(Company.id == company_id).first()
            if not company:
                logger.warning(f"Company not found for notification: {company_id}")
                return
            
            # Get company admin users to notify
            company_admins = self.db.query(User).filter(
                and_(
                    User.company_id == company_id,
                    User.role.in_(["admin", "company_admin"]),
                    User.is_active == True
                )
            ).all()
            
            if not company_admins:
                logger.info(f"No company admins found to notify for company: {company_id}")
                return
            
            # Create notification message
            action_descriptions = {
                "document_access_override": "accessed your company's document",
                "document_deletion_override": "deleted your company's document",
                "purchase_order_access_override": "accessed your company's purchase order",
                "data_export_override": "exported your company's data"
            }
            
            action_description = action_descriptions.get(
                action_type, 
                f"performed {action_type} on your company's resource"
            )
            
            notification_title = "Platform Admin Action"
            notification_message = (
                f"Platform administrator {admin_user.full_name} ({admin_user.email}) "
                f"{action_description}. This action has been logged for audit purposes."
            )
            
            # Send notification to each company admin
            for admin in company_admins:
                try:
                    await self.notification_service.create_notification(
                        user_id=admin.id,
                        type="admin_action",
                        title=notification_title,
                        message=notification_message,
                        data={
                            "action_type": action_type,
                            "admin_user_id": str(admin_user.id),
                            "admin_user_email": admin_user.email,
                            "admin_user_name": admin_user.full_name,
                            "company_id": str(company_id),
                            "company_name": company.name,
                            "details": details,
                            "timestamp": datetime.utcnow().isoformat(),
                            "severity": "high"
                        },
                        priority="high"
                    )
                    
                    logger.info(
                        "Admin action notification sent",
                        recipient_user_id=str(admin.id),
                        company_id=str(company_id),
                        action_type=action_type
                    )
                    
                except Exception as e:
                    logger.error(
                        "Failed to send admin action notification",
                        error=str(e),
                        recipient_user_id=str(admin.id),
                        company_id=str(company_id)
                    )
                    
        except Exception as e:
            logger.error(
                "Failed to notify company of admin action",
                error=str(e),
                company_id=str(company_id),
                action_type=action_type
            )
    
    def get_admin_audit_trail(
        self,
        admin_user_id: Optional[UUID] = None,
        company_id: Optional[UUID] = None,
        action_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> list[AuditEvent]:
        """
        Retrieve admin audit trail with filtering options.
        
        Args:
            admin_user_id: Filter by specific admin user
            company_id: Filter by affected company
            action_type: Filter by action type
            start_date: Filter events after this date
            end_date: Filter events before this date
            limit: Maximum number of events to return
            
        Returns:
            List of audit events matching the criteria
        """
        query = self.db.query(AuditEvent).filter(
            AuditEvent.event_type == "admin_override"
        )
        
        if admin_user_id:
            query = query.filter(AuditEvent.user_id == admin_user_id)
        
        if company_id:
            query = query.filter(AuditEvent.company_id == company_id)
        
        if action_type:
            query = query.filter(AuditEvent.action == action_type)
        
        if start_date:
            query = query.filter(AuditEvent.timestamp >= start_date)
        
        if end_date:
            query = query.filter(AuditEvent.timestamp <= end_date)
        
        return query.order_by(AuditEvent.timestamp.desc()).limit(limit).all()
