"""
Transformation models for comprehensive supply chain transformation tracking.
"""
from sqlalchemy import Column, String, DateTime, ForeignKey, func, Numeric, Date, Index, Enum as SQLEnum, Text, Boolean, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid
from enum import Enum
from datetime import datetime

from app.core.database import Base


class TransformationType(str, Enum):
    """Enumeration of transformation types in the supply chain."""
    HARVEST = "HARVEST"
    MILLING = "MILLING"
    CRUSHING = "CRUSHING"
    REFINING = "REFINING"
    FRACTIONATION = "FRACTIONATION"
    BLENDING = "BLENDING"
    MANUFACTURING = "MANUFACTURING"
    REPACKING = "REPACKING"
    STORAGE = "STORAGE"
    TRANSPORT = "TRANSPORT"


class TransformationStatus(str, Enum):
    """Status of transformation events."""
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class ValidationStatus(str, Enum):
    """Validation status of transformation events."""
    PENDING = "pending"
    VALIDATED = "validated"
    REJECTED = "rejected"


class TransformationEvent(Base):
    """Central table for tracking all transformation events in the supply chain."""
    
    __tablename__ = "transformation_events"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_id = Column(String(100), unique=True, nullable=False)  # 'TRANS-2024-001', 'MILL-2024-456'
    transformation_type = Column(SQLEnum(TransformationType), nullable=False)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    facility_id = Column(String(100))  # Mill code, facility identifier
    
    # Input/Output tracking
    input_batches = Column(JSONB, nullable=False)  # [{"batch_id": "uuid", "quantity": 1000, "unit": "MT"}]
    output_batches = Column(JSONB, nullable=False)  # [{"batch_id": "uuid", "quantity": 800, "unit": "MT"}]
    
    # Transformation details
    process_description = Column(Text)
    process_parameters = Column(JSONB)  # Role-specific parameters
    quality_metrics = Column(JSONB)  # Quality measurements
    
    # Yield and efficiency
    total_input_quantity = Column(Numeric(12, 4))
    total_output_quantity = Column(Numeric(12, 4))
    yield_percentage = Column(Numeric(5, 4))
    efficiency_metrics = Column(JSONB)  # Energy, water, resource usage
    
    # Timing
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True))
    duration_hours = Column(Numeric(8, 2))
    
    # Location and context
    location_name = Column(String(255))
    location_coordinates = Column(JSONB)  # {"latitude": 1.23, "longitude": 103.45}
    weather_conditions = Column(JSONB)  # For harvest events
    
    # Certifications and compliance
    certifications = Column(JSONB)
    compliance_data = Column(JSONB)
    
    # Status and validation
    status = Column(SQLEnum(TransformationStatus), default=TransformationStatus.PLANNED)
    validation_status = Column(SQLEnum(ValidationStatus), default=ValidationStatus.PENDING)
    validated_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    validated_at = Column(DateTime(timezone=True))
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Additional metadata
    event_metadata = Column(JSONB)
    
    # Versioning fields
    current_version = Column(Integer, default=1)
    is_locked = Column(Boolean, default=False)
    lock_reason = Column(Text)
    locked_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    locked_at = Column(DateTime(timezone=True))
    
    # Relationships
    company = relationship("Company", back_populates="transformation_events")
    created_by_user = relationship("User", foreign_keys=[created_by_user_id])
    validated_by_user = relationship("User", foreign_keys=[validated_by_user_id])
    locked_by_user = relationship("User", foreign_keys=[locked_by_user_id])
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_transformation_events_type', 'transformation_type'),
        Index('idx_transformation_events_company', 'company_id'),
        Index('idx_transformation_events_status', 'status'),
        Index('idx_transformation_events_start_time', 'start_time'),
        Index('idx_transformation_events_facility', 'facility_id'),
        Index('idx_transformation_events_validation', 'validation_status'),
    )


class PlantationHarvestData(Base):
    """Plantation harvest data for harvest transformation events."""
    
    __tablename__ = "plantation_harvest_data"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    transformation_event_id = Column(UUID(as_uuid=True), ForeignKey("transformation_events.id"), nullable=False)
    
    # Farm and location data
    farm_id = Column(String(100), nullable=False)
    farm_name = Column(String(255))
    gps_coordinates = Column(JSONB, nullable=False)  # {"latitude": 1.23, "longitude": 103.45}
    field_id = Column(String(100))
    
    # Harvest data
    harvest_date = Column(Date, nullable=False)
    harvest_method = Column(String(100))  # 'manual', 'mechanical'
    yield_per_hectare = Column(Numeric(8, 2))
    total_hectares = Column(Numeric(8, 2))
    
    # Quality data
    ffb_quality_grade = Column(String(50))  # 'A', 'B', 'C'
    moisture_content = Column(Numeric(5, 2))
    free_fatty_acid = Column(Numeric(5, 2))
    
    # Labor and resources
    labor_hours = Column(Numeric(8, 2))
    equipment_used = Column(JSONB)  # List of equipment
    fuel_consumed = Column(Numeric(8, 2))
    
    # Certifications
    certifications = Column(JSONB)
    sustainability_metrics = Column(JSONB)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    transformation_event = relationship("TransformationEvent")
    
    # Indexes
    __table_args__ = (
        Index('idx_plantation_harvest_event', 'transformation_event_id'),
        Index('idx_plantation_harvest_farm', 'farm_id'),
        Index('idx_plantation_harvest_date', 'harvest_date'),
    )


class MillProcessingData(Base):
    """Mill processing data for milling transformation events."""
    
    __tablename__ = "mill_processing_data"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    transformation_event_id = Column(UUID(as_uuid=True), ForeignKey("transformation_events.id"), nullable=False)
    
    # Processing parameters
    extraction_rate = Column(Numeric(5, 2))  # OER (Oil Extraction Rate)
    processing_capacity = Column(Numeric(12, 2))  # MT/hour
    processing_time_hours = Column(Numeric(8, 2))
    
    # Input data
    ffb_quantity = Column(Numeric(12, 4))
    ffb_quality_grade = Column(String(50))
    ffb_moisture_content = Column(Numeric(5, 2))
    
    # Output data
    cpo_quantity = Column(Numeric(12, 4))
    cpo_quality_grade = Column(String(50))
    cpo_ffa_content = Column(Numeric(5, 2))
    cpo_moisture_content = Column(Numeric(5, 2))
    kernel_quantity = Column(Numeric(12, 4))
    
    # Quality metrics
    oil_content_input = Column(Numeric(5, 2))
    oil_content_output = Column(Numeric(5, 2))
    extraction_efficiency = Column(Numeric(5, 2))
    
    # Resource usage
    energy_consumed = Column(Numeric(12, 2))  # kWh
    water_consumed = Column(Numeric(12, 2))  # m³
    steam_consumed = Column(Numeric(12, 2))  # MT
    
    # Equipment and maintenance
    equipment_used = Column(JSONB)
    maintenance_status = Column(JSONB)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    transformation_event = relationship("TransformationEvent")
    
    # Indexes
    __table_args__ = (
        Index('idx_mill_processing_event', 'transformation_event_id'),
        Index('idx_mill_processing_extraction_rate', 'extraction_rate'),
    )


class RefineryProcessingData(Base):
    """Refinery processing data for refining/fractionation transformation events."""
    
    __tablename__ = "refinery_processing_data"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    transformation_event_id = Column(UUID(as_uuid=True), ForeignKey("transformation_events.id"), nullable=False)
    
    # Processing type
    process_type = Column(String(50), nullable=False)  # 'refining', 'fractionation', 'hydrogenation'
    
    # Input data
    input_oil_quantity = Column(Numeric(12, 4))
    input_oil_type = Column(String(100))  # 'CPO', 'RBDPO'
    input_oil_quality = Column(JSONB)
    
    # Output data
    output_olein_quantity = Column(Numeric(12, 4))
    output_stearin_quantity = Column(Numeric(12, 4))
    output_other_quantity = Column(Numeric(12, 4))
    
    # Quality parameters
    iv_value = Column(Numeric(5, 2))  # Iodine Value
    melting_point = Column(Numeric(5, 2))
    solid_fat_content = Column(JSONB)  # At different temperatures
    color_grade = Column(String(50))
    
    # Processing parameters
    refining_loss = Column(Numeric(5, 2))
    fractionation_yield_olein = Column(Numeric(5, 2))
    fractionation_yield_stearin = Column(Numeric(5, 2))
    temperature_profile = Column(JSONB)
    pressure_profile = Column(JSONB)
    
    # Resource usage
    energy_consumed = Column(Numeric(12, 2))
    water_consumed = Column(Numeric(12, 2))
    chemicals_used = Column(JSONB)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    transformation_event = relationship("TransformationEvent")
    
    # Indexes
    __table_args__ = (
        Index('idx_refinery_processing_event', 'transformation_event_id'),
        Index('idx_refinery_processing_type', 'process_type'),
    )


class ManufacturerProcessingData(Base):
    """Manufacturer processing data for blending/manufacturing transformation events."""
    
    __tablename__ = "manufacturer_processing_data"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    transformation_event_id = Column(UUID(as_uuid=True), ForeignKey("transformation_events.id"), nullable=False)
    
    # Product information
    product_type = Column(String(100), nullable=False)  # 'soap', 'margarine', 'chocolate', 'biofuel'
    product_name = Column(String(255))
    product_grade = Column(String(50))
    
    # Recipe and formulation
    recipe_ratios = Column(JSONB, nullable=False)  # {"palm_oil": 0.6, "coconut_oil": 0.3, "other": 0.1}
    total_recipe_quantity = Column(Numeric(12, 4))
    recipe_unit = Column(String(20))
    
    # Input materials
    input_materials = Column(JSONB, nullable=False)  # [{"material": "palm_oil", "quantity": 600, "unit": "MT"}]
    
    # Output products
    output_quantity = Column(Numeric(12, 4))
    output_unit = Column(String(20))
    production_lot_number = Column(String(100))
    packaging_type = Column(String(100))
    packaging_quantity = Column(Numeric(12, 2))
    
    # Quality control
    quality_control_tests = Column(JSONB)
    quality_parameters = Column(JSONB)
    batch_testing_results = Column(JSONB)
    
    # Production parameters
    production_line = Column(String(100))
    production_shift = Column(String(50))
    production_speed = Column(Numeric(8, 2))  # units/hour
    
    # Resource usage
    energy_consumed = Column(Numeric(12, 2))
    water_consumed = Column(Numeric(12, 2))
    waste_generated = Column(Numeric(12, 2))
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    transformation_event = relationship("TransformationEvent")
    
    # Indexes
    __table_args__ = (
        Index('idx_manufacturer_processing_event', 'transformation_event_id'),
        Index('idx_manufacturer_processing_type', 'product_type'),
        Index('idx_manufacturer_processing_lot', 'production_lot_number'),
    )


class TransformationBatchMapping(Base):
    """Maps transformation events to their input and output batches."""
    
    __tablename__ = "transformation_batch_mapping"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    transformation_event_id = Column(UUID(as_uuid=True), ForeignKey("transformation_events.id"), nullable=False)
    batch_id = Column(UUID(as_uuid=True), ForeignKey("batches.id"), nullable=False)
    role = Column(String(50), nullable=False)  # 'input', 'output'
    sequence_order = Column(Numeric(5, 2))  # Order of processing
    quantity_used = Column(Numeric(12, 4))
    quantity_unit = Column(String(20))
    quality_grade = Column(String(50))
    notes = Column(Text)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Relationships
    transformation_event = relationship("TransformationEvent")
    batch = relationship("Batch")
    created_by_user = relationship("User")
    
    # Indexes
    __table_args__ = (
        Index('idx_transformation_batch_mapping_event', 'transformation_event_id'),
        Index('idx_transformation_batch_mapping_batch', 'batch_id'),
        Index('idx_transformation_batch_mapping_role', 'role'),
    )
