"""
Main orchestrator for origin validation.

This module coordinates the complete origin validation process,
orchestrating multiple validators and combining their results.
"""

from typing import Dict, Any, Optional
from uuid import UUID
from sqlalchemy.orm import Session

from ..validators import (
    CoordinateValidator, 
    CertificationValidator, 
    HarvestDateValidator,
    RegionalValidator
)
from ..models.results import OriginDataValidationResult
from ..models.enums import ComplianceStatus
from .data_provider import OriginDataProvider
from app.schemas.confirmation import OriginDataCapture
from app.models.product import Product
from app.core.logging import get_logger

logger = get_logger(__name__)


class OriginValidationOrchestrator:
    """Orchestrates the complete origin validation process."""
    
    def __init__(
        self,
        db: Session,
        data_provider: OriginDataProvider,
        coord_validator: CoordinateValidator,
        cert_validator: CertificationValidator,
        date_validator: HarvestDateValidator,
        regional_validator: RegionalValidator
    ):
        self.db = db
        self.data_provider = data_provider
        self.coord_validator = coord_validator
        self.cert_validator = cert_validator
        self.date_validator = date_validator
        self.regional_validator = regional_validator
    
    def validate_comprehensive_origin_data(
        self,
        origin_data: OriginDataCapture,
        product_id: UUID,
        purchase_order_id: Optional[UUID] = None
    ) -> OriginDataValidationResult:
        """
        Perform comprehensive validation of origin data.
        
        Args:
            origin_data: Origin data to validate
            product_id: Product UUID for context-specific validation
            purchase_order_id: Optional purchase order UUID for additional context
            
        Returns:
            Comprehensive validation result
        """
        logger.info(
            "Starting comprehensive origin data validation",
            product_id=str(product_id),
            po_id=str(purchase_order_id) if purchase_order_id else None
        )
        
        # Get product context
        product = self._get_product(product_id)
        if not product:
            return self._create_invalid_result("Product not found")
        
        # Build validation context
        context = {"product": product, "purchase_order_id": purchase_order_id}
        
        # Step 1: Coordinate validation
        coord_result = self.coord_validator.validate(
            origin_data.geographic_coordinates, context
        )
        context["detected_region"] = coord_result.get("metadata", {}).get("detected_region")
        
        # Step 2: Certification validation
        cert_result = self.cert_validator.validate(
            origin_data.certifications, context
        )
        
        # Step 3: Harvest date validation
        date_result = self.date_validator.validate(
            origin_data.harvest_date, context
        )
        
        # Step 4: Regional compliance validation
        regional_result = self.regional_validator.validate(
            origin_data, context
        )
        
        # Step 5: Calculate overall scores and status
        quality_score = self._calculate_quality_score(
            coord_result, cert_result, date_result, regional_result
        )
        
        compliance_status = self._determine_compliance_status(
            coord_result, cert_result, date_result, regional_result, quality_score
        )
        
        # Compile all messages
        all_errors = []
        all_warnings = []
        all_suggestions = []
        
        for validation in [coord_result, cert_result, date_result, regional_result]:
            all_errors.extend(validation.get("errors", []))
            all_warnings.extend(validation.get("warnings", []))
            all_suggestions.extend(validation.get("suggestions", []))
        
        # Create final result
        is_valid = len(all_errors) == 0
        
        result = OriginDataValidationResult(
            is_valid=is_valid,
            coordinate_validation=coord_result,
            certification_validation=cert_result,
            harvest_date_validation=date_result,
            regional_compliance=regional_result,
            quality_score=quality_score,
            errors=all_errors,
            warnings=all_warnings,
            suggestions=all_suggestions,
            compliance_status=compliance_status.value
        )
        
        logger.info(
            "Origin data validation completed",
            product_id=str(product_id),
            is_valid=is_valid,
            quality_score=quality_score,
            compliance_status=compliance_status.value,
            detected_region=context.get("detected_region"),
            errors_count=len(all_errors),
            warnings_count=len(all_warnings)
        )
        
        return result
    
    def _get_product(self, product_id: UUID) -> Optional[Product]:
        """Get product from database."""
        try:
            return self.db.query(Product).filter(Product.id == product_id).first()
        except Exception as e:
            logger.error(f"Error fetching product {product_id}: {e}")
            return None
    
    def _create_invalid_result(self, error_message: str) -> OriginDataValidationResult:
        """Create an invalid result with error message."""
        return OriginDataValidationResult(
            is_valid=False,
            coordinate_validation={"is_valid": False, "errors": [], "warnings": [], "suggestions": [], "metadata": {}},
            certification_validation={"is_valid": False, "errors": [], "warnings": [], "suggestions": [], "metadata": {}},
            harvest_date_validation={"is_valid": False, "errors": [], "warnings": [], "suggestions": [], "metadata": {}},
            regional_compliance={"is_valid": False, "errors": [], "warnings": [], "suggestions": [], "metadata": {}},
            quality_score=0.0,
            errors=[error_message],
            warnings=[],
            suggestions=[],
            compliance_status=ComplianceStatus.NON_COMPLIANT.value
        )
    
    def _calculate_quality_score(
        self, 
        coord_result: Dict[str, Any],
        cert_result: Dict[str, Any],
        date_result: Dict[str, Any],
        regional_result: Dict[str, Any]
    ) -> float:
        """Calculate overall quality score from individual validation results."""
        
        # Extract individual scores
        coord_score = self._extract_coordinate_score(coord_result)
        cert_score = cert_result.get("metadata", {}).get("quality_score", 0.0)
        date_score = date_result.get("metadata", {}).get("freshness_score", 0.0)
        regional_score = regional_result.get("metadata", {}).get("compliance_score", 0.0)
        
        # Weighted average (certifications and regional compliance are most important)
        weights = [0.2, 0.4, 0.2, 0.2]  # coord, cert, date, regional
        scores = [coord_score, cert_score, date_score, regional_score]
        
        weighted_sum = sum(score * weight for score, weight in zip(scores, weights))
        return min(weighted_sum, 1.0)
    
    def _extract_coordinate_score(self, coord_result: Dict[str, Any]) -> float:
        """Extract coordinate quality score from validation result."""
        metadata = coord_result.get("metadata", {})
        accuracy_level = metadata.get("accuracy_level", "moderate")
        detected_region = metadata.get("detected_region")
        
        # Base score from accuracy
        accuracy_scores = {
            "excellent": 1.0,
            "good": 0.9,
            "moderate": 0.7,
            "low": 0.5,
            "poor": 0.3
        }
        base_score = accuracy_scores.get(accuracy_level, 0.5)
        
        # Bonus for being in known region
        region_bonus = 0.1 if detected_region else 0.0
        
        return min(base_score + region_bonus, 1.0)
    
    def _determine_compliance_status(
        self,
        coord_result: Dict[str, Any],
        cert_result: Dict[str, Any],
        date_result: Dict[str, Any],
        regional_result: Dict[str, Any],
        quality_score: float
    ) -> ComplianceStatus:
        """Determine overall compliance status."""
        
        # Check for any errors (non-compliant)
        has_errors = any(
            len(result.get("errors", [])) > 0 
            for result in [coord_result, cert_result, date_result, regional_result]
        )
        
        if has_errors:
            return ComplianceStatus.NON_COMPLIANT
        
        # Check regional compliance level
        regional_compliance = regional_result.get("metadata", {}).get("compliance_score", 1.0)
        
        # Determine status based on quality score and regional compliance
        if quality_score >= 0.9 and regional_compliance >= 0.9:
            return ComplianceStatus.EXCELLENT
        elif quality_score >= 0.8 and regional_compliance >= 0.8:
            return ComplianceStatus.GOOD
        elif quality_score >= 0.7 and regional_compliance >= 0.7:
            return ComplianceStatus.ACCEPTABLE
        elif quality_score >= 0.5 or regional_compliance >= 0.5:
            return ComplianceStatus.NEEDS_IMPROVEMENT
        else:
            return ComplianceStatus.NON_COMPLIANT
    
    # Legacy compatibility methods
    def get_certification_bodies(self) -> Dict[str, Any]:
        """Get certification bodies configuration."""
        return self.data_provider.certifications.get("certification_bodies", {})
    
    def get_palm_oil_regions(self) -> Dict[str, Any]:
        """Get palm oil regions configuration."""
        return self.data_provider.regions
    
    def get_certification_requirements(self) -> Dict[str, Any]:
        """Get certification requirements configuration."""
        return self.data_provider.certifications.get("regional_requirements", {})
