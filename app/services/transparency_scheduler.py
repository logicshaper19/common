"""
Transparency calculation job scheduler for automatic recalculation on PO changes.
"""
from typing import Optional, List, Dict, Any, Set
from uuid import UUID
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.core.database import get_db
from app.core.logging import get_logger
from app.services.transparency_jobs import (
    calculate_transparency_async,
    bulk_recalculate_transparency,
    invalidate_transparency_cache
)
from app.models.purchase_order import PurchaseOrder
from app.models.audit_event import AuditEvent

logger = get_logger(__name__)


class TransparencyScheduler:
    """
    Service for scheduling transparency calculations based on PO changes.
    
    This service handles:
    - Automatic scheduling when POs are created/updated
    - Dependency tracking for affected POs
    - Batch scheduling for efficiency
    - Cache invalidation coordination
    """
    
    def __init__(self, db: Session):
        self.db = db
        
        # Configuration
        self.RECALCULATION_DELAY_SECONDS = 30  # Wait 30 seconds before recalculating
        self.BATCH_SIZE = 50  # Maximum POs to process in one batch
        self.MAX_DEPENDENCY_DEPTH = 10  # Maximum depth to traverse for dependencies
    
    def schedule_po_transparency_update(
        self,
        po_id: UUID,
        trigger_event: str = "po_updated",
        delay_seconds: Optional[int] = None,
        force_recalculation: bool = False
    ) -> str:
        """
        Schedule transparency calculation for a specific PO.
        
        Args:
            po_id: Purchase order UUID
            trigger_event: Event that triggered the update
            delay_seconds: Delay before calculation (default: 30 seconds)
            force_recalculation: Force recalculation even if cached
            
        Returns:
            Task ID of the scheduled job
        """
        delay = delay_seconds or self.RECALCULATION_DELAY_SECONDS
        
        logger.info(
            "Scheduling transparency calculation",
            po_id=str(po_id),
            trigger_event=trigger_event,
            delay_seconds=delay,
            force_recalculation=force_recalculation
        )
        
        # Schedule the calculation task with delay
        task = calculate_transparency_async.apply_async(
            args=[str(po_id), force_recalculation],
            countdown=delay
        )
        
        # Record the scheduling event
        audit_event = AuditEvent(
            event_type="transparency_calculation_scheduled",
            entity_type="purchase_order",
            entity_id=po_id,
            details={
                "task_id": task.id,
                "trigger_event": trigger_event,
                "delay_seconds": delay,
                "force_recalculation": force_recalculation
            }
        )
        self.db.add(audit_event)
        self.db.commit()
        
        logger.info(
            "Transparency calculation scheduled",
            po_id=str(po_id),
            task_id=task.id,
            trigger_event=trigger_event
        )
        
        return task.id
    
    def schedule_dependent_po_updates(
        self,
        source_po_id: UUID,
        trigger_event: str = "dependency_updated",
        delay_seconds: Optional[int] = None
    ) -> List[str]:
        """
        Schedule transparency updates for all POs that depend on the source PO.
        
        Args:
            source_po_id: Source purchase order UUID
            trigger_event: Event that triggered the update
            delay_seconds: Delay before calculation
            
        Returns:
            List of task IDs for scheduled jobs
        """
        delay = delay_seconds or self.RECALCULATION_DELAY_SECONDS
        
        logger.info(
            "Finding dependent POs for transparency update",
            source_po_id=str(source_po_id),
            trigger_event=trigger_event
        )
        
        # Find all POs that depend on this source PO
        dependent_po_ids = self._find_dependent_pos(source_po_id)
        
        if not dependent_po_ids:
            logger.info(
                "No dependent POs found",
                source_po_id=str(source_po_id)
            )
            return []
        
        logger.info(
            "Found dependent POs for transparency update",
            source_po_id=str(source_po_id),
            dependent_count=len(dependent_po_ids)
        )
        
        # Schedule updates for dependent POs
        task_ids = []
        
        if len(dependent_po_ids) <= self.BATCH_SIZE:
            # Schedule individual tasks for small batches
            for po_id in dependent_po_ids:
                task_id = self.schedule_po_transparency_update(
                    po_id=po_id,
                    trigger_event=trigger_event,
                    delay_seconds=delay,
                    force_recalculation=True  # Force recalculation for dependencies
                )
                task_ids.append(task_id)
        else:
            # Use bulk processing for large batches
            po_id_strings = [str(po_id) for po_id in dependent_po_ids]
            task = bulk_recalculate_transparency.apply_async(
                args=[po_id_strings, True],  # Force recalculation
                countdown=delay
            )
            task_ids.append(task.id)
            
            logger.info(
                "Scheduled bulk transparency recalculation",
                source_po_id=str(source_po_id),
                dependent_count=len(dependent_po_ids),
                bulk_task_id=task.id
            )
        
        # Invalidate cache for all affected POs
        all_affected_po_ids = [str(source_po_id)] + [str(po_id) for po_id in dependent_po_ids]
        invalidate_transparency_cache.apply_async(
            args=[all_affected_po_ids],
            countdown=5  # Invalidate cache quickly
        )
        
        return task_ids
    
    def schedule_periodic_recalculation(
        self,
        company_id: Optional[UUID] = None,
        max_age_hours: int = 24,
        force_recalculation: bool = False
    ) -> str:
        """
        Schedule periodic recalculation for stale transparency scores.
        
        Args:
            company_id: Optional company ID to limit scope
            max_age_hours: Maximum age of scores before recalculation
            force_recalculation: Force recalculation even if cached
            
        Returns:
            Task ID of the bulk recalculation job
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)
        
        logger.info(
            "Scheduling periodic transparency recalculation",
            company_id=str(company_id) if company_id else "all",
            max_age_hours=max_age_hours,
            cutoff_time=cutoff_time.isoformat()
        )
        
        # Find POs with stale transparency scores
        query = self.db.query(PurchaseOrder).filter(
            or_(
                PurchaseOrder.transparency_calculated_at.is_(None),
                PurchaseOrder.transparency_calculated_at < cutoff_time
            ),
            PurchaseOrder.status.in_(["confirmed", "in_transit", "delivered"])
        )
        
        if company_id:
            query = query.filter(
                or_(
                    PurchaseOrder.buyer_company_id == company_id,
                    PurchaseOrder.seller_company_id == company_id
                )
            )
        
        stale_pos = query.limit(1000).all()  # Limit to prevent overwhelming the system
        
        if not stale_pos:
            logger.info("No stale transparency scores found")
            return None
        
        po_id_strings = [str(po.id) for po in stale_pos]
        
        # Schedule bulk recalculation
        task = bulk_recalculate_transparency.apply_async(
            args=[po_id_strings, force_recalculation],
            countdown=60  # Start in 1 minute
        )
        
        logger.info(
            "Scheduled periodic transparency recalculation",
            company_id=str(company_id) if company_id else "all",
            stale_po_count=len(stale_pos),
            task_id=task.id
        )
        
        return task.id
    
    def _find_dependent_pos(self, source_po_id: UUID, visited: Optional[Set[UUID]] = None) -> List[UUID]:
        """
        Find all POs that depend on the source PO (recursively).
        
        Args:
            source_po_id: Source purchase order UUID
            visited: Set of already visited POs (for cycle detection)
            
        Returns:
            List of dependent PO UUIDs
        """
        if visited is None:
            visited = set()
        
        if source_po_id in visited or len(visited) >= self.MAX_DEPENDENCY_DEPTH:
            return []
        
        visited.add(source_po_id)
        dependent_pos = []
        
        try:
            # Find POs that have this PO as an input material
            pos_with_inputs = self.db.query(PurchaseOrder).filter(
                PurchaseOrder.input_materials.isnot(None)
            ).all()
            
            for po in pos_with_inputs:
                if po.input_materials:
                    for input_material in po.input_materials:
                        if input_material.get("source_po_id") == str(source_po_id):
                            if po.id not in visited:
                                dependent_pos.append(po.id)
                                # Recursively find dependencies of this PO
                                nested_deps = self._find_dependent_pos(po.id, visited.copy())
                                dependent_pos.extend(nested_deps)
            
        except Exception as e:
            logger.error(
                "Error finding dependent POs",
                source_po_id=str(source_po_id),
                error=str(e)
            )
        
        # Remove duplicates while preserving order
        seen = set()
        unique_dependent_pos = []
        for po_id in dependent_pos:
            if po_id not in seen:
                seen.add(po_id)
                unique_dependent_pos.append(po_id)
        
        return unique_dependent_pos
    
    def get_scheduled_jobs_status(self, po_id: UUID) -> Dict[str, Any]:
        """
        Get status of scheduled transparency jobs for a PO.
        
        Args:
            po_id: Purchase order UUID
            
        Returns:
            Dictionary containing job status information
        """
        # Query recent audit events for this PO
        recent_events = self.db.query(AuditEvent).filter(
            AuditEvent.entity_type == "purchase_order",
            AuditEvent.entity_id == po_id,
            AuditEvent.event_type.in_([
                "transparency_calculation_scheduled",
                "transparency_calculation_completed",
                "transparency_calculation_failed"
            ]),
            AuditEvent.created_at > datetime.utcnow() - timedelta(hours=24)
        ).order_by(AuditEvent.created_at.desc()).limit(10).all()
        
        status = {
            "po_id": str(po_id),
            "recent_jobs": [],
            "last_calculation": None,
            "pending_jobs": 0,
            "failed_jobs": 0
        }
        
        for event in recent_events:
            job_info = {
                "event_type": event.event_type,
                "created_at": event.created_at.isoformat(),
                "details": event.details
            }
            status["recent_jobs"].append(job_info)
            
            if event.event_type == "transparency_calculation_completed":
                if not status["last_calculation"]:
                    status["last_calculation"] = event.created_at.isoformat()
            elif event.event_type == "transparency_calculation_scheduled":
                status["pending_jobs"] += 1
            elif event.event_type == "transparency_calculation_failed":
                status["failed_jobs"] += 1
        
        return status
