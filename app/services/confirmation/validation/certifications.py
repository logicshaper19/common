"""
Certifications validation service.
"""
from typing import Any, List, Dict, Set
from datetime import datetime, date

from ..domain.models import ValidationResult
from ..domain.enums import CertificationType
from .base import ValidationService


class CertificationsValidator(ValidationService):
    """Validator for certifications."""
    
    def __init__(self, db):
        """Initialize with certification standards."""
        super().__init__(db)
        
        # Standard certification types
        self.standard_certifications = {cert.value for cert in CertificationType}
        
        # High-value certifications that provide extra credibility
        self.high_value_certifications = {
            CertificationType.RSPO.value,
            CertificationType.NDPE.value,
            CertificationType.RAINFOREST_ALLIANCE.value,
            CertificationType.ORGANIC.value,
            CertificationType.FAIR_TRADE.value
        }
        
        # Certifications that are commonly faked or misused
        self.commonly_misused = {
            CertificationType.SUSTAINABLE.value,
            CertificationType.TRACEABLE.value
        }
    
    def validate(self, data: Any, context: Dict[str, Any] = None) -> List[ValidationResult]:
        """
        Validate certifications list.
        
        Args:
            data: List of certification names
            context: Optional context (product_category, company_type, etc.)
            
        Returns:
            List of validation results
        """
        results = []
        
        if not isinstance(data, list):
            results.append(
                self._create_error(
                    message="Certifications must be provided as a list",
                    field="certifications",
                    code="INVALID_TYPE"
                )
            )
            return results
        
        # Validate individual certifications
        for i, cert in enumerate(data):
            cert_results = self._validate_single_certification(cert, i)
            results.extend(cert_results)
        
        # Validate certification combination
        if all(result.is_valid for result in results):
            results.extend(self._validate_certification_combination(data, context))
            results.extend(self._validate_certification_relevance(data, context))
        
        return results
    
    def _validate_single_certification(
        self, 
        certification: Any, 
        index: int
    ) -> List[ValidationResult]:
        """Validate a single certification."""
        results = []
        field_name = f"certifications[{index}]"
        
        if not isinstance(certification, str):
            results.append(
                self._create_error(
                    message="Each certification must be a string",
                    field=field_name,
                    code="INVALID_TYPE"
                )
            )
            return results
        
        cert_name = certification.strip()
        
        if not cert_name:
            results.append(
                self._create_error(
                    message="Certification name cannot be empty",
                    field=field_name,
                    code="EMPTY_VALUE"
                )
            )
            return results
        
        # Check if it's a standard certification
        if cert_name not in self.standard_certifications:
            # Check for common misspellings or variations
            suggestions = self._get_certification_suggestions(cert_name)
            
            results.append(
                self._create_warning(
                    message=f"'{cert_name}' is not a recognized standard certification",
                    field=field_name,
                    suggestions=suggestions if suggestions else [
                        "Use standard certification names",
                        "Contact support to add new certification types"
                    ]
                )
            )
        else:
            # Check if it's commonly misused
            if cert_name in self.commonly_misused:
                results.append(
                    self._create_warning(
                        message=f"'{cert_name}' is a general term. Consider using specific certification standards.",
                        field=field_name,
                        suggestions=[
                            "Use specific certification body names",
                            "Provide certification numbers or details"
                        ]
                    )
                )
        
        return results
    
    def _validate_certification_combination(
        self, 
        certifications: List[str], 
        context: Dict[str, Any] = None
    ) -> List[ValidationResult]:
        """Validate the combination of certifications."""
        results = []
        
        # Check for duplicates
        cert_set = set(certifications)
        if len(cert_set) != len(certifications):
            duplicates = [cert for cert in cert_set if certifications.count(cert) > 1]
            results.append(
                self._create_warning(
                    message=f"Duplicate certifications found: {', '.join(duplicates)}",
                    field="certifications",
                    suggestions=["Remove duplicate entries"]
                )
            )
        
        # Check for conflicting certifications
        conflicts = self._check_certification_conflicts(cert_set)
        for conflict in conflicts:
            results.append(
                self._create_warning(
                    message=f"Potentially conflicting certifications: {conflict['message']}",
                    field="certifications",
                    suggestions=conflict["suggestions"]
                )
            )
        
        # Provide recommendations based on what's missing
        recommendations = self._get_certification_recommendations(cert_set, context)
        for rec in recommendations:
            results.append(
                self._create_warning(
                    message=rec["message"],
                    field="certifications",
                    suggestions=rec["suggestions"]
                )
            )
        
        return results
    
    def _validate_certification_relevance(
        self, 
        certifications: List[str], 
        context: Dict[str, Any] = None
    ) -> List[ValidationResult]:
        """Validate certification relevance to product/company."""
        results = []
        
        if not context:
            return results
        
        product_category = context.get("product_category")
        company_type = context.get("company_type")
        
        # Check relevance based on product category
        if product_category:
            relevance_results = self._check_product_relevance(certifications, product_category)
            results.extend(relevance_results)
        
        # Check relevance based on company type
        if company_type:
            company_results = self._check_company_relevance(certifications, company_type)
            results.extend(company_results)
        
        return results
    
    def _get_certification_suggestions(self, cert_name: str) -> List[str]:
        """Get suggestions for misspelled or similar certifications."""
        suggestions = []
        cert_lower = cert_name.lower()
        
        # Common misspellings and variations
        mappings = {
            "rspo": [CertificationType.RSPO.value],
            "roundtable": [CertificationType.RSPO.value, CertificationType.RTRS.value],
            "rainforest": [CertificationType.RAINFOREST_ALLIANCE.value],
            "organic": [CertificationType.ORGANIC.value],
            "fairtrade": [CertificationType.FAIR_TRADE.value],
            "fair trade": [CertificationType.FAIR_TRADE.value],
            "sustainable": [CertificationType.RSPO.value, CertificationType.SUSTAINABLE.value],
            "palm": [CertificationType.RSPO.value, CertificationType.ISPO.value, CertificationType.MSPO.value]
        }
        
        for key, values in mappings.items():
            if key in cert_lower:
                suggestions.extend(values)
        
        return list(set(suggestions))
    
    def _check_certification_conflicts(self, certifications: Set[str]) -> List[Dict[str, Any]]:
        """Check for conflicting certifications."""
        conflicts = []
        
        # Example: Some certifications might be mutually exclusive or redundant
        if (CertificationType.ISPO.value in certifications and 
            CertificationType.MSPO.value in certifications):
            conflicts.append({
                "message": "ISPO and MSPO are both Indonesian/Malaysian palm oil standards",
                "suggestions": ["Choose the most relevant standard for your region"]
            })
        
        return conflicts
    
    def _get_certification_recommendations(
        self, 
        certifications: Set[str], 
        context: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """Get recommendations for additional certifications."""
        recommendations = []
        
        if not context:
            return recommendations
        
        product_category = context.get("product_category")
        company_type = context.get("company_type")
        
        # Recommend RSPO for palm oil products
        if (product_category in ["raw_material", "processed_material"] and
            CertificationType.RSPO.value not in certifications):
            recommendations.append({
                "message": "Consider adding RSPO certification for palm oil products",
                "suggestions": ["Apply for RSPO certification", "Work with RSPO certified suppliers"]
            })
        
        # Recommend environmental certifications for originators
        if (company_type == "originator" and
            not any(cert in certifications for cert in [
                CertificationType.RAINFOREST_ALLIANCE.value,
                CertificationType.ORGANIC.value
            ])):
            recommendations.append({
                "message": "Environmental certifications strengthen originator credibility",
                "suggestions": ["Consider Rainforest Alliance certification", "Explore organic certification"]
            })
        
        return recommendations
    
    def _check_product_relevance(
        self, 
        certifications: List[str], 
        product_category: str
    ) -> List[ValidationResult]:
        """Check certification relevance to product category."""
        results = []
        
        # Define relevant certifications by product category
        relevance_map = {
            "raw_material": {
                "highly_relevant": [
                    CertificationType.RSPO.value,
                    CertificationType.ORGANIC.value,
                    CertificationType.RAINFOREST_ALLIANCE.value
                ],
                "somewhat_relevant": [
                    CertificationType.FAIR_TRADE.value,
                    CertificationType.SUSTAINABLE.value
                ]
            },
            "processed_material": {
                "highly_relevant": [
                    CertificationType.RSPO.value,
                    CertificationType.ISCC.value
                ],
                "somewhat_relevant": [
                    CertificationType.ORGANIC.value,
                    CertificationType.SUSTAINABLE.value
                ]
            }
        }
        
        if product_category in relevance_map:
            relevant_certs = relevance_map[product_category]
            
            # Check if any highly relevant certifications are present
            has_highly_relevant = any(
                cert in certifications 
                for cert in relevant_certs["highly_relevant"]
            )
            
            if not has_highly_relevant:
                results.append(
                    self._create_warning(
                        message=f"No highly relevant certifications for {product_category} products",
                        suggestions=[
                            f"Consider adding: {', '.join(relevant_certs['highly_relevant'])}"
                        ]
                    )
                )
        
        return results
    
    def _check_company_relevance(
        self, 
        certifications: List[str], 
        company_type: str
    ) -> List[ValidationResult]:
        """Check certification relevance to company type."""
        results = []
        
        # Define expected certifications by company type
        company_expectations = {
            "originator": [
                CertificationType.RSPO.value,
                CertificationType.RAINFOREST_ALLIANCE.value,
                CertificationType.ORGANIC.value
            ],
            "processor": [
                CertificationType.RSPO.value,
                CertificationType.ISCC.value
            ],
            "brand": [
                CertificationType.RSPO.value,
                CertificationType.FAIR_TRADE.value
            ]
        }
        
        if company_type in company_expectations:
            expected = company_expectations[company_type]
            has_expected = any(cert in certifications for cert in expected)
            
            if not has_expected:
                results.append(
                    self._create_warning(
                        message=f"No typical certifications for {company_type} companies",
                        suggestions=[
                            f"Consider certifications common for {company_type}s: {', '.join(expected)}"
                        ]
                    )
                )
        
        return results
