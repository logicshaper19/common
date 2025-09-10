"""
Enhanced External Service Client with Circuit Breaker Protection.

This module provides a robust client for external service calls with
circuit breaker protection, retry logic, and comprehensive error handling.
"""

import asyncio
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Union, List
from urllib.parse import urljoin

import httpx
from pydantic import BaseModel

from app.core.circuit_breaker import (
    CircuitBreaker, 
    CircuitBreakerConfig, 
    get_circuit_breaker,
    circuit_breaker
)
from app.core.error_handling import ErrorHandler, ErrorCode
from app.core.logging import get_logger
from app.core.config import get_settings

logger = get_logger(__name__)
settings = get_settings()


@dataclass
class RetryConfig:
    """Configuration for retry logic."""
    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True


@dataclass
class ServiceEndpoint:
    """External service endpoint configuration."""
    name: str
    base_url: str
    timeout: int = 30
    retry_config: Optional[RetryConfig] = None
    circuit_breaker_config: Optional[CircuitBreakerConfig] = None
    headers: Optional[Dict[str, str]] = None
    auth_token: Optional[str] = None


class ExternalServiceError(Exception):
    """Base exception for external service errors."""
    
    def __init__(
        self, 
        message: str, 
        service_name: str,
        status_code: Optional[int] = None,
        response_body: Optional[str] = None
    ):
        super().__init__(message)
        self.service_name = service_name
        self.status_code = status_code
        self.response_body = response_body


class ExternalServiceTimeoutError(ExternalServiceError):
    """Timeout error for external services."""
    pass


class ExternalServiceUnavailableError(ExternalServiceError):
    """Service unavailable error."""
    pass


class ExternalServiceClient:
    """
    Enhanced client for external service calls with circuit breaker protection.
    """
    
    def __init__(self, endpoint: ServiceEndpoint):
        self.endpoint = endpoint
        self.retry_config = endpoint.retry_config or RetryConfig()
        
        # Initialize circuit breaker
        cb_config = endpoint.circuit_breaker_config or CircuitBreakerConfig(
            failure_threshold=settings.circuit_breaker_failure_threshold,
            timeout=settings.circuit_breaker_timeout
        )
        self.circuit_breaker = get_circuit_breaker(
            f"external_service_{endpoint.name}",
            cb_config
        )
        
        # Setup HTTP client
        headers = {
            'User-Agent': f'Common-Platform/{settings.app_version}',
            'Accept': 'application/json',
            'Content-Type': 'application/json',
        }
        
        if endpoint.headers:
            headers.update(endpoint.headers)
        
        if endpoint.auth_token:
            headers['Authorization'] = f'Bearer {endpoint.auth_token}'
        
        self.client = httpx.AsyncClient(
            base_url=endpoint.base_url,
            timeout=endpoint.timeout,
            headers=headers,
            follow_redirects=True
        )
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.client.aclose()
    
    async def get(
        self, 
        path: str, 
        params: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Make a GET request."""
        return await self._make_request('GET', path, params=params, **kwargs)
    
    async def post(
        self, 
        path: str, 
        data: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Make a POST request."""
        return await self._make_request('POST', path, json=data, **kwargs)
    
    async def put(
        self, 
        path: str, 
        data: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Make a PUT request."""
        return await self._make_request('PUT', path, json=data, **kwargs)
    
    async def delete(
        self, 
        path: str, 
        **kwargs
    ) -> Dict[str, Any]:
        """Make a DELETE request."""
        return await self._make_request('DELETE', path, **kwargs)
    
    async def _make_request(
        self, 
        method: str, 
        path: str, 
        **kwargs
    ) -> Dict[str, Any]:
        """Make an HTTP request with circuit breaker and retry protection."""
        
        async def _request():
            return await self._execute_request(method, path, **kwargs)
        
        # Use circuit breaker protection
        return await self.circuit_breaker.call(_request)
    
    async def _execute_request(
        self, 
        method: str, 
        path: str, 
        **kwargs
    ) -> Dict[str, Any]:
        """Execute HTTP request with retry logic."""
        last_exception = None
        
        for attempt in range(self.retry_config.max_retries + 1):
            try:
                start_time = time.time()
                
                response = await self.client.request(method, path, **kwargs)
                
                duration = time.time() - start_time
                
                # Log successful request
                logger.info(
                    "External service request successful",
                    service=self.endpoint.name,
                    method=method,
                    path=path,
                    status_code=response.status_code,
                    duration=duration,
                    attempt=attempt + 1
                )
                
                # Handle HTTP errors
                if response.status_code >= 400:
                    await self._handle_http_error(response, method, path)
                
                # Parse response
                try:
                    return response.json()
                except Exception:
                    # Return empty dict for non-JSON responses
                    return {}
                
            except httpx.TimeoutException as e:
                last_exception = ExternalServiceTimeoutError(
                    f"Request to {self.endpoint.name} timed out",
                    self.endpoint.name
                )
                
                logger.warning(
                    "External service request timeout",
                    service=self.endpoint.name,
                    method=method,
                    path=path,
                    attempt=attempt + 1,
                    timeout=self.endpoint.timeout
                )
                
            except httpx.ConnectError as e:
                last_exception = ExternalServiceUnavailableError(
                    f"Failed to connect to {self.endpoint.name}",
                    self.endpoint.name
                )
                
                logger.warning(
                    "External service connection error",
                    service=self.endpoint.name,
                    method=method,
                    path=path,
                    attempt=attempt + 1,
                    error=str(e)
                )
                
            except Exception as e:
                last_exception = ExternalServiceError(
                    f"Unexpected error calling {self.endpoint.name}: {str(e)}",
                    self.endpoint.name
                )
                
                logger.error(
                    "External service unexpected error",
                    service=self.endpoint.name,
                    method=method,
                    path=path,
                    attempt=attempt + 1,
                    error=str(e),
                    error_type=type(e).__name__
                )
            
            # Calculate retry delay
            if attempt < self.retry_config.max_retries:
                delay = self._calculate_retry_delay(attempt)
                
                logger.info(
                    "Retrying external service request",
                    service=self.endpoint.name,
                    attempt=attempt + 1,
                    delay=delay
                )
                
                await asyncio.sleep(delay)
        
        # All retries exhausted
        logger.error(
            "External service request failed after all retries",
            service=self.endpoint.name,
            method=method,
            path=path,
            max_retries=self.retry_config.max_retries
        )
        
        raise last_exception
    
    async def _handle_http_error(self, response: httpx.Response, method: str, path: str):
        """Handle HTTP error responses."""
        try:
            error_body = response.text
        except Exception:
            error_body = "Unable to read response body"
        
        if response.status_code >= 500:
            # Server error - should trigger circuit breaker
            raise ExternalServiceUnavailableError(
                f"Server error from {self.endpoint.name}: {response.status_code}",
                self.endpoint.name,
                response.status_code,
                error_body
            )
        elif response.status_code == 429:
            # Rate limited - should trigger circuit breaker
            raise ExternalServiceUnavailableError(
                f"Rate limited by {self.endpoint.name}",
                self.endpoint.name,
                response.status_code,
                error_body
            )
        else:
            # Client error - should not trigger circuit breaker
            raise ExternalServiceError(
                f"Client error from {self.endpoint.name}: {response.status_code}",
                self.endpoint.name,
                response.status_code,
                error_body
            )
    
    def _calculate_retry_delay(self, attempt: int) -> float:
        """Calculate retry delay with exponential backoff and jitter."""
        delay = self.retry_config.base_delay * (
            self.retry_config.exponential_base ** attempt
        )
        
        # Apply maximum delay
        delay = min(delay, self.retry_config.max_delay)
        
        # Add jitter to prevent thundering herd
        if self.retry_config.jitter:
            import random
            delay *= (0.5 + random.random() * 0.5)
        
        return delay
    
    def get_status(self) -> Dict[str, Any]:
        """Get client status including circuit breaker status."""
        return {
            'endpoint': {
                'name': self.endpoint.name,
                'base_url': self.endpoint.base_url,
                'timeout': self.endpoint.timeout,
            },
            'circuit_breaker': self.circuit_breaker.get_status(),
            'retry_config': {
                'max_retries': self.retry_config.max_retries,
                'base_delay': self.retry_config.base_delay,
                'max_delay': self.retry_config.max_delay,
            }
        }


class ExternalServiceRegistry:
    """Registry for managing external service clients."""
    
    def __init__(self):
        self._clients: Dict[str, ExternalServiceClient] = {}
        self._endpoints: Dict[str, ServiceEndpoint] = {}
    
    def register_endpoint(self, endpoint: ServiceEndpoint) -> None:
        """Register an external service endpoint."""
        self._endpoints[endpoint.name] = endpoint
        logger.info(f"Registered external service endpoint: {endpoint.name}")
    
    async def get_client(self, service_name: str) -> ExternalServiceClient:
        """Get or create a client for the specified service."""
        if service_name not in self._endpoints:
            raise ValueError(f"Unknown service: {service_name}")
        
        if service_name not in self._clients:
            endpoint = self._endpoints[service_name]
            self._clients[service_name] = ExternalServiceClient(endpoint)
        
        return self._clients[service_name]
    
    def get_all_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all registered services."""
        return {
            name: client.get_status() 
            for name, client in self._clients.items()
        }
    
    async def close_all(self) -> None:
        """Close all client connections."""
        for client in self._clients.values():
            await client.client.aclose()
        self._clients.clear()


# Global registry
_service_registry = ExternalServiceRegistry()


def get_service_registry() -> ExternalServiceRegistry:
    """Get the global service registry."""
    return _service_registry


def register_external_service(endpoint: ServiceEndpoint) -> None:
    """Register an external service endpoint."""
    _service_registry.register_endpoint(endpoint)


async def get_external_service_client(service_name: str) -> ExternalServiceClient:
    """Get a client for the specified external service."""
    return await _service_registry.get_client(service_name)
