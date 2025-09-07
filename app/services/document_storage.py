"""
Document storage service for handling file uploads and management
"""
import os
import uuid
import mimetypes
from typing import Optional, List, Dict, Any, BinaryIO
from datetime import datetime, timedelta
from pathlib import Path

import boto3
from botocore.exceptions import ClientError
from fastapi import UploadFile, HTTPException
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.document import Document, ProxyRelationship, ProxyAction
from app.models.user import User
from app.models.company import Company


class DocumentStorageService:
    """Service for handling document uploads, storage, and management"""
    
    def __init__(self, db: Session):
        self.db = db
        self.s3_client = None
        self.bucket_name = getattr(settings, 'AWS_S3_BUCKET', 'common-supply-chain-documents')
        
        # Initialize S3 client if AWS credentials are available
        if hasattr(settings, 'AWS_ACCESS_KEY_ID') and settings.AWS_ACCESS_KEY_ID:
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=getattr(settings, 'AWS_REGION', 'us-east-1')
            )
    
    async def upload_document(
        self,
        file: UploadFile,
        document_type: str,
        company_id: str,
        user_id: str,
        po_id: Optional[str] = None,
        on_behalf_of_company_id: Optional[str] = None,
        sector_id: Optional[str] = None,
        tier_level: Optional[int] = None,
        compliance_regulations: Optional[List[str]] = None
    ) -> Document:
        """
        Upload a document and create database record
        
        Args:
            file: The uploaded file
            document_type: Type of document (rspo_certificate, catchment_polygon, etc.)
            company_id: ID of the company uploading
            user_id: ID of the user uploading
            po_id: Optional PO ID this document relates to
            on_behalf_of_company_id: If proxy upload, the company being represented
            sector_id: Sector this document belongs to
            tier_level: Tier level of the uploader
            compliance_regulations: List of regulations this document supports
        
        Returns:
            Document: Created document record
        """
        
        # Validate file
        await self._validate_file(file, document_type)
        
        # Check proxy permissions if uploading on behalf of another company
        if on_behalf_of_company_id:
            await self._validate_proxy_permissions(
                user_id, company_id, on_behalf_of_company_id, document_type
            )
        
        # Generate unique file name
        file_extension = Path(file.filename).suffix
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        storage_key = f"documents/{document_type}/{unique_filename}"
        
        # Upload to storage
        storage_url = await self._upload_to_storage(file, storage_key)
        
        # Create document record
        document = Document(
            po_id=po_id,
            company_id=company_id,
            uploaded_by_user_id=user_id,
            document_type=document_type,
            file_name=unique_filename,
            original_file_name=file.filename,
            file_size=file.size,
            mime_type=file.content_type,
            storage_url=storage_url,
            storage_key=storage_key,
            is_proxy_upload=bool(on_behalf_of_company_id),
            on_behalf_of_company_id=on_behalf_of_company_id,
            document_category=self._get_document_category(document_type),
            compliance_regulations=compliance_regulations or [],
            tier_level=tier_level,
            sector_id=sector_id
        )
        
        self.db.add(document)
        self.db.commit()
        self.db.refresh(document)
        
        # Log proxy action if applicable
        if on_behalf_of_company_id:
            await self._log_proxy_action(
                user_id, company_id, on_behalf_of_company_id, 
                'document_upload', document.id, po_id
            )
        
        return document
    
    async def _validate_file(self, file: UploadFile, document_type: str) -> None:
        """Validate uploaded file"""
        
        # Check file size (10MB limit)
        max_size = 10 * 1024 * 1024  # 10MB
        if file.size > max_size:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Maximum size is {max_size / (1024*1024)}MB"
            )
        
        # Check file type based on document type
        allowed_types = self._get_allowed_mime_types(document_type)
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type. Allowed types: {', '.join(allowed_types)}"
            )
        
        # Reset file pointer
        await file.seek(0)
    
    def _get_allowed_mime_types(self, document_type: str) -> List[str]:
        """Get allowed MIME types for document type"""
        type_mapping = {
            'rspo_certificate': ['application/pdf', 'image/jpeg', 'image/png'],
            'catchment_polygon': ['application/json', 'application/geo+json', 'application/zip'],
            'harvest_record': ['application/pdf', 'application/vnd.ms-excel', 'text/csv'],
            'audit_report': ['application/pdf'],
            'certification': ['application/pdf', 'image/jpeg', 'image/png'],
            'map_data': ['application/json', 'application/geo+json', 'image/png', 'image/jpeg']
        }
        return type_mapping.get(document_type, ['application/pdf'])
    
    def _get_document_category(self, document_type: str) -> str:
        """Get document category from document type"""
        category_mapping = {
            'rspo_certificate': 'certificate',
            'catchment_polygon': 'map',
            'harvest_record': 'report',
            'audit_report': 'audit',
            'certification': 'certificate',
            'map_data': 'map'
        }
        return category_mapping.get(document_type, 'document')
    
    async def _upload_to_storage(self, file: UploadFile, storage_key: str) -> str:
        """Upload file to storage (S3 or local)"""
        
        if self.s3_client:
            # Upload to S3
            try:
                await file.seek(0)
                self.s3_client.upload_fileobj(
                    file.file,
                    self.bucket_name,
                    storage_key,
                    ExtraArgs={
                        'ContentType': file.content_type,
                        'ServerSideEncryption': 'AES256'
                    }
                )
                return f"s3://{self.bucket_name}/{storage_key}"
            except ClientError as e:
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to upload file to S3: {str(e)}"
                )
        else:
            # Local storage fallback
            local_path = Path("uploads") / storage_key
            local_path.parent.mkdir(parents=True, exist_ok=True)
            
            await file.seek(0)
            with open(local_path, "wb") as buffer:
                content = await file.read()
                buffer.write(content)
            
            return f"file://{local_path.absolute()}"
    
    async def _validate_proxy_permissions(
        self, 
        user_id: str, 
        proxy_company_id: str, 
        originator_company_id: str, 
        document_type: str
    ) -> None:
        """Validate that user has permission to upload on behalf of originator"""
        
        proxy_relationship = self.db.query(ProxyRelationship).filter(
            ProxyRelationship.proxy_company_id == proxy_company_id,
            ProxyRelationship.originator_company_id == originator_company_id,
            ProxyRelationship.status == 'active'
        ).first()
        
        if not proxy_relationship:
            raise HTTPException(
                status_code=403,
                detail="No active proxy relationship found"
            )
        
        # Check if document type is allowed
        if (proxy_relationship.document_types_allowed and 
            document_type not in proxy_relationship.document_types_allowed):
            raise HTTPException(
                status_code=403,
                detail=f"Not authorized to upload {document_type} documents"
            )
        
        # Check if relationship has expired
        if (proxy_relationship.expires_at and 
            proxy_relationship.expires_at < datetime.utcnow()):
            raise HTTPException(
                status_code=403,
                detail="Proxy authorization has expired"
            )
    
    async def _log_proxy_action(
        self,
        user_id: str,
        proxy_company_id: str,
        originator_company_id: str,
        action_type: str,
        document_id: Optional[str] = None,
        po_id: Optional[str] = None
    ) -> None:
        """Log proxy action for audit trail"""
        
        proxy_relationship = self.db.query(ProxyRelationship).filter(
            ProxyRelationship.proxy_company_id == proxy_company_id,
            ProxyRelationship.originator_company_id == originator_company_id,
            ProxyRelationship.status == 'active'
        ).first()
        
        if proxy_relationship:
            proxy_action = ProxyAction(
                proxy_relationship_id=proxy_relationship.id,
                po_id=po_id,
                document_id=document_id,
                action_type=action_type,
                action_description=f"Uploaded {action_type} document on behalf of originator",
                performed_by_user_id=user_id,
                action_result='success'
            )
            
            self.db.add(proxy_action)
            self.db.commit()
    
    async def get_documents(
        self,
        company_id: Optional[str] = None,
        po_id: Optional[str] = None,
        document_type: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> List[Document]:
        """Get documents with optional filters"""
        
        query = self.db.query(Document)
        
        if company_id:
            query = query.filter(Document.company_id == company_id)
        if po_id:
            query = query.filter(Document.po_id == po_id)
        if document_type:
            query = query.filter(Document.document_type == document_type)
        if user_id:
            query = query.filter(Document.uploaded_by_user_id == user_id)
        
        return query.order_by(Document.created_at.desc()).all()
    
    async def delete_document(self, document_id: str, user_id: str) -> bool:
        """Delete a document (soft delete by updating status)"""
        
        document = self.db.query(Document).filter(Document.id == document_id).first()
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Check permissions (user must be uploader or have admin rights)
        if document.uploaded_by_user_id != user_id:
            # TODO: Add admin permission check
            raise HTTPException(status_code=403, detail="Not authorized to delete this document")
        
        # Update validation status instead of hard delete
        document.validation_status = 'deleted'
        self.db.commit()
        
        return True
