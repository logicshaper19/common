"""
Circuit Breaker Pattern Implementation for External Service Protection.

This module provides circuit breaker functionality to protect against
cascading failures when external services are unavailable.
"""

import asyncio
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, Optional, TypeVar, Generic, Union
from functools import wraps

from app.core.logging import get_logger

logger = get_logger(__name__)

T = TypeVar('T')


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"        # Normal operation
    OPEN = "open"           # Failing, rejecting requests
    HALF_OPEN = "half_open" # Testing if service recovered


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker."""
    
    # Failure threshold to open circuit
    failure_threshold: int = 5
    
    # Success threshold to close circuit from half-open
    success_threshold: int = 3
    
    # Time to wait before trying half-open (seconds)
    timeout: int = 60
    
    # Time window for failure counting (seconds)
    failure_window: int = 300
    
    # Expected exceptions that should trigger circuit breaker
    expected_exceptions: tuple = (
        ConnectionError,
        TimeoutError,
        OSError,
    )
    
    # Exceptions that should NOT trigger circuit breaker
    ignored_exceptions: tuple = (
        ValueError,
        TypeError,
        KeyError,
    )


@dataclass
class CircuitBreakerMetrics:
    """Metrics for circuit breaker monitoring."""
    
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    circuit_open_count: int = 0
    last_failure_time: Optional[datetime] = None
    last_success_time: Optional[datetime] = None
    current_consecutive_failures: int = 0
    current_consecutive_successes: int = 0
    
    def success_rate(self) -> float:
        """Calculate success rate."""
        if self.total_requests == 0:
            return 1.0
        return self.successful_requests / self.total_requests
    
    def failure_rate(self) -> float:
        """Calculate failure rate."""
        return 1.0 - self.success_rate()


class CircuitBreakerError(Exception):
    """Exception raised when circuit breaker is open."""
    
    def __init__(self, message: str, circuit_name: str, state: CircuitState):
        super().__init__(message)
        self.circuit_name = circuit_name
        self.state = state


class CircuitBreaker(Generic[T]):
    """
    Circuit breaker implementation for protecting external service calls.
    
    The circuit breaker monitors failures and prevents calls to failing
    services, allowing them time to recover.
    """
    
    def __init__(self, name: str, config: Optional[CircuitBreakerConfig] = None):
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self.state = CircuitState.CLOSED
        self.metrics = CircuitBreakerMetrics()
        self._failure_times: list = []
        self._last_state_change = datetime.utcnow()
        self._lock = asyncio.Lock()
    
    async def call(self, func: Callable[..., T], *args, **kwargs) -> T:
        """
        Execute a function with circuit breaker protection.
        
        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
            
        Raises:
            CircuitBreakerError: When circuit is open
            Original exception: When function fails
        """
        async with self._lock:
            await self._update_state()
            
            if self.state == CircuitState.OPEN:
                raise CircuitBreakerError(
                    f"Circuit breaker '{self.name}' is OPEN",
                    self.name,
                    self.state
                )
            
            self.metrics.total_requests += 1
        
        try:
            # Execute the function
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)
            
            await self._record_success()
            return result
            
        except Exception as e:
            await self._record_failure(e)
            raise
    
    async def _update_state(self) -> None:
        """Update circuit breaker state based on current conditions."""
        now = datetime.utcnow()
        
        if self.state == CircuitState.OPEN:
            # Check if timeout period has passed
            if now - self._last_state_change >= timedelta(seconds=self.config.timeout):
                await self._transition_to_half_open()
        
        elif self.state == CircuitState.HALF_OPEN:
            # Check if we should close or open based on recent results
            if self.metrics.current_consecutive_successes >= self.config.success_threshold:
                await self._transition_to_closed()
            elif self.metrics.current_consecutive_failures >= 1:
                await self._transition_to_open()
    
    async def _record_success(self) -> None:
        """Record a successful operation."""
        async with self._lock:
            self.metrics.successful_requests += 1
            self.metrics.last_success_time = datetime.utcnow()
            self.metrics.current_consecutive_successes += 1
            self.metrics.current_consecutive_failures = 0
            
            logger.debug(
                "Circuit breaker success recorded",
                circuit_name=self.name,
                consecutive_successes=self.metrics.current_consecutive_successes
            )
    
    async def _record_failure(self, exception: Exception) -> None:
        """Record a failed operation."""
        # Check if this exception should trigger circuit breaker
        if not self._should_trigger_circuit_breaker(exception):
            logger.debug(
                "Exception ignored by circuit breaker",
                circuit_name=self.name,
                exception_type=type(exception).__name__
            )
            return
        
        async with self._lock:
            now = datetime.utcnow()
            self.metrics.failed_requests += 1
            self.metrics.last_failure_time = now
            self.metrics.current_consecutive_failures += 1
            self.metrics.current_consecutive_successes = 0
            
            # Add to failure times for window-based counting
            self._failure_times.append(now)
            
            # Remove old failures outside the window
            cutoff_time = now - timedelta(seconds=self.config.failure_window)
            self._failure_times = [t for t in self._failure_times if t > cutoff_time]
            
            logger.warning(
                "Circuit breaker failure recorded",
                circuit_name=self.name,
                consecutive_failures=self.metrics.current_consecutive_failures,
                failures_in_window=len(self._failure_times),
                exception_type=type(exception).__name__
            )
            
            # Check if we should open the circuit
            if (self.state == CircuitState.CLOSED and 
                len(self._failure_times) >= self.config.failure_threshold):
                await self._transition_to_open()
    
    def _should_trigger_circuit_breaker(self, exception: Exception) -> bool:
        """Check if an exception should trigger the circuit breaker."""
        # Check ignored exceptions first
        if isinstance(exception, self.config.ignored_exceptions):
            return False
        
        # Check expected exceptions
        if isinstance(exception, self.config.expected_exceptions):
            return True
        
        # Default: trigger for any exception not explicitly ignored
        return True
    
    async def _transition_to_open(self) -> None:
        """Transition circuit to OPEN state."""
        self.state = CircuitState.OPEN
        self._last_state_change = datetime.utcnow()
        self.metrics.circuit_open_count += 1
        
        logger.error(
            "Circuit breaker opened",
            circuit_name=self.name,
            failure_count=len(self._failure_times),
            consecutive_failures=self.metrics.current_consecutive_failures
        )
    
    async def _transition_to_half_open(self) -> None:
        """Transition circuit to HALF_OPEN state."""
        self.state = CircuitState.HALF_OPEN
        self._last_state_change = datetime.utcnow()
        
        logger.info(
            "Circuit breaker half-opened",
            circuit_name=self.name,
            timeout_duration=self.config.timeout
        )
    
    async def _transition_to_closed(self) -> None:
        """Transition circuit to CLOSED state."""
        self.state = CircuitState.CLOSED
        self._last_state_change = datetime.utcnow()
        self.metrics.current_consecutive_failures = 0
        self._failure_times.clear()
        
        logger.info(
            "Circuit breaker closed",
            circuit_name=self.name,
            consecutive_successes=self.metrics.current_consecutive_successes
        )
    
    def get_status(self) -> Dict[str, Any]:
        """Get current circuit breaker status."""
        return {
            "name": self.name,
            "state": self.state.value,
            "metrics": {
                "total_requests": self.metrics.total_requests,
                "successful_requests": self.metrics.successful_requests,
                "failed_requests": self.metrics.failed_requests,
                "success_rate": self.metrics.success_rate(),
                "failure_rate": self.metrics.failure_rate(),
                "circuit_open_count": self.metrics.circuit_open_count,
                "current_consecutive_failures": self.metrics.current_consecutive_failures,
                "current_consecutive_successes": self.metrics.current_consecutive_successes,
                "last_failure_time": self.metrics.last_failure_time.isoformat() if self.metrics.last_failure_time else None,
                "last_success_time": self.metrics.last_success_time.isoformat() if self.metrics.last_success_time else None,
            },
            "config": {
                "failure_threshold": self.config.failure_threshold,
                "success_threshold": self.config.success_threshold,
                "timeout": self.config.timeout,
                "failure_window": self.config.failure_window,
            },
            "last_state_change": self._last_state_change.isoformat(),
            "failures_in_window": len(self._failure_times)
        }


class CircuitBreakerRegistry:
    """Registry for managing multiple circuit breakers."""
    
    def __init__(self):
        self._breakers: Dict[str, CircuitBreaker] = {}
    
    def get_or_create(
        self, 
        name: str, 
        config: Optional[CircuitBreakerConfig] = None
    ) -> CircuitBreaker:
        """Get existing circuit breaker or create new one."""
        if name not in self._breakers:
            self._breakers[name] = CircuitBreaker(name, config)
        return self._breakers[name]
    
    def get_all_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all circuit breakers."""
        return {name: breaker.get_status() for name, breaker in self._breakers.items()}
    
    def reset_all(self) -> None:
        """Reset all circuit breakers to closed state."""
        for breaker in self._breakers.values():
            breaker.state = CircuitState.CLOSED
            breaker.metrics = CircuitBreakerMetrics()
            breaker._failure_times.clear()


# Global registry
_circuit_breaker_registry = CircuitBreakerRegistry()


def get_circuit_breaker(
    name: str, 
    config: Optional[CircuitBreakerConfig] = None
) -> CircuitBreaker:
    """Get or create a circuit breaker."""
    return _circuit_breaker_registry.get_or_create(name, config)


def circuit_breaker(
    name: str,
    failure_threshold: int = 5,
    success_threshold: int = 3,
    timeout: int = 60,
    failure_window: int = 300
):
    """
    Decorator to add circuit breaker protection to a function.
    
    Args:
        name: Circuit breaker name
        failure_threshold: Number of failures to open circuit
        success_threshold: Number of successes to close circuit
        timeout: Seconds to wait before trying half-open
        failure_window: Time window for failure counting
    """
    def decorator(func: Callable) -> Callable:
        config = CircuitBreakerConfig(
            failure_threshold=failure_threshold,
            success_threshold=success_threshold,
            timeout=timeout,
            failure_window=failure_window
        )
        breaker = get_circuit_breaker(name, config)
        
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            return await breaker.call(func, *args, **kwargs)
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            return asyncio.run(breaker.call(func, *args, **kwargs))
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def get_all_circuit_breaker_status() -> Dict[str, Dict[str, Any]]:
    """Get status of all circuit breakers."""
    return _circuit_breaker_registry.get_all_status()
