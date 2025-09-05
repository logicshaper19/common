"""
Background job processing for transparency calculations.
"""
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime, timedelta
from celery import Task
from celery.exceptions import Retry, MaxRetriesExceededError
from sqlalchemy.orm import Session
import json

from app.celery_app import celery_app
from app.core.database import get_db
from app.core.redis import get_redis, RedisCache
from app.core.logging import get_logger
from app.services.transparency_engine import TransparencyCalculationEngine, TransparencyResult
from app.models.purchase_order import PurchaseOrder
from app.models.audit_event import AuditEvent

logger = get_logger(__name__)


class TransparencyCalculationTask(Task):
    """
    Custom Celery task class for transparency calculations with enhanced error handling.
    """
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Handle task failure."""
        logger.error(
            "Transparency calculation task failed",
            task_id=task_id,
            args=args,
            kwargs=kwargs,
            error=str(exc),
            traceback=str(einfo)
        )
        
        # Record failure in audit log
        try:
            db = next(get_db())
            po_id = args[0] if args else kwargs.get('po_id')
            
            audit_event = AuditEvent(
                event_type="transparency_calculation_failed",
                entity_type="purchase_order",
                entity_id=po_id,
                details={
                    "task_id": task_id,
                    "error": str(exc),
                    "retry_count": self.request.retries,
                    "max_retries": self.max_retries
                }
            )
            db.add(audit_event)
            db.commit()
        except Exception as audit_error:
            logger.error("Failed to record audit event", error=str(audit_error))
        finally:
            db.close()
    
    def on_success(self, retval, task_id, args, kwargs):
        """Handle task success."""
        logger.info(
            "Transparency calculation task completed successfully",
            task_id=task_id,
            args=args,
            kwargs=kwargs
        )
    
    def on_retry(self, exc, task_id, args, kwargs, einfo):
        """Handle task retry."""
        logger.warning(
            "Transparency calculation task retrying",
            task_id=task_id,
            args=args,
            kwargs=kwargs,
            error=str(exc),
            retry_count=self.request.retries
        )


@celery_app.task(
    bind=True,
    base=TransparencyCalculationTask,
    autoretry_for=(Exception,),
    retry_kwargs={'max_retries': 3, 'countdown': 60},
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True
)
def calculate_transparency_async(self, po_id: str, force_recalculation: bool = False) -> Dict[str, Any]:
    """
    Asynchronously calculate transparency scores for a purchase order.
    
    Args:
        po_id: Purchase order UUID as string
        force_recalculation: Force recalculation even if cached
        
    Returns:
        Dictionary containing transparency calculation results
    """
    start_time = datetime.utcnow()
    
    logger.info(
        "Starting async transparency calculation",
        task_id=self.request.id,
        po_id=po_id,
        force_recalculation=force_recalculation
    )
    
    db = None
    try:
        # Get database session
        db = next(get_db())
        
        # Check if PO exists
        po = db.query(PurchaseOrder).filter(PurchaseOrder.id == UUID(po_id)).first()
        if not po:
            raise ValueError(f"Purchase order {po_id} not found")
        
        # Check cache first (unless force recalculation)
        cache_key = f"transparency:{po_id}"
        cached_result = None

        if not force_recalculation:
            try:
                import asyncio
                redis_client = asyncio.run(get_redis())
                cache = RedisCache(redis_client)
                cached_result = asyncio.run(cache.get(cache_key))
                
                if cached_result:
                    logger.info(
                        "Using cached transparency result",
                        po_id=po_id,
                        cache_age_minutes=(datetime.utcnow() - datetime.fromisoformat(cached_result['calculated_at'])).total_seconds() / 60
                    )
                    return cached_result
            except Exception as cache_error:
                logger.warning("Cache lookup failed, proceeding with calculation", error=str(cache_error))
        
        # Calculate transparency scores
        transparency_engine = TransparencyCalculationEngine(db)
        result = transparency_engine.calculate_transparency(
            po_id=UUID(po_id),
            force_recalculation=force_recalculation,
            include_detailed_analysis=False  # Skip detailed analysis for background jobs
        )
        
        # Update purchase order with new scores
        po.transparency_to_mill = result.ttm_score
        po.transparency_to_plantation = result.ttp_score
        po.transparency_calculated_at = result.calculated_at
        db.commit()
        
        # Prepare result for caching and return
        result_dict = {
            "po_id": str(result.po_id),
            "ttm_score": result.ttm_score,
            "ttp_score": result.ttp_score,
            "confidence_level": result.confidence_level,
            "traced_percentage": result.traced_percentage,
            "untraced_percentage": result.untraced_percentage,
            "total_nodes": result.total_nodes,
            "max_depth": result.max_depth,
            "circular_references": [str(ref) for ref in result.circular_references],
            "degradation_applied": result.degradation_applied,
            "calculated_at": result.calculated_at.isoformat(),
            "calculation_duration_ms": result.calculation_duration_ms,
            "task_id": self.request.id
        }
        
        # Cache the result for 1 hour
        try:
            import asyncio
            redis_client = asyncio.run(get_redis())
            cache = RedisCache(redis_client)
            asyncio.run(cache.set(cache_key, result_dict, expire=3600))
            logger.info("Transparency result cached", po_id=po_id)
        except Exception as cache_error:
            logger.warning("Failed to cache result", error=str(cache_error))
        
        # Record success in audit log
        audit_event = AuditEvent(
            event_type="transparency_calculation_completed",
            entity_type="purchase_order",
            entity_id=UUID(po_id),
            details={
                "task_id": self.request.id,
                "ttm_score": result.ttm_score,
                "ttp_score": result.ttp_score,
                "confidence_level": result.confidence_level,
                "calculation_duration_ms": result.calculation_duration_ms,
                "total_nodes": result.total_nodes
            }
        )
        db.add(audit_event)
        db.commit()
        
        end_time = datetime.utcnow()
        duration_ms = (end_time - start_time).total_seconds() * 1000
        
        logger.info(
            "Async transparency calculation completed",
            task_id=self.request.id,
            po_id=po_id,
            ttm_score=result.ttm_score,
            ttp_score=result.ttp_score,
            duration_ms=duration_ms
        )
        
        return result_dict
        
    except Exception as e:
        logger.error(
            "Async transparency calculation failed",
            task_id=self.request.id,
            po_id=po_id,
            error=str(e)
        )
        
        # If this is the final retry, mark the PO as having a calculation error
        if self.request.retries >= self.max_retries:
            try:
                if db:
                    po = db.query(PurchaseOrder).filter(PurchaseOrder.id == UUID(po_id)).first()
                    if po:
                        po.transparency_calculated_at = datetime.utcnow()
                        # Could add an error flag field to the model
                        db.commit()
            except Exception as update_error:
                logger.error("Failed to update PO after calculation failure", error=str(update_error))
        
        raise
        
    finally:
        if db:
            db.close()


@celery_app.task(
    bind=True,
    autoretry_for=(Exception,),
    retry_kwargs={'max_retries': 2, 'countdown': 30}
)
def bulk_recalculate_transparency(self, po_ids: List[str], force_recalculation: bool = False) -> Dict[str, Any]:
    """
    Bulk recalculate transparency scores for multiple purchase orders.
    
    Args:
        po_ids: List of purchase order UUIDs as strings
        force_recalculation: Force recalculation even if cached
        
    Returns:
        Dictionary containing bulk calculation results
    """
    start_time = datetime.utcnow()
    
    logger.info(
        "Starting bulk transparency recalculation",
        task_id=self.request.id,
        po_count=len(po_ids),
        force_recalculation=force_recalculation
    )
    
    results = {
        "total_pos": len(po_ids),
        "successful": 0,
        "failed": 0,
        "errors": [],
        "task_id": self.request.id
    }
    
    # Process each PO
    for po_id in po_ids:
        try:
            # Schedule individual calculation task
            task = calculate_transparency_async.delay(po_id, force_recalculation)
            results["successful"] += 1
            
            logger.debug(
                "Scheduled transparency calculation",
                po_id=po_id,
                subtask_id=task.id
            )
            
        except Exception as e:
            results["failed"] += 1
            results["errors"].append({
                "po_id": po_id,
                "error": str(e)
            })
            
            logger.error(
                "Failed to schedule transparency calculation",
                po_id=po_id,
                error=str(e)
            )
    
    end_time = datetime.utcnow()
    duration_ms = (end_time - start_time).total_seconds() * 1000
    
    logger.info(
        "Bulk transparency recalculation completed",
        task_id=self.request.id,
        total_pos=results["total_pos"],
        successful=results["successful"],
        failed=results["failed"],
        duration_ms=duration_ms
    )
    
    return results


@celery_app.task(bind=True)
def invalidate_transparency_cache(self, po_ids: List[str]) -> Dict[str, Any]:
    """
    Invalidate transparency cache for specified purchase orders.
    
    Args:
        po_ids: List of purchase order UUIDs as strings
        
    Returns:
        Dictionary containing invalidation results
    """
    logger.info(
        "Starting transparency cache invalidation",
        task_id=self.request.id,
        po_count=len(po_ids)
    )
    
    results = {
        "total_pos": len(po_ids),
        "invalidated": 0,
        "errors": [],
        "task_id": self.request.id
    }
    
    try:
        import asyncio
        redis_client = asyncio.run(get_redis())
        cache = RedisCache(redis_client)

        for po_id in po_ids:
            try:
                cache_key = f"transparency:{po_id}"
                asyncio.run(cache.delete(cache_key))
                results["invalidated"] += 1
                
                logger.debug("Invalidated transparency cache", po_id=po_id)
                
            except Exception as e:
                results["errors"].append({
                    "po_id": po_id,
                    "error": str(e)
                })
                
                logger.error(
                    "Failed to invalidate transparency cache",
                    po_id=po_id,
                    error=str(e)
                )
        
    except Exception as e:
        logger.error(
            "Failed to connect to Redis for cache invalidation",
            error=str(e)
        )
        results["errors"].append({
            "error": f"Redis connection failed: {str(e)}"
        })
    
    logger.info(
        "Transparency cache invalidation completed",
        task_id=self.request.id,
        total_pos=results["total_pos"],
        invalidated=results["invalidated"],
        errors_count=len(results["errors"])
    )
    
    return results
