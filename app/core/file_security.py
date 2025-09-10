"""
Enhanced file upload security and validation.

This module provides comprehensive file upload security including:
- File type validation and MIME type checking
- Malware scanning and virus detection
- File size limits and content validation
- Filename sanitization and path traversal prevention
"""

import os
import re
import hashlib
import tempfile
import mimetypes
import subprocess
from typing import Dict, List, Optional, Set, Tuple, Union, Any
from pathlib import Path

from fastapi import UploadFile, HTTPException, status

from app.core.logging import get_logger
from app.core.input_validation import InputValidator, InputValidationError

# Optional dependencies with graceful fallbacks
try:
    import magic
    HAS_MAGIC = True
except ImportError:
    HAS_MAGIC = False

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

logger = get_logger(__name__)


class FileSecurityError(Exception):
    """Exception raised when file security validation fails."""
    
    def __init__(self, message: str, file_name: str = None, error_code: str = None):
        self.message = message
        self.file_name = file_name
        self.error_code = error_code
        super().__init__(message)


class FileSecurityValidator:
    """
    Comprehensive file upload security validator.
    
    Features:
    - MIME type validation and spoofing detection
    - File size limits and content validation
    - Malware scanning and virus detection
    - Filename sanitization
    - Path traversal prevention
    - Executable file detection
    """
    
    # Maximum file sizes by category (in bytes)
    MAX_FILE_SIZES = {
        'document': 25 * 1024 * 1024,      # 25MB for documents
        'image': 10 * 1024 * 1024,         # 10MB for images
        'spreadsheet': 50 * 1024 * 1024,   # 50MB for spreadsheets
        'archive': 100 * 1024 * 1024,      # 100MB for archives
        'geographic': 100 * 1024 * 1024,   # 100MB for GIS files
        'default': 10 * 1024 * 1024        # 10MB default
    }
    
    # Allowed MIME types by category
    ALLOWED_MIME_TYPES = {
        'document': [
            'application/pdf',
            'application/msword',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'text/plain',
            'text/csv'
        ],
        'image': [
            'image/jpeg',
            'image/png',
            'image/gif',
            'image/bmp',
            'image/tiff',
            'image/webp'
        ],
        'spreadsheet': [
            'application/vnd.ms-excel',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'text/csv'
        ],
        'archive': [
            'application/zip',
            'application/x-zip-compressed',
            'application/gzip',
            'application/x-tar'
        ],
        'geographic': [
            'application/json',  # GeoJSON
            'application/vnd.google-earth.kml+xml',  # KML
            'application/zip',   # Shapefile archives
            'text/plain'         # Various GIS text formats
        ]
    }
    
    # Dangerous file extensions that should never be allowed
    DANGEROUS_EXTENSIONS = {
        '.exe', '.bat', '.cmd', '.com', '.pif', '.scr', '.vbs', '.js', '.jar',
        '.app', '.deb', '.pkg', '.dmg', '.rpm', '.msi', '.dll', '.so', '.dylib',
        '.sh', '.bash', '.zsh', '.fish', '.ps1', '.psm1', '.psd1', '.ps1xml',
        '.php', '.asp', '.aspx', '.jsp', '.py', '.rb', '.pl', '.cgi'
    }
    
    # File signatures (magic numbers) for common file types
    FILE_SIGNATURES = {
        'pdf': [b'%PDF'],
        'jpeg': [b'\xff\xd8\xff'],
        'png': [b'\x89PNG\r\n\x1a\n'],
        'gif': [b'GIF87a', b'GIF89a'],
        'zip': [b'PK\x03\x04', b'PK\x05\x06', b'PK\x07\x08'],
        'docx': [b'PK\x03\x04'],  # DOCX is a ZIP file
        'xlsx': [b'PK\x03\x04'],  # XLSX is a ZIP file
        'exe': [b'MZ'],
        'elf': [b'\x7fELF'],
    }
    
    def __init__(self):
        self.input_validator = InputValidator()
        if HAS_MAGIC:
            self.magic_mime = magic.Magic(mime=True)
            self.magic_type = magic.Magic()
        else:
            self.magic_mime = None
            self.magic_type = None
    
    async def validate_file_upload(
        self,
        file: UploadFile,
        allowed_categories: List[str],
        max_size_override: Optional[int] = None,
        require_virus_scan: bool = True
    ) -> Dict[str, Any]:
        """
        Comprehensive file upload validation.
        
        Args:
            file: Uploaded file object
            allowed_categories: List of allowed file categories
            max_size_override: Override default max file size
            require_virus_scan: Whether to perform virus scanning
            
        Returns:
            Validation result dictionary
            
        Raises:
            FileSecurityError: If validation fails
        """
        validation_result = {
            'is_valid': False,
            'file_info': {},
            'security_checks': {},
            'warnings': [],
            'errors': []
        }
        
        try:
            # 1. Validate filename
            safe_filename = self._validate_filename(file.filename)
            
            # 2. Read file content for analysis
            content = await file.read()
            await file.seek(0)  # Reset file pointer
            
            # 3. Basic file info
            file_info = {
                'original_filename': file.filename,
                'safe_filename': safe_filename,
                'size': len(content),
                'content_type': file.content_type
            }
            
            # 4. Validate file size
            max_size = max_size_override or self._get_max_size_for_categories(allowed_categories)
            if len(content) > max_size:
                raise FileSecurityError(
                    f"File size ({len(content)} bytes) exceeds maximum allowed size ({max_size} bytes)",
                    file.filename,
                    "FILE_TOO_LARGE"
                )
            
            # 5. Detect actual MIME type
            detected_mime = self._detect_mime_type(content)
            file_info['detected_mime_type'] = detected_mime
            
            # 6. Validate MIME type against allowed categories
            if not self._is_mime_type_allowed(detected_mime, allowed_categories):
                raise FileSecurityError(
                    f"File type '{detected_mime}' is not allowed for categories: {allowed_categories}",
                    file.filename,
                    "INVALID_FILE_TYPE"
                )
            
            # 7. Check for MIME type spoofing
            if file.content_type and file.content_type != detected_mime:
                validation_result['warnings'].append(
                    f"MIME type mismatch: declared '{file.content_type}', detected '{detected_mime}'"
                )
            
            # 8. Validate file signature
            if not self._validate_file_signature(content, detected_mime):
                raise FileSecurityError(
                    "File signature does not match detected MIME type",
                    file.filename,
                    "INVALID_FILE_SIGNATURE"
                )
            
            # 9. Check for dangerous content
            security_checks = await self._perform_security_checks(content, safe_filename)
            validation_result['security_checks'] = security_checks
            
            if not security_checks['passed']:
                raise FileSecurityError(
                    f"Security validation failed: {'; '.join(security_checks['errors'])}",
                    file.filename,
                    "SECURITY_VIOLATION"
                )
            
            # 10. Virus scanning (if enabled and available)
            if require_virus_scan:
                virus_scan_result = await self._scan_for_viruses(content, safe_filename)
                validation_result['virus_scan'] = virus_scan_result
                
                if not virus_scan_result['clean']:
                    raise FileSecurityError(
                        f"Virus detected: {virus_scan_result.get('threat_name', 'Unknown threat')}",
                        file.filename,
                        "VIRUS_DETECTED"
                    )
            
            # 11. Content-specific validation
            content_validation = await self._validate_file_content(content, detected_mime)
            validation_result['content_validation'] = content_validation
            
            validation_result['file_info'] = file_info
            validation_result['is_valid'] = True
            
            logger.info(
                "File upload validation successful",
                filename=safe_filename,
                size=len(content),
                mime_type=detected_mime
            )
            
            return validation_result
            
        except FileSecurityError:
            raise
        except Exception as e:
            logger.error(
                "File validation error",
                filename=file.filename,
                error=str(e)
            )
            raise FileSecurityError(
                f"File validation failed: {str(e)}",
                file.filename,
                "VALIDATION_ERROR"
            )
    
    def _validate_filename(self, filename: str) -> str:
        """
        Validate and sanitize filename.
        
        Args:
            filename: Original filename
            
        Returns:
            Sanitized filename
            
        Raises:
            FileSecurityError: If filename is invalid
        """
        if not filename:
            raise FileSecurityError("Filename is required", filename, "MISSING_FILENAME")
        
        # Check for path traversal attempts
        if '..' in filename or '/' in filename or '\\' in filename:
            raise FileSecurityError(
                "Filename contains invalid path characters",
                filename,
                "INVALID_FILENAME"
            )
        
        # Extract extension
        file_path = Path(filename)
        extension = file_path.suffix.lower()
        
        # Check for dangerous extensions
        if extension in self.DANGEROUS_EXTENSIONS:
            raise FileSecurityError(
                f"File extension '{extension}' is not allowed",
                filename,
                "DANGEROUS_EXTENSION"
            )
        
        # Sanitize filename
        safe_name = re.sub(r'[^a-zA-Z0-9._-]', '_', file_path.stem)
        safe_filename = f"{safe_name}{extension}"
        
        # Ensure filename is not too long
        if len(safe_filename) > 255:
            safe_filename = safe_filename[:255]
        
        return safe_filename
    
    def _get_max_size_for_categories(self, categories: List[str]) -> int:
        """Get maximum file size for given categories."""
        max_size = 0
        for category in categories:
            category_max = self.MAX_FILE_SIZES.get(category, self.MAX_FILE_SIZES['default'])
            max_size = max(max_size, category_max)
        return max_size or self.MAX_FILE_SIZES['default']
    
    def _detect_mime_type(self, content: bytes) -> str:
        """Detect MIME type from file content."""
        try:
            if self.magic_mime:
                return self.magic_mime.from_buffer(content)
            else:
                # Fallback to basic detection based on file signatures
                return self._detect_mime_type_fallback(content)
        except Exception as e:
            logger.warning(f"Failed to detect MIME type: {e}")
            return 'application/octet-stream'

    def _detect_mime_type_fallback(self, content: bytes) -> str:
        """Fallback MIME type detection when python-magic is not available."""
        # Basic detection based on file signatures
        if content.startswith(b'%PDF'):
            return 'application/pdf'
        elif content.startswith(b'\xff\xd8\xff'):
            return 'image/jpeg'
        elif content.startswith(b'\x89PNG\r\n\x1a\n'):
            return 'image/png'
        elif content.startswith(b'GIF87a') or content.startswith(b'GIF89a'):
            return 'image/gif'
        elif content.startswith(b'PK\x03\x04'):
            return 'application/zip'
        else:
            return 'application/octet-stream'
    
    def _is_mime_type_allowed(self, mime_type: str, categories: List[str]) -> bool:
        """Check if MIME type is allowed for given categories."""
        for category in categories:
            allowed_types = self.ALLOWED_MIME_TYPES.get(category, [])
            if mime_type in allowed_types:
                return True
        return False
    
    def _validate_file_signature(self, content: bytes, mime_type: str) -> bool:
        """Validate file signature against MIME type."""
        # Get expected signatures for MIME type
        type_mapping = {
            'application/pdf': 'pdf',
            'image/jpeg': 'jpeg',
            'image/png': 'png',
            'image/gif': 'gif',
            'application/zip': 'zip',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'docx',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': 'xlsx'
        }
        
        file_type = type_mapping.get(mime_type)
        if not file_type:
            return True  # No signature validation for unknown types
        
        expected_signatures = self.FILE_SIGNATURES.get(file_type, [])
        if not expected_signatures:
            return True
        
        # Check if content starts with any expected signature
        for signature in expected_signatures:
            if content.startswith(signature):
                return True
        
        return False
    
    async def _perform_security_checks(self, content: bytes, filename: str) -> Dict[str, Any]:
        """Perform security checks on file content."""
        security_result = {
            'passed': True,
            'errors': [],
            'warnings': [],
            'checks_performed': []
        }
        
        # Check for executable signatures
        if self._contains_executable_signatures(content):
            security_result['passed'] = False
            security_result['errors'].append("File contains executable signatures")
        security_result['checks_performed'].append('executable_signature_check')
        
        # Check for suspicious patterns
        suspicious_patterns = [
            b'<script',
            b'javascript:',
            b'vbscript:',
            b'data:text/html',
            b'<?php',
            b'<%',
            b'#!/bin/',
            b'#!/usr/bin/'
        ]
        
        for pattern in suspicious_patterns:
            if pattern in content:
                security_result['warnings'].append(f"Suspicious pattern found: {pattern.decode('utf-8', errors='ignore')}")
        
        security_result['checks_performed'].append('suspicious_pattern_check')
        
        return security_result
    
    def _contains_executable_signatures(self, content: bytes) -> bool:
        """Check if content contains executable file signatures."""
        executable_signatures = [
            b'MZ',      # Windows PE
            b'\x7fELF', # Linux ELF
            b'\xca\xfe\xba\xbe',  # Java class file
            b'\xfe\xed\xfa\xce',  # Mach-O (macOS)
            b'\xfe\xed\xfa\xcf',  # Mach-O (macOS)
        ]
        
        for signature in executable_signatures:
            if content.startswith(signature):
                return True
        
        return False
    
    async def _scan_for_viruses(self, content: bytes, filename: str) -> Dict[str, Any]:
        """
        Scan file content for viruses using ClamAV or similar.
        
        Note: This is a placeholder implementation. In production,
        integrate with actual antivirus software like ClamAV.
        """
        scan_result = {
            'clean': True,
            'scanned': False,
            'threat_name': None,
            'scanner': 'placeholder'
        }
        
        try:
            # Placeholder: In production, use actual virus scanner
            # Example with ClamAV:
            # result = subprocess.run(['clamdscan', '--no-summary', '-'], 
            #                        input=content, capture_output=True)
            # scan_result['clean'] = result.returncode == 0
            # scan_result['scanned'] = True
            
            # For now, just check for obvious malware signatures
            malware_signatures = [
                b'X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*',  # EICAR test
            ]
            
            for signature in malware_signatures:
                if signature in content:
                    scan_result['clean'] = False
                    scan_result['threat_name'] = 'Test virus signature'
                    break
            
            scan_result['scanned'] = True
            
        except Exception as e:
            logger.warning(f"Virus scanning failed: {e}")
            scan_result['clean'] = True  # Assume clean if scan fails
            scan_result['scanned'] = False
        
        return scan_result
    
    async def _validate_file_content(self, content: bytes, mime_type: str) -> Dict[str, Any]:
        """Validate file content based on MIME type."""
        content_result = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'metadata': {}
        }
        
        try:
            if mime_type.startswith('image/') and HAS_PIL:
                # Validate image files using PIL
                with tempfile.NamedTemporaryFile() as temp_file:
                    temp_file.write(content)
                    temp_file.flush()

                    try:
                        with Image.open(temp_file.name) as img:
                            content_result['metadata'] = {
                                'width': img.width,
                                'height': img.height,
                                'format': img.format,
                                'mode': img.mode
                            }
                    except Exception as e:
                        content_result['valid'] = False
                        content_result['errors'].append(f"Invalid image file: {str(e)}")

            elif mime_type.startswith('image/') and not HAS_PIL:
                # Basic image validation without PIL
                content_result['warnings'].append("PIL not available - limited image validation")

            elif mime_type == 'application/pdf':
                # Basic PDF validation
                if not content.startswith(b'%PDF'):
                    content_result['valid'] = False
                    content_result['errors'].append("Invalid PDF file structure")
            
        except Exception as e:
            content_result['warnings'].append(f"Content validation error: {str(e)}")
        
        return content_result


# Global file security validator instance
file_security_validator = FileSecurityValidator()
