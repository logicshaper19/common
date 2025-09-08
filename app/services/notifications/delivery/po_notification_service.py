"""
Purchase Order specific notification service.
"""
from typing import List, Optional, Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.models.purchase_order import PurchaseOrder
from app.models.notification import NotificationType
from ..domain.models import NotificationContext, NotificationTarget
from ..domain.enums import NotificationTypeCategory, ChannelPriority

logger = get_logger(__name__)


class PurchaseOrderNotificationService:
    """
    Service for handling Purchase Order specific notifications.
    
    Features:
    - PO lifecycle event notifications
    - Stakeholder identification and targeting
    - Business context enrichment
    - PO-specific notification templates
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def notify_po_created(
        self,
        po: PurchaseOrder,
        created_by_user_id: UUID
    ) -> NotificationContext:
        """
        Create notification context for PO creation.
        
        Args:
            po: Created purchase order
            created_by_user_id: User who created the PO
            
        Returns:
            NotificationContext for PO creation
        """
        return NotificationContext(
            notification_type=NotificationType.PO_CREATED,
            category=NotificationTypeCategory.PURCHASE_ORDER,
            title=f"New Purchase Order #{po.po_number}",
            message=f"Purchase Order #{po.po_number} has been created for {po.product_name}",
            related_po_id=po.id,
            related_company_id=po.buyer_company_id,
            business_context={
                "po_number": po.po_number,
                "product_name": po.product_name,
                "quantity": po.quantity,
                "unit_price": float(po.unit_price) if po.unit_price else None,
                "total_amount": float(po.total_amount) if po.total_amount else None,
                "buyer_company_id": str(po.buyer_company_id),
                "seller_company_id": str(po.seller_company_id),
                "created_by_user_id": str(created_by_user_id),
                "delivery_date": po.delivery_date.isoformat() if po.delivery_date else None
            },
            metadata={
                "event": "po_created",
                "po_status": po.status.value if po.status else None
            }
        )
    
    def notify_po_confirmed(
        self,
        po: PurchaseOrder,
        confirmed_by_user_id: UUID,
        confirmation_details: Optional[Dict[str, Any]] = None
    ) -> NotificationContext:
        """
        Create notification context for PO confirmation.
        
        Args:
            po: Confirmed purchase order
            confirmed_by_user_id: User who confirmed the PO
            confirmation_details: Additional confirmation details
            
        Returns:
            NotificationContext for PO confirmation
        """
        return NotificationContext(
            notification_type=NotificationType.PO_CONFIRMED,
            category=NotificationTypeCategory.PURCHASE_ORDER,
            title=f"Purchase Order #{po.po_number} Confirmed",
            message=f"Purchase Order #{po.po_number} has been confirmed by the seller",
            related_po_id=po.id,
            related_company_id=po.seller_company_id,
            business_context={
                "po_number": po.po_number,
                "product_name": po.product_name,
                "confirmed_by_user_id": str(confirmed_by_user_id),
                "confirmation_date": confirmation_details.get("confirmation_date") if confirmation_details else None,
                "seller_notes": confirmation_details.get("seller_notes") if confirmation_details else None,
                "estimated_delivery": confirmation_details.get("estimated_delivery") if confirmation_details else None,
                **(confirmation_details or {})
            },
            metadata={
                "event": "po_confirmed",
                "po_status": po.status.value if po.status else None,
                "confirmation_timestamp": confirmation_details.get("timestamp") if confirmation_details else None
            }
        )
    
    def notify_po_status_changed(
        self,
        po: PurchaseOrder,
        old_status: str,
        new_status: str,
        changed_by_user_id: UUID,
        change_reason: Optional[str] = None
    ) -> NotificationContext:
        """
        Create notification context for PO status change.
        
        Args:
            po: Purchase order with status change
            old_status: Previous status
            new_status: New status
            changed_by_user_id: User who changed the status
            change_reason: Reason for status change
            
        Returns:
            NotificationContext for PO status change
        """
        return NotificationContext(
            notification_type=NotificationType.PO_STATUS_CHANGED,
            category=NotificationTypeCategory.PURCHASE_ORDER,
            title=f"Purchase Order #{po.po_number} Status Updated",
            message=f"Purchase Order #{po.po_number} status changed from {old_status} to {new_status}",
            related_po_id=po.id,
            related_company_id=po.buyer_company_id,
            business_context={
                "po_number": po.po_number,
                "product_name": po.product_name,
                "old_status": old_status,
                "new_status": new_status,
                "changed_by_user_id": str(changed_by_user_id),
                "change_reason": change_reason,
                "change_timestamp": po.updated_at.isoformat() if po.updated_at else None
            },
            metadata={
                "event": "po_status_changed",
                "status_transition": f"{old_status}_to_{new_status}",
                "change_reason": change_reason
            }
        )
    
    def get_po_notification_targets(
        self,
        po: PurchaseOrder,
        notification_type: NotificationType
    ) -> List[NotificationTarget]:
        """
        Get notification targets for a PO-related notification.
        
        Args:
            po: Purchase order
            notification_type: Type of notification
            
        Returns:
            List of notification targets
        """
        targets = []
        
        try:
            # Get buyer company users
            if notification_type in [
                NotificationType.PO_CONFIRMED,
                NotificationType.PO_STATUS_CHANGED
            ]:
                buyer_users = self._get_company_notification_users(po.buyer_company_id)
                targets.extend(buyer_users)
            
            # Get seller company users
            if notification_type in [
                NotificationType.PO_CREATED,
                NotificationType.PO_STATUS_CHANGED
            ]:
                seller_users = self._get_company_notification_users(po.seller_company_id)
                targets.extend(seller_users)
            
            logger.debug(
                "PO notification targets identified",
                po_id=str(po.id),
                notification_type=notification_type.value,
                target_count=len(targets)
            )
            
            return targets
            
        except Exception as e:
            logger.error(
                "Failed to get PO notification targets",
                po_id=str(po.id),
                notification_type=notification_type.value,
                error=str(e)
            )
            return []
    
    def _get_company_notification_users(self, company_id: UUID) -> List[NotificationTarget]:
        """
        Get users from a company who should receive notifications.
        
        Args:
            company_id: Company UUID
            
        Returns:
            List of notification targets for company users
        """
        from app.models.user import User
        
        try:
            # Get active users from the company
            users = self.db.query(User).filter(
                User.company_id == company_id,
                User.is_active == True
            ).all()
            
            targets = []
            for user in users:
                target = NotificationTarget(
                    user_id=user.id,
                    company_id=company_id,
                    email=user.email,
                    timezone=getattr(user, 'timezone', None),
                    language=getattr(user, 'language', 'en')
                )
                targets.append(target)
            
            return targets
            
        except Exception as e:
            logger.error(
                "Failed to get company notification users",
                company_id=str(company_id),
                error=str(e)
            )
            return []
