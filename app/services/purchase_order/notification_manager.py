"""
Purchase order notification manager.

This module handles notifications for purchase order events,
managing communication between buyers and sellers.
"""

from typing import Dict, Any, Optional, List
from uuid import UUID
from sqlalchemy.orm import Session

from app.models.purchase_order import PurchaseOrder
from app.core.logging import get_logger
from .exceptions import PurchaseOrderNotificationError

logger = get_logger(__name__)


class NotificationManager:
    """Handles notifications for purchase order events."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def notify_po_created(
        self, 
        po: PurchaseOrder, 
        created_by_company_id: UUID,
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Send notification for purchase order creation.
        
        Args:
            po: Created purchase order
            created_by_company_id: ID of company that created the PO
            context: Additional context for notification
        """
        try:
            logger.info(
                "Sending PO creation notification",
                po_id=str(po.id),
                po_number=po.po_number,
                created_by=str(created_by_company_id)
            )
            
            # Determine recipient (the other party)
            recipient_company_id = (
                po.seller_company_id if created_by_company_id == po.buyer_company_id 
                else po.buyer_company_id
            )
            
            # Prepare notification data
            notification_data = {
                "event_type": "po_created",
                "po_id": str(po.id),
                "po_number": po.po_number,
                "created_by_company_id": str(created_by_company_id),
                "recipient_company_id": str(recipient_company_id),
                "buyer_company_id": str(po.buyer_company_id),
                "seller_company_id": str(po.seller_company_id),
                "product_id": str(po.product_id),
                "total_amount": float(po.total_amount),
                "delivery_date": po.delivery_date.isoformat() if po.delivery_date else None,
                "status": po.status,
                "context": context or {}
            }
            
            # Send notification using notification service
            self._send_notification(
                notification_type="po_created",
                recipient_company_id=recipient_company_id,
                data=notification_data
            )
            
            logger.info(
                "PO creation notification sent successfully",
                po_id=str(po.id),
                recipient_company_id=str(recipient_company_id)
            )
            
        except Exception as e:
            logger.error(
                "Failed to send PO creation notification",
                po_id=str(po.id),
                error=str(e)
            )
            raise PurchaseOrderNotificationError(
                "Failed to send PO creation notification",
                po_id=po.id,
                notification_type="po_created"
            )
    
    def notify_po_updated(
        self, 
        po: PurchaseOrder, 
        updated_by_company_id: UUID,
        changed_fields: List[str],
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Send notification for purchase order update.
        
        Args:
            po: Updated purchase order
            updated_by_company_id: ID of company that updated the PO
            changed_fields: List of fields that were changed
            context: Additional context for notification
        """
        try:
            logger.info(
                "Sending PO update notification",
                po_id=str(po.id),
                po_number=po.po_number,
                updated_by=str(updated_by_company_id),
                changed_fields=changed_fields
            )
            
            # Determine recipient (the other party)
            recipient_company_id = (
                po.seller_company_id if updated_by_company_id == po.buyer_company_id 
                else po.buyer_company_id
            )
            
            # Prepare notification data
            notification_data = {
                "event_type": "po_updated",
                "po_id": str(po.id),
                "po_number": po.po_number,
                "updated_by_company_id": str(updated_by_company_id),
                "recipient_company_id": str(recipient_company_id),
                "changed_fields": changed_fields,
                "current_status": po.status,
                "total_amount": float(po.total_amount),
                "context": context or {}
            }
            
            # Send notification
            self._send_notification(
                notification_type="po_updated",
                recipient_company_id=recipient_company_id,
                data=notification_data
            )
            
            logger.info(
                "PO update notification sent successfully",
                po_id=str(po.id),
                recipient_company_id=str(recipient_company_id)
            )
            
        except Exception as e:
            logger.error(
                "Failed to send PO update notification",
                po_id=str(po.id),
                error=str(e)
            )
            # Don't raise exception for notification failures in updates
            # as the update operation should still succeed
    
    def notify_status_changed(
        self, 
        po: PurchaseOrder, 
        old_status: str,
        new_status: str,
        changed_by_company_id: UUID,
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Send notification for purchase order status change.
        
        Args:
            po: Purchase order with status change
            old_status: Previous status
            new_status: New status
            changed_by_company_id: ID of company that changed the status
            context: Additional context for notification
        """
        try:
            logger.info(
                "Sending PO status change notification",
                po_id=str(po.id),
                po_number=po.po_number,
                old_status=old_status,
                new_status=new_status,
                changed_by=str(changed_by_company_id)
            )
            
            # Determine recipient (the other party)
            recipient_company_id = (
                po.seller_company_id if changed_by_company_id == po.buyer_company_id 
                else po.buyer_company_id
            )
            
            # Prepare notification data
            notification_data = {
                "event_type": "po_status_changed",
                "po_id": str(po.id),
                "po_number": po.po_number,
                "changed_by_company_id": str(changed_by_company_id),
                "recipient_company_id": str(recipient_company_id),
                "old_status": old_status,
                "new_status": new_status,
                "status_transition": f"{old_status} -> {new_status}",
                "context": context or {}
            }
            
            # Send notification
            self._send_notification(
                notification_type="po_status_changed",
                recipient_company_id=recipient_company_id,
                data=notification_data
            )
            
            logger.info(
                "PO status change notification sent successfully",
                po_id=str(po.id),
                recipient_company_id=str(recipient_company_id)
            )
            
        except Exception as e:
            logger.error(
                "Failed to send PO status change notification",
                po_id=str(po.id),
                error=str(e)
            )
            # Don't raise exception for notification failures
    
    def notify_po_deleted(
        self, 
        po: PurchaseOrder, 
        deleted_by_company_id: UUID,
        reason: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Send notification for purchase order deletion.
        
        Args:
            po: Purchase order being deleted
            deleted_by_company_id: ID of company that deleted the PO
            reason: Optional reason for deletion
            context: Additional context for notification
        """
        try:
            logger.info(
                "Sending PO deletion notification",
                po_id=str(po.id),
                po_number=po.po_number,
                deleted_by=str(deleted_by_company_id),
                reason=reason
            )
            
            # Determine recipient (the other party)
            recipient_company_id = (
                po.seller_company_id if deleted_by_company_id == po.buyer_company_id 
                else po.buyer_company_id
            )
            
            # Prepare notification data
            notification_data = {
                "event_type": "po_deleted",
                "po_id": str(po.id),
                "po_number": po.po_number,
                "deleted_by_company_id": str(deleted_by_company_id),
                "recipient_company_id": str(recipient_company_id),
                "deletion_reason": reason,
                "context": context or {}
            }
            
            # Send notification
            self._send_notification(
                notification_type="po_deleted",
                recipient_company_id=recipient_company_id,
                data=notification_data
            )
            
            logger.info(
                "PO deletion notification sent successfully",
                po_id=str(po.id),
                recipient_company_id=str(recipient_company_id)
            )
            
        except Exception as e:
            logger.error(
                "Failed to send PO deletion notification",
                po_id=str(po.id),
                error=str(e)
            )
            # Don't raise exception for notification failures in deletion
    
    def notify_delivery_reminder(
        self, 
        po: PurchaseOrder,
        days_until_delivery: int,
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Send delivery reminder notification.
        
        Args:
            po: Purchase order with upcoming delivery
            days_until_delivery: Number of days until delivery
            context: Additional context for notification
        """
        try:
            logger.info(
                "Sending delivery reminder notification",
                po_id=str(po.id),
                po_number=po.po_number,
                days_until_delivery=days_until_delivery
            )
            
            # Send to both buyer and seller
            notification_data = {
                "event_type": "delivery_reminder",
                "po_id": str(po.id),
                "po_number": po.po_number,
                "days_until_delivery": days_until_delivery,
                "delivery_date": po.delivery_date.isoformat() if po.delivery_date else None,
                "delivery_location": po.delivery_location,
                "context": context or {}
            }
            
            # Send to buyer
            self._send_notification(
                notification_type="delivery_reminder",
                recipient_company_id=po.buyer_company_id,
                data={**notification_data, "recipient_role": "buyer"}
            )
            
            # Send to seller
            self._send_notification(
                notification_type="delivery_reminder",
                recipient_company_id=po.seller_company_id,
                data={**notification_data, "recipient_role": "seller"}
            )
            
            logger.info(
                "Delivery reminder notifications sent successfully",
                po_id=str(po.id)
            )
            
        except Exception as e:
            logger.error(
                "Failed to send delivery reminder notification",
                po_id=str(po.id),
                error=str(e)
            )
    
    def _send_notification(
        self, 
        notification_type: str,
        recipient_company_id: UUID,
        data: Dict[str, Any]
    ) -> None:
        """
        Send notification using the notification service.
        
        Args:
            notification_type: Type of notification
            recipient_company_id: ID of recipient company
            data: Notification data
        """
        try:
            # Import here to avoid circular imports
            from app.services.notification_events import NotificationEventTrigger
            
            notification_trigger = NotificationEventTrigger(self.db)
            
            # Map notification types to trigger methods
            if notification_type == "po_created":
                notification_trigger.trigger_po_created(
                    po_id=UUID(data["po_id"]),
                    created_by_user_id=data["created_by_company_id"]  # This should be user_id
                )
            elif notification_type == "po_updated":
                notification_trigger.trigger_po_updated(
                    po_id=UUID(data["po_id"]),
                    updated_by_user_id=data["updated_by_company_id"]  # This should be user_id
                )
            elif notification_type == "po_status_changed":
                notification_trigger.trigger_po_status_changed(
                    po_id=UUID(data["po_id"]),
                    old_status=data["old_status"],
                    new_status=data["new_status"],
                    changed_by_user_id=data["changed_by_company_id"]  # This should be user_id
                )
            elif notification_type == "amendment_proposed":
                # For now, log the amendment proposal notification
                logger.info(
                    "Amendment proposal notification",
                    po_id=data["po_id"],
                    po_number=data["po_number"],
                    proposed_quantity=data["proposed_quantity"],
                    reason=data["amendment_reason"]
                )
            elif notification_type == "amendment_approved":
                # For now, log the amendment approval notification
                logger.info(
                    "Amendment approval notification",
                    po_id=data["po_id"],
                    po_number=data["po_number"],
                    new_quantity=data["new_quantity"]
                )
            elif notification_type == "amendment_rejected":
                # For now, log the amendment rejection notification
                logger.info(
                    "Amendment rejection notification",
                    po_id=data["po_id"],
                    po_number=data["po_number"],
                    buyer_notes=data.get("buyer_notes")
                )
            # Add other notification types as needed
            
        except ImportError:
            logger.warning(
                "Notification service not available, skipping notification",
                notification_type=notification_type,
                recipient_company_id=str(recipient_company_id)
            )
        except Exception as e:
            logger.error(
                "Failed to send notification via notification service",
                notification_type=notification_type,
                recipient_company_id=str(recipient_company_id),
                error=str(e)
            )
            raise

    # Phase 1 MVP Amendment Notification Methods

    def notify_amendment_proposed(
        self,
        po: PurchaseOrder,
        proposer,
        proposal,
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Send notification for amendment proposal.

        Args:
            po: Purchase order with proposed amendment
            proposer: User who proposed the amendment
            proposal: Amendment proposal data
            context: Additional context
        """
        try:
            logger.info(
                "Sending amendment proposal notification",
                po_id=str(po.id),
                po_number=po.po_number,
                proposer_id=str(proposer.id)
            )

            # Notify buyer about the amendment proposal
            notification_data = {
                "po_id": str(po.id),
                "po_number": po.po_number,
                "proposer_company_id": str(proposer.company_id),
                "proposed_quantity": str(proposal.proposed_quantity),
                "proposed_unit": proposal.proposed_quantity_unit,
                "amendment_reason": proposal.amendment_reason,
                "original_quantity": str(po.quantity),
                "original_unit": po.unit
            }

            if context:
                notification_data.update(context)

            self._send_notification(
                notification_type="amendment_proposed",
                recipient_company_id=po.buyer_company_id,
                data=notification_data
            )

        except Exception as e:
            logger.error(f"Failed to send amendment proposal notification: {str(e)}")
            raise PurchaseOrderNotificationError(f"Amendment proposal notification failed: {str(e)}")

    def notify_amendment_approved(
        self,
        po: PurchaseOrder,
        approver,
        approval,
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Send notification for amendment approval.

        Args:
            po: Purchase order with approved amendment
            approver: User who approved the amendment
            approval: Approval data
            context: Additional context
        """
        try:
            logger.info(
                "Sending amendment approval notification",
                po_id=str(po.id),
                po_number=po.po_number,
                approver_id=str(approver.id)
            )

            # Notify seller about the amendment approval
            notification_data = {
                "po_id": str(po.id),
                "po_number": po.po_number,
                "approver_company_id": str(approver.company_id),
                "buyer_notes": approval.buyer_notes,
                "new_quantity": str(po.quantity),
                "new_unit": po.unit
            }

            if context:
                notification_data.update(context)

            self._send_notification(
                notification_type="amendment_approved",
                recipient_company_id=po.seller_company_id,
                data=notification_data
            )

        except Exception as e:
            logger.error(f"Failed to send amendment approval notification: {str(e)}")
            raise PurchaseOrderNotificationError(f"Amendment approval notification failed: {str(e)}")

    def notify_amendment_rejected(
        self,
        po: PurchaseOrder,
        rejector,
        approval,
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Send notification for amendment rejection.

        Args:
            po: Purchase order with rejected amendment
            rejector: User who rejected the amendment
            approval: Rejection data
            context: Additional context
        """
        try:
            logger.info(
                "Sending amendment rejection notification",
                po_id=str(po.id),
                po_number=po.po_number,
                rejector_id=str(rejector.id)
            )

            # Notify seller about the amendment rejection
            notification_data = {
                "po_id": str(po.id),
                "po_number": po.po_number,
                "rejector_company_id": str(rejector.company_id),
                "buyer_notes": approval.buyer_notes,
                "original_quantity": str(po.quantity),
                "original_unit": po.unit
            }

            if context:
                notification_data.update(context)

            self._send_notification(
                notification_type="amendment_rejected",
                recipient_company_id=po.seller_company_id,
                data=notification_data
            )

        except Exception as e:
            logger.error(f"Failed to send amendment rejection notification: {str(e)}")
            raise PurchaseOrderNotificationError(f"Amendment rejection notification failed: {str(e)}")
