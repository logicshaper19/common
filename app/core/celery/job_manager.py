"""
Enhanced Celery Job Management System

This module provides comprehensive background job processing with:
- Job prioritization and queuing
- Retry strategies and error handling
- Job monitoring and status tracking
- Performance metrics and analytics
- Dead letter queue management
"""

import asyncio
from typing import Any, Dict, List, Optional, Callable, Union
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field
import json
import uuid

from celery import Celery, Task, current_task
from celery.exceptions import Retry, MaxRetriesExceededError
from celery.result import AsyncResult
from celery.signals import task_prerun, task_postrun, task_failure, task_success
from kombu import Queue, Exchange

from app.core.logging import get_logger
from app.core.config import settings
from app.core.caching import get_cache_manager, CacheKey

logger = get_logger(__name__)


class JobPriority(Enum):
    """Job priority levels."""
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3


class JobStatus(Enum):
    """Job status enumeration."""
    PENDING = "PENDING"
    STARTED = "STARTED"
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    RETRY = "RETRY"
    REVOKED = "REVOKED"


@dataclass
class JobMetadata:
    """Job metadata for tracking and monitoring."""
    job_id: str
    task_name: str
    priority: JobPriority
    status: JobStatus
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    retry_count: int = 0
    max_retries: int = 3
    error_message: Optional[str] = None
    result_data: Optional[Dict[str, Any]] = None
    execution_time: Optional[float] = None
    queue_name: Optional[str] = None
    user_id: Optional[str] = None
    company_id: Optional[str] = None
    tags: List[str] = field(default_factory=list)


class EnhancedCeleryTask(Task):
    """Enhanced Celery task with comprehensive monitoring."""
    
    def __init__(self):
        self.cache_manager = get_cache_manager()
        self.job_metadata: Optional[JobMetadata] = None
    
    def on_success(self, retval, task_id, args, kwargs):
        """Handle successful task completion."""
        if self.job_metadata:
            self.job_metadata.status = JobStatus.SUCCESS
            self.job_metadata.completed_at = datetime.utcnow()
            self.job_metadata.result_data = retval
            self._update_job_metadata()
        
        logger.info(f"Task {task_id} completed successfully")
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Handle task failure."""
        if self.job_metadata:
            self.job_metadata.status = JobStatus.FAILURE
            self.job_metadata.completed_at = datetime.utcnow()
            self.job_metadata.error_message = str(exc)
            self._update_job_metadata()
        
        logger.error(f"Task {task_id} failed: {exc}")
    
    def on_retry(self, exc, task_id, args, kwargs, einfo):
        """Handle task retry."""
        if self.job_metadata:
            self.job_metadata.status = JobStatus.RETRY
            self.job_metadata.retry_count += 1
            self.job_metadata.error_message = str(exc)
            self._update_job_metadata()
        
        logger.warning(f"Task {task_id} retrying (attempt {self.job_metadata.retry_count if self.job_metadata else 'unknown'})")
    
    def _update_job_metadata(self):
        """Update job metadata in cache."""
        if self.job_metadata:
            cache_key = f"job:metadata:{self.job_metadata.job_id}"
            self.cache_manager.set(cache_key, self.job_metadata.__dict__, ttl=86400)  # 24 hours


class JobManager:
    """Comprehensive job management system."""
    
    def __init__(self, celery_app: Celery):
        self.celery_app = celery_app
        self.cache_manager = get_cache_manager()
        self._setup_queues()
        self._setup_signals()
    
    def _setup_queues(self):
        """Setup priority-based queues."""
        # Define exchanges
        default_exchange = Exchange('default', type='direct')
        priority_exchange = Exchange('priority', type='direct')
        
        # Define queues with different priorities
        self.celery_app.conf.task_routes = {
            'app.core.celery.jobs.critical.*': {'queue': 'critical'},
            'app.core.celery.jobs.high.*': {'queue': 'high'},
            'app.core.celery.jobs.normal.*': {'queue': 'normal'},
            'app.core.celery.jobs.low.*': {'queue': 'low'},
        }
        
        self.celery_app.conf.task_default_queue = 'normal'
        self.celery_app.conf.task_queues = (
            Queue('critical', priority_exchange, routing_key='critical', queue_arguments={'x-max-priority': 10}),
            Queue('high', priority_exchange, routing_key='high', queue_arguments={'x-max-priority': 7}),
            Queue('normal', default_exchange, routing_key='normal', queue_arguments={'x-max-priority': 5}),
            Queue('low', default_exchange, routing_key='low', queue_arguments={'x-max-priority': 3}),
        )
    
    def _setup_signals(self):
        """Setup Celery signals for monitoring."""
        
        @task_prerun.connect
        def task_prerun_handler(sender=None, task_id=None, task=None, args=None, kwargs=None, **kwds):
            """Handle task pre-run."""
            job_metadata = JobMetadata(
                job_id=task_id,
                task_name=task.name,
                priority=JobPriority.NORMAL,
                status=JobStatus.STARTED,
                created_at=datetime.utcnow(),
                started_at=datetime.utcnow()
            )
            
            # Store metadata
            cache_key = f"job:metadata:{task_id}"
            self.cache_manager.set(cache_key, job_metadata.__dict__, ttl=86400)
            
            logger.info(f"Task {task_id} started: {task.name}")
        
        @task_postrun.connect
        def task_postrun_handler(sender=None, task_id=None, task=None, args=None, kwargs=None, retval=None, state=None, **kwds):
            """Handle task post-run."""
            cache_key = f"job:metadata:{task_id}"
            metadata_dict = self.cache_manager.get(cache_key)
            
            if metadata_dict:
                metadata = JobMetadata(**metadata_dict)
                metadata.completed_at = datetime.utcnow()
                metadata.status = JobStatus.SUCCESS if state == 'SUCCESS' else JobStatus.FAILURE
                
                if metadata.started_at:
                    metadata.execution_time = (metadata.completed_at - metadata.started_at).total_seconds()
                
                self.cache_manager.set(cache_key, metadata.__dict__, ttl=86400)
                
                logger.info(f"Task {task_id} completed: {task.name} in {metadata.execution_time:.2f}s")
    
    def submit_job(
        self,
        task_name: str,
        args: tuple = (),
        kwargs: dict = None,
        priority: JobPriority = JobPriority.NORMAL,
        queue: str = None,
        eta: datetime = None,
        countdown: int = None,
        max_retries: int = 3,
        retry_delay: int = 60,
        user_id: str = None,
        company_id: str = None,
        tags: List[str] = None
    ) -> str:
        """
        Submit a job to the queue with comprehensive metadata.
        
        Args:
            task_name: Name of the Celery task
            args: Task arguments
            kwargs: Task keyword arguments
            priority: Job priority level
            queue: Specific queue name (overrides priority-based routing)
            eta: Estimated time of arrival
            countdown: Delay in seconds before execution
            max_retries: Maximum number of retries
            retry_delay: Delay between retries in seconds
            user_id: User ID for tracking
            company_id: Company ID for tracking
            tags: List of tags for categorization
            
        Returns:
            Job ID
        """
        kwargs = kwargs or {}
        tags = tags or []
        
        # Determine queue based on priority if not specified
        if not queue:
            queue_map = {
                JobPriority.CRITICAL: 'critical',
                JobPriority.HIGH: 'high',
                JobPriority.NORMAL: 'normal',
                JobPriority.LOW: 'low'
            }
            queue = queue_map.get(priority, 'normal')
        
        # Submit task
        result = self.celery_app.send_task(
            task_name,
            args=args,
            kwargs=kwargs,
            queue=queue,
            eta=eta,
            countdown=countdown,
            retry=True,
            retry_policy={
                'max_retries': max_retries,
                'interval_start': retry_delay,
                'interval_step': retry_delay,
                'interval_max': retry_delay * 2
            }
        )
        
        # Create job metadata
        job_metadata = JobMetadata(
            job_id=result.id,
            task_name=task_name,
            priority=priority,
            status=JobStatus.PENDING,
            created_at=datetime.utcnow(),
            max_retries=max_retries,
            queue_name=queue,
            user_id=user_id,
            company_id=company_id,
            tags=tags
        )
        
        # Store metadata
        cache_key = f"job:metadata:{result.id}"
        self.cache_manager.set(cache_key, job_metadata.__dict__, ttl=86400)
        
        logger.info(f"Job submitted: {result.id} ({task_name}) with priority {priority.name}")
        
        return result.id
    
    def get_job_status(self, job_id: str) -> Optional[JobMetadata]:
        """Get job status and metadata."""
        cache_key = f"job:metadata:{job_id}"
        metadata_dict = self.cache_manager.get(cache_key)
        
        if metadata_dict:
            return JobMetadata(**metadata_dict)
        
        # Fallback to Celery result
        try:
            result = AsyncResult(job_id, app=self.celery_app)
            if result.state:
                return JobMetadata(
                    job_id=job_id,
                    task_name=result.name or "unknown",
                    priority=JobPriority.NORMAL,
                    status=JobStatus(result.state),
                    created_at=datetime.utcnow()
                )
        except Exception as e:
            logger.warning(f"Failed to get job status for {job_id}: {e}")
        
        return None
    
    def get_job_result(self, job_id: str) -> Any:
        """Get job result."""
        try:
            result = AsyncResult(job_id, app=self.celery_app)
            return result.get(timeout=1)
        except Exception as e:
            logger.warning(f"Failed to get job result for {job_id}: {e}")
            return None
    
    def cancel_job(self, job_id: str) -> bool:
        """Cancel a pending job."""
        try:
            self.celery_app.control.revoke(job_id, terminate=True)
            
            # Update metadata
            cache_key = f"job:metadata:{job_id}"
            metadata_dict = self.cache_manager.get(cache_key)
            if metadata_dict:
                metadata = JobMetadata(**metadata_dict)
                metadata.status = JobStatus.REVOKED
                metadata.completed_at = datetime.utcnow()
                self.cache_manager.set(cache_key, metadata.__dict__, ttl=86400)
            
            logger.info(f"Job cancelled: {job_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to cancel job {job_id}: {e}")
            return False
    
    def get_queue_stats(self) -> Dict[str, Any]:
        """Get queue statistics."""
        try:
            inspect = self.celery_app.control.inspect()
            
            stats = {
                "active": inspect.active(),
                "scheduled": inspect.scheduled(),
                "reserved": inspect.reserved(),
                "stats": inspect.stats()
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get queue stats: {e}")
            return {}
    
    def get_job_metrics(self, hours: int = 24) -> Dict[str, Any]:
        """Get job performance metrics."""
        # This would typically query a metrics database
        # For now, we'll return basic stats from cache
        
        metrics = {
            "total_jobs": 0,
            "successful_jobs": 0,
            "failed_jobs": 0,
            "average_execution_time": 0.0,
            "queue_distribution": {},
            "error_rate": 0.0
        }
        
        # In a real implementation, this would query job history
        # For now, return placeholder data
        return metrics


# Create Celery app with enhanced configuration
celery_app = Celery(
    'common',
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        'app.core.celery.jobs.critical',
        'app.core.celery.jobs.high',
        'app.core.celery.jobs.normal',
        'app.core.celery.jobs.low'
    ]
)

# Configure Celery
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    worker_disable_rate_limits=False,
    task_compression='gzip',
    result_compression='gzip',
    result_expires=3600,  # 1 hour
    task_ignore_result=False,
    task_store_eager_result=True,
    task_always_eager=False,  # Set to True for testing
    task_eager_propagates=True,
    worker_send_task_events=True,
    task_send_sent_event=True,
    result_backend_transport_options={
        'master_name': 'mymaster',
        'visibility_timeout': 3600,
    }
)

# Initialize job manager
job_manager = JobManager(celery_app)


# Utility functions
def submit_background_job(
    task_name: str,
    args: tuple = (),
    kwargs: dict = None,
    priority: JobPriority = JobPriority.NORMAL,
    **options
) -> str:
    """Submit a background job."""
    return job_manager.submit_job(
        task_name=task_name,
        args=args,
        kwargs=kwargs,
        priority=priority,
        **options
    )


def get_job_status(job_id: str) -> Optional[JobMetadata]:
    """Get job status."""
    return job_manager.get_job_status(job_id)


def cancel_job(job_id: str) -> bool:
    """Cancel a job."""
    return job_manager.cancel_job(job_id)


def get_queue_stats() -> Dict[str, Any]:
    """Get queue statistics."""
    return job_manager.get_queue_stats()
