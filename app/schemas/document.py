"""
Pydantic schemas for document management
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, validator


class DocumentBase(BaseModel):
    """Base schema for Document"""
    document_type: str = Field(..., description="Type of document (rspo_certificate, catchment_polygon, etc.)")
    file_name: str = Field(..., description="Stored file name")
    original_file_name: str = Field(..., description="Original file name from upload")
    file_size: Optional[int] = Field(None, description="File size in bytes")
    mime_type: Optional[str] = Field(None, description="MIME type of the file")
    document_category: Optional[str] = Field(None, description="Document category (certificate, map, report, audit)")
    compliance_regulations: Optional[List[str]] = Field(None, description="Regulations this document supports")


class DocumentCreate(DocumentBase):
    """Schema for creating a new document"""
    po_id: Optional[UUID] = Field(None, description="Purchase order ID this document relates to")
    on_behalf_of_company_id: Optional[UUID] = Field(None, description="Company ID if uploading as proxy")
    sector_id: Optional[str] = Field(None, description="Sector this document belongs to")
    tier_level: Optional[int] = Field(None, description="Tier level of uploader")
    expiry_date: Optional[datetime] = Field(None, description="Document expiry date")
    issue_date: Optional[datetime] = Field(None, description="Document issue date")
    issuing_authority: Optional[str] = Field(None, description="Who issued the document")


class DocumentResponse(DocumentBase):
    """Schema for document responses"""
    id: UUID
    po_id: Optional[UUID]
    company_id: UUID
    uploaded_by_user_id: UUID
    
    # Storage information
    storage_url: str
    storage_provider: str = "aws_s3"
    storage_key: Optional[str]
    
    # Validation status
    validation_status: str = "pending"
    validation_errors: Optional[Dict[str, Any]]
    validation_metadata: Optional[Dict[str, Any]]
    
    # Proxy context
    is_proxy_upload: bool = False
    on_behalf_of_company_id: Optional[UUID]
    proxy_authorization_id: Optional[UUID]
    
    # Document properties
    expiry_date: Optional[datetime]
    issue_date: Optional[datetime]
    issuing_authority: Optional[str]
    
    # Context
    tier_level: Optional[int]
    sector_id: Optional[str]
    
    # Audit fields
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class DocumentListResponse(BaseModel):
    """Schema for paginated document list responses"""
    documents: List[DocumentResponse]
    total: int
    limit: int
    offset: int


class ProxyRelationshipBase(BaseModel):
    """Base schema for ProxyRelationship"""
    proxy_company_id: UUID = Field(..., description="Company ID of the proxy (e.g., cooperative)")
    originator_company_id: UUID = Field(..., description="Company ID of the originator (e.g., mill)")
    relationship_type: str = Field("cooperative_mill", description="Type of proxy relationship")
    authorized_permissions: List[str] = Field(..., description="List of authorized permissions")
    document_types_allowed: Optional[List[str]] = Field(None, description="Document types proxy can upload")
    sector_id: Optional[str] = Field(None, description="Sector this relationship applies to")
    notes: Optional[str] = Field(None, description="Additional notes or restrictions")


class ProxyRelationshipCreate(ProxyRelationshipBase):
    """Schema for creating a new proxy relationship"""
    expires_at: Optional[datetime] = Field(None, description="When this authorization expires")
    
    @validator('authorized_permissions')
    def validate_permissions(cls, v):
        valid_permissions = [
            'upload_certificates', 'provide_gps', 'submit_harvest_data',
            'upload_documents', 'confirm_po', 'add_origin_data'
        ]
        for permission in v:
            if permission not in valid_permissions:
                raise ValueError(f"Invalid permission: {permission}")
        return v
    
    @validator('document_types_allowed')
    def validate_document_types(cls, v):
        if v is None:
            return v
        valid_types = [
            'rspo_certificate', 'catchment_polygon', 'harvest_record',
            'audit_report', 'certification', 'map_data'
        ]
        for doc_type in v:
            if doc_type not in valid_types:
                raise ValueError(f"Invalid document type: {doc_type}")
        return v


class ProxyRelationshipResponse(ProxyRelationshipBase):
    """Schema for proxy relationship responses"""
    id: UUID
    authorized_by_user_id: UUID
    
    # Status and validity
    status: str = "pending"
    authorized_at: Optional[datetime]
    expires_at: Optional[datetime]
    revoked_at: Optional[datetime]
    revoked_by_user_id: Optional[UUID]
    
    # Audit fields
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ProxyActionResponse(BaseModel):
    """Schema for proxy action audit trail"""
    id: UUID
    proxy_relationship_id: UUID
    po_id: Optional[UUID]
    document_id: Optional[UUID]
    
    # Action details
    action_type: str
    action_description: Optional[str]
    action_data: Optional[Dict[str, Any]]
    
    # Actor information
    performed_by_user_id: UUID
    performed_at: datetime
    
    # Result
    action_result: str = "success"
    error_details: Optional[Dict[str, Any]]
    
    class Config:
        from_attributes = True


# Document type definitions for validation
DOCUMENT_TYPES = {
    'rspo_certificate': {
        'category': 'certificate',
        'allowed_mime_types': ['application/pdf', 'image/jpeg', 'image/png'],
        'max_size_mb': 10,
        'description': 'RSPO certification documents'
    },
    'catchment_polygon': {
        'category': 'map',
        'allowed_mime_types': ['application/json', 'application/geo+json', 'application/zip'],
        'max_size_mb': 5,
        'description': 'Mill catchment area polygon data'
    },
    'harvest_record': {
        'category': 'report',
        'allowed_mime_types': ['application/pdf', 'application/vnd.ms-excel', 'text/csv'],
        'max_size_mb': 10,
        'description': 'Harvest records and production data'
    },
    'audit_report': {
        'category': 'audit',
        'allowed_mime_types': ['application/pdf'],
        'max_size_mb': 20,
        'description': 'Third-party audit reports'
    },
    'certification': {
        'category': 'certificate',
        'allowed_mime_types': ['application/pdf', 'image/jpeg', 'image/png'],
        'max_size_mb': 10,
        'description': 'General certification documents'
    },
    'map_data': {
        'category': 'map',
        'allowed_mime_types': ['application/json', 'application/geo+json', 'image/png', 'image/jpeg'],
        'max_size_mb': 15,
        'description': 'Geographic and mapping data'
    }
}


class DocumentTypeInfo(BaseModel):
    """Schema for document type information"""
    document_type: str
    category: str
    allowed_mime_types: List[str]
    max_size_mb: int
    description: str


class DocumentTypesResponse(BaseModel):
    """Schema for available document types"""
    document_types: Dict[str, DocumentTypeInfo]


# Validation schemas for specific document types
class RSPOCertificateMetadata(BaseModel):
    """Metadata schema for RSPO certificates"""
    certificate_number: Optional[str]
    certificate_type: Optional[str]  # 'IP', 'SG', 'MB', 'B&C'
    mill_name: Optional[str]
    mill_code: Optional[str]
    valid_from: Optional[datetime]
    valid_until: Optional[datetime]
    certification_body: Optional[str]


class CatchmentPolygonMetadata(BaseModel):
    """Metadata schema for catchment area polygons"""
    mill_id: Optional[str]
    total_area_hectares: Optional[float]
    polygon_type: Optional[str]  # 'actual', 'estimated', 'buffer'
    data_source: Optional[str]
    collection_date: Optional[datetime]
    coordinate_system: Optional[str] = "WGS84"


class HarvestRecordMetadata(BaseModel):
    """Metadata schema for harvest records"""
    harvest_period_start: Optional[datetime]
    harvest_period_end: Optional[datetime]
    total_volume_tons: Optional[float]
    number_of_suppliers: Optional[int]
    record_type: Optional[str]  # 'monthly', 'quarterly', 'annual'
