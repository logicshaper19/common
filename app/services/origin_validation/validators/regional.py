"""
Regional compliance validation component.

This module handles validation of regional compliance requirements
including data completeness and regional standards.
"""

from typing import Dict, Any, Optional
from ..models.boundaries import GeographicBoundaryService
from ..models.requirements import CertificationRequirementService
from ..models.enums import PalmOilRegion
from .base import BaseValidator, ValidationResult
from app.schemas.confirmation import OriginDataCapture


class RegionalValidator(BaseValidator):
    """Validates regional compliance requirements."""
    
    def __init__(
        self, 
        boundary_service: GeographicBoundaryService,
        requirement_service: CertificationRequirementService
    ):
        self.boundary_service = boundary_service
        self.requirement_service = requirement_service
    
    def validate(self, origin_data: OriginDataCapture, 
                context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate regional compliance requirements.
        
        Args:
            origin_data: Complete origin data
            context: Validation context including detected region and product
            
        Returns:
            Regional compliance validation result
        """
        result = ValidationResult()
        
        detected_region = context.get("detected_region")
        product = context.get("product")
        
        if not detected_region:
            return self._handle_unknown_region(result)
        
        try:
            region_enum = PalmOilRegion(detected_region)
        except ValueError:
            result.add_warning(f"Unknown region for compliance validation: {detected_region}")
            return self._create_default_result(result, detected_region)
        
        # Get regional requirements
        requirements = self.requirement_service.get_requirements_for_region(
            region_enum, 
            getattr(product, 'category', 'raw_material')
        )
        
        compliance_score = 1.0
        requirements_met = []
        requirements_missing = []
        
        if requirements:
            # Check certification compliance
            compliance_result = self._validate_certification_compliance(
                origin_data.certifications, requirements, result
            )
            compliance_score *= compliance_result["score"]
            requirements_met.extend(compliance_result["met"])
            requirements_missing.extend(compliance_result["missing"])
        
        # Check data completeness for region
        completeness_result = self._validate_data_completeness(
            origin_data, region_enum, result
        )
        compliance_score *= completeness_result["score"]
        
        # Validate region-specific standards
        standards_result = self._validate_regional_standards(
            origin_data, region_enum, result
        )
        compliance_score *= standards_result["score"]
        
        # Set metadata
        result.update_metadata({
            "region": detected_region,
            "compliance_score": max(compliance_score, 0.0),
            "compliance_level": requirements.compliance_level if requirements else "optional",
            "requirements_met": requirements_met,
            "requirements_missing": requirements_missing,
            "data_completeness": completeness_result,
            "standards_compliance": standards_result
        })
        
        return result.to_dict()
    
    def _handle_unknown_region(self, result: ValidationResult) -> Dict[str, Any]:
        """Handle case where region cannot be determined."""
        result.add_warning("Cannot determine regional compliance - location outside known palm oil regions")
        
        result.update_metadata({
            "region": None,
            "compliance_score": 0.5,
            "compliance_level": "unknown",
            "requirements_met": [],
            "requirements_missing": []
        })
        
        return result.to_dict()
    
    def _create_default_result(self, result: ValidationResult, region: str) -> Dict[str, Any]:
        """Create default result for unknown regions."""
        result.update_metadata({
            "region": region,
            "compliance_score": 1.0,
            "compliance_level": "optional",
            "requirements_met": [],
            "requirements_missing": []
        })
        
        return result.to_dict()
    
    def _validate_certification_compliance(
        self, 
        certifications: list[str], 
        requirements: Any,
        result: ValidationResult
    ) -> Dict[str, Any]:
        """Validate certification compliance against requirements."""
        compliance_result = requirements.check_compliance(certifications)
        
        # Add appropriate messages
        if compliance_result["is_compliant"]:
            result.add_suggestion(f"Meets certification requirements ({requirements.compliance_level})")
        else:
            missing = compliance_result["missing_required"]
            if missing:
                if requirements.compliance_level == "mandatory":
                    result.add_error(f"Missing mandatory certifications: {', '.join(missing)}")
                else:
                    result.add_warning(f"Missing recommended certifications: {', '.join(missing)}")
        
        return {
            "score": compliance_result["compliance_score"],
            "met": compliance_result["provided_certifications"],
            "missing": compliance_result["missing_required"] + compliance_result["missing_recommended"]
        }
    
    def _validate_data_completeness(
        self, 
        origin_data: OriginDataCapture, 
        region: PalmOilRegion,
        result: ValidationResult
    ) -> Dict[str, Any]:
        """Validate data completeness for the region."""
        completeness_score = 1.0
        completeness_issues = []
        
        # Get region info to determine standards
        region_info = self.boundary_service.get_region_info(region)
        quality_standards = region_info.get("quality_standards", [])
        
        # Check farm identification for major producing regions
        if "farm_identification_recommended" in quality_standards:
            if not origin_data.farm_information:
                result.add_warning("Farm identification recommended for this region")
                completeness_score -= 0.1
                completeness_issues.append("missing_farm_information")
            else:
                result.add_suggestion("Farm identification provided")
        
        # Check high accuracy requirement
        if "high_accuracy_required" in quality_standards:
            if not origin_data.geographic_coordinates.accuracy_meters:
                result.add_warning("GPS accuracy information required for this region")
                completeness_score -= 0.1
                completeness_issues.append("missing_gps_accuracy")
            elif origin_data.geographic_coordinates.accuracy_meters > 50:
                result.add_warning("Higher GPS accuracy recommended for this region")
                completeness_score -= 0.05
                completeness_issues.append("low_gps_accuracy")
        
        # Check harvest date for major regions
        if region in [PalmOilRegion.SOUTHEAST_ASIA, PalmOilRegion.WEST_AFRICA]:
            if not origin_data.harvest_date:
                result.add_warning("Harvest date recommended for major producing regions")
                completeness_score -= 0.1
                completeness_issues.append("missing_harvest_date")
        
        # Check seasonal tracking
        if "seasonal_tracking" in quality_standards:
            if not origin_data.harvest_date:
                result.add_warning("Seasonal tracking requires harvest date information")
                completeness_score -= 0.15
                completeness_issues.append("missing_seasonal_data")
        
        return {
            "score": max(completeness_score, 0.0),
            "issues": completeness_issues,
            "standards_checked": quality_standards
        }
    
    def _validate_regional_standards(
        self, 
        origin_data: OriginDataCapture, 
        region: PalmOilRegion,
        result: ValidationResult
    ) -> Dict[str, Any]:
        """Validate region-specific standards."""
        standards_score = 1.0
        standards_issues = []
        
        # Region-specific validations
        if region == PalmOilRegion.SOUTHEAST_ASIA:
            standards_result = self._validate_southeast_asia_standards(origin_data, result)
        elif region == PalmOilRegion.WEST_AFRICA:
            standards_result = self._validate_west_africa_standards(origin_data, result)
        elif region == PalmOilRegion.SOUTH_AMERICA:
            standards_result = self._validate_south_america_standards(origin_data, result)
        else:
            standards_result = {"score": 1.0, "issues": []}
        
        return standards_result
    
    def _validate_southeast_asia_standards(
        self, 
        origin_data: OriginDataCapture, 
        result: ValidationResult
    ) -> Dict[str, Any]:
        """Validate Southeast Asia specific standards."""
        score = 1.0
        issues = []
        
        # High standards for major producing region
        if not origin_data.farm_information:
            result.add_suggestion("Farm identification highly recommended for Southeast Asia")
            score -= 0.05
            issues.append("farm_id_recommended")
        
        # RSPO certification highly valued
        if "RSPO" not in origin_data.certifications:
            result.add_suggestion("RSPO certification highly recommended for Southeast Asia")
            score -= 0.1
            issues.append("rspo_recommended")
        
        return {"score": max(score, 0.0), "issues": issues}
    
    def _validate_west_africa_standards(
        self, 
        origin_data: OriginDataCapture, 
        result: ValidationResult
    ) -> Dict[str, Any]:
        """Validate West Africa specific standards."""
        score = 1.0
        issues = []
        
        # Sustainability focus
        sustainability_certs = ["RSPO", "Rainforest Alliance", "Sustainable"]
        has_sustainability = any(cert in origin_data.certifications for cert in sustainability_certs)
        
        if not has_sustainability:
            result.add_suggestion("Sustainability certification recommended for West Africa")
            score -= 0.1
            issues.append("sustainability_recommended")
        
        return {"score": max(score, 0.0), "issues": issues}
    
    def _validate_south_america_standards(
        self, 
        origin_data: OriginDataCapture, 
        result: ValidationResult
    ) -> Dict[str, Any]:
        """Validate South America specific standards."""
        score = 1.0
        issues = []
        
        # Deforestation monitoring important
        deforestation_certs = ["NDPE", "Rainforest Alliance"]
        has_deforestation = any(cert in origin_data.certifications for cert in deforestation_certs)
        
        if not has_deforestation:
            result.add_suggestion("Deforestation monitoring certification recommended for South America")
            score -= 0.1
            issues.append("deforestation_monitoring_recommended")
        
        return {"score": max(score, 0.0), "issues": issues}
