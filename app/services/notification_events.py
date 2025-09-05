"""
Event-driven notification triggers for the Common supply chain platform.
"""
from typing import Optional, Dict, Any, List
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.logging import get_logger
from app.services.notifications import NotificationService
from app.models.notification import NotificationType, NotificationPriority
from app.models.purchase_order import PurchaseOrder
from app.models.company import Company
from app.models.user import User

logger = get_logger(__name__)


class NotificationEventTrigger:
    """
    Service for triggering notifications based on system events.
    
    This service acts as the bridge between business logic events
    and the notification system, ensuring that relevant stakeholders
    are notified of important changes in the supply chain.
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.notification_service = NotificationService(db)
    
    def trigger_po_created(self, po_id: UUID, created_by_user_id: UUID) -> List[str]:
        """
        Trigger notifications when a new PO is created.
        
        Args:
            po_id: Purchase order UUID
            created_by_user_id: User who created the PO
            
        Returns:
            List of notification IDs created
        """
        try:
            po = self.db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
            if not po:
                logger.error("PO not found for notification trigger", po_id=str(po_id))
                return []
            
            # Get buyer and seller companies
            buyer_company = self.db.query(Company).filter(Company.id == po.buyer_company_id).first()
            seller_company = self.db.query(Company).filter(Company.id == po.seller_company_id).first()
            
            template_variables = {
                "po_number": po.po_number,
                "buyer_company": buyer_company.name if buyer_company else "Unknown",
                "seller_company": seller_company.name if seller_company else "Unknown",
                "product_name": "Product",  # Would need to join with Product table
                "quantity": str(po.quantity),
                "unit": po.unit,
                "delivery_date": po.delivery_date.strftime("%Y-%m-%d") if po.delivery_date else "TBD",
                "total_amount": str(po.total_amount) if po.total_amount else "TBD"
            }
            
            # Create notifications for seller company users (they need to confirm)
            notifications = self.notification_service.create_po_notification(
                po_id=po_id,
                notification_type=NotificationType.PO_CREATED,
                template_variables=template_variables
            )
            
            notification_ids = [str(n.id) for n in notifications]
            
            logger.info(
                "PO created notifications triggered",
                po_id=str(po_id),
                po_number=po.po_number,
                notifications_count=len(notifications),
                notification_ids=notification_ids
            )
            
            return notification_ids
            
        except Exception as e:
            logger.error(
                "Failed to trigger PO created notifications",
                po_id=str(po_id),
                error=str(e)
            )
            return []
    
    def trigger_po_confirmed(self, po_id: UUID, confirmed_by_user_id: UUID) -> List[str]:
        """
        Trigger notifications when a PO is confirmed.
        
        Args:
            po_id: Purchase order UUID
            confirmed_by_user_id: User who confirmed the PO
            
        Returns:
            List of notification IDs created
        """
        try:
            po = self.db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
            if not po:
                logger.error("PO not found for notification trigger", po_id=str(po_id))
                return []
            
            # Get companies
            buyer_company = self.db.query(Company).filter(Company.id == po.buyer_company_id).first()
            seller_company = self.db.query(Company).filter(Company.id == po.seller_company_id).first()
            
            template_variables = {
                "po_number": po.po_number,
                "buyer_company": buyer_company.name if buyer_company else "Unknown",
                "seller_company": seller_company.name if seller_company else "Unknown",
                "confirmed_date": datetime.utcnow().strftime("%Y-%m-%d %H:%M"),
                "delivery_date": po.delivery_date.strftime("%Y-%m-%d") if po.delivery_date else "TBD"
            }
            
            # Create notifications for buyer company users
            notifications = self.notification_service.create_po_notification(
                po_id=po_id,
                notification_type=NotificationType.PO_CONFIRMED,
                template_variables=template_variables
            )
            
            notification_ids = [str(n.id) for n in notifications]
            
            logger.info(
                "PO confirmed notifications triggered",
                po_id=str(po_id),
                po_number=po.po_number,
                notifications_count=len(notifications),
                notification_ids=notification_ids
            )
            
            return notification_ids
            
        except Exception as e:
            logger.error(
                "Failed to trigger PO confirmed notifications",
                po_id=str(po_id),
                error=str(e)
            )
            return []
    
    def trigger_po_status_changed(
        self,
        po_id: UUID,
        old_status: str,
        new_status: str,
        changed_by_user_id: UUID
    ) -> List[str]:
        """
        Trigger notifications when PO status changes.
        
        Args:
            po_id: Purchase order UUID
            old_status: Previous status
            new_status: New status
            changed_by_user_id: User who changed the status
            
        Returns:
            List of notification IDs created
        """
        try:
            po = self.db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
            if not po:
                logger.error("PO not found for notification trigger", po_id=str(po_id))
                return []
            
            # Skip notifications for certain status changes
            skip_statuses = ["pending"]  # Don't notify for initial pending status
            if new_status in skip_statuses:
                return []
            
            # Get companies
            buyer_company = self.db.query(Company).filter(Company.id == po.buyer_company_id).first()
            seller_company = self.db.query(Company).filter(Company.id == po.seller_company_id).first()
            
            template_variables = {
                "po_number": po.po_number,
                "old_status": old_status.replace("_", " ").title(),
                "new_status": new_status.replace("_", " ").title(),
                "status": new_status.replace("_", " ").title(),
                "buyer_company": buyer_company.name if buyer_company else "Unknown",
                "seller_company": seller_company.name if seller_company else "Unknown",
                "changed_date": datetime.utcnow().strftime("%Y-%m-%d %H:%M")
            }
            
            # Determine priority based on status
            priority = NotificationPriority.NORMAL
            if new_status in ["cancelled", "rejected"]:
                priority = NotificationPriority.HIGH
            elif new_status in ["delivered", "completed"]:
                priority = NotificationPriority.NORMAL
            
            # Create notifications for both buyer and seller
            notifications = self.notification_service.create_po_notification(
                po_id=po_id,
                notification_type=NotificationType.PO_STATUS_CHANGED,
                template_variables=template_variables
            )
            
            # Update notification priority
            for notification in notifications:
                notification.priority = priority
                self.db.commit()
            
            notification_ids = [str(n.id) for n in notifications]
            
            logger.info(
                "PO status changed notifications triggered",
                po_id=str(po_id),
                po_number=po.po_number,
                old_status=old_status,
                new_status=new_status,
                priority=priority.value,
                notifications_count=len(notifications),
                notification_ids=notification_ids
            )
            
            return notification_ids
            
        except Exception as e:
            logger.error(
                "Failed to trigger PO status changed notifications",
                po_id=str(po_id),
                old_status=old_status,
                new_status=new_status,
                error=str(e)
            )
            return []
    
    def trigger_transparency_updated(
        self,
        po_id: UUID,
        ttm_score: Optional[float] = None,
        ttp_score: Optional[float] = None,
        confidence_level: Optional[float] = None
    ) -> List[str]:
        """
        Trigger notifications when transparency scores are updated.
        
        Args:
            po_id: Purchase order UUID
            ttm_score: New TTM score
            ttp_score: New TTP score
            confidence_level: New confidence level
            
        Returns:
            List of notification IDs created
        """
        try:
            po = self.db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
            if not po:
                logger.error("PO not found for notification trigger", po_id=str(po_id))
                return []
            
            # Only notify if scores are significant (above threshold)
            min_score_threshold = 0.1
            if (ttm_score and ttm_score < min_score_threshold and 
                ttp_score and ttp_score < min_score_threshold):
                return []  # Don't notify for very low scores
            
            template_variables = {
                "po_number": po.po_number,
                "ttm_score": f"{ttm_score:.2%}" if ttm_score else "N/A",
                "ttp_score": f"{ttp_score:.2%}" if ttp_score else "N/A",
                "confidence_level": f"{confidence_level:.2%}" if confidence_level else "N/A",
                "updated_date": datetime.utcnow().strftime("%Y-%m-%d %H:%M")
            }
            
            # Create notifications for both buyer and seller
            notifications = self.notification_service.create_po_notification(
                po_id=po_id,
                notification_type=NotificationType.TRANSPARENCY_UPDATED,
                template_variables=template_variables
            )
            
            notification_ids = [str(n.id) for n in notifications]
            
            logger.info(
                "Transparency updated notifications triggered",
                po_id=str(po_id),
                po_number=po.po_number,
                ttm_score=ttm_score,
                ttp_score=ttp_score,
                confidence_level=confidence_level,
                notifications_count=len(notifications),
                notification_ids=notification_ids
            )
            
            return notification_ids
            
        except Exception as e:
            logger.error(
                "Failed to trigger transparency updated notifications",
                po_id=str(po_id),
                error=str(e)
            )
            return []
    
    def trigger_supplier_invitation(
        self,
        supplier_email: str,
        inviting_company_id: UUID,
        relationship_id: UUID
    ) -> List[str]:
        """
        Trigger notifications for supplier invitations.
        
        Args:
            supplier_email: Email of invited supplier
            inviting_company_id: Company sending the invitation
            relationship_id: Business relationship UUID
            
        Returns:
            List of notification IDs created
        """
        try:
            # Get inviting company
            inviting_company = self.db.query(Company).filter(
                Company.id == inviting_company_id
            ).first()
            
            if not inviting_company:
                logger.error("Inviting company not found", company_id=str(inviting_company_id))
                return []
            
            # For supplier invitations, we would typically send email directly
            # since the user might not exist in the system yet
            # This is a placeholder for the invitation flow
            
            logger.info(
                "Supplier invitation notification triggered",
                supplier_email=supplier_email,
                inviting_company=inviting_company.name,
                relationship_id=str(relationship_id)
            )
            
            # Return empty list since this would be handled by email service directly
            return []
            
        except Exception as e:
            logger.error(
                "Failed to trigger supplier invitation notifications",
                supplier_email=supplier_email,
                inviting_company_id=str(inviting_company_id),
                error=str(e)
            )
            return []
    
    def trigger_system_alert(
        self,
        alert_type: str,
        message: str,
        affected_companies: List[UUID] = None,
        priority: NotificationPriority = NotificationPriority.NORMAL,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        """
        Trigger system-wide alerts.
        
        Args:
            alert_type: Type of system alert
            message: Alert message
            affected_companies: List of company UUIDs to notify
            priority: Alert priority
            metadata: Additional alert metadata
            
        Returns:
            List of notification IDs created
        """
        try:
            notification_ids = []
            
            # Get target companies
            if affected_companies:
                companies = self.db.query(Company).filter(
                    Company.id.in_(affected_companies)
                ).all()
            else:
                # Notify all companies for system-wide alerts
                companies = self.db.query(Company).all()
            
            # Create notifications for all users in affected companies
            for company in companies:
                users = self.db.query(User).filter(
                    User.company_id == company.id,
                    User.is_active == True
                ).all()
                
                for user in users:
                    notification = self.notification_service.create_notification(
                        user_id=user.id,
                        notification_type=NotificationType.SYSTEM_ALERT,
                        title=f"System Alert: {alert_type}",
                        message=message,
                        priority=priority,
                        metadata=metadata or {}
                    )
                    notification_ids.append(str(notification.id))
            
            logger.info(
                "System alert notifications triggered",
                alert_type=alert_type,
                affected_companies_count=len(companies),
                notifications_count=len(notification_ids),
                priority=priority.value
            )
            
            return notification_ids
            
        except Exception as e:
            logger.error(
                "Failed to trigger system alert notifications",
                alert_type=alert_type,
                error=str(e)
            )
            return []
