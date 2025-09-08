"""
Domain models and value objects for confirmation service.
"""
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime, date
from decimal import Decimal
from dataclasses import dataclass, field as dataclass_field

from .enums import (
    ConfirmationInterfaceType,
    ValidationSeverity,
    ComplianceStatus,
    DocumentStatus
)


@dataclass
class ConfirmationContext:
    """Context information for confirmation processing."""
    purchase_order_id: UUID
    current_user_company_id: UUID
    seller_company_type: str
    product_category: str
    product_can_have_composition: bool
    interface_type: Optional[ConfirmationInterfaceType] = None
    
    def __post_init__(self):
        """Determine interface type based on business rules."""
        if not self.interface_type:
            self.interface_type = self._determine_interface_type()
    
    def _determine_interface_type(self) -> ConfirmationInterfaceType:
        """
        Determine interface type based on business rules.
        
        Business Logic:
        1. If seller is 'originator' OR product is 'raw_material' → Origin Data Interface
        2. If seller is 'processor' OR product can_have_composition → Transformation Interface  
        3. Otherwise → Simple Confirmation Interface
        """
        if self.seller_company_type == 'originator' or self.product_category == 'raw_material':
            return ConfirmationInterfaceType.ORIGIN_DATA_INTERFACE
        elif self.seller_company_type == 'processor' or self.product_can_have_composition:
            return ConfirmationInterfaceType.TRANSFORMATION_INTERFACE
        else:
            return ConfirmationInterfaceType.SIMPLE_CONFIRMATION_INTERFACE


@dataclass
class ValidationResult:
    """Result of a validation operation."""
    is_valid: bool
    severity: ValidationSeverity
    message: str
    field: Optional[str] = None
    code: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    suggestions: List[str] = dataclass_field(default_factory=list)
    
    @classmethod
    def error(cls, message: str, field: str = None, code: str = None, **kwargs) -> 'ValidationResult':
        """Create an error validation result."""
        return cls(
            is_valid=False,
            severity=ValidationSeverity.ERROR,
            message=message,
            field=field,
            code=code,
            **kwargs
        )
    
    @classmethod
    def warning(cls, message: str, field: str = None, **kwargs) -> 'ValidationResult':
        """Create a warning validation result."""
        return cls(
            is_valid=True,
            severity=ValidationSeverity.WARNING,
            message=message,
            field=field,
            **kwargs
        )
    
    @classmethod
    def success(cls, message: str, **kwargs) -> 'ValidationResult':
        """Create a success validation result."""
        return cls(
            is_valid=True,
            severity=ValidationSeverity.SUCCESS,
            message=message,
            **kwargs
        )


@dataclass
class InterfaceConfig:
    """Configuration for a confirmation interface."""
    required_fields: List[str]
    optional_fields: List[str]
    validation_rules: Dict[str, Any]
    ui_config: Dict[str, Any]
    
    def get_all_fields(self) -> List[str]:
        """Get all fields (required + optional)."""
        return self.required_fields + self.optional_fields
    
    def is_field_required(self, field_name: str) -> bool:
        """Check if a field is required."""
        return field_name in self.required_fields


@dataclass
class DocumentRequirement:
    """Document requirement for confirmation."""
    name: str
    description: str
    status: DocumentStatus
    file_types: List[str]
    max_size_mb: Optional[int] = None
    is_required: bool = True
    uploaded_at: Optional[datetime] = None
    file_url: Optional[str] = None
    validation_errors: List[str] = dataclass_field(default_factory=list)


@dataclass
class GeographicCoordinates:
    """Geographic coordinates value object."""
    latitude: float
    longitude: float
    accuracy_meters: Optional[float] = None
    elevation_meters: Optional[float] = None
    
    def __post_init__(self):
        """Validate coordinates on creation."""
        if not (-90 <= self.latitude <= 90):
            raise ValueError(f"Latitude must be between -90 and 90, got {self.latitude}")
        if not (-180 <= self.longitude <= 180):
            raise ValueError(f"Longitude must be between -180 and 180, got {self.longitude}")
        if self.accuracy_meters is not None and self.accuracy_meters < 0:
            raise ValueError(f"Accuracy must be non-negative, got {self.accuracy_meters}")
    
    def is_precise(self, threshold_meters: float = 10.0) -> bool:
        """Check if coordinates are precise enough."""
        return self.accuracy_meters is not None and self.accuracy_meters <= threshold_meters


@dataclass
class InputMaterial:
    """Input material for transformation interface."""
    source_po_id: UUID
    quantity_used: Decimal
    percentage_contribution: float
    material_type: str
    source_po_number: Optional[str] = None
    available_quantity: Optional[Decimal] = None
    
    def __post_init__(self):
        """Validate input material on creation."""
        if self.quantity_used <= 0:
            raise ValueError("Quantity used must be positive")
        if not (0 <= self.percentage_contribution <= 100):
            raise ValueError("Percentage contribution must be between 0 and 100")


@dataclass
class OriginData:
    """Origin data for origin data interface."""
    geographic_coordinates: GeographicCoordinates
    certifications: List[str]
    harvest_date: Optional[date] = None
    farm_identification: Optional[str] = None
    batch_number: Optional[str] = None
    quality_parameters: Optional[Dict[str, Any]] = None
    additional_data: Optional[Dict[str, Any]] = None


@dataclass
class TransformationData:
    """Transformation data for transformation interface."""
    input_materials: List[InputMaterial]
    transformation_process: str
    facility_location: Optional[str] = None
    processing_date: Optional[date] = None
    yield_percentage: Optional[float] = None
    quality_parameters: Optional[Dict[str, Any]] = None
    
    def get_total_percentage(self) -> float:
        """Get total percentage contribution from all input materials."""
        return sum(material.percentage_contribution for material in self.input_materials)
    
    def is_percentage_valid(self, tolerance: float = 0.01) -> bool:
        """Check if total percentage is approximately 100%."""
        total = self.get_total_percentage()
        return abs(total - 100.0) <= tolerance
