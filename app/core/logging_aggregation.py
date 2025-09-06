"""
Comprehensive logging aggregation and error tracking system.
"""
import json
import traceback
import sys
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import asyncio
from contextlib import asynccontextmanager

import structlog
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.core.config import settings
from app.core.database import get_db
from app.core.redis import get_redis
from app.core.logging import get_logger

logger = get_logger(__name__)


class LogLevel(str, Enum):
    """Log level enumeration."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ErrorSeverity(str, Enum):
    """Error severity enumeration."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class LogEntry:
    """Structured log entry."""
    timestamp: datetime
    level: LogLevel
    message: str
    logger_name: str
    module: str
    function: str
    line_number: int
    request_id: Optional[str] = None
    user_id: Optional[str] = None
    company_id: Optional[str] = None
    session_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    extra_data: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.extra_data is None:
            self.extra_data = {}


@dataclass
class ErrorEvent:
    """Error event for tracking and alerting."""
    error_id: str
    timestamp: datetime
    severity: ErrorSeverity
    error_type: str
    error_message: str
    stack_trace: str
    module: str
    function: str
    line_number: int
    request_id: Optional[str] = None
    user_id: Optional[str] = None
    company_id: Optional[str] = None
    context: Dict[str, Any] = None
    fingerprint: Optional[str] = None
    count: int = 1
    first_seen: Optional[datetime] = None
    last_seen: Optional[datetime] = None
    
    def __post_init__(self):
        if self.context is None:
            self.context = {}
        if self.first_seen is None:
            self.first_seen = self.timestamp
        if self.last_seen is None:
            self.last_seen = self.timestamp


class LogAggregator:
    """
    Centralized log aggregation system.
    
    Features:
    - Structured logging
    - Log level filtering
    - Context enrichment
    - Performance metrics
    - Error tracking
    - Log rotation
    - Search and filtering
    """
    
    def __init__(self):
        self.buffer: List[LogEntry] = []
        self.buffer_size = 1000
        self.flush_interval = 60  # seconds
        self.error_cache = {}
        self.metrics = {
            "logs_processed": 0,
            "errors_tracked": 0,
            "warnings_count": 0,
            "last_flush": datetime.utcnow()
        }
    
    async def log(self, entry: LogEntry):
        """Add log entry to aggregation buffer."""
        self.buffer.append(entry)
        self.metrics["logs_processed"] += 1
        
        # Track errors and warnings
        if entry.level == LogLevel.ERROR:
            await self._track_error(entry)
        elif entry.level == LogLevel.WARNING:
            self.metrics["warnings_count"] += 1
        
        # Flush buffer if full
        if len(self.buffer) >= self.buffer_size:
            await self.flush_logs()
    
    async def _track_error(self, entry: LogEntry):
        """Track error for monitoring and alerting."""
        try:
            # Create error fingerprint
            fingerprint = self._create_error_fingerprint(entry)
            
            # Check if this error has been seen before
            if fingerprint in self.error_cache:
                self.error_cache[fingerprint]["count"] += 1
                self.error_cache[fingerprint]["last_seen"] = entry.timestamp
            else:
                # New error
                error_event = ErrorEvent(
                    error_id=f"err_{int(entry.timestamp.timestamp())}",
                    timestamp=entry.timestamp,
                    severity=self._determine_error_severity(entry),
                    error_type=entry.extra_data.get("error_type", "UnknownError"),
                    error_message=entry.message,
                    stack_trace=entry.extra_data.get("stack_trace", ""),
                    module=entry.module,
                    function=entry.function,
                    line_number=entry.line_number,
                    request_id=entry.request_id,
                    user_id=entry.user_id,
                    company_id=entry.company_id,
                    context=entry.extra_data,
                    fingerprint=fingerprint
                )
                
                self.error_cache[fingerprint] = asdict(error_event)
                self.metrics["errors_tracked"] += 1
                
                # Send alert for critical errors
                if error_event.severity == ErrorSeverity.CRITICAL:
                    await self._send_error_alert(error_event)
        
        except Exception as e:
            logger.error("Failed to track error", error=str(e))
    
    def _create_error_fingerprint(self, entry: LogEntry) -> str:
        """Create unique fingerprint for error grouping."""
        import hashlib
        
        # Use module, function, and error type for fingerprinting
        fingerprint_data = f"{entry.module}:{entry.function}:{entry.extra_data.get('error_type', 'Unknown')}"
        return hashlib.md5(fingerprint_data.encode()).hexdigest()[:16]
    
    def _determine_error_severity(self, entry: LogEntry) -> ErrorSeverity:
        """Determine error severity based on context."""
        error_type = entry.extra_data.get("error_type", "")
        
        # Critical errors
        if any(keyword in error_type.lower() for keyword in ["database", "redis", "security", "auth"]):
            return ErrorSeverity.CRITICAL
        
        # High severity errors
        if any(keyword in error_type.lower() for keyword in ["validation", "permission", "business"]):
            return ErrorSeverity.HIGH
        
        # Medium severity errors
        if any(keyword in error_type.lower() for keyword in ["http", "api", "request"]):
            return ErrorSeverity.MEDIUM
        
        return ErrorSeverity.LOW
    
    async def _send_error_alert(self, error_event: ErrorEvent):
        """Send alert for critical errors."""
        try:
            # This would integrate with alerting systems like PagerDuty, Slack, etc.
            alert_data = {
                "error_id": error_event.error_id,
                "severity": error_event.severity.value,
                "message": error_event.error_message,
                "module": error_event.module,
                "timestamp": error_event.timestamp.isoformat(),
                "context": error_event.context
            }
            
            # Store alert in Redis for immediate processing
            redis_client = await get_redis()
            await redis_client.lpush("error_alerts", json.dumps(alert_data))
            
            logger.warning("Critical error alert sent", error_id=error_event.error_id)
            
        except Exception as e:
            logger.error("Failed to send error alert", error=str(e))
    
    async def flush_logs(self):
        """Flush log buffer to persistent storage."""
        if not self.buffer:
            return
        
        try:
            # Store logs in database
            await self._store_logs_in_database()
            
            # Store logs in Redis for real-time access
            await self._store_logs_in_redis()
            
            # Clear buffer
            self.buffer.clear()
            self.metrics["last_flush"] = datetime.utcnow()
            
            logger.debug(f"Flushed {len(self.buffer)} log entries")
            
        except Exception as e:
            logger.error("Failed to flush logs", error=str(e))
    
    async def _store_logs_in_database(self):
        """Store logs in database for long-term storage."""
        if not self.buffer:
            return
        
        try:
            db = next(get_db())
            
            # Prepare batch insert
            log_records = []
            for entry in self.buffer:
                log_records.append({
                    "timestamp": entry.timestamp,
                    "level": entry.level.value,
                    "message": entry.message,
                    "logger_name": entry.logger_name,
                    "module": entry.module,
                    "function": entry.function,
                    "line_number": entry.line_number,
                    "request_id": entry.request_id,
                    "user_id": entry.user_id,
                    "company_id": entry.company_id,
                    "session_id": entry.session_id,
                    "ip_address": str(entry.ip_address) if entry.ip_address else None,
                    "user_agent": entry.user_agent,
                    "extra_data": json.dumps(entry.extra_data)
                })
            
            # Batch insert logs
            if log_records:
                db.execute(text("""
                    INSERT INTO application_logs 
                    (timestamp, level, message, logger_name, module, function, line_number,
                     request_id, user_id, company_id, session_id, ip_address, user_agent, extra_data)
                    VALUES 
                    (:timestamp, :level, :message, :logger_name, :module, :function, :line_number,
                     :request_id, :user_id, :company_id, :session_id, :ip_address, :user_agent, :extra_data)
                """), log_records)
                
                db.commit()
        
        except Exception as e:
            logger.error("Failed to store logs in database", error=str(e))
    
    async def _store_logs_in_redis(self):
        """Store recent logs in Redis for real-time access."""
        try:
            redis_client = await get_redis()
            
            # Store recent logs (last 1000 entries)
            for entry in self.buffer[-1000:]:
                log_data = {
                    "timestamp": entry.timestamp.isoformat(),
                    "level": entry.level.value,
                    "message": entry.message,
                    "module": entry.module,
                    "request_id": entry.request_id,
                    "user_id": entry.user_id,
                    "company_id": entry.company_id
                }
                
                await redis_client.lpush("recent_logs", json.dumps(log_data))
            
            # Keep only recent logs (last 1000)
            await redis_client.ltrim("recent_logs", 0, 999)
            
        except Exception as e:
            logger.error("Failed to store logs in Redis", error=str(e))
    
    async def search_logs(self, 
                         level: Optional[LogLevel] = None,
                         module: Optional[str] = None,
                         user_id: Optional[str] = None,
                         company_id: Optional[str] = None,
                         start_time: Optional[datetime] = None,
                         end_time: Optional[datetime] = None,
                         limit: int = 100) -> List[Dict[str, Any]]:
        """Search logs with filtering."""
        try:
            db = next(get_db())
            
            # Build query
            conditions = []
            params = {}
            
            if level:
                conditions.append("level = :level")
                params["level"] = level.value
            
            if module:
                conditions.append("module = :module")
                params["module"] = module
            
            if user_id:
                conditions.append("user_id = :user_id")
                params["user_id"] = user_id
            
            if company_id:
                conditions.append("company_id = :company_id")
                params["company_id"] = company_id
            
            if start_time:
                conditions.append("timestamp >= :start_time")
                params["start_time"] = start_time
            
            if end_time:
                conditions.append("timestamp <= :end_time")
                params["end_time"] = end_time
            
            where_clause = " AND ".join(conditions) if conditions else "1=1"
            
            query = f"""
                SELECT timestamp, level, message, logger_name, module, function,
                       request_id, user_id, company_id, extra_data
                FROM application_logs
                WHERE {where_clause}
                ORDER BY timestamp DESC
                LIMIT :limit
            """
            
            params["limit"] = limit
            
            result = db.execute(text(query), params)
            
            logs = []
            for row in result:
                log_entry = {
                    "timestamp": row.timestamp.isoformat(),
                    "level": row.level,
                    "message": row.message,
                    "logger_name": row.logger_name,
                    "module": row.module,
                    "function": row.function,
                    "request_id": row.request_id,
                    "user_id": row.user_id,
                    "company_id": row.company_id,
                    "extra_data": json.loads(row.extra_data) if row.extra_data else {}
                }
                logs.append(log_entry)
            
            return logs
            
        except Exception as e:
            logger.error("Failed to search logs", error=str(e))
            return []
    
    async def get_error_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get error summary for the specified time period."""
        try:
            db = next(get_db())
            
            since = datetime.utcnow() - timedelta(hours=hours)
            
            # Get error counts by type
            result = db.execute(text("""
                SELECT 
                    module,
                    COUNT(*) as error_count,
                    COUNT(DISTINCT user_id) as affected_users,
                    COUNT(DISTINCT company_id) as affected_companies
                FROM application_logs
                WHERE level = 'error' AND timestamp >= :since
                GROUP BY module
                ORDER BY error_count DESC
            """), {"since": since})
            
            error_by_module = []
            for row in result:
                error_by_module.append({
                    "module": row.module,
                    "error_count": row.error_count,
                    "affected_users": row.affected_users,
                    "affected_companies": row.affected_companies
                })
            
            # Get total error count
            result = db.execute(text("""
                SELECT COUNT(*) as total_errors
                FROM application_logs
                WHERE level = 'error' AND timestamp >= :since
            """), {"since": since})
            
            total_errors = result.scalar() or 0
            
            return {
                "time_period_hours": hours,
                "total_errors": total_errors,
                "error_by_module": error_by_module,
                "cached_errors": len(self.error_cache),
                "metrics": self.metrics
            }
            
        except Exception as e:
            logger.error("Failed to get error summary", error=str(e))
            return {}
    
    async def cleanup_old_logs(self, days: int = 30):
        """Clean up old logs to manage storage."""
        try:
            db = next(get_db())
            
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            result = db.execute(text("""
                DELETE FROM application_logs
                WHERE timestamp < :cutoff_date
            """), {"cutoff_date": cutoff_date})
            
            deleted_count = result.rowcount
            db.commit()
            
            logger.info(f"Cleaned up {deleted_count} old log entries")
            
        except Exception as e:
            logger.error("Failed to cleanup old logs", error=str(e))


class StructuredLogger:
    """Enhanced structured logger with context management."""
    
    def __init__(self, name: str):
        self.name = name
        self.aggregator = LogAggregator()
        self.context = {}
    
    @asynccontextmanager
    async def context_manager(self, **context):
        """Context manager for adding context to logs."""
        old_context = self.context.copy()
        self.context.update(context)
        try:
            yield self
        finally:
            self.context = old_context
    
    async def _log(self, level: LogLevel, message: str, **kwargs):
        """Internal logging method."""
        import inspect
        
        # Get caller information
        frame = inspect.currentframe().f_back.f_back
        module = frame.f_globals.get("__name__", "unknown")
        function = frame.f_code.co_name
        line_number = frame.f_lineno
        
        # Merge context and kwargs
        extra_data = {**self.context, **kwargs}
        
        # Create log entry
        entry = LogEntry(
            timestamp=datetime.utcnow(),
            level=level,
            message=message,
            logger_name=self.name,
            module=module,
            function=function,
            line_number=line_number,
            extra_data=extra_data
        )
        
        # Add to aggregator
        await self.aggregator.log(entry)
    
    async def debug(self, message: str, **kwargs):
        """Log debug message."""
        await self._log(LogLevel.DEBUG, message, **kwargs)
    
    async def info(self, message: str, **kwargs):
        """Log info message."""
        await self._log(LogLevel.INFO, message, **kwargs)
    
    async def warning(self, message: str, **kwargs):
        """Log warning message."""
        await self._log(LogLevel.WARNING, message, **kwargs)
    
    async def error(self, message: str, **kwargs):
        """Log error message."""
        # Add exception info if available
        if sys.exc_info()[0] is not None:
            kwargs["error_type"] = sys.exc_info()[0].__name__
            kwargs["stack_trace"] = traceback.format_exc()
        
        await self._log(LogLevel.ERROR, message, **kwargs)
    
    async def critical(self, message: str, **kwargs):
        """Log critical message."""
        await self._log(LogLevel.CRITICAL, message, **kwargs)


# Global log aggregator instance
log_aggregator = LogAggregator()


def get_structured_logger(name: str) -> StructuredLogger:
    """Get structured logger instance."""
    return StructuredLogger(name)
