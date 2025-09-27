"""
Inventory-level transformation models for realistic supply chain operations.
Implements proportional provenance tracking and inventory pooling.
"""
from sqlalchemy import Column, String, DateTime, ForeignKey, func, Numeric, Index, Enum as SQLEnum, Text, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid
from enum import Enum
from datetime import datetime

from app.core.database import Base


class TransformationMode(str, Enum):
    """Transformation operation modes."""
    BATCH_LEVEL = "BATCH_LEVEL"  # Precise batch tracking (existing)
    INVENTORY_LEVEL = "INVENTORY_LEVEL"  # Inventory pooling with proportional provenance


class AllocationMethod(str, Enum):
    """Methods for allocating from inventory pool."""
    PROPORTIONAL = "PROPORTIONAL"  # Default: proportional allocation
    FIFO = "FIFO"  # First-In-First-Out
    LIFO = "LIFO"  # Last-In-First-Out
    QUALITY_BASED = "QUALITY_BASED"  # Based on quality metrics
    ENTIRE_BATCHES_FIRST = "ENTIRE_BATCHES_FIRST"  # Use complete batches first
    MANUAL = "MANUAL"  # Manual override


class TransformationProvenance(Base):
    """Tracks proportional provenance from source batches in inventory-level transformations."""
    
    __tablename__ = "transformation_provenance"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    transformation_event_id = Column(UUID(as_uuid=True), ForeignKey("transformation_events.id"), nullable=False)
    source_batch_id = Column(UUID(as_uuid=True), ForeignKey("batches.id"), nullable=False)
    
    # Allocation details
    contribution_ratio = Column(Numeric(5, 4), nullable=False)  # 0.5 = 50%
    contribution_quantity = Column(Numeric(12, 4), nullable=False)  # Actual quantity used
    contribution_unit = Column(String(20), nullable=False)
    
    # Inherited provenance data (merged from source batch)
    inherited_origin_data = Column(JSONB)  # Merged origin data from source batch
    inherited_certifications = Column(JSONB)  # Combined certifications
    inherited_quality_metrics = Column(JSONB)  # Quality metrics from source
    
    # Allocation context
    allocation_method = Column(SQLEnum(AllocationMethod), nullable=False)
    allocation_priority = Column(Numeric(3, 0))  # Order of allocation (1, 2, 3...)
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Relationships
    transformation_event = relationship("TransformationEvent")
    source_batch = relationship("Batch")
    created_by_user = relationship("User")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_transformation_provenance_event', 'transformation_event_id'),
        Index('idx_transformation_provenance_batch', 'source_batch_id'),
        Index('idx_transformation_provenance_method', 'allocation_method'),
    )


class InventoryPool(Base):
    """Represents available inventory pools for transformations."""
    
    __tablename__ = "inventory_pools"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    
    # Pool summary
    total_available_quantity = Column(Numeric(12, 4), nullable=False, default=0)
    unit = Column(String(20), nullable=False)
    batch_count = Column(Numeric(5, 0), nullable=False, default=0)
    
    # Pool composition (which batches contribute and how much)
    pool_composition = Column(JSONB, nullable=False, default=list)  # [{"batch_id": "uuid", "quantity": 500, "percentage": 0.5, "batch_number": "H-2024-001"}]
    
    # Pool metadata
    last_calculated_at = Column(DateTime(timezone=True), server_default=func.now())
    calculation_method = Column(String(50), default='AUTOMATIC')  # 'AUTOMATIC', 'MANUAL', 'SCHEDULED'
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Relationships
    company = relationship("Company")
    product = relationship("Product")
    created_by_user = relationship("User")
    
    # Indexes and constraints for performance and data integrity
    __table_args__ = (
        Index('idx_inventory_pool_company_product', 'company_id', 'product_id'),
        Index('idx_inventory_pool_updated', 'updated_at'),
        # Unique constraint: one pool per company-product combination
        Index('idx_inventory_pool_unique', 'company_id', 'product_id', unique=True),
    )


class InventoryAllocation(Base):
    """Tracks inventory allocations for transformations."""
    
    __tablename__ = "inventory_allocations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    transformation_event_id = Column(UUID(as_uuid=True), ForeignKey("transformation_events.id"), nullable=False)
    inventory_pool_id = Column(UUID(as_uuid=True), ForeignKey("inventory_pools.id"), nullable=False)
    
    # Allocation details
    requested_quantity = Column(Numeric(12, 4), nullable=False)
    allocated_quantity = Column(Numeric(12, 4), nullable=False)
    unit = Column(String(20), nullable=False)
    allocation_method = Column(SQLEnum(AllocationMethod), nullable=False)
    
    # Allocation results
    allocation_details = Column(JSONB, nullable=False)  # Detailed breakdown of which batches were used
    allocation_timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    # Status tracking
    status = Column(String(20), nullable=False, default='ACTIVE')  # 'ACTIVE', 'RELEASED', 'CANCELLED'
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Relationships
    transformation_event = relationship("TransformationEvent")
    inventory_pool = relationship("InventoryPool")
    created_by_user = relationship("User")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_inventory_allocation_transformation', 'transformation_event_id'),
        Index('idx_inventory_allocation_pool', 'inventory_pool_id'),
        Index('idx_inventory_allocation_status', 'status'),
    )


class MassBalanceValidation(Base):
    """Tracks mass balance validation for transformations."""
    
    __tablename__ = "mass_balance_validations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    transformation_event_id = Column(UUID(as_uuid=True), ForeignKey("transformation_events.id"), nullable=False)
    
    # Input/Output quantities
    total_input_quantity = Column(Numeric(12, 4), nullable=False)
    total_output_quantity = Column(Numeric(12, 4), nullable=False)
    expected_output_quantity = Column(Numeric(12, 4), nullable=False)
    waste_quantity = Column(Numeric(12, 4), nullable=False)
    
    # Validation results
    balance_ratio = Column(Numeric(8, 4), nullable=False)  # actual_output / expected_output
    tolerance_threshold = Column(Numeric(5, 4), nullable=False, default=0.05)  # 5% default
    is_balanced = Column(Boolean, nullable=False)
    validation_notes = Column(Text)
    
    # Validation context
    validation_method = Column(String(50), default='AUTOMATIC')  # 'AUTOMATIC', 'MANUAL', 'OVERRIDE'
    validated_at = Column(DateTime(timezone=True), server_default=func.now())
    validated_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Relationships
    transformation_event = relationship("TransformationEvent")
    validated_by_user = relationship("User")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_mass_balance_transformation', 'transformation_event_id'),
        Index('idx_mass_balance_validated', 'validated_at'),
    )
