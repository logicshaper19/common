"""
Document management API endpoints
"""
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth import get_current_user
from app.core.file_security import file_security_validator, FileSecurityError
from app.models.user import User
from app.models.document import Document, ProxyRelationship
from app.services.document_storage import DocumentStorageService
from app.schemas.document import (
    DocumentResponse, DocumentCreate, ProxyRelationshipResponse,
    ProxyRelationshipCreate, DocumentListResponse
)
from app.exceptions.document_exceptions import DocumentError, map_document_exception_to_http

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    document_type: str = Form(...),
    po_id: Optional[str] = Form(None),
    on_behalf_of_company_id: Optional[str] = Form(None),
    sector_id: Optional[str] = Form(None),
    tier_level: Optional[int] = Form(None),
    compliance_regulations: Optional[str] = Form(None),  # JSON string
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Upload a document with metadata.
    Supports both direct uploads and proxy uploads (cooperative on behalf of mill).
    Enhanced with comprehensive security validation.
    """

    # Enhanced file security validation
    try:
        # Determine allowed file categories based on document type
        allowed_categories = ['document']  # Default
        if document_type in ['rspo_certificate', 'bci_certificate']:
            allowed_categories = ['document', 'image']
        elif document_type == 'catchment_polygon':
            allowed_categories = ['geographic', 'archive']
        elif document_type in ['harvest_record', 'member_list']:
            allowed_categories = ['spreadsheet', 'document']

        # Perform comprehensive file validation
        validation_result = await file_security_validator.validate_file_upload(
            file=file,
            allowed_categories=allowed_categories,
            require_virus_scan=True
        )

        if not validation_result['is_valid']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "message": "File validation failed",
                    "error_code": "INVALID_FILE",
                    "errors": validation_result.get('errors', []),
                    "warnings": validation_result.get('warnings', [])
                }
            )

    except FileSecurityError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": e.message,
                "error_code": e.error_code or "FILE_SECURITY_ERROR",
                "file_name": e.file_name
            }
        )

    # Parse compliance regulations if provided
    regulations_list = []
    if compliance_regulations:
        try:
            import json
            regulations_list = json.loads(compliance_regulations)
        except json.JSONDecodeError:
            regulations_list = [compliance_regulations]  # Single regulation as string

    storage_service = DocumentStorageService(db)

    try:
        document = await storage_service.upload_document(
            file=file,
            document_type=document_type,
            company_id=str(current_user.company_id),
            user_id=str(current_user.id),
            po_id=po_id,
            on_behalf_of_company_id=on_behalf_of_company_id,
            sector_id=sector_id,
            tier_level=tier_level,
            compliance_regulations=regulations_list
        )

        return DocumentResponse.from_orm(document)

    except DocumentError as e:
        raise map_document_exception_to_http(e)
    except Exception as e:
        # Log unexpected errors and convert to generic DocumentError
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Unexpected error in document upload: {str(e)}")

        from app.exceptions.document_exceptions import DocumentError
        doc_error = DocumentError(f"Document upload failed: {str(e)}")
        raise map_document_exception_to_http(doc_error)


@router.get("/", response_model=DocumentListResponse)
async def get_documents(
    po_id: Optional[str] = Query(None),
    document_type: Optional[str] = Query(None),
    company_id: Optional[str] = Query(None),
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get documents with optional filters.
    Users can only see documents from their company or documents uploaded on their behalf.
    """
    
    storage_service = DocumentStorageService(db)
    
    # If no company_id specified, default to current user's company
    if not company_id:
        company_id = str(current_user.company_id)
    
    # Security check: users can only see their company's documents
    # Admin override: super admins can view any company's documents
    if company_id != str(current_user.company_id):
        if current_user.role != 'admin':
            raise HTTPException(status_code=403, detail="Access denied")

        # Enhanced admin audit logging
        from app.services.audit import AuditService
        audit_service = AuditService(db)

        try:
            await audit_service.log_admin_action(
                admin_user_id=current_user.id,
                action_type="document_list_access_override",
                target_resource_type="document_list",
                target_resource_id=f"company_{company_id}",
                target_company_id=UUID(company_id),
                details={
                    "access_type": "document_list_view",
                    "target_company_id": company_id,
                    "filters": {
                        "po_id": po_id,
                        "document_type": document_type
                    }
                }
            )
        except Exception as e:
            logger.error(f"Failed to log admin override action: {e}")
            # Continue with the request even if audit logging fails
    
    documents = await storage_service.get_documents(
        company_id=company_id,
        po_id=po_id,
        document_type=document_type
    )
    
    # Apply pagination
    total = len(documents)
    paginated_documents = documents[offset:offset + limit]
    
    return DocumentListResponse(
        documents=[DocumentResponse.from_orm(doc) for doc in paginated_documents],
        total=total,
        limit=limit,
        offset=offset
    )


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific document by ID"""
    
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Security check: user must have access to this document
    has_access = False
    access_reason = "direct_access"

    # Check normal access permissions
    if (document.company_id == current_user.company_id or
        document.on_behalf_of_company_id == current_user.company_id):
        has_access = True

    # Admin override check
    elif current_user.role == 'admin':
        has_access = True
        access_reason = "admin_override"

        # Enhanced admin audit logging
        from app.services.audit import AuditService
        audit_service = AuditService(db)

        try:
            await audit_service.log_admin_action(
                admin_user_id=current_user.id,
                action_type="document_access_override",
                target_resource_type="document",
                target_resource_id=str(document_id),
                target_company_id=document.company_id,
                details={
                    "document_name": document.filename,
                    "document_type": document.document_type,
                    "file_size": document.file_size,
                    "original_company": document.company.name if document.company else "Unknown",
                    "access_reason": "admin_override"
                }
            )
        except Exception as e:
            logger.error(f"Failed to log admin override action: {e}")
            # Continue with the request even if audit logging fails

    if not has_access:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return DocumentResponse.from_orm(document)


@router.delete("/{document_id}")
async def delete_document(
    document_id: UUID,
    deletion_reason: Optional[str] = Query(None, description="Reason for deletion (required for admin overrides)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a document (soft delete)"""

    storage_service = DocumentStorageService(db)

    try:
        success = await storage_service.delete_document(
            document_id=str(document_id),
            user_id=str(current_user.id),
            deletion_reason=deletion_reason
        )

        if success:
            return {"message": "Document deleted successfully"}
        else:
            from app.exceptions.document_exceptions import DocumentError
            doc_error = DocumentError("Failed to delete document")
            raise map_document_exception_to_http(doc_error)

    except DocumentError as e:
        raise map_document_exception_to_http(e)
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Unexpected error in document deletion: {str(e)}")

        from app.exceptions.document_exceptions import DocumentError
        doc_error = DocumentError(f"Document deletion failed: {str(e)}")
        raise map_document_exception_to_http(doc_error)


# Proxy relationship endpoints

@router.post("/proxy/relationships", response_model=ProxyRelationshipResponse)
async def create_proxy_relationship(
    relationship_data: ProxyRelationshipCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a proxy relationship authorization.
    Allows cooperatives to upload documents on behalf of mills.
    """
    
    # Validate that current user can authorize for the originator company
    if str(current_user.company_id) != relationship_data.originator_company_id:
        raise HTTPException(
            status_code=403, 
            detail="Can only authorize proxy relationships for your own company"
        )
    
    # Check if relationship already exists
    existing = db.query(ProxyRelationship).filter(
        ProxyRelationship.proxy_company_id == relationship_data.proxy_company_id,
        ProxyRelationship.originator_company_id == relationship_data.originator_company_id,
        ProxyRelationship.status.in_(['pending', 'active'])
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=400,
            detail="Proxy relationship already exists"
        )
    
    # Create new proxy relationship
    proxy_relationship = ProxyRelationship(
        proxy_company_id=relationship_data.proxy_company_id,
        originator_company_id=relationship_data.originator_company_id,
        authorized_by_user_id=current_user.id,
        relationship_type=relationship_data.relationship_type,
        authorized_permissions=relationship_data.authorized_permissions,
        document_types_allowed=relationship_data.document_types_allowed,
        status='active',  # Auto-approve for now
        sector_id=relationship_data.sector_id,
        notes=relationship_data.notes
    )
    
    if relationship_data.expires_at:
        proxy_relationship.expires_at = relationship_data.expires_at
    
    db.add(proxy_relationship)
    db.commit()
    db.refresh(proxy_relationship)
    
    return ProxyRelationshipResponse.from_orm(proxy_relationship)


@router.get("/proxy/relationships", response_model=List[ProxyRelationshipResponse])
async def get_proxy_relationships(
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get proxy relationships for current user's company.
    Returns relationships where company is either proxy or originator.
    """
    
    query = db.query(ProxyRelationship).filter(
        (ProxyRelationship.proxy_company_id == current_user.company_id) |
        (ProxyRelationship.originator_company_id == current_user.company_id)
    )
    
    if status:
        query = query.filter(ProxyRelationship.status == status)
    
    relationships = query.order_by(ProxyRelationship.created_at.desc()).all()
    
    return [ProxyRelationshipResponse.from_orm(rel) for rel in relationships]


@router.put("/proxy/relationships/{relationship_id}/status")
async def update_proxy_relationship_status(
    relationship_id: UUID,
    status: str = Form(...),  # 'active', 'suspended', 'revoked'
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update the status of a proxy relationship"""
    
    relationship = db.query(ProxyRelationship).filter(
        ProxyRelationship.id == relationship_id
    ).first()
    
    if not relationship:
        raise HTTPException(status_code=404, detail="Proxy relationship not found")
    
    # Only originator company can update status
    if relationship.originator_company_id != current_user.company_id:
        raise HTTPException(
            status_code=403,
            detail="Only the originator company can update relationship status"
        )
    
    if status not in ['active', 'suspended', 'revoked']:
        raise HTTPException(
            status_code=400,
            detail="Invalid status. Must be 'active', 'suspended', or 'revoked'"
        )
    
    relationship.status = status
    if status == 'revoked':
        relationship.revoked_at = db.func.now()
        relationship.revoked_by_user_id = current_user.id
    
    db.commit()
    
    return {"message": f"Proxy relationship status updated to {status}"}
