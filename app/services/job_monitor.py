"""
Job monitoring and error handling service for background transparency calculations.
"""
from typing import Optional, List, Dict, Any, Union
from uuid import UUID
from datetime import datetime, timedelta
from enum import Enum
from celery import Celery
from celery.result import AsyncResult
from sqlalchemy.orm import Session

from app.celery_app import celery_app
from app.core.database import get_db
from app.core.redis import get_redis, RedisCache
from app.core.logging import get_logger
from app.models.audit_event import AuditEvent

logger = get_logger(__name__)


class JobStatus(str, Enum):
    """Job status enumeration."""
    PENDING = "PENDING"
    STARTED = "STARTED"
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    RETRY = "RETRY"
    REVOKED = "REVOKED"


class JobPriority(str, Enum):
    """Job priority enumeration."""
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"


class TransparencyJobMonitor:
    """
    Service for monitoring and managing transparency calculation jobs.
    
    Features:
    - Job status tracking and reporting
    - Error detection and alerting
    - Performance monitoring
    - Job queue management
    - Automatic retry logic
    - Dead letter queue handling
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.celery_app = celery_app
        
        # Monitoring configuration
        self.JOB_TIMEOUT_MINUTES = 30
        self.MAX_RETRY_ATTEMPTS = 3
        self.DEAD_LETTER_TTL_HOURS = 24
        
        # Redis keys for monitoring
        self.ACTIVE_JOBS_KEY = "transparency:active_jobs"
        self.FAILED_JOBS_KEY = "transparency:failed_jobs"
        self.METRICS_KEY = "transparency:job_metrics"
    
    async def get_job_status(self, task_id: str) -> Dict[str, Any]:
        """
        Get detailed status of a transparency calculation job.
        
        Args:
            task_id: Celery task ID
            
        Returns:
            Dictionary containing job status and details
        """
        try:
            result = AsyncResult(task_id, app=self.celery_app)
            
            status_info = {
                "task_id": task_id,
                "status": result.status,
                "result": None,
                "error": None,
                "traceback": None,
                "started_at": None,
                "completed_at": None,
                "duration_seconds": None,
                "retry_count": 0,
                "queue": None
            }
            
            # Get task info from Celery
            if result.info:
                if isinstance(result.info, dict):
                    status_info.update(result.info)
                elif result.status == JobStatus.FAILURE:
                    status_info["error"] = str(result.info)
            
            # Get additional info from task metadata
            task_info = result._get_task_meta()
            if task_info:
                status_info.update({
                    "started_at": task_info.get("date_start"),
                    "completed_at": task_info.get("date_done"),
                    "retry_count": task_info.get("retries", 0),
                    "queue": task_info.get("queue")
                })
            
            # Calculate duration if available
            if status_info["started_at"] and status_info["completed_at"]:
                start_time = datetime.fromisoformat(status_info["started_at"])
                end_time = datetime.fromisoformat(status_info["completed_at"])
                status_info["duration_seconds"] = (end_time - start_time).total_seconds()
            
            # Get result data for successful jobs
            if result.status == JobStatus.SUCCESS and result.result:
                status_info["result"] = result.result
            
            logger.debug("Retrieved job status", task_id=task_id, status=result.status)
            return status_info
            
        except Exception as e:
            logger.error("Failed to get job status", task_id=task_id, error=str(e))
            return {
                "task_id": task_id,
                "status": "UNKNOWN",
                "error": f"Failed to retrieve status: {str(e)}"
            }
    
    async def get_active_jobs(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get list of currently active transparency calculation jobs.
        
        Args:
            limit: Maximum number of jobs to return
            
        Returns:
            List of active job information
        """
        try:
            # Get active tasks from Celery
            inspect = self.celery_app.control.inspect()
            
            active_jobs = []
            
            # Get active tasks from all workers
            active_tasks = inspect.active()
            if active_tasks:
                for worker, tasks in active_tasks.items():
                    for task in tasks:
                        if task["name"].startswith("app.services.transparency"):
                            job_info = {
                                "task_id": task["id"],
                                "task_name": task["name"],
                                "worker": worker,
                                "args": task.get("args", []),
                                "kwargs": task.get("kwargs", {}),
                                "started_at": task.get("time_start"),
                                "status": "RUNNING"
                            }
                            active_jobs.append(job_info)
            
            # Get scheduled tasks
            scheduled_tasks = inspect.scheduled()
            if scheduled_tasks:
                for worker, tasks in scheduled_tasks.items():
                    for task in tasks:
                        if task["request"]["name"].startswith("app.services.transparency"):
                            job_info = {
                                "task_id": task["request"]["id"],
                                "task_name": task["request"]["name"],
                                "worker": worker,
                                "args": task["request"].get("args", []),
                                "kwargs": task["request"].get("kwargs", {}),
                                "scheduled_at": task.get("eta"),
                                "status": "SCHEDULED"
                            }
                            active_jobs.append(job_info)
            
            # Sort by start time and limit results
            active_jobs.sort(key=lambda x: x.get("started_at", x.get("scheduled_at", "")), reverse=True)
            return active_jobs[:limit]
            
        except Exception as e:
            logger.error("Failed to get active jobs", error=str(e))
            return []
    
    async def get_failed_jobs(self, hours: int = 24, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get list of failed transparency calculation jobs.
        
        Args:
            hours: Number of hours to look back
            limit: Maximum number of jobs to return
            
        Returns:
            List of failed job information
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        try:
            # Query audit events for failed jobs
            failed_events = self.db.query(AuditEvent).filter(
                AuditEvent.event_type == "transparency_calculation_failed",
                AuditEvent.created_at >= cutoff_time
            ).order_by(AuditEvent.created_at.desc()).limit(limit).all()
            
            failed_jobs = []
            for event in failed_events:
                job_info = {
                    "task_id": event.details.get("task_id"),
                    "po_id": str(event.entity_id),
                    "failed_at": event.created_at.isoformat(),
                    "error": event.details.get("error"),
                    "retry_count": event.details.get("retry_count", 0),
                    "max_retries": event.details.get("max_retries", 0)
                }
                failed_jobs.append(job_info)
            
            return failed_jobs
            
        except Exception as e:
            logger.error("Failed to get failed jobs", error=str(e))
            return []
    
    async def retry_failed_job(self, task_id: str, force: bool = False) -> Dict[str, Any]:
        """
        Retry a failed transparency calculation job.
        
        Args:
            task_id: Celery task ID to retry
            force: Force retry even if max retries exceeded
            
        Returns:
            Dictionary containing retry result
        """
        try:
            result = AsyncResult(task_id, app=self.celery_app)
            
            if result.status != JobStatus.FAILURE and not force:
                return {
                    "success": False,
                    "error": f"Job is not in failed state: {result.status}"
                }
            
            # Get original task arguments
            task_info = result._get_task_meta()
            if not task_info:
                return {
                    "success": False,
                    "error": "Could not retrieve original task information"
                }
            
            # Extract original arguments
            original_args = task_info.get("args", [])
            original_kwargs = task_info.get("kwargs", {})
            task_name = task_info.get("name", "")
            
            # Schedule new task with same arguments
            from app.services.transparency_jobs import calculate_transparency_async
            
            if "calculate_transparency_async" in task_name:
                new_task = calculate_transparency_async.delay(*original_args, **original_kwargs)
                
                logger.info(
                    "Retried failed transparency calculation",
                    original_task_id=task_id,
                    new_task_id=new_task.id
                )
                
                return {
                    "success": True,
                    "original_task_id": task_id,
                    "new_task_id": new_task.id
                }
            else:
                return {
                    "success": False,
                    "error": f"Unsupported task type: {task_name}"
                }
                
        except Exception as e:
            logger.error("Failed to retry job", task_id=task_id, error=str(e))
            return {
                "success": False,
                "error": str(e)
            }
    
    async def cancel_job(self, task_id: str, terminate: bool = False) -> Dict[str, Any]:
        """
        Cancel a running or scheduled transparency calculation job.
        
        Args:
            task_id: Celery task ID to cancel
            terminate: Whether to terminate forcefully
            
        Returns:
            Dictionary containing cancellation result
        """
        try:
            # Revoke the task
            self.celery_app.control.revoke(task_id, terminate=terminate)
            
            logger.info(
                "Cancelled transparency calculation job",
                task_id=task_id,
                terminate=terminate
            )
            
            return {
                "success": True,
                "task_id": task_id,
                "terminated": terminate
            }
            
        except Exception as e:
            logger.error("Failed to cancel job", task_id=task_id, error=str(e))
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_queue_stats(self) -> Dict[str, Any]:
        """
        Get transparency job queue statistics.
        
        Returns:
            Dictionary containing queue statistics
        """
        try:
            inspect = self.celery_app.control.inspect()
            
            stats = {
                "transparency_queue": {
                    "active": 0,
                    "scheduled": 0,
                    "reserved": 0
                },
                "workers": [],
                "total_active": 0,
                "total_scheduled": 0
            }
            
            # Get active tasks
            active_tasks = inspect.active()
            if active_tasks:
                for worker, tasks in active_tasks.items():
                    transparency_tasks = [t for t in tasks if t["name"].startswith("app.services.transparency")]
                    stats["transparency_queue"]["active"] += len(transparency_tasks)
                    stats["total_active"] += len(transparency_tasks)
            
            # Get scheduled tasks
            scheduled_tasks = inspect.scheduled()
            if scheduled_tasks:
                for worker, tasks in scheduled_tasks.items():
                    transparency_tasks = [t for t in tasks if t["request"]["name"].startswith("app.services.transparency")]
                    stats["transparency_queue"]["scheduled"] += len(transparency_tasks)
                    stats["total_scheduled"] += len(transparency_tasks)
            
            # Get reserved tasks
            reserved_tasks = inspect.reserved()
            if reserved_tasks:
                for worker, tasks in reserved_tasks.items():
                    transparency_tasks = [t for t in tasks if t["name"].startswith("app.services.transparency")]
                    stats["transparency_queue"]["reserved"] += len(transparency_tasks)
            
            # Get worker stats
            worker_stats = inspect.stats()
            if worker_stats:
                for worker, worker_info in worker_stats.items():
                    stats["workers"].append({
                        "name": worker,
                        "status": "online",
                        "total_tasks": worker_info.get("total", {}),
                        "pool": worker_info.get("pool", {})
                    })
            
            return stats
            
        except Exception as e:
            logger.error("Failed to get queue stats", error=str(e))
            return {
                "error": str(e),
                "transparency_queue": {"active": 0, "scheduled": 0, "reserved": 0},
                "workers": [],
                "total_active": 0,
                "total_scheduled": 0
            }
    
    async def get_performance_metrics(self, hours: int = 24) -> Dict[str, Any]:
        """
        Get transparency job performance metrics.
        
        Args:
            hours: Number of hours to analyze
            
        Returns:
            Dictionary containing performance metrics
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        try:
            # Query audit events for completed and failed jobs
            completed_events = self.db.query(AuditEvent).filter(
                AuditEvent.event_type == "transparency_calculation_completed",
                AuditEvent.created_at >= cutoff_time
            ).all()
            
            failed_events = self.db.query(AuditEvent).filter(
                AuditEvent.event_type == "transparency_calculation_failed",
                AuditEvent.created_at >= cutoff_time
            ).all()
            
            # Calculate metrics
            total_jobs = len(completed_events) + len(failed_events)
            success_rate = len(completed_events) / total_jobs if total_jobs > 0 else 0
            
            # Calculate average duration for completed jobs
            durations = [
                event.details.get("calculation_duration_ms", 0)
                for event in completed_events
                if event.details.get("calculation_duration_ms")
            ]
            
            avg_duration_ms = sum(durations) / len(durations) if durations else 0
            
            metrics = {
                "period_hours": hours,
                "total_jobs": total_jobs,
                "completed_jobs": len(completed_events),
                "failed_jobs": len(failed_events),
                "success_rate": round(success_rate, 4),
                "average_duration_ms": round(avg_duration_ms, 2),
                "min_duration_ms": min(durations) if durations else 0,
                "max_duration_ms": max(durations) if durations else 0,
                "jobs_per_hour": round(total_jobs / hours, 2) if hours > 0 else 0
            }
            
            return metrics
            
        except Exception as e:
            logger.error("Failed to get performance metrics", error=str(e))
            return {
                "error": str(e),
                "period_hours": hours,
                "total_jobs": 0,
                "completed_jobs": 0,
                "failed_jobs": 0,
                "success_rate": 0,
                "average_duration_ms": 0
            }
    
    async def cleanup_old_jobs(self, days: int = 7) -> Dict[str, Any]:
        """
        Clean up old job records and audit events.
        
        Args:
            days: Number of days to keep records
            
        Returns:
            Dictionary containing cleanup results
        """
        cutoff_time = datetime.utcnow() - timedelta(days=days)
        
        try:
            # Clean up old audit events
            deleted_events = self.db.query(AuditEvent).filter(
                AuditEvent.event_type.in_([
                    "transparency_calculation_scheduled",
                    "transparency_calculation_completed",
                    "transparency_calculation_failed"
                ]),
                AuditEvent.created_at < cutoff_time
            ).delete()
            
            self.db.commit()
            
            logger.info(
                "Cleaned up old transparency job records",
                deleted_events=deleted_events,
                cutoff_days=days
            )
            
            return {
                "success": True,
                "deleted_events": deleted_events,
                "cutoff_days": days
            }
            
        except Exception as e:
            logger.error("Failed to cleanup old jobs", error=str(e))
            self.db.rollback()
            return {
                "success": False,
                "error": str(e)
            }
