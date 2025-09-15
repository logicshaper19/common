"""
Transformation versioning models for comprehensive audit trail and data integrity.
"""
from sqlalchemy import Column, String, DateTime, ForeignKey, func, Numeric, Text, Boolean, Integer, Index, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid
from enum import Enum
from datetime import datetime

from app.core.database import Base


class VersionType(str, Enum):
    """Types of transformation event versions."""
    REVISION = "revision"
    CORRECTION = "correction"
    AMENDMENT = "amendment"


class ApprovalStatus(str, Enum):
    """Approval status for transformation versions."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class TransformationEventVersion(Base):
    """Version history for transformation events."""
    
    __tablename__ = "transformation_event_versions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    transformation_event_id = Column(UUID(as_uuid=True), ForeignKey("transformation_events.id"), nullable=False)
    version_number = Column(Integer, nullable=False)
    version_type = Column(SQLEnum(VersionType), default=VersionType.REVISION)
    
    # Snapshot of the event data at this version
    event_data = Column(JSONB, nullable=False)
    process_parameters = Column(JSONB)
    quality_metrics = Column(JSONB)
    efficiency_metrics = Column(JSONB)
    
    # Version metadata
    change_reason = Column(Text)
    change_description = Column(Text)
    approval_required = Column(Boolean, default=False)
    approval_status = Column(SQLEnum(ApprovalStatus), default=ApprovalStatus.PENDING)
    approved_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    approved_at = Column(DateTime(timezone=True))
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Relationships
    transformation_event = relationship("TransformationEvent")
    created_by_user = relationship("User", foreign_keys=[created_by_user_id])
    approved_by_user = relationship("User", foreign_keys=[approved_by_user_id])
    
    # Indexes
    __table_args__ = (
        Index('idx_transformation_versions_event', 'transformation_event_id'),
        Index('idx_transformation_versions_number', 'transformation_event_id', 'version_number'),
        Index('idx_transformation_versions_approval', 'approval_status'),
    )


class InheritanceType(str, Enum):
    """Types of quality inheritance."""
    DIRECT = "direct"
    DEGRADED = "degraded"
    ENHANCED = "enhanced"
    CALCULATED = "calculated"


class QualityInheritanceRule(Base):
    """Rules for quality inheritance between transformation stages."""
    
    __tablename__ = "quality_inheritance_rules"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    transformation_type = Column(String(50), nullable=False)  # References transformation_type enum
    input_quality_metric = Column(String(100), nullable=False)
    output_quality_metric = Column(String(100), nullable=False)
    inheritance_type = Column(SQLEnum(InheritanceType), nullable=False)
    inheritance_formula = Column(Text)  # SQL formula or calculation logic
    degradation_factor = Column(Numeric(5, 4))  # For degraded inheritance
    enhancement_factor = Column(Numeric(5, 4))  # For enhanced inheritance
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Relationships
    created_by_user = relationship("User")
    
    # Indexes
    __table_args__ = (
        Index('idx_quality_rules_type', 'transformation_type'),
        Index('idx_quality_rules_active', 'is_active'),
    )


class CostCategory(str, Enum):
    """Categories of transformation costs."""
    ENERGY = "energy"
    LABOR = "labor"
    MATERIALS = "materials"
    EQUIPMENT = "equipment"
    OVERHEAD = "overhead"
    TRANSPORT = "transport"
    WASTE = "waste"


class TransformationCost(Base):
    """Cost tracking for transformation events."""
    
    __tablename__ = "transformation_costs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    transformation_event_id = Column(UUID(as_uuid=True), ForeignKey("transformation_events.id"), nullable=False)
    cost_category = Column(SQLEnum(CostCategory), nullable=False)
    cost_type = Column(String(100), nullable=False)  # 'electricity', 'fuel', 'water', 'maintenance', etc.
    quantity = Column(Numeric(12, 4), nullable=False)
    unit = Column(String(20), nullable=False)
    unit_cost = Column(Numeric(12, 4), nullable=False)
    total_cost = Column(Numeric(15, 2), nullable=False)
    currency = Column(String(3), default='USD')
    
    # Cost breakdown details
    cost_breakdown = Column(JSONB)  # Detailed breakdown of cost components
    supplier_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"))  # For external costs
    cost_center = Column(String(100))  # Internal cost center
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Relationships
    transformation_event = relationship("TransformationEvent")
    supplier = relationship("Company")
    created_by_user = relationship("User")
    
    # Indexes
    __table_args__ = (
        Index('idx_transformation_costs_event', 'transformation_event_id'),
        Index('idx_transformation_costs_category', 'cost_category'),
        Index('idx_transformation_costs_date', 'created_at'),
    )


class TransformationProcessTemplate(Base):
    """Templates for standardized transformation processes."""
    
    __tablename__ = "transformation_process_templates"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    template_name = Column(String(255), nullable=False)
    transformation_type = Column(String(50), nullable=False)  # References transformation_type enum
    company_type = Column(String(50), nullable=False)  # 'plantation', 'mill', 'refinery', 'manufacturer'
    sector_id = Column(String(50), ForeignKey("sectors.id"))
    
    # Template configuration
    template_config = Column(JSONB, nullable=False)  # Process parameters, required fields, validation rules
    default_metrics = Column(JSONB)  # Default quality and efficiency metrics
    cost_estimates = Column(JSONB)  # Estimated costs for this process
    quality_standards = Column(JSONB)  # Quality requirements and thresholds
    
    # Template metadata
    description = Column(Text)
    version = Column(String(20), default='1.0')
    is_standard = Column(Boolean, default=False)  # Industry standard template
    is_active = Column(Boolean, default=True)
    
    # Usage tracking
    usage_count = Column(Integer, default=0)
    last_used_at = Column(DateTime(timezone=True))
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    updated_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    # Relationships
    sector = relationship("Sector")
    created_by_user = relationship("User", foreign_keys=[created_by_user_id])
    updated_by_user = relationship("User", foreign_keys=[updated_by_user_id])
    
    # Indexes
    __table_args__ = (
        Index('idx_process_templates_type', 'transformation_type'),
        Index('idx_process_templates_company_type', 'company_type'),
        Index('idx_process_templates_active', 'is_active'),
    )


class EndpointType(str, Enum):
    """Types of real-time monitoring endpoints."""
    SENSOR = "sensor"
    API = "api"
    FILE_UPLOAD = "file_upload"
    MANUAL = "manual"


class AuthType(str, Enum):
    """Types of authentication for monitoring endpoints."""
    NONE = "none"
    API_KEY = "api_key"
    OAUTH = "oauth"
    BASIC = "basic"


class RealTimeMonitoringEndpoint(Base):
    """Real-time monitoring endpoints for transformation data."""
    
    __tablename__ = "real_time_monitoring_endpoints"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    facility_id = Column(String(100), nullable=False)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    endpoint_name = Column(String(255), nullable=False)
    endpoint_type = Column(SQLEnum(EndpointType), nullable=False)
    endpoint_url = Column(String(500))
    data_format = Column(String(50))  # 'json', 'csv', 'xml', 'binary'
    
    # Monitoring configuration
    monitored_metrics = Column(JSONB, nullable=False)  # List of metrics to monitor
    update_frequency = Column(Integer, default=60)  # Seconds between updates
    data_retention_days = Column(Integer, default=30)
    
    # Authentication and security
    auth_type = Column(SQLEnum(AuthType), default=AuthType.NONE)
    auth_config = Column(JSONB)  # Authentication configuration
    
    # Status and health
    is_active = Column(Boolean, default=True)
    last_data_received = Column(DateTime(timezone=True))
    last_error = Column(Text)
    error_count = Column(Integer, default=0)
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Relationships
    company = relationship("Company")
    created_by_user = relationship("User")
    
    # Indexes
    __table_args__ = (
        Index('idx_monitoring_endpoints_facility', 'facility_id'),
        Index('idx_monitoring_endpoints_company', 'company_id'),
        Index('idx_monitoring_endpoints_active', 'is_active'),
    )
