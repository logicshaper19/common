"""
Document models for file uploads and document management
"""
import uuid
from sqlalchemy import Column, String, Integer, Boolean, Text, DateTime, ForeignKey, func, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import JSONType


class Document(Base):
    """
    Document model for storing file uploads and metadata.
    Supports both direct uploads and proxy uploads (cooperative on behalf of mill).
    """
    __tablename__ = "documents"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Relationships
    po_id = Column(UUID(as_uuid=True), ForeignKey("purchase_orders.id"), nullable=True)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    uploaded_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Document metadata
    document_type = Column(String(50), nullable=False)  # 'rspo_certificate', 'catchment_polygon', 'harvest_record'
    file_name = Column(String(255), nullable=False)
    original_file_name = Column(String(255), nullable=False)
    file_size = Column(Integer)  # Size in bytes
    mime_type = Column(String(100))
    
    # Storage information
    storage_url = Column(Text, nullable=False)
    storage_provider = Column(String(50), default='aws_s3')
    storage_key = Column(String(500))  # S3 key or file path
    
    # Validation status
    validation_status = Column(String(20), default='pending')  # 'pending', 'valid', 'invalid', 'expired'
    validation_errors = Column(JSONType)
    validation_metadata = Column(JSONType)  # Additional validation data
    
    # Proxy upload context
    is_proxy_upload = Column(Boolean, default=False)
    on_behalf_of_company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=True)
    proxy_authorization_id = Column(UUID(as_uuid=True), nullable=True)  # Reference to authorization
    
    # Document properties
    document_category = Column(String(50))  # 'certificate', 'map', 'report', 'audit'
    expiry_date = Column(DateTime(timezone=True))  # For certificates
    issue_date = Column(DateTime(timezone=True))
    issuing_authority = Column(String(255))  # Who issued the certificate
    
    # Compliance context
    compliance_regulations = Column(JSONType)  # ['EUDR', 'RSPO', 'UFLPA']
    tier_level = Column(Integer)  # Tier level of uploader
    sector_id = Column(String(50), ForeignKey("sectors.id"))
    
    # Soft delete and versioning
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    is_deleted = Column(Boolean, default=False, nullable=False)
    version = Column(Integer, default=1, nullable=False)
    parent_document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=True)

    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    company = relationship("Company", foreign_keys=[company_id])
    uploaded_by = relationship("User", foreign_keys=[uploaded_by_user_id])
    on_behalf_of_company = relationship("Company", foreign_keys=[on_behalf_of_company_id])
    purchase_order = relationship("PurchaseOrder", foreign_keys=[po_id])
    sector = relationship("Sector", foreign_keys=[sector_id])
    parent_document = relationship("Document", remote_side=[id], foreign_keys=[parent_document_id])

    # Table arguments for indexes and constraints
    __table_args__ = (
        # Performance indexes for common queries
        Index('idx_document_company_type', 'company_id', 'document_type'),
        Index('idx_document_po_type', 'po_id', 'document_type'),
        Index('idx_document_validation_status', 'validation_status'),
        Index('idx_document_created_at', 'created_at'),
        Index('idx_document_deleted', 'is_deleted', 'deleted_at'),
        Index('idx_document_version', 'parent_document_id', 'version'),
        # Unique constraint to prevent duplicate active documents
        Index('idx_unique_active_document_per_po_type', 'po_id', 'document_type', 'company_id',
              unique=True, postgresql_where=(Column('is_deleted') == False)),
    )


class ProxyRelationship(Base):
    """
    Model for tracking proxy relationships between companies.
    E.g., Cooperative authorized to upload documents for Mills.
    """
    __tablename__ = "proxy_relationships"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Relationship parties
    proxy_company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    originator_company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    
    # Authorization details
    authorized_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    relationship_type = Column(String(50), default='cooperative_mill')  # 'cooperative_mill', 'processor_farmer'
    
    # Permissions
    authorized_permissions = Column(JSONType, nullable=False)  # ['upload_certificates', 'provide_gps', 'submit_harvest_data']
    document_types_allowed = Column(JSONType)  # ['rspo_certificate', 'catchment_polygon']
    
    # Status and validity
    status = Column(String(20), default='pending')  # 'pending', 'active', 'suspended', 'revoked'
    authorized_at = Column(DateTime(timezone=True))
    expires_at = Column(DateTime(timezone=True))
    revoked_at = Column(DateTime(timezone=True))
    revoked_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    # Context
    sector_id = Column(String(50), ForeignKey("sectors.id"))
    notes = Column(Text)  # Additional context or restrictions
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    proxy_company = relationship("Company", foreign_keys=[proxy_company_id])
    originator_company = relationship("Company", foreign_keys=[originator_company_id])
    authorized_by = relationship("User", foreign_keys=[authorized_by_user_id])
    revoked_by = relationship("User", foreign_keys=[revoked_by_user_id])
    sector = relationship("Sector", foreign_keys=[sector_id])

    # Table arguments for indexes
    __table_args__ = (
        Index('idx_proxy_relationship_active', 'status', 'expires_at'),
        Index('idx_proxy_relationship_authorizer', 'originator_company_id', 'status'),
        Index('idx_proxy_relationship_proxy', 'proxy_company_id', 'status'),
        Index('idx_proxy_relationship_sector', 'sector_id', 'status'),
    )


class ProxyAction(Base):
    """
    Audit trail for actions performed by proxies on behalf of originators.
    """
    __tablename__ = "proxy_actions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Relationship context
    proxy_relationship_id = Column(UUID(as_uuid=True), ForeignKey("proxy_relationships.id"), nullable=False)
    po_id = Column(UUID(as_uuid=True), ForeignKey("purchase_orders.id"), nullable=True)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=True)

    # Action details
    action_type = Column(String(50), nullable=False)  # 'document_upload', 'origin_data_entry', 'po_confirmation'
    action_description = Column(Text)
    action_data = Column(JSONType)  # Detailed action data

    # Actor information
    performed_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    performed_at = Column(DateTime(timezone=True), server_default=func.now())

    # Result
    action_result = Column(String(20), default='success')  # 'success', 'failed', 'partial'
    error_details = Column(JSONType)

    # Relationships
    proxy_relationship = relationship("ProxyRelationship", foreign_keys=[proxy_relationship_id])
    purchase_order = relationship("PurchaseOrder", foreign_keys=[po_id])
    document = relationship("Document", foreign_keys=[document_id])
    performed_by = relationship("User", foreign_keys=[performed_by_user_id])

    # Table arguments for indexes
    __table_args__ = (
        Index('idx_proxy_action_document', 'document_id', 'performed_at'),
        Index('idx_proxy_action_relationship', 'proxy_relationship_id', 'performed_at'),
        Index('idx_proxy_action_performed_by', 'performed_by_user_id', 'performed_at'),
        Index('idx_proxy_action_type', 'action_type', 'performed_at'),
    )
