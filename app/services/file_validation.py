"""
Enhanced File Validation Service
Provides comprehensive file validation including content inspection, security checks, and format validation
"""
import os
import hashlib
import mimetypes
from typing import Dict, List, Optional, Tuple
from fastapi import HTTPException, UploadFile
import magic
import logging

logger = logging.getLogger(__name__)

class FileValidationError(Exception):
    """Custom exception for file validation errors"""
    pass

class SecurityValidationError(FileValidationError):
    """Custom exception for security-related validation errors"""
    pass

class FileValidator:
    """
    Comprehensive file validator with security checks
    """
    
    # Maximum file sizes by document type (in bytes)
    MAX_FILE_SIZES = {
        'rspo_certificate': 10 * 1024 * 1024,  # 10MB
        'bci_certificate': 10 * 1024 * 1024,   # 10MB
        'catchment_polygon': 50 * 1024 * 1024, # 50MB for geographic files
        'harvest_record': 25 * 1024 * 1024,    # 25MB for spreadsheets
        'audit_report': 20 * 1024 * 1024,      # 20MB
        'cooperative_license': 10 * 1024 * 1024,
        'member_list': 15 * 1024 * 1024,
        'farm_registration': 10 * 1024 * 1024,
        'processing_license': 10 * 1024 * 1024,
        'quality_certificate': 10 * 1024 * 1024,
        'mining_license': 10 * 1024 * 1024,
        'conflict_minerals_report': 20 * 1024 * 1024,
        'environmental_permit': 15 * 1024 * 1024,
        'default': 10 * 1024 * 1024  # 10MB default
    }
    
    # Allowed MIME types by document type
    ALLOWED_MIME_TYPES = {
        'rspo_certificate': ['application/pdf', 'image/jpeg', 'image/png'],
        'bci_certificate': ['application/pdf', 'image/jpeg', 'image/png'],
        'catchment_polygon': [
            'application/vnd.google-earth.kml+xml',
            'application/zip',  # For shapefiles
            'application/json',  # For GeoJSON
            'application/pdf'
        ],
        'harvest_record': [
            'application/pdf',
            'application/vnd.ms-excel',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'text/csv'
        ],
        'audit_report': ['application/pdf'],
        'cooperative_license': ['application/pdf', 'image/jpeg', 'image/png'],
        'member_list': [
            'application/pdf',
            'application/vnd.ms-excel',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'text/csv'
        ],
        'default': ['application/pdf', 'image/jpeg', 'image/png']
    }
    
    # Dangerous file extensions that should never be allowed
    DANGEROUS_EXTENSIONS = {
        '.exe', '.bat', '.cmd', '.com', '.pif', '.scr', '.vbs', '.js', '.jar',
        '.app', '.deb', '.pkg', '.dmg', '.rpm', '.msi', '.dll', '.so', '.dylib'
    }
    
    # Magic number signatures for common file types
    MAGIC_SIGNATURES = {
        'application/pdf': [b'%PDF'],
        'image/jpeg': [b'\xff\xd8\xff'],
        'image/png': [b'\x89PNG\r\n\x1a\n'],
        'application/zip': [b'PK\x03\x04', b'PK\x05\x06', b'PK\x07\x08'],
        'application/vnd.ms-excel': [b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1'],
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': [b'PK\x03\x04'],
    }

    def __init__(self):
        """Initialize the file validator"""
        self.magic_mime = magic.Magic(mime=True)
        
    async def validate_file(
        self, 
        file: UploadFile, 
        document_type: str,
        additional_checks: bool = True
    ) -> Dict[str, any]:
        """
        Comprehensive file validation
        
        Args:
            file: The uploaded file
            document_type: Type of document being uploaded
            additional_checks: Whether to perform additional security checks
            
        Returns:
            Dict containing validation results and metadata
            
        Raises:
            FileValidationError: If validation fails
            SecurityValidationError: If security checks fail
        """
        validation_result = {
            'is_valid': False,
            'file_info': {},
            'security_checks': {},
            'content_validation': {},
            'errors': [],
            'warnings': []
        }
        
        try:
            # Basic file info
            file_info = await self._get_file_info(file)
            validation_result['file_info'] = file_info
            
            # Security checks
            if additional_checks:
                security_result = await self._perform_security_checks(file, file_info)
                validation_result['security_checks'] = security_result
                
                if not security_result['passed']:
                    validation_result['errors'].extend(security_result['errors'])
                    raise SecurityValidationError("File failed security checks")
            
            # File size validation
            await self._validate_file_size(file, document_type)
            
            # MIME type validation
            await self._validate_mime_type(file, document_type, file_info)
            
            # Content validation
            content_result = await self._validate_file_content(file, document_type)
            validation_result['content_validation'] = content_result
            
            if not content_result['valid']:
                validation_result['errors'].extend(content_result['errors'])
                validation_result['warnings'].extend(content_result.get('warnings', []))
            
            # If we get here, validation passed
            validation_result['is_valid'] = True
            
        except (FileValidationError, SecurityValidationError) as e:
            validation_result['errors'].append(str(e))
            logger.warning(f"File validation failed: {str(e)}")
            
        except Exception as e:
            validation_result['errors'].append(f"Unexpected validation error: {str(e)}")
            logger.error(f"Unexpected file validation error: {str(e)}")
            
        finally:
            # Reset file position
            await file.seek(0)
            
        return validation_result
    
    async def _get_file_info(self, file: UploadFile) -> Dict[str, any]:
        """Get basic file information"""
        # Read file content for analysis
        content = await file.read()
        await file.seek(0)
        
        # Calculate file hash
        file_hash = hashlib.sha256(content).hexdigest()
        
        # Get MIME type using python-magic
        detected_mime = self.magic_mime.from_buffer(content)
        
        # Get file extension
        filename = file.filename or ""
        file_extension = os.path.splitext(filename)[1].lower()
        
        return {
            'filename': filename,
            'size': len(content),
            'extension': file_extension,
            'declared_mime_type': file.content_type,
            'detected_mime_type': detected_mime,
            'sha256_hash': file_hash
        }
    
    async def _perform_security_checks(self, file: UploadFile, file_info: Dict) -> Dict[str, any]:
        """Perform security checks on the file"""
        security_result = {
            'passed': True,
            'errors': [],
            'checks_performed': []
        }
        
        # Check for dangerous file extensions
        if file_info['extension'] in self.DANGEROUS_EXTENSIONS:
            security_result['passed'] = False
            security_result['errors'].append(f"Dangerous file extension: {file_info['extension']}")
        security_result['checks_performed'].append('dangerous_extension_check')
        
        # Check MIME type spoofing
        declared_mime = file_info['declared_mime_type']
        detected_mime = file_info['detected_mime_type']
        
        if declared_mime != detected_mime:
            # Some tolerance for similar types
            if not self._are_mime_types_compatible(declared_mime, detected_mime):
                security_result['passed'] = False
                security_result['errors'].append(
                    f"MIME type mismatch: declared '{declared_mime}', detected '{detected_mime}'"
                )
        security_result['checks_performed'].append('mime_type_spoofing_check')
        
        # Check file signature (magic numbers)
        content = await file.read(1024)  # Read first 1KB
        await file.seek(0)
        
        if not self._validate_file_signature(content, detected_mime):
            security_result['passed'] = False
            security_result['errors'].append("File signature does not match detected MIME type")
        security_result['checks_performed'].append('file_signature_check')
        
        # Check for embedded executables (basic check)
        if self._contains_executable_signatures(content):
            security_result['passed'] = False
            security_result['errors'].append("File contains suspicious executable signatures")
        security_result['checks_performed'].append('executable_signature_check')
        
        return security_result
    
    async def _validate_file_size(self, file: UploadFile, document_type: str) -> None:
        """Validate file size against limits"""
        content = await file.read()
        await file.seek(0)
        
        file_size = len(content)
        max_size = self.MAX_FILE_SIZES.get(document_type, self.MAX_FILE_SIZES['default'])
        
        if file_size > max_size:
            raise FileValidationError(
                f"File size {file_size} bytes exceeds maximum allowed size "
                f"{max_size} bytes for document type '{document_type}'"
            )
        
        if file_size == 0:
            raise FileValidationError("File is empty")
    
    async def _validate_mime_type(self, file: UploadFile, document_type: str, file_info: Dict) -> None:
        """Validate MIME type against allowed types"""
        allowed_types = self.ALLOWED_MIME_TYPES.get(document_type, self.ALLOWED_MIME_TYPES['default'])
        detected_mime = file_info['detected_mime_type']
        
        if detected_mime not in allowed_types:
            raise FileValidationError(
                f"File type '{detected_mime}' not allowed for document type '{document_type}'. "
                f"Allowed types: {', '.join(allowed_types)}"
            )
    
    async def _validate_file_content(self, file: UploadFile, document_type: str) -> Dict[str, any]:
        """Validate file content based on document type"""
        content_result = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'metadata': {}
        }
        
        # Document-specific content validation
        if document_type in ['rspo_certificate', 'bci_certificate']:
            await self._validate_certificate_content(file, content_result)
        elif document_type == 'catchment_polygon':
            await self._validate_geographic_content(file, content_result)
        elif document_type in ['harvest_record', 'member_list']:
            await self._validate_spreadsheet_content(file, content_result)
        
        return content_result
    
    async def _validate_certificate_content(self, file: UploadFile, result: Dict) -> None:
        """Validate certificate file content"""
        # Basic PDF validation for certificates
        content = await file.read(1024)
        await file.seek(0)
        
        if content.startswith(b'%PDF'):
            # Basic PDF structure check
            if b'%%EOF' not in await file.read():
                result['warnings'].append("PDF file may be corrupted or incomplete")
            await file.seek(0)
        
        # Additional certificate-specific checks could be added here
        # e.g., checking for specific certificate authorities, expiry dates, etc.
    
    async def _validate_geographic_content(self, file: UploadFile, result: Dict) -> None:
        """Validate geographic file content"""
        content = await file.read()
        await file.seek(0)
        
        # Basic validation for different geographic formats
        if b'<kml' in content.lower() or b'<?xml' in content:
            # KML file validation
            if b'<coordinates>' not in content.lower():
                result['warnings'].append("KML file may not contain coordinate data")
        elif content.startswith(b'PK'):
            # Potentially a shapefile (ZIP format)
            result['metadata']['format'] = 'shapefile_zip'
        elif content.startswith(b'{') and b'"coordinates"' in content:
            # GeoJSON validation
            result['metadata']['format'] = 'geojson'
    
    async def _validate_spreadsheet_content(self, file: UploadFile, result: Dict) -> None:
        """Validate spreadsheet file content"""
        # Basic validation for spreadsheet files
        content = await file.read(1024)
        await file.seek(0)
        
        if content.startswith(b'PK'):
            # Excel format (XLSX)
            result['metadata']['format'] = 'xlsx'
        elif content.startswith(b'\xd0\xcf\x11\xe0'):
            # Old Excel format (XLS)
            result['metadata']['format'] = 'xls'
        elif b',' in content:
            # Likely CSV
            result['metadata']['format'] = 'csv'
    
    def _are_mime_types_compatible(self, declared: str, detected: str) -> bool:
        """Check if declared and detected MIME types are compatible"""
        # Some common compatible MIME type pairs
        compatible_pairs = [
            ('application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 'application/zip'),
            ('application/vnd.google-earth.kml+xml', 'text/xml'),
            ('text/csv', 'text/plain'),
        ]
        
        return (declared, detected) in compatible_pairs or (detected, declared) in compatible_pairs
    
    def _validate_file_signature(self, content: bytes, mime_type: str) -> bool:
        """Validate file signature against MIME type"""
        signatures = self.MAGIC_SIGNATURES.get(mime_type, [])
        if not signatures:
            return True  # No signature check available
        
        return any(content.startswith(sig) for sig in signatures)
    
    def _contains_executable_signatures(self, content: bytes) -> bool:
        """Check for embedded executable signatures"""
        executable_signatures = [
            b'MZ',  # DOS/Windows executable
            b'\x7fELF',  # Linux executable
            b'\xfe\xed\xfa',  # Mach-O executable (macOS)
        ]
        
        return any(sig in content for sig in executable_signatures)
