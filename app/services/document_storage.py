"""
Enhanced Document Storage Service
Handles file uploads, storage, and document management with comprehensive security,
transaction management, and error handling
"""
import os
import uuid
import mimetypes
import logging
from typing import Optional, List, Dict, Any, BinaryIO, Tuple
from datetime import datetime, timedelta
from pathlib import Path

import boto3
from botocore.exceptions import ClientError
from fastapi import UploadFile, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.core.config import settings
from app.models.document import Document, ProxyRelationship, ProxyAction
from app.models.user import User
from app.models.company import Company
from app.services.file_validation import FileValidator
from app.exceptions.document_exceptions import (
    DocumentError, DocumentValidationError, DocumentSecurityError,
    DocumentStorageError, DocumentNotFoundError, DocumentAccessDeniedError,
    ProxyAuthorizationError, DocumentTransactionError, DocumentTransactionContext
)
from app.core.logging import get_logger

logger = get_logger(__name__)

logger = logging.getLogger(__name__)


class DocumentStorageService:
    """Enhanced service for handling document uploads, storage, and management with security"""

    def __init__(self, db: Session):
        self.db = db
        self.s3_client = None
        self.bucket_name = getattr(settings, 'AWS_S3_BUCKET', 'common-supply-chain-documents')
        self.file_validator = FileValidator()

        # Initialize S3 client if AWS credentials are available
        if hasattr(settings, 'AWS_ACCESS_KEY_ID') and settings.AWS_ACCESS_KEY_ID:
            try:
                self.s3_client = boto3.client(
                    's3',
                    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                    region_name=getattr(settings, 'AWS_REGION', 'us-east-1')
                )
                # Test S3 connection
                self.s3_client.head_bucket(Bucket=self.bucket_name)
                logger.info("S3 client initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize S3 client: {e}. Falling back to local storage.")
                self.s3_client = None
    
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
        compliance_regulations: Optional[List[str]] = None,
        perform_security_checks: bool = True
    ) -> Document:
        """
        Upload a document with comprehensive validation and transaction management

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
            perform_security_checks: Whether to perform security validation

        Returns:
            Document: Created document record

        Raises:
            DocumentValidationError: If file validation fails
            DocumentSecurityError: If security checks fail
            ProxyAuthorizationError: If proxy permissions are invalid
            DocumentStorageError: If storage operations fail
            DocumentTransactionError: If database operations fail
        """

        try:
            # Use transaction context for automatic rollback on failure
            with DocumentTransactionContext(self.db, self) as tx_context:

                # 1. Comprehensive file validation
                validation_result = await self.file_validator.validate_file(
                    file, document_type, perform_security_checks
                )

                if not validation_result['is_valid']:
                    if validation_result['security_checks'].get('errors'):
                        raise DocumentSecurityError(
                            "File failed security validation",
                            security_issues=validation_result['security_checks']['errors'],
                            details=validation_result
                        )
                    else:
                        raise DocumentValidationError(
                            "File validation failed",
                            validation_errors=validation_result['errors'],
                            details=validation_result
                        )

                # 2. Check proxy permissions if uploading on behalf of another company
                proxy_relationship_id = None
                if on_behalf_of_company_id:
                    proxy_relationship_id = await self._validate_proxy_permissions(
                        user_id, company_id, on_behalf_of_company_id, document_type
                    )

                # 3. Check for existing documents (prevent duplicates)
                await self._check_duplicate_document(
                    po_id, document_type, company_id, on_behalf_of_company_id
                )

                # 4. Generate unique file name and storage key
                file_info = validation_result['file_info']
                file_extension = file_info['extension'] or Path(file.filename or '').suffix
                unique_filename = f"{uuid.uuid4()}{file_extension}"
                storage_key = f"documents/{document_type}/{datetime.now().strftime('%Y/%m')}/{unique_filename}"

                # 5. Upload to storage
                storage_url = await self._upload_to_storage(file, storage_key)
                tx_context.track_storage_operation('upload', storage_key)

                # 6. Create document record
                document = Document(
                    po_id=po_id,
                    company_id=company_id,
                    uploaded_by_user_id=user_id,
                    document_type=document_type,
                    file_name=unique_filename,
                    original_file_name=file.filename or 'unknown',
                    file_size=file_info['size'],
                    mime_type=file_info['detected_mime_type'],
                    storage_url=storage_url,
                    storage_key=storage_key,
                    is_proxy_upload=bool(on_behalf_of_company_id),
                    on_behalf_of_company_id=on_behalf_of_company_id,
                    proxy_authorization_id=proxy_relationship_id,
                    document_category=self._get_document_category(document_type),
                    compliance_regulations=compliance_regulations or [],
                    tier_level=tier_level,
                    sector_id=sector_id,
                    validation_status='valid',
                    validation_metadata=validation_result.get('content_validation', {})
                )

                # 7. Save document to database
                self.db.add(document)
                self.db.flush()  # Get the ID without committing

                # 8. Log proxy action if applicable
                if on_behalf_of_company_id and proxy_relationship_id:
                    await self._log_proxy_action(
                        proxy_relationship_id, user_id, 'document_upload',
                        document.id, po_id
                    )

                # Transaction will be committed by context manager
                return document

        except DocumentError:
            # Re-raise document-specific errors
            raise
        except Exception as e:
            # Convert unexpected errors to DocumentTransactionError
            logger.error(f"Unexpected error during document upload: {str(e)}")
            raise DocumentTransactionError(
                f"Document upload failed: {str(e)}",
                operation="upload_document"
            )

    async def _check_duplicate_document(
        self,
        po_id: Optional[str],
        document_type: str,
        company_id: str,
        on_behalf_of_company_id: Optional[str]
    ) -> None:
        """Check for existing documents to prevent duplicates"""
        query = self.db.query(Document).filter(
            Document.document_type == document_type,
            Document.is_deleted == False,
            Document.validation_status != 'deleted'
        )

        if po_id:
            query = query.filter(Document.po_id == po_id)

        # Check based on who the document is for
        target_company_id = on_behalf_of_company_id or company_id
        query = query.filter(
            or_(
                Document.company_id == target_company_id,
                Document.on_behalf_of_company_id == target_company_id
            )
        )

        existing_doc = query.first()
        if existing_doc:
            raise DocumentValidationError(
                f"Document of type '{document_type}' already exists for this context",
                details={
                    "existing_document_id": str(existing_doc.id),
                    "po_id": po_id,
                    "company_id": target_company_id
                }
            )

    def _get_document_category(self, document_type: str) -> str:
        """Get document category based on document type"""
        category_mapping = {
            'rspo_certificate': 'certificate',
            'bci_certificate': 'certificate',
            'cooperative_license': 'certificate',
            'farm_registration': 'certificate',
            'processing_license': 'certificate',
            'quality_certificate': 'certificate',
            'mining_license': 'certificate',
            'environmental_permit': 'certificate',
            'catchment_polygon': 'map',
            'harvest_record': 'report',
            'audit_report': 'report',
            'conflict_minerals_report': 'report',
            'member_list': 'report'
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
    ) -> str:
        """
        Validate that user has permission to upload on behalf of originator

        Returns:
            str: The proxy relationship ID if valid

        Raises:
            ProxyAuthorizationError: If proxy permissions are invalid
        """

        proxy_relationship = self.db.query(ProxyRelationship).filter(
            ProxyRelationship.proxy_company_id == proxy_company_id,
            ProxyRelationship.originator_company_id == originator_company_id,
            ProxyRelationship.status == 'active'
        ).first()

        if not proxy_relationship:
            raise ProxyAuthorizationError(
                proxy_company_id, originator_company_id,
                "No active proxy relationship found"
            )

        # Check if document type is allowed
        if (proxy_relationship.document_types_allowed and
            document_type not in proxy_relationship.document_types_allowed):
            raise ProxyAuthorizationError(
                proxy_company_id, originator_company_id,
                f"Not authorized to upload {document_type} documents"
            )

        # Check if relationship has expired
        if (proxy_relationship.expires_at and
            proxy_relationship.expires_at < datetime.now(datetime.timezone.utc).replace(tzinfo=None)):
            raise ProxyAuthorizationError(
                proxy_company_id, originator_company_id,
                "Proxy authorization has expired"
            )

        return str(proxy_relationship.id)

    async def delete_file(self, storage_key: str) -> bool:
        """
        Delete file from storage (for rollback purposes)

        Args:
            storage_key: The storage key/path of the file to delete

        Returns:
            bool: True if deletion was successful, False otherwise
        """
        try:
            if self.s3_client:
                # Delete from S3
                self.s3_client.delete_object(Bucket=self.bucket_name, Key=storage_key)
                logger.info(f"Deleted file from S3: {storage_key}")
                return True
            else:
                # Delete from local storage
                local_path = Path("uploads") / storage_key
                if local_path.exists():
                    local_path.unlink()
                    logger.info(f"Deleted local file: {local_path}")
                    return True
                else:
                    logger.warning(f"Local file not found for deletion: {local_path}")
                    return False

        except ClientError as e:
            logger.error(f"Failed to delete file from S3: {storage_key}, error: {e}")
            return False
        except Exception as e:
            logger.error(f"Failed to delete file: {storage_key}, error: {e}")
            return False

    async def _log_proxy_action(
        self,
        proxy_relationship_id: str,
        user_id: str,
        action_type: str,
        document_id: Optional[str] = None,
        po_id: Optional[str] = None
    ) -> None:
        """Log proxy action for audit trail"""

        proxy_action = ProxyAction(
            proxy_relationship_id=proxy_relationship_id,
            po_id=po_id,
            document_id=document_id,
            action_type=action_type,
            action_description=f"Performed {action_type} on behalf of originator",
            performed_by_user_id=user_id,
            action_result='success'
        )

        self.db.add(proxy_action)
        # Note: Don't commit here, let the transaction context handle it
    
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
            # Admin override: check if user is admin
            from app.models.user import User
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user or user.role != 'admin':
                raise HTTPException(status_code=403, detail="Not authorized to delete this document")

            # Log admin override for audit trail
            logger.info(
                "Admin override: deleting document uploaded by different user",
                admin_user_id=str(user_id),
                document_id=str(document_id),
                original_uploader_id=str(document.uploaded_by_user_id)
            )
        
        # Update validation status instead of hard delete
        document.validation_status = 'deleted'
        self.db.commit()
        
        return True

    async def get_documents_by_po(self, po_id: str) -> List[Document]:
        """
        Get all documents for a specific purchase order

        Args:
            po_id: Purchase order ID

        Returns:
            List of documents associated with the PO
        """
        return await self.get_documents(po_id=po_id)
