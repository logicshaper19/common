"""
Document requirements service for confirmation system.
"""
from typing import List, Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session

from ..domain.models import ConfirmationContext, DocumentRequirement
from ..domain.enums import ConfirmationInterfaceType, DocumentStatus


class DocumentRequirementsService:
    """Service for managing document requirements during confirmation."""
    
    def __init__(self, db: Session):
        """Initialize with database session."""
        self.db = db
    
    def get_requirements_for_context(
        self, 
        context: ConfirmationContext
    ) -> List[DocumentRequirement]:
        """
        Get document requirements based on confirmation context.
        
        Args:
            context: Confirmation context
            
        Returns:
            List of document requirements
        """
        requirements = []
        
        # Base requirements for all confirmations
        requirements.extend(self._get_base_requirements())
        
        # Interface-specific requirements
        if context.interface_type == ConfirmationInterfaceType.ORIGIN_DATA_INTERFACE:
            requirements.extend(self._get_origin_data_requirements())
        elif context.interface_type == ConfirmationInterfaceType.TRANSFORMATION_INTERFACE:
            requirements.extend(self._get_transformation_requirements())
        elif context.interface_type == ConfirmationInterfaceType.SIMPLE_CONFIRMATION_INTERFACE:
            requirements.extend(self._get_simple_confirmation_requirements())
        
        # Company type specific requirements
        requirements.extend(self._get_company_type_requirements(context.seller_company_type))
        
        # Product category specific requirements
        requirements.extend(self._get_product_category_requirements(context.product_category))
        
        return requirements
    
    def validate_uploaded_documents(
        self,
        context: ConfirmationContext,
        uploaded_documents: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Validate that all required documents are uploaded.
        
        Args:
            context: Confirmation context
            uploaded_documents: List of uploaded document info
            
        Returns:
            Validation result with missing documents and status
        """
        requirements = self.get_requirements_for_context(context)
        required_docs = [req for req in requirements if req.is_required]
        
        # Create mapping of uploaded documents by name
        uploaded_by_name = {doc["name"]: doc for doc in uploaded_documents}
        
        missing_documents = []
        invalid_documents = []
        valid_documents = []
        
        for requirement in required_docs:
            if requirement.name not in uploaded_by_name:
                missing_documents.append({
                    "name": requirement.name,
                    "description": requirement.description,
                    "file_types": requirement.file_types
                })
            else:
                uploaded_doc = uploaded_by_name[requirement.name]
                validation_result = self._validate_single_document(uploaded_doc, requirement)
                
                if validation_result["is_valid"]:
                    valid_documents.append(uploaded_doc)
                else:
                    invalid_documents.append({
                        "name": requirement.name,
                        "errors": validation_result["errors"]
                    })
        
        return {
            "all_required_uploaded": len(missing_documents) == 0 and len(invalid_documents) == 0,
            "missing_documents": missing_documents,
            "invalid_documents": invalid_documents,
            "valid_documents": valid_documents,
            "total_required": len(required_docs),
            "total_uploaded": len(uploaded_documents)
        }
    
    def _get_base_requirements(self) -> List[DocumentRequirement]:
        """Get base document requirements for all confirmations."""
        return [
            DocumentRequirement(
                name="Company Registration",
                description="Valid company registration certificate",
                status=DocumentStatus.REQUIRED,
                file_types=["pdf", "jpg", "png"],
                max_size_mb=5,
                is_required=True
            )
        ]
    
    def _get_origin_data_requirements(self) -> List[DocumentRequirement]:
        """Get document requirements for origin data interface."""
        return [
            DocumentRequirement(
                name="RSPO Certificate",
                description="Valid RSPO certification document",
                status=DocumentStatus.REQUIRED,
                file_types=["pdf", "jpg", "png"],
                max_size_mb=10,
                is_required=True
            ),
            DocumentRequirement(
                name="Environmental Permit",
                description="Environmental compliance permit",
                status=DocumentStatus.REQUIRED,
                file_types=["pdf"],
                max_size_mb=5,
                is_required=True
            ),
            DocumentRequirement(
                name="Land Title",
                description="Proof of land ownership or lease",
                status=DocumentStatus.REQUIRED,
                file_types=["pdf", "jpg", "png"],
                max_size_mb=10,
                is_required=True
            ),
            DocumentRequirement(
                name="Quality Certificate",
                description="Product quality certification",
                status=DocumentStatus.OPTIONAL,
                file_types=["pdf", "jpg", "png"],
                max_size_mb=5,
                is_required=False
            )
        ]
    
    def _get_transformation_requirements(self) -> List[DocumentRequirement]:
        """Get document requirements for transformation interface."""
        return [
            DocumentRequirement(
                name="Processing License",
                description="Valid processing facility license",
                status=DocumentStatus.REQUIRED,
                file_types=["pdf"],
                max_size_mb=5,
                is_required=True
            ),
            DocumentRequirement(
                name="Quality Control Report",
                description="Quality control test results",
                status=DocumentStatus.REQUIRED,
                file_types=["pdf", "xlsx"],
                max_size_mb=10,
                is_required=True
            ),
            DocumentRequirement(
                name="Facility Certificate",
                description="Facility certification (ISO, HACCP, etc.)",
                status=DocumentStatus.OPTIONAL,
                file_types=["pdf", "jpg", "png"],
                max_size_mb=5,
                is_required=False
            ),
            DocumentRequirement(
                name="Input Material Certificates",
                description="Certificates for input materials used",
                status=DocumentStatus.REQUIRED,
                file_types=["pdf", "zip"],
                max_size_mb=20,
                is_required=True
            )
        ]
    
    def _get_simple_confirmation_requirements(self) -> List[DocumentRequirement]:
        """Get document requirements for simple confirmation interface."""
        return [
            DocumentRequirement(
                name="Delivery Confirmation",
                description="Confirmation of delivery capability",
                status=DocumentStatus.OPTIONAL,
                file_types=["pdf", "txt"],
                max_size_mb=2,
                is_required=False
            )
        ]
    
    def _get_company_type_requirements(self, company_type: str) -> List[DocumentRequirement]:
        """Get document requirements based on company type."""
        requirements = []
        
        if company_type == "originator":
            requirements.extend([
                DocumentRequirement(
                    name="Plantation License",
                    description="Valid plantation operating license",
                    status=DocumentStatus.REQUIRED,
                    file_types=["pdf"],
                    max_size_mb=5,
                    is_required=True
                ),
                DocumentRequirement(
                    name="Environmental Impact Assessment",
                    description="Environmental impact assessment report",
                    status=DocumentStatus.REQUIRED,
                    file_types=["pdf"],
                    max_size_mb=15,
                    is_required=True
                )
            ])
        
        elif company_type == "processor":
            requirements.extend([
                DocumentRequirement(
                    name="Manufacturing License",
                    description="Valid manufacturing/processing license",
                    status=DocumentStatus.REQUIRED,
                    file_types=["pdf"],
                    max_size_mb=5,
                    is_required=True
                ),
                DocumentRequirement(
                    name="Safety Compliance Certificate",
                    description="Workplace safety compliance certificate",
                    status=DocumentStatus.REQUIRED,
                    file_types=["pdf"],
                    max_size_mb=5,
                    is_required=True
                )
            ])
        
        elif company_type == "brand":
            requirements.extend([
                DocumentRequirement(
                    name="Brand Registration",
                    description="Brand/trademark registration certificate",
                    status=DocumentStatus.OPTIONAL,
                    file_types=["pdf", "jpg", "png"],
                    max_size_mb=5,
                    is_required=False
                )
            ])
        
        return requirements
    
    def _get_product_category_requirements(self, product_category: str) -> List[DocumentRequirement]:
        """Get document requirements based on product category."""
        requirements = []
        
        if product_category == "raw_material":
            requirements.extend([
                DocumentRequirement(
                    name="Harvest Certificate",
                    description="Certificate of harvest date and method",
                    status=DocumentStatus.REQUIRED,
                    file_types=["pdf", "jpg", "png"],
                    max_size_mb=5,
                    is_required=True
                )
            ])
        
        elif product_category == "processed_material":
            requirements.extend([
                DocumentRequirement(
                    name="Processing Certificate",
                    description="Certificate of processing method and standards",
                    status=DocumentStatus.REQUIRED,
                    file_types=["pdf"],
                    max_size_mb=5,
                    is_required=True
                )
            ])
        
        return requirements
    
    def _validate_single_document(
        self, 
        document: Dict[str, Any], 
        requirement: DocumentRequirement
    ) -> Dict[str, Any]:
        """Validate a single uploaded document against requirements."""
        errors = []
        
        # Check file type
        file_extension = document.get("file_extension", "").lower()
        if file_extension not in requirement.file_types:
            errors.append(f"Invalid file type. Expected: {', '.join(requirement.file_types)}")
        
        # Check file size
        file_size_mb = document.get("file_size_mb", 0)
        if requirement.max_size_mb and file_size_mb > requirement.max_size_mb:
            errors.append(f"File too large. Maximum size: {requirement.max_size_mb}MB")
        
        # Check if file exists and is accessible
        if not document.get("file_url"):
            errors.append("Document file is not accessible")
        
        return {
            "is_valid": len(errors) == 0,
            "errors": errors
        }
