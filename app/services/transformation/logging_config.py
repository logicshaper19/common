"""
Comprehensive logging configuration for transformation services.

This module provides structured logging with proper context, correlation IDs,
and performance monitoring for all transformation operations.
"""
import logging
import json
import time
from typing import Dict, Any, Optional, List
from datetime import datetime
from uuid import UUID, uuid4
from contextvars import ContextVar
from functools import wraps

from app.core.logging import get_logger

# Context variables for request tracking
request_id_var: ContextVar[Optional[str]] = ContextVar('request_id', default=None)
user_id_var: ContextVar[Optional[str]] = ContextVar('user_id', default=None)
company_id_var: ContextVar[Optional[str]] = ContextVar('company_id', default=None)
operation_name_var: ContextVar[Optional[str]] = ContextVar('operation_name', default=None)

logger = get_logger(__name__)


class TransformationLogger:
    """
    Enhanced logger for transformation services with structured logging.
    
    This logger provides:
    - Structured JSON logging with context
    - Performance monitoring and timing
    - Request correlation and tracing
    - Error tracking and alerting
    - Business metrics and KPIs
    """
    
    def __init__(self, name: str):
        self.logger = get_logger(name)
        self._performance_metrics = {}
    
    def _get_context(self) -> Dict[str, Any]:
        """Get current logging context."""
        return {
            "request_id": request_id_var.get(),
            "user_id": user_id_var.get(),
            "company_id": company_id_var.get(),
            "operation_name": operation_name_var.get(),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def _log_with_context(
        self, 
        level: int, 
        message: str, 
        extra_data: Optional[Dict[str, Any]] = None,
        exc_info: bool = False
    ) -> None:
        """Log message with context and extra data."""
        context = self._get_context()
        if extra_data:
            context.update(extra_data)
        
        self.logger.log(level, message, extra=context, exc_info=exc_info)
    
    def info(self, message: str, **kwargs) -> None:
        """Log info message with context."""
        self._log_with_context(logging.INFO, message, kwargs)
    
    def warning(self, message: str, **kwargs) -> None:
        """Log warning message with context."""
        self._log_with_context(logging.WARNING, message, kwargs)
    
    def error(self, message: str, **kwargs) -> None:
        """Log error message with context."""
        self._log_with_context(logging.ERROR, message, kwargs, exc_info=True)
    
    def debug(self, message: str, **kwargs) -> None:
        """Log debug message with context."""
        self._log_with_context(logging.DEBUG, message, kwargs)
    
    def critical(self, message: str, **kwargs) -> None:
        """Log critical message with context."""
        self._log_with_context(logging.CRITICAL, message, kwargs, exc_info=True)
    
    def start_operation(self, operation_name: str, **kwargs) -> str:
        """Start timing an operation and return operation ID."""
        operation_id = str(uuid4())
        start_time = time.time()
        
        self._performance_metrics[operation_id] = {
            "operation_name": operation_name,
            "start_time": start_time,
            "extra_data": kwargs
        }
        
        self.info(
            f"Starting operation: {operation_name}",
            operation_id=operation_id,
            **kwargs
        )
        
        return operation_id
    
    def end_operation(self, operation_id: str, **kwargs) -> Dict[str, Any]:
        """End timing an operation and return performance metrics."""
        if operation_id not in self._performance_metrics:
            self.warning(f"Operation ID not found: {operation_id}")
            return {}
        
        operation_data = self._performance_metrics[operation_id]
        end_time = time.time()
        duration = end_time - operation_data["start_time"]
        
        performance_metrics = {
            "operation_id": operation_id,
            "operation_name": operation_data["operation_name"],
            "duration_seconds": duration,
            "start_time": operation_data["start_time"],
            "end_time": end_time,
            "extra_data": {**operation_data["extra_data"], **kwargs}
        }
        
        # Log performance metrics
        self.info(
            f"Completed operation: {operation_data['operation_name']}",
            **performance_metrics
        )
        
        # Clean up
        del self._performance_metrics[operation_id]
        
        return performance_metrics
    
    def log_business_metric(
        self, 
        metric_name: str, 
        value: float, 
        unit: str = "count",
        **kwargs
    ) -> None:
        """Log business metrics and KPIs."""
        self.info(
            f"Business metric: {metric_name}",
            metric_name=metric_name,
            metric_value=value,
            metric_unit=unit,
            metric_type="business",
            **kwargs
        )
    
    def log_performance_metric(
        self, 
        metric_name: str, 
        value: float, 
        unit: str = "seconds",
        **kwargs
    ) -> None:
        """Log performance metrics."""
        self.info(
            f"Performance metric: {metric_name}",
            metric_name=metric_name,
            metric_value=value,
            metric_unit=unit,
            metric_type="performance",
            **kwargs
        )
    
    def log_data_quality_metric(
        self, 
        metric_name: str, 
        value: float, 
        threshold: Optional[float] = None,
        **kwargs
    ) -> None:
        """Log data quality metrics."""
        extra_data = {
            "metric_name": metric_name,
            "metric_value": value,
            "metric_type": "data_quality",
            **kwargs
        }
        
        if threshold is not None:
            extra_data["threshold"] = threshold
            extra_data["status"] = "pass" if value >= threshold else "fail"
        
        self.info(f"Data quality metric: {metric_name}", **extra_data)
    
    def log_transformation_event(
        self, 
        event_type: str, 
        transformation_id: str,
        **kwargs
    ) -> None:
        """Log transformation-specific events."""
        self.info(
            f"Transformation event: {event_type}",
            event_type=event_type,
            transformation_id=transformation_id,
            event_category="transformation",
            **kwargs
        )
    
    def log_template_generation(
        self, 
        template_type: str, 
        company_type: str,
        **kwargs
    ) -> None:
        """Log template generation events."""
        self.info(
            f"Template generation: {template_type}",
            template_type=template_type,
            company_type=company_type,
            event_category="template",
            **kwargs
        )
    
    def log_validation_event(
        self, 
        validation_type: str, 
        is_valid: bool,
        error_count: int = 0,
        **kwargs
    ) -> None:
        """Log validation events."""
        self.info(
            f"Validation event: {validation_type}",
            validation_type=validation_type,
            is_valid=is_valid,
            error_count=error_count,
            event_category="validation",
            **kwargs
        )
    
    def log_database_operation(
        self, 
        operation_type: str, 
        table_name: str,
        record_count: int = 1,
        **kwargs
    ) -> None:
        """Log database operations."""
        self.info(
            f"Database operation: {operation_type}",
            operation_type=operation_type,
            table_name=table_name,
            record_count=record_count,
            event_category="database",
            **kwargs
        )
    
    def log_error_with_context(
        self, 
        error: Exception, 
        operation: str,
        **kwargs
    ) -> None:
        """Log error with full context and stack trace."""
        self.error(
            f"Error in {operation}: {str(error)}",
            error_type=type(error).__name__,
            error_message=str(error),
            operation=operation,
            event_category="error",
            **kwargs
        )


def get_transformation_logger(name: str) -> TransformationLogger:
    """Get a transformation logger instance."""
    return TransformationLogger(name)


def set_logging_context(
    request_id: Optional[str] = None,
    user_id: Optional[str] = None,
    company_id: Optional[str] = None,
    operation_name: Optional[str] = None
) -> None:
    """Set logging context for the current request."""
    if request_id:
        request_id_var.set(request_id)
    if user_id:
        user_id_var.set(user_id)
    if company_id:
        company_id_var.set(company_id)
    if operation_name:
        operation_name_var.set(operation_name)


def clear_logging_context() -> None:
    """Clear logging context."""
    request_id_var.set(None)
    user_id_var.set(None)
    company_id_var.set(None)
    operation_name_var.set(None)


def log_operation(operation_name: str):
    """Decorator to log operation start/end with performance metrics."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Get logger from the instance if available
            logger_instance = None
            if hasattr(args[0], 'logger'):
                logger_instance = args[0].logger
            else:
                logger_instance = get_transformation_logger(func.__module__)
            
            # Start operation timing
            operation_id = logger_instance.start_operation(operation_name)
            
            try:
                # Execute function
                result = func(*args, **kwargs)
                
                # End operation timing
                logger_instance.end_operation(operation_id, success=True)
                
                return result
                
            except Exception as e:
                # Log error and end operation
                logger_instance.log_error_with_context(e, operation_name)
                logger_instance.end_operation(operation_id, success=False, error=str(e))
                raise
        
        return wrapper
    return decorator


def log_performance(metric_name: str, unit: str = "seconds"):
    """Decorator to log performance metrics."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Get logger from the instance if available
            logger_instance = None
            if hasattr(args[0], 'logger'):
                logger_instance = args[0].logger
            else:
                logger_instance = get_transformation_logger(func.__module__)
            
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                
                duration = time.time() - start_time
                logger_instance.log_performance_metric(metric_name, duration, unit)
                
                return result
                
            except Exception as e:
                duration = time.time() - start_time
                logger_instance.log_performance_metric(f"{metric_name}_error", duration, unit)
                raise
        
        return wrapper
    return decorator


def log_business_metrics(metric_name: str, value_func: callable):
    """Decorator to log business metrics."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Get logger from the instance if available
            logger_instance = None
            if hasattr(args[0], 'logger'):
                logger_instance = args[0].logger
            else:
                logger_instance = get_transformation_logger(func.__module__)
            
            try:
                result = func(*args, **kwargs)
                
                # Calculate and log business metric
                value = value_func(result)
                logger_instance.log_business_metric(metric_name, value)
                
                return result
                
            except Exception as e:
                logger_instance.log_error_with_context(e, f"business_metric_{metric_name}")
                raise
        
        return wrapper
    return decorator


# Global logger instances for different components
template_logger = get_transformation_logger("transformation.templates")
creation_logger = get_transformation_logger("transformation.creation")
validation_logger = get_transformation_logger("transformation.validation")
transaction_logger = get_transformation_logger("transformation.transaction")
api_logger = get_transformation_logger("transformation.api")
