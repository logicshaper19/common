"""
API endpoints for transparency job monitoring and management.
"""
from typing import List, Optional, Dict, Any
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.services.transparency_jobs import (
    calculate_transparency_async,
    bulk_recalculate_transparency,
    invalidate_transparency_cache
)
# TransparencyScheduler not implemented yet - using job functions directly
# from app.services.transparency_scheduler import TransparencyScheduler
# Using RedisCache directly instead of non-existent TransparencyCache
from app.core.redis import get_redis, RedisCache
from app.services.job_monitor import TransparencyJobMonitor, JobStatus, JobPriority
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/transparency-jobs", tags=["transparency-jobs"])


# Request/Response Models
class TransparencyJobRequest(BaseModel):
    """Request to schedule transparency calculation."""
    purchase_order_id: UUID
    force_recalculation: bool = Field(False, description="Force recalculation even if cached")
    priority: JobPriority = Field(JobPriority.NORMAL, description="Job priority")
    delay_seconds: Optional[int] = Field(None, description="Delay before execution")


class BulkTransparencyJobRequest(BaseModel):
    """Request to schedule bulk transparency calculations."""
    purchase_order_ids: List[UUID]
    force_recalculation: bool = Field(False, description="Force recalculation even if cached")
    priority: JobPriority = Field(JobPriority.NORMAL, description="Job priority")


class CacheWarmingRequest(BaseModel):
    """Request to warm transparency cache."""
    purchase_order_ids: List[UUID]
    priority: JobPriority = Field(JobPriority.NORMAL, description="Warming priority")


class JobResponse(BaseModel):
    """Response for job operations."""
    success: bool
    task_id: Optional[str] = None
    message: str
    details: Optional[Dict[str, Any]] = None


class JobStatusResponse(BaseModel):
    """Response for job status."""
    task_id: str
    status: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    duration_seconds: Optional[float] = None
    retry_count: int = 0


class QueueStatsResponse(BaseModel):
    """Response for queue statistics."""
    transparency_queue: Dict[str, int]
    workers: List[Dict[str, Any]]
    total_active: int
    total_scheduled: int


class PerformanceMetricsResponse(BaseModel):
    """Response for performance metrics."""
    period_hours: int
    total_jobs: int
    completed_jobs: int
    failed_jobs: int
    success_rate: float
    average_duration_ms: float
    jobs_per_hour: float


@router.post("/schedule", response_model=JobResponse)
async def schedule_transparency_calculation(
    request: TransparencyJobRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> JobResponse:
    """
    Schedule transparency calculation for a purchase order.
    
    This endpoint schedules an asynchronous transparency calculation job
    with configurable priority and delay settings.
    """
    try:
        # Direct job scheduling using available functions
        task_id = calculate_transparency_async.apply_async(
            args=[str(request.purchase_order_id)],
            countdown=request.delay_seconds,
            priority=request.priority.value if request.priority else 5
        ).id
        
        logger.info(
            "Transparency calculation scheduled via API",
            po_id=str(request.purchase_order_id),
            task_id=task_id,
            user_id=str(current_user.id)
        )
        
        return JobResponse(
            success=True,
            task_id=task_id,
            message="Transparency calculation scheduled successfully",
            details={
                "purchase_order_id": str(request.purchase_order_id),
                "priority": request.priority,
                "delay_seconds": request.delay_seconds
            }
        )
        
    except Exception as e:
        logger.error(
            "Failed to schedule transparency calculation",
            po_id=str(request.purchase_order_id),
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to schedule transparency calculation: {str(e)}"
        )


@router.post("/bulk-schedule", response_model=JobResponse)
async def schedule_bulk_transparency_calculation(
    request: BulkTransparencyJobRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> JobResponse:
    """
    Schedule bulk transparency calculations for multiple purchase orders.
    
    This endpoint is useful for recalculating transparency scores for
    large batches of purchase orders efficiently.
    """
    try:
        po_id_strings = [str(po_id) for po_id in request.purchase_order_ids]
        
        # Schedule bulk calculation
        task = bulk_recalculate_transparency.delay(
            po_id_strings,
            request.force_recalculation
        )
        
        logger.info(
            "Bulk transparency calculation scheduled via API",
            po_count=len(request.purchase_order_ids),
            task_id=task.id,
            user_id=str(current_user.id)
        )
        
        return JobResponse(
            success=True,
            task_id=task.id,
            message=f"Bulk transparency calculation scheduled for {len(request.purchase_order_ids)} purchase orders",
            details={
                "purchase_order_count": len(request.purchase_order_ids),
                "priority": request.priority,
                "force_recalculation": request.force_recalculation
            }
        )
        
    except Exception as e:
        logger.error(
            "Failed to schedule bulk transparency calculation",
            po_count=len(request.purchase_order_ids),
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to schedule bulk transparency calculation: {str(e)}"
        )


@router.get("/status/{task_id}", response_model=JobStatusResponse)
async def get_job_status(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> JobStatusResponse:
    """
    Get status of a transparency calculation job.
    
    Returns detailed information about job progress, results, and any errors.
    """
    try:
        monitor = TransparencyJobMonitor(db)
        status_info = await monitor.get_job_status(task_id)
        
        return JobStatusResponse(
            task_id=task_id,
            status=status_info.get("status", "UNKNOWN"),
            result=status_info.get("result"),
            error=status_info.get("error"),
            started_at=status_info.get("started_at"),
            completed_at=status_info.get("completed_at"),
            duration_seconds=status_info.get("duration_seconds"),
            retry_count=status_info.get("retry_count", 0)
        )
        
    except Exception as e:
        logger.error("Failed to get job status", task_id=task_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get job status: {str(e)}"
        )


@router.get("/active", response_model=List[Dict[str, Any]])
async def get_active_jobs(
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """
    Get list of currently active transparency calculation jobs.
    
    Returns information about running and scheduled jobs.
    """
    try:
        monitor = TransparencyJobMonitor(db)
        active_jobs = await monitor.get_active_jobs(limit)
        
        return active_jobs
        
    except Exception as e:
        logger.error("Failed to get active jobs", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get active jobs: {str(e)}"
        )


@router.get("/failed", response_model=List[Dict[str, Any]])
async def get_failed_jobs(
    hours: int = Query(24, ge=1, le=168),  # Max 1 week
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """
    Get list of failed transparency calculation jobs.
    
    Returns information about jobs that failed within the specified time period.
    """
    try:
        monitor = TransparencyJobMonitor(db)
        failed_jobs = await monitor.get_failed_jobs(hours, limit)
        
        return failed_jobs
        
    except Exception as e:
        logger.error("Failed to get failed jobs", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get failed jobs: {str(e)}"
        )


@router.post("/retry/{task_id}", response_model=JobResponse)
async def retry_failed_job(
    task_id: str,
    force: bool = Query(False, description="Force retry even if max retries exceeded"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> JobResponse:
    """
    Retry a failed transparency calculation job.
    
    Creates a new job with the same parameters as the failed job.
    """
    try:
        monitor = TransparencyJobMonitor(db)
        result = await monitor.retry_failed_job(task_id, force)
        
        if result["success"]:
            return JobResponse(
                success=True,
                task_id=result.get("new_task_id"),
                message="Job retry scheduled successfully",
                details=result
            )
        else:
            return JobResponse(
                success=False,
                message=f"Failed to retry job: {result.get('error')}",
                details=result
            )
        
    except Exception as e:
        logger.error("Failed to retry job", task_id=task_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retry job: {str(e)}"
        )


@router.delete("/cancel/{task_id}", response_model=JobResponse)
async def cancel_job(
    task_id: str,
    terminate: bool = Query(False, description="Forcefully terminate the job"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> JobResponse:
    """
    Cancel a running or scheduled transparency calculation job.
    
    Can optionally terminate the job forcefully if it's currently running.
    """
    try:
        monitor = TransparencyJobMonitor(db)
        result = await monitor.cancel_job(task_id, terminate)
        
        if result["success"]:
            return JobResponse(
                success=True,
                message="Job cancelled successfully",
                details=result
            )
        else:
            return JobResponse(
                success=False,
                message=f"Failed to cancel job: {result.get('error')}",
                details=result
            )
        
    except Exception as e:
        logger.error("Failed to cancel job", task_id=task_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cancel job: {str(e)}"
        )


@router.get("/queue-stats", response_model=QueueStatsResponse)
async def get_queue_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> QueueStatsResponse:
    """
    Get transparency job queue statistics.
    
    Returns information about active, scheduled, and reserved jobs.
    """
    try:
        monitor = TransparencyJobMonitor(db)
        stats = await monitor.get_queue_stats()
        
        return QueueStatsResponse(
            transparency_queue=stats["transparency_queue"],
            workers=stats["workers"],
            total_active=stats["total_active"],
            total_scheduled=stats["total_scheduled"]
        )
        
    except Exception as e:
        logger.error("Failed to get queue stats", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get queue statistics: {str(e)}"
        )


@router.get("/metrics", response_model=PerformanceMetricsResponse)
async def get_performance_metrics(
    hours: int = Query(24, ge=1, le=168),  # Max 1 week
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> PerformanceMetricsResponse:
    """
    Get transparency job performance metrics.
    
    Returns statistics about job completion rates, durations, and throughput.
    """
    try:
        monitor = TransparencyJobMonitor(db)
        metrics = await monitor.get_performance_metrics(hours)
        
        return PerformanceMetricsResponse(
            period_hours=metrics["period_hours"],
            total_jobs=metrics["total_jobs"],
            completed_jobs=metrics["completed_jobs"],
            failed_jobs=metrics["failed_jobs"],
            success_rate=metrics["success_rate"],
            average_duration_ms=metrics["average_duration_ms"],
            jobs_per_hour=metrics["jobs_per_hour"]
        )
        
    except Exception as e:
        logger.error("Failed to get performance metrics", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get performance metrics: {str(e)}"
        )


@router.post("/cache/warm", response_model=JobResponse)
async def warm_transparency_cache(
    request: CacheWarmingRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> JobResponse:
    """
    Warm transparency cache for frequently accessed purchase orders.
    
    Pre-calculates transparency scores for specified POs to improve response times.
    """
    try:
        # Use bulk recalculation to warm cache
        task_id = bulk_recalculate_transparency.apply_async(
            args=[request.purchase_order_ids],
            kwargs={"force_recalculation": False},  # Don't force, just ensure cached
            priority=request.priority.value if request.priority else 5
        ).id

        return JobResponse(
            success=True,
            message=f"Cache warming scheduled for {len(request.purchase_order_ids)} purchase orders",
            details={
                "task_id": task_id,
                "scheduled": len(request.purchase_order_ids),
                "purchase_order_ids": request.purchase_order_ids
            }
        )
        
    except Exception as e:
        logger.error("Failed to warm cache", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to warm cache: {str(e)}"
        )


@router.delete("/cache/invalidate", response_model=JobResponse)
async def invalidate_transparency_cache(
    purchase_order_ids: List[UUID],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> JobResponse:
    """
    Invalidate transparency cache for specified purchase orders.
    
    Forces recalculation on next access by removing cached results.
    """
    try:
        po_id_strings = [str(po_id) for po_id in purchase_order_ids]
        
        # Schedule cache invalidation
        task = invalidate_transparency_cache.delay(po_id_strings)
        
        return JobResponse(
            success=True,
            task_id=task.id,
            message=f"Cache invalidation scheduled for {len(purchase_order_ids)} purchase orders"
        )
        
    except Exception as e:
        logger.error("Failed to invalidate cache", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to invalidate cache: {str(e)}"
        )
