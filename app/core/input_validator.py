"""
Comprehensive Input Validation System
Validates all inputs to prevent security vulnerabilities and data corruption.
"""
from typing import Dict, List, Optional, Any, Union, Callable
import re
import uuid
from datetime import datetime, date
from decimal import Decimal, InvalidOperation
import logging
from enum import Enum
from dataclasses import dataclass

logger = logging.getLogger(__name__)

class ValidationError(Exception):
    """Exception raised for input validation errors."""
    def __init__(self, field: str, message: str, value: Any = None):
        self.field = field
        self.message = message
        self.value = value
        super().__init__(f"Validation error for field '{field}': {message}")

class ValidatorType(Enum):
    """Types of validators available."""
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    DECIMAL = "decimal"
    BOOLEAN = "boolean"
    EMAIL = "email"
    UUID = "uuid"
    DATE = "date"
    DATETIME = "datetime"
    ENUM = "enum"
    LIST = "list"
    DICT = "dict"
    PHONE = "phone"
    URL = "url"
    COORDINATES = "coordinates"
    PERCENTAGE = "percentage"
    COMPANY_TYPE = "company_type"
    BATCH_STATUS = "batch_status"
    ORDER_STATUS = "order_status"
    CERTIFICATION_TYPE = "certification_type"
    PRODUCT_TYPE = "product_type"

@dataclass
class ValidationRule:
    """Defines a validation rule for a field."""
    field_name: str
    validator_type: ValidatorType
    required: bool = True
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    min_value: Optional[Union[int, float, Decimal]] = None
    max_value: Optional[Union[int, float, Decimal]] = None
    pattern: Optional[str] = None
    allowed_values: Optional[List[Any]] = None
    custom_validator: Optional[Callable] = None
    sanitize: bool = True
    description: str = ""

class InputValidator:
    """
    Comprehensive input validation system with security focus.
    """
    
    # Predefined validation patterns
    PATTERNS = {
        'email': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
        'phone': r'^\+?[1-9]\d{1,14}$',  # E.164 format
        'url': r'^https?://(?:[-\w.])+(?:\:[0-9]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:\#(?:[\w.])*)?)?$',
        'uuid': r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
        'batch_id': r'^[A-Z0-9]{6,20}$',
        'po_number': r'^PO[0-9]{6,15}$',
        'alphanumeric': r'^[a-zA-Z0-9_-]+$',
        'safe_string': r'^[a-zA-Z0-9\s\-_.,()]+$',
        'sql_injection': r'(;|\-\-|\/\*|\*\/|union|select|insert|update|delete|drop|create|alter)',
    }
    
    # Allowed enum values
    ALLOWED_VALUES = {
        'company_type': [
            'plantation_grower', 'mill_processor', 'refinery_crusher',
            'trader_aggregator', 'brand', 'manufacturer'
        ],
        'batch_status': ['available', 'reserved', 'allocated', 'processed'],
        'order_status': ['pending', 'confirmed', 'fulfilled', 'cancelled'],
        'delivery_status': ['pending', 'in_transit', 'delivered', 'failed'],
        'certification_type': ['RSPO', 'MSPO', 'Organic', 'Rainforest Alliance', 'Fair Trade'],
        'product_type': ['FFB', 'CPO', 'RBDPO', 'Palm Kernel', 'Olein', 'Stearin'],
        'document_category': ['certificate', 'map', 'report', 'audit'],
        'compliance_status': ['pending', 'verified', 'failed', 'exempt'],
        'notification_type': ['system', 'alert', 'reminder', 'update', 'warning', 'error'],
        'notification_priority': ['low', 'medium', 'high', 'urgent'],
        'notification_status': ['unread', 'read', 'archived', 'dismissed'],
        'delivery_channel': ['in_app', 'email', 'sms', 'webhook'],
        'user_role': ['admin', 'manager', 'operator', 'viewer'],
        'transformation_type': ['milling', 'refining', 'fractionation'],
        'transportation_type': ['truck', 'ship', 'rail', 'pipeline', 'multimodal'],
        'movement_type': ['inbound', 'outbound', 'transfer', 'adjustment']
    }
    
    def __init__(self):
        self.validation_cache = {}
    
    def validate_field(self, field_name: str, value: Any, rule: ValidationRule) -> Any:
        """
        Validate a single field according to its rule.
        
        Args:
            field_name: Name of the field being validated
            value: Value to validate
            rule: Validation rule to apply
            
        Returns:
            Validated and potentially sanitized value
            
        Raises:
            ValidationError: If validation fails
        """
        try:
            # Handle None values
            if value is None:
                if rule.required:
                    raise ValidationError(field_name, "Field is required")
                return None
            
            # Convert empty strings to None if not required
            if isinstance(value, str) and value.strip() == "":
                if rule.required:
                    raise ValidationError(field_name, "Field cannot be empty")
                return None
            
            # Apply sanitization if enabled
            if rule.sanitize and isinstance(value, str):
                value = self._sanitize_string(value)
            
            # Apply type-specific validation
            validated_value = self._validate_by_type(field_name, value, rule)
            
            # Apply custom validator if provided
            if rule.custom_validator:
                validated_value = rule.custom_validator(validated_value)
            
            return validated_value
            
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Validation error for field {field_name}: {str(e)}")
            raise ValidationError(field_name, f"Validation failed: {str(e)}", value)
    
    def validate_dict(self, data: Dict[str, Any], rules: List[ValidationRule]) -> Dict[str, Any]:
        """
        Validate a dictionary of data against a list of rules.
        
        Args:
            data: Dictionary to validate
            rules: List of validation rules
            
        Returns:
            Validated and sanitized dictionary
            
        Raises:
            ValidationError: If any validation fails
        """
        if not isinstance(data, dict):
            raise ValidationError("data", "Input must be a dictionary")
        
        validated_data = {}
        errors = []
        
        # Create rule lookup
        rule_lookup = {rule.field_name: rule for rule in rules}
        
        # Validate each field in rules
        for rule in rules:
            try:
                value = data.get(rule.field_name)
                validated_data[rule.field_name] = self.validate_field(
                    rule.field_name, value, rule
                )
            except ValidationError as e:
                errors.append(e)
        
        # Check for unknown fields
        unknown_fields = set(data.keys()) - set(rule_lookup.keys())
        if unknown_fields:
            logger.warning(f"Unknown fields ignored: {unknown_fields}")
        
        if errors:
            # Combine all error messages
            error_messages = [f"{e.field}: {e.message}" for e in errors]
            raise ValidationError("validation", "; ".join(error_messages))
        
        return validated_data
    
    def _validate_by_type(self, field_name: str, value: Any, rule: ValidationRule) -> Any:
        """Validate value by its type."""
        validator_type = rule.validator_type
        
        if validator_type == ValidatorType.STRING:
            return self._validate_string(field_name, value, rule)
        elif validator_type == ValidatorType.INTEGER:
            return self._validate_integer(field_name, value, rule)
        elif validator_type == ValidatorType.FLOAT:
            return self._validate_float(field_name, value, rule)
        elif validator_type == ValidatorType.DECIMAL:
            return self._validate_decimal(field_name, value, rule)
        elif validator_type == ValidatorType.BOOLEAN:
            return self._validate_boolean(field_name, value, rule)
        elif validator_type == ValidatorType.EMAIL:
            return self._validate_email(field_name, value, rule)
        elif validator_type == ValidatorType.UUID:
            return self._validate_uuid(field_name, value, rule)
        elif validator_type == ValidatorType.DATE:
            return self._validate_date(field_name, value, rule)
        elif validator_type == ValidatorType.DATETIME:
            return self._validate_datetime(field_name, value, rule)
        elif validator_type == ValidatorType.ENUM:
            return self._validate_enum(field_name, value, rule)
        elif validator_type == ValidatorType.LIST:
            return self._validate_list(field_name, value, rule)
        elif validator_type == ValidatorType.DICT:
            return self._validate_dict_type(field_name, value, rule)
        elif validator_type == ValidatorType.PHONE:
            return self._validate_phone(field_name, value, rule)
        elif validator_type == ValidatorType.URL:
            return self._validate_url(field_name, value, rule)
        elif validator_type == ValidatorType.COORDINATES:
            return self._validate_coordinates(field_name, value, rule)
        elif validator_type == ValidatorType.PERCENTAGE:
            return self._validate_percentage(field_name, value, rule)
        else:
            # Handle business-specific types
            return self._validate_business_type(field_name, value, rule)
    
    def _validate_string(self, field_name: str, value: Any, rule: ValidationRule) -> str:
        """Validate string value."""
        if not isinstance(value, str):
            try:
                value = str(value)
            except Exception:
                raise ValidationError(field_name, "Cannot convert to string")
        
        # Check for SQL injection patterns
        if re.search(self.PATTERNS['sql_injection'], value.lower()):
            raise ValidationError(field_name, "Contains potential SQL injection patterns")
        
        # Length validation
        if rule.min_length is not None and len(value) < rule.min_length:
            raise ValidationError(field_name, f"Minimum length is {rule.min_length}")
        
        if rule.max_length is not None and len(value) > rule.max_length:
            raise ValidationError(field_name, f"Maximum length is {rule.max_length}")
        
        # Pattern validation
        if rule.pattern and not re.match(rule.pattern, value):
            raise ValidationError(field_name, f"Does not match required pattern")
        
        return value
    
    def _validate_integer(self, field_name: str, value: Any, rule: ValidationRule) -> int:
        """Validate integer value."""
        try:
            if isinstance(value, str):
                # Remove whitespace and check for integer format
                value = value.strip()
                if not value.lstrip('-').isdigit():
                    raise ValueError("Not a valid integer")
            
            int_value = int(value)
            
            # Range validation
            if rule.min_value is not None and int_value < rule.min_value:
                raise ValidationError(field_name, f"Minimum value is {rule.min_value}")
            
            if rule.max_value is not None and int_value > rule.max_value:
                raise ValidationError(field_name, f"Maximum value is {rule.max_value}")
            
            return int_value
            
        except (ValueError, TypeError):
            raise ValidationError(field_name, "Must be a valid integer")
    
    def _validate_float(self, field_name: str, value: Any, rule: ValidationRule) -> float:
        """Validate float value."""
        try:
            float_value = float(value)
            
            # Check for infinity and NaN
            if not isinstance(float_value, (int, float)) or str(float_value).lower() in ['inf', '-inf', 'nan']:
                raise ValidationError(field_name, "Must be a finite number")
            
            # Range validation
            if rule.min_value is not None and float_value < rule.min_value:
                raise ValidationError(field_name, f"Minimum value is {rule.min_value}")
            
            if rule.max_value is not None and float_value > rule.max_value:
                raise ValidationError(field_name, f"Maximum value is {rule.max_value}")
            
            return float_value
            
        except (ValueError, TypeError):
            raise ValidationError(field_name, "Must be a valid number")
    
    def _validate_decimal(self, field_name: str, value: Any, rule: ValidationRule) -> Decimal:
        """Validate decimal value."""
        try:
            decimal_value = Decimal(str(value))
            
            # Range validation
            if rule.min_value is not None and decimal_value < Decimal(str(rule.min_value)):
                raise ValidationError(field_name, f"Minimum value is {rule.min_value}")
            
            if rule.max_value is not None and decimal_value > Decimal(str(rule.max_value)):
                raise ValidationError(field_name, f"Maximum value is {rule.max_value}")
            
            return decimal_value
            
        except (InvalidOperation, ValueError, TypeError):
            raise ValidationError(field_name, "Must be a valid decimal number")
    
    def _validate_boolean(self, field_name: str, value: Any, rule: ValidationRule) -> bool:
        """Validate boolean value."""
        if isinstance(value, bool):
            return value
        
        if isinstance(value, str):
            lower_value = value.lower().strip()
            if lower_value in ['true', '1', 'yes', 'on']:
                return True
            elif lower_value in ['false', '0', 'no', 'off']:
                return False
        
        if isinstance(value, (int, float)):
            return bool(value)
        
        raise ValidationError(field_name, "Must be a valid boolean value")
    
    def _validate_email(self, field_name: str, value: Any, rule: ValidationRule) -> str:
        """Validate email address."""
        if not isinstance(value, str):
            raise ValidationError(field_name, "Email must be a string")
        
        value = value.strip().lower()
        
        if not re.match(self.PATTERNS['email'], value):
            raise ValidationError(field_name, "Must be a valid email address")
        
        if len(value) > 254:  # RFC 5321 limit
            raise ValidationError(field_name, "Email address too long")
        
        return value
    
    def _validate_uuid(self, field_name: str, value: Any, rule: ValidationRule) -> str:
        """Validate UUID."""
        if not isinstance(value, str):
            raise ValidationError(field_name, "UUID must be a string")
        
        value = value.strip().lower()
        
        try:
            # Validate using uuid module
            uuid_obj = uuid.UUID(value)
            return str(uuid_obj)
        except ValueError:
            raise ValidationError(field_name, "Must be a valid UUID")
    
    def _validate_date(self, field_name: str, value: Any, rule: ValidationRule) -> date:
        """Validate date value."""
        if isinstance(value, date):
            return value
        
        if isinstance(value, datetime):
            return value.date()
        
        if isinstance(value, str):
            try:
                return datetime.strptime(value.strip(), '%Y-%m-%d').date()
            except ValueError:
                try:
                    return datetime.fromisoformat(value.strip()).date()
                except ValueError:
                    pass
        
        raise ValidationError(field_name, "Must be a valid date (YYYY-MM-DD)")
    
    def _validate_datetime(self, field_name: str, value: Any, rule: ValidationRule) -> datetime:
        """Validate datetime value."""
        if isinstance(value, datetime):
            return value
        
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value.strip())
            except ValueError:
                try:
                    return datetime.strptime(value.strip(), '%Y-%m-%d %H:%M:%S')
                except ValueError:
                    pass
        
        raise ValidationError(field_name, "Must be a valid datetime")
    
    def _validate_enum(self, field_name: str, value: Any, rule: ValidationRule) -> str:
        """Validate enum value."""
        if not isinstance(value, str):
            value = str(value)
        
        value = value.strip()
        
        allowed_values = rule.allowed_values
        if not allowed_values:
            raise ValidationError(field_name, "No allowed values defined for enum")
        
        if value not in allowed_values:
            raise ValidationError(field_name, f"Must be one of: {', '.join(allowed_values)}")
        
        return value
    
    def _validate_list(self, field_name: str, value: Any, rule: ValidationRule) -> List[Any]:
        """Validate list value."""
        if not isinstance(value, list):
            raise ValidationError(field_name, "Must be a list")
        
        if rule.min_length is not None and len(value) < rule.min_length:
            raise ValidationError(field_name, f"List must have at least {rule.min_length} items")
        
        if rule.max_length is not None and len(value) > rule.max_length:
            raise ValidationError(field_name, f"List must have at most {rule.max_length} items")
        
        return value
    
    def _validate_dict_type(self, field_name: str, value: Any, rule: ValidationRule) -> Dict[str, Any]:
        """Validate dictionary value."""
        if not isinstance(value, dict):
            raise ValidationError(field_name, "Must be a dictionary")
        
        return value
    
    def _validate_phone(self, field_name: str, value: Any, rule: ValidationRule) -> str:
        """Validate phone number."""
        if not isinstance(value, str):
            raise ValidationError(field_name, "Phone number must be a string")
        
        # Remove common separators
        cleaned = re.sub(r'[\s\-\(\)\.]+', '', value.strip())
        
        if not re.match(self.PATTERNS['phone'], cleaned):
            raise ValidationError(field_name, "Must be a valid phone number")
        
        return cleaned
    
    def _validate_url(self, field_name: str, value: Any, rule: ValidationRule) -> str:
        """Validate URL."""
        if not isinstance(value, str):
            raise ValidationError(field_name, "URL must be a string")
        
        value = value.strip()
        
        if not re.match(self.PATTERNS['url'], value):
            raise ValidationError(field_name, "Must be a valid URL")
        
        if len(value) > 2048:  # Reasonable URL length limit
            raise ValidationError(field_name, "URL too long")
        
        return value
    
    def _validate_coordinates(self, field_name: str, value: Any, rule: ValidationRule) -> tuple:
        """Validate GPS coordinates."""
        if isinstance(value, (list, tuple)) and len(value) == 2:
            try:
                lat, lng = float(value[0]), float(value[1])
                
                if not (-90 <= lat <= 90):
                    raise ValidationError(field_name, "Latitude must be between -90 and 90")
                
                if not (-180 <= lng <= 180):
                    raise ValidationError(field_name, "Longitude must be between -180 and 180")
                
                return (lat, lng)
            except (ValueError, TypeError):
                pass
        
        raise ValidationError(field_name, "Must be valid coordinates [latitude, longitude]")
    
    def _validate_percentage(self, field_name: str, value: Any, rule: ValidationRule) -> float:
        """Validate percentage value."""
        try:
            percent_value = float(value)
            
            if not (0 <= percent_value <= 100):
                raise ValidationError(field_name, "Percentage must be between 0 and 100")
            
            return percent_value
            
        except (ValueError, TypeError):
            raise ValidationError(field_name, "Must be a valid percentage")
    
    def _validate_business_type(self, field_name: str, value: Any, rule: ValidationRule) -> str:
        """Validate business-specific types."""
        if not isinstance(value, str):
            value = str(value)
        
        value = value.strip()
        
        # Map validator types to allowed values
        type_mapping = {
            ValidatorType.COMPANY_TYPE: 'company_type',
            ValidatorType.BATCH_STATUS: 'batch_status',
            ValidatorType.ORDER_STATUS: 'order_status',
            ValidatorType.CERTIFICATION_TYPE: 'certification_type',
            ValidatorType.PRODUCT_TYPE: 'product_type'
        }
        
        allowed_key = type_mapping.get(rule.validator_type)
        if not allowed_key:
            raise ValidationError(field_name, f"Unknown validator type: {rule.validator_type}")
        
        allowed_values = self.ALLOWED_VALUES.get(allowed_key, [])
        if value not in allowed_values:
            raise ValidationError(field_name, f"Must be one of: {', '.join(allowed_values)}")
        
        return value
    
    def _sanitize_string(self, value: str) -> str:
        """Sanitize string input."""
        if not isinstance(value, str):
            return value
        
        # Remove null bytes
        value = value.replace('\x00', '')
        
        # Normalize whitespace
        value = re.sub(r'\s+', ' ', value.strip())
        
        # Remove control characters except common ones
        value = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', value)
        
        return value

# Predefined validation rule sets for common use cases

CERTIFICATION_VALIDATION_RULES = [
    ValidationRule('company_id', ValidatorType.UUID, required=False),
    ValidationRule('certification_type', ValidatorType.CERTIFICATION_TYPE, required=False),
    ValidationRule('expires_within_days', ValidatorType.INTEGER, required=False, min_value=0, max_value=3650),
    ValidationRule('compliance_status', ValidatorType.ENUM, required=False, 
                  allowed_values=['pending', 'verified', 'failed', 'exempt']),
    ValidationRule('location_id', ValidatorType.UUID, required=False),
]

BATCH_SEARCH_VALIDATION_RULES = [
    ValidationRule('product_name', ValidatorType.STRING, required=False, max_length=255),
    ValidationRule('product_type', ValidatorType.PRODUCT_TYPE, required=False),
    ValidationRule('status', ValidatorType.BATCH_STATUS, required=False),
    ValidationRule('company_id', ValidatorType.UUID, required=False),
    ValidationRule('min_quantity', ValidatorType.FLOAT, required=False, min_value=0),
    ValidationRule('min_transparency_score', ValidatorType.PERCENTAGE, required=False),
    ValidationRule('certification_required', ValidatorType.CERTIFICATION_TYPE, required=False),
    ValidationRule('limit', ValidatorType.INTEGER, required=False, min_value=1, max_value=1000),
]

PURCHASE_ORDER_VALIDATION_RULES = [
    ValidationRule('company_id', ValidatorType.UUID, required=False),
    ValidationRule('role_filter', ValidatorType.ENUM, required=False, 
                  allowed_values=['buyer', 'seller']),
    ValidationRule('status', ValidatorType.ORDER_STATUS, required=False),
    ValidationRule('product_type', ValidatorType.PRODUCT_TYPE, required=False),
    ValidationRule('min_value', ValidatorType.FLOAT, required=False, min_value=0),
    ValidationRule('limit', ValidatorType.INTEGER, required=False, min_value=1, max_value=1000),
]

FARM_LOCATION_VALIDATION_RULES = [
    ValidationRule('company_id', ValidatorType.UUID, required=False),
    ValidationRule('certification_type', ValidatorType.CERTIFICATION_TYPE, required=False),
    ValidationRule('compliance_status', ValidatorType.ENUM, required=False,
                  allowed_values=['pending', 'verified', 'failed', 'exempt']),
    ValidationRule('eudr_compliant_only', ValidatorType.BOOLEAN, required=False),
    ValidationRule('min_farm_size', ValidatorType.FLOAT, required=False, min_value=0),
]

COMPANY_INFO_VALIDATION_RULES = [
    ValidationRule('company_id', ValidatorType.UUID, required=False),
    ValidationRule('company_type', ValidatorType.COMPANY_TYPE, required=False),
    ValidationRule('min_transparency_score', ValidatorType.PERCENTAGE, required=False),
    ValidationRule('include_statistics', ValidatorType.BOOLEAN, required=False),
    ValidationRule('include_contact_info', ValidatorType.BOOLEAN, required=False),
]

# Convenience functions

def create_validator() -> InputValidator:
    """Create a new input validator instance."""
    return InputValidator()

def validate_certification_params(params: Dict[str, Any]) -> Dict[str, Any]:
    """Validate certification function parameters."""
    validator = InputValidator()
    return validator.validate_dict(params, CERTIFICATION_VALIDATION_RULES)

def validate_batch_search_params(params: Dict[str, Any]) -> Dict[str, Any]:
    """Validate batch search parameters."""
    validator = InputValidator()
    return validator.validate_dict(params, BATCH_SEARCH_VALIDATION_RULES)

def validate_purchase_order_params(params: Dict[str, Any]) -> Dict[str, Any]:
    """Validate purchase order parameters."""
    validator = InputValidator()
    return validator.validate_dict(params, PURCHASE_ORDER_VALIDATION_RULES)

def validate_farm_location_params(params: Dict[str, Any]) -> Dict[str, Any]:
    """Validate farm location parameters."""
    validator = InputValidator()
    return validator.validate_dict(params, FARM_LOCATION_VALIDATION_RULES)

def validate_company_info_params(params: Dict[str, Any]) -> Dict[str, Any]:
    """Validate company info parameters."""
    validator = InputValidator()
    return validator.validate_dict(params, COMPANY_INFO_VALIDATION_RULES)
