"""
Correlation ID middleware for request tracing.

This module provides:
1. Automatic correlation ID generation and propagation
2. Request/response logging with correlation IDs
3. Performance monitoring with request tracking
4. Error correlation and debugging support
"""

import time
import uuid
from typing import Callable, Optional
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from contextlib import contextmanager
from contextvars import ContextVar

import structlog

logger = structlog.get_logger(__name__)

# Context variable for correlation ID
correlation_id_context: ContextVar[Optional[str]] = ContextVar('correlation_id', default=None)


class CorrelationIDMiddleware(BaseHTTPMiddleware):
    """Middleware to handle correlation IDs for request tracing."""
    
    def __init__(self, app, header_name: str = "X-Correlation-ID"):
        super().__init__(app)
        self.header_name = header_name
        
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with correlation ID."""
        # Get or generate correlation ID
        correlation_id = (
            request.headers.get(self.header_name) or
            request.headers.get("X-Request-ID") or
            f"req_{uuid.uuid4().hex[:12]}"
        )
        
        # Set correlation ID in context
        correlation_id_context.set(correlation_id)
        request.state.correlation_id = correlation_id
        
        # Start timing
        start_time = time.time()
        
        # Log request start
        await self._log_request_start(request, correlation_id)
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000
            
            # Add correlation ID to response headers
            response.headers[self.header_name] = correlation_id
            response.headers["X-Request-ID"] = correlation_id
            
            # Log successful response
            await self._log_request_success(request, response, correlation_id, duration_ms)
            
            return response
            
        except Exception as e:
            # Calculate duration for failed request
            duration_ms = (time.time() - start_time) * 1000
            
            # Log request failure
            await self._log_request_failure(request, correlation_id, duration_ms, str(e))
            
            # Re-raise the exception
            raise
    
    async def _log_request_start(self, request: Request, correlation_id: str):
        """Log request start with correlation ID."""
        logger.info(
            "Request started",
            correlation_id=correlation_id,
            method=request.method,
            path=request.url.path,
            query_params=str(request.query_params) if request.query_params else None,
            client_ip=self._get_client_ip(request),
            user_agent=request.headers.get("User-Agent"),
            content_length=request.headers.get("Content-Length"),
            content_type=request.headers.get("Content-Type")
        )
    
    async def _log_request_success(self, 
                                 request: Request, 
                                 response: Response, 
                                 correlation_id: str, 
                                 duration_ms: float):
        """Log successful request completion."""
        logger.info(
            "Request completed",
            correlation_id=correlation_id,
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=round(duration_ms, 2),
            response_size=response.headers.get("Content-Length"),
            cache_status=response.headers.get("X-Cache-Status")
        )
        
        # Track performance metrics
        await self._track_performance_metrics(request, response, duration_ms)
    
    async def _log_request_failure(self, 
                                 request: Request, 
                                 correlation_id: str, 
                                 duration_ms: float, 
                                 error: str):
        """Log failed request."""
        logger.error(
            "Request failed",
            correlation_id=correlation_id,
            method=request.method,
            path=request.url.path,
            duration_ms=round(duration_ms, 2),
            error=error,
            client_ip=self._get_client_ip(request)
        )
        
        # Track error metrics
        await self._track_error_metrics(request, error)
    
    async def _track_performance_metrics(self, 
                                       request: Request, 
                                       response: Response, 
                                       duration_ms: float):
        """Track performance metrics for monitoring."""
        try:
            # This would typically send metrics to your monitoring system
            # For now, we'll just log the metrics
            
            # Categorize response time
            if duration_ms > 5000:
                performance_category = "very_slow"
            elif duration_ms > 2000:
                performance_category = "slow"
            elif duration_ms > 1000:
                performance_category = "moderate"
            else:
                performance_category = "fast"
            
            logger.debug(
                "Performance metrics",
                correlation_id=correlation_id_context.get(),
                endpoint=f"{request.method} {request.url.path}",
                duration_ms=duration_ms,
                performance_category=performance_category,
                status_code=response.status_code
            )
            
        except Exception as e:
            logger.warning("Failed to track performance metrics", error=str(e))
    
    async def _track_error_metrics(self, request: Request, error: str):
        """Track error metrics for monitoring."""
        try:
            logger.debug(
                "Error metrics",
                correlation_id=correlation_id_context.get(),
                endpoint=f"{request.method} {request.url.path}",
                error_type=type(error).__name__ if hasattr(error, '__class__') else "Unknown",
                error_message=error
            )
            
        except Exception as e:
            logger.warning("Failed to track error metrics", error=str(e))
    
    def _get_client_ip(self, request: Request) -> Optional[str]:
        """Extract client IP address from request."""
        # Check for forwarded headers first (for load balancers/proxies)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Take the first IP in the chain
            return forwarded_for.split(",")[0].strip()
        
        # Check for real IP header
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Fall back to direct client IP
        if request.client:
            return request.client.host
        
        return None


class RequestMetricsCollector:
    """Collects and aggregates request metrics."""
    
    def __init__(self):
        self.request_counts = {}
        self.response_times = {}
        self.error_counts = {}
        self.reset_interval = 300  # 5 minutes
        self.last_reset = time.time()
    
    def record_request(self, 
                      method: str, 
                      path: str, 
                      status_code: int, 
                      duration_ms: float):
        """Record request metrics."""
        self._check_reset()
        
        endpoint = f"{method} {path}"
        
        # Count requests
        if endpoint not in self.request_counts:
            self.request_counts[endpoint] = 0
        self.request_counts[endpoint] += 1
        
        # Track response times
        if endpoint not in self.response_times:
            self.response_times[endpoint] = []
        self.response_times[endpoint].append(duration_ms)
        
        # Count errors
        if status_code >= 400:
            if endpoint not in self.error_counts:
                self.error_counts[endpoint] = 0
            self.error_counts[endpoint] += 1
    
    def get_metrics_summary(self) -> dict:
        """Get aggregated metrics summary."""
        self._check_reset()
        
        summary = {
            "collection_period_seconds": self.reset_interval,
            "endpoints": {}
        }
        
        for endpoint in self.request_counts.keys():
            request_count = self.request_counts.get(endpoint, 0)
            response_times = self.response_times.get(endpoint, [])
            error_count = self.error_counts.get(endpoint, 0)
            
            if response_times:
                avg_response_time = sum(response_times) / len(response_times)
                max_response_time = max(response_times)
                min_response_time = min(response_times)
            else:
                avg_response_time = max_response_time = min_response_time = 0
            
            error_rate = (error_count / request_count * 100) if request_count > 0 else 0
            
            summary["endpoints"][endpoint] = {
                "request_count": request_count,
                "error_count": error_count,
                "error_rate_percentage": round(error_rate, 2),
                "avg_response_time_ms": round(avg_response_time, 2),
                "max_response_time_ms": round(max_response_time, 2),
                "min_response_time_ms": round(min_response_time, 2)
            }
        
        return summary
    
    def _check_reset(self):
        """Reset metrics if interval has passed."""
        current_time = time.time()
        if current_time - self.last_reset > self.reset_interval:
            self.request_counts.clear()
            self.response_times.clear()
            self.error_counts.clear()
            self.last_reset = current_time


@contextmanager
def correlation_context(correlation_id: str = None):
    """Context manager for setting correlation ID."""
    if correlation_id is None:
        correlation_id = f"ctx_{uuid.uuid4().hex[:12]}"
    
    token = correlation_id_context.set(correlation_id)
    try:
        yield correlation_id
    finally:
        correlation_id_context.reset(token)


def get_correlation_id() -> Optional[str]:
    """Get the current correlation ID from context."""
    return correlation_id_context.get()


def generate_correlation_id() -> str:
    """Generate a new correlation ID."""
    return f"gen_{uuid.uuid4().hex[:12]}"


# Global metrics collector
request_metrics_collector = RequestMetricsCollector()
