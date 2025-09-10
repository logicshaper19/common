"""
Service Documentation Template

This module provides a standardized template for documenting service classes
and methods across the application. It ensures consistency in documentation
and helps maintain high code quality standards.

Usage:
    Copy the appropriate docstring template and customize it for your service.
"""

# Class Documentation Template
CLASS_DOCSTRING_TEMPLATE = '''
"""
{service_name} Service Module

This module provides comprehensive {service_description} functionality including:
{functionality_list}

The {service_name} class handles all business logic related to {business_domain},
ensuring data consistency and proper error handling throughout the system.

Key Features:
- {feature_1}
- {feature_2}
- {feature_3}

Dependencies:
- {dependency_1}
- {dependency_2}

Author: {author}
Version: {version}
Last Updated: {last_updated}
"""
'''

# Method Documentation Template
METHOD_DOCSTRING_TEMPLATE = '''
"""
{method_description}

{detailed_explanation}

Args:
    {param_name} ({param_type}): {param_description}
    {param_name2} ({param_type2}, optional): {param_description2}. Defaults to {default_value}.

Returns:
    {return_type}: {return_description}

Raises:
    {exception_type}: {exception_description}
    {exception_type2}: {exception_description2}

Example:
    >>> service = {service_name}({constructor_args})
    >>> result = service.{method_name}({example_args})
    >>> print(result.{example_property})

Note:
    {additional_notes}
"""
'''

# Property Documentation Template
PROPERTY_DOCSTRING_TEMPLATE = '''
"""
{property_description}

{detailed_explanation}

Returns:
    {return_type}: {return_description}

Example:
    >>> service = {service_name}({constructor_args})
    >>> value = service.{property_name}
    >>> print(value)

Note:
    {additional_notes}
"""
'''

# Constructor Documentation Template
CONSTRUCTOR_DOCSTRING_TEMPLATE = '''
"""
Initialize the {service_name} with required dependencies.

Args:
    {param_name} ({param_type}): {param_description}
    {param_name2} ({param_type2}, optional): {param_description2}. Defaults to {default_value}.

Raises:
    ValueError: If {validation_condition}
    TypeError: If {type_validation_condition}

Example:
    >>> service = {service_name}({example_args})
    >>> print(service.{example_property})
"""
'''

# Service Interface Documentation Template
INTERFACE_DOCSTRING_TEMPLATE = '''
"""
{interface_name} Protocol

This protocol defines the interface for {service_description} services.
It ensures consistent behavior across different implementations and
enables proper dependency injection and testing.

Methods:
    {method_name}: {method_description}
    {method_name2}: {method_description2}

Example:
    >>> def my_function(service: {interface_name}):
    ...     result = service.{method_name}()
    ...     return result
"""
'''

# Error Handling Documentation Template
ERROR_HANDLING_TEMPLATE = '''
"""
Error Handling Strategy

This service uses the standardized error handling system with the following
error codes and behaviors:

Business Logic Errors:
- {error_code_1}: {error_description_1}
- {error_code_2}: {error_description_2}

Validation Errors:
- {validation_error_1}: {validation_description_1}
- {validation_error_2}: {validation_description_2}

Database Errors:
- {db_error_1}: {db_description_1}
- {db_error_2}: {db_description_2}

Example Error Handling:
    >>> try:
    ...     result = service.{method_name}()
    ... except {exception_type} as e:
    ...     logger.error(f"Error in {method_name}: {{e}}")
    ...     raise
"""
'''

# Performance Documentation Template
PERFORMANCE_TEMPLATE = '''
"""
Performance Considerations

This service is optimized for the following performance characteristics:

Query Optimization:
- {optimization_1}
- {optimization_2}

Caching Strategy:
- {caching_strategy_1}
- {caching_strategy_2}

Memory Usage:
- {memory_consideration_1}
- {memory_consideration_2}

Scalability:
- {scalability_note_1}
- {scalability_note_2}

Example Performance Monitoring:
    >>> import time
    >>> start_time = time.time()
    >>> result = service.{method_name}()
    >>> execution_time = time.time() - start_time
    >>> logger.info(f"{method_name} executed in {{execution_time:.2f}}s")
"""
'''

# Testing Documentation Template
TESTING_TEMPLATE = '''
"""
Testing Strategy

This service includes comprehensive test coverage with the following test types:

Unit Tests:
- {unit_test_1}
- {unit_test_2}

Integration Tests:
- {integration_test_1}
- {integration_test_2}

Mocking Strategy:
- {mocking_strategy_1}
- {mocking_strategy_2}

Example Test:
    >>> def test_{method_name}():
    ...     # Arrange
    ...     service = {service_name}(mock_db)
    ...     
    ...     # Act
    ...     result = service.{method_name}()
    ...     
    ...     # Assert
    ...     assert result is not None
    ...     assert result.{property} == expected_value
"""
'''

# Security Documentation Template
SECURITY_TEMPLATE = '''
"""
Security Considerations

This service implements the following security measures:

Authentication:
- {auth_measure_1}
- {auth_measure_2}

Authorization:
- {authorization_measure_1}
- {authorization_measure_2}

Data Validation:
- {validation_measure_1}
- {validation_measure_2}

Input Sanitization:
- {sanitization_measure_1}
- {sanitization_measure_2}

Example Security Check:
    >>> def secure_{method_name}(user_id: str, data: dict):
    ...     # Verify user permissions
    ...     if not has_permission(user_id, "write"):
    ...         raise InsufficientPermissionsError()
    ...     
    ...     # Validate and sanitize input
    ...     validated_data = validate_input(data)
    ...     return service.{method_name}(validated_data)
"""
'''

# Configuration Documentation Template
CONFIGURATION_TEMPLATE = '''
"""
Configuration Management

This service uses the following configuration parameters:

Environment Variables:
- {env_var_1}: {env_var_description_1}
- {env_var_2}: {env_var_description_2}

Configuration Files:
- {config_file_1}: {config_file_description_1}
- {config_file_2}: {config_file_description_2}

Default Values:
- {default_1}: {default_description_1}
- {default_2}: {default_description_2}

Example Configuration:
    >>> from app.core.config import settings
    >>> service = {service_name}(
    ...     db=db_session,
    ...     config=settings.{config_section}
    ... )
"""
'''

# Logging Documentation Template
LOGGING_TEMPLATE = '''
"""
Logging Strategy

This service implements comprehensive logging with the following levels:

Info Level:
- {info_log_1}
- {info_log_2}

Warning Level:
- {warning_log_1}
- {warning_log_2}

Error Level:
- {error_log_1}
- {error_log_2}

Debug Level:
- {debug_log_1}
- {debug_log_2}

Example Logging:
    >>> logger.info(f"Starting {method_name} for user {{user_id}}")
    >>> try:
    ...     result = service.{method_name}()
    ...     logger.info(f"{method_name} completed successfully")
    ... except Exception as e:
    ...     logger.error(f"Error in {method_name}: {{e}}")
    ...     raise
"""
'''

# Migration Documentation Template
MIGRATION_TEMPLATE = '''
"""
Database Migration Support

This service supports the following database migrations:

Schema Changes:
- {schema_change_1}
- {schema_change_2}

Data Migrations:
- {data_migration_1}
- {data_migration_2}

Backward Compatibility:
- {compatibility_note_1}
- {compatibility_note_2}

Example Migration:
    >>> def migrate_{service_name}_data():
    ...     # Migration logic here
    ...     pass
"""
'''

# API Documentation Template
API_DOCSTRING_TEMPLATE = '''
"""
{endpoint_name} Endpoint

{endpoint_description}

HTTP Method: {http_method}
Path: {path}
Authentication: {authentication_required}

Request Parameters:
    {param_name} ({param_type}): {param_description}
    {param_name2} ({param_type2}, optional): {param_description2}

Request Body:
    {body_description}

Response:
    {response_description}

Status Codes:
    {status_code_1}: {status_description_1}
    {status_code_2}: {status_description_2}

Example Request:
    {example_request}

Example Response:
    {example_response}

Raises:
    {exception_type}: {exception_description}
"""
'''

def generate_docstring(template: str, **kwargs) -> str:
    """
    Generate a docstring from a template with provided values.
    
    Args:
        template (str): The docstring template to use
        **kwargs: Key-value pairs to substitute in the template
        
    Returns:
        str: The generated docstring
        
    Example:
        >>> docstring = generate_docstring(
        ...     CLASS_DOCSTRING_TEMPLATE,
        ...     service_name="UserService",
        ...     service_description="user management",
        ...     functionality_list="- User creation and authentication\n- Profile management\n- Permission handling"
        ... )
    """
    return template.format(**kwargs)
