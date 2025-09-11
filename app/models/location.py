"""
Location Model for Universal Farm-Level Traceability

This model supports farm-level structure for ANY company type,
enabling brands, traders, processors, cooperatives, mills, and originators
to track individual farms/plantations for regulatory compliance.
"""
from sqlalchemy import Column, String, Boolean, Numeric, Integer, ForeignKey, DateTime, Index, Date, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
from app.models.base import DynamicJSONType


class Location(Base):
    """Location model supporting farm-level traceability for any company type"""
    
    __tablename__ = "locations"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=func.uuid_generate_v4())
    
    # Basic location info
    name = Column(String(255), nullable=False)
    location_type = Column(String(50), default='warehouse')  # 'warehouse', 'office', 'farm', 'plantation', 'mill', 'factory'
    address = Column(String(500))
    city = Column(String(100))
    state_province = Column(String(100))
    country = Column(String(100))
    postal_code = Column(String(20))
    
    # Company relationship
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    parent_company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=True)  # For farm hierarchy
    
    # Farm-specific fields (optional for any company type)
    is_farm_location = Column(Boolean, default=False)
    farm_type = Column(String(50))  # 'palm_plantation', 'leather_farm', 'silk_farm', 'coffee_farm', etc.
    farm_size_hectares = Column(Numeric(10, 3))
    farm_polygon = Column(String)  # Farm boundaries for large farms (simplified for now)
    established_year = Column(Integer)
    registration_number = Column(String(100))
    specialization = Column(String(100))  # 'calf_leather', 'mulberry_silk', 'arabica_coffee', etc.
    farm_owner_name = Column(String(200))  # For smallholders
    farm_contact_info = Column(DynamicJSONType)  # Phone, email, address details
    
    # Geographic coordinates (required for farms)
    latitude = Column(Numeric(10, 8))
    longitude = Column(Numeric(11, 8))
    accuracy_meters = Column(Numeric(8, 2))  # GPS accuracy
    elevation_meters = Column(Numeric(8, 2))  # Elevation above sea level
    
    # Compliance and certification data
    certifications = Column(DynamicJSONType)  # RSPO, Organic, Fair Trade, etc.
    compliance_data = Column(DynamicJSONType)  # EUDR, US regulatory compliance data
    
    # EUDR Compliance Fields (CRITICAL)
    deforestation_cutoff_date = Column(Date, default='2020-12-31')  # EUDR cutoff date
    land_use_change_history = Column(DynamicJSONType)  # Historical land use changes
    legal_land_tenure_docs = Column(DynamicJSONType)  # Legal documentation for land ownership
    due_diligence_statement = Column(DynamicJSONType)  # EUDR due diligence statement
    risk_assessment_data = Column(DynamicJSONType)  # Deforestation and other risk assessments
    compliance_verification_date = Column(DateTime(timezone=True))
    compliance_verified_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    compliance_status = Column(String(20), default='pending')  # 'pending', 'verified', 'failed', 'exempt'
    exemption_reason = Column(Text)  # Reason for compliance exemption
    
    # US Regulatory Compliance Fields
    uflpa_compliance_data = Column(DynamicJSONType)  # UFLPA forced labor risk assessment
    cbp_documentation = Column(DynamicJSONType)  # Customs and Border Protection docs
    supply_chain_mapping = Column(DynamicJSONType)  # Detailed supply chain mapping
    us_risk_assessment = Column(DynamicJSONType)  # US-specific risk assessments
    
    # Compliance Audit Trail
    last_compliance_check = Column(DateTime(timezone=True))
    compliance_check_frequency_days = Column(Integer, default=365)  # How often to re-check
    next_compliance_check_due = Column(DateTime(timezone=True))
    compliance_notes = Column(Text)  # Additional compliance notes
    
    # Status and metadata
    is_active = Column(Boolean, default=True)
    notes = Column(String(1000))
    
    # Audit trail
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    # Relationships
    company = relationship("Company", foreign_keys=[company_id], back_populates="locations")
    parent_company = relationship("Company", foreign_keys=[parent_company_id])
    batch_contributions = relationship("BatchFarmContribution", back_populates="location")
    created_by_user = relationship("User", foreign_keys=[created_by_user_id])
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_locations_company_id', 'company_id'),
        Index('idx_locations_parent_company_id', 'parent_company_id'),
        Index('idx_locations_is_farm_location', 'is_farm_location'),
        Index('idx_locations_farm_type', 'farm_type'),
        Index('idx_locations_farm_size_hectares', 'farm_size_hectares'),
        Index('idx_locations_country', 'country'),
        Index('idx_locations_coordinates', 'latitude', 'longitude'),
    )
    
    def __repr__(self):
        return f"<Location(name={self.name}, type={self.location_type}, is_farm={self.is_farm_location})>"
