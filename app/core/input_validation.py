"""
Comprehensive input validation and sanitization utilities.

This module provides robust input validation, sanitization, and security
measures to prevent SQL injection, XSS, and other input-based attacks.
"""

import re
import html
import uuid
from typing import Any, Dict, List, Optional, Union, Tuple
from urllib.parse import urlparse
from datetime import datetime
from decimal import Decimal, InvalidOperation

from fastapi import HTTPException, status
from pydantic import BaseModel, validator
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.logging import get_logger

# Optional dependencies with graceful fallbacks
try:
    import bleach
    HAS_BLEACH = True
except ImportError:
    HAS_BLEACH = False

logger = get_logger(__name__)


class InputValidationError(Exception):
    """Exception raised when input validation fails."""
    
    def __init__(self, message: str, field: str = None, value: Any = None):
        self.message = message
        self.field = field
        self.value = value
        super().__init__(message)


class SQLInjectionDetector:
    """
    Detects potential SQL injection attempts in user input.
    """
    
    # SQL injection patterns
    SQL_INJECTION_PATTERNS = [
        r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|EXECUTE)\b)",
        r"(\b(UNION|OR|AND)\s+\d+\s*=\s*\d+)",
        r"(--|\#|\/\*|\*\/)",
        r"(\b(SLEEP|WAITFOR|DELAY)\s*\()",
        r"(\'\s*(OR|AND)\s*\'\w*\'\s*=\s*\'\w*)",
        r"(\'\s*;\s*(DROP|DELETE|INSERT|UPDATE))",
        r"(\bINFORMATION_SCHEMA\b)",
        r"(\bSYS\.\w+)",
        r"(\bxp_\w+)",
        r"(\bsp_\w+)",
    ]
    
    def __init__(self):
        self.compiled_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.SQL_INJECTION_PATTERNS]
    
    def detect_sql_injection(self, input_value: str) -> Tuple[bool, List[str]]:
        """
        Detect potential SQL injection in input.
        
        Args:
            input_value: Input string to check
            
        Returns:
            Tuple of (is_suspicious, matched_patterns)
        """
        if not isinstance(input_value, str):
            return False, []
        
        matched_patterns = []
        
        for pattern in self.compiled_patterns:
            if pattern.search(input_value):
                matched_patterns.append(pattern.pattern)
        
        return len(matched_patterns) > 0, matched_patterns
    
    def sanitize_sql_input(self, input_value: str) -> str:
        """
        Sanitize input to prevent SQL injection.
        
        Args:
            input_value: Input string to sanitize
            
        Returns:
            Sanitized string
        """
        if not isinstance(input_value, str):
            return str(input_value)
        
        # Remove dangerous SQL keywords and characters
        sanitized = input_value
        
        # Remove SQL comments
        sanitized = re.sub(r'--.*$', '', sanitized, flags=re.MULTILINE)
        sanitized = re.sub(r'/\*.*?\*/', '', sanitized, flags=re.DOTALL)
        
        # Escape single quotes
        sanitized = sanitized.replace("'", "''")
        
        # Remove or escape dangerous characters
        dangerous_chars = [';', '--', '/*', '*/', 'xp_', 'sp_']
        for char in dangerous_chars:
            sanitized = sanitized.replace(char, '')
        
        return sanitized.strip()


class XSSProtector:
    """
    Protects against Cross-Site Scripting (XSS) attacks.
    """
    
    # Allowed HTML tags for rich text content
    ALLOWED_TAGS = [
        'p', 'br', 'strong', 'em', 'u', 'ol', 'ul', 'li',
        'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'blockquote'
    ]
    
    # Allowed HTML attributes
    ALLOWED_ATTRIBUTES = {
        '*': ['class'],
        'a': ['href', 'title'],
        'img': ['src', 'alt', 'width', 'height']
    }
    
    # XSS patterns to detect
    XSS_PATTERNS = [
        r'<script[^>]*>.*?</script>',
        r'javascript:',
        r'on\w+\s*=',
        r'<iframe[^>]*>.*?</iframe>',
        r'<object[^>]*>.*?</object>',
        r'<embed[^>]*>.*?</embed>',
        r'<form[^>]*>.*?</form>',
        r'<input[^>]*>',
        r'<meta[^>]*>',
        r'<link[^>]*>',
        r'vbscript:',
        r'data:text/html',
    ]
    
    def __init__(self):
        self.compiled_patterns = [re.compile(pattern, re.IGNORECASE | re.DOTALL) for pattern in self.XSS_PATTERNS]
    
    def detect_xss(self, input_value: str) -> Tuple[bool, List[str]]:
        """
        Detect potential XSS in input.
        
        Args:
            input_value: Input string to check
            
        Returns:
            Tuple of (is_suspicious, matched_patterns)
        """
        if not isinstance(input_value, str):
            return False, []
        
        matched_patterns = []
        
        for pattern in self.compiled_patterns:
            if pattern.search(input_value):
                matched_patterns.append(pattern.pattern)
        
        return len(matched_patterns) > 0, matched_patterns
    
    def sanitize_html(self, input_value: str, allow_tags: bool = False) -> str:
        """
        Sanitize HTML input to prevent XSS.
        
        Args:
            input_value: Input string to sanitize
            allow_tags: Whether to allow safe HTML tags
            
        Returns:
            Sanitized string
        """
        if not isinstance(input_value, str):
            return str(input_value)
        
        if allow_tags and HAS_BLEACH:
            # Use bleach to clean HTML while preserving safe tags
            return bleach.clean(
                input_value,
                tags=self.ALLOWED_TAGS,
                attributes=self.ALLOWED_ATTRIBUTES,
                strip=True
            )
        else:
            # Escape all HTML (fallback when bleach is not available)
            return html.escape(input_value)
    
    def escape_for_javascript(self, input_value: str) -> str:
        """
        Escape string for safe use in JavaScript context.
        
        Args:
            input_value: Input string to escape
            
        Returns:
            JavaScript-safe string
        """
        if not isinstance(input_value, str):
            input_value = str(input_value)
        
        # Escape dangerous characters for JavaScript
        escape_map = {
            '\\': '\\\\',
            '"': '\\"',
            "'": "\\'",
            '\n': '\\n',
            '\r': '\\r',
            '\t': '\\t',
            '<': '\\u003c',
            '>': '\\u003e',
            '&': '\\u0026',
            '/': '\\/',
        }
        
        for char, escaped in escape_map.items():
            input_value = input_value.replace(char, escaped)
        
        return input_value


class InputValidator:
    """
    Comprehensive input validation and sanitization.
    """
    
    def __init__(self):
        self.sql_detector = SQLInjectionDetector()
        self.xss_protector = XSSProtector()
    
    def validate_and_sanitize(
        self,
        value: Any,
        field_name: str,
        data_type: str = "string",
        max_length: Optional[int] = None,
        min_length: Optional[int] = None,
        allow_html: bool = False,
        required: bool = True,
        pattern: Optional[str] = None
    ) -> Any:
        """
        Validate and sanitize input value.
        
        Args:
            value: Input value to validate
            field_name: Name of the field being validated
            data_type: Expected data type
            max_length: Maximum length for strings
            min_length: Minimum length for strings
            allow_html: Whether to allow HTML content
            required: Whether the field is required
            pattern: Regex pattern to match
            
        Returns:
            Validated and sanitized value
            
        Raises:
            InputValidationError: If validation fails
        """
        # Check if required
        if required and (value is None or value == ""):
            raise InputValidationError(f"Field '{field_name}' is required", field_name, value)
        
        # Handle None values for optional fields
        if value is None:
            return None
        
        # Convert to string for validation
        str_value = str(value)
        
        # Check for SQL injection
        is_sql_suspicious, sql_patterns = self.sql_detector.detect_sql_injection(str_value)
        if is_sql_suspicious:
            logger.warning(
                "SQL injection attempt detected",
                field=field_name,
                value=str_value[:100],
                patterns=sql_patterns
            )
            raise InputValidationError(
                f"Invalid input detected in field '{field_name}': potential SQL injection",
                field_name,
                value
            )
        
        # Check for XSS
        is_xss_suspicious, xss_patterns = self.xss_protector.detect_xss(str_value)
        if is_xss_suspicious and not allow_html:
            logger.warning(
                "XSS attempt detected",
                field=field_name,
                value=str_value[:100],
                patterns=xss_patterns
            )
            raise InputValidationError(
                f"Invalid input detected in field '{field_name}': potential XSS",
                field_name,
                value
            )
        
        # Sanitize based on data type
        if data_type == "string":
            return self._validate_string(str_value, field_name, max_length, min_length, allow_html, pattern)
        elif data_type == "email":
            return self._validate_email(str_value, field_name)
        elif data_type == "uuid":
            return self._validate_uuid(str_value, field_name)
        elif data_type == "integer":
            return self._validate_integer(value, field_name)
        elif data_type == "decimal":
            return self._validate_decimal(value, field_name)
        elif data_type == "boolean":
            return self._validate_boolean(value, field_name)
        elif data_type == "url":
            return self._validate_url(str_value, field_name)
        else:
            return value
    
    def _validate_string(
        self,
        value: str,
        field_name: str,
        max_length: Optional[int],
        min_length: Optional[int],
        allow_html: bool,
        pattern: Optional[str]
    ) -> str:
        """Validate string input."""
        # Sanitize HTML/XSS
        sanitized = self.xss_protector.sanitize_html(value, allow_html)
        
        # Check length constraints
        if min_length and len(sanitized) < min_length:
            raise InputValidationError(
                f"Field '{field_name}' must be at least {min_length} characters",
                field_name,
                value
            )
        
        if max_length and len(sanitized) > max_length:
            raise InputValidationError(
                f"Field '{field_name}' must not exceed {max_length} characters",
                field_name,
                value
            )
        
        # Check pattern if provided
        if pattern and not re.match(pattern, sanitized):
            raise InputValidationError(
                f"Field '{field_name}' does not match required format",
                field_name,
                value
            )
        
        return sanitized
    
    def _validate_email(self, value: str, field_name: str) -> str:
        """Validate email address."""
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, value):
            raise InputValidationError(
                f"Field '{field_name}' must be a valid email address",
                field_name,
                value
            )
        return value.lower().strip()
    
    def _validate_uuid(self, value: str, field_name: str) -> str:
        """Validate UUID format."""
        try:
            uuid.UUID(value)
            return value
        except ValueError:
            raise InputValidationError(
                f"Field '{field_name}' must be a valid UUID",
                field_name,
                value
            )
    
    def _validate_integer(self, value: Any, field_name: str) -> int:
        """Validate integer value."""
        try:
            return int(value)
        except (ValueError, TypeError):
            raise InputValidationError(
                f"Field '{field_name}' must be a valid integer",
                field_name,
                value
            )
    
    def _validate_decimal(self, value: Any, field_name: str) -> Decimal:
        """Validate decimal value."""
        try:
            return Decimal(str(value))
        except (InvalidOperation, ValueError, TypeError):
            raise InputValidationError(
                f"Field '{field_name}' must be a valid decimal number",
                field_name,
                value
            )
    
    def _validate_boolean(self, value: Any, field_name: str) -> bool:
        """Validate boolean value."""
        if isinstance(value, bool):
            return value
        
        if isinstance(value, str):
            lower_value = value.lower()
            if lower_value in ('true', '1', 'yes', 'on'):
                return True
            elif lower_value in ('false', '0', 'no', 'off'):
                return False
        
        raise InputValidationError(
            f"Field '{field_name}' must be a valid boolean value",
            field_name,
            value
        )
    
    def _validate_url(self, value: str, field_name: str) -> str:
        """Validate URL format."""
        try:
            result = urlparse(value)
            if not all([result.scheme, result.netloc]):
                raise ValueError("Invalid URL")
            
            # Only allow safe schemes
            if result.scheme not in ('http', 'https', 'ftp', 'ftps'):
                raise ValueError("Unsafe URL scheme")
            
            return value
        except ValueError:
            raise InputValidationError(
                f"Field '{field_name}' must be a valid URL",
                field_name,
                value
            )


def validate_sql_query_params(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate and sanitize SQL query parameters.
    
    Args:
        params: Dictionary of query parameters
        
    Returns:
        Sanitized parameters
        
    Raises:
        InputValidationError: If validation fails
    """
    validator = InputValidator()
    sanitized_params = {}
    
    for key, value in params.items():
        try:
            # Validate parameter name
            if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', key):
                raise InputValidationError(f"Invalid parameter name: {key}")
            
            # Validate and sanitize value
            sanitized_value = validator.validate_and_sanitize(
                value,
                key,
                data_type="string",
                max_length=1000,
                required=False
            )
            
            sanitized_params[key] = sanitized_value
            
        except InputValidationError as e:
            logger.error(f"Parameter validation failed: {e.message}")
            raise
    
    return sanitized_params


def safe_execute_query(db: Session, query: str, params: Optional[Dict[str, Any]] = None) -> Any:
    """
    Safely execute a SQL query with parameter validation.
    
    Args:
        db: Database session
        query: SQL query string
        params: Query parameters
        
    Returns:
        Query result
        
    Raises:
        InputValidationError: If validation fails
    """
    # Validate parameters if provided
    if params:
        params = validate_sql_query_params(params)
    
    # Use parameterized query to prevent SQL injection
    try:
        result = db.execute(text(query), params or {})
        return result
    except Exception as e:
        logger.error(
            "SQL query execution failed",
            query=query[:200],
            params=params,
            error=str(e)
        )
        raise


# Global validator instance
input_validator = InputValidator()
