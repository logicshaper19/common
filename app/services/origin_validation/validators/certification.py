"""
Certification validation component.

This module handles validation of certifications against regional and
product requirements.
"""

from typing import Dict, Any, List
from ..models.requirements import CertificationRequirementService
from ..models.enums import CertificationBody, PalmOilRegion
from .base import BaseValidator, ValidationResult


class CertificationValidator(BaseValidator):
    """Validates certifications against regional and product requirements."""
    
    def __init__(self, requirement_service: CertificationRequirementService):
        self.requirement_service = requirement_service
    
    def validate(self, certifications: List[str], 
                context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate certifications comprehensively.
        
        Args:
            certifications: List of certification strings
            context: Validation context including product and region info
            
        Returns:
            Certification validation result
        """
        result = ValidationResult()
        
        product = context.get("product")
        detected_region = context.get("detected_region")
        
        # Validate recognition
        recognition_result = self._validate_recognition(certifications, result)
        
        # Validate regional requirements
        regional_result = self._validate_regional_requirements(
            certifications, detected_region, product, result
        )
        
        # Calculate quality score
        quality_score = self._calculate_quality_score(
            recognition_result["recognized_certifications"]
        )
        
        # Set metadata
        result.update_metadata({
            "recognized_certifications": recognition_result["recognized_certifications"],
            "unrecognized_certifications": recognition_result["unrecognized_certifications"],
            "quality_score": quality_score,
            "regional_compliance": regional_result,
            "total_certifications": len(certifications),
            "recognition_rate": len(recognition_result["recognized_certifications"]) / max(len(certifications), 1)
        })
        
        return result.to_dict()
    
    def _validate_recognition(self, certifications: List[str], 
                             result: ValidationResult) -> Dict[str, Any]:
        """
        Validate certification recognition.
        
        Args:
            certifications: List of certification strings
            result: Result object to add messages to
            
        Returns:
            Recognition validation result
        """
        valid_certifications = {cert.value for cert in CertificationBody}
        recognized_certs = []
        unrecognized_certs = []
        
        for cert in certifications:
            if cert in valid_certifications:
                recognized_certs.append(cert)
            else:
                unrecognized_certs.append(cert)
                result.add_warning(f"Unrecognized certification: {cert}")
        
        if not certifications:
            result.add_warning("No certifications provided")
        elif not recognized_certs:
            result.add_error("No recognized certifications found")
        elif len(recognized_certs) == len(certifications):
            result.add_suggestion("All certifications are recognized")
        
        return {
            "recognized_certifications": recognized_certs,
            "unrecognized_certifications": unrecognized_certs
        }
    
    def _validate_regional_requirements(
        self, 
        certifications: List[str], 
        detected_region: str, 
        product: Any,
        result: ValidationResult
    ) -> Dict[str, Any]:
        """
        Validate against regional requirements.
        
        Args:
            certifications: List of certification strings
            detected_region: Detected palm oil region
            product: Product information
            result: Result object to add messages to
            
        Returns:
            Regional compliance result
        """
        if not detected_region:
            result.add_warning("Cannot validate regional requirements - region not detected")
            return {"compliance_score": 0.5, "requirements_met": [], "requirements_missing": []}
        
        try:
            region_enum = PalmOilRegion(detected_region)
        except ValueError:
            result.add_warning(f"Unknown region for requirements validation: {detected_region}")
            return {"compliance_score": 0.5, "requirements_met": [], "requirements_missing": []}
        
        # Get regional requirements
        requirements = self.requirement_service.get_requirements_for_region(
            region_enum, 
            getattr(product, 'category', 'raw_material')
        )
        
        if not requirements:
            result.add_suggestion(f"No specific requirements for {detected_region}")
            return {"compliance_score": 1.0, "requirements_met": [], "requirements_missing": []}
        
        # Check compliance
        compliance_result = requirements.check_compliance(certifications)
        
        # Add messages based on compliance
        if compliance_result["is_compliant"]:
            result.add_suggestion(f"Meets regional requirements for {detected_region}")
        else:
            missing = compliance_result["missing_required"]
            if missing:
                result.add_error(f"Missing required certifications for {detected_region}: {', '.join(missing)}")
        
        missing_recommended = compliance_result["missing_recommended"]
        if missing_recommended:
            result.add_suggestion(f"Consider adding recommended certifications: {', '.join(missing_recommended)}")
        
        return compliance_result
    
    def _calculate_quality_score(self, recognized_certifications: List[str]) -> float:
        """
        Calculate quality score based on certifications.
        
        Args:
            recognized_certifications: List of recognized certification strings
            
        Returns:
            Quality score (0-1)
        """
        if not recognized_certifications:
            return 0.0
        
        high_value_certs = CertificationBody.get_high_value_certifications()
        high_value_names = {cert.value for cert in high_value_certs}
        
        # Base score from having any certifications
        base_score = 0.3
        
        # Bonus for high-value certifications
        high_value_count = sum(1 for cert in recognized_certifications if cert in high_value_names)
        high_value_bonus = min(high_value_count * 0.2, 0.6)
        
        # Bonus for multiple certifications (diversity)
        diversity_bonus = min((len(recognized_certifications) - 1) * 0.05, 0.1)
        
        total_score = base_score + high_value_bonus + diversity_bonus
        return min(total_score, 1.0)
    
    def get_certification_recommendations(
        self, 
        current_certifications: List[str],
        region: str,
        product_category: str
    ) -> List[str]:
        """
        Get certification recommendations for improvement.
        
        Args:
            current_certifications: Current certifications
            region: Palm oil region
            product_category: Product category
            
        Returns:
            List of recommended certifications
        """
        recommendations = []
        
        try:
            region_enum = PalmOilRegion(region)
            requirements = self.requirement_service.get_requirements_for_region(
                region_enum, product_category
            )
            
            if requirements:
                # Recommend missing required certifications
                missing_required = [
                    cert.value for cert in requirements.required_certifications
                    if cert.value not in current_certifications
                ]
                recommendations.extend(missing_required)
                
                # Recommend high-value certifications not yet held
                high_value_certs = CertificationBody.get_high_value_certifications()
                missing_high_value = [
                    cert.value for cert in high_value_certs
                    if cert.value not in current_certifications
                ]
                recommendations.extend(missing_high_value[:3])  # Limit to top 3
        
        except ValueError:
            # If region is unknown, recommend general high-value certifications
            high_value_certs = CertificationBody.get_high_value_certifications()
            recommendations = [
                cert.value for cert in high_value_certs
                if cert.value not in current_certifications
            ][:3]
        
        return list(dict.fromkeys(recommendations))  # Remove duplicates while preserving order
