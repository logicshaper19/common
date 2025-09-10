"""
Input validation middleware for comprehensive request validation.

This middleware provides automatic input validation and sanitization
for all API requests to prevent injection attacks and ensure data integrity.
"""

import json
import time
from typing import Dict, Any, Optional, List
from urllib.parse import unquote

from fastapi import Request, Response, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.core.logging import get_logger
from app.core.input_validation import InputValidator, InputValidationError

logger = get_logger(__name__)


class InputValidationMiddleware(BaseHTTPMiddleware):
    """
    Middleware for automatic input validation and sanitization.
    
    Features:
    - Validates all request parameters and body content
    - Sanitizes input to prevent XSS and SQL injection
    - Logs suspicious input attempts
    - Configurable validation rules per endpoint
    """
    
    def __init__(
        self,
        app: ASGIApp,
        validate_query_params: bool = True,
        validate_path_params: bool = True,
        validate_request_body: bool = True,
        max_request_size: int = 10 * 1024 * 1024,  # 10MB
        excluded_paths: Optional[List[str]] = None
    ):
        super().__init__(app)
        self.validate_query_params = validate_query_params
        self.validate_path_params = validate_path_params
        self.validate_request_body = validate_request_body
        self.max_request_size = max_request_size
        self.excluded_paths = excluded_paths or [
            '/docs',
            '/redoc',
            '/openapi.json',
            '/health',
            '/metrics'
        ]
        self.validator = InputValidator()
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """Process request through input validation."""
        start_time = time.time()
        
        # Skip validation for excluded paths
        if self._should_skip_validation(request.url.path):
            return await call_next(request)
        
        try:
            # Validate request size
            if hasattr(request, 'content_length') and request.content_length:
                if request.content_length > self.max_request_size:
                    logger.warning(
                        "Request size exceeds limit",
                        path=request.url.path,
                        size=request.content_length,
                        limit=self.max_request_size
                    )
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail="Request size exceeds maximum allowed size"
                    )
            
            # Validate query parameters
            if self.validate_query_params and request.query_params:
                await self._validate_query_parameters(request)
            
            # Validate path parameters
            if self.validate_path_params:
                await self._validate_path_parameters(request)
            
            # Validate request body
            if self.validate_request_body and request.method in ['POST', 'PUT', 'PATCH']:
                await self._validate_request_body(request)
            
            # Process request
            response = await call_next(request)
            
            # Log successful validation
            processing_time = time.time() - start_time
            logger.debug(
                "Request validation completed",
                path=request.url.path,
                method=request.method,
                processing_time=processing_time
            )
            
            return response
            
        except HTTPException:
            raise
        except InputValidationError as e:
            logger.warning(
                "Input validation failed",
                path=request.url.path,
                method=request.method,
                field=e.field,
                error=e.message
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "message": "Input validation failed",
                    "error_code": "INVALID_INPUT",
                    "field": e.field,
                    "details": e.message
                }
            )
        except Exception as e:
            logger.error(
                "Input validation middleware error",
                path=request.url.path,
                method=request.method,
                error=str(e)
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error during input validation"
            )
    
    def _should_skip_validation(self, path: str) -> bool:
        """Check if validation should be skipped for this path."""
        return any(excluded in path for excluded in self.excluded_paths)
    
    async def _validate_query_parameters(self, request: Request) -> None:
        """Validate query parameters."""
        for key, value in request.query_params.items():
            try:
                # Decode URL-encoded values
                decoded_value = unquote(value)
                
                # Validate parameter name
                self.validator.validate_and_sanitize(
                    key,
                    f"query_param_name_{key}",
                    data_type="string",
                    max_length=100,
                    pattern=r'^[a-zA-Z_][a-zA-Z0-9_-]*$'
                )
                
                # Validate parameter value
                sanitized_value = self.validator.validate_and_sanitize(
                    decoded_value,
                    f"query_param_{key}",
                    data_type="string",
                    max_length=1000,
                    required=False
                )
                
                # Update query params with sanitized values
                # Note: This is read-only in Starlette, so we log instead
                if sanitized_value != decoded_value:
                    logger.info(
                        "Query parameter sanitized",
                        param=key,
                        original=decoded_value[:100],
                        sanitized=sanitized_value[:100]
                    )
                
            except InputValidationError as e:
                raise InputValidationError(
                    f"Invalid query parameter '{key}': {e.message}",
                    f"query_param_{key}",
                    value
                )
    
    async def _validate_path_parameters(self, request: Request) -> None:
        """Validate path parameters."""
        path_parts = request.url.path.split('/')
        
        for i, part in enumerate(path_parts):
            if part:  # Skip empty parts
                try:
                    # Check for path traversal attempts
                    if '..' in part or part.startswith('.'):
                        raise InputValidationError(
                            "Path traversal attempt detected",
                            f"path_part_{i}",
                            part
                        )
                    
                    # Validate path component
                    self.validator.validate_and_sanitize(
                        part,
                        f"path_part_{i}",
                        data_type="string",
                        max_length=255,
                        required=False
                    )
                    
                except InputValidationError as e:
                    raise InputValidationError(
                        f"Invalid path component '{part}': {e.message}",
                        f"path_part_{i}",
                        part
                    )
    
    async def _validate_request_body(self, request: Request) -> None:
        """Validate request body content."""
        try:
            # Get content type
            content_type = request.headers.get('content-type', '').lower()
            
            if 'application/json' in content_type:
                await self._validate_json_body(request)
            elif 'application/x-www-form-urlencoded' in content_type:
                await self._validate_form_body(request)
            elif 'multipart/form-data' in content_type:
                # File uploads are handled separately
                pass
            else:
                # For other content types, perform basic validation
                body = await request.body()
                if body:
                    body_str = body.decode('utf-8', errors='ignore')
                    self.validator.validate_and_sanitize(
                        body_str,
                        "request_body",
                        data_type="string",
                        max_length=self.max_request_size,
                        required=False
                    )
            
        except UnicodeDecodeError:
            raise InputValidationError(
                "Request body contains invalid characters",
                "request_body",
                None
            )
        except json.JSONDecodeError:
            raise InputValidationError(
                "Invalid JSON in request body",
                "request_body",
                None
            )
    
    async def _validate_json_body(self, request: Request) -> None:
        """Validate JSON request body."""
        try:
            body = await request.body()
            if not body:
                return
            
            # Parse JSON
            try:
                json_data = json.loads(body)
            except json.JSONDecodeError as e:
                raise InputValidationError(
                    f"Invalid JSON: {str(e)}",
                    "request_body",
                    body.decode('utf-8', errors='ignore')[:100]
                )
            
            # Validate JSON structure
            await self._validate_json_object(json_data, "request_body")
            
        except InputValidationError:
            raise
        except Exception as e:
            raise InputValidationError(
                f"JSON validation error: {str(e)}",
                "request_body",
                None
            )
    
    async def _validate_json_object(self, obj: Any, field_prefix: str, depth: int = 0) -> None:
        """Recursively validate JSON object."""
        # Prevent deeply nested objects (DoS protection)
        if depth > 10:
            raise InputValidationError(
                "JSON object too deeply nested",
                field_prefix,
                None
            )
        
        if isinstance(obj, dict):
            # Limit number of keys
            if len(obj) > 100:
                raise InputValidationError(
                    "Too many keys in JSON object",
                    field_prefix,
                    len(obj)
                )
            
            for key, value in obj.items():
                # Validate key
                self.validator.validate_and_sanitize(
                    key,
                    f"{field_prefix}.{key}_key",
                    data_type="string",
                    max_length=100
                )
                
                # Recursively validate value
                await self._validate_json_object(value, f"{field_prefix}.{key}", depth + 1)
        
        elif isinstance(obj, list):
            # Limit array size
            if len(obj) > 1000:
                raise InputValidationError(
                    "Array too large in JSON",
                    field_prefix,
                    len(obj)
                )
            
            for i, item in enumerate(obj):
                await self._validate_json_object(item, f"{field_prefix}[{i}]", depth + 1)
        
        elif isinstance(obj, str):
            # Validate string values
            self.validator.validate_and_sanitize(
                obj,
                field_prefix,
                data_type="string",
                max_length=10000,
                required=False
            )
    
    async def _validate_form_body(self, request: Request) -> None:
        """Validate form-encoded request body."""
        try:
            form_data = await request.form()
            
            for key, value in form_data.items():
                # Validate field name
                self.validator.validate_and_sanitize(
                    key,
                    f"form_field_{key}_name",
                    data_type="string",
                    max_length=100,
                    pattern=r'^[a-zA-Z_][a-zA-Z0-9_-]*$'
                )
                
                # Validate field value
                if hasattr(value, 'read'):  # File upload
                    # File validation is handled separately
                    continue
                else:
                    self.validator.validate_and_sanitize(
                        str(value),
                        f"form_field_{key}",
                        data_type="string",
                        max_length=10000,
                        required=False
                    )
                
        except Exception as e:
            raise InputValidationError(
                f"Form validation error: {str(e)}",
                "form_data",
                None
            )


class SecurityHeadersValidationMiddleware(BaseHTTPMiddleware):
    """
    Middleware to validate and enforce security headers.
    """
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """Validate security headers and add security checks."""
        
        # Check for suspicious headers
        suspicious_headers = [
            'x-forwarded-host',
            'x-original-url',
            'x-rewrite-url'
        ]
        
        for header in suspicious_headers:
            if header in request.headers:
                value = request.headers[header]
                logger.warning(
                    "Suspicious header detected",
                    header=header,
                    value=value,
                    client_ip=request.client.host if request.client else "unknown"
                )
        
        # Validate User-Agent
        user_agent = request.headers.get('user-agent', '')
        if len(user_agent) > 1000:
            logger.warning(
                "Unusually long User-Agent header",
                length=len(user_agent),
                client_ip=request.client.host if request.client else "unknown"
            )
        
        # Process request
        response = await call_next(request)
        
        return response


def create_input_validation_middleware(
    validate_query_params: bool = True,
    validate_path_params: bool = True,
    validate_request_body: bool = True,
    max_request_size: int = 10 * 1024 * 1024,
    excluded_paths: Optional[List[str]] = None
) -> InputValidationMiddleware:
    """
    Create input validation middleware with configuration.
    
    Args:
        validate_query_params: Whether to validate query parameters
        validate_path_params: Whether to validate path parameters
        validate_request_body: Whether to validate request body
        max_request_size: Maximum request size in bytes
        excluded_paths: Paths to exclude from validation
        
    Returns:
        Configured InputValidationMiddleware
    """
    return InputValidationMiddleware(
        app=None,  # Will be set by FastAPI
        validate_query_params=validate_query_params,
        validate_path_params=validate_path_params,
        validate_request_body=validate_request_body,
        max_request_size=max_request_size,
        excluded_paths=excluded_paths
    )
