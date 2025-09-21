"""
Validation utilities for compliance services.
"""
import html
import re
from typing import Any, Dict, List, Optional, Union
from decimal import Decimal
from uuid import UUID

from app.services.compliance.exceptions import ValidationError
from app.services.compliance.config import get_compliance_config


class DataValidator:
    """Data validation utilities for compliance services."""
    
    def __init__(self):
        self.config = get_compliance_config()
    
    def validate_risk_score(self, score: Union[Decimal, float, str]) -> Decimal:
        """Validate risk score is within valid range."""
        try:
            risk_score = Decimal(str(score))
            if not (0.0 <= risk_score <= 1.0):
                raise ValidationError(
                    f"Risk score must be between 0.0 and 1.0, got {risk_score}",
                    field="risk_score"
                )
            return risk_score
        except (ValueError, TypeError) as e:
            raise ValidationError(
                f"Invalid risk score format: {score}",
                field="risk_score"
            ) from e
    
    def validate_yield_percentage(self, yield_pct: Union[Decimal, float, str]) -> Decimal:
        """Validate yield percentage is within valid range."""
        try:
            yield_percentage = Decimal(str(yield_pct))
            config = self.config.get_mass_balance_config()
            
            if not (config.min_yield_percentage <= yield_percentage <= config.max_yield_percentage):
                raise ValidationError(
                    f"Yield percentage must be between {config.min_yield_percentage} and {config.max_yield_percentage}, got {yield_percentage}",
                    field="yield_percentage"
                )
            return yield_percentage
        except (ValueError, TypeError) as e:
            raise ValidationError(
                f"Invalid yield percentage format: {yield_pct}",
                field="yield_percentage"
            ) from e
    
    def validate_waste_percentage(self, waste_pct: Union[Decimal, float, str]) -> Decimal:
        """Validate waste percentage is within valid range."""
        try:
            waste_percentage = Decimal(str(waste_pct))
            config = self.config.get_mass_balance_config()
            
            if not (config.min_waste_percentage <= waste_percentage <= config.max_waste_percentage):
                raise ValidationError(
                    f"Waste percentage must be between {config.min_waste_percentage} and {config.max_waste_percentage}, got {waste_percentage}",
                    field="waste_percentage"
                )
            return waste_percentage
        except (ValueError, TypeError) as e:
            raise ValidationError(
                f"Invalid waste percentage format: {waste_pct}",
                field="waste_percentage"
            ) from e
    
    def validate_yield_waste_sum(self, yield_pct: Decimal, waste_pct: Decimal) -> None:
        """Validate that yield and waste percentages don't exceed 100%."""
        config = self.config.get_mass_balance_config()
        total = yield_pct + waste_pct
        
        if total > config.max_yield_waste_sum:
            raise ValidationError(
                f"Sum of yield ({yield_pct}%) and waste ({waste_pct}%) percentages ({total}%) exceeds maximum allowed ({config.max_yield_waste_sum}%)",
                field="yield_waste_sum"
            )
    
    def validate_hs_code(self, hs_code: str) -> str:
        """Validate HS code format."""
        if not hs_code:
            raise ValidationError("HS code cannot be empty", field="hs_code")
        
        # Basic HS code format validation (4-6 digits with optional dots and 2-4 digits)
        if not re.match(r'^\d{4,6}(\.\d{2,4})*$', hs_code):
            raise ValidationError(
                f"Invalid HS code format: {hs_code}. Expected format: 1234.56.78 or 123456",
                field="hs_code"
            )
        
        return hs_code
    
    def validate_uuid(self, value: Any, field_name: str) -> UUID:
        """Validate UUID format."""
        if isinstance(value, UUID):
            return value
        
        try:
            return UUID(str(value))
        except (ValueError, TypeError) as e:
            raise ValidationError(
                f"Invalid UUID format for {field_name}: {value}",
                field=field_name
            ) from e
    
    def validate_supply_chain_depth(self, depth: int) -> int:
        """Validate supply chain depth is within limits."""
        config = self.config
        if depth < 0:
            raise ValidationError(
                f"Supply chain depth cannot be negative: {depth}",
                field="supply_chain_depth"
            )
        
        if depth > config.max_supply_chain_depth:
            raise ValidationError(
                f"Supply chain depth ({depth}) exceeds maximum allowed ({config.max_supply_chain_depth})",
                field="supply_chain_depth"
            )
        
        return depth
    
    def validate_quantity(self, quantity: Union[Decimal, float, str], field_name: str) -> Decimal:
        """Validate quantity is positive."""
        try:
            qty = Decimal(str(quantity))
            if qty <= 0:
                raise ValidationError(
                    f"{field_name} must be positive, got {qty}",
                    field=field_name
                )
            return qty
        except (ValueError, TypeError) as e:
            raise ValidationError(
                f"Invalid quantity format for {field_name}: {quantity}",
                field=field_name
            ) from e


class TemplateDataSanitizer:
    """Sanitize data before template rendering."""
    
    def __init__(self):
        self.config = get_compliance_config()
    
    def sanitize_string(self, value: str) -> str:
        """Sanitize string value for template rendering."""
        if not isinstance(value, str):
            return str(value)
        
        if self.config.sanitize_template_data:
            # HTML escape for security
            return html.escape(value)
        
        return value
    
    def sanitize_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize dictionary data for template rendering."""
        sanitized = {}
        
        for key, value in data.items():
            if isinstance(value, str):
                sanitized[key] = self.sanitize_string(value)
            elif isinstance(value, dict):
                sanitized[key] = self.sanitize_dict(value)
            elif isinstance(value, list):
                sanitized[key] = self.sanitize_list(value)
            else:
                sanitized[key] = value
        
        return sanitized
    
    def sanitize_list(self, data: List[Any]) -> List[Any]:
        """Sanitize list data for template rendering."""
        sanitized = []
        
        for item in data:
            if isinstance(item, str):
                sanitized.append(self.sanitize_string(item))
            elif isinstance(item, dict):
                sanitized.append(self.sanitize_dict(item))
            elif isinstance(item, list):
                sanitized.append(self.sanitize_list(item))
            else:
                sanitized.append(item)
        
        return sanitized
    
    def sanitize_template_data(self, data: Any) -> Any:
        """Sanitize any data structure for template rendering."""
        if isinstance(data, str):
            return self.sanitize_string(data)
        elif isinstance(data, dict):
            return self.sanitize_dict(data)
        elif isinstance(data, list):
            return self.sanitize_list(data)
        else:
            return data


# Global instances
data_validator = DataValidator()
template_sanitizer = TemplateDataSanitizer()


def get_data_validator() -> DataValidator:
    """Get the global data validator."""
    return data_validator


def get_template_sanitizer() -> TemplateDataSanitizer:
    """Get the global template sanitizer."""
    return template_sanitizer
