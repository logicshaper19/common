"""
Configuration for Unified PO Model implementation.

This module centralizes all configuration values that were previously hardcoded
throughout the Unified PO Model implementation.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from app.models.transformation import TransformationType


@dataclass
class UnifiedPOConfig:
    """Configuration for Unified PO Model implementation."""
    
    # Processor types that should trigger transformations
    PROCESSOR_TYPES: List[str] = field(default_factory=lambda: [
        'mill', 'refinery', 'manufacturer', 'processor'
    ])
    
    # Company type to transformation type mapping
    TRANSFORMATION_TYPE_MAPPING: Dict[str, TransformationType] = field(default_factory=lambda: {
        'mill': TransformationType.MILLING,
        'refinery': TransformationType.REFINING,
        'manufacturer': TransformationType.MANUFACTURING,
        'processor': TransformationType.BLENDING
    })
    
    # ID generation patterns
    BATCH_ID_PATTERN: str = "PO-{po_id_short}-BATCH-{timestamp}"
    EVENT_ID_PATTERN: str = "{transformation_type}-{date}-{po_id_short}"
    FACILITY_ID_PATTERN: str = "{company_type}-001"
    
    # Timestamp formats
    TIMESTAMP_FORMAT: str = "%Y%m%d_%H%M%S"
    DATE_FORMAT: str = "%Y%m%d"
    
    # Default values
    DEFAULT_BATCH_TYPE: str = "PROCESSING"
    DEFAULT_UNIT: str = "kg"
    DEFAULT_DELIVERY_DAYS: int = 30
    DEFAULT_DELIVERY_LOCATION: str = "Port of Singapore"
    
    # UUID truncation
    UUID_SHORT_LENGTH: int = 8
    
    # Product category mapping
    PRODUCT_CATEGORY_MAPPING: Dict[str, str] = field(default_factory=lambda: {
        "raw_material": "raw_material",
        "crude_oil": "raw_material", 
        "refined_oil": "raw_material",
        "finished_goods": "finished_good"
    })
    
    # Batch metadata keys
    BATCH_METADATA_KEYS: Dict[str, str] = field(default_factory=lambda: {
        "purchase_order_id": "purchase_order_id",
        "seller_company_id": "seller_company_id",
        "buyer_company_id": "buyer_company_id",
        "created_from_po_confirmation": "created_from_po_confirmation"
    })
    
    # Relationship types
    RELATIONSHIP_TYPES: Dict[str, str] = field(default_factory=lambda: {
        "SALE": "sale",
        "TRANSFORMATION": "transformation",
        "SPLIT": "split",
        "MERGE": "merge"
    })
    
    # Default relationship type for PO-based batch creation
    DEFAULT_RELATIONSHIP_TYPE: str = "sale"
    
    # Error messages
    ERROR_MESSAGES: Dict[str, str] = field(default_factory=lambda: {
        "PO_NOT_FOUND": "Purchase order not found",
        "PO_NOT_CONFIRMED": "Purchase order is not confirmed",
        "COMPANY_NOT_FOUND": "Company not found",
        "PRODUCT_NOT_FOUND": "Product not found",
        "BATCH_CREATION_FAILED": "Failed to create batch from PO confirmation",
        "TRANSFORMATION_SUGGESTION_FAILED": "Failed to create transformation suggestion",
        "BATCH_RELATIONSHIP_FAILED": "Failed to create batch relationship",
        "TRACEABILITY_CHAIN_FAILED": "Failed to get traceability chain"
    })
    
    # Logging context keys
    LOG_CONTEXT_KEYS: Dict[str, str] = field(default_factory=lambda: {
        "BATCH_ID": "batch_id",
        "PO_ID": "po_id",
        "COMPANY_ID": "company_id",
        "USER_ID": "user_id",
        "TRANSFORMATION_TYPE": "transformation_type",
        "RELATIONSHIP_TYPE": "relationship_type"
    })


# Global config instance
config = UnifiedPOConfig()


def get_config() -> UnifiedPOConfig:
    """Get the Unified PO Model configuration."""
    return config


def format_batch_id(po_id: str, timestamp: str) -> str:
    """Format batch ID using configured pattern."""
    po_id_short = po_id[:config.UUID_SHORT_LENGTH]
    return config.BATCH_ID_PATTERN.format(
        po_id_short=po_id_short,
        timestamp=timestamp
    )


def format_event_id(transformation_type: str, date: str, po_id: str) -> str:
    """Format event ID using configured pattern."""
    po_id_short = po_id[:config.UUID_SHORT_LENGTH]
    return config.EVENT_ID_PATTERN.format(
        transformation_type=transformation_type,
        date=date,
        po_id_short=po_id_short
    )


def format_facility_id(company_type: str) -> str:
    """Format facility ID using configured pattern."""
    return config.FACILITY_ID_PATTERN.format(
        company_type=company_type.upper()
    )


def get_transformation_type(company_type: str) -> Optional[TransformationType]:
    """Get transformation type for company type."""
    return config.TRANSFORMATION_TYPE_MAPPING.get(company_type)


def is_processor_type(company_type: str) -> bool:
    """Check if company type is a processor."""
    return company_type in config.PROCESSOR_TYPES


def get_product_category(category: str) -> str:
    """Get mapped product category."""
    return config.PRODUCT_CATEGORY_MAPPING.get(category, "raw_material")
