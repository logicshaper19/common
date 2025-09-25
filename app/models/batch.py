"""
Batch model for tracking harvest, processing, and transformation batches.
"""
from sqlalchemy import Column, String, DateTime, ForeignKey, func, Numeric, Date, Index
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid

from app.core.database import Base
from app.models.base import JSONType


class Batch(Base):
    """Batch model for tracking harvest, processing, and transformation batches."""
    
    __tablename__ = "batches"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    batch_id = Column(String(100), unique=True, nullable=False)  # 'batch_refined_2023_456', 'HARVEST-2023-10-001'
    batch_type = Column(String(50), nullable=False)  # 'harvest', 'processing', 'transformation'
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    
    # Quantity and unit
    quantity = Column(Numeric(12, 4), nullable=False)
    unit = Column(String(20), nullable=False)  # 'KGM', 'MT'
    
    # Batch specific data
    production_date = Column(Date, nullable=False)
    expiry_date = Column(Date)
    quality_metrics = Column(JSONType)  # Quality measurements and parameters
    
    # Location and facility information
    location_name = Column(String(255))  # Farm name, mill name, processing facility
    location_coordinates = Column(JSONType)  # {"latitude": 1.23, "longitude": 103.45}
    facility_code = Column(String(100))  # Mill code, facility identifier
    
    # Transformation tracking
    transformation_id = Column(String(100))  # For refineries: transformation events
    parent_batch_ids = Column(JSONType)  # List of input batch IDs for traceability

    # Purchase Order Linkage - REMOVED: Use audit trail for provenance tracking instead of direct FK
    # source_purchase_order_id = Column(UUID(as_uuid=True), ForeignKey("purchase_orders.id"))  # REMOVED: Circular reference
    
    # Origin and traceability data
    origin_data = Column(JSONType)  # Origin data for harvest batches
    certifications = Column(JSONType)  # List of applicable certifications
    
    # Processing and handling information
    processing_method = Column(String(255))  # Processing method used
    storage_conditions = Column(String(500))  # Storage conditions and requirements
    transportation_method = Column(String(255))  # Transportation method
    
    # Status and lifecycle
    status = Column(String(50), nullable=False, default='active')  # 'active', 'transferred', 'delivered', 'consumed', 'expired', 'recalled'
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    # Additional metadata
    batch_metadata = Column(JSONType)  # Additional batch-specific metadata
    
    # Relationships
    # source_purchase_order relationship removed - use batch_creation_events for provenance tracking
    product = relationship("Product")
    creation_events = relationship("BatchCreationEvent", foreign_keys="BatchCreationEvent.batch_id", cascade="all, delete-orphan")
    po_linkages = relationship("POBatchLinkage", back_populates="batch")
    po_allocations = relationship("POFulfillmentAllocation", back_populates="source_batch")
    farm_contributions = relationship("BatchFarmContribution", back_populates="batch")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_batch_company_id', 'company_id'),
        Index('idx_batch_product_id', 'product_id'),
        Index('idx_batch_type', 'batch_type'),
        Index('idx_batch_production_date', 'production_date'),
        Index('idx_batch_status', 'status'),
        Index('idx_batch_transformation_id', 'transformation_id'),
        # Index('idx_batch_source_po', 'source_purchase_order_id'),  # REMOVED: Field no longer exists
    )


class BatchTransaction(Base):
    """Batch transaction model for tracking batch movements and transformations."""
    
    __tablename__ = "batch_transactions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    transaction_type = Column(String(50), nullable=False)  # 'creation', 'consumption', 'transformation', 'transfer'
    
    # Source and destination batches
    source_batch_id = Column(UUID(as_uuid=True), ForeignKey("batches.id"))
    destination_batch_id = Column(UUID(as_uuid=True), ForeignKey("batches.id"))
    
    # Transaction details
    quantity_moved = Column(Numeric(12, 4), nullable=False)
    unit = Column(String(20), nullable=False)
    
    # Related entities
    purchase_order_id = Column(UUID(as_uuid=True), ForeignKey("purchase_orders.id"))
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    
    # Transaction metadata
    transaction_date = Column(DateTime(timezone=True), nullable=False)
    reference_number = Column(String(100))  # External reference number
    notes = Column(String(1000))
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Additional data
    transaction_data = Column(JSONType)  # Additional transaction-specific data
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_batch_transaction_source', 'source_batch_id'),
        Index('idx_batch_transaction_destination', 'destination_batch_id'),
        Index('idx_batch_transaction_po', 'purchase_order_id'),
        Index('idx_batch_transaction_company', 'company_id'),
        Index('idx_batch_transaction_date', 'transaction_date'),
        Index('idx_batch_transaction_type', 'transaction_type'),
    )


class BatchRelationship(Base):
    """Batch relationship model for tracking parent-child relationships between batches."""
    
    __tablename__ = "batch_relationships"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    parent_batch_id = Column(UUID(as_uuid=True), ForeignKey("batches.id"), nullable=False)
    child_batch_id = Column(UUID(as_uuid=True), ForeignKey("batches.id"), nullable=False)
    
    # Relationship details
    relationship_type = Column(String(50), nullable=False)  # 'input_material', 'split', 'merge', 'transformation'
    quantity_contribution = Column(Numeric(12, 4), nullable=False)  # Quantity from parent used in child
    percentage_contribution = Column(Numeric(5, 4))  # Percentage of child batch from this parent
    
    # Transformation details
    transformation_process = Column(String(255))  # Description of transformation process
    transformation_date = Column(DateTime(timezone=True), nullable=False)
    
    # Quality and yield information
    yield_percentage = Column(Numeric(5, 4))  # Yield from transformation
    quality_impact = Column(JSONType)  # Quality changes during transformation
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_batch_rel_parent', 'parent_batch_id'),
        Index('idx_batch_rel_child', 'child_batch_id'),
        Index('idx_batch_rel_type', 'relationship_type'),
        Index('idx_batch_rel_date', 'transformation_date'),
    )
