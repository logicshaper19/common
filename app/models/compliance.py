"""
Compliance-related database models for EUDR, RSPO, and other regulations.
"""
from sqlalchemy import Column, String, DateTime, ForeignKey, Numeric, Date, Text, Boolean, func, Index
from sqlalchemy.dialects.postgresql import UUID, ARRAY, JSONB
from sqlalchemy.orm import relationship
import uuid

from app.core.database import Base


class ComplianceTemplate(Base):
    """Compliance template model for storing report templates."""
    
    __tablename__ = "compliance_templates"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    regulation_type = Column(String(50), nullable=False)  # 'EUDR', 'RSPO', 'ISCC'
    version = Column(String(20), nullable=False)
    template_content = Column(Text, nullable=False)
    validation_rules = Column(JSONB)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    is_active = Column(Boolean, default=True)
    created_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    # Relationships
    created_by_user = relationship("User", foreign_keys=[created_by_user_id])
    reports = relationship("ComplianceReport", back_populates="template")


class ComplianceReport(Base):
    """Compliance report model for storing generated reports."""
    
    __tablename__ = "compliance_reports"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    template_id = Column(UUID(as_uuid=True), ForeignKey("compliance_templates.id"), nullable=False)
    po_id = Column(UUID(as_uuid=True), ForeignKey("purchase_orders.id"))
    report_data = Column(JSONB)
    generated_at = Column(DateTime, default=func.now())
    status = Column(String(50), default='GENERATED')
    file_path = Column(String(500))
    file_size = Column(Numeric(15, 0))
    generated_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    # Relationships
    company = relationship("Company", foreign_keys=[company_id])
    template = relationship("ComplianceTemplate", back_populates="reports")
    purchase_order = relationship("PurchaseOrder", foreign_keys=[po_id])
    generated_by_user = relationship("User", foreign_keys=[generated_by_user_id])


class RiskAssessment(Base):
    """Risk assessment model for tracking various risk types."""
    
    __tablename__ = "risk_assessments"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"))
    batch_id = Column(UUID(as_uuid=True), ForeignKey("batches.id"))
    po_id = Column(UUID(as_uuid=True), ForeignKey("purchase_orders.id"))
    risk_type = Column(String(50), nullable=False)  # 'DEFORESTATION', 'HUMAN_RIGHTS', etc.
    risk_score = Column(Numeric(5, 2), nullable=False)  # 0.00 to 1.00
    risk_factors = Column(JSONB)
    mitigation_measures = Column(Text)
    assessment_date = Column(Date, default=func.current_date())
    assessed_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    next_assessment_date = Column(Date)
    
    # Relationships
    company = relationship("Company", foreign_keys=[company_id])
    batch = relationship("Batch", foreign_keys=[batch_id])
    purchase_order = relationship("PurchaseOrder", foreign_keys=[po_id])
    assessed_by_user = relationship("User", foreign_keys=[assessed_by_user_id])


class MassBalanceCalculation(Base):
    """Mass balance calculation model for transformation events."""
    
    __tablename__ = "mass_balance_calculations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    transformation_event_id = Column(UUID(as_uuid=True), ForeignKey("transformation_events.id"), nullable=False)
    input_quantity = Column(Numeric(12, 4), nullable=False)
    output_quantity = Column(Numeric(12, 4), nullable=False)
    yield_percentage = Column(Numeric(5, 2), nullable=False)  # 0.00 to 100.00
    waste_percentage = Column(Numeric(5, 2), nullable=False)  # 0.00 to 100.00
    calculation_method = Column(String(100))
    calculated_at = Column(DateTime, default=func.now())
    calculated_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    # Relationships
    transformation_event = relationship("TransformationEvent", foreign_keys=[transformation_event_id])
    calculated_by_user = relationship("User", foreign_keys=[calculated_by_user_id])


class HSCode(Base):
    """HS code lookup table for product classification."""
    
    __tablename__ = "hs_codes"
    
    code = Column(String(20), primary_key=True)
    description = Column(Text, nullable=False)
    category = Column(String(100))
    regulation_applicable = Column(ARRAY(String(50)))  # ['EUDR', 'RSPO', 'ISCC']
    created_at = Column(DateTime, default=func.now())


# Add indexes for performance
Index('idx_compliance_templates_type', ComplianceTemplate.regulation_type)
Index('idx_compliance_templates_active', ComplianceTemplate.is_active)
Index('idx_compliance_reports_company', ComplianceReport.company_id)
Index('idx_compliance_reports_po', ComplianceReport.po_id)
Index('idx_compliance_reports_generated', ComplianceReport.generated_at)
Index('idx_risk_assessments_company', RiskAssessment.company_id)
Index('idx_risk_assessments_batch', RiskAssessment.batch_id)
Index('idx_risk_assessments_type', RiskAssessment.risk_type)
Index('idx_mass_balance_transformation', MassBalanceCalculation.transformation_event_id)
